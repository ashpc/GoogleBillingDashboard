import json
import csv
import pytz
import datetime
import os
import random
import binascii

from apps.config.apps_config import log, db_session
from apps.billing.billingDBQuery import get_project_ids
from apps.billing.models import Project
from apps.instance.models import Instance

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.exc import IntegrityError
from apiclient import discovery
from oauth2client.client import GoogleCredentials

scheduler = BackgroundScheduler()


def get_time(hour, mins):

    '''
    Add this if you need to have multiple processes in the same instance
    rand_no = random.randint(1, 10)
    mins = int(mins) + rand_no
    hour = int(hour)
    if mins > 60:
        hour += 1
        if hour > 23:
            hour = 0
    '''
    time = dict(hour=hour, mins=mins, sec=utcnow().second)
    return time


def utcnow():
    return datetime.datetime.now(tz=pytz.utc)


def data_processor(job_type):


    status = 200
    message = dict(success=[], fail=[])
    startTime = datetime.datetime.now()
    lock_file = True

    project_ids = get_project_ids()

    for project in project_ids:
        try:
            project = project.split('-')[1]
            log.info('--------- PROJECT ID: {0} --------------'.format(project))
            random_number = binascii.hexlify(os.urandom(32)).decode()
            # log.info(' RANDOM NUMBER --- {0}'.format(random_number))

            # Get the application default credentials. When running locally, these are
            # available after running `gcloud init`. When running on compute
            # engine, these are available from the environment.
            credentials = GoogleCredentials.get_application_default()

            # Construct the compute service object (version v1) for interacting
            # with the API. You can browse other available API services and versions at
            # https://developers.google.com/api-client-library/python/apis/
            service = discovery.build('compute', 'v1', credentials=credentials)

            zones = service.zones()
            request = zones.list(project=project)
            # get all zones for each project
            while request is not None:
                response = request.execute()

                # get all instance metadata for each zone
                for zone in response['items']:
                    z = zone['description'].encode('ascii','ignore')
                    instance_req = service.instances().list(project=project, zone=z)
                    while instance_req is not None:
                        instance_res = instance_req.execute()
                        if 'items' in instance_res:
                            insert_instance_data(instance_res['items'], z )


                        instance_req = service.instances().list_next(previous_request=instance_req, previous_response=instance_res)


                    request = zones.list_next(previous_request=request, previous_response=response)



            log.info('Process {0} Start time --- {1}'.format(project, startTime))
            # If you have too many items to list in one request, list_next() will
            # automatically handle paging with the pageToken.

            message['success'].append(project)

        except Exception as e:
            log.error(' Error in getting Project Details - {0}'.format(e))
            message['fail'].append({'project':project, 'error':str(e)})
            status = 500
            pass

    endTime = datetime.datetime.now()
    log.info('Process End time --- {0}'.format(endTime))

    elapsedTime = endTime - startTime

    time = 'Total Time to Process all the files -- {0}'.format(divmod(elapsedTime.total_seconds(), 60))
    log.info(time)

    log.info(' ARGS PASSED --- {0}'.format(job_type))

    response = dict(data=json.dumps(message), status=status, time=time)
    return response

'''
    Insert instance metadata in instance table

'''


def insert_instance_data(instance_list,zone):
    instance = dict()
    # data_list is a string in csv format
    # read csv to db

    try:

        for obj in instance_list:
            instance_id = obj['id']
            project_name = obj['zone'].split('/')[6]
            insert_data(instance_id, 'project', project_name)
            insert_data(instance_id, 'zone', zone)
            insert_data(instance_id, 'creationTimestamp', obj['creationTimestamp'])
            insert_data(instance_id, 'selfLink', obj['selfLink'])
            insert_data(instance_id, 'status', obj['status'])
            insert_data(instance_id, 'name', obj['name'])
            insert_data(instance_id, 'machineType', obj['machineType'])

            if 'tags' in  obj and 'items' in  obj['tags']['items']:
                for tag in obj['tags']['items']:
                    insert_data(instance_id, 'tags.items',tag)

            for networkInterfaces in obj['networkInterfaces']:
                insert_data(instance_id, 'networkInterfaces.network', networkInterfaces['network'])
                insert_data(instance_id, 'networkInterfaces.networkIP', networkInterfaces['networkIP'])
                for accessconfig in networkInterfaces['accessConfigs']:
                    if 'natIP' in accessconfig:
                        insert_data(instance_id, 'networkInterfaces.accessconfig.natIP', accessconfig['natIP'])

            for disk in obj['disks']:
                insert_data(instance_id, 'disks.type', disk['type'])
                insert_data(instance_id, 'disks.mode', disk['mode'])
                insert_data(instance_id, 'disks.interface', disk['interface'])
                insert_data(instance_id, 'disks.source', disk['source'])

                for license in disk['licenses']:
                    insert_data(instance_id, 'disks.license', license)

            if 'items' in obj['metadata']:
                for metadata in obj['metadata']['items']:
                    if metadata['key'] != 'ssh-keys':
                        insert_data(instance_id, 'metadata.'+ metadata['key'], metadata['value'])


            for serviceAccount in obj['serviceAccounts']:
                insert_data(instance_id, 'serviceAccounts.email', serviceAccount['email'])
                for scope in serviceAccount['scopes']:
                    insert_data(instance_id, 'serviceAccounts.scope', scope)

            insert_data(instance_id, 'scheduling.onHostMaintenance', obj['scheduling']['onHostMaintenance'])
            insert_data(instance_id, 'scheduling.automaticRestart', obj['scheduling']['automaticRestart'])
            insert_data(instance_id, 'scheduling.preemptible', obj['scheduling']['preemptible'])



    except Exception as e:
        log.error('Error in inserting data into the DB -- {0}'.format(e[0]))
        db_session.rollback()

    return instance


def insert_data(instanceId, key, value):
    done = False
    log.info('---- starting to add info to DB ----')
    try:
        log.info('--------------------- ADDED INFO TO DB ---------------------')
        instance = Instance(instanceId=instanceId, key=key, value=value)
        db_session.add(instance)
        db_session.commit()
        done = True
    except IntegrityError as e:
        log.info('---- DATA ALREADY IN DB --- UPDATE  ------')
        # log.info('{0}<---->{1}<----->{2}<------>{3}'.format(instanceId=instanceId, key=key, value=value))
        db_session.rollback()
        instance = Instance.query.filter_by( instanceId=instanceId, key=key, value=value).first()
        instance.value = value
        db_session.commit()

        done = True
    except Exception as e:
        log.error(' ------------- ERROR IN ADDING DATA TO THE DB ------------- {0}'.format(e[0]))

    return done
