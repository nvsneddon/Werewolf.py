import mongothon

from dbconnect import my_db


def delete_many(filter):
    my_db['abilities'].delete_many(filter)


ability_schema = mongothon.Schema({
    "server": {"type": int, "default": False},
    "spirits": {"type": bool, "default": False},
    "dead_wolves": {"type": bool, "default": False},
    "werewolves": {"type": bool, "default": False},
    "seer": {"type": bool, "default": False},
    "bodyguard": {"type": bool, "default": False},
    "cupid": {"type": bool, "default": True}
})

Abilities = mongothon.create_model(ability_schema, my_db['abilities'])