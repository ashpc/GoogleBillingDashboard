import pytz

__author__ = 'ashwini'

"""Command-line sample application for listing all objects in a bucket using
the Cloud Storage API.

This sample is used on this page:

    https://cloud.google.com/storage/docs/json_api/v1/json-api-python-samples

For more information, see the README.md under /storage.
"""
import json
from apiclient import discovery
from oauth2client.client import GoogleCredentials
from apps.config.apps_config import BUCKET_NAME, ARCHIVE_BUCKET_NAME, log, db_session
import datetime
from apps.billing.models import Billing, Project
from apps.usage.usageData import data_processor as usage_processor
from apps.instance.instanceData import data_processor as instance_processor
from apscheduler.schedulers.background import BackgroundScheduler

import os
from sqlalchemy.exc import IntegrityError
import binascii

scheduler = BackgroundScheduler()


def run_scheduler():
    global scheduler
    log.info('---- In run_scheduler ----')
    scheduler.remove_all_jobs()
    scheduler.print_jobs()
    scheduler.add_job(data_processor, id='data_processor', args=['now'])
    scheduler.add_job(usage_processor, id='usage_data_processor', args=['now'])
    scheduler.add_job(instance_processor, id='instance_data_processor', args=['now'])
    log.info('------ Jobs List -----')
    scheduler.print_jobs()
    return scheduler


def set_scheduler(hour, min):
    global scheduler
    scheduler.remove_all_jobs()
    scheduler.print_jobs()
    log.info(' ----- IN SET SCHEDULER -----')
    scheduler.add_job(data_processor, 'cron', hour=get_time(hour, min)['hour'],
                      minute=get_time(hour, min)['mins'], second=get_time(hour, min)['sec'],
                      id='data_processor', args=['cron'])
    scheduler.add_job(usage_processor, 'cron', hour=get_time(hour, min)['hour'],
                      minute=get_time(hour, min)['mins'], second=get_time(hour, min)['sec'],
                      id='usage_data_processor', args=['cron'])
    scheduler.add_job(instance_processor, 'interval',
                      minutes=5,
                      id='instance_data_processor', args=['cron'])
    log.info('------ SCHEDULER INIT -----')
    log.info('------ Jobs List -----')
    scheduler.print_jobs()
    return scheduler


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
    message = 'Prcoess Complete '
    startTime = datetime.datetime.now()
    lock_file = True
    log.info('BUCKET_NAME')
    log.info(BUCKET_NAME)
    log.info('ARCHIVE_BUCKET_NAME')
    log.info(ARCHIVE_BUCKET_NAME)

    try:
        bucket = BUCKET_NAME
        archive_bucket = ARCHIVE_BUCKET_NAME
        random_number = binascii.hexlify(os.urandom(32)).decode()
        log.info(' RANDOM NUMBER --- {0}'.format(random_number))

        # Get the application default credentials. When running locally, these are
        # available after running `gcloud init`. When running on compute
        # engine, these are available from the environment.
        credentials = GoogleCredentials.get_application_default()

        # Construct the service object for interacting with the Cloud Storage API -
        # the 'storage' service, at version 'v1'.
        # You can browse other available api services and versions here:
        # https://developers.google.com/api-client-library/python/apis/
        service = discovery.build('storage', 'v1', credentials=credentials)

        # Make a request to buckets.get to retrieve a list of objects in the
        # specified bucket.
        req = service.buckets().get(bucket=bucket)
        resp = req.execute()

        # print(json.dumps(resp, indent=2))

        # Create a request to objects.list to retrieve a list of objects.
        fields_to_return = \
            'nextPageToken,items(name,size,contentType,metadata(my-key))'
        req = service.objects().list(bucket=bucket, fields=fields_to_return)
        file_count = 0
        log.info('Process {0} Start time --- {1}'.format(bucket, startTime))
        # If you have too many items to list in one request, list_next() will
        # automatically handle paging with the pageToken.
        while req:
            resp = req.execute()
            # print(json.dumps(resp, indent=2))
            if len(resp) == 0:
                log.info('############################################################################################')
                log.info('--------- THE BUCKET LIST IS EMPTY --------------')
                log.info('--------- NO FILES TO PROCESS  --------------')
                log.info(resp)
                log.info('############################################################################################')

            else:
                get_filenames(resp, service, random_number)

            req = service.objects().list_next(req, resp)

    except Exception as e:
        log.error(' Error in getting Bucket Details - {0}'.format(e[0]))
        message = e[0]
        status = 500

    endTime = datetime.datetime.now()
    log.info('Process End time --- {0}'.format(endTime))

    elapsedTime = endTime - startTime

    time = 'Total Time to Process all the files -- {0}'.format(divmod(elapsedTime.total_seconds(), 60))
    log.info(time)

    log.info(' ARGS PASSED --- {0}'.format(job_type))
    if job_type == 'now':
        set_scheduler(os.environ.get('SCHEDULER_HOUR'), os.environ.get('SCHEDULER_MIN'))

    response = dict(data=json.dumps(message), status=status, time=time)
    return response


