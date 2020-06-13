import discord
from discord.ext import commands
from schemer import ValidationException

import decorators
from decorators import is_admin, findPerson
from game import Game
import asyncio
import models.channels
import models.game
import models.election
import models.server
import models.villager
import files
import abilities


def can_clear():
    async def predicate(ctx):
        bot_admin_channel = discord.utils.get(ctx.guild.channels, name="bot-admin")
        return ctx.author in bot_admin_channel.overwrites or ctx.author == ctx.guild.owner

    return commands.check(predicate)


def has_role(r):
    async def predicate(ctx):
        return r in ctx.author.roles

    return commands.check(predicate)


async def add_roles_subroutine(ctx):
    for i, j in files.roles_config["roles"].items():
        if discord.utils.get(ctx.guild.roles, name=i) is not None:
            continue
        permission_object = discord.Permissions().none()
        permission_object.update(**files.roles_config["general-permissions"])
        if j["permissions-update"] is not None:
            permission_object.update(**j["permissions-update"])
        c = discord.Color.from_rgb(*j["color"])
        await ctx.guild.create_role(name=i, permissions=permission_object, color=c)
        message = i + " role created"
        await ctx.send(message)


class Bot(commands.Cog):

    def __init__(self, bot):
        self.__bot = bot
        self.__bot.add_cog(Game(self.__bot))
        # self.__game = False

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        print(error)

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

    @commands.command()
    @is_admin()
    async def changeprefix(self, ctx, new_prefix):
        server_document = models.server.Server.find_one({
            "server": ctx.guild.id
        })
        if server_document is None:
            server_document = models.server.Server({
                "server": ctx.guild.id
            })
            server_document.save()
        server_document["prefix"] = new_prefix
        server_document.save()
        await ctx.send(f"Prefix changed to {new_prefix}")

    @commands.command(**files.command_parameters['playing'])
    @decorators.is_no_game()
    async def playing(self, ctx):
        playing_role = discord.utils.get(ctx.guild.roles, name="Playing")
        await ctx.author.edit(roles={playing_role})
        await ctx.send(f"{ctx.author.mention} is now playing.")

    @commands.command(**files.command_parameters['notplaying'])
    @decorators.is_no_game()
    async def notplaying(self, ctx):
        await ctx.author.edit(roles=[])
        await ctx.send(f"{ctx.author.mention} is not playing.")

    @commands.command()
    @is_admin()
    async def addroles(self, ctx):
        await add_roles_subroutine(ctx)

    @commands.command()
    @is_admin()
    async def setupserver(self, ctx):
        await ctx.send("Setting up server!")
        with ctx.typing():  # This is where the fun begins
            await add_roles_subroutine(ctx)
            x = models.channels.Channels.find_one({"server": ctx.guild.id})
            if x is not None:
                await ctx.send("You already have the channels set up.")
                return
            if not await self.create_channels(ctx.guild):
                await ctx.send("I did all that I could. I need you to either give me permissions to access the town "
                               "category, or temporarily grant me admin permissions and I can fix the rest.\n Once "
                               "you're done with that, you can type the same command again and I'll continue setting "
                               "everything up.")

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
    async def count(self, ctx):
        playing_role = discord.utils.get(ctx.guild.roles, name="Playing")
        playing_people_iterator = filter(lambda x: playing_role in x.roles, ctx.guild.members)
        await ctx.send(len(list(playing_people_iterator)))

    @commands.command()
    @is_admin()
    async def resetchannels(self, ctx):
        await self.removechannels(ctx)
        await self.addchannels(ctx)

    @commands.command()
    @is_admin()
    async def addchannels(self, ctx):
        with ctx.typing():  # This is where the fun begins
            x = models.channels.Channels.find_one({"server": ctx.guild.id})
            if x is not None:
                await ctx.send("You already have the channels set up.")
                return
            if not await self.create_channels(ctx.guild):
                await ctx.send("I did all that I could. I need you to either give me permissions to access the town "
                               "category, or temporarily grant me admin permissions and I can fix the rest.\n Once "
                               "you're done with that, you can type the same command again and I'll continue setting "
                               "everything up.")

    async def create_channels(self, guild):
        town_square_category = discord.utils.get(guild.categories,
                                                 name=files.channels_config["category-name"])
        if town_square_category is None:
            town_square_category = await self.create_category(guild)
            if town_square_category is None:  # admin permissions not given
                return False

        await self.hide_town_category(guild, town_square_category)

        channel_id_dict = dict()
        channel_id_dict["guild"] = guild.id
        for i in files.channels_config["channels"]:
            channel_message = '\n'.join(files.werewolfMessages["channel_messages"][i])
            channel = await guild.create_text_channel(name=i, category=town_square_category,
                                                      topic=channel_message)
            msg = await channel.send(channel_message)
            await msg.pin()
            channel_id_dict[i] = channel.id

        await self.unhide_town_category(guild, town_square_category)
        channels = models.channels.Channels.find_one({"server": guild.id})
        if channels is None:
            channels = models.channels.Channels({
                "server": guild.id,
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
                target = discord.utils.get(guild.roles, name=k)
                await ch.set_permissions(target, overwrite=discord.PermissionOverwrite(**l))
        return True

    async def unhide_town_category(self, guild, town_square_category):
        for i, j in files.channels_config["category-permissions"].items():
            target = discord.utils.get(guild.roles, name=i)
            await town_square_category.set_permissions(target, overwrite=discord.PermissionOverwrite(**j))

    async def create_category(self, guild):
        town_square_category = await guild.create_category_channel(files.channels_config["category-name"])
        bot_role = discord.utils.get(guild.me.roles, managed=True)
        permissions = files.readJsonFromConfig("permissions.json")
        bot_roles = guild.me.roles
        is_administrator = False
        for x in bot_roles:
            if x.permissions.administrator:
                is_administrator = True
                break
        if not is_administrator:
            return None
        await town_square_category.set_permissions(bot_role,
                                                   overwrite=discord.PermissionOverwrite(**permissions["manage"]))
        # This last line is why the bot needs admin powers for this part. It's assigning itself permissions to
        # manage the channel (it let's people die, assigns people to their special channels and keeps the game
        # running).
        return town_square_category

    async def hide_town_category(self, guild, town_square_category):
        for i in files.channels_config["category-permissions"]:
            target = discord.utils.get(guild.roles, name=i)
            permissions = files.readJsonFromConfig("permissions.json")
            await town_square_category.set_permissions(target,
                                                       overwrite=discord.PermissionOverwrite(**permissions["none"]))

    def cog_unload(self):
        return super().cog_unload()

    @commands.command()
    @is_admin()
    @decorators.is_no_game()
    async def removechannels(self, ctx):
        with ctx.typing():
            c = discord.utils.get(ctx.guild.categories,
                                  name=files.channels_config["category-name"])
            for i in c.channels:
                await i.delete()
            # await c.delete()

            channel = models.channels.Channels.find_one({"server": ctx.guild.id})
            if channel is not None:
                channel.remove()

    @commands.command()
    @is_admin()
    @decorators.is_no_game()
    async def changeday(self, ctx, time):
        if models.server.set_day(ctx.guild.id, time):
            await ctx.send(f"Time set to {time}")
        else:
            await ctx.send("Bad time format. Please try using the hh:mm 24h format.")

    @commands.command()
    @is_admin()
    @decorators.is_no_game()
    async def changenight(self, ctx, time):
        if models.server.set_night(ctx.guild.id, time):
            await ctx.send(f"Time set to {time}")
        else:
            await ctx.send("Bad time format. Please try using the hh:mm 24h format")

    @commands.command()
    @is_admin()
    @decorators.is_no_game()
    async def changewarning(self, ctx, minutes):
        if models.server.set_warning(ctx.guild.id, minutes):
            await ctx.send(f"Warning set to {minutes} before nighttime")
        else:
            await ctx.send("Please make sure the number isn't bigger than 180.")

    @commands.command()
    @is_admin()
    async def changeannouncement(self, ctx):
        server_document = models.server.Server.find_one({"server": ctx.guild.id})
        if "announce_character" not in server_document:
            server_document["announce_character"] = True
            server_document.save()
        server_document["announce_character"] = not server_document["announce_character"]
        server_document.save()
        await ctx.send(
            f"The narrator will now {'not ' if not server_document['announce_character'] else ''}announce the character roles.")

    @commands.command(**files.command_parameters['gettime'])
    async def gettime(self, ctx):
        server_document = models.server.Server.find_one({"server": ctx.guild.id})
        if server_document is None:
            server_document = models.server.Server({
                "server": ctx.guild.id
            })
            server_document.save()
        await ctx.send(f"Day time is at {server_document['daytime']}")
        await ctx.send(f"Night time is at {server_document['nighttime']}")
        await ctx.send(f"Warning happens {server_document['warning']} minutes before nighttime")
