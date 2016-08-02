from flask.wrappers import Response
import json
import logging
from flask import Blueprint, request
from flask.templating import render_template
from apps.config.apps_config import QUOTA_VIEW, USAGE_VIEW

mod = Blueprint('login', __name__, url_prefix='/')


@mod.route('/')
def index():
    url = 'index.html'
    return render_template(url, quota_flag=QUOTA_VIEW, usage_flag=USAGE_VIEW, title="Cloud Admin Tool")


'''
            LOGIN API
'''


@mod.route('login', methods=['POST'])
def user_login():
    log.info('In Login Call')
    username = request.json['username']
    password = request.json['password']
    return login(username, password)


@mod.route('logout', methods=['POST'])
def user_logout():
    log.info('In Logout Call')
    username = request.json['username']
    return logout(username)


log = logging.getLogger()

login_list = [
    {'username': 'test', 'password': 'test'}
]


def login(username, password):
    data = dict()
    data['username'] = username.lower()
    data['password'] = password.lower()
    global login_list
    for user in login_list:
        if user['username'] == username.lower():
            if user['password'] == password.lower():
                data['login_cookie'] = 'success'
            else:
                data['login_error'] = 'Wrong Password'
            break
        else:
            data['login_error'] = 'User Name does not exist'

    resp = Response(response=json.dumps(data),
                    status=200,
                    mimetype="application/json")
    return resp


def logout(username):
    data = dict()
    data['username'] = username

    resp = Response(response=json.dumps(data),
                    status=200,
                    mimetype="application/json")
    return resp
