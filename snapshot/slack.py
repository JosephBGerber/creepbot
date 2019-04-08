from re import compile
from os import environ
from requests import get, post
import time

_users = compile(r"(<@)([\w]+)([>|])")


def list_users(event):
    if "text" not in event:
        return []
    lst = []
    for user in _users.finditer(event["text"]):
        lst.append(user.group(2))
    return lst


def get_week(season):
    if season:
        return int((time.time()-season["start_ts"])//604800)
    else:
        return -1


def post_message(text, channel, oauth):
    post('https://slack.com/api/chat.postMessage', {
        'token': oauth,
        'channel': channel,
        'text': text
    })


def get_oauth(code):
    return get('https://slack.com/api/oauth.access', {
        'client_id': environ["CLIENT_ID"],
        'client_secret': environ["CLIENT_SECRET"],
        'code': code
    }).json()


def react(channel, timestamp, token, reaction):
    post('https://slack.com/api/reactions.add', {
        'channel': channel,
        'name': reaction,
        'timestamp': timestamp,
        'token': token
    })
