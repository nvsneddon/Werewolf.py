import mongothon

from dbconnect import my_db


def delete_many(filter):
    my_db['undead'].delete_many(filter)


undead_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "day_choice": {"type": str, "default": ""},  # I will eventually move all ids over to string type
    "night_choice": {"type": str, "default": ""},
    "undead": {"type": list, "default": []},
    "necromancer": {"type": str, "default": ""}
})

Undead = mongothon.create_model(undead_schema, my_db['undead'])
