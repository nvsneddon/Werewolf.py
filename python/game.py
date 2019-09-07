import random
from villager import Villager
import discord
import threading
import schedule
import time
import datetime
from discord.ext import commands
from files import channels_config, getChannelId, werewolfMessages


class Game(commands.Cog):

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
        self.__bakerdead: bool = False
        self.__protected: Villager = None
        self.__daysleft = 3
        self.__hunter = False   # Variable to turn on the hunter's power
        self.__resettedCharacters = ("bodyguard", "seer")
        self.__running = True

        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()

        schedule.every().day.at("07:00").do(self.daytime).tag("game")
        schedule.every().day.at("20:55").do(self.almostnighttime).tag("game")
        schedule.every().day.at("21:00").do(self.nighttime).tag("game")

        check_time = datetime.datetime.now().time()
        if datetime.time(7, 0) <= check_time <= datetime.time(21, 0):
            self.voted = False
            self.killed = True
        else:
            # Night time
            self.voted = True
            self.killed = False

        cards = []
        if len(roles) >= 6:
            cards += roles[5]*["baker"]
        if len(roles) >= 5:
            cards += roles[4]*["hunter"]
        if len(roles) >= 4:
            cards += roles[3]*["cupid"]
        if len(roles) >= 3:
            cards += roles[2]*["bodyguard"]
        if len(roles) >= 2:
            cards += roles[1]*["seer"]
        if len(roles) >= 1:
            cards += roles[0]*["werewolf"]

        if len(players) > len(cards):
            cards += (len(players) - len(cards))*["villager"]
        if randomshuffle:
            random.shuffle(cards)

        for x in players:
            y = Villager(str(x), cards[0], x.id)
            self.__players.append(y)
            cards.pop(0)
    
        for i in self.__players:
            print(i)

    def is_from_channel(channelname: str):
        async def predicate(ctx):
            channel1 = ctx.guild.get_channel(getChannelId(channelname))
            channel2 = ctx.channel
            return channel1 == channel2
        return commands.check(predicate)

    @commands.command()
    @is_from_channel("werewolves")
    async def kill(self, ctx, *args):
        if len(args) > 1:
            await ctx.send("You can only kill one person at a time. Please try again")
            return
        elif len(args) == 0:
            await ctx.send("Please tell us who you are planning on killing")
            return
        target = self.findPlayer(args[0])
        print("The target is", target.getName())
        if self.__protected == target:
            await ctx.send("That person has been protected. You just wasted your kill!")
        else:
            await ctx.send("Killing {}".format(target.getName()))
            target.die()
            dead_role = discord.utils.get(ctx.guild.roles, name="Dead")    
            target_user = ctx.message.guild.get_member_named(target.getDiscordTag())
            await target_user.edit(roles=[dead_role])
            town_square_id = getChannelId("town-square")
            town_square_channel = ctx.guild.get_channel(town_square_id)
            await town_square_channel.send(werewolfMessages[target.getCharacter()]["killed"].format(target.getName()))

    @commands.command()
    async def testingthis(self, ctx):
        await ctx.send(self.findPlayer("picksupchickens").getDiscordTag())

    def cog_unload(self):
        schedule.clear("game")
        # self.__bot.remove_cog("Election")
        return super().cog_unload()

    def daytime(self):
        if self.__bakerdead:
            self.__daysleft -= 1
        self.__killed = True
        for x in self.__players:
            if x.character == "werewolf":
                self.usedAbility = True
            elif x.character in self.__resettedCharacters:
                x.usedAbility = False
            x.protected = False

    def nighttime(self):
        self.__killed = False
        self.__voted = True
    
    def almostnighttime(self):
        pass

    def getVillagerByID(self, id: int) -> Villager:
        for x in self.__players:
            if id == x.getUserID():
                return x
        return None

    # returns person that was killed
    def killmaybe(self, killer, target) -> None:
        killerVillager = self.findPlayer(killer)
        if killerVillager.iskiller():
            self.findVillager(target).die()

    def findPlayer(self, name: str) -> Villager:
        if name[0:3] == "<@!": # in case the user that is passed in has been mentioned with @
            name = name[3:-1]
        elif name[0:2] == "<@":
            name = name[2:-1]
        for x in self.__players:
            if x.getName().lower() == name.lower() or x.getDiscordTag().lower() == name.lower():
                return x 
        return None

