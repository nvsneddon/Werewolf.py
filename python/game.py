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
import files
from villager import Villager
from abilities import Abilities
from cipher import Cipher
from exceptions import DocumentFoundException




class Game(commands.Cog):
    __cipher: typing.Optional[Cipher]
    __last_protected: str
    __bakerdays: int
    __bakerdead: bool
    __voted: bool
    __inlove: typing.List[Villager]
    __players: typing.List[Villager]

    # players is a list of all of the name of people playing
    # roles is a list of numbers of all of the characters that will be playing
    # raises ValueError Exception when too many roles are handed out

    async def die_from_db(self, villager_tag: str, server: int):
        v = models.villager.Villager.find_one({
            "server": server,
            "name": villager_tag
        })

        guild = self.__bot.get_guild(server)
        member = guild.get_member_named(villager_tag)
        if v["werewolf"]:
            self.__numWerewolves -= 1
        else:
            self.__numVillagers -= 1
        if v["character"] == "hunter":
            self.__hunter = True
            self.__pending_death = villager_tag
        v.update_instance({"alive": False})
        if v["character"] == 'baker':
            self.__bakerdead = True


    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)

    def hunter():
        def predicate(ctx):
            cog = ctx.bot.get_cog("Game")
            return cog.Hunter and cog.AlmostDead == str(ctx.message.author)

        return commands.check(predicate)

    def __init__(self, bot, members, future, roles, randomshuffle=True, send_message_flag=True, guild_id = 0):
        self.__bot = bot
        self.__hunter_future = None
        self.__cipher = None
        self.__voted = False
        self.__game_future = future
        self.__players = []
        self.__members = members
        self.__inlove = []
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

        schedule.every().day.at(files.config["daytime"]).do(self.daytime).tag("game")
        warn_voting_time = datetime.datetime(1, 1, 1, int(
            files.config['nighttime'][:2]), int(files.config['nighttime'][3:5])) - datetime.datetime(1, 1, 1, 0, files.config['minutes-before-warning'])
        schedule.every().day.at(str(warn_voting_time)).do(self.almostnighttime).tag("game")
        schedule.every().day.at(files.config["nighttime"]).do(self.nighttime).tag("game")
        # schedule.every(3).seconds.do(self.daytime).tag("game")

        night_array = files.config["nighttime"].split(':')
        day_array = files.config["daytime"].split(':')

        check_time = datetime.datetime.now().time()
        if datetime.time(int(day_array[0]), int(day_array[1])) <= check_time <= datetime.time(int(night_array[0]), int(night_array[1])):
            self.__abilities.start_game()
        else:
            self.__abilities.start_game(True)

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

        if len(members) > len(cards):
            cards += (len(members) - len(cards)) * ["villager"]
        if randomshuffle:
            random.shuffle(cards)
        for x in members:
            y = Villager(str(x), cards[0], x.id, x.nick, server=guild_id)
            if cards[0] in ("werewolf"):
                self.__numWerewolves += 1;
            else:
                self.__numVillagers += 1;
            self.__players.append(y)
            cards.pop(0)
            message = '\n'.join(files.werewolfMessages[y.Character]["welcome"])
            if send_message_flag:
                self.__bot.loop.create_task(self.__sendPM(x, message))


        afterlife_message = ""

        for i in self.__players:
            afterlife_message += f"{i.Mention} is a {i.Character}\n"
            print(i)

        self.__bot.loop.create_task(self.__afterlife_message(afterlife_message))

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
        if not self.__abilities.check_ability("werewolves"):
            await ctx.send("You already killed. Get some rest and don't get caught.")
            return
        target = self.findVillager(person_name)
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        self.__abilities.use_ability("werewolves")
        if target.Protected:
            await ctx.send("That person has been protected. You just wasted your kill!")
            announcement_id = files.getChannelId("announcements")
            announcements_channel = ctx.guild.get_channel(announcement_id)
            await announcements_channel.send(f"The werewolves have tried to kill {target.Mention} but has been protected. We're glad you're alive.")
        else:
            await ctx.send("Killing {}".format(target.Mention))
            announcement_id = files.getChannelId("announcements")
            announcements_channel = ctx.guild.get_channel(announcement_id)
            await announcements_channel.send(files.werewolfMessages[target.Character]["killed"].format(target.Mention))
            await self.die(ctx.guild, target)
        if self.Winner != "":
            self.__game_future.set_result(self.Winner)

    async def die(self, guild, target: Villager):
        if target.die():
            self.__numWerewolves -= 1
            self.__bakerdays -= 1
        else:
            self.__numVillagers -= 1
        if target.Character == "hunter":
            self.__hunter = True
            self.__pending_death = target.DiscordTag
            self.__hunter_future = self.__bot.loop.create_future()
            await self.__hunter_future
        elif target.Character == "baker":
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



        if target in self.__inlove:
            self.__inlove.remove(target)
            other: Villager = self.__inlove[0]
            self.__inlove.remove(other)
            town_square_id = files.getChannelId("announcements")
            town_square_channel = guild.get_channel(town_square_id)
            await town_square_channel.send(files.werewolfMessages[other.Character]["inlove"].format(other.Mention))
            await self.die(guild, other)

        dead_role = discord.utils.get(guild.roles, name="Dead")
        # await channel.set_permissions(member, overwrite=None)

        for x in files.channels_config["channels"]:
            if x == "announcements":
                continue
            channel = guild.get_channel(files.getChannelId(x))
            member = guild.get_member_named(target.DiscordTag)
            await channel.set_permissions(member, overwrite=None)

        target_user = guild.get_member_named(target.DiscordTag)
        await target_user.edit(roles=[dead_role])

    @commands.command(**files.command_parameters['countpeople'])
    async def countpeople(self, ctx):
        await ctx.send(f"Villagers: {self.__numVillagers}\nWerewolves: {self.__numWerewolves}")

    @commands.command(aliases=['daytime'])
    @decorators.is_admin()
    async def day(self, ctx):
        self.daytime()

    @commands.command(aliases=['nighttime'])
    @decorators.is_admin()
    async def night(self, ctx):
        self.nighttime()

    @commands.command()
    @decorators.is_admin()
    async def announcenight(self, ctx):
        self.almostnighttimeannounce()

    @commands.command(**files.command_parameters['shoot'])
    @hunter()
    async def shoot(self, ctx, victim: str):
        dead_villager = self.findVillager(victim)
        if dead_villager is None:
            ctx.send("Please try again. That person wasn't able to be found.")
            return
        lynched_message = files.werewolfMessages[dead_villager.Character]["hunter"].format(dead_villager.Mention)
        town_square_channel = ctx.guild.get_channel(files.getChannelId("town-square"))
        await town_square_channel.send(lynched_message)
        await self.die(ctx.guild, dead_villager)
        self.__hunter_future.set_result("dead")
        self.__bot.remove_command("shoot")

        # await self.findWinner(ctx)

    @commands.command(**files.command_parameters['investigate'])
    @decorators.is_from_channel("seer")
    async def investigate(self, ctx, person_name):
        if not self.__abilities.check_ability("seer"):
            await ctx.send("The future is hazy, but when it's night again you may have a better chance. If you don't die before!")
            return
        target = self.findVillager(person_name)
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        if not self.__abilities.check_ability("seer"):
            await ctx.send("You already used your ability. Try again after the next sunrise.")
            return
        await ctx.send("{} is {}a werewolf".format(target.Mention, "" if target.Werewolf else "not "))
        self.__abilities.use_ability("seer")

    @commands.command(**files.command_parameters['protect'])
    @decorators.is_from_channel("bodyguard")
    async def protect(self, ctx, person_name):
        if not self.__abilities.check_ability("bodyguard"):
            await ctx.send("You've been protecting someone and now you're tired. Get some rest until the next morning.")
            return
        protector: Villager = self.findVillager(ctx.message.author.name)
        the_protected_one = self.findVillager(person_name)
        if the_protected_one is None:
            await ctx.send("I couldn't find that person!")
            return
        if self.__last_protected == person_name:
            await ctx.send("You protected that person recently. Try someone new.")
            return
        if the_protected_one.Dead:
            await ctx.send("You should have protected that person sooner. Choose someone else.")
            return
        self.__abilities.use_ability("bodyguard")
        await ctx.send("You've protected {}".format(the_protected_one.Mention))
        the_protected_one.Protected = True
        self.__last_protected = person_name
        protected_member = ctx.guild.get_member_named(the_protected_one.DiscordTag)
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
        for x in self.__players:
            if not x.Dead and not x.InLove:
                return False
        return True

    @commands.command(aliases=["matchlove", "makeinlove"])
    @decorators.is_from_channel("cupid")
    @decorators.has_ability("cupid")
    async def match(self, ctx, person1: str, person2: str):
        villager1 = self.findVillager(person1)
        villager2 = self.findVillager(person2)
        if villager1 is None:
            await ctx.send("The first person could not be found. Try again.")
            return
        if villager2 is None:
            await ctx.send("The second villager could not be found. Try again.")
            return
        if villager1.Dead or villager2.Dead:
            await ctx.send("You can't match dead villagers. Try again!")
            return
        self.__abilities.use_ability("cupid")
        self.__inlove.append(villager1)
        self.__inlove.append(villager2)
        await ctx.send("{} and {} are in love now".format(person1, person2))
        self.__bot.remove_command("match")
        read_write_permission = files.readJsonFromConfig("permissions.json")["read_write"]
        love_channel = ctx.guild.get_channel(files.getChannelId("lovebirds", ctx.guild.id))
        for x in self.__inlove:
            await love_channel.set_permissions(ctx.guild.get_member_named(x.DiscordTag),
                                               overwrite=discord.PermissionOverwrite(**read_write_permission))
        await love_channel.send("Welcome {} and {}. "
                                "You two are now in love! :heart:".format(villager1.Mention, villager2.Mention))

    async def startvote(self, guild):
        self.__lynching = True
        town_square_id = files.getChannelId("town-square", guild.id)
        town_square_channel = guild.get_channel(town_square_id)
        announcements_id = files.getChannelId("announcements", guild.id)
        announcements_channel = guild.get_channel(announcements_id)
        future = self.__bot.loop.create_future()
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
        self.__election_cog = election.Election(self.__bot, future, to_vote, channel=town_square_channel, guild_id=guild.id)
        self.__bot.add_cog(self.__election_cog)
        await announcements_channel.send("You can now vote to lynch.")
        await future
        m.remove()
        self.__lynching = False
        self.__bot.remove_cog("Election")
        self.__election_cog = None
        result = future.result()
        if result == "cancel":
            await announcements_channel.send("The lynching vote has been cancelled")
            return
        await announcements_channel.send("The voting has closed.")
        self.__has_lynched = True
        if len(result) == 0:
            await announcements_channel.send("All of you guys forgot to vote. Too bad!")
        else:
            x = random.choice(result)
            dead_villager: Villager = self.findVillager(x)
            if len(result) > 1:
                await announcements_channel.send(
                f"You couldn't decide on only one person, but someone has to die! Because you guys couldn't pick, I'll pick someone myself.\n"
                f"I'll pick {dead_villager.Mention}! No hard feelings!")
            await self.die(guild, dead_villager )
            dead_villager.die()
            lynched_message = files.werewolfMessages[dead_villager.Character]["lynched"].format(dead_villager.Mention)
            await announcements_channel.send(lynched_message)
            if self.Winner != "":
                self.__game_future.set_result(self.Winner)

    def cog_unload(self):
        schedule.clear("game")
        self.__bot.remove_cog("Election")
        if self.__election_cog is not None:
            self.__bot.remove_cog("Election")
        return super().cog_unload()

    def daytime(self):
        guild = self.__bot.get_guild(681696629224505376)
        for x in self.__players:
            x.Protected = False
        self.__has_lynched = False
        self.__abilities.daytime()
        self.__bot.loop.create_task(self.daytimeannounce())
        if self.__bakerdead:
            self.__bot.loop.create_task(self.starve_die(self.__starving_people[self.__bakerdays], guild))

            if self.Winner != "":
                self.__game_future.set_result(self.Winner)
                return

    async def daytimeannounce(self):
        announcements_id = files.getChannelId("announcements")
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
                await self.die(guild, x)
                await town_square_channel.send(files.werewolfMessages[x.Character]["starve"].format(x.Mention))
        self.__bakerdays += 1

    def nighttime(self):
        # self.__killed = False
        self.__bot.loop.create_task(self.nighttimeannounce())
        self.__abilities.nighttime()
        if self.__election_cog is not None:
            self.__election_cog.stop_vote()

    async def nighttimeannounce(self):
        announcements_id = files.getChannelId("announcements")
        announcements_channel = self.__bot.get_channel(announcements_id)
        await announcements_channel.send("It is nighttime")

    def almostnighttime(self):
        self.__bot.loop.create_task(self.almostnighttimeannounce())

    async def almostnighttimeannounce(self):
        town_square_id = files.getChannelId("town-square")
        town_square_channel = self.__bot.get_channel(town_square_id)
        x = files.config["minutes-before-warning"]
        await town_square_channel.send(f"{x} minute{'s' if x > 1 else ''} left until nighttime.")
        if self.__lynching:
            await town_square_channel.send("Once nighttime falls, the lynch vote will be finished.")

    def getVillagerByID(self, player_id: int) -> typing.Optional[Villager]:
        for x in self.__players:
            if player_id == x.UserID:
                return x
        return None

    def findVillager(self, name: str) -> typing.Optional[Villager]:
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

    @property
    def Winner(self) -> str:
        # channel = ctx.guild.get_channel(getChannelId("town-square"))
        if self.cupidWinner():
            return "cupid"
        if self.GameStats["werewolves"] >= self.GameStats["villagers"]:
            return "werewolves"
        elif self.GameStats["werewolves"] == 0:
            return "villagers"
        # elif self.__bakerdays < 0:
        #     return "bakerdead"
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
    def Hunter(self):
        return self.__hunter

    @property
    def AlmostDead(self):
        return self.__pending_death
