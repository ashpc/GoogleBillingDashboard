__author__ = 'ashwini'

'''
    __doc__ = "Any DB connection or query is executed here"
'''

from sqlalchemy.sql import func
from apps.config.apps_config import db_session, log
from apps.billing.models import Billing, Project, AlchemyEncoder
import json
import re, datetime


'''
    Create tables for the first time
'''


def create_table():
    db_session.create_all()
    return True


'''
    Get the list of distinct projects from billing table

    SELECT  DISTINCT(project_id) FROM reporting.billing;
'''


def get_distinct_projects():
    project_list = db_session.query(Billing.project_id).distinct()

    return project_list


'''
    Get the list of cost centers from project table

    SELECT distinct(cost_center) FROM reporting.projects;
'''


def get_cost_centers(unique):
    if unique:
        center_list = db_session.query(Project.cost_center).distinct()
    else:
        center_list = db_session.query(Project).all()
    return center_list


'''
    Get list of distinct project ids from project table

    SELECT DISTINCT(project_id) FROM reporting.project;
'''

def get_project_ids():
    project_list = db_session.query(Project.project_id).distinct()
    project_ids = (item[0] for item in project_list)

    return list(project_ids)

'''
    Get the list of projects already in projects table

    "SELECT project_id as project_id FROM reporting.projects where project_id = '12345';"
'''


def get_project(project_id):
    project = Project.query.filter_by(project_id=project_id).all()

    return project


'''
    Update project info in projects table

'''


def update_project(cost_center, project_id, project_name, director, director_email, contact_name, contact_email,
                   alert_amount):
    project = Project.query.filter_by(project_id=project_id).first()
    project.cost_center = cost_center
    project.project_name = project_name
    project.director = director
    project.director_email = director_email
    project.contact_name = contact_name
    project.contact_email = contact_email
    project.alert_amount = alert_amount

    db_session.commit()

    return project


'''
    Insert project info in projects table

'''


def create_project(cost_center, project_id, project_name, director, director_email, contact_name, contact_email,
                   alert_amount):
    project = Project(cost_center, project_id, project_name, director, director_email, contact_name, contact_email,
                      alert_amount)
    db_session.add(project)
    db_session.commit()

    return project


'''
    Delete project info in projects table
'''


def delete_project(project_id):
    project = Project.query.filter_by(project_id=project_id).first()

    db_session.delete(project)
    db_session.commit()

    return project


'''
    Get the list of resource_list from  usage table

    SELECT  DISTINCT(resource_type) FROM reporting.Billing where project_id in (" + project_ids + ");

'''


def get_resource_list_per_project(project_ids):
    resource_list = db_session.query(Billing.resource_type). \
        filter(Billing.project_id.in_(project_ids)). \
        distinct()
    return resource_list


'''
    Get billing data per year

    output_type ='month'
    SELECT EXTRACT(month FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 GROUP BY EXTRACT(month FROM Billing.usage_date)

    output_type ='quarter'
    SELECT EXTRACT(quarter FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 GROUP BY EXTRACT(quarter FROM Billing.usage_date)

    output_type ='week'
    SELECT EXTRACT(week FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 GROUP BY EXTRACT(week FROM Billing.usage_date)


'''


