import mongothon

from dbconnect import my_db
#
# role_schema = {
#     "spirits": {"type": bool, "required": True},
#     "dead_wolves": {"type": bool, "required": True},
#     "werewolves": {"type": bool, "required": True},
#     "seer": {"type": bool, "required": True},
#     "bodyguard": {"type": bool, "required": True},
#     "cupid": {"type": bool, "required": True}
# }

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