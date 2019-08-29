import random
from villager import Villager
import discord
import threading
import schedule
import time
import datetime
from discord.ext import commands


class Game(commands.Cog):

    # players is a list of all of the name of people playing
    # roles is a list of numbers of all of the characters that will be playing
    # raises ValueError Exception when too many roles are handed out

    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)

    def __init__(self, bot, players, roles, randomshuffle=True):
        self.bot = bot
        self.__players = []
        self.__inlove = []
        self.__bakerdead = False
        self.__protected = ""
        self.__daysleft = 3
        self.__hunter = False   # Variable to turn on the hunter's power
        self.__resettedCharacters = ("bodyguard", "seer")
        self.__running = True

        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()

        schedule.every().day.at("07:00").do(self.daytime).tag("game")
        schedule.every().day.at("21:00").do(self.nighttime).tag("game")


        check_time = datetime.datetime.now().time()
        if check_time >= datetime.time(7,0) and check_time <= datetime.time(21,0):
            self.voted = False
            self.killed = True
        else:
            #Night time
            self.voted = True 
            self.killed = False 

        cards = []
        if len(roles) >= 6:
            for n in range(roles[5]):
                cards.append("baker")
        if len(roles) >= 5:
            for m in range(roles[4]):
                cards.append("hunter")
        if len(roles) >= 4:
            for l in range(roles[3]):
                cards.append("cupid")
        if len(roles) >= 3:
            for k in range(roles[2]):
                cards.append("bodyguard")
        if len(roles) >= 2:
            for j in range(roles[1]):
                cards.append("seer")
        if len(roles) >= 1:
            for i in range(roles[0]):
                cards.append("werewolf")

        if len(players) > len(cards):
            for a in range(len(players)-len(cards)):
                cards.append("villager")
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

    def findVillager(self, name):
        for x in self.__players:
            if x.getname() == name:
                return x
        return None

    # returns person that was killed
    def kill(self, killer, target):
        killerVillager = self.findVillager(killer)
        if killerVillager.iskiller():
            self.findVillager(target).die()

    def cog_unload(self):
        schedule.clear("game")
        return super().cog_unload()