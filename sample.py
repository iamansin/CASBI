from pymongo import MongoClient
MONGO_DB="mongodb+srv://redhood:aarav123@cluster0.krvu0rv.mongodb.net/CASBI?retryWrites=true&w=majority"
MONGO_CLIENT=MongoClient(MONGO_DB)
db = MONGO_CLIENT.get_database()  # Gets the database specified in the URI
collection_names = db.list_collection_names()
print("Available collections:")
for collection in collection_names:
    print(f" - {collection}")