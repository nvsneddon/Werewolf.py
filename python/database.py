import pymongo
import files

database_config = files.readJsonFromConfig("../config/database_config.json")

myclient = pymongo.MongoClient(
    f"mongodb+srv://{database_config['user']}:{database_config['password']}@werewolf-game-cluster-xxi0b.mongodb.net/test?retryWrites=true&w=majority")


def update_channels(server, channels):
    mydb = myclient["games"]
    mycol = mydb["channels"]

    query = {"server": server}
    if mycol.count_documents(query) == 1:
        mycol.update_one(query, {"$set": {"channels": channels}})

    elif mycol.count_documents(query) == 0:
        doc = {
            "server": server,
            "channels": channels
        }
        x = mycol.insert_one(doc)
        print(x.inserted_id)
    else:
        print("Oops!")
        raise ValueError

def deleteChannels(server):
    mydb = myclient["games"]
    mycol = mydb["channels"]
    query = {"server": server}
    mycol.delete_one(query)

def getChannels(server):
    mydb = myclient["games"]
    mycol = mydb["channels"]
    query = {"server": server}
    x = mycol.find_one(query)
    return x["channels"]


if __name__ == "__main__":
    mydb = myclient["games"]
    mycol = mydb["channels"]

    update_channels(1400, {
        "bot-admin": 2643264,
        "town-square": 26,
        "werewolves": 535
    })

    for x, y in getChannels(1400).items():
        print(x, y)

