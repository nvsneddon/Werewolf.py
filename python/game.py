import datetime
import random
import threading
import time
import typing
import sys

import discord
import schedule
from discord.ext import commands

import decorators
import election
import files
import models.channels
import models.villager
import models.election
import models.server
import models.game

import abilities


async def declare_winner(bot, winner, guild_id):
    announcements_id = models.channels.getChannelId("announcements", guild_id)
    announcements_channel = bot.get_channel(announcements_id)
    if winner == "werewolves":
        await announcements_channel.send("Werewolves outnumber the villagers. Werewolves won.")
    elif winner == "villagers":
        await announcements_channel.send("All werewolves are now dead. Villagers win!")
    elif winner == "cupid":
        await announcements_channel.send("Cupid did a great job. The last two people alive are the love birds.")
    elif winner == "bakerdead":
        await announcements_channel.send("Everyone has starved. The werewolves survive off of villagers' corpses "
                                         "and win the game.")

def distribute_roles(roles):
    cards = []
    if len(roles) >= 7:
        cards += roles[6] * ["mason"]
    if len(roles) >= 6:
        cards += roles[5] * ["baker"]
    if len(roles) >= 5:
        cards += roles[4] * ["hunter"]
    if len(roles) >= 4:
        cards += roles[3] * ["cupid"]
    if len(roles) >= 3:
        cards += roles[2] * ["bodyguard"]
    if len(roles) >= 2:
        cards += roles[1] * ["seer"]
    if len(roles) >= 1:
        cards += roles[0] * ["werewolf"]
    return cards


