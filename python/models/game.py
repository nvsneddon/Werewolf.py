import mongothon

from dbconnect import my_db


def delete_many(filter):
    my_db['game'].delete_many(filter)


game_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "players": {"type": list, "required": True},  # list of villager discord_id
    "inlove": {"type": list, "default": []},
    "bakerdead": {"type": bool, "default": False},
    "voting": {"type": bool, "default": False},
    "last_protected_id": {"type": int, "default": -1},
    "hunter_ids": {"type": list, "default": []},
    "almost_dead_hunter": {"type": int, "default": -1},
    "werewolfcount": {"type": int, "required": True},
    "villagercount": {"type": int, "required": True},
})

Game = mongothon.create_model(game_schema, my_db['game'])
