class Abilities:

    def __init__(self):
        self.__roles = {
            "spirits": False,
            "werewolves": False,
            "seer": False,
            "bodyguard": False,
            "villager": False
        }

        self.__night = ("spirits", "werewolves")
        self.__day = ("seer", "bodyguard", "villager")

    def __reset_abilities(self):
        for x in self.__roles:
            self.__roles[x] = False

    def start_game(self, night=False):
        if night:
            self.nighttime()
            for x in self.__roles:
                if x in self.__day:
                    self.__roles[x] = True
        else:
            self.daytime()

    def check_ability(self, character):
        if character not in self.__roles:
            raise Exception("Character role not found.")
        return self.__roles[character]

    def use_ability(self, character):
        if character not in self.__roles:
            raise Exception("Character role not found.")
        self.__roles[character] = False

    def daytime(self):
        for x in self.__roles:
            if x in self.__day:
                self.__roles[x] = True
            else:
                self.__roles[x] = False

    def nighttime(self):
        for x in self.__roles:
            if x in self.__night:
                self.__roles[x] = True
