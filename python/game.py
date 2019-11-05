import datetime
import random
import threading
import time
from typing import Optional, List

import discord
import schedule
from discord.ext import commands

from decorators import is_from_channel, is_admin
from election import Election
from files import getChannelId, werewolfMessages, config, readJsonFromConfig
from villager import Villager


class Game(commands.Cog):
    __protected: str
    __daysleft: int
    __bakerdead: bool
    __inlove: List[Villager]
    __players: List[Villager]

    # players is a list of all of the name of people playing
    # roles is a list of numbers of all of the characters that will be playing
    # raises ValueError Exception when too many roles are handed out

    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)

    def __init__(self, bot, players, roles, randomshuffle=True):
        self.__bot = bot
        self.__players = []
        self.__inlove = []
        self.__bakerdead = False
        self.__protected = None
        self.__daysleft = 3
        self.__hunter = False  # Variable to turn on the hunter's power
        self.__running = True

        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()

        schedule.every().day.at(config["daytime"]).do(self.daytime).tag("game")
        schedule.every().day.at(config["vote-warning"]).do(self.almostnighttime).tag("game")
        schedule.every().day.at(config["nighttime"]).do(self.nighttime).tag("game")

        check_time = datetime.datetime.now().time()
        if datetime.time(7, 0) <= check_time <= datetime.time(21, 0):
            self.__killed = False
        else:
            # Night time
            self.__killed = True

        cards = []
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

        if len(players) > len(cards):
            cards += (len(players) - len(cards)) * ["villager"]
        if randomshuffle:
            random.shuffle(cards)

        for x in players:
            y = Villager(str(x), cards[0], x.id)
            self.__players.append(y)
            cards.pop(0)

        for i in self.__players:
            print(i)

    @commands.command(aliases=["murder"])
    @is_from_channel("werewolves")
    async def kill(self, ctx, person_name: str):
        target = self.findVillager(person_name)
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        if target.Protected:
            await ctx.send("That person has been protected. You just wasted your kill!")
        else:
            await ctx.send("Killing {}".format(target.Name))
            town_square_id = getChannelId("town-square")
            town_square_channel = ctx.guild.get_channel(town_square_id)
            await town_square_channel.send(werewolfMessages[target.Character]["killed"].format(target.Mention))
            await self.die(ctx, target)

    async def die(self, ctx, target: Villager):
        target.die()
        if target in self.__inlove:
            self.__inlove.remove(target)
            other = self.__inlove[0]
            self.__inlove.remove(other)
            town_square_id = getChannelId("town-square")
            town_square_channel = ctx.guild.get_channel(town_square_id)
            #TODO Change the message to support both names of dead people
            await town_square_channel.send(werewolfMessages[target.Character]["inlove"].format(other.Mention))
            await self.die(ctx, other)
        dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
        target_user = ctx.message.guild.get_member_named(target.DiscordTag)
        await target_user.edit(roles=[dead_role])

    @commands.command(aliases=["see", "look", "suspect"])
    @is_from_channel("seer")
    async def investigate(self, ctx, person_name: str):
        target = self.findVillager(person_name)
        seer: Villager = self.findVillager(ctx.message.author.name)
        if seer is None:
            message = "Seer is None. This should never happen"
            print(message)
            ctx.send(message)
            return
        if target is None:
            await ctx.send("That person could not be found. Please try again.")
            return
        if seer.UsedAbility:
            await ctx.send("{} is {} a werewolf".format(person_name, "" if target.IsWerewolf else "not"))
        else:
            await ctx.send("You already used your ability. You can use it soon though.")

    @commands.command()
    @is_from_channel("bodyguard")
    async def protect(self, ctx, person_name: str):
        protector: Villager = self.findVillager(ctx.message.author.name)
        the_protected_one = self.findVillager(person_name)
        if the_protected_one is None:
            await ctx.send("I couldn't find that person!")
            return
        if the_protected_one.Dead:
            await ctx.send("You should have protected that person sooner")
            return
        if self.__protected == person_name:
            ctx.send("You protected that person recently. Try someone new.")
            return
        if protector.UsedAbility:
            await ctx.send("You already protected someone today. You're tired! Get some rest")
            return
        await ctx.send("You've protected {}".format(the_protected_one.Name))
        the_protected_one.Protected = True
        self.__protected = person_name
        protector.UsedAbility = True
        protected_member = ctx.guild.get_member_named(person_name)
        await protected_member.send("You have been protected for the night! You can sleep in peace! :)")

    @commands.command(aliases=["shoot", "makeinlove"])
    @is_from_channel("cupid")
    async def shootarrow(self, ctx, person1: str, person2: str):
        villager1 = self.findVillager(person1)
        villager2 = self.findVillager(person2)
        if villager1 is None:
            await ctx.send("The first person could not be found. Try again.")
            return
        if villager2 is None:
            await ctx.send("The second villager could not be found. Try again.")
            return
        self.__inlove.append(villager1)
        self.__inlove.append(villager2)
        await ctx.send("{} and {} are in love now".format(person1, person2))
        self.__bot.remove_command("shootarrow")
        read_write_permission = readJsonFromConfig("permissions.json")["read_write"]
        love_channel = ctx.guild.get_channel(getChannelId("lovebirds"))
        for x in self.__inlove:
            await love_channel.set_permissions(ctx.guild.get_member_named(x.DiscordTag),
                                               overwrite=discord.PermissionOverwrite(**read_write_permission))
        await love_channel.send("Welcome {} and {}. "
                                "You two are now in love! :heart:".format(villager1.Mention, villager2.Mention))

    @commands.command(alias=["startwerewolfvote"])
    @is_admin()
    async def startvote(self, ctx):
        town_square_id = getChannelId("town-square")
        town_square_channel = ctx.guild.get_channel(town_square_id)
        future = self.__bot.loop.create_future()
        election_cog = Election(self.__bot, future, self.__players)
        self.__bot.add_cog(election_cog)
        await town_square_channel.send("The lynching vote has now begun.")
        await future
        self.__bot.remove_cog("Election")
        result = future.result()
        if result == "cancel":
            await town_square_channel.send("The lynching vote has been cancelled")
            return
        await town_square_channel.send("The voting has closed.")
        for x in result:
            dead_villager = self.findVillager(x)
            await self.die(ctx, dead_villager)
            lynched_message = werewolfMessages[dead_villager.Character]["lynched"].format(dead_villager.Mention)
            await town_square_channel.send(lynched_message)
        if len(result) > 1:
            await town_square_channel.send("We had a bloodbath because we had a tie.")

    def cog_unload(self):
        schedule.clear("game")
        # self.__bot.remove_cog("Election")
        return super().cog_unload()

    def daytime(self):
        if self.__bakerdead:
            self.__daysleft -= 1
        self.__killed = True
        for x in self.__players:
            x.UsedAbility = False
            x.Protected = False

    def nighttime(self):
        self.__killed = False

    def almostnighttime(self):
        pass

    def getVillagerByID(self, player_id: int) -> Optional[Villager]:
        for x in self.__players:
            if player_id == x.UserID:
                return x
        return None

    # TODO remove when content at not having this piece of code
    # # returns person that was killed
    # def killmaybe(self, killer, target) -> None:
    #     killerVillager = self.findVillager(killer)
    #     if killerVillager.iskiller():
    #         self.findVillager(target).die()

    def findVillager(self, name: str) -> Optional[Villager]:
        if name[0:3] == "<@!":  # in case the user that is passed in has been mentioned with @
            name = name[3:-1]
        elif name[0:2] == "<@":
            name = name[2:-1]
        for x in self.__players:
            if x.Name.lower() == name.lower() or x.DiscordTag.lower() == name.lower():
                return x
        return None
