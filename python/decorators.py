import discord
from discord.ext import commands


def is_admin():
    async def predicate(ctx):
        return ctx.channel == discord.utils.get(ctx.guild.channels, name="bot-admin")

    return commands.check(predicate)


def is_from_channel(channel_name: str):
    async def predicate(ctx):
        return ctx.channel == discord.utils.get(ctx.guild.channels, name=channel_name)

    return commands.check(predicate)
