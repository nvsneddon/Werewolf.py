import models.abilities

ROLES = {
    "spirits",
    "dead_wolves",
    "werewolves",
    "necromancer",
    "seer",
    "bodyguard",
    "cupid"
}

NIGHT = {"seer", "spirits", "dead_wolves", "werewolves", "necromancer"}
DAY = {"bodyguard", "necromancer"}
ONE_TIME = {"cupid"}


def start_game(guild_id: int, night=False):
    models.abilities.delete_many({"server": guild_id})
    m = models.abilities.Abilities({
        "server": guild_id
    })
    m.save()
    if not night:
        daytime(guild_id)


def daytime(guild_id):
    ability_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    for x in ROLES:
        if x in ONE_TIME:
            continue
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
    if ability_document is None:
        return False
    return ability_document[character]


def use_ability(character, guild_id):
    if character not in ROLES:
        raise Exception("character role not found.")
    ability_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    ability_document[character] = False
    ability_document.save()


def finish_game(guild_id):
    abilities_document = models.abilities.Abilities.find_one({
        "server": guild_id
    })
    abilities_document.remove()
