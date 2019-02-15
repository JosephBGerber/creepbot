from flask import jsonify
from creepbot.database import get_top_creepshoters, get_top_creepshotees, get_season_wins, get_user_stats


join_ids = lambda ids: ', '.join(f'*<@{name}>*' for name in ids)


def fail_command():
    return jsonify(response_type='ephemeral',
                   text='Usage: `/creepbot` `best|worst|@user` [week|season|all-time]')


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

    if not season:
        text = f"<@{user}> has earned {points} points."
    else:
        text = f"<@{user}> has earned {points} points and won {wins} time(s)."

    return jsonify(response_type='ephemeral', text=text)
