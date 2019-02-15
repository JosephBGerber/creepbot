from creepbot.slack import get_permalink, _users
from creepbot.database import create_creepshot, increment_plus, increment_trash, decrement_plus, decrement_trash, get_season
from creepbot.command import *
from flask import abort, Flask, request, jsonify
from os import environ
import pprint


app = Flask(__name__)


@app.route('/', methods=['POST'])
def main():
    json = request.json
    pprint.pprint(json)
    if request.json.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    season = get_season(json["team_id"])
    if json['type'] == 'url_verification':
        return json['challenge']

    team_id = json["team_id"]

    if "files" in json["event"] and json["event"]["type"] == "message" and json["event"]["channel"] == environ["CHANNEL"]:
        create_creepshot(team_id, json["event"])
        return ''

    if json["event"]["type"] == "reaction_added" and json["event"]["reaction"] == environ["PLUS_REACTION"]:
        increment_plus(team_id, json["event"]["item"]["ts"])

    if json["event"]["type"] == "reaction_added" and json["event"]["reaction"] == environ["TRASH_REACTION"]:
        increment_trash(team_id, json["event"]["item"]["ts"])

    if json["event"]["type"] == "reaction_removed" and json["event"]["reaction"] == environ["PLUS_REACTION"]:
        decrement_plus(team_id, json["event"]["item"]["ts"])

    if json["event"]["type"] == "reaction_removed" and json["event"]["reaction"] == environ["TRASH_REACTION"]:
        decrement_plus(team_id, json["event"]["item"]["ts"])

    return ''


@app.route('/command', methods=['POST'])
def statistics():
    if request.form.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    team_id = request.form.get("team_id")
    season = get_season(team_id)

    gm_list = ["UFWE1SCRK"]

    arguments = request.form.get('text', "").split(' ')
    print(arguments)

    user_result = _users.search(arguments[0])
    if arguments[0] not in ["help", "best", "worst", "wins", "gm_end", "gm_start"] and not user_result:
        return fail_command()

    if len(arguments) > 1 and arguments[1] in ["week", "season", "all-time"]:
        time_range = arguments[1]
    else:
        time_range = "week"

    if arguments[0] == "help":
        return help_command()

    if arguments[0] == "best":
        return best_command(team_id, season, time_range)

    if arguments[0] == "worst":
        return worst_command(team_id, season, time_range)

    if arguments[0] == "wins":
        return wins_command(team_id, season, time_range)

    if user_result:
        return user_command(team_id, season, time_range, user_result[2])

    if arguments[0] == "gm_start":
        if request.form.get("user_id") in gm_list:
            if len(arguments) < 2:
                return jsonify(text="Season name required")
            else:
                return gm_start_season_command(team_id, season, arguments[1])
        else:
            return jsonify(text="You're not a gm")

    if arguments[0] == "gm_end":
        if request.form.get("user_id") in gm_list:
            return gm_end_season_command(team_id, season)
        else:
            return jsonify(text="You're not a gm")

    return fail_command()


