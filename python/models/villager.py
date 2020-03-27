import mongothon

from dbconnect import my_db

def removeAll(filter):
    my_db['villager'].delete_many(filter)

villager_schema = mongothon.Schema({
    "discord_id": {"type": int, "required": True},
    "server": {"type": int, "required": True},
    "character": {"type": str, "required": True},
    "werewolf": {"type": bool, "required": True},
    "alive": {"type": bool, "default": True},
    "inlove": {"type": bool, "default": False}
})

Villager = mongothon.create_model(villager_schema, my_db['villager'])

