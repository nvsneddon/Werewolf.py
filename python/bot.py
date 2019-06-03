import discord
from discord.ext import commands
from game import Game
import asyncio
import os
import json
from cogstest import Test
from files import werewolfMessages, commandDescriptions, config, channels_config, roles_config

bot = commands.Bot(command_prefix='!')

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
    notplaying_role = discord.utils.get(ctx.guild.roles, name="Not Playing")
    if len(args) == 0:
        ctx.send("Please add game parameters to the game")
        return
    players = []
    for member in ctx.guild.members:
        if notplaying_role not in member.roles:
            players.append(str(member))
    if len(players) < sum(args):
        await ctx.send("You gave out too many roles for the number of people.")
        return
    bot.add_cog(Game(bot, players, args))

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
async def addroles(ctx):
    for i, j in roles_config["roles"].items():
        if discord.utils.get(ctx.guild.roles, name=i) is not None:
            continue
        permissionObject = discord.Permissions().none()
        permissionObject.update(**roles_config["general-permissions"])
        if j["permissions-update"] is not None:
            permissionObject.update(**j["permissions-update"])
        c = discord.Color.from_rgb(*j["color"])
        role = await ctx.guild.create_role(name = i, permissions = permissionObject, color = c)
        message = i + " role created"
        await ctx.send(message)

@bot.command()
@is_admin()
async def resetrolepermissions(ctx):
    for i, j in roles_config["roles"].items():
        role = discord.utils.get(ctx.guild.roles, name=i)
        if role is None:
            continue
        permissionObject = discord.Permissions().none()
        permissionObject.update(**roles_config["general-permissions"])
        if j["permissions-update"] is not None:
            permissionObject.update(**j["permissions-update"])
        await role.edit(permissions = permissionObject)
        message = i + " role permissions reset"
        await ctx.send(message)
        await ping(ctx)


@bot.command()
@is_admin()
async def testroles(ctx):
    roles = []
    roles.append(discord.utils.get(ctx.guild.roles, name="Not Playing"))
    roles.append(discord.utils.get(ctx.guild.roles, name="Playing"))
    roles.append(discord.utils.get(ctx.guild.roles, name="Dead"))
    roles.append(discord.utils.get(ctx.guild.roles, name="Alive"))
    roles.append(discord.utils.get(ctx.guild.roles, name="Mayor"))

    for i in range(len(roles)):
        for j in range(i+1, len(roles)):
            if roles[i].permissions == roles[j].permissions:
                print("These permissions are equal in these roles:", roles[i], roles[j])
            else:
                print("These permissions are not equal in these roles:", roles[i], roles[j])

@bot.command()
@is_admin()
async def addcategory(ctx):
    c = await ctx.guild.create_category_channel(channels_config["category-name"])
    for i, j in channels_config["category-permissions"].items():
        target = discord.utils.get(ctx.guild.roles, name=i)
        await c.set_permissions(target, overwrite=discord.PermissionOverwrite(**j))

    for i in channels_config["channels"]:
        await ctx.guild.create_text_channel(name = i, category = c)

    for i, j in channels_config["channel-permissions"].items():
        ch = discord.utils.get(c.channels, name=i)
        for k, l in j.items():
            target = discord.utils.get(ctx.guild.roles, name=k)
            await ch.set_permissions(target, overwrite=discord.PermissionOverwrite(**l))


@bot.command()
@is_admin()
async def removecategory(ctx):
    c = discord.utils.get(ctx.guild.categories, name=channels_config["category-name"])
    for i in c.channels:
        await i.delete()
    await c.delete()

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
    if name[0:3] == "<@!":
        return ctx.message.server.get_member(name[3:-1])
    elif name[0:2] == "<@":
        return ctx.message.server.get_member(name[2:-1])
    else:
        return ctx.message.server.get_member_named(name)


bot.run(config["token"])
