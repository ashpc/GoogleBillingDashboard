from apps.application import app
import itertools
import datetime
import os
import simplejson
import logging

from apps.billing.models import Billing, Project
from apps.usage.models import Usage
from apps.config.apps_config import db_session, log, USAGE_VIEW,QUOTA_VIEW
from apps.instance.instanceData import data_processor
from flask import Blueprint, request
from flask.wrappers import Response
from flask.templating import render_template
logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger()

mod = Blueprint('instance', __name__, url_prefix='/instance')

@mod.route('/')
@app.route('/index')
def instance():
    return "Hello Warld"

@mod.route('/api/loadData')
def get_instance_metadata():
    msg = data_processor('now')
    log.info(msg['data'])

    resp=Response(response=msg['data'], status=200, mimetype="application/json")

    return resp
