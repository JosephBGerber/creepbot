from pymongo import MongoClient
from bson import Decimal128
from snapshot.slack import list_users, react, get_week
from os import environ
import time


db = MongoClient(environ["MONGODB_URI"])['creepbot']


def get_workspaces():
    return db['workspaces'].find({})


class DatabaseWrapper:

    def __init__(self, team_id):
        self.team_id = team_id
        self.season = db[team_id + 'seasons'].find_one({'ended': False})

    def create_shot(self, event):
        ts = event["ts"]
        channel = event["channel"]
        user = event["user"]
        lst = list_users(event)
        week = get_week(self.season)

        if self.season:
            season = self.season["name"]
        else:
            season = "none"

        if len(lst) > 0:
            db[self.team_id + 'shots'].insert_one({"ts": Decimal128(ts), "channel": channel, "user": user,
                                                   "targets": lst, "week": week, "season": season,
                                                   "plus": -1, "trash": -1})

            token = self.get_oauth()
            react(channel, ts, token, environ["PLUS_REACTION"])
            react(channel, ts, token, environ["TRASH_REACTION"])
            print(f"Shot {ts} created.")
        else:
            pass

    def increment_plus(self, ts):
        db[self.team_id + 'shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"plus": 1}})
        print(f"Shot {ts} plus incremented.")

    def decrement_plus(self, ts):
        db[self.team_id + 'shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"plus": -1}})
        print(f"Shot {ts} plus decremented.")

    def increment_trash(self, ts):
        db[self.team_id + 'shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"trash": 1}})
        print(f"Shot {ts} trash incremented.")

    def decrement_trash(self, ts):
        db[self.team_id + 'shots'].update_one({"ts": Decimal128(ts)}, {"$inc": {"trash": -1}})
        print(f"Shot {ts} trash decremented.")

    def set_channel(self, channel):
        db['workspaces'].update_one({"team_id": self.team_id}, {"$set": {"channel": channel}})

    def correct_channel(self, channel):
        set_channel = db['workspaces'].find_one({"team_id": self.team_id})["channel"]
        return set_channel == channel

    def start_season(self, name):
        return db[self.team_id + 'seasons'].insert_one({"name": name, "start_ts": self.get_time_range("week"),
                                                       "ended": False})

    def end_season(self):
        return db[self.team_id + 'seasons'].update_one({'ended': False},
                                                       {'$set': {"ended": True, "end_ts": time.time()}})

    def save_oauth(self, token):
        db['workspaces'].insert({"team_id": self.team_id, "channel": "null", "oauth": token})

    def get_oauth(self):
        return db['workspaces'].find_one({"team_id": self.team_id})["oauth"]

    def get_top_users(self, time_range, user=None):
        aggregation = []
        if user:
            aggregation += [{'$match': {'user': user}}]

        aggregation += [
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range(time_range)]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': '$user', 'count': {'$sum': '$plus'}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]

        return list(db[self.team_id + 'shots'].aggregate(aggregation))

    def get_top_targets(self, time_range):
        aggregation = [
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range(time_range)]}}},
            {'$match': {'$expr': {'$lte': ['$trash', 10]}}},
            {'$unwind': '$targets'},
            {'$group': {'_id': '$targets', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]

        return list(db[self.team_id + 'shots'].aggregate(aggregation))

    def get_season_wins(self, user=None):
        aggregation = [
            {'$match': {'$expr': {'$lt': ['$ts', self.get_time_range("week")]}}},
            {'$match': {'$expr': {'$gt': ['$ts', self.get_time_range("season")]}}},
            {'$match': {'$expr': {'$gt': ['$week', -1]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': {'user': '$user', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
            {'$group': {'_id': '$_id.week', 'users': {'$push': '$_id.user'}, 'sums': {'$push': '$sum'}}},
            {'$project': {'_id': '$_id',
                          'user': {'$arrayElemAt': ['$users', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
            {'$group': {'_id': '$user', 'wins': {'$sum': 1}}},
            {'$sort': {'wins': -1}},
        ]

        if user:
            aggregation += [{'$match': {'_id': user}}]

        aggregation += [{'$limit': 5}]

        return list(db[self.team_id + 'shots'].aggregate(aggregation))

    def get_last_weeks_winner(self):
        aggregation = [
            {'$match': {'$expr': {'$gt': ['$week', -1]}}},
            {'$match': {'$expr': {'$lt': ['$trash', 10]}}},
            {'$group': {'_id': {'user': '$user', 'week': '$week'}, 'sum': {'$sum': '$plus'}}},
            {'$group': {'_id': '$_id.week', 'users': {'$push': '$_id.user'}, 'sums': {'$push': '$sum'}}},
            {'$project': {'_id': '$_id',
                          'user': {'$arrayElemAt': ['$users', {'$indexOfArray': ['$sums', {'$max': '$sums'}]}]}}},
            {'$sort': {'_id': -1}}]

        wins = list(db[self.team_id + 'shots'].aggregate(aggregation))

        if len(wins):
            winner = wins[0]
        else:
            winner = "Nobody"

        return winner

    def get_user_stats(self, time_range, user):
        points = self.get_top_users(time_range, user)

        if len(points) == 1:
            points = points[0]['count']
        else:
            points = 0

        wins = self.get_season_wins(user)

        if len(wins) == 1:
            wins = wins[0]['wins']
        else:
            wins = 0

        return wins, points

    def get_season_champion(self):
        wins = self.get_season_wins()

        if len(wins) > 0:
            champion = wins[0]['_id']
        else:
            champion = "Nobody"

        return champion

    def get_time_range(self, time_range):
        if time_range == "all-time":
            return 0

        if time_range == "season":
            if self.season is None:
                return 0
            else:
                return self.season["start_ts"]

        if time_range == "week":
            """Calculates the epoch time of last Sunday@7:00 GMT-4:00"""
            gmtime = time.gmtime()
            wday = gmtime.tm_wday
            seconds = gmtime.tm_sec
            minutes = gmtime.tm_min + gmtime.tm_hour*60
            if wday == 6 and minutes >= 1380:
                return time.time() - (minutes-1380)*60 - seconds
            else:
                return time.time() - (wday + 1)*86400 - (minutes-1380)*60 - seconds
