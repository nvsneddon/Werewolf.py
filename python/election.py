from typing import Optional

from decorators import is_admin
from villager import Villager

import discord
import asyncio
from discord.ext import commands


class Election(commands.Cog):

    def __init__(self, bot, future, people):
        self.__bot = bot
        self.__people: [Villager] = people
        self.__casted_votes = {}
        self.__voted = {}
        self.__future = future
        self.__result = None
        for x in people:
            self.__casted_votes[x.Name] = 0

    @commands.command()
    async def endvote(self, ctx):
        self.stop_vote()

    @commands.command()
    async def getleading(self, ctx):
        if len(self.__Leading) == 0:
            await ctx.send("No vote has been cast yet. No one is in the lead.")
            return
        message = f"The leading {'person is' if len(self.__Leading) < 2 else 'people are:'}"
        message += '\n' + '\n'.join(self.__Leading)
        await ctx.send(message)

    def stop_vote(self):
        self.__future.set_result(self.__Leading)

    @property
    def __Leading(self):
        maxTally = 0
        leading = []
        for name, votes in self.__casted_votes.items():
            if votes == 0:
                continue
            if maxTally < votes:
                leading = [name]
                maxTally = votes
            elif maxTally == votes:
                leading.append(name)
        return leading

    @property
    def __VoteNumber(self):
        return len(self.__voted)

    @commands.command()
    @is_admin()
    async def cancelvote(self, ctx):
        self.__future.set_result("cancel")

    @commands.command(aliases=["castvote"])
    async def vote(self, ctx, voteestring: str):
        votee = self.findCandidate(voteestring)
        if votee is None:
            await ctx.send("Couldn't find the candidate's name. Please make sure there was no typo with your answer.")
            return
        if votee.Name in self.__casted_votes:
            voter_name = ctx.message.author.name
            if voter_name in self.__voted:
                self.__casted_votes[self.__voted[voter_name]] -= 1
            self.__casted_votes[votee.Name] += 1
            self.__voted[voter_name] = votee.Name
            await ctx.send("Your vote for {} has been confirmed".format(voteestring))
        else:
            await ctx.send("You can't vote for that person. Please try again.")

    @commands.command(aliases=["show_score"])
    async def showscore(self, ctx):
        sorted_people = ""
        for x in sorted(self.__casted_votes, key=self.__casted_votes.get, reverse=True):
            sorted_people += "{}: {}\n".format(x, self.__casted_votes[x])
        await ctx.send(sorted_people)

    def findCandidate(self, name: str) -> Optional[Villager]:
        print(name)
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            name = name[3:-1]
        elif name[0:2] == "<@":
            name = name[2:-1]
        for x in self.__people:
            print(x)
            if x.Name.lower() == name.lower() or str(x.UserID) == name.lower():
                return x
        return None

