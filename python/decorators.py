import discord
from discord.ext import commands

import models.game
import models.election
import models.villager
import abilities


def is_admin():
    async def predicate(ctx):
        return ctx.channel == discord.utils.get(ctx.guild.channels, name="bot-admin")

    return commands.check(predicate)


def is_from_channel(channel_name: str):
    async def predicate(ctx):
        return ctx.channel == discord.utils.get(ctx.guild.channels, name=channel_name)

    return commands.check(predicate)


def is_character(character_name: str):
    def predicate(ctx):
        v = models.villager.Villager.find_one({
            "discord_id": ctx.author.id,
            "server": ctx.guild.id
        })
        return v["character"] == character_name

    return commands.check(predicate)


def is_not_character(character_name: str):
    def predicate(ctx):
        v = models.villager.Villager.find_one({
            "discord_id": ctx.author.id,
            "server": ctx.guild.id
        })
        return v["character"] != character_name

    return commands.check(predicate)


def has_ability(character_name: str):
    def predicate(ctx):
        return abilities.check_ability(character=character_name, guild_id=ctx.guild.id)

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


def is_vote_channel():
    def predicate(ctx):
        election_document = models.election.Election.find_one({
            "server": ctx.guild.id
        })
        if election_document is None:
            return False
        return election_document["channel"] == ctx.channel.id

    return commands.check(predicate)


def is_election():
    def predicate(ctx):
        election_document = models.election.Election.find_one({
            "server": ctx.guild.id
        })
        return election_document is not None

    return commands.check(predicate)


def is_game():
    def predicate(ctx):
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        return game_document is not None

    return commands.check(predicate)


def is_no_game():
    def predicate(ctx):
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        return game_document is None

    return commands.check(predicate)


def hunter():
    def predicate(ctx):
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        if game_document is None:
            return False

        return ctx.message.author.id in game_document["hunter_ids"]

    return commands.check(predicate)
