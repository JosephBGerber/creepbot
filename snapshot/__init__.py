from snapshot.slack import get_oauth, _users
from snapshot.database import DatabaseWrapper
from snapshot.command import *
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

    return "Snapshot has been installed"


@app.route('/', methods=['POST'])
def main():
    json = request.json
    if request.json.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    if json['type'] == 'url_verification':
        return json['challenge']

    team_id = json["team_id"]
    db = DatabaseWrapper(team_id)

    if "files" in json["event"] and json["event"]["type"] == "message" and json["event"]["channel"] in environ["CHANNEL_LIST"].split():
        db.create_shot(json["event"])
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
    db = DatabaseWrapper(team_id)

    gm_list = environ["GM_LIST"].split()

    arguments = request.form.get('text', "").split(' ')

    user_result = _users.search(arguments[0])
    if arguments[0] not in ["help", "best", "worst", "wins", "gm_end", "gm_start", "gm_week"] and not user_result:
        return fail_command()

    if len(arguments) > 1 and arguments[1] in ["week", "season", "all-time"]:
        time_range = arguments[1]
    else:
        time_range = "week"

    if arguments[0] == "help":
        return help_command()

    if arguments[0] == "best":
        top_users = db.get_top_users(time_range)
        return best_command(time_range, top_users)

    if arguments[0] == "worst":
        top_targets = db.get_top_targets(time_range)
        return worst_command(time_range, top_targets)

    if arguments[0] == "wins":
        season_wins = db.get_season_wins()
        return wins_command(db.season, season_wins)

    if user_result:
        wins, points = db.get_user_stats("season", user_result[2])
        return user_command(db.season, user_result[2], wins, points)

    if arguments[0] == "gm_start":
        if request.form.get("user_id") not in gm_list:
            return jsonify(response_type='ephemeral', text="You're not a gm")
        if db.season:
            return jsonify(response_type='ephemeral', text="There is already an active season.")
        if len(arguments) < 2:
            return jsonify(response_type='ephemeral', text="Season name required")

        success = db.start_season(arguments[1])
        if success:
            return gm_start_season_command(arguments[1])

    if arguments[0] == "gm_end":
        if request.form.get("user_id") not in gm_list:
            return jsonify(response_type='ephemeral', text="You're not a gm")
        result = db.end_season()
        if result.modified_count == 0:
            return jsonify(response_type="ephemeral", text="Ending season failed.")

        champion = db.get_season_champion()
        return gm_end_season_command(champion)

    if arguments[0] == "gm_week":
        if request.form.get("user_id") not in gm_list:
            return jsonify(response_type='ephemeral', text="You're not a gm")
        if not db.season:
            return jsonify(response_type='ephemeral', text="There is no current season.")

        champion = db.get_last_weeks_winner()
        return gm_week_command(champion)

    return fail_command()


