from flask import jsonify
from creepbot.database import DatabaseWrapper, get_season
from os import environ

join_ids = lambda ids: ', '.join(f'*<@{name}>*' for name in ids)


class CommandHandler:

    def __init__(self, team_id):
        self.team_id = team_id
        self.season = get_season(team_id)
        self.db = DatabaseWrapper(team_id, self.season)

    def help_command(self):
        plus = environ["PLUS_REACTION"]
        trash = environ["TRASH_REACTION"]

        text = f"Reply to a creepshot with :{plus}: if you think it's advanced and it deserves a point!\n\n" + \
               f"Reply to a creepshot with :{trash}: if you think it's trash.\n\n" + \
               f"Every :{plus}: gives a point to the creepshoter, but if a creepshot gets enough :{trash}: all" + \
               f"its points are lost.\n\n" + \
               f"At the end of the week the users with the most points gets a win!\n\n" + \
               f"Get the most wins by the end of the semester to become the season champion!!\n\n" + \
               f"Try using /creepbot to get statistics about the game."

        return jsonify(response_type='in_channel', text=text)

    def fail_command(self):
        return jsonify(response_type='ephemeral',
                       text='Usage: `/creepbot` `best|worst|wins|@user` [week|season|all-time]')

    def best_command(self, time_range):
        text = f"Users with the most likes of {time_range}:\n"
        for index, reactions in enumerate(self.db.get_top_creepshoters(time_range), 1):
            text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'
        return jsonify(response_type='ephemeral', text=text)

    def worst_command(self, time_range):
        text = f"Most creepshoted users of {time_range}:\n"
        for index, reactions in enumerate(self.db.get_top_creepshotees(time_range), 1):
            text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'
        return jsonify(response_type='ephemeral', text=text)

    def wins_command(self):
        if not self.season:
            text = "There is no current season."
            return jsonify(response_type='ephemeral', text=text)
        else:
            text = "Users with the most wins of this season:\n"

            for index, reactions in enumerate(self.db.get_season_wins(), 1):
                text += f'{index}. {join_ids(reactions["creepshoters"])} - {reactions["_id"]}\n'
            return jsonify(response_type='ephemeral', text=text)

    def user_command(self, time_range, user):
        wins, points = self.db.get_user_stats(time_range, user)

        if self.season:
            text = f"<@{user}> has earned {points} points and won {wins} time(s)."
        else:
            text = f"<@{user}> has earned {points} points."

        return jsonify(response_type='ephemeral', text=text)

    def gm_start_season_command(self, name):
        if self.season:
            text = "There is already an active season."
            return jsonify(response_type='ephemeral', text=text)
        else:
            success = self.db.start_season(name)
            if success:
                plus = environ["PLUS_REACTION"]
                trash = environ["TRASH_REACTION"]

                text = f"Welcome to creepshot season {name}!!\n\n" + \
                       f"Reply to a creepshot with :{plus}: if you think it's advanced and it deserves a point!\n\n" + \
                       f"Reply to a creepshot with :{trash}: if you think it's trash.\n\n" + \
                       f"Every :{plus}: gives a point to the creepshoter, but if a creepshot gets enough :{trash}: all" + \
                       f"its points are lost.\n\n" + \
                       f"At the end of the week the users with the most points gets a win!\n\n" + \
                       f"Get the most wins by the end of the semester to become the season champion!!\n\n" + \
                       f"Try using /creepbot to get statistics about the game."

                return jsonify(response_type='in_channel', text=text)

    def gm_end_season_command(self):
        result = self.db.end_season()
        if result.modified_count > 0:
            champ = self.db.get_season_champion()
            text = f"Congratulations <@{champ}> you’re the creepshot champion.\n\n" + \
                   "Come find Joseph Gerber to receive your recognition and paper crown!\n\n" + \
                   "That’s all for this semester so there will be no more wins until next season, " + \
                   "but your all-time score is still being updated so keep posting those creepshots!"

            return jsonify(response_type='in_channel', text=text)

        else:
            text = "Ending season failed."
            return jsonify(response_type="ephemeral", text=text)
