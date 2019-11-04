from villager import Villager

import discord
import asyncio
from discord.ext import commands


class Election(commands.Cog):

    # __people: List[Villager]

    def __init__(self, bot, future):
        self.__bot = bot
        self.__casted_votes = {}
        self.__voted = ()
        self.__future = future
        self.__result = None

    @commands.command()
    async def vote(self, ctx, res):
        self.__future.set_result(res)

