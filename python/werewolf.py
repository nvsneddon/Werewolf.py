import discord
from discord.ext import commands
from villager import Villager

class Werewolf(commands.Cog, Villager):

    @commands.check
    def is_werewolf():
        async def predicate(ctx):
            return ctx.channel == discord.utils.get(ctx.guild.channels, name="werewolf")
        return commands.check(predicate)

