import logging
from flask.app import Flask
from apps.config.apps_config import db_session
import os

app = Flask(__name__)

from apps.billing.views import mod as billingModule
from apps.login.views import mod as loginModule
from apps.quota.views import mod as quotaModule
from apps.usage.views import mod as usageModule
from apps.instance.views import mod as instanceModule
from apps.billing.views import init_scheduler
import sys, socket

app.register_blueprint(billingModule)
app.register_blueprint(loginModule)
app.register_blueprint(quotaModule)
app.register_blueprint(usageModule)
app.register_blueprint(instanceModule)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
    db_session.close()


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

#init_scheduler()

'''
  Init scheduler only once for all the workers
'''
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 47500))
except socket.error:
    print "!!!scheduler already started, DO NOTHING"
else:
    init_scheduler()
    print "scheduler started"