class Game(commands.Cog):

    def __init__(self, bot):
        self.__bot = bot
        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()
        self.__bot.add_cog(election.Election(self.__bot))

        # self.schedule_day_and_night(guild_id)
        # self.initialize_game(guild_id, members, randomshuffle, roles, send_message_flag)

    async def die_from_db(self, villager_id: int, guild_id: int, leaving=False):
        v = models.villager.Villager.find_one({
            "server": guild_id,
            "discord_id": villager_id
        })
        game_document = models.game.Game.find_one({
            "server": guild_id
        })
        guild = self.__bot.get_guild(guild_id)
        if v["werewolf"]:
            game_document["werewolfcount"] -= 1
        else:
            game_document["villagercount"] -= 1
        game_document.save()
        if v["character"] == "hunter" and not leaving:
            game_document["hunter_ids"].append(v["discord_id"])
            game_document.save()
            return
        if v["character"] == "baker":
            game_document["bakerdead"] = True
            villagers = models.villager.Villager.find({
                "server": guild_id
            })
            for v in villagers:
                if v["alive"] and not v["werewolf"] and v["discord_id"] != villager_id:
                    game_document["starving"].append(v["discord_id"])
        game_document.save()

        await self.die(guild, villager_id)
        await self.__announce_winner(guild_id)


    async def die(self, guild, villager_id):
        game_document = models.game.Game.find_one({
            "server": guild.id
        })
        v = models.villager.Villager.find_one({
            "server": guild.id,
            "discord_id": villager_id
        })
        if v["discord_id"] in game_document["inlove"]:
            game_document["inlove"].remove(v["discord_id"])
            other_id: int = game_document["inlove"][0]
            game_document["inlove"].remove(other_id)
            game_document.save()
            town_square_id = models.channels.getChannelId("announcements", guild.id)
            town_square_channel = guild.get_channel(town_square_id)
            other_member = guild.get_member(other_id)
            other_document = models.villager.Villager.find_one({
                "server": guild.id,
                "discord_id": other_id
            })
            await town_square_channel.send(
                files.werewolfMessages[other_document["character"]]["inlove"].format(other_member.mention))
            await self.die_from_db(other_id, guild.id)
        v["alive"] = False
        v.save()
        game_document.save()
        member = guild.get_member(v["discord_id"])
        dead_role = discord.utils.get(guild.roles, name="Dead")
        for x in files.channels_config["channels"]:
            if x == "announcements":
                continue
            channel = guild.get_channel(models.channels.getChannelId(x, guild.id))
            await channel.set_permissions(member, overwrite=None)
        await member.edit(roles=[dead_role])

    @commands.command(**files.command_parameters["startgame"])
    @decorators.is_admin()
    @decorators.is_no_game()
    async def startgame(self, ctx, *args: int):
        with ctx.typing():
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            playing_role = discord.utils.get(ctx.guild.roles, name="Playing")
            if len(args) == 0:
                await ctx.send("Please add game parameters to the game")
                return
            players = []
            for member in ctx.guild.members:
                if playing_role in member.roles:
                    players.append(member)
            if len(players) < sum(args):
                await ctx.send("You gave out too many roles for the number of people. Please try again.")
                return
            for player in players:
                await player.edit(roles=[alive_role])
            nighttime = self.schedule_day_and_night(ctx.guild.id)
            self.initialize_game(ctx.guild.id, players, randomshuffle=True, roles=args, send_message_flag=files.send_message_flag)
            read_write_permission = files.readJsonFromConfig("permissions.json")["read_write"]
            for x in players:
                v_model = models.villager.Villager.find_one({
                    "server": ctx.guild.id,
                    "discord_id": x.id
                })
                character = v_model["character"]
                if character in files.channels_config["character-to-channel"]:
                    channel_name = files.channels_config["character-to-channel"][character]
                    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                    await channel.set_permissions(x, overwrite=discord.PermissionOverwrite(**read_write_permission))

        announcements_id = models.channels.getChannelId("announcements", ctx.guild.id)
        announcements_channel = self.__bot.get_channel(announcements_id)
        await announcements_channel.send("Let the games begin!")
        await announcements_channel.send(f"It is {'nighttime' if nighttime else 'daytime'}")
        await ctx.send("The game has started!")

    async def finishGame(self, guild):
        playing_role = discord.utils.get(
            guild.roles, name="Playing")

        villagers = models.villager.Villager.find({"server": guild.id})
        for v in villagers:
            member = guild.get_member(v["discord_id"])

            await member.edit(roles=[playing_role])
            for x in files.channels_config["channels"]:
                if x == "announcements":
                    continue
                channel = discord.utils.get(guild.channels, name=x)
                await channel.set_permissions(member, overwrite=None)
            v.remove()
        models.game.delete_many({"server": guild.id})
        models.election.delete_many({"server": guild.id})
        abilities.finish_game(guild.id)
        self.clear_schedule(str(guild.id))


    async def __announce_winner(self, guild_id):
        game = models.game.Game.find_one({ "server": guild_id })
        if game is None:
            print("No game found to announce winner. Please try again")
            return
        announcements_id = models.channels.getChannelId("announcements", guild_id)
        announcements_channel = self.__bot.get_channel(announcements_id)
        guild = self.__bot.get_guild(guild_id)
        if self.__cupidwinner(guild_id, game["inlove"]):
            await announcements_channel.send("The only alive people left are the two people in love. Cupid wins.")
            with announcements_channel.typing():
                await self.finishGame(guild)
            await announcements_channel.send("The game has ended!")
        elif game["werewolfcount"] > game["villagercount"]:
            await announcements_channel.send("Werewolves outnumber the villagers. Werewolves win")
            with announcements_channel.typing():
                await self.finishGame(guild)
            await announcements_channel.send("The game has ended!")
        elif game["werewolfcount"] == 0:
            await announcements_channel.send("All werewolves are dead. Villagers win!")
            with announcements_channel.typing():
                await self.finishGame(guild)
            await announcements_channel.send("The game has ended!")

    def __cupidwinner(self, guild_id, love):
        villagers = models.villager.Villager.find({
            "server": guild_id,
            "alive": True
        })
        for v in villagers:
            if v["discord_id"] not in love:
                return False
        return True

    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)

    def initialize_game(self, guild_id, members, randomshuffle, roles, send_message_flag):
        num_werewolves = 0
        num_villagers = 0
        num_players = 0
        players = []
        afterlife_message = ""
        cards = distribute_roles(roles)
        if len(members) > len(cards):
            cards += (len(members) - len(cards)) * ["villager"]
        if randomshuffle:
            random.shuffle(cards)
        for x in members:
            # y = villager.Villager(str(x), cards[0], x.id, x.nick, server=guild_id)
            models.villager.delete_many({
                "discord_id": x.id,
                "server": guild_id,
            })
            character = cards[0]
            is_bad = files.isBad(character)
            v = models.villager.Villager({
                "discord_id": x.id,
                "server": guild_id,
                "character": character,
                "werewolf": files.isBad(character)
            })
            v.save()
            if is_bad:
                num_werewolves += 1
            else:
                num_villagers += 1
            num_players += 1
            players.append(id)
            afterlife_message += f"{x.mention} is a {character}\n"
            cards.pop(0)
            message = '\n'.join(files.werewolfMessages[character]["welcome"])
            if send_message_flag:
                self.__bot.loop.create_task(self.__sendPM(x, message))
        models.game.delete_many({"server": guild_id})
        game_object = models.game.Game({
            "server": guild_id,
            "players": [x.id for x in members],
            "werewolfcount": num_werewolves,
            "villagercount": num_villagers
        })
        game_object.save()
        self.__bot.loop.create_task(self.__afterlife_message(afterlife_message, guild_id))

    def schedule_day_and_night(self, guild_id, reschedule=False):
        server_document = models.server.Server.find_one({
            "server": guild_id
        })
        schedule.every().day.at(server_document["daytime"]).do(self.daytime, guild_id).tag("game", str(guild_id), str(guild_id) + "daytime")
        warn_voting_time = datetime.datetime(10, 1, 2, int(
            server_document['nighttime'][:2]), int(server_document['nighttime'][3:5])) - \
                           datetime.timedelta(minutes=server_document['warning'])
        warn_voting_time_string = f"{warn_voting_time.hour:02d}:{warn_voting_time.minute:02d}"
        schedule.every().day.at(warn_voting_time_string).do(self.almostnighttime, guild_id).tag("game", str(guild_id) + "warning")
        schedule.every().day.at(server_document["nighttime"]).do(self.nighttime, guild_id).tag("game",
                                                                                                     str(guild_id) + "nighttime")
        night_array = server_document["nighttime"].split(':')
        day_array = server_document["daytime"].split(':')
        check_time = datetime.datetime.now().time()
        daytime_time = datetime.time(int(day_array[0]), int(day_array[1]))
        nighttime_time = datetime.time(int(night_array[0]), int(night_array[1]))
        is_nighttime = not (daytime_time <= check_time <= nighttime_time)
        if daytime_time > nighttime_time: # If daytime is bigger, that means that being between the values means
                                          # that it's nighttime
            is_nighttime = not is_nighttime
        if not reschedule:
            abilities.start_game(guild_id, night=is_nighttime)
        return is_nighttime

    async def __afterlife_message(self, message, guild_id):
        afterlife_id = models.channels.getChannelId("afterlife", guild_id)
        afterlife_channel = self.__bot.get_channel(afterlife_id)
        await afterlife_channel.send(message)
        async for x in (afterlife_channel.history(limit=1)):
            await x.pin()

    async def __sendPM(self, member, message):
        await member.send(message)

    @commands.command()
    @decorators.is_admin()
    async def endgame(self, ctx):
        with ctx.typing():
            await self.finishGame(ctx.guild)
            await ctx.send("Game has ended")

    @commands.command(**files.command_parameters['kill'])
    @decorators.is_from_channel("werewolves")
    @decorators.is_game()
    async def kill(self, ctx, person_name):
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        if game_document is None:
            ctx.send("There's no game right now. You can't kill yet.")
            return
        if not abilities.check_ability("werewolves", ctx.guild.id):
            await ctx.send("You already killed. Get some rest and don't get caught.")
            return
        target = self.findMember(name=person_name, guild_id=ctx.guild.id)
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        target_document = models.villager.Villager.find_one({
            "discord_id": target.id,
            "server": ctx.guild.id
        })
        if target.id in game_document["hunter_ids"]:
            await ctx.send("You can't kill the hunter after the hunter has already been killed. "
                           "The hunter will die when he shoots. Don't worry!")
            return
        if target_document is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        abilities.use_ability("werewolves", ctx.guild.id)
        if target.id == game_document["protected"]:
            await ctx.send("That person has been protected. You just wasted your kill!")
            announcement_id = models.channels.getChannelId("announcements", ctx.guild.id)
            announcements_channel = ctx.guild.get_channel(announcement_id)
            await announcements_channel.send(
                f"The werewolves have tried to kill {target.mention} who was protected. We're glad you're alive.")
        else:
            await ctx.send("Killing {}".format(target.mention))
            game_document["dying_villager_id"] = target.id
            game_document.save()


    async def announce_dead(self, guild):
        game_document = models.game.Game.find_one({"server": guild.id})
        target_id = game_document["dying_villager_id"]
        target_document = models.villager.Villager.find_one({
            "discord_id": target_id,
            "server": guild.id
        })
        target = guild.get_member(target_id)
        announcement_id = models.channels.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcement_id)
        await announcements_channel.send(
            files.werewolfMessages[target_document["character"]]["killed"].format(target.mention))
        game_document["dying_villager_id"] = -1
        game_document.save()
        await self.die_from_db(target_id, guild.id)

    @commands.command(**files.command_parameters['countpeople'])
    async def countpeople(self, ctx):

        game = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        if game is None:
            await ctx.send("You don't have a game going on!")
        else:
            await ctx.send(f"Villagers: {game['villagercount']}\nWerewolves: {game['werewolfcount']}")

    @commands.command(aliases=['daytime'])
    @decorators.is_admin()
    @decorators.is_game()
    async def day(self, ctx):
        self.daytime(ctx.guild.id)

    @commands.command(aliases=['nighttime'])
    @decorators.is_admin()
    @decorators.is_game()
    async def night(self, ctx):
        self.nighttime(ctx.guild.id)

    @commands.command()
    @decorators.is_admin()
    @decorators.is_game()
    async def announcenight(self, ctx):
        self.almostnighttimeannounce()

    @commands.command(**files.command_parameters['shoot'])
    @decorators.hunter()
    @decorators.is_game()
    async def shoot(self, ctx, victim_name: str):
        dead_villager = self.findMember(victim_name, ctx.guild.id)
        if dead_villager is None:
            ctx.send("Please try again. That person wasn't able to be found.")
            return
        dead_villager_document = models.villager.Villager.find_one({
            "server": ctx.guild.id,
            "discord_id": dead_villager.id
        })
        if dead_villager_document is None:
            ctx.send("Please try again. That person wasn't able to be found.")
            return
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        game_document["hunter_ids"].remove(ctx.author.id)
        game_document.save()
        lynched_message = files.werewolfMessages[dead_villager_document["character"]]["hunter"].format(dead_villager.mention)
        town_square_channel = ctx.guild.get_channel(models.channels.getChannelId("town-square", ctx.guild.id))
        announcements_channel = ctx.guild.get_channel(models.channels.getChannelId("announcements", ctx.guild.id))
        await announcements_channel.send(lynched_message)
        await town_square_channel.send(lynched_message)
        await self.die_from_db(villager_id=dead_villager.id, guild_id=ctx.guild.id)
        await self.die(ctx.guild, ctx.author.id)

    @commands.command(**files.command_parameters['investigate'])
    @decorators.is_from_channel("seer")
    @decorators.is_game()
    async def investigate(self, ctx, person_name):
        if not abilities.check_ability("seer", ctx.guild.id):
            await ctx.send("You already used your ability. Try again after the next sunrise.")
            return
        if not abilities.check_ability("seer", ctx.guild.id):
            await ctx.send(
                "The future is hazy, but when it's night again you may have a better chance. If you don't die before!")
            return
        target = self.findMember(person_name, ctx.guild.id)
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        target_document = models.villager.Villager.find_one({
            "server": ctx.guild.id,
            "discord_id": target.id
        })
        if target_document is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        await ctx.send("{} is {}a werewolf".format(target.mention, "" if target_document['werewolf'] else "not "))
        abilities.use_ability("seer", ctx.guild.id)

    @commands.command(**files.command_parameters['protect'])
    @decorators.is_from_channel("bodyguard")
    @decorators.is_game()
    async def protect(self, ctx, person_name):
        if not abilities.check_ability("bodyguard", ctx.guild.id):
            await ctx.send("You've been protecting someone and now you're tired. Get some rest until the next morning.")
            return
        # protector: villager.Villager = self.findVillager(ctx.message.author.name)
        the_protected_one = self.findMember(name=person_name, guild_id=ctx.guild.id)
        if the_protected_one is None:
            await ctx.send("I couldn't find that person!")
            return
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        protected_document = models.villager.Villager.find_one({
            "server": ctx.guild.id,
            "discord_id": the_protected_one.id
        })
        if protected_document is None:
            await ctx.send("I couldn't find that person!")
            return
        if game_document["last_protected_id"] == the_protected_one.id:
            await ctx.send("You protected that person recently. Try someone new.")
            return
        if not protected_document["alive"]:
            await ctx.send("You should have protected that person sooner. Choose someone else.")
            return
        abilities.use_ability("bodyguard", ctx.guild.id)
        await ctx.send("You've protected {}".format(the_protected_one.mention))
        game_document["protected"] = the_protected_one.id
        game_document["last_protected_id"] = the_protected_one.id
        game_document.save()

    @commands.command(**files.command_parameters['getinstructions'])
    async def getinstructions(self, ctx):
        await ctx.send('\n'.join(files.werewolfMessages["help"]))

    @commands.command(**files.command_parameters['sendmessage'])
    @decorators.is_from_channel("afterlife")
    @decorators.is_game()
    async def sendmessage(self, ctx, word: str):
        v = models.villager.Villager.find_one({
            "server": ctx.guild.id,
            "discord_id": ctx.author.id
        })
        is_werewolf = v["werewolf"]
        if not abilities.check_ability("dead_wolves" if is_werewolf else "spirits", ctx.guild.id):
            await ctx.send("You've already sent a message or a hint. Wait until the next night.")
            return
        if len(word.split(' ')) > 1:
            await ctx.send("You can only send one word at a time")
            return
        if self.findPlayer(word, ctx.guild.id) is not None:
            await ctx.send("You cannot use a name of someone playing as the actual word.")
            return
        if is_werewolf:
            abilities.use_ability("dead_wolves", ctx.guild.id)
        else:
            abilities.use_ability("spirits", ctx.guild.id)
        channel = ctx.guild.get_channel(models.channels.getChannelId("mason", ctx.guild.id))
        await channel.send("You have received a message from above.")
        await channel.send(word)

    @commands.command(**files.command_parameters['match'])
    @decorators.is_from_channel("cupid")
    @decorators.has_ability("cupid")
    @decorators.is_game()
    async def match(self, ctx, person1: str, person2: str):
        member1 = self.findMember(person1, ctx.guild.id)
        member2 = self.findMember(person2, ctx.guild.id)
        if member1 is None:
            await ctx.send("The first person could not be found. Try again.")
            return
        if member2 is None:
            await ctx.send("The second villager could not be found. Try again.")
            return

        villager1 = models.villager.Villager.find_one({
            "discord_id": member1.id,
            "server": ctx.guild.id
        })
        villager2 = models.villager.Villager.find_one({
            "discord_id": member2.id,
            "server": ctx.guild.id
        })
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        if not villager1["alive"] or not villager2["alive"]:
            await ctx.send("You can't match dead villagers. Try again!")
            return
        abilities.use_ability("cupid", ctx.guild.id)
        game_document["inlove"].append(villager1["discord_id"])
        game_document["inlove"].append(villager2["discord_id"])
        game_document.save()
        await ctx.send("{} and {} are in love now".format(person1, person2))
        # self.__bot.remove_command("match")
        read_write_permission = files.readJsonFromConfig("permissions.json")["read_write"]
        love_channel = ctx.guild.get_channel(models.channels.getChannelId("lovebirds", ctx.guild.id))
        for x in game_document["inlove"]:
            await love_channel.set_permissions(ctx.guild.get_member(x),
                                               overwrite=discord.PermissionOverwrite(**read_write_permission))
        await love_channel.send("Welcome {} and {}. "
                                "You two are now in love! :heart:".format(member1.mention, member2.mention))

    async def startvote(self, guild):
        town_square_id = models.channels.getChannelId("town-square", guild.id)
        town_square_channel = guild.get_channel(town_square_id)
        announcements_id = models.channels.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcements_id)
        town_square_id = models.channels.getChannelId("town-square", guild.id)
        town_square_channel = guild.get_channel(town_square_id)
        to_vote = []
        villagers = models.villager.Villager.find({
            "server": guild.id
        })
        for i in villagers:
            if i["alive"]:
                to_vote.append(i["discord_id"])

        election.start_vote(town_square_channel, guild.id, to_vote)
        await announcements_channel.send("You can now vote to lynch.")

    async def stopvote(self, guild):
        cog = self.__bot.get_cog("Election")
        result = cog.stop_vote(guild.id)

        announcements_id = models.channels.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcements_id)
        await announcements_channel.send("The voting has closed.")
        if len(result) == 0:
            await announcements_channel.send("All of you guys forgot to vote. Too bad!")
        else:
            x = random.choice(result)
            dead_villager = self.findMember(x, guild.id)
            dead_player = self.findPlayer(x, guild.id)
            if len(result) > 1:
                await announcements_channel.send(
                    f"You couldn't decide on only one person, but someone has to die! Because you guys couldn't pick, I'll pick someone myself.\n"
                    f"I'll pick {dead_villager.mention}! No hard feelings!")
            # await self.die(guild, dead_villager.id)
            # dead_villager.die(guild.id)
            lynched_message = files.werewolfMessages[dead_player["character"]]["lynched"].format(dead_villager.mention)
            await announcements_channel.send(lynched_message)
            # await self.die(guild, dead_villager.id)
            await self.die_from_db(dead_villager.id, guild.id)

    def cog_unload(self):
        self.clear_schedule()
        return super().cog_unload()

    def clear_schedule(self, tag="game"):
        schedule.clear(str(tag))
        # self.__bot.remove_cog("Election")
        # if self.__election_cog is not None:
        #     self.__bot.remove_cog("Election")


    def daytime(self, guild_id: int):
        guild = self.__bot.get_guild(guild_id)
        game_document = models.game.Game.find_one({
            "server": guild_id
        })
        game_document["protected"] = -1
        game_document.save()
        abilities.daytime(guild_id)
        self.__bot.loop.create_task(self.daytimeannounce(guild_id, bakerdead=game_document["bakerdead"]))


    async def daytimeannounce(self, guild_id, bakerdead):
        announcements_id = models.channels.getChannelId("announcements", guild_id)
        announcements_channel = self.__bot.get_channel(announcements_id)
        await announcements_channel.send("It is daytime")

        if bakerdead:
            await self.starve_die(guild)
        # if self.__bakerdead and self.__bakerdays > 0:
        #     await announcements_channel.send(f"You have {self.__bakerdays} days left")
        await self.announce_dead(guild=self.__bot.get_guild(guild_id))
        game_doc = models.game.Game.find_one({ "server": guild_id })
        if game_doc is not None:
            await self.startvote(announcements_channel.guild)

    async def starve_die(self, guild):
        announcements_id = models.channels.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcements_id)
        game_document = models.game.Game.find_one({
            "server": guild.id
        })
        for _ in range(random.choice([0,0,1,1,1,2,2,3])):
            dead_id = random.choice(game_document["starving"])
            dead_villager = models.villager.Villager.find_one({
                "server": guild.id,
                "discord_id": dead_id
            })
            game_document["starving"].remove(dead_id)
            game_document.save()
            if not dead_villager["alive"]:
                continue
            await announcements_channel.send(files.werewolfMessages[dead_villager["character"]]["starve"].format(
                guild.get_member(dead_id).mention))
            await self.die_from_db(dead_id, guild.id)

    def nighttime(self, guild_id):
        # self.__killed = False
        self.__bot.loop.create_task(self.nighttimeannounce(guild_id))
        abilities.nighttime(guild_id)
        if election.is_vote(guild_id):
            self.__bot.loop.create_task(self.stopvote(self.__bot.get_guild(guild_id)))

    async def nighttimeannounce(self, guild_id):
        announcements_id = models.channels.getChannelId("announcements", guild_id)
        announcements_channel = self.__bot.get_channel(announcements_id)
        await announcements_channel.send("It is nighttime")

    def almostnighttime(self, guild_id):
        self.__bot.loop.create_task(self.almostnighttimeannounce(guild_id))

    async def almostnighttimeannounce(self, guild_id):
        announcements_id = models.channels.getChannelId("announcements", guild_id)
        announcement_channel = self.__bot.get_channel(announcements_id)
        server_document = models.server.Server.find_one({"server": guild_id})
        x = server_document["warning"]
        await announcement_channel.send(f"{x} minute{'s' if x > 1 else ''} left until nighttime.")
        if election.is_vote(guild_id):
            await announcement_channel.send("Once nighttime falls, the lynch vote will be finished.")

    def findMember(self, name: str, guild_id: int):
        guild = self.__bot.get_guild(guild_id)
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            id = int(name[3:-1])
        elif name[0:2] == "<@":
            id = int(name[2:-1])
        else:
            id = 0
        if id != 0:
            return guild.get_member(id)
        villagers = models.villager.Villager.find({
            "server": guild_id
        })
        for v in villagers:
            m = guild.get_member(v["discord_id"])
            name = name.lower()
            if name == m.display_name.lower() or name == m.name.lower() or name == str(m).lower():
                return m
        return guild.get_member_named(name)

    def findPlayer(self, name: str, guild_id: int):
        member = self.findMember(name, guild_id)
        if member is None:
            return None
        return models.villager.Villager.find_one({
            "server": guild_id,
            "discord_id": member.id
        })
