from typing import Optional

from discord.ext import commands

import decorators
from files import command_parameters
import models.election
import models.villager

def is_vote(guild_id):
    db_election = models.election.Election.find_one({"server": str(guild_id)})
    return db_election is not None

def start_vote(channel, guild_id, people):
    casted_votes = {}
    for x in people:
        casted_votes[str(x)] = 0
    models.election.delete_many({"server": str(guild_id)})
    # models.villager.Villager.find({"server": str(guild_id)})
    models.villager.Villager.find({"server": str(guild_id)})
    models.election.Election({
        "server": str(guild_id),
        "casted_votes": casted_votes,
        "people": people,
        "channel": str(channel.id)
    }).save()


class Election(commands.Cog):

    def __init__(self, bot):
        self.__bot = bot

    @commands.command(**command_parameters['showleading'])
    @decorators.is_election()
    async def showleading(self, ctx):
        if len(self.__get_leading(ctx.guild.id)) == 0:
            await ctx.send("No vote has been cast yet. No one is in the lead.")
            return
        message = f"The leading {'person is' if len(self.__get_leading(ctx.guild.id)) < 2 else 'people are:'}"
        message += '\n' + '\n'.join(self.__get_leading(ctx.guild.id))
        await ctx.send(message)

    # TODO Figure out how to get the guild_id at nighttime
    def stop_vote(self, guild_id):
        leading = self.__get_leading(guild_id)
        models.election.delete_many({"server": str(guild_id)})
        return leading

    @commands.command(**command_parameters['lock'])
    @decorators.is_vote_channel()
    @decorators.is_election()
    async def lock(self, ctx):
        db_election = models.election.Election.find_one({"server": str(ctx.guild.id)})
        # voter = str(ctx.message.author)
        if str(ctx.message.author.id) not in db_election["locked"]:
            if str(ctx.message.author.id) not in db_election["voted"]:
                await ctx.send("You haven't voted for someone yet. You can't lock a vote for no one.")
                return
            id_voted_for = db_election['voted'][str(ctx.message.author.id)]
            await ctx.send(f"You have locked your vote for {ctx.guild.get_member(id_voted_for).display_name}")
            db_election["locked"].append(str(ctx.message.author.id))
            vote_counts = {}
            for i in db_election["locked"]:
                votee = db_election['voted'][i]
                if votee in vote_counts:
                    vote_counts[votee] += 1
                else:
                    vote_counts[votee] = 1
            vote_counts_sorted_keys = sorted(vote_counts, key=vote_counts.get, reverse=True)
            votes = vote_counts[vote_counts_sorted_keys[0]]
            db_election.save()
            if votes > len(db_election["casted_votes"])/2:
                await ctx.send("Half of the people locked their votes for one person, so the voting will end now.")
                cog = self.__bot.get_cog("Game")
                await cog.stopvote(ctx.guild)
        else:
            await ctx.send("You've already locked your vote.")


    @commands.command(**command_parameters['unlock'])
    @decorators.is_vote_channel()
    @decorators.is_election()
    async def unlock(self, ctx):
        db_election = models.election.Election.find_one({"server": str(ctx.guild.id)})
        if str(ctx.message.author.id) not in db_election["locked"]:
            await ctx.send("You haven't locked your vote, so you can't unlock.")
        else:
            db_election["locked"].remove(str(ctx.message.author.id))
            await ctx.send("Vote has been unlocked.")
            db_election.save()

    @commands.command(**command_parameters['vote'])
    @decorators.is_vote_channel()
    @decorators.is_election()
    async def vote(self, ctx, voteestring: str):
        db_election = models.election.Election.find_one({"server": str(ctx.guild.id)})
        if str(ctx.message.author.id) in db_election["locked"]:
            await ctx.send("You've already locked your vote")
            return
        # votee = self.findCandidate(voteestring)
        votee_id = self.getCandidateID(voteestring, ctx.guild.id)
        if votee_id == -1:
            await ctx.send("Couldn't find the candidate's name. Please make sure there was no typo with your answer.")
            return
        if str(votee_id) in db_election["casted_votes"]:
            voter_id = ctx.message.author.id
            if str(voter_id) in db_election["voted"]:
                db_election["casted_votes"][str(db_election["voted"][str(voter_id)])] -= 1
            db_election["casted_votes"][str(votee_id)] += 1
            db_election["voted"][str(voter_id)] = votee_id
            votee = ctx.guild.get_member(votee_id)
            await ctx.send(f"Your vote for {votee.mention} has been confirmed")
            db_election.save()
        else:
            await ctx.send("You can't vote for that person. Please try again.")

    @commands.command(**command_parameters['showvote'])
    @decorators.is_election()
    async def showvote(self, ctx):
        db_election = models.election.Election.find_one({"server": str(ctx.guild.id)})
        voted_people = ""
        who_voted = {}
        for x in sorted(db_election['voted'], key=db_election["casted_votes"].get, reverse=True):
            person = db_election['voted'][str(x)]
            if person not in who_voted:
                who_voted[person] = []
            who_voted[person].append(x)
        # db_election["casted_votes"].get
        for x in sorted(who_voted, key=lambda x: db_election["casted_votes"].get(str(x)), reverse=True):
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

    def getCandidateID(self, name: str, server_id: int) -> int:
        people = models.villager.Villager.find({"server": server_id})
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            name = name[3:-1]
        elif name[0:2] == "<@":
            name = name[2:-1]
        for x in people:
            member = self.__bot.get_guild(server_id).get_member(x["discord_id"])
            if name.lower() == member.display_name.lower() or str(member.id) == name or name.lower() == member.name.lower() or name.lower() == str(member).lower():
                return member.id
        return -1

    def __get_leading(self, guild_id):
        db_election = models.election.Election.find_one({"server": str(guild_id)})
        max_tally = 0
        leading = []
        for id, votes in db_election["casted_votes"].items():
            id = int(id)
            if votes == 0:
                continue
            if max_tally < votes:
                v = self.__bot.get_guild(guild_id).get_member(id)
                leading = [v.mention]
                max_tally = votes
            elif max_tally == votes:
                v = self.__bot.get_guild(guild_id).get_member(id)
                leading.append(v.mention)
        return leading

