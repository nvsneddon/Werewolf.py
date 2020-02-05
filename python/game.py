import datetime
import random
import threading
import time
from typing import Optional, List

import discord
import schedule
from discord.ext import commands

from decorators import is_from_channel, is_admin, findPerson, is_not_character, has_ability
from election import Election
from files import getChannelId, werewolfMessages, config, readJsonFromConfig, channels_config
from villager import Villager
from abilities import Abilities
from cipher import Cipher


class Game(commands.Cog):
    __cipher: Optional[Cipher]
    __last_protected: str
    __daysleft: int
    __bakerdead: bool
    __voted: bool
    __inlove: List[Villager]
    __players: List[Villager]

    # players is a list of all of the name of people playing
    # roles is a list of numbers of all of the characters that will be playing
    # raises ValueError Exception when too many roles are handed out

    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)

    def hunter():
        def predicate(ctx):
            cog = ctx.bot.get_cog("Game")
            return cog.Hunter and cog.AlmostDead == str(ctx.message.author)

        return commands.check(predicate)

    def __init__(self, bot, members, future, roles, randomshuffle=True, send_message_flag=True):
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
        self.__last_protected = None
        self.__daysleft = 4
        self.__hunter = False  # Variable to turn on the hunter's power
        self.__running = True
        self.__numWerewolves = 0
        self.__numVillagers = 0
        self.__abilities = Abilities()

        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()

        schedule.every().day.at(config["daytime"]).do(self.daytime).tag("game")
        schedule.every().day.at(config["vote-warning"]).do(self.almostnighttime).tag("game")
        schedule.every().day.at(config["nighttime"]).do(self.nighttime).tag("game")
        # schedule.every(3).seconds.do(self.daytime).tag("game")

        check_time = datetime.datetime.now().time()
        if datetime.time(7, 0) <= check_time <= datetime.time(19, 0):
            self.__abilities.start_game()
            # self.__killed = False
        else:
            self.__abilities.start_game(True)
            # Night time
            # self.__killed = True

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
            y = Villager(str(x), cards[0], x.id, x.nick)
            if cards[0] in ("werewolf"):
                self.__numWerewolves += 1;
            else:
                self.__numVillagers += 1;
            self.__players.append(y)
            cards.pop(0)
            message = '\n'.join(werewolfMessages[y.Character]["welcome"])
            if send_message_flag:
                self.__bot.loop.create_task(self.__sendPM(x, message))

        for i in self.__players:
            print(i)

    async def __sendPM(self, member, message):
        await member.send(message)

    @property
    def Abilities(self):
        return self.__abilities

    @property
    def GameStats(self):
        return {
            "werewolves": self.__numWerewolves,
            "villagers": self.__numVillagers
        }

    @commands.command(aliases=["murder"])
    @is_from_channel("werewolves")
    async def kill(self, ctx, person_name: str):
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
        else:
            await ctx.send("Killing {}".format(target.Mention))
            town_square_id = getChannelId("town-square")
            town_square_channel = ctx.guild.get_channel(town_square_id)
            await town_square_channel.send(werewolfMessages[target.Character]["killed"].format(target.Mention))
            await self.die(ctx, target)
        if self.Winner != "":
            self.__game_future.set_result(self.Winner)

    async def die(self, ctx, target: Villager):
        if target.die():
            self.__numWerewolves -= 1
        else:
            self.__numVillagers -= 1
        if target.Character == "hunter":
            self.__hunter = True
            self.__pending_death = target.DiscordTag
            self.__hunter_future = self.__bot.loop.create_future()
            await self.__hunter_future
        elif target.Character == "baker":
            self.__bakerdead = True
        if target in self.__inlove:
            self.__inlove.remove(target)
            other: Villager = self.__inlove[0]
            self.__inlove.remove(other)
            town_square_id = getChannelId("town-square")
            town_square_channel = ctx.guild.get_channel(town_square_id)
            # TODO Change the message to support both names of dead people
            await town_square_channel.send(werewolfMessages[other.Character]["inlove"].format(other.Mention))
            await self.die(ctx, other)

        dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
        # await channel.set_permissions(member, overwrite=None)

        for x in channels_config["channels"]:
            channel = ctx.guild.get_channel(getChannelId(x))
            member = ctx.guild.get_member_named(target.DiscordTag)
            await channel.set_permissions(member, overwrite=None)

        target_user = ctx.message.guild.get_member_named(target.DiscordTag)
        await target_user.edit(roles=[dead_role])

    @commands.command()
    async def countpeople(self, ctx):
        await ctx.send(f"Villagers: {self.__numVillagers}\nWerewolves: {self.__numWerewolves}")

    @commands.command(aliases=['daytime'])
    @is_admin()
    async def day(self, ctx):
        self.daytime()

    @commands.command(aliases=['nighttime'])
    @is_admin()
    async def night(self, ctx):
        self.nighttime()

    @commands.command()
    @is_admin()
    async def announcenight(self, ctx):
        self.almostnighttimeannounce()

    @commands.command()
    @hunter()
    async def shoot(self, ctx, victim: str):
        dead_villager = self.findVillager(victim)
        if dead_villager is None:
            ctx.send("Please try again. That person wasn't able to be found.")
            return
        lynched_message = werewolfMessages[dead_villager.Character]["hunter"].format(dead_villager.Mention)
        town_square_channel = ctx.guild.get_channel(getChannelId("town-square"))
        await town_square_channel.send(lynched_message)
        await self.die(ctx, dead_villager)
        self.__hunter_future.set_result("dead")
        self.__bot.remove_command("shoot")

        # await self.findWinner(ctx)

    @commands.command(aliases=["see", "look", "suspect"])
    @is_from_channel("seer")
    async def investigate(self, ctx, person_name: str):
        if not self.__abilities.check_ability("seer"):
            await ctx.send("The future is hazy, but tomorrow you could have a better chance. If you don't die before!")
            return
        target = self.findVillager(person_name)
        # seer: Villager = self.findVillager(ctx.message.author.name)
        # if seer is None:
        #     message = "Seer is None. This should never happen"
        #     print(message)
        #     ctx.send(message)
        #     return
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        if not self.__abilities.check_ability("seer"):
            await ctx.send("You already used your ability. Try again after the next sunrise.")
            return
        await ctx.send("{} is {} a werewolf".format(target.Mention, "" if target.IsWerewolf else "not"))
        self.__abilities.use_ability("seer")

    @commands.command()
    @is_from_channel("bodyguard")
    async def protect(self, ctx, person_name: str):
        if not self.__abilities.check_ability("bodyguard"):
            await ctx.send("You've been protecting someone and now you're tired. Get some rest until the next morning.")
            return
        protector: Villager = self.findVillager(ctx.message.author.name)
        the_protected_one = self.findVillager(person_name)
        if the_protected_one is None:
            await ctx.send("I couldn't find that person!")
            return
        if self.__last_protected == person_name:
            ctx.send("You protected that person recently. Try someone new.")
            return
        if the_protected_one.Dead:
            await ctx.send("You should have protected that person sooner. Choose someone else.")
            return
        self.__abilities.use_ability("bodyguard")
        await ctx.send("You've protected {}".format(the_protected_one.Mention))
        the_protected_one.Protected = True
        self.__last_protected = person_name
        protector.UsedAbility = True
        protected_member = ctx.guild.get_member_named(the_protected_one.DiscordTag)
        await protected_member.send("You have been protected for the night! You can sleep in peace! :)")

    @commands.command()
    async def sendinstructions(self, ctx):
        await ctx.send(werewolfMessages["help"])

    @commands.command()
    @is_from_channel("afterlife")
    @is_not_character("werewolf")
    async def sendmessage(self, ctx, word: str):
        if not self.__abilities.check_ability("spirits"):
            await ctx.send("You've already sent a message or a hint. Wait until the next night.")
            return
        if len(word.split(' ')) > 1:
            await ctx.send("You can only send one word at a time")
            return
        if findPerson(ctx, word) is not None:
            await ctx.send("You cannot use the name as the actual word.")
            return
        self.__abilities.use_ability("spirits")
        self.__cipher = Cipher(word)
        channel = ctx.guild.get_channel(getChannelId("mason"))
        await channel.send("You have received a message from above.")
        await channel.send(self.__cipher.Decode)

    @commands.command()
    @is_from_channel("afterlife")
    @is_not_character("werewolf")
    async def sendhint(self, ctx):
        if not self.__abilities.check_ability("spirits"):
            await ctx.send("You've already sent a message or a hint. Wait until the next night.")
            return
        if self.__cipher == None:
            await ctx.send("There is no cipher that you can give out. Give out a hint instead.")
            return
        self.__abilities.use_ability("spirits")
        channel = ctx.guild.get_channel(getChannelId("mason"))
        await channel.send("You have received a hint from above. Hopefully this will help you decipher the code.")
        await channel.send(self.__cipher.Hint)

    def cupidWinner(self):
        for x in self.__players:
            if not x.Dead and not x.InLove:
                return False
        return True

    @property
    def Winner(self) -> str:
        # channel = ctx.guild.get_channel(getChannelId("town-square"))
        if self.cupidWinner():
            return "cupid"
        if self.GameStats["werewolves"] >= self.GameStats["villagers"]:
            return "werewolves"
        elif self.GameStats["werewolves"] == 0:
            return "villagers"
        elif self.__daysleft <= 0:
            return "bakerdead"
        return ""

    @commands.command(aliases=["matchlove", "makeinlove"])
    @is_from_channel("cupid")
    @has_ability("cupid")
    async def match(self, ctx, person1: str, person2: str):
        villager1 = self.findVillager(person1)
        villager2 = self.findVillager(person2)
        if villager1 is None:
            await ctx.send("The first person could not be found. Try again.")
            return
        if villager2 is None:
            await ctx.send("The second villager could not be found. Try again.")
            return
        self.__abilities.use_ability("cupid")
        self.__inlove.append(villager1)
        self.__inlove.append(villager2)
        await ctx.send("{} and {} are in love now".format(person1, person2))
        self.__bot.remove_command("match")
        read_write_permission = readJsonFromConfig("permissions.json")["read_write"]
        love_channel = ctx.guild.get_channel(getChannelId("lovebirds"))
        for x in self.__inlove:
            await love_channel.set_permissions(ctx.guild.get_member_named(x.DiscordTag),
                                               overwrite=discord.PermissionOverwrite(**read_write_permission))
        await love_channel.send("Welcome {} and {}. "
                                "You two are now in love! :heart:".format(villager1.Mention, villager2.Mention))

    @commands.command(alias=["startwerewolfvote"])
    async def startvote(self, ctx):

        town_square_id = getChannelId("town-square")
        town_square_channel = ctx.guild.get_channel(town_square_id)
        future = self.__bot.loop.create_future()
        self.__election_cog = Election(self.__bot, future, self.__players)
        self.__bot.add_cog(self.__election_cog)
        await town_square_channel.send("The lynching vote has now begun.")
        await future
        self.__bot.remove_cog("Election")
        self.__election_cog = None
        result = future.result()
        if result == "cancel":
            await town_square_channel.send("The lynching vote has been cancelled")
            return
        await town_square_channel.send("The voting has closed.")
        for x in result:
            dead_villager: Villager = self.findVillager(x)
            print("The dead villager", dead_villager)
            await self.die(ctx, dead_villager)
            dead_villager.die()
            lynched_message = werewolfMessages[dead_villager.Character]["lynched"].format(dead_villager.Mention)
            await town_square_channel.send(lynched_message)
        if len(result) > 1:
            await town_square_channel.send("We had a bloodbath because we had a tie.")
        if self.Winner != "":
            self.__game_future.set_result(self.Winner)

    @property
    def Hunter(self):
        return self.__hunter

    @property
    def AlmostDead(self):
        return self.__pending_death

    def cog_unload(self):
        schedule.clear("game")
        # self.__bot.remove_cog("Election")
        return super().cog_unload()

    def daytime(self):
        if self.__bakerdead:
            self.__daysleft -= 1
            if self.Winner != "":
                self.__game_future.set_result(self.Winner)

        for x in self.__players:
            x.Protected = False

        self.__bot.loop.create_task(self.daytimeannounce())

    async def daytimeannounce(self, ):
        town_square_id = getChannelId("town-square")
        town_square_channel = self.__bot.get_channel(town_square_id)
        await town_square_channel.send("It is daytime")
        if self.__bakerdead and self.__daysleft > 0:
            await town_square_channel.send(f"You have {self.__daysleft} days left")

    def nighttime(self):
        # self.__killed = False
        self.__abilities.nighttime()
        if self.__election_cog is not None:
            self.__election_cog.stop_vote()
        self.__bot.loop.create_task(self.nighttimeannounce())

    async def nighttimeannounce(self):
        town_square_id = getChannelId("town-square")
        town_square_channel = self.__bot.get_channel(town_square_id)
        await town_square_channel.send("It is nighttime")

    def almostnighttime(self):
        self.__bot.loop.create_task(self.almostnighttimeannounce())

    async def almostnighttimeannounce(self):
        town_square_id = getChannelId("town-square")
        town_square_channel = self.__bot.get_channel(town_square_id)
        x = config["minutes-before-warning"]
        print(type(x))
        await town_square_channel.send("It is almost nighttime")

    def getVillagerByID(self, player_id: int) -> Optional[Villager]:
        for x in self.__players:
            if player_id == x.UserID:
                return x
        return None

    def findVillager(self, name: str) -> Optional[Villager]:
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
