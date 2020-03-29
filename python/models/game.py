import mongothon

from dbconnect import my_db

game_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "players": {"type": list, "required": True},
    "inlove": {"type": list, "default": []},
    "bakerdead": {"type": bool, "default": False},
    "voting": {"type": bool, "default": False},
    "last_protected_id": {"type": str, "default": ""},
    "daysleft": {"type": int, "required": True},
    "hunter_killing": {"type": bool, "default": False},
    "werewolfcount": {"type": int, "default": 0},
    "villagercount": {"type": int, "required": True}    
})

Game = mongothon.create_model(game_schema, my_db['game'])