import discord
from discord.ext import commands
from game import Game
import asyncio
import os
import json
from cogstest import Test
from files import werewolfMessages, commandDescriptions, config, channels_config, roles_config, readJsonFromConfig


class Bot(commands.Cog):

    def __init__(self, bot):
        self.__bot = bot

    def is_admin():
        async def predicate(ctx):
            return ctx.channel == discord.utils.get(ctx.guild.channels, name="bot-admin")
        return commands.check(predicate)

    def has_role(self, r):
        async def predicate(ctx):
            return r in ctx.author.roles
        return commands.check(predicate)

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
        await ctx.send(output)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(":ping_pong: Pong!")

    @commands.command(pass_context=True)
    @is_admin()
    async def startgame(self, ctx, *args: int):
        alive_role = discord.utils.get(
            ctx.guild.roles, name="Alive")    
        playing_role = discord.utils.get(
            ctx.guild.roles, name="Playing")
        if len(args) == 0:
            await ctx.send("Please add game parameters to the game")
            return
        players = []
        for member in ctx.guild.members:
            if playing_role in member.roles:
                players.append(member)
                await member.edit(roles=[alive_role])
        if len(players) < sum(args):
            await ctx.send("You gave out too many roles for the number of people.")
            return
        game_cog = Game(self.__bot, players, args)
        self.__bot.add_cog(game_cog)
        read_write_permission = readJsonFromConfig("permissions.json")["read_write"]
        for x in ctx.guild.members:
            if playing_role in x.roles:
                await x.edit(roles=[alive_role])
                character = game_cog.getVillagerByID(x.id).getCharacter()
                if character in channels_config["character-to-channel"]:
                    channel = channels_config["character-to-channel"][character]
                    # await channel.set_permissions(x, overwrite=discord.PermissionOverwrite(**read_write_permission))

                

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

    @commands.command()
    async def search(self, ctx, *args):
        user = self.findPerson(ctx, args)
        if user != None:
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
            permissionObject = discord.Permissions().none()
            permissionObject.update(**roles_config["general-permissions"])
            if j["permissions-update"] is not None:
                permissionObject.update(**j["permissions-update"])
            c = discord.Color.from_rgb(*j["color"])
            role = await ctx.guild.create_role(name=i, permissions=permissionObject, color=c)
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
            await ping(ctx)

    @commands.command()
    @is_admin()
    async def testroles(self, ctx):
        roles = []
        roles.append(discord.utils.get(ctx.guild.roles, name="Not Playing"))
        roles.append(discord.utils.get(ctx.guild.roles, name="Playing"))
        roles.append(discord.utils.get(ctx.guild.roles, name="Dead"))
        roles.append(discord.utils.get(ctx.guild.roles, name="Alive"))
        roles.append(discord.utils.get(ctx.guild.roles, name="Mayor"))

        for i in range(len(roles)):
            for j in range(i+1, len(roles)):
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

    def findPerson(self, ctx, *args):
        if len(args) == 1:
            if type(args[0]) is str:
                name = args[0]
            else:
                name = " ".join(args[0])
        else:
            print("Something went very wrong. Args is not of length 1")
            return None
        if name[0:3] == "<@!":
            return ctx.message.guild.get_member(name[3:-1])
        elif name[0:2] == "<@":
            return ctx.message.guild.get_member(name[2:-1])
        else:
            return ctx.message.guild.get_member_named(name)
