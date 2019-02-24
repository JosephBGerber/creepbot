from pymongo import MongoClient
from bson import Decimal128
from creepbot.slack import list_users, react, get_week
from os import environ
import time


db = MongoClient(environ["MONGODB_URI"])


def get_season(team_id):
    return db[team_id]['seasons'].find_one({'ended': False})


class DatabaseWrapper:

    def __init__(self, team_id, season):
        self.team_id = team_id
        self.season = season

    def start_season(self, name):
        return db[self.team_id]['seasons'].insert_one({"name": name, "start_ts": self.get_time_range("week"), "ended": False,
                                                       "team_id": self.team_id})

    def end_season(self):
        return db[self.team_id]['seasons'].update_one({'ended': False}, {'$set': {"ended": True, "end_ts": time.time()}})

    def create_creepshot(self, event):
        ts = event["ts"]
        channel = event["channel"]
        user = event["user"]
        lst = list_users(event)
        week = get_week(self.season)

        if len(lst) > 0:
            db[self.team_id].shots.insert_one({"ts": Decimal128(ts), "channel": channel, "creepshoter": user, "week": week,
                                               "creepshotee": list_users(event), "plus": -1, "trash": -1})

            react(channel, ts, environ["PLUS_REACTION"])
            react(channel, ts, environ["TRASH_REACTION"])
        else:
            pass

    def increment_plus(self, ts):
        db[self.team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"plus": 1}})

    def decrement_plus(self, ts):
        db[self.team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"plus": -1}})

    def increment_trash(self, ts):
        db[self.team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"trash": 1}})

    def decrement_trash(self, ts):
        db[self.team_id]['shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"trash": -1}})

    def get_top_creepshoters(self, time_range):
        aggregation = [
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range(time_range)]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': '$creepshoter', 'count': {'$sum': '$plus'}}},
            {'$group': {'_id': '$count', 'ids': {'$push': '$_id'}}},
            {'$sort': {'_id': -1}},
            {'$limit': 5}
        ]

        return db[self.team_id]['shots'].aggregate(aggregation)

    def get_top_creepshotees(self, time_range):
        aggregation = [
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range(time_range)]}}},
            {'$match': {'$expr': {'$lte': ['$trash', 10]}}},
            {'$unwind': '$creepshotee'},
            {'$group': {'_id': '$creepshotee', 'count': {'$sum': 1}}},
            {'$group': {'_id': '$count', 'ids': {'$push': '$_id'}}},
            {'$sort': {'_id': -1}},
            {'$limit': 5}
        ]

        return db[self.team_id]['shots'].aggregate(aggregation)

    def get_season_wins(self):
        aggregation = [
            {'$match': {'$expr': {'$lt': ['$ts', self.get_time_range("week")]}}},
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range("season")]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': {'creepshoter': '$creepshoter', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
            {'$group': {'_id': '$_id.week', 'creepshoters': {'$push': '$_id.creepshoter'}, 'sums': {'$push': '$sum'}}},
            {'$project': {'_id': '$_id', 'creepshoters': {'$arrayElemAt': ['$creepshoters', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
            {'$group': {'_id': '$creepshoters', 'wins': {'$sum': 1}}},
            {'$group': {'_id': '$wins', 'creepshoters': {'$push': '$_id'}}},
            {'$sort': {'_id': -1}},
            {'$limit': 5}
        ]

        return db[self.team_id]['shots'].aggregate(aggregation)

    def get_user_stats(self, time_range, user):
        aggregation = [
            {'$match': {'$expr': {'$lt': ['$ts', self.get_time_range("week")]}}},
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range("season")]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': {'creepshoter': '$creepshoter', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
            {'$group': {'_id': '$_id.week', 'creepshoters': {'$push': '$_id.creepshoter'}, 'sums': {'$push': '$sum'}}},
            {'$project': {'_id': '$_id', 'creepshoters': {'$arrayElemAt': ['$creepshoters', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
            {'$group': {'_id': '$creepshoters', 'wins': {'$sum': 1}}},
            {'$match': {'_id': user}}
        ]

        try:
            wins = db[self.team_id]['shots'].aggregate(aggregation).next().get('wins')
        except StopIteration:
            wins = 0

        aggregation = [
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range(time_range)]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$match': {'$expr': {'$gte': ['$plus', 1]}}},
            {'$group': {'_id': '$creepshoter', 'count': {'$sum': '$plus'}}},
            {'$match': {'_id': user}}
        ]

        try:
            points = db[self.team_id]['shots'].aggregate(aggregation).next().get('count')
        except StopIteration:
            points = 0

        return wins, points

    def get_season_champion(self):
        aggregation = [
            {'$match': {'$expr': {'$lt': ['$ts', self.get_time_range("week")]}}},
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range("season")]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': {'creepshoter': '$creepshoter', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
            {'$group': {'_id': '$_id.week', 'creepshoters': {'$push': '$_id.creepshoter'}, 'sums': {'$push': '$sum'}}},
            {'$project': {'_id': '$_id', 'creepshoters': {'$arrayElemAt': ['$creepshoters', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
            {'$group': {'_id': '$creepshoters', 'wins': {'$sum': 1}}},
            {'$sort': {'wins': -1}},
            {'$limit': 1}]

        try:
            champ = db[self.team_id]['shots'].aggregate(aggregation).next().get("_id")
        except StopIteration:
            champ = "Nobody"

        return champ

    def get_time_range(self, time_range):
        if time_range == "all-time":
            return 0

        if time_range == "season":
            if self.season is None:
                return 0
            else:
                return self.season["start_ts"]

        if time_range == "week":
            """Calculates the epoch time of last Sunday@6:00"""
            return time.time() - (time.time() % 604800) - 280800
