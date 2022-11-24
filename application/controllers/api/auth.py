from flask import current_app as app
from flask import jsonify, request
from application.models import *
from flask_security.utils import verify_password, hash_password
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_expects_json import expects_json

from .response_codes import *
from .json_schema import *

# ============================================================================AUTHORIZATION======================================================================
@app.route("/api/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email", None)
        password = request.json.get("password", None)
        user = User.query.filter_by(email=email).one_or_none()

        if user and verify_password(password, user.password):
            access_token = create_access_token(identity=user.id)
            return jsonify(name=user.username, token=access_token), 200
        
        return show_401("Bad username or Password")
    except:
        app.logger.exception("API_LOGIN: Error occurred")
        return show_500()

@app.route("/api/register", methods=["POST"])
@expects_json(register_user_schema)
def register():
    try:
        username = request.json.get("name", None)
        email = request.json.get("email", None)
        password = request.json.get("password", None)
        user = User.query.filter_by(email=email).one_or_none()

        if user == None:
            new_user = User(username=username, email=email, password=hash_password(password), active=1)
            db.session.add(new_user)
            db.session.commit()
            return jsonify(msg="New User Created"), 201
        else:
            return show_400('email already exists')
    except:
        db.session.rollback()
        app.logger.exception("API_REGISTER: Error occurred")
        return show_500()

# ==============================================================================================================================================================