def get_billing_data_per_year(year, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year).group_by(func.unix_timestamp(Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year).group_by(
            func.extract(output_type, Billing.usage_date))
    return billing_data


'''
    Get billing data per year  month given

    output_type ='month'
    SELECT Billing.project_id AS usage_project_id, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND EXTRACT(month FROM Billing.usage_date) = :param_2
     GROUP BY Billing.project_id

'''


def get_billing_data_per_year_month(year, value_to_match, output_type):
    if year == value_to_match:
        billing_data = db_session.query(Billing.project_id, func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year).group_by(Billing.project_id)
    else:
        billing_data = db_session.query(Billing.project_id, func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract(output_type, Billing.usage_date) == value_to_match).group_by(Billing.project_id)

    return billing_data


def get_billing_data_per_year_month_week_day(year, value_to_match, output_type, project_ids):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   func.extract('month', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract('month', Billing.usage_date) == value_to_match).group_by(
            func.extract(output_type, Billing.usage_date), Billing.project_id)

    return billing_data


def get_billing_data_per_year_quarter_week_day(year, quarter, project_id, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   func.extract('quarter', Billing.usage_date) == quarter). \
            group_by(func.extract(output_type, Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   func.extract('quarter', Billing.usage_date) == quarter).group_by(
            func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   func.extract('quarter', Billing.usage_date) == quarter).group_by(
            func.extract(output_type, Billing.usage_date))

    return billing_data


'''
 NEED TO LOOK INTO THIS
'''


def get_billing_data_per_year_month_week_day_all(year, value_to_match, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract('month', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract('month', Billing.usage_date) == value_to_match).group_by(Billing.project_id,
                                                                                         func.extract(output_type,
                                                                                                      Billing.usage_date))

    return billing_data


'''
    GIVEN week
'''


def get_billing_data_per_year_week_day(year, value_to_match, output_type, project_ids):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   func.extract('week', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract('week', Billing.usage_date) == value_to_match).group_by(
            func.extract(output_type, Billing.usage_date), Billing.project_id)

    return billing_data


'''
    Get billing data per year per center
    ( project ids will be passed that will belong to a center)

    output_type ='month'
    SELECT EXTRACT(month FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM v.usage_date) = :param_1 AND Billing.project_id IN
    (:project_id_1, :project_id_2, :project_id_3) GROUP BY EXTRACT(month FROM Billing.usage_date)

    output_type ='week'
    SELECT EXTRACT(week FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id IN
    (:project_id_1, :project_id_2, :project_id_3) GROUP BY EXTRACT(week FROM Billing.usage_date)

'''


def get_billing_data_per_year_per_center(year, project_ids, output_type):
    if output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids)). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids)). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


'''
    Get billing data per year per center per day
    ( project ids will be passed that will belong to a center)

    SELECT unix_timestamp(Billing.usage_date) AS unix_timestamp_1, sum(Billing.cost)
    AS sum_1, Billing.usage_value AS usage_usage_value, Billing.measurement_unit AS usage_measurement_unit FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND
    Billing.project_id IN (:project_id_1, :project_id_2, :project_id_3)
    GROUP BY unix_timestamp(Billing.usage_date)

'''


def get_billing_data_per_year_per_center_days(year, project_ids):
    billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                    Billing.usage_value,
                                    Billing.measurement_unit). \
        filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids)). \
        group_by(func.unix_timestamp(Billing.usage_date))

    return billing_data


'''
    Get billing data per year per center by quarter
        ( project ids will be passed that will belong to a center)

    output_type='month'
    SELECT EXTRACT(month FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id
     IN (:project_id_1, :project_id_2, :project_id_3)
    AND EXTRACT(quarter FROM Billing.usage_date) = :param_2 GROUP BY EXTRACT(month FROM Billing.usage_date)

    output_type='week'
    SELECT EXTRACT(week FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id
    IN (:project_id_1, :project_id_2, :project_id_3)
    AND EXTRACT(quarter FROM Billing.usage_date) = :param_2 GROUP BY EXTRACT(week FROM Billing.usage_date)

'''


def get_billing_data_per_year_per_center_quarter(year, project_ids, quarter, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   func.extract('quarter', Billing.usage_date) == quarter). \
            group_by(func.extract(output_type, Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   func.extract('quarter', Billing.usage_date) == quarter). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   func.extract('quarter', Billing.usage_date) == quarter). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


'''
    Get billing data of each project for a year

    output_type='week'
    SELECT EXTRACT(week FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id = :project_id_1
     GROUP BY EXTRACT(week FROM Billing.usage_date)

    output_type='month'
    SELECT EXTRACT(month FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id = :project_id_1
     GROUP BY EXTRACT(month FROM Billing.usage_date)

    output_type='day'

    SELECT unix_timestamp(Billing.usage_date) AS unix_timestamp_1, sum(Billing.cost)
    AS sum_1, Billing.usage_value AS usage_usage_value, Billing.measurement_unit AS usage_measurement_unit FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id
    IN (:project_id_1, :project_id_2, :project_id_3)
    GROUP BY unix_timestamp(Billing.usage_date)

'''


