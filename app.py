import os, logging
from flask import Flask

from application.config import LocalDevelopmentConfig
from application.database import db
from application.models import User, Role
from application import workers
from flask_security import Security, SQLAlchemySessionUserDatastore

from flask_restful import Api
from flask_jwt_extended import JWTManager
#from datetime import datetime

# set the configurations for the log file
logging.basicConfig(filename='debug.log', level=logging.INFO, format='[%(levelname)s %(asctime)s %(name)s] ' + '%(message)s')
# set app = None to initialize variable
app = None
api = None
jwt = None
celery = None

def create_app():
    '''This function creates a flask app along with all the necessary db, context, security relating things.
    '''
    # create flask app with name = __name__ and template folder where .html are stored
    app = Flask(__name__, template_folder='templates')

    # check if flask environment is is development
    if os.environ.get('FLASK_ENV') == 'development':
        app.logger.info('STARTING DEVELOPMENT ENVIRONMENT')
        # load development configurations
        app.config.from_object(LocalDevelopmentConfig)
    
    db.init_app(app)
    app.app_context().push()

    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    security = Security(app, user_datastore)
    app.app_context().push()
    api = Api(app)
    app.app_context().push()
    jwt = JWTManager(app)
    app.app_context().push()

    celery = workers.celery
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"],
    )

    celery.Task = workers.ContextTask
    app.app_context().push()

    app.logger.info('App setup complete.')
    
    return app, api, jwt, celery

app, api, jwt, celery = create_app()

import application.controllers.default
import application.controllers.api.json_schema
import application.controllers.api.response_codes
import application.controllers.api.auth
from application.controllers.api.trackers import Each_Tracker_api, Trackers_api
from application.controllers.api.logs import Each_Log_api, Logs_api
import application.controllers.api.stats

api.add_resource(Each_Tracker_api, "/api/tracker/<int:id>")
api.add_resource(Trackers_api, "/api/tracker")
api.add_resource(Each_Log_api, "/api/tracker/<int:tracker_id>/logs/<int:log_id>")
api.add_resource(Logs_api, "/api/tracker/<int:tracker_id>/logs")


if __name__ == '__main__':
    app.run()