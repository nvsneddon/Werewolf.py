import random
from villager import Villager
import discord
import threading
import schedule
import time
import datetime
from discord.ext import commands
from files import channels_config


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
        self.__protected = ""
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
            self.__players.append(Villager(x, cards[0]))
            cards.pop(0)
    
        for i in self.__players:
            print(i)

    def iswerewolf(self, person):
        return self.findVillager(person).iswerewolf()

    def getCharacter(self, person):
        return self.findVillager(person).getCharacter()

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

    def findVillager(self, name: str) -> Villager:
        for x in self.__players:
            if x.getName() == name:
                return x
        return None

    def isWerewolf(self, name: str) -> bool:
        return self.findVillager(name).isWerewolf()

    # returns person that was killed
    def kill(self, killer, target) -> None:
        killerVillager = self.findVillager(killer)
        if killerVillager.iskiller():
            self.findVillager(target).die()

    def findPlayer(self, name: str):
        for x in self.__self.players:
            if x.getName == name or x.getDiscordTag == name:
                return x 
        return None