def get_billing_data_per_project_year(year, project_id, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id). \
            group_by(func.unix_timestamp(Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


'''
    Get aggregated cost of each resource for a project for that month

    output_type='month'
    SELECT Billing.resource_type AS usage_resource_type, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND
    EXTRACT(month FROM Billing.usage_date) = :param_2 AND Billing.project_id = :project_id_1
    GROUP BY month(Billing.usage_date)

    output_type='week'
    SELECT Billing.resource_type AS usage_resource_type, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND
    EXTRACT(month FROM Billing.usage_date) = :param_2 AND Billing.project_id = :project_id_1
    GROUP BY week(Billing.usage_date)

'''


def get_billing_data_per_resource_month_center(year, value_to_match, project_id, output_type):
    billing_data = db_session.query(Billing.resource_type, func.sum(Billing.cost)). \
        filter(func.extract('year', Billing.usage_date) == year,
               func.extract(output_type, Billing.usage_date) == value_to_match,
               Billing.project_id == project_id, ). \
        group_by(Billing.resource_type)

    return billing_data


def get_billing_data_per_resource_month_week_day_center(year, value_to_match, project_id, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date),
                                        func.sum(Billing.cost), Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract('month', Billing.usage_date) == value_to_match, Billing.project_id == project_id). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(Billing.resource_type, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   func.extract('month', Billing.usage_date) == value_to_match).group_by(
            func.extract(output_type, Billing.usage_date), Billing.resource_type)

    return billing_data


def get_billing_data_per_resource_week_day_center(year, value_to_match, project_id, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date),
                                        func.sum(Billing.cost), Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year,
                   func.extract('week', Billing.usage_date) == value_to_match, Billing.project_id == project_id). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(Billing.resource_type, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   func.extract('week', Billing.usage_date) == value_to_match).group_by(
            func.extract(output_type, Billing.usage_date), Billing.resource_type)

    return billing_data


'''
    Get aggregated cost of each resource for a resource

    output_type='week'
    SELECT EXTRACT(week FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id
    IN (:project_id_1, :project_id_2, :project_id_3)
    AND resource_type =:resource_1
    GROUP BY EXTRACT(week FROM Billing.usage_date)

    output_type='month'
    SELECT EXTRACT(month FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND
    Billing.project_id IN (:project_id_1, :project_id_2, :project_id_3)
    AND resource_type =:resource_1
    GROUP BY EXTRACT(month FROM Billing.usage_date)

    output_type='day'

    SELECT unix_timestamp(Billing.usage_date) AS unix_timestamp_1, sum(Billing.cost)
    AS sum_1, Billing.usage_value AS usage_usage_value, Billing.measurement_unit AS usage_measurement_unit FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND
    Billing.project_id IN (:project_id_1, :project_id_2, :project_id_3)
    AND resource_type =:resource_1
    GROUP BY unix_timestamp(Billing.usage_date)

'''


