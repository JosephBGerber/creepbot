from creepbot.slack import get_permalink, _users
from creepbot.database import *
from creepbot.command import fail_command, best_command, worst_command
from flask import abort, Flask, jsonify, request
from os import environ
import pprint


app = Flask(__name__)


@app.route('/', methods=['POST'])
def main():
    json = request.json
    pprint.pprint(json)
    if request.json.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

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

    arguments = request.form.get('text', "").split(' ')
    print(arguments)

    user_result = _users.search(arguments[0])
    if len(arguments) == 0 or arguments[0] not in ["best", "worst"] or user_result:
        return fail_command()

    if len(arguments) > 1 and arguments[1] in ["week", "season", "all-time"]:
        time_range = arguments[1]
    else:
        time_range = "week"

    if arguments[0] == "best":
        return best_command(team_id, season, time_range)

    if arguments[0] == "worst":
        return worst_command(team_id, season, time_range)

    return fail_command()


