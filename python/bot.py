import discord
from discord.ext import commands

from decorators import is_admin, findPerson
from election import Election
from game import Game
import asyncio
import models.channels
import models.game
import models.villager
import os
import json
import files


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
        self.__game = False

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        print(error)

    @commands.command(**files.command_parameters['echo'])
    async def echo(self, ctx, *args):
        if len(args) > 0:
            output = ''
            for x in args:
                output += x
                output += ' '
            print(output)
            await ctx.send(output)

    @commands.command(**files.command_parameters['tickle'])
    async def tickle(self, ctx):
        await ctx.send(":rofl:  Stop it!  :rofl: :rofl:")

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

    @commands.command(**files.command_parameters["ping"])
    async def ping(self, ctx):
        await ctx.send(":ping_pong: Pong!")

    @commands.command(**files.command_parameters['playing'])
    async def playing(self, ctx):
        playing_role = discord.utils.get(ctx.guild.roles, name="Playing")
        await ctx.author.edit(roles={playing_role})
        await ctx.send(f"{ctx.author.mention} is now playing.")

    @commands.command(**files.command_parameters['notplaying'])
    async def notplaying(self, ctx):
        if self.__game:
            await ctx.send("You can't stop now!")
            return
        await ctx.author.edit(roles=[])
        await ctx.send(f"{ctx.author.mention} is not playing.")

    @commands.command(**files.command_parameters["startgame"])
    @is_admin()
    async def startgame(self, ctx, *args: int):
        with ctx.typing():
            game_future = self.__bot.loop.create_future()
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            playing_role = discord.utils.get(ctx.guild.roles, name="Playing")
            if len(args) == 0:
                await ctx.send("Please add game parameters to the game")
                return
            players = []
            for member in ctx.guild.members:
                if playing_role in member.roles:
                    players.append(member)
            if len(players) < sum(args):
                await ctx.send("You gave out too many roles for the number of people. Please try again.")
                return
            for player in players:
                await player.edit(roles=[alive_role])
            game_cog = Game(self.__bot, randomshuffle=False, members=players, guild_id=ctx.guild.id, future=game_future, roles=args, send_message_flag=False)
            self.__bot.add_cog(game_cog)
            self.__game = True
            read_write_permission = files.readJsonFromConfig("permissions.json")["read_write"]
            for x in players:
                v_model = models.villager.Villager.find_one({
                    "server": ctx.guild.id,
                    "discord_id": x.id
                })
                character = v_model["character"]
                if character in files.channels_config["character-to-channel"]:
                    channel_name = files.channels_config["character-to-channel"][character]
                    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                    await channel.set_permissions(x, overwrite=discord.PermissionOverwrite(**read_write_permission))

        town_square_id = files.getChannelId("announcements", ctx.guild.id)
        town_square_channel = self.__bot.get_channel(town_square_id)
        await town_square_channel.send("Let the games begin!")
        await ctx.send("The game has started!")
        await game_future
        self.__game = False
        winner = game_future.result()
        if winner == "werewolves":
            await town_square_channel.send("Werewolves outnumber the villagers. Werewolves won.")
        elif winner == "villagers":
            await town_square_channel.send("All werewolves are now dead. Villagers win!")
        elif winner == "cupid":
            await town_square_channel.send("Cupid did a great job. The last two people alive are the love birds.")
        elif winner == "bakerdead":
            await town_square_channel.send("Everyone has starved. The werewolves survive off of villagers' corpses "
                                           "and win the game.")

        await self.__finishGame(ctx)

    @commands.command()
    @is_admin()
    async def endgame(self, ctx):
        with ctx.typing():
            await self.__finishGame(ctx)
            await ctx.send("Game has ended")

    async def __finishGame(self, ctx):
        playing_role = discord.utils.get(
            ctx.guild.roles, name="Playing")

        villagers = models.villager.Villager.find({"server": ctx.guild.id})
        for v in villagers:
            member = ctx.guild.get_member(v["discord_id"])

            await member.edit(roles=[playing_role])
            for x in files.channels_config["channels"]:
                if x == "announcements":
                    continue
                channel = discord.utils.get(ctx.guild.channels, name=x)
                await channel.set_permissions(member, overwrite=None)
            v.remove()
        models.game.delete_many({"server": ctx.guild.id})
        self.__bot.remove_cog("Game")

    @commands.command(brief="Exits the game")
    @is_admin()
    async def exit(self, ctx):
        with ctx.typing():
            await self.__finishGame(ctx)
            await ctx.send("Goodbye!")
        await self.__bot.logout()

    @exit.error
    async def exit_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("I'm sorry, but you cannot shut me down!")

    @commands.command()
    @is_admin()
    async def addroles(self, ctx):
        for i, j in files.roles_config["roles"].items():
            if discord.utils.get(ctx.guild.roles, name=i) is not None:
                continue
            permission_object = discord.Permissions().none()
            permission_object.update(**files.roles_config["general-permissions"])
            if j["permissions-update"] is not None:
                permission_object.update(**j["permissions-update"])
            c = discord.Color.from_rgb(*j["color"])
            role = await ctx.guild.create_role(name=i, permissions=permission_object, color=c)
            message = i + " role created"
            await ctx.send(message)

    @commands.command()
    @is_admin()
    async def resetrolepermissions(self, ctx):
        for i, j in files.roles_config["roles"].items():
            role = discord.utils.get(ctx.guild.roles, name=i)
            if role is None:
                continue
            permissionObject = discord.Permissions().none()
            permissionObject.update(**files.roles_config["general-permissions"])
            if j["permissions-update"] is not None:
                permissionObject.update(**j["permissions-update"])
            await role.edit(permissions=permissionObject)
            message = i + " role permissions reset"
            await ctx.send(message)

    @commands.command()
    @is_admin()
    async def addcategory(self, ctx):
        x = models.channels.Channels.find_one({"server": ctx.guild.id})
        if x is not None:
            await ctx.send("You already have the channels set up.")
            return
        town_square_category = await ctx.guild.create_category_channel(files.channels_config["category-name"])
        for i, j in files.channels_config["category-permissions"].items():
            target = discord.utils.get(ctx.guild.roles, name=i)
            await town_square_category.set_permissions(target, overwrite=discord.PermissionOverwrite(**j))
        channel_id_dict = dict()
        channel_id_dict["guild"] = ctx.guild.id
        for i in files.channels_config["channels"]:
            await ctx.guild.create_text_channel(name=i, category=town_square_category)
            channel = discord.utils.get(ctx.guild.channels, name=i)
            await channel.send('\n'.join(files.werewolfMessages["channel_messages"][i]))
            channel_id_dict[i] = channel.id
            async for x in (channel.history(limit=1)):
                await x.pin()


        channels = models.channels.Channels.find_one({"server": ctx.guild.id})
        if channels is None:
            channels = models.channels.Channels({
                "server": ctx.guild.id,
                "channels": channel_id_dict
            })
            channels.save()
        else:
            channels.update_instance({"channels": channel_id_dict})


        for i, j in files.channels_config["channel-permissions"].items():
            ch = discord.utils.get(town_square_category.channels, name=i)
            if ch is None:
                print("The name is", i)
            for k, l in j.items():
                target = discord.utils.get(ctx.guild.roles, name=k)
                await ch.set_permissions(target, overwrite=discord.PermissionOverwrite(**l))

    def cog_unload(self):
        return super().cog_unload()

    @commands.command()
    @is_admin()
    async def removecategory(self, ctx):
        c = discord.utils.get(ctx.guild.categories,
                              name=files.channels_config["category-name"])
        for i in c.channels:
            await i.delete()
        await c.delete()

        channel = models.channels.Channels.find_one({"server": ctx.guild.id})
        channel.remove()
