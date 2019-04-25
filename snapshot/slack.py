from re import compile
from os import environ
from requests import get, post
import time
import pprint

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


def react(channel, timestamp, token, reaction):
    post('https://slack.com/api/reactions.add', {
        'channel': channel,
        'name': reaction,
        'timestamp': timestamp,
        'token': token
    })


def post_message(text, channel, token):
    response = post('https://slack.com/api/chat.postMessage', {
        'token': token,
        'channel': channel,
        'text': text
    })

    pprint.pprint(response)


def permalink(shot, token):
    return (get('https://slack.com/api/chat.getPermalink', {
        'token': token,
        'channel': shot['channel'],
        'message_ts': shot['ts']
    }),
            shot['plus'])


def get_oauth(code):
    return get('https://slack.com/api/oauth.access', {
        'client_id': environ["CLIENT_ID"],
        'client_secret': environ["CLIENT_SECRET"],
        'code': code
    }).json()



