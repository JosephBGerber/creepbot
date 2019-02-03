from pymongo import MongoClient
from creepbot.slack import list_users, react
from os import environ

try:
    db = MongoClient(environ["MONGODB_URI"])[environ["MONGODB_DATABASE"]]
except:
    db = MongoClient()[environ["MONGODB_DATABASE"]]


def create_creepshot(event):
    ts = event["ts"]
    channel = event["channel"]
    _id = ts + "@" + channel

    db.shots.insert_one({"_id": _id, "creepshoter": f"<@{event['user']}", "creepshotee": list_users(event),
                         "plus": -1, "trash": -1})

    react(channel, ts, environ["PLUS_REACTION"])
    react(channel, ts, environ["TRASH_REACTION"])


def increment_plus(_id):
    db.shots.update_one({"_id": _id}, {"$inc": {"plus": 1}})


def decrement_plus(_id):
    db.shots.update_one({"_id": _id}, {"$inc": {"plus": -1}})


def increment_trash(_id):
    db.shots.update_one({"_id": _id}, {"$inc": {"trash": 1}})


def decrement_trash(_id):
    db.shots.update_one({"_id": _id}, {"$inc": {"trash": -1}})


def get_top_creepshoters():
    aggregation = [
        {'$match': {'$expr': {'$lte': ['$trash', 10]}}},
        {'$match': {'$expr': {'$gte': ['$plus', 2]}}},
        {'$group': {'_id': '$creepshoter', 'count': {'$sum': 1}}},
        {'$group': {'_id': '$count', 'ids': {'$push': '$_id'}}},
        {'$sort': {'_id': -1}},
        {'$limit': 5}
    ]
    return db.shots.aggregate(aggregation)


def get_top_creepshots():
    aggregation = [
        {'$match': {'$expr': {'$lte': ['$trash', 10]}}},
        {'$match': {'$expr': {'$gte': ['$plus', 5]}}},
        {'$sort': {'plus': -1}},
        {'$limit': 5}
    ]
    return db.shots.aggregate(aggregation)


def get_top_creepshotees():
    aggregation = [
        {'$match': {'$expr': {'$lte': ['$trash', 10]}}},
        {'$match': {'$expr': {'$gte': ['$plus', 2]}}},
        {'$unwind': '$creepshotee'},
        {'$group': {'_id': '$creepshotee', 'count': {'$sum': 1}}},
        {'$group': {'_id': '$count', 'ids': {'$push': '$_id'}}},
        {'$sort': {'_id': -1}},
        {'$limit': 5}
    ]
    return db.shots.aggregate(aggregation)
