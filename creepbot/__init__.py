from creepbot.slack import list_users, get_permalink
from creepbot.database import *
from flask import abort, Flask, jsonify, request
from os import environ
import pprint


join_ids = lambda ids: ', '.join(f'*{name}*' for name in ids)


app = Flask(__name__)


@app.route('/', methods=['POST'])
def main():
    json = request.json
    if request.json.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    if json['type'] == 'url_verification':
        return json['challenge']

    if "files" in json["event"] and json["event"]["type"] == "message" and (len(list_users(json["event"])) > 0) and json["event"]["channel"] == environ["CHANNEL"]:

        create_creepshot(json["event"])
        return ''

    if json["event"]["type"] == "reaction_added" and json["event"]["reaction"] == environ["PLUS_REACTION"]:
        increment_plus(item_id(json["event"]))

    if json["event"]["type"] == "reaction_added" and json["event"]["reaction"] == environ["TRASH_REACTION"]:
        increment_trash(item_id(json["event"]))

    if json["event"]["type"] == "reaction_removed" and json["event"]["reaction"] == environ["PLUS_REACTION"]:
        decrement_plus(item_id(json["event"]))

    if json["event"]["type"] == "reaction_removed" and json["event"]["reaction"] == environ["TRASH_REACTION"]:
        decrement_plus(item_id(json["event"]))

    return ''


@app.route('/command', methods=['POST'])
def statistics():
    if request.form.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)
    arguments = request.form.get('text', '').split(' ')
    if len(arguments) == 0:
        return jsonify(response_type='ephemeral', text='Usage: `/creepbot` `best|targets|shots`')
    field = arguments[0]
    if field == "best":
        text = 'Cshers with the most points:\n'
        for index, reactions in enumerate(get_top_creepshoters(), 1):
            text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'
        return jsonify(response_type='in_channel', text=text)

    elif field == "shots":
        text = "Best creepshots of all time:\n"
        for index, reaction in enumerate(get_top_creepshots(), 1):
            ts, channel = reaction["_id"].split("@")
            link = get_permalink(channel, ts)
            text += f'{index}: {link} by {reaction["creepshoter"]} - {reaction["plus"]}\n'
        return jsonify(response_type="in_channel", text=text)

    elif field == "targets":
        text = "Most creepshotted cshers of all time:\n"
        for index, reactions in enumerate(get_top_creepshotees(), 1):
            pprint.pprint(reactions)
            text += f'{index}. {join_ids(reactions["ids"])} - {reactions["_id"]}\n'
        return jsonify(response_type='in_channel', text=text)

    else:
        return jsonify(response_type='ephemeral', text='Usage: `/creepbot` `users|scores`')


def item_id(event):
    ts = event["item"]["ts"]
    channel = event["item"]["channel"]
    return ts + "@" + channel
