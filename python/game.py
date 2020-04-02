import datetime
import random
import threading
import time
import typing

import discord
import schedule
from discord.ext import commands

import decorators
import election
import models.election
import models.game
import files
import villager
import models.villager

from abilities import Abilities
from cipher import Cipher


def hunter():
    def predicate(ctx):
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        if game_document is None:
            return False

        return ctx.message.author.id in game_document["hunter_ids"]

    return commands.check(predicate)

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
    __cipher: typing.Optional[Cipher]
    __last_protected: str
    __bakerdays: int
    __bakerdead: bool
    __voted: bool
    __inlove: typing.List[villager.Villager]
    __players: typing.List[villager.Villager]

    # players is a list of all of the name of people playing
    # roles is a list of numbers of all of the characters that will be playing
    # raises ValueError Exception when too many roles are handed out

    async def die_from_db(self, villager_id: int, guild_id: int):
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
        if v["character"] == "hunter":
            game_document["hunter_ids"].append(v["discord_id"])
            game_document.save()
            return
        if v["character"] == "baker":
            villager_players = [y for y in self.__players if not y.Werewolf and not y.Dead]
            max_death_day = (((len(villager_players) - 1) // 3) * 3 + 3)
            s_people = [[] for i in range(max_death_day)]
            random.shuffle(villager_players)
            n = 0
            while len(villager_players) != 0:
                p = villager_players[:3]
                for i in p:
                    r = random.choice(range(3)) + n
                    s_people[r].append(i)
                villager_players = villager_players[3:]
                n += 3

            self.__bakerdead = True
            self.__starving_people = s_people

            for i in range(len(self.__starving_people)):
                for j in self.__starving_people[i]:
                    print(i, j.Name)

        await self.die(guild, villager_id)


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
            town_square_id = files.getChannelId("announcements")
            town_square_channel = guild.get_channel(town_square_id)
            other_member = guild.get_member(other_id)
            await town_square_channel.send(
                files.werewolfMessages[v["character"]]["inlove"].format(other_member.mention))
            # await self.die(guild, other)
            await self.die_from_db(other_id, guild.id)
        v["alive"] = False
        v.save()
        game_document.save()
        member = guild.get_member(v["discord_id"])
    #     await self.mark_dead(guild, member)
    #
    # async def mark_dead(self, guild, member):
        dead_role = discord.utils.get(guild.roles, name="Dead")
        for x in files.channels_config["channels"]:
            if x == "announcements":
                continue
            channel = guild.get_channel(files.getChannelId(x))
            await channel.set_permissions(member, overwrite=None)
        await member.edit(roles=[dead_role])

    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)

    def __init__(self, bot, members, future, roles, randomshuffle=True, send_message_flag=True, guild_id=0):

        self.__bot = bot
        self.__hunter_future = None
        self.__cipher = None
        self.__voted = False
        self.__game_future = future
        self.__players = []
        self.__members = members
        self.__pending_death = None
        self.__bakerdead = False
        self.__election_cog = None
        self.__lynching = False
        self.__has_lynched = False
        self.__last_protected = None
        self.__bakerdays = 0
        self.__starving_people = []
        self.__hunter = False  # Variable to turn on the hunter's power
        self.__running = True
        self.__numWerewolves = 0
        self.__numVillagers = 0
        self.__abilities = Abilities()
        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()
        self.__election_cog = election.Election(self.__bot)
        self.__bot.add_cog(self.__election_cog)

        self.schedule_day_and_night(guild_id)
        self.initialize_game(guild_id, members, randomshuffle, roles, send_message_flag)

    def initialize_game(self, guild_id, members, randomshuffle, roles, send_message_flag):
        num_werewolves = 0
        num_villagers = 0
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
        self.__bot.loop.create_task(self.__afterlife_message(afterlife_message))



    def schedule_day_and_night(self, guild_id):
        schedule.every().day.at(files.config["daytime"]).do(self.daytime, guild_id=guild_id).tag("game", str(guild_id))
        warn_voting_time = datetime.datetime(1, 1, 1, int(
            files.config['nighttime'][:2]), int(files.config['nighttime'][3:5])) - \
                           datetime.datetime(1, 1, 1, 0, files.config['minutes-before-warning'])
        schedule.every().day.at(str(warn_voting_time)).do(self.almostnighttime, guild_id=guild_id).tag("game",
                                                                                                       str(guild_id))
        schedule.every().day.at(files.config["nighttime"]).do(self.nighttime, guild_id=guild_id).tag("game",
                                                                                                     str(guild_id))
        night_array = files.config["nighttime"].split(':')
        day_array = files.config["daytime"].split(':')
        check_time = datetime.datetime.now().time()
        if datetime.time(int(day_array[0]), int(day_array[1])) <= check_time <= datetime.time(int(night_array[0]),
                                                                                              int(night_array[1])):
            self.__abilities.start_game()
        else:
            self.__abilities.start_game(True)

    async def __afterlife_message(self, message):
        afterlife_id = files.getChannelId("afterlife")
        afterlife_channel = self.__bot.get_channel(afterlife_id)
        await afterlife_channel.send(message)
        async for x in (afterlife_channel.history(limit=1)):
            await x.pin()

    async def __sendPM(self, member, message):
        await member.send(message)

    @commands.command(**files.command_parameters['kill'])
    @decorators.is_from_channel("werewolves")
    async def kill(self, ctx, person_name):
        game_document = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        if game_document is None:
            ctx.send("There's no game right now. You can't kill yet.")
            return
        if not self.__abilities.check_ability("werewolves"):
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
        if target_document is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        self.__abilities.use_ability("werewolves")
        if target.id == game_document["protected"]:
            await ctx.send("That person has been protected. You just wasted your kill!")
            announcement_id = files.getChannelId("announcements")
            announcements_channel = ctx.guild.get_channel(announcement_id)
            await announcements_channel.send(
                f"The werewolves have tried to kill {target.mention} who was protected. We're glad you're alive.")
        else:
            await ctx.send("Killing {}".format(target.mention))
            announcement_id = files.getChannelId("announcements")
            announcements_channel = ctx.guild.get_channel(announcement_id)
            await announcements_channel.send(
                files.werewolfMessages[target_document["character"]]["killed"].format(target.mention))
            await self.die_from_db(target.id, ctx.guild.id)
        if self.Winner != "":
            self.__game_future.set_result(self.Winner)

    async def declareWinner(self, guild_id: int, winner):
        pass

    @commands.command(**files.command_parameters['countpeople'])
    async def countpeople(self, ctx):
        game = models.game.Game.find_one({
            "server": ctx.guild.id
        })
        await ctx.send(f"Villagers: {game['villagercount']}\nWerewolves: {game['werewolfcount']}")

    @commands.command(aliases=['daytime'])
    @decorators.is_admin()
    async def day(self, ctx):
        self.daytime(ctx.guild.id)

    @commands.command(aliases=['nighttime'])
    @decorators.is_admin()
    async def night(self, ctx):
        self.nighttime(ctx.guild.id)

    @commands.command()
    @decorators.is_admin()
    async def announcenight(self, ctx):
        self.almostnighttimeannounce()

    @commands.command(**files.command_parameters['shoot'])
    @hunter()
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
        lynched_message = files.werewolfMessages[dead_villager_document["character"]]["hunter"].format(dead_villager.mention)
        town_square_channel = ctx.guild.get_channel(files.getChannelId("town-square"))
        announcements_channel = ctx.guild.get_channel(files.getChannelId("announcements"))
        await announcements_channel.send(lynched_message)
        await town_square_channel.send(lynched_message)
        await self.die_from_db(villager_id=dead_villager.id, guild_id=ctx.guild.id)
        await self.die(ctx.guild, ctx.author.id)
        # self.__hunter_future.set_result("dead")
        # self.__bot.remove_command("shoot")

        # await self.findWinner(ctx)

    @commands.command(**files.command_parameters['investigate'])
    @decorators.is_from_channel("seer")
    async def investigate(self, ctx, person_name):
        if not self.__abilities.check_ability("seer"):
            await ctx.send("You already used your ability. Try again after the next sunrise.")
            return
        if not self.__abilities.check_ability("seer"):
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
        self.__abilities.use_ability("seer")

    @commands.command(**files.command_parameters['protect'])
    @decorators.is_from_channel("bodyguard")
    async def protect(self, ctx, person_name):
        if not self.__abilities.check_ability("bodyguard"):
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
        self.__abilities.use_ability("bodyguard")
        await ctx.send("You've protected {}".format(the_protected_one.mention))
        game_document["protected"] = the_protected_one.id
        game_document["last_protected_id"] = the_protected_one.id
        game_document.save()
        # protected_member = ctx.guild.get_member_named(the_protected_one.id)
        # if not the_protected_one.Werewolf:
        # await protected_member.send("You have been protected for the night! You can sleep in peace! :)")

    @commands.command(**files.command_parameters['getinstructions'])
    async def getinstructions(self, ctx):
        await ctx.send('\n'.join(files.werewolfMessages["help"]))

    @commands.command(**files.command_parameters['sendmessage'])
    @decorators.is_from_channel("afterlife")
    async def sendmessage(self, ctx, word: str):
        is_werewolf = self.findVillager(str(ctx.author)).Werewolf
        if not self.__abilities.check_ability("dead_wolves" if is_werewolf else "spirits"):
            await ctx.send("You've already sent a message or a hint. Wait until the next night.")
            return
        if len(word.split(' ')) > 1:
            await ctx.send("You can only send one word at a time")
            return
        if decorators.findPerson(ctx, word) is not None:
            await ctx.send("You cannot use the name as the actual word.")
            return
        if is_werewolf:
            self.__abilities.use_ability("dead_wolves")
        else:
            self.__abilities.use_ability("spirits")
        # self.__cipher = Cipher(word)
        channel = ctx.guild.get_channel(files.getChannelId("mason"))
        await channel.send("You have received a message from above.")
        await channel.send(word)

    def cupidWinner(self):
        return False

    @commands.command(aliases=["matchlove", "makeinlove"])
    @decorators.is_from_channel("cupid")
    @decorators.has_ability("cupid")
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
        self.__abilities.use_ability("cupid")
        game_document["inlove"].append(villager1["discord_id"])
        game_document["inlove"].append(villager2["discord_id"])
        game_document.save()
        await ctx.send("{} and {} are in love now".format(person1, person2))
        # self.__bot.remove_command("match")
        read_write_permission = files.readJsonFromConfig("permissions.json")["read_write"]
        love_channel = ctx.guild.get_channel(files.getChannelId("lovebirds", ctx.guild.id))
        for x in self.__inlove:
            await love_channel.set_permissions(ctx.guild.get_member(x),
                                               overwrite=discord.PermissionOverwrite(**read_write_permission))
        await love_channel.send("Welcome {} and {}. "
                                "You two are now in love! :heart:".format(member1.mention, member2.mention))

    async def startvote(self, guild):
        self.__lynching = True
        town_square_id = files.getChannelId("town-square", guild.id)
        town_square_channel = guild.get_channel(town_square_id)
        announcements_id = files.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcements_id)
        town_square_id = files.getChannelId("town-square")
        town_square_channel = guild.get_channel(town_square_id)
        # future = self.__bot.loop.create_future()
        to_vote = []
        for i in self.__players:
            discordPerson = guild.get_member_named(i.DiscordTag)
            alive_role = discord.utils.get(guild.roles, name="Alive")
            if alive_role in discordPerson.roles:
                to_vote.append(i)
        # m = models.election.Election.find_one({"server": guild.id})
        # if m is not None:
        #     raise DocumentFoundException
        # m = models.election.Election({
        #     "server": guild.id,
        #     "people": to_vote,
        #     "future": future,
        #     "channel": town_square_channel.id
        # })
        # m.save()

        election.start_vote(town_square_channel, guild.id, to_vote)
        await announcements_channel.send("You can now vote to lynch.")
        # await future
        # m.remove()

    async def stopvote(self, guild):
        self.__lynching = False
        cog = self.__bot.get_cog("Election")
        result = cog.stop_vote(guild.id)
        # self.__bot.remove_cog("Election")
        # self.__election_cog = None

        announcements_id = files.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcements_id)
        await announcements_channel.send("The voting has closed.")
        self.__has_lynched = True
        if len(result) == 0:
            await announcements_channel.send("All of you guys forgot to vote. Too bad!")
        else:
            x = random.choice(result)
            dead_villager: villager.Villager = self.findVillager(x)
            if len(result) > 1:
                await announcements_channel.send(
                    f"You couldn't decide on only one person, but someone has to die! Because you guys couldn't pick, I'll pick someone myself.\n"
                    f"I'll pick {dead_villager.Mention}! No hard feelings!")
            await self.die(guild, dead_villager)
            # dead_villager.die(guild.id)
            lynched_message = files.werewolfMessages[dead_villager.Character]["lynched"].format(dead_villager.Mention)
            await announcements_channel.send(lynched_message)
            await self.die(guild, dead_villager)
            if self.Winner != "":
                self.__game_future.set_result(self.Winner)

    def cog_unload(self):
        self.stop_game()
        return super().cog_unload()

    def stop_game(self, tag="game"):
        schedule.clear(str(tag))
        self.__bot.remove_cog("Election")
        if self.__election_cog is not None:
            self.__bot.remove_cog("Election")

    def daytime(self, guild_id: int):
        guild = self.__bot.get_guild(guild_id)
        game_document = models.game.Game.find_one({
            "server": guild_id
        })
        game_document["protected"] = -1
        game_document.save()
        self.__has_lynched = False
        self.__abilities.daytime()
        self.__bot.loop.create_task(self.daytimeannounce(guild_id))
        if self.__bakerdead:
            self.__bot.loop.create_task(self.starve_die(self.__starving_people[self.__bakerdays], guild))

    async def daytimeannounce(self, guild_id):
        announcements_id = files.getChannelId("announcements", 681696629224505376)
        announcements_channel = self.__bot.get_channel(announcements_id)

        await announcements_channel.send("It is daytime")
        # if self.__bakerdead and self.__bakerdays > 0:
        #     await announcements_channel.send(f"You have {self.__bakerdays} days left")
        await self.startvote(announcements_channel.guild)

    async def starve_die(self, dead_people, guild):
        town_square_id = files.getChannelId("announcements")
        town_square_channel = guild.get_channel(town_square_id)
        for x in dead_people:
            if not x.Dead:
                await town_square_channel.send(files.werewolfMessages[x.Character]["starve"].format(x.Mention))
                await self.die(guild, x)
        self.__bakerdays += 1
        if self.Winner != "":
            self.__game_future.set_result(self.Winner)
            return

    def nighttime(self, guild_id):
        # self.__killed = False
        self.__bot.loop.create_task(self.nighttimeannounce(guild_id))
        self.__abilities.nighttime()
        if election.is_vote(guild_id):
            self.__bot.loop.create_task(self.stopvote(self.__bot.get_guild(guild_id)))

    async def nighttimeannounce(self, guild_id):
        announcements_id = files.getChannelId("announcements", guild_id)
        announcements_channel = self.__bot.get_channel(announcements_id)
        await announcements_channel.send("It is nighttime")

    def almostnighttime(self, guid_id):
        self.__bot.loop.create_task(self.almostnighttimeannounce(guild_id))

    async def almostnighttimeannounce(self, guild_id):
        town_square_id = files.getChannelId("town-square", 681696629224505376)
        town_square_channel = self.__bot.get_channel(town_square_id)
        x = files.config["minutes-before-warning"]
        await town_square_channel.send(f"{x} minute{'s' if x > 1 else ''} left until nighttime.")
        if self.__lynching:
            await town_square_channel.send("Once nighttime falls, the lynch vote will be finished.")

    def getVillagerByID(self, player_id: int) -> typing.Optional[villager.Villager]:
        for x in self.__players:
            if player_id == x.UserID:
                return x
        return None

    def findVillager(self, name: str) -> typing.Optional[villager.Villager]:
        id = 0
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            id = int(name[3:-1])
        elif name[0:2] == "<@":
            id = int(name[2:-1])
        for x in self.__players:
            if x.UserID == id or x.Name.lower() == name.lower() or \
                    x.DiscordTag.lower() == name.lower() or x.NickName.lower() == name.lower():
                return x
        return None

    def findMember(self, name: str, guild_id: int):
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            id = int(name[3:-1])
        elif name[0:2] == "<@":
            id = int(name[2:-1])
        else:
            id = 0
        if id != 0:
            return self.__bot.get_guild(guild_id).get_member(id)
        else:
            return self.__bot.get_guild(guild_id).get_member_named(name)

    @property
    def Winner(self) -> str:
        # channel = ctx.guild.get_channel(getChannelId("town-square"))
        # if self.cupidWinner():
        #     return "cupid"
        # if self.GameStats["werewolves"] >= self.GameStats["villagers"]:
        #     return "werewolves"
        # elif self.GameStats["werewolves"] == 0:
        #     return "villagers"
        # # elif self.__bakerdays < 0:
        # #     return "bakerdead"
        return ""

    @property
    def Abilities(self):
        return self.__abilities

    @property
    def GameStats(self):
        return {
            "werewolves": self.__numWerewolves,
            "villagers": self.__numVillagers
        }

    @property
    def AlmostDead(self):
        return self.__pending_death
