import mongothon
import files
import pymongo

database_config = files.readJsonFromConfig("../config/database_config.json")

my_client = pymongo.MongoClient(database_config["url"].format(database_config["user"], database_config["password"]))
my_db = my_client["games"]

channels_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "channels": {"type": dict}
})

Channels = mongothon.create_model(channels_schema, my_db["channels"])

