import discord
from discord.ext import commands
#from game import Game
import asyncio
import os
import json
#from cogstest import Test

werewolfGame = None
werewolfMessages = None
commandDescriptions = None

dirname = os.path.dirname(__file__)
try:
    f = open(os.path.join(dirname, '../config/messages.json'))
    werewolfMessages = json.loads(f.read())
    f.close()
    f2 = open(os.path.join(dirname, "../config/command_descriptions.json"))
    commandDescriptions = json.loads(f2.read())
    f2.close()
except FileNotFoundError:
    print("Please make sure the messages.json and the command_descriptions.json files are in the config folder and try again.")
    exit()

try:
    f3 = open(os.path.join(dirname, "../config/discord-config.json"))
    config = json.loads(f3.read())
    f3.close()
except FileNotFoundError:
    print("The config file was not found. Please make sure the discord-config.py file is in the config folder. Please refer to the README for more information.")
    exit()

bot = commands.Bot(command_prefix='!')
special_channels = config["channels"]

def is_admin():
    async def predicate(ctx):
        return ctx.channel.id == config["channels"]["bot-admin"]
    return commands.check(predicate)

def has_role(r):
    async def predicate(ctx):
        return r in ctx.author.roles
    return commands.check(predicate)

@bot.event
async def on_ready():
    print("The werewolves are howling!")


@bot.command()
async def echo(ctx, *args):
    output = ''
    for x in args:
        output += x
        output += ' '
    await ctx.send(output)


@bot.command()
async def ping(ctx):
    await ctx.send(":ping_pong: Pong!")



@bot.command(pass_context=True)
async def startgame(ctx, *args: int):
    """server = ctx.message.server
    global werewolfGame
    notplaying_role = discord.utils.get(server.roles, name="Not Playing")
    #alive_role = discord.utils.get(server.roles, name="Alive")

    players = []
    for member in server.members:
        if notplaying_role not in member.roles:
            players.append(str(member))
    try:
        werewolfGame = Game(players, args)
    except ValueError:
        await ctx.send("You gave out too many roles for the game!")"""
    pass


@bot.command(pass_context=True)
async def clear(ctx, number=10):
    if (discord.utils.get(ctx.message.author.roles, name="Owner") is None) and (ctx.message.author != findPerson(ctx, "keyclimber")):
        await ctx.send("You don't have permission to do this!")
        return
    # Converting the amount of messages to delete to an integer
    number = int(number+1)
    counter = 0
    async for x in bot.logs_from(ctx.message.channel, limit=number):
        if counter < number:
            if x.pinned:
                continue
            await bot.delete_message(x)
            counter += 1
            
async def resetPermissions(ctx, member, channel=""):
    #alive_role = discord.utils.get(ctx.message.server.roles, name="Alive")
    #dead_role = discord.utils.get(ctx.message.server.roles, name="Dead")
    #mayor_role = discord.utils.get(ctx.message.server.roles, name="Mayor")
    playing_role = discord.utils.get(ctx.message.server.roles, name="Playing")
    await bot.replace_roles(member, playing_role)
    await bot.delete_channel_permissions(discord.utils.get(ctx.message.server.channels, name="lovebirds"), member)
    if channel != "" and channel in special_channels:
        await bot.delete_channel_permissions(discord.utils.get(ctx.message.server.channels, name=channel), member)
    """else:
        for x in special_channels:
            await bot.delete_channel_permissions(ctx.message.server.get_channel(special_channels[x]), member)"""

@bot.command()
@is_admin()
async def exit(ctx):
    await ctx.send("Goodbye!")
    await bot.logout()

@exit.error
async def exit_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("I'm sorry, but you cannot shut me down!")

@bot.command()
@is_admin()
async def addrole(ctx):
    permissionObject = discord.Permissions()
    up = {
        "read_messages": True,
        "send_messages": True
    }
    permissionObject.update(**up)
    c = discord.Color.red()
    await ctx.guild.create_role(name = "Test role", permissions = permissionObject, color = c)
    await ctx.send("I think it worked!")

def findPerson(ctx, *args):
    if len(args) == 1:
        if type(args[0]) is str:
            name = args[0]
        else:
            name = " ".join(args[0])
        return name
    else:
        print("Something went very wrong. Args is not of length 1")
        return None




bot.run(config["token"])
