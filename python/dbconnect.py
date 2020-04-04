import mongothon
# import files
import pymongo
import os

# database_config = files.readJsonFromConfig("../config/database_config.json")
# try:
#     dir_name = os.path.dirname(__file__)
#     f = open(os.path.join(dir_name, "../config/database_config.json"))
#     database_config = json.loads(f.read())
#     f.close()
#
# except:
#     print("Database config not found")
#     raise FileNotFoundError

my_client = pymongo.MongoClient(os.getenv("url").format(os.getenv("user"), os.getenv("password")))
my_db = my_client["games"]