def check_for_lock_file(filename, random_no, service):
    locked = True
    try:
        log.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

        log.info('------- GET THE {0} -- {1}------'.format(filename, random_no))
        # Get Payload Data
        req = service.objects().get(
            bucket=BUCKET_NAME,
            object=filename)
        get_file_meta_data = req.execute()


        # check for metadata -- lock
        lock_metadata = None
        startTime_metadata = None
        startTime_metadata_day = None
        startTime_metadata_month = None
        startTime_metadata_hour = None

        hourdiff = 0
        mindiff = 0

        today = utcnow().day
        thisMonth = utcnow().month
        now_hour = utcnow().hour
        now_min = utcnow().minute

        if today < 10:
            today = '0' + str(today)
        if thisMonth < 10:
            thisMonth = '0' + str(thisMonth)

        if 'metadata' in get_file_meta_data and 'lock' in get_file_meta_data['metadata']:
            lock_metadata = str(get_file_meta_data['metadata']['lock'])

        if 'metadata' in get_file_meta_data and 'startTime' in get_file_meta_data['metadata']:
            startTime_metadata = str(get_file_meta_data['metadata']['startTime'])
            startTime_metadata_month = startTime_metadata.split('-')[1]
            startTime_metadata_day = startTime_metadata.split('-')[2].split(" ")[0]
            startTime_metadata_hour = startTime_metadata.split('-')[2].split(" ")[1].split(":")[0]
            startTime_metadata_min = startTime_metadata.split('-')[2].split(" ")[1].split(":")[1]
            # check for time difference if more than 1 then restart the process
            hourdiff = int(now_hour) - int(startTime_metadata_hour)
            mindiff = int(now_min) - int(startTime_metadata_hour)

        log.info('METADATA -- {0} -- {1}'.format(lock_metadata, startTime_metadata))

        if lock_metadata is not None and startTime_metadata is not None \
                and startTime_metadata_day == str(today) and startTime_metadata_month == str(thisMonth) \
                and mindiff < 30:
            log.info(' Lock metadata found and is same day')
            locked = True
        else:
            log.info(' No lock metadata found  or StartTime was old')
            update_done = update_lockfile(filename, random_no, service)
            if update_done:
                log.info(' Updating the lock file was done -- Recheck for the random no --{0}'.format(random_no))
                req = service.objects().get(
                    bucket=BUCKET_NAME,
                    object=filename)
                get_file_meta_data = req.execute()
                lock_metadata = str(get_file_meta_data['metadata']['lock'])
                if lock_metadata == random_no:
                    log.info(' Checking for random No done   and MATCHED  -- Start the process --{0}'.format(random_no))
                    log.info(' File --{0}'.format(filename))
                    locked = False
                else:
                    log.info(' Checking for random No done   and DID NOT MATCH -- DO NOTHING')
                    locked = True
            else:
                log.info(' Updating the lock file was not done -- So donot do anything')
                locked = True
        log.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


    except Exception as e:
        log.error(' Error in getting Lock file  -- {0}'.format(e[0]))

    return locked


def update_lockfile(filename, lock_value, service):
    done = False
    try:
        resource = dict(metadata=dict(lock=lock_value, startTime=str(utcnow())))
        copy_object = service.objects().copy(sourceBucket=BUCKET_NAME, sourceObject=filename,
                                             destinationBucket=BUCKET_NAME, destinationObject=filename,
                                             body=resource)
        resp = copy_object.execute()
        done = True
    except Exception as e:
        log.error(' Error  while updating the lock file --- {0}'.format(e[0]))

    return done