def get_billing_data_per_resource(year, project_ids, resource, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource). \
            group_by(func.unix_timestamp(Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource). \
            group_by(func.extract(output_type, Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


'''
    Get aggregated  cost of a resource for a project for all months

    output_type='week'
    SELECT EXTRACT(week FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id =:project_id_1
    AND resource_type =:resource_1
    GROUP BY EXTRACT(week FROM Billing.usage_date)

    output_type='month'
    SELECT EXTRACT(month FROM Billing.usage_date) AS anon_1, sum(Billing.cost) AS sum_1 FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id = :project_id_1
    AND resource_type =:resource_1
    GROUP BY EXTRACT(month FROM Billing.usage_date)

    output_type='day'
    SELECT unix_timestamp(Billing.usage_date) AS unix_timestamp_1, sum(Billing.cost)
    AS sum_1, Billing.usage_value AS usage_usage_value, Billing.measurement_unit AS usage_measurement_unit FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id = :project_id_1
    AND resource_type =:resource_1
    GROUP BY unix_timestamp(Billing.usage_date)

'''


def get_billing_data_per_resource_per_project(year, project_id, resource, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource). \
            group_by(func.unix_timestamp(Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource). \
            group_by(func.month(Billing.usage_date))
    else:
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource). \
            group_by(func.month(Billing.usage_date))

    return billing_data


'''
    Get aggregated   cost of a resource for a project for a month


    output_type='day'/'month'/'week'

    SELECT unix_timestamp(Billing.usage_date) AS unix_timestamp_1, sum(Billing.cost)
    AS sum_1, Billing.usage_value AS usage_usage_value, Billing.measurement_unit AS usage_measurement_unit FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id = :project_id_1
    AND resource_type =:resource_1 AND EXTRACT(output_type FROM Billing.usage_date) = :param_1
    GROUP BY unix_timestamp(Billing.usage_date)

'''


def get_billing_data_per_resource_per_project_per_month(year, value_to_match, project_id, resource, output_type):
    if output_type == 'month' or output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('month', Billing.usage_date) == value_to_match). \
            group_by(func.unix_timestamp(Billing.usage_date))

    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract('week', Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('month', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


def get_billing_data_per_resource_per_project_per_quarter(year, value_to_match, project_id, resource, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('quarter', Billing.usage_date) == value_to_match). \
            group_by(func.unix_timestamp(Billing.usage_date))

    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('quarter', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))
    elif output_type == 'month' or output_type == 'week':
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('quarter', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


def get_billing_data_per_resource_per_project_per_week(year, value_to_match, project_id, resource, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('week', Billing.usage_date) == value_to_match). \
            group_by(func.unix_timestamp(Billing.usage_date))

    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract('week', Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id == project_id,
                   Billing.resource_type == resource, func.extract('week', Billing.usage_date) == value_to_match). \
            group_by(func.extract('week', Billing.usage_date))

    return billing_data


'''
    Get aggregated cost of a resource for all project for a month


    output_type='day'/'month'/'week'

    SELECT unix_timestamp(Billing.usage_date) AS unix_timestamp_1, sum(Billing.cost)
    AS sum_1, Billing.usage_value AS usage_usage_value, Billing.measurement_unit AS usage_measurement_unit FROM Billing
    WHERE EXTRACT(year FROM Billing.usage_date) = :param_1 AND Billing.project_id IN(:project_id_1,:project_2)
    AND resource_type =:resource_1 AND EXTRACT(output_type FROM Billing.usage_date) = :param_1
    GROUP BY unix_timestamp(Billing.usage_date)
'''


def get_billing_data_per_resource_all_project_per_day_month(year, value_to_match, project_ids, resource, output_type):
    if output_type == 'month' or output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('month', Billing.usage_date) == value_to_match). \
            group_by(func.unix_timestamp(Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('month', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


def get_billing_data_per_resource_all_project_per_day_week(year, value_to_match, project_ids, resource, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('week', Billing.usage_date) == value_to_match). \
            group_by(func.unix_timestamp(Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('week', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


def get_billing_data_per_resource_all_project_per_day_quarter(year, value_to_match, project_ids, resource, output_type):
    if output_type == 'day':
        billing_data = db_session.query(func.unix_timestamp(Billing.usage_date), func.sum(Billing.cost),
                                        Billing.usage_value,
                                        Billing.measurement_unit). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('quarter', Billing.usage_date) == value_to_match). \
            group_by(func.unix_timestamp(Billing.usage_date))
    elif output_type == 'week':
        billing_data = db_session.query(Billing.project_id, func.extract(output_type, Billing.usage_date),
                                        func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('quarter', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))
    elif output_type == 'month' or output_type == 'week':
        billing_data = db_session.query(func.extract(output_type, Billing.usage_date), func.sum(Billing.cost)). \
            filter(func.extract('year', Billing.usage_date) == year, Billing.project_id.in_(project_ids),
                   Billing.resource_type == resource, func.extract('quarter', Billing.usage_date) == value_to_match). \
            group_by(func.extract(output_type, Billing.usage_date))

    return billing_data


'''

 Set global cost_center_list
'''

'''
   get all cost_center_list to set global variable
'''


def set_global_cost_center_list():
    center_list = get_cost_centers(False)
    cost_center_list = []
    project_unique_ids = []
    for center in center_list:
        project = dict()

        center_data = json.loads(json.dumps(center, cls=AlchemyEncoder))
        project['cost_center'] = center_data['cost_center']
        project['project_id'] = center_data['project_id']
        project['project_name'] = center_data['project_name']
        project['director'] = '' if center_data['director'] is None else center_data['director']
        project['director_email'] = '' if center_data['director_email'] is None else center_data['director_email']
        project['contact_name'] = '' if center_data['contact_name'] is None else center_data['contact_name']
        project['contact_email'] = '' if center_data['contact_email'] is None else center_data['contact_email']
        project['alert_amount'] = '' if center_data['alert_amount'] == 0 else center_data['alert_amount']

        project_unique_ids.append(center_data['project_id'])

        cost_center_list.append(project)

    project_list = get_distinct_projects()

    for project in project_list:
        if project[0] not in project_unique_ids:
            cost_center_list.append(
                dict(cost_center='other', project_id=project[0], project_name=project[0], director='other',
                     director_email='', contact_name='', contact_email='', alert_amount=''))

    return cost_center_list
