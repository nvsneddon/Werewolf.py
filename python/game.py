import random
from villager import Villager
from exceptions import PermissionException

class Game:

    # players is a list of all of the name of people playing
    # roles is a list of numbers of all of the characters that will be playing
    # raises ValueError Exception when too many roles are handed out

    def __init__(self, players, roles, day=True, randomshuffle=True):
        self.__players = []
        self.__inlove = []
        self.__bakerdead = False
        self.__protected = ""
        self.__daysleft = 3
        self.__hunter = False   # Variable to turn on the hunter's power
        self.__resettedCharacters = ("bodyguard", "seer")
        
        if day:
            self.__voted = False
            self.__killed = True
        else:
            # Night time
            self.__voted = True 
            self.__killed = False 


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

        if len(players) < len(cards):
            raise ValueError("You have given out too many roles for the number of people playing.")
        elif len(players) > len(cards):
            for a in range(len(players)-len(cards)):
                cards.append("villager")
        if randomshuffle:
            random.shuffle(cards)

        for x in players:
            self.__players.append(Villager(x, cards[0]))
            cards.pop(0)

    def nighttime(self):
        self.__killed = False
        self.__voted = True

    def iswerewolf(self, person):
        return self.findVillager(person).iswerewolf()

    def getCharacter(self, person):
        return self.findVillager(person).getCharacter()

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

    def findVillager(self, name):
        for x in self.__players:
            if x.getName() == name:
                return x
        return None

    # returns person that was killed
    def kill(self, killer, target):
        killerVillager = self.findVillager(killer)
        if killerVillager.iskiller():
            self.findVillager(target).die()
        