def get_filenames(resp, service, random_number):
    try:
        for key, items in resp.iteritems():

            for item in items:
                log.info('############################################################################################')
                filename = item['name']

                lock_file = check_for_lock_file(filename, random_number, service)

                if not lock_file:
                    log.info('File was not locked and hence locking it and processing the files')
                    # ARCHIVE THE FILE FIRST
                    copy_resp = copy_file_to_archive(filename, service, BUCKET_NAME, ARCHIVE_BUCKET_NAME)
                    if len(copy_resp) == 0:
                        log.error(' ERROR IN COPYING FILE --- SKIPPING FILE -- {0} '.format(filename))
                    else:
                        log.info(' COPYING FILE DONE ')
                        log.info('Getting file -- {0}'.format(filename))
                        get_file_resp = get_file(filename, service)
                        if len(get_file_resp) == 0:
                            log.error('Error in getting file -- {0}'.format(get_file_resp))
                        else:
                            process_file_resp = process_file(filename, get_file_resp, service)
                            if len(process_file_resp) == 0:
                                log.error('Error in Processing file -- {0}'.format(filename))
                            else:
                                delete_resp = delete_file(filename, service)  # type is string if success

                                if isinstance(delete_resp, dict) and len(delete_resp) == 0:
                                    log.error(' Error in Deleting file --- {0} '.format(filename))
                else:
                    log.info(' {0} Locked --- Do Nothing -----'.format(filename))
                    continue

                log.info('############################################################################################')

    except Exception as e:
        log.error('Error in accessing File -- {0}'.format(e[0]))


def get_file(filename, service):
    file_content = dict()
    try:

        # Get Payload Data
        req = service.objects().get_media(
            bucket=BUCKET_NAME,
            object=filename)
        file_content = req.execute()

    except Exception as e:
        log.error('Error in getting the file -- {0}, {1}'.format(filename, e[0]))

    return file_content


def process_file(filename, file_content, service):
    insert_resp = dict()
    try:
        log.info('Processing file -- {0} -- STARTING'.format(filename))

        data_list = json.loads(file_content)
        '''
          parse the json and load the data to db
          once loading done move the file to archive folder

          todo : attach timestamp and tmp to file name while processing

        '''
        insert_resp = insert_usage_data(data_list, filename, service)
        insert_project_resp = insert_project__table_data(data_list, filename, service)

        log.info('Processing file -- {0} -- ENDING'.format(filename))

    except Exception as e:
        log.error('Error in processing the file -- {0}'.format(e[0]))
    return insert_resp


'''
    Insert billing info in usage table

'''


def insert_usage_data(data_list, filename, service):
    usage = dict()
    try:
        data_count = 0
        total_count = 0
        log.info('---- Starting to Add/Update billing data -----')
        for data in data_list:
            total_count += 1

            date = data['startTime']
            resource_type = str(data['lineItemId']).replace("com.google.cloud/services", "").replace(
                "com.googleapis/services", "")
            account_id = str(data['accountId'])
            usage_date = datetime.datetime.strptime(
                date.split("-")[0] + '-' + date.split("-")[1] + '-' + date.split("-")[2], "%Y-%m-%dT%H:%M:%S")
            # check if there is projectnumber else add it as Not available
            if 'projectNumber' in data:
                project_id = 'ID-' + str(data['projectNumber'])
            else:
                project_id = 'Not Available'

            if len(data['measurements']) != 0:
                usage_value = float(data['measurements'][0]['sum'])
                measurement_unit = str(data['measurements'][0]['unit'])
            else:
                usage_value = float(0)
                measurement_unit = str('none')
            # check if credits is there if so then add it to cost
            cost = float(data['cost']['amount'])
            if 'credits' in data:
                cost = float(data['cost']['amount'])
                # log.info('CREDITS PRESENT FOR THIS DATA')
                # log.info('cost before-- {0}'.format(cost))
                for credit in data['credits']:
                    cost += float(credit['amount'])
                    # log.info('{0}<---->{1}<----->{2}<------>{3}'.format(usage_date, project_id, credit['amount'], cost))
                    # log.info('cost after -- {0}'.format(cost))
            if cost == 0:
                # log.info('--- COST is 0 --- NOT adding to DB')
                continue
            else:
                # log.info('INSERTING DATA INTO DB -- {0}'.format(data))
                insert_done = insert_data(usage_date, cost, project_id, resource_type, account_id, usage_value,
                                          measurement_unit)
                if not insert_done:
                    log.info(data)
                    continue
                else:
                    data_count += 1

        usage = dict(message=' data has been added to db')
        log.info(
            'DONE adding {0} items out of {1} for file -- {2} into the db '.format(data_count, total_count, filename))
    except Exception as e:
        log.error('Error in inserting data into the DB -- {0}'.format(e[0]))
        db_session.rollback()

    return usage


