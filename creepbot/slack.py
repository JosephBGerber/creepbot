from re import compile
from os import environ
from requests import get, post

_users = compile(r"<@[\w]+>")


def list_users(event):
    if "text" not in event:
        return 0
    return _users.findall(event["text"])


def get_channel(channel):
    return '#' + get('https://slack.com/api/channels.info', {
        'channel': channel,
        'token': environ['OAUTH_TOKEN']
    }).json()['channel']['name']


def get_user_name(user):
    json = get('https://slack.com/api/users.info', {
        'token': environ['OAUTH_TOKEN'],
        'user': user
    }).json()
    return json['user']['profile']['display_name']


def react(channel, timestamp, reaction):
    post('https://slack.com/api/reactions.add', {
        'channel': channel,
        'name': reaction,
        'timestamp': timestamp,
        'token': environ['OAUTH_TOKEN']
    })
