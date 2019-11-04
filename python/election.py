from villager import Villager

import discord
import asyncio
from discord.ext import commands


class Election(commands.Cog):


    def __init__(self, bot, future, people):
        self.__bot = bot
        self.__casted_votes = {}
        self.__voted = ()
        self.__future = future
        self.__result = None
        for x in people:
            self.__casted_votes[x] = 0

    async def endvote(self, ctx):
        self.__future.set_result("filler")

    @property
    def __Leading(self):
        maxTally = 0
        leading = []
        for name, votes in self.__casted_votes.items():
            if maxTally < votes:
                leading = [name]
                maxTally = votes
            elif maxTally == votes:
                leading.append(name)
        return leading

    @property
    def __VoteNumber(self):
        return len(self.__voted)

    @property
    def __Sorted(self):
        return sorted(self.__casted_votes, key=self.__casted_votes.get, reverse=True)

    @commands.command(alias=["castvote"])
    async def vote(self, ctx, person: str):
        if person in self.__casted_votes:
            pass
        else:
            await ctx.send("You can't vote for that person. Please try again.")

    @commands.command(alias=["leading"])
    async def leaders(self):
        return self.__Leading