'''
    Insert Project info in Project table

'''


def insert_project__table_data(data_list, filename, service):
    project = dict()
    try:
        data_count = 0
        total_count = 0
        log.info('---- Starting to Add/Update Project Name -----')
        for data in data_list:
            total_count += 1

            '''
                update the Project table with project_name with data['projectName']
                if there else use data['projectId'] if there else add as support
            '''
            if 'projectNumber' in data:
                project_id = 'ID-' + str(data['projectNumber'])
                if 'projectName' in data:
                    insert_done = insert_project_data(project_id, data['projectName'])
                else:
                    insert_done = insert_project_data(project_id, project_id)

            else:
                project_id = 'Not Available'
                insert_done = insert_project_data(project_id, 'support')

            if not insert_done:
                log.info(data)
                continue
            else:
                data_count += 1

        project = dict(message=' data has been added to db')
        log.info(
            'DONE adding {0} items out of {1} for file -- {2} into the db '.format(data_count, total_count, filename))
    except Exception as e:
        log.error('Error in inserting data into the DB -- {0}'.format(e[0]))
        db_session.rollback()

    return project


def insert_data(usage_date, cost, project_id, resource_type, account_id, usage_value, measurement_unit):
    done = False
    log.info('{0}<---->{1}<----->{2}<------>{3}<------>{4}'.format(usage_date, cost, project_id, resource_type,usage_value))
    try:
        usage = Billing(usage_date, cost, project_id, resource_type, account_id, usage_value, measurement_unit)
        db_session.add(usage)
        db_session.commit()
        done = True
    except IntegrityError as e:
        # log.info('---- DATA ALREADY IN DB --- UPDATE  ------')
        # log.info('{0}<---->{1}<----->{2}<------>{3}<------>{4}'.format(usage_date, cost, project_id, resource_type,usage_value))
        db_session.rollback()
        usage = Billing.query.filter_by(project_id=project_id, usage_date=usage_date,
                                        resource_type=resource_type).first()
        usage.cost = cost
        usage.usage_value = usage_value
        usage.measurement_unit = measurement_unit
        db_session.commit()

        done = True
    except Exception as e:
        log.error(' ------------- ERROR IN ADDING DATA TO THE DB ------------- {0}'.format(e[0]))
    return done


def insert_project_data(project_id, project_name):
    done = False
    log.info('{0}<---->{1}'.format(project_id, project_name))
    try:
        project = Project('other', project_id, project_name, 'other', '', '', '', 0)
        db_session.add(project)
        db_session.commit()
        done = True
    except IntegrityError as e:
        # log.info('---- Project DATA ALREADY IN DB --- UPDATE  ------')
        db_session.rollback()
        project = Project.query.filter_by(project_id=project_id).first()
        project.project_name = project_name
        db_session.commit()

        done = True
    except Exception as e:
        log.error(' ------------- ERROR IN ADDING DATA TO THE DB ------------- {0}'.format(e[0]))
    return done


def copy_file_to_archive(filename, service, main_bucket, dest_bucket):
    resp = dict()
    try:

        log.info('Starting to move the file to {0} ---- {1}'.format(dest_bucket, filename))

        copy_object = service.objects().copy(sourceBucket=main_bucket, sourceObject=filename,
                                             destinationBucket=dest_bucket, destinationObject=filename,
                                             body={})
        resp = copy_object.execute()

        log.info('DONE Moving of file - {0} to Archive -{1} '.format(filename, dest_bucket))

        # delete_moved_file(filename, service)

    except Exception as e:

        log.error('Error in Copying the object to archive folder - {0}'.format(e[0]))

    return resp


def delete_file(filename, service):
    resp = dict()
    try:
        log.info('Starting to Delete the file {0} from {1}'.format(filename, BUCKET_NAME))

        delete_object = service.objects().delete(bucket=BUCKET_NAME, object=filename)
        resp = delete_object.execute()

        log.info('DONE Deleting file - {0}  from - {1} '.format(filename, BUCKET_NAME))

    except Exception as e:
        log.error('Error in deleting the old file - {0}'.format(e[0]))
        # add code to add metadata or rename the file
    return resp


def set_scheduler_initial():
    print(' -------------- SETTING INITiAL SCHEDULER ---------------------')
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    log.info(os.environ.get('SCHEDULER_HOUR'))
    log.info(os.environ.get('SCHEDULER_MIN'))

    set_scheduler(os.environ.get('SCHEDULER_HOUR'), os.environ.get('SCHEDULER_MIN'))
