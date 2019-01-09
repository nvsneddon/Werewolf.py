class Villager:
    def __init__(self, name, character, werewolf):
        __specialChannel = ("werewolf", "bodyguard", "seer", "cupid")
        self.__discordTag = name
        self.__name = name.split('#')[0]
        self.__character = character 
        self.__werewolf = werewolf
        self.__killer = False 
        self.__alive = True
        self.__protected = False
        self.__usedAbility = False
        self.__inSpecialChannel = bool(character in specialChannel)
        self.__inLove = False
        
    def protect(self):
        self.__protected = True

    def die(self):
        self.__alive = False

    def isdead(self):
        return not __self.alive

    def isProtected(self):
        return __self.protected