import mongothon

from dbconnect import my_db

villager_schema = mongothon.Schema({
    "name": {"type": str, "required": True},
    "server": {"type": int, "required": True},
    "alive": {"type": bool, "default": True},
    "character": {"type": str, "required": True},
    "werewolf": {"type": bool, "required": True},
    "inlove": {"type": bool, "default": False}
})

Villager = mongothon.create_model(villager_schema, my_db['villager'])
