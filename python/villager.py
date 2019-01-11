class Villager:
    def __init__(self, name, character):
        specialChannel = ("werewolf", "bodyguard", "seer", "cupid")
        self.__name = name
        self.__character = character 
        self.__werewolf = (character == "werewolf")
        self.__killer = (character == "werewolf") 
        self.__alive = True
        self.__protected = False
        self.__usedAbility = False
        self.__inSpecialChannel = bool(character in specialChannel)
        self.__inLove = False


    def getName(self):
        return self.__name

    def getCharacter(self):
        return self.__character
        
    def protect(self):
        self.__protected = True

    def die(self):
        self.__alive = False

    def isdead(self):
        return not self.__alive

    def iswerewolf(self):
        return self.__werewolf

    def isProtected(self):
        return __self.protected
