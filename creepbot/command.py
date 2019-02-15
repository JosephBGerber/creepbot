from flask import jsonify
from creepbot.database import get_top_creepshoters, get_top_creepshotees, get_season_wins, get_user_stats, start_season, end_season, get_season_champion
from os import environ

join_ids = lambda ids: ', '.join(f'*<@{name}>*' for name in ids)


def help_command():
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


def fail_command():
    return jsonify(response_type='ephemeral',
                   text='Usage: `/creepbot` `best|worst|wins|@user` [week|season|all-time]')


def best_command(team_id, season, time_range):
    text = f"Users with the most likes of {time_range}:\n"

    for index, reactions in enumerate(get_top_creepshoters(team_id, season, time_range), 1):
        text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'

    return jsonify(response_type='ephemeral', text=text)


def worst_command(team_id, season, time_range):
    text = f"Most creepshoted users of {time_range}:\n"

    for index, reactions in enumerate(get_top_creepshotees(team_id, season, time_range), 1):
        text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'
    return jsonify(response_type='ephemeral', text=text)


def wins_command(team_id, season, time_range):
    if not season:
        text = "There is no current season."
        return jsonify(response_type='ephemeral', text=text)
    else:
        text = "Users with the most wins of this season:\n"

        for index, reactions in enumerate(get_season_wins(team_id, season, time_range), 1):
            text += f'{index}. {join_ids(reactions["creepshoters"])} - {reactions["_id"]}\n'
        return jsonify(response_type='ephemeral', text=text)


def user_command(team_id, season, time_range, user):
    wins, points = get_user_stats(team_id, season, time_range, user)

    if season:
        text = f"<@{user}> has earned {points} points and won {wins} time(s)."
    else:
        text = f"<@{user}> has earned {points} points."

    return jsonify(response_type='ephemeral', text=text)


def gm_start_season_command(team_id, season, name):
    if season:
        text = "There is already an active season."
        return jsonify(response_type='ephemeral', text=text)
    else:
        success = start_season(team_id, season, name)
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


def gm_end_season_command(team_id, season):
    result = end_season(team_id)
    if result.modified_count > 0:
        champ = get_season_champion(team_id, season)
        text = f"Congratulations <@{champ}> you’re the creepshot champion.\n\n" + \
               "Come find Joseph Gerber to receive your recognition and paper crown!\n\n" + \
               "That’s all for this semester so there will be no more wins until next season, " + \
               "but your all-time score is still being updated so keep posting those creepshots!"

        return jsonify(response_type='in_channel', text=text)

    else:
        text = "Ending season failed."
        return jsonify(response_type="ephemeral", text=text)
