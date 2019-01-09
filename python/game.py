import random
from datetime import datetime, time

class Game:

    #players is a list of all of the name of people playing
    #roles is a list of numbers of all of the characters that will be playing
    def __init__(self, players, roles, day=True):
        self.__players = players
        self.__inlove = []
        self.__bakerdead = False
        self.__protected = ""
        self.__hunter = False   #Variable to turn on the hunter's power
        
        if day:
            self.__voted = False
            self.__killed = True
        else:
            #Night time
            self.__voted = True 
            self.__killed = False 

        cards = []
        if (len(roles) >= 6):
            for n in range(roles[5]):
                cards.append("baker")
        if (len(roles) >= 5):
            for m in range(roles[4]):
                cards.append("hunter")
        if (len(roles) >= 4):
            for l in range(roles[3]):
                cards.append("cupid")
        if (len(roles) >= 3):
            for k in range(roles[2]):
                cards.append("bodyguard")
        if (len(roles) >= 2):
            for j in range(roles[1]):
                cards.append("seer")
        if (len(roles) >= 1):
            for i in range(roles[0]):
                cards.append("werewolf")
        random.shuffle(cards)

        if len(players) < len(cards):
            print("Error!!!")
            print("You gave out too many roles for the number of people.")
        elif len(players) > len(cards):
            for a in range(len(players)-len(cards)):
                cards.append("villager")
