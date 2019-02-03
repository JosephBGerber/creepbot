from creepbot.slack import list_users
from creepbot.database import *
from flask import abort, Flask, jsonify, request
from os import environ
import pprint


#_get_names = lambda field, ids: sorted(get_name(field, id) for id in ids)
#_join_ids = lambda field, ids: ', '.join(f'*{name}*' for name in _get_names(field, ids))


app = Flask(__name__)


@app.route('/', methods=['POST'])
def main():
    pprint.pprint(request.json)
    json = request.json
    if request.json.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)

    if json['type'] == 'url_verification':
        return json['challenge']

    if "files" in json["event"] and json["event"]["type"] == "message" and len(list_users(json["event"])):
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


@app.route(f'/{environ["REACTION"]}', methods = ['POST'])
def statistics():
    if request.form.get('token') != environ['SLACK_VERIFICATION_TOKEN']:
        abort(403)
    arguments = request.form.get('text', '').split(' ')
    if len(arguments) == 0:
        return jsonify(response_type = 'ephemeral', text = f'Usage: `/creepbot` `scores` [`month|today|week|year`]')
    field = arguments[0]
    try:
        top = arguments[1]
    except:
        top = ''
    if top == 'today':
        text = 'today'
    elif top == 'month':
        text = 'this month'
    elif top == 'week':
        text = 'this week'
    elif top == 'year':
        text = 'this year'
    else:
        text = 'of all-time'
    text = 'Users with the most creepshots:\n'
    field = field[:-1]
    for index, reactions in enumerate(get_top_reactions(field, top), 1):
        text += f'{index}. {_join_ids(field, reactions["ids"])} - {reactions["_id"]}\n'
    return jsonify(response_type = 'in_channel', text = text)


def item_id(event):
    ts = event["item"]["ts"]
    channel = event["item"]["channel"]
    return ts + "@" + channel
