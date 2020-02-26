import mongothon
import files
import pymongo

database_config = files.readJsonFromConfig("../config/database_config.json")

my_client = pymongo.MongoClient(database_config["url"].format(database_config["user"], database_config["password"]))
my_db = my_client["games"]

villager_schema = mongothon.Schema({
    "name": {"type": str, "required": True},
    "alive": {"type": bool, "required": True},
    "character": {"type": str, "required": True},
    "werewolf": {"type": bool, "required": True},
    "inlove": {"type": bool, "required": True}
})

Villager = mongothon.create_model(villager_schema, my_db['villager'])
