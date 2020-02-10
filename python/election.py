from typing import Optional

from discord.ext import commands

from decorators import is_vote_leader, is_vote_channel
from villager import Villager


class Election(commands.Cog):

    def __init__(self, bot, future, people, voteleader=None, channel=None):
        self.__bot = bot
        self.__people: [Villager] = people
        self.__casted_votes = {}
        self.__voted = {}
        self.__locked = []
        self.__future = future
        self.__result = None
        self.__channel = channel
        self.__vote_leader = voteleader
        print(self.__channel, "is the channel")
        for x in people:
            self.__casted_votes[x.Name] = 0

    # @commands.command()
    # @is_vote_leader()
    # @is_vote_channel()
    # async def endvote(self, ctx):
    #     self.stop_vote()

    @commands.command()
    @is_vote_channel()
    async def showleading(self, ctx):
        if len(self.__Leading) == 0:
            await ctx.send("No vote has been cast yet. No one is in the lead.")
            return
        message = f"The leading {'person is' if len(self.__Leading) < 2 else 'people are:'}"
        message += '\n' + '\n'.join(self.__Leading)
        await ctx.send(message)

    def stop_vote(self):
        self.__future.set_result(self.__Leading)

    @commands.command()
    @is_vote_channel()
    async def lock(self, ctx):
        if str(ctx.message.author) not in self.__locked:
            await ctx.send(f"You have locked your vote for {self.__voted[ctx.message.author.name]}")
            self.__locked.append(str(ctx.message.author))
            if len(self.__locked) == len(self.__people):
                await ctx.send("Everyone locked their votes in. Ending vote")
                self.stop_vote()

    # @commands.command()
    # @is_vote_leader()
    # @is_vote_channel()
    # async def cancelvote(self, ctx):
    #     self.__future.set_result("cancel")

    @commands.command(aliases=["castvote"])
    @is_vote_channel()
    async def vote(self, ctx, voteestring: str):
        if str(ctx.message.author) in self.__locked:
            await ctx.send("You've already locked your vote")
            return
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
            await ctx.send(f"Your vote for {votee.Mention} has been confirmed")
        else:
            await ctx.send("You can't vote for that person. Please try again.")

    @commands.command()
    @is_vote_channel()
    async def showvote(self, ctx):
        voted_people = ""
        for x in sorted(self.__voted, key=self.__voted.get):
            v = self.findCandidate(x)
            x_villager = self.findCandidate(self.__voted[x])
            voted_people += "{} voted for {}\n".format(v.ProperName, x_villager.ProperName)
        await ctx.send(voted_people)

    @commands.command(aliases=["show_score"])
    @is_vote_channel()
    async def showscore(self, ctx):
        sorted_people = ""
        for x in sorted(self.__casted_votes, key=self.__casted_votes.get, reverse=True):
            v = self.findCandidate(x)
            sorted_people += "{}: {}\n".format(v.ProperName, self.__casted_votes[x])
        await ctx.send(sorted_people)

    def findCandidate(self, name: str) -> Optional[Villager]:
        print(name)
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            name = name[3:-1]
        elif name[0:2] == "<@":
            name = name[2:-1]
        for x in self.__people:
            if x.Name.lower() == name.lower() or str(
                    x.UserID).lower() == name.lower() or x.DiscordTag.lower() == name.lower() or x.NickName.lower() == name.lower():
                return x
        return None

    @property
    def VoteLeader(self):
        return self.__vote_leader

    @property
    def VoteChannel(self):
        return self.__channel

    @property
    def __Leading(self):
        max_tally = 0
        leading = []
        for name, votes in self.__casted_votes.items():
            if votes == 0:
                continue
            if max_tally < votes:
                v = self.findCandidate(name)
                leading = [v.Mention]
                max_tally = votes
            elif max_tally == votes:
                v = self.findCandidate(name)
                leading.append(v.Mention)
        return leading

    @property
    def __VoteNumber(self):
        return len(self.__voted)