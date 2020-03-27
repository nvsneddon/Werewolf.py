import discord
from discord.ext import commands

from villager import Villager


def is_admin():
    async def predicate(ctx):
        return ctx.channel == discord.utils.get(ctx.guild.channels, name="bot-admin")

    return commands.check(predicate)


def is_vote_channel():
    async def predicate(ctx):
        cog = ctx.bot.get_cog("Election")
        if cog.VoteChannel is None:
            return True
        return cog.VoteChannel == ctx.channel

    return commands.check(predicate)


def is_from_channel(channel_name: str):
    async def predicate(ctx):
        return ctx.channel == discord.utils.get(ctx.guild.channels, name=channel_name)

    return commands.check(predicate)


def is_character(character_name: str):
    async def predicate(ctx):
        cog = ctx.bot.get_cog("Game")
        v: Villager = cog.findVillager(str(ctx.author))
        return v.Character == character_name

    return commands.check(predicate)


def is_not_character(character_name: str):
    async def predicate(ctx):
        cog = ctx.bot.get_cog("Game")
        v: Villager = cog.findVillager(str(ctx.author))
        return v.Character != character_name

    return commands.check(predicate)


def has_ability(character_name: str):
    def predicate(ctx):
        cog = ctx.bot.get_cog("Game")
        return cog.Abilities.check_ability(character_name)

    return commands.check(predicate)


def findPerson(ctx, *args):
    if len(args) == 1:
        if type(args[0]) is str:
            name = args[0]
        else:
            name = " ".join(args[0])
    else:
        print("Something went very wrong. Args is not of length 1")
        return None
    if name[0:3] == "<@!":
        return ctx.guild.get_member(int(name[3:-1]))
    elif name[0:2] == "<@":
        return ctx.guild.get_member(int(name[2:-1]))
    else:
        return ctx.guild.get_member_named(name)
