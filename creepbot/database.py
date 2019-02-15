from pymongo import MongoClient
from bson import Decimal128
from creepbot.slack import list_users, react
from os import environ
import time


try:
    db = MongoClient(environ["MONGODB_URI"])
except:
    db = MongoClient()


def get_season(team_id):
    return db[team_id]['seasons'].find_one({'end_ts': False})


def create_creepshot(team_id, event):
    ts = event["ts"]
    channel = event["channel"]
    user = event["user"]
    lst = list_users(event)

    if len(lst) > 0:
        db[team_id].shots.insert_one({"ts": Decimal128(ts), "channel": channel, "creepshoter": user,
                             "creepshotee": list_users(event), "plus": -1, "trash": -1})

        react(channel, ts, environ["PLUS_REACTION"])
        react(channel, ts, environ["TRASH_REACTION"])
    else:
        pass


def increment_plus(team_id, ts):
    db[team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"plus": 1}})


def decrement_plus(team_id, ts):
    db[team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"plus": -1}})


def increment_trash(team_id, ts):
    db[team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"trash": 1}})


def decrement_trash(team_id, ts):
    db[team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"trash": -1}})


def get_top_creepshoters(team_id, season, time_range):
    aggregation = [
        {'$match': {'$expr': {'$gt': ['$ts', get_time_range(season, time_range)]}}},
        {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
        {'$match': {'$expr': {'$gte': ['$plus', 1]}}},
        {'$group': {'_id': '$creepshoter', 'count': {'$sum': '$plus'}}},
        {'$group': {'_id': '$count', 'ids': {'$push': '$_id'}}},
        {'$sort': {'_id': -1}},
        {'$limit': 5}
    ]

    return db[team_id]['shots'].aggregate(aggregation)


def get_top_creepshotees(team_id, season, time_range):
    aggregation = [
        {'$match': {'$expr': {'$gt': ['$ts', get_time_range(season, time_range)]}}},
        {'$match': {'$expr': {'$lte': ['$trash', 10]}}},
        {'$match': {'$expr': {'$gte': ['$plus', 1]}}},
        {'$unwind': '$creepshotee'},
        {'$group': {'_id': '$creepshotee', 'count': {'$sum': 1}}},
        {'$group': {'_id': '$count', 'ids': {'$push': '$_id'}}},
        {'$sort': {'_id': -1}},
        {'$limit': 5}
    ]

    return db[team_id]['shots'].aggregate(aggregation)


def get_season_wins(team_id, season, time_range):
    aggregation = [
    {'$match': {'$expr': {'$gt': ['$ts', get_time_range(season, "season")]}}},
    {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
    {'$group': {'_id': {'creepshoter': '$creepshoter', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
    {'$group': {'_id': '$_id.week', 'creepshoters': {'$push': '$_id.creepshoter'}, 'sums': {'$push': '$sum'}}},
    {'$project': {'_id': '$_id', 'creepshoters': {'$arrayElemAt': ['$creepshoters', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
    {'$group': {'_id': '$creepshoters', 'wins': {'$sum': 1}}},
    {'$group': {'_id': '$wins', 'creepshoters': {'$push': '$_id'}}},
    {'$sort': {'_id': -1}},
    {'$limit': 5}]

    return db[team_id]['shots'].aggregate(aggregation)


def get_user_stats(team_id, season, time_range, user):
    aggregation = [
        {'$match': {'$expr': {'$gt': ['$ts', get_time_range(season, "season")]}}},
        {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
        {'$group': {'_id': {'creepshoter': '$creepshoter', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
        {'$group': {'_id': '$_id.week', 'creepshoters': {'$push': '$_id.creepshoter'}, 'sums': {'$push': '$sum'}}},
        {'$project': {'_id': '$_id', 'creepshoters': {'$arrayElemAt': ['$creepshoters', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
        {'$group': {'_id': '$creepshoters', 'wins': {'$sum': 1}}},
        {'$match': {'_id': user}}
    ]

    try:
        wins = db[team_id]['shots'].aggregate(aggregation).next().get('wins')
    except StopIteration:
        wins = 0

    aggregation = [
        {'$match': {'$expr': {'$gt': ['$ts', get_time_range(season, time_range)]}}},
        {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
        {'$match': {'$expr': {'$gte': ['$plus', 1]}}},
        {'$group': {'_id': '$creepshoter', 'count': {'$sum': '$plus'}}},
        {'$match': {'_id': user}}
    ]

    try:
        points = db[team_id]['shots'].aggregate(aggregation).next().get('count')
    except StopIteration:
        points = 0

    return wins, points


def get_time_range(season, time_range):
    if time_range == "all-time":
        return 0

    if time_range == "season":
        if season is None:
            return 0
        else:
            return season["start_ts"]

    if time_range == "week":
        """Calculates the epoch time of last Sunday@6:00"""
        return time.time() - (time.time() % 604800) - 280800
