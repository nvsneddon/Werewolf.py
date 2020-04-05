import pymongo
import json
import os

# database_config = files.readJsonFromConfig("../config/database_config.json")
try:
    dir_name = os.path.dirname(__file__)
    f = open(os.path.join(dir_name, "../config/database_config.json"))
    database_config = json.loads(f.read())
    f.close()

except:
    print("Database config not found")
    raise FileNotFoundError

my_client = pymongo.MongoClient(database_config["url"].format(database_config["user"], database_config["password"]))
if "collection" in database_config:
    my_db = my_client[database_config["collection"]]
else:
    my_db = my_client["games"]
