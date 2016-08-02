from apps.application import app
import itertools
import datetime
import os
import simplejson
import logging

from apps.billing.models import Billing, Project
from apps.usage.models import Usage
from apps.config.apps_config import db_session, log, USAGE_VIEW,QUOTA_VIEW
from apps.usage.usageData import data_processor
from flask import Blueprint, request, redirect
from flask.wrappers import Response
from flask.templating import render_template
logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger()

mod = Blueprint('usage', __name__, url_prefix='/usage')

@mod.route('/')
@app.route('/index')
def index():
    # if USAGE_VIEW == 'True':
    #     url = 'usage/index.html'
    #     return render_template(url,quota_flag=QUOTA_VIEW, usage_flag=USAGE_VIEW, title="Cloud Admin Tool")
    #
    # return redirect('/')
    # return render_template('/', quota_flag=QUOTA_VIEW, usage_flag=USAGE_VIEW, title="Cloud Admin Tool")

    url = 'usage/index.html'
    return render_template(url,quota_flag=QUOTA_VIEW, usage_flag=USAGE_VIEW, title="Cloud Admin Tool")

@mod.route('/api/dbdump')
def getAllUsage():
    print("blah")
    data = db_session.query(Usage).all()
    data = [x.__dict__ for x in data]

    for x in data:
        x['usage_date'] = x['usage_date'].strftime('%Y-%m-%d')
        del x['_sa_instance_state']

    resp = Response(response=simplejson.dumps(data),
                    status=200,
                    mimetype="application/json")

    return resp


@mod.route('/api/usagetable', methods=['GET'])
def load_usage_table():
    year = request.args.get('year', None)
    month = request.args.get('month', None)
    project = request.args.get('project', None)

    data = db_session.query(Usage).all()
    data = [x.__dict__ for x in data]

    # year = 4 digit year
    if year is not None:
        data = filter(lambda x: x['usage_date'].year == int(year), data)

    # month = month num
    if month is not None:
        data = filter(lambda x: x['usage_date'].month == int(month), data)

    # project = project_name
    if project is not None:
        data = filter(lambda x: x['resource_uri'].split('/')[1] == str(project), data)


    for x in data:
        x['usage_date'] = x['usage_date'].strftime('%Y-%m-%d')
        del x['_sa_instance_state']

    data = list(data)

    resp = Response(response=simplejson.dumps(data), status=200, mimetype='application/json')

    return resp

@mod.route('/api/projectnames', methods=['GET'])
def getProjectNames():
    project_list = db_session.query(Project.project_name).distinct()
    project_names = [item[0] for item in project_list]

    resp = Response(response=simplejson.dumps(project_names), status=200, mimetype='application/json')
    return resp

@mod.route('/api/dbdump/projectId')
def getAllProjectId():
    print("blah")
    data = db_session.query(Usage.resource_id).distinct()

    # data = [x.__dict__ for x in data]
    new_data = []
    for (item) in data:
        new_data.append(item[0])

    resp = Response(response=simplejson.dumps(new_data),
                    status=200,
                    mimetype="application/json")

    return resp


@mod.route('/api/loadData')
def loadData():

    msg = data_processor('now')
    log.info(msg)
    resp = Response(response=msg['data'],
                    status=200,
                    mimetype="application/json")
    return resp
