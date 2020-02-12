from typing import Optional

from discord.ext import commands

from decorators import is_vote_channel
from files import command_parameters
from villager import Villager


class Election(commands.Cog):

    def __init__(self, bot, future, people, vote_leader=None, channel=None):
        self.__bot = bot
        self.__people: [Villager] = people
        self.__casted_votes = {}
        self.__voted = {}
        self.__locked = []
        self.__future = future
        self.__result = None
        self.__channel = channel
        self.__vote_leader = vote_leader
        for x in people:
            self.__casted_votes[x.Name] = 0

    @commands.command(**command_parameters['showleading'])
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

    @commands.command(**command_parameters['lock'])
    @is_vote_channel()
    async def lock(self, ctx):
        if str(ctx.message.author) not in self.__locked:
            if ctx.message.author.name not in self.__voted:
                await ctx.send("You haven't voted for someone yet. You can't lock a vote for no one.")
                return
            await ctx.send(f"You have locked your vote for {self.__voted[ctx.message.author.name]}")
            self.__locked.append(str(ctx.message.author))
            if len(self.__locked) == len(self.__people):
                if len(self.__Leading) > 1:
                    await ctx.send(f"The vote is tied between {' and '.join(self.__Leading)}.\n"
                                   f"You can still change your mind and unlock your vote with !unlock. "
                                   f"If nighttime falls and there is still a tie, no one will die.")
                else:
                    await ctx.send("Everyone locked their votes in. Ending vote")
                    self.stop_vote()
        else:
            await ctx.send("You've already locked your vote.")

    @commands.command(**command_parameters['unlock'])
    @is_vote_channel()
    async def unlock(self, ctx):
        if str(ctx.message.author) not in self.__locked:
            await ctx.send("You haven't locked your vote, so you can't unlock.")
        else:
            self.__locked.remove(str(ctx.message.author))
            await ctx.send("Vote has been unlocked.")

    @commands.command(**command_parameters['vote'])
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

    @commands.command(**command_parameters['showvote'])
    @is_vote_channel()
    async def showvote(self, ctx):
        voted_people = ""
        who_voted = {}
        for x in sorted(self.__voted, key=self.__casted_votes.get, reverse=True):
            person = self.__voted[x]
            if person not in who_voted:
                who_voted[person] = []
            who_voted[person].append(x)
            v = self.findCandidate(x)
            x_villager = self.findCandidate(person)
            # voted_people += "{} voted for {}\n".format(v.ProperName, x_villager.ProperName)
        for x in sorted(who_voted, key=self.__casted_votes.get, reverse=True):
            y = who_voted[x]
            voting_list = [self.findCandidate(a).ProperName for a in y]
            # if len(voting_list) > 1:
            #     voting_list[-1] = 'and ' + voting_list[-1]
            # voted_people += ', '.join(voting_list) + f' voted for {self.findCandidate(x).ProperName}\n'
            voted_people += f"{len(voting_list)} {'person' if len(voting_list) == 1 else 'people'} voted for {self.findCandidate(x).ProperName}"
            voted_people += "\n\t"
            voted_people += '\n\t'.join(voting_list) + '\n'
        if voted_people == "":
            await ctx.send("No one voted yet.")
        else:
            await ctx.send(voted_people)

    # @commands.command(**command_parameters['showscore'])
    # @is_vote_channel()
    # async def showscore(self, ctx):
    #     sorted_people = ""
    #     for x in sorted(self.__casted_votes, key=self.__casted_votes.get, reverse=True):
    #         v = self.findCandidate(x)
    #         sorted_people += "{}: {}\n".format(v.ProperName, self.__casted_votes[x])
    #     await ctx.send(sorted_people)

    def findCandidate(self, name: str) -> Optional[Villager]:
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
