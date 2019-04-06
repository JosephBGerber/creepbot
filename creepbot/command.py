from flask import jsonify
from os import environ


def join_ids(ids):
    return ', '.join(f'*<@{name}>*' for name in ids)


def help_command():
    plus = environ["PLUS_REACTION"]
    trash = environ["TRASH_REACTION"]

    text = f"Reply to a creepshot with :{plus}: if you think it's advanced and it deserves a point!\n\n" + \
           f"Reply to a creepshot with :{trash}: if you think it's trash.\n\n" + \
           f"Every :{plus}: gives a point to the creepshoter, but if a creepshot gets enough :{trash}: all " + \
           f"its points are lost.\n\n" + \
           f"At the end of the week the users with the most points gets a win!\n\n" + \
           f"Get the most wins by the end of the semester to become the season champion!!\n\n" + \
           f"Try using /creepbot to get statistics about the game."

    return jsonify(response_type='ephemeral', text=text)


def fail_command():
    return jsonify(response_type='ephemeral',
                   text='Usage: `/creepbot` `best|worst|wins|@user` [week|season|all-time]')


def best_command(time_range, top_users):
    text = f"Users with the most likes of {time_range}:\n"
    for index, reactions in enumerate(top_users, 1):
        text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'

    return jsonify(response_type='ephemeral', text=text)


def worst_command(time_range, top_targets):
    text = f"Most targeted users of {time_range}:\n"

    for index, reactions in enumerate(top_targets, 1):
        text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'

    return jsonify(response_type='ephemeral', text=text)


def wins_command(season, season_wins):
    if not season:
        text = "There is no current season."
        return jsonify(response_type='ephemeral', text=text)
    else:
        text = "Users with the most wins of this season:\n"
        for index, reactions in enumerate(season_wins, 1):
            text += f'{index}. {join_ids(reactions["creepshoters"])} - {reactions["_id"]}\n'

        return jsonify(response_type='ephemeral', text=text)


def user_command(season, user, wins, points):
    if season:
        text = f"<@{user}> has earned {points} points and won {wins} time(s)."
    else:
        text = f"<@{user}> has earned {points} points."

    return jsonify(response_type='ephemeral', text=text)


def gm_start_season_command(name):

        plus = environ["PLUS_REACTION"]
        trash = environ["TRASH_REACTION"]

        text = f"Welcome to creepshot season {name}!!\n\n" + \
               f"Reply to a creepshot with :{plus}: if you think it's advanced and it deserves a point!\n\n" + \
               f"Reply to a creepshot with :{trash}: if you think it's trash.\n\n" + \
               f"Every :{plus}: gives a point to the creepshoter, but if a creepshot gets enough :{trash}:" + \
               f" all its points are ignored.\n\n" + \
               f"At the end of the week the users with the most points gets a win!\n\n" + \
               f"Get the most wins by the end of the semester to become the season champion!!\n\n" + \
               f"Try using /creepbot to get statistics about the game."

        return jsonify(response_type='in_channel', text=text)


def gm_end_season_command(champion):

    text = f"Congratulations <@{champion}> you’re the creepshot champion.\n\n" + \
           "Go find a creepbot gm to receive your paper crown!\n\n" + \
           "That’s all for this semester so there will be no more wins until next season, " + \
           "but your all-time score is still being updated so keep posting those creepshots!"

    return jsonify(response_type='in_channel', text=text)


def gm_week_command(champion):
    text = f"Congratulations to <@{champion}> for getting the most points this week!"
    return jsonify(response_type="in_channel", text=text)

