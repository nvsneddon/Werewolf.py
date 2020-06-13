import mongothon

from dbconnect import my_db


def delete_many(filter):
    my_db['undead'].delete_many(filter)


undead_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "day_choice": {"type": int, "default": -1},
    "night_choice": {"type": int, "default": -1},
    "undead": {"type": list, "default": []},
    "necromancer": {"type": int, "default": -1}
})

Undead = mongothon.create_model(undead_schema, my_db['undead'])
