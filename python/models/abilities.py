import mongothon

from dbconnect import my_db


def delete_many(filter):
    my_db['abilities'].delete_many(filter)


ability_schema = mongothon.Schema({
    "server": {"type": int, "default": True},
    "spirits": {"type": bool, "default": True},
    "dead_wolves": {"type": bool, "default": True},
    "werewolves": {"type": bool, "default": True},
    "seer": {"type": bool, "default": True},
    "bodyguard": {"type": bool, "default": True},
    "cupid": {"type": bool, "default": True}
})

Abilities = mongothon.create_model(ability_schema, my_db['abilities'])