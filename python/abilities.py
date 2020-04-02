import models.abilities

ROLES = {
    "spirits": False,
    "dead_wolves": False,
    "werewolves": False,
    "seer": False,
    "bodyguard": False,
    "cupid": True
}

NIGHT = {"seer", "spirits", "dead_wolves", "werewolves"}
DAY = {"bodyguard"}


def init_abilities(guild_id: int, night=False):
    m = models.abilities.Abilities({
        "server": guild_id
    })
    m.save()
    if night:
        nighttime(guild_id)
    else:
        daytime(guild_id)


def daytime(guild_id):
    ability_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    for x in ROLES:
        if x in DAY:
            ability_document[x] = True
        else:
            ability_document[x] = False
    ability_document.save()


def nighttime(guild_id):
    ability_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    for x in ability_document:
        if x in NIGHT:
            ability_document[x] = True
    ability_document.save()


def check_ability(character: str, guild_id):
    if character not in ROLES:
        raise Exception("character role not found.")
    ability_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    return ability_document[character]


def use_ability(character, guild_id):
    if character not in ROLES:
        raise Exception("character role not found.")
    ability_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    ability_document[character] = False


class Abilities:


    def use_ability(self, character):
        if character not in self.__roles:
            raise Exception("Character role not found.")
        self.__roles[character] = False
