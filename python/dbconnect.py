import pymongo
import json
import os
import files

database_config = files.readJsonFromConfig("../config/database_config.json")

my_client = pymongo.MongoClient(database_config["url"].format(database_config["user"], database_config["password"]))
if "collection" in database_config:
    my_db = my_client[database_config["collection"]]
else:
    my_db = my_client["games"]
