import discord
from discord.ext import commands

from decorators import is_admin, findPerson
from election import Election
from game import Game
import asyncio
import os
import json
from files import werewolfMessages, commandDescriptions, config, channels_config, roles_config, readJsonFromConfig


def can_clear():
    async def predicate(ctx):
        return not ((discord.utils.get(ctx.message.author.roles, name="Owner") is None) and (
                ctx.message.author != findPerson(ctx, "keyclimber")))

    return commands.check(predicate)


def has_role(r):
    async def predicate(ctx):
        return r in ctx.author.roles

    return commands.check(predicate)


class Bot(commands.Cog):

    def __init__(self, bot):
        self.__bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        print(error)

    @commands.command()
    async def echo(self, ctx, *args):
        output = ''
        for x in args:
            output += x
            output += ' '
        print(output)
        await ctx.send(output)

    @commands.command()
    @can_clear()
    async def clear(self, ctx, number=10):
        # Converting the amount of messages to delete to an integer
        number = int(number + 1)
        counter = 0
        delete_channel = ctx.message.channel
        async for x in (delete_channel.history(limit=number)):
            if counter < number:
                if x.pinned:
                    continue
                await x.delete()
                counter += 1
                await asyncio.sleep(0.4)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(":ping_pong: Pong!")

    @commands.command(pass_context=True)
    @is_admin()
    async def startgame(self, ctx, *args: int):
        game_future = self.__bot.loop.create_future()
        alive_role = discord.utils.get(
            ctx.guild.roles, name="Alive")
        playing_role = discord.utils.get(
            ctx.guild.roles, name="Playing")
        roles_assignment = [alive_role]
        if len(args) == 0:
            await ctx.send("Please add game parameters to the game")
            return
        players = []
        for member in ctx.guild.members:
            if playing_role in member.roles:
                players.append(member)
        if len(players) < sum(args):
            await ctx.send("You gave out too many roles for the number of people.")
            return
        for player in players:
            await player.edit(roles=roles_assignment)
        game_cog = Game(self.__bot, players, game_future, args)
        self.__bot.add_cog(game_cog)
        read_write_permission = readJsonFromConfig("permissions.json")["read_write"]
        for x in ctx.guild.members:
            if alive_role in x.roles:
                character = game_cog.getVillagerByID(x.id).Character
                if character in channels_config["character-to-channel"]:
                    channel_name = channels_config["character-to-channel"][character]
                    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                    await channel.set_permissions(x, overwrite=discord.PermissionOverwrite(**read_write_permission))
        await ctx.send("Let the games begin!")
        await game_future
        await self.__finishGame(ctx)


    @commands.command()
    @is_admin()
    async def endgame(self, ctx):
        await ctx.send("Ending Game")
        await self.__finishGame(ctx)

    async def __finishGame(self, ctx):
        self.__bot.remove_cog("Game")
        playing_role = discord.utils.get(
            ctx.guild.roles, name="Playing")
        owner_role = discord.utils.get(
            ctx.guild.roles, name="Owner")
        for member in ctx.guild.members:
            if owner_role not in member.roles:
                await member.edit(roles=[playing_role])
            for x in channels_config["channels"]:
                channel = discord.utils.get(ctx.guild.channels, name=x)
                await channel.set_permissions(member, overwrite=None)

    @commands.command()
    async def search(self, ctx, *args):
        user = findPerson(ctx, args)
        if user is not None:
            await ctx.send(user.display_name)
        else:
            await ctx.send("That person has not been found")

    @commands.command()
    @is_admin()
    async def exit(self, ctx):
        await ctx.send("Goodbye!")
        await self.__finishGame(ctx)
        await self.__bot.logout()

    @exit.error
    async def exit_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("I'm sorry, but you cannot shut me down!")

    @commands.command()
    @is_admin()
    async def addroles(self, ctx):
        for i, j in roles_config["roles"].items():
            if discord.utils.get(ctx.guild.roles, name=i) is not None:
                continue
            permission_object = discord.Permissions().none()
            permission_object.update(**roles_config["general-permissions"])
            if j["permissions-update"] is not None:
                permission_object.update(**j["permissions-update"])
            c = discord.Color.from_rgb(*j["color"])
            role = await ctx.guild.create_role(name=i, permissions=permission_object, color=c)
            message = i + " role created"
            await ctx.send(message)

    @commands.command()
    @is_admin()
    async def resetrolepermissions(self, ctx):
        for i, j in roles_config["roles"].items():
            role = discord.utils.get(ctx.guild.roles, name=i)
            if role is None:
                continue
            permissionObject = discord.Permissions().none()
            permissionObject.update(**roles_config["general-permissions"])
            if j["permissions-update"] is not None:
                permissionObject.update(**j["permissions-update"])
            await role.edit(permissions=permissionObject)
            message = i + " role permissions reset"
            await ctx.send(message)

    @commands.command()
    @is_admin()
    async def testroles(self, ctx):
        roles = [discord.utils.get(ctx.guild.roles, name="Not Playing"),
                 discord.utils.get(ctx.guild.roles, name="Playing"), discord.utils.get(ctx.guild.roles, name="Dead"),
                 discord.utils.get(ctx.guild.roles, name="Alive"), discord.utils.get(ctx.guild.roles, name="Mayor")]

        for i in range(len(roles)):
            for j in range(i + 1, len(roles)):
                if roles[i].permissions == roles[j].permissions:
                    print("These permissions are equal in these roles:",
                          roles[i], roles[j])
                else:
                    print("These permissions are not equal in these roles:",
                          roles[i], roles[j])

    @commands.command()
    @is_admin()
    async def addcategory(self, ctx):
        c = await ctx.guild.create_category_channel(channels_config["category-name"])
        for i, j in channels_config["category-permissions"].items():
            target = discord.utils.get(ctx.guild.roles, name=i)
            await c.set_permissions(target, overwrite=discord.PermissionOverwrite(**j))
        channel_id_dict = dict()
        for i in channels_config["channels"]:
            await ctx.guild.create_text_channel(name=i, category=c)
            id = discord.utils.get(ctx.guild.channels, name=i).id
            channel_id_dict[i] = id

        try:
            dirname = os.path.dirname(__file__)
            f = open(os.path.join(dirname, '../config/channel_id_list.json'), "w")
            f.write(json.dumps(channel_id_dict))
            f.close()
        except:
            print("Something went wrong. Exiting now!")
            exit()

        for i, j in channels_config["channel-permissions"].items():
            ch = discord.utils.get(c.channels, name=i)
            for k, l in j.items():
                target = discord.utils.get(ctx.guild.roles, name=k)
                await ch.set_permissions(target, overwrite=discord.PermissionOverwrite(**l))

    def cog_unload(self):
        return super().cog_unload()

    @commands.command()
    @is_admin()
    async def removecategory(self, ctx):
        c = discord.utils.get(ctx.guild.categories,
                              name=channels_config["category-name"])
        for i in c.channels:
            await i.delete()
        await c.delete()

        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, '../config/channel_id_list.json')
        if os.path.exists(path):
            os.remove(path)



