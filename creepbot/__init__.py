from creepbot.slack import get_oauth, _users
from creepbot.database import DatabaseWrapper, get_season
from creepbot.command import CommandHandler
from flask import abort, Flask, request, jsonify
from os import environ
import pprint


app = Flask(__name__)


@app.route('/oauth', methods=['GET'])
def auth():
    code = request.args.get("code")
    oauth = get_oauth(code)
    team_id = oauth["team_id"]
    db = DatabaseWrapper(team_id, False)
    token = oauth['bot']['bot_access_token']
    db.save_oauth(token)

    return "Creepbot has been installed"


@app.route('/', methods=['POST'])
def main():
    json = request.json
    pprint.pprint(json)
    if request.json.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    if json['type'] == 'url_verification':
        return json['challenge']

    team_id = json["team_id"]
    season = get_season(json["team_id"])
    db = DatabaseWrapper(team_id, season)

    if "files" in json["event"] and json["event"]["type"] == "message" and json["event"]["channel"] in environ["CHANNEL_LIST"].split():
        db.create_creepshot(json["event"])
        return ''

    if json["event"]["type"] == "reaction_added" and json["event"]["reaction"] == environ["PLUS_REACTION"]:
        db.increment_plus(json["event"]["item"]["ts"])

    if json["event"]["type"] == "reaction_added" and json["event"]["reaction"] == environ["TRASH_REACTION"]:
        db.increment_trash(json["event"]["item"]["ts"])

    if json["event"]["type"] == "reaction_removed" and json["event"]["reaction"] == environ["PLUS_REACTION"]:
        db.decrement_plus(json["event"]["item"]["ts"])

    if json["event"]["type"] == "reaction_removed" and json["event"]["reaction"] == environ["TRASH_REACTION"]:
        db.decrement_trash(json["event"]["item"]["ts"])

    return ''


@app.route('/command', methods=['POST'])
def statistics():
    if request.form.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    team_id = request.form.get("team_id")
    c = CommandHandler(team_id)

    gm_list = environ["GM_LIST"].split()

    arguments = request.form.get('text', "").split(' ')
    print(arguments)

    user_result = _users.search(arguments[0])
    if arguments[0] not in ["help", "best", "worst", "wins", "gm_end", "gm_start", "gm_week"] and not user_result:
        return c.fail_command()

    if len(arguments) > 1 and arguments[1] in ["week", "season", "all-time"]:
        time_range = arguments[1]
    else:
        time_range = "week"

    if arguments[0] == "help":
        return c.help_command()

    if arguments[0] == "best":
        return c.best_command(time_range)

    if arguments[0] == "worst":
        return c.worst_command(time_range)

    if arguments[0] == "wins":
        return c.wins_command()

    if user_result:
        return c.user_command(time_range, user_result[2])

    if arguments[0] == "gm_start":
        if request.form.get("user_id") in gm_list:
            if len(arguments) < 2:
                return jsonify(text="Season name required")
            else:
                return c.gm_start_season_command(arguments[1])
        else:
            return jsonify(text="You're not a gm")

    if arguments[0] == "gm_end":
        if request.form.get("user_id") in gm_list:
            return c.gm_end_season_command()
        else:
            return jsonify(text="You're not a gm")

    if arguments[0] == "gm_week":
        if request.form.get("user_id") in gm_list:
            return c.gm_week_command()
        else:
            return jsonify(text="You're not a gm")
    return c.fail_command()


