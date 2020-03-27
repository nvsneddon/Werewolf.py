from typing import Optional

from discord.ext import commands

from decorators import is_vote_channel
from files import command_parameters
from villager import Villager
import models.election
import models.villager


class Election(commands.Cog):

    def __init__(self, bot, future, people, guild_id, channel=None):
        self.__bot = bot
        self.__people: [Villager] = people
        self.__casted_votes = {}
        self.__voted = {}
        self.__locked = []
        self.__future = future
        self.__result = None
        self.__channel = channel
        casted_votes = {}
        for x in people:
            self.__casted_votes[x.Name] = 0
            casted_votes[str(x.UserID)] = 0
        x = models.election.Election.find({
            "server": guild_id
        })
        models.election.delete_many({"server": guild_id})
        models.election.Election({
            "server": guild_id,
            "casted_votes": casted_votes,
            "people": [x.UserID for x in self.__people],
            "channel": channel.id
        }).save()

    @commands.command(**command_parameters['showleading'])
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
        db_election = models.election.Election.find_one({"server": ctx.guild.id})
        voter = str(ctx.message.author)
        if ctx.message.author.id not in db_election["locked"]:
            if ctx.message.author.name not in self.__voted:
                await ctx.send("You haven't voted for someone yet. You can't lock a vote for no one.")
                return
            await ctx.send(f"You have locked your vote for {self.__voted[ctx.message.author.name]}")
            db_election["locked"].append(ctx.message.author.id)
            vote_counts = {}
            for i in db_election["locked"]:
                votee = self.__voted[self.findCandidateId(i).Name]
                if votee in vote_counts:
                    vote_counts[votee] += 1
                else:
                    vote_counts[votee] = 1
            vote_counts_sorted_keys = sorted(vote_counts, key=vote_counts.get, reverse=True)
            votes = vote_counts[vote_counts_sorted_keys[0]]
            if votes > len(self.__casted_votes)/2:
                await ctx.send("Half of the people locked their votes for one person, so the voting will end now.")
                self.stop_vote()
            db_election.save()
        else:
            await ctx.send("You've already locked your vote.")


    @commands.command(**command_parameters['unlock'])
    @is_vote_channel()
    async def unlock(self, ctx):
        db_election = models.election.Election.find_one({"server": ctx.guild.id})
        if ctx.message.author.id not in db_election["locked"]:
            await ctx.send("You haven't locked your vote, so you can't unlock.")
        else:
            db_election["locked"].remove(ctx.message.author.id)
            await ctx.send("Vote has been unlocked.")
            db_election.save()

    @commands.command(**command_parameters['vote'])
    @is_vote_channel()
    async def vote(self, ctx, voteestring: str):
        db_election = models.election.Election.find_one({"server": ctx.guild.id})
        if ctx.message.author.id in db_election["locked"]:
            await ctx.send("You've already locked your vote")
            return
        # votee = self.findCandidate(voteestring)
        votee_id = self.getCandidateID(voteestring, ctx.guild.id)
        if votee_id == -1:
            await ctx.send("Couldn't find the candidate's name. Please make sure there was no typo with your answer.")
            return
        if str(votee_id) in db_election["casted_votes"]:
            voter_id = ctx.message.author.id
            if voter_id in db_election["voted"]:
                db_election["casted_votes"][str(db_election[str(voter_id)])] -= 1
            db_election["casted_votes"][str(votee_id)] += 1
            db_election["voted"][str(voter_id)] = votee_id
            votee = ctx.guild.get_member(votee_id)
            await ctx.send(f"Your vote for {votee.mention} has been confirmed")
            db_election.save()
        else:
            await ctx.send("You can't vote for that person. Please try again.")

    @commands.command(**command_parameters['showvote'])
    async def showvote(self, ctx):
        db_election = models.election.Election.find_one({"server": ctx.guild.id})
        voted_people = ""
        who_voted = {}
        for x in sorted(db_election['voted'], key=db_election["casted_votes"].get, reverse=True):
            person = db_election['voted'][str(x)]
            if person not in who_voted:
                who_voted[person] = []
            who_voted[person].append(x)
        for x in sorted(who_voted, key=db_election["casted_votes"].get, reverse=True):
            y = who_voted[x]
            voting_list = [ctx.guild.get_member(int(a)).display_name for a in y]
            voted_people += f"{len(voting_list)} {'person' if len(voting_list) == 1 else 'people'} voted for " \
                            f"{ctx.guild.get_member(x).display_name} "
            voted_people += "\n\t"
            voted_people += '\n\t'.join(voting_list) + '\n'
        if voted_people == "":
            await ctx.send("No one voted yet.")
        else:
            await ctx.send(voted_people)

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

    def getCandidateID(self, name: str, server_id: int) -> int:
        # if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
        #     name = name[3:-1]
        # elif name[0:2] == "<@":
        #     name = name[2:-1]
        people = models.villager.Villager.find({"server": server_id})
        for x in people:
            member = self.__bot.get_guild(server_id).get_member(x["discord_id"])
            if name.lower() == member.display_name.lower() or name.lower() == member.mention or name.lower() == member.name.lower() or name.lower() == str(member).lower():
                return member.id
        return -1


    def findCandidateId(self, id: int) -> Optional[Villager]:
        for x in self.__people:
            if x.UserID == id:
                return x
        return None

    @property
    def Locked(self):
        return self.__locked

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
