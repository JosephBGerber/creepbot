from pymongo import MongoClient
from creepbot.slack import list_users, react
from os import environ


db = MongoClient(environ["MONGODB_URI"])[environ["MONGODB_DATABASE"]]


def create_creepshot(event):
    ts = event["ts"]
    channel = event["channel"]
    _id = ts + "@" + channel

    db.shots.insert_one({"_id": _id, "creepshoter": event["user"], "creepshotee": list_users(event),
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


