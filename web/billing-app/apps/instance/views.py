from apps.application import app
import itertools
import datetime
import os
import simplejson
import logging

from apps.billing.models import Billing, Project
from apps.instance.models import Instance
from apps.config.apps_config import db_session, log, USAGE_VIEW,QUOTA_VIEW
from apps.instance.instanceData import data_processor
from flask import Blueprint, request
from flask.wrappers import Response
from flask.templating import render_template
logging.basicConfig(level=logging.DEBUG)


mod = Blueprint('instance', __name__, url_prefix='/instance')

@mod.route('/')
@app.route('/index')
def instance():
    url = 'instance/index.html'
    return render_template(url,quota_flag=QUOTA_VIEW, usage_flag=USAGE_VIEW, title="Cloud Admin Tool")

@mod.route('/api/loadData')
def get_instance_metadata():
    msg = data_processor('now')
    log.info(msg['data'])

    resp=Response(response=msg['data'], status=200, mimetype="application/json")

    return resp

@mod.route('/api/instancetable', methods=['POST'])
def load_instance_table():
    body = request.get_json()
    log.info("------- body: {0} -------".format(body))
    machine_type = body.get('machine_type', None)
    tags = body.get('tags', None)
    project = body.get('project', None)
    month = body.get('month', None)
    year = body.get('year', None)

    data = db_session.query(Instance).order_by(Instance.instanceId).all()

    data = [x.__dict__ for x in data]

    for x in data:
        del x['_sa_instance_state']

    instance_obj_list = data
    instance_obj_list = build_objs(data)

    for x in instance_obj_list:
        if 'machineType' in x:
            x['machineType'] = x['machineType'].split('/')[-1]

    # project = project name
    if project is not None:
        project = project.lower()
        instance_obj_list = filter(lambda x: x['project']== project, instance_obj_list)

    # machine_type = just the machine type bit
    if machine_type is not None:
        instance_obj_list = filter(lambda x: x['machineType'] == machine_type, instance_obj_list)

    # tags should be filtered as AND
    if tags is not None:
        tags = [x.encode('UTF8') for x in tags]
        tags= set(tags)
        instance_obj_list = filter(lambda x: 'tags.items' in x and tags.issubset(set(x['tags.items'])), instance_obj_list)

    if year is not None:
        year = int(year)
        instance_obj_list = filter(lambda x: int(x['creationTimestamp'].split('-')[0]) == year, instance_obj_list)

    if month is not None:
        month = int(month)
        instance_obj_list = filter(lambda x: int(x['creationTimestamp'].split('-')[1]) == month, instance_obj_list)

    resp=Response(response=simplejson.dumps(instance_obj_list), status=200, mimetype="application/json")

    return resp


@mod.route('/api/machinetypes', methods=['GET'])
def get_machine_types():

    data = db_session.query(Instance).filter(Instance.key == 'machineType').all()
    data = (x.__dict__ for x in data)

    machine_types_list = [ y['value'].split('/')[-1] for y in data ]

    # remove duplicate machine types
    machine_types_list  = list(set(machine_types_list))


    resp = Response(response=simplejson.dumps(machine_types_list), status=200, mimetype="application/json")

    return resp

@mod.route('/api/tags')
def get_tags():

    data = db_session.query(Instance.value).filter(Instance.key == "tags.items").distinct()

    tmp = set()
    for x in data:
        x = tuple(x)
        tmp.add(x[0])

    data =  list(tmp)
    resp = Response(response=simplejson.dumps(data), status=200, mimetype="application/json")

    return resp

def build_objs(data):
    instances_obj = dict()

    for row in data:
        if row['instanceId'] not in instances_obj:
            instances_obj[row['instanceId']] = {}
        if row['key'] == 'tags.items':
            if 'tags.items' not in instances_obj[row['instanceId']]:
                instances_obj[row['instanceId']]['tags.items'] = []
            instances_obj[row['instanceId']]['tags.items'].append(row['value'])
        elif 'metadata' in row['key']:
            if 'metadata' not in instances_obj[row['instanceId']]:
                instances_obj[row['instanceId']]['metadata'] = []
            instances_obj[row['instanceId']]['metadata'].append({'key': row['key'].replace('metadata.', ''),'value':row['value']})
        elif 'disks' in row['key']:
            if 'disks' not in instances_obj[row['instanceId']]:
                instances_obj[row['instanceId']]['disks'] = []
            instances_obj[row['instanceId']]['disks'].append({'key': row['key'].replace('disks.', ''),'value':row['value']})

        else:
            temp = dict()
            temp[row['key']] = row['value']
            temp['instanceId'] = row['instanceId']
            instances_obj[row['instanceId']].update(temp)

    instances_list = [instances_obj[k] for k in instances_obj]

    return instances_list
