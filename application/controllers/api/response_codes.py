from flask import jsonify, make_response
from jsonschema import ValidationError
from flask import current_app as app

def show_200(msg="success"):
        return make_response(jsonify({"msg": msg, "status": "success"}), 200)

def show_404(msg = "The requested resource was not found on this server"):
    return make_response(jsonify({"msg": msg, "status": "error"}), 404)

def show_500():
    return make_response(jsonify({"msg": "Internal server error occurred", "status": "error"}), 500)

def show_400(msg = "Bad Request sent"):
    return make_response(jsonify({"msg": msg, "status": "error"}), 400)

def show_401(msg = "Bad data sent"):
    return make_response(jsonify({"msg": msg, "status": "error"}), 401)

def show_201(msg="created"):
    return make_response(jsonify({"msg": msg, "status": "success"}), 201)

@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({'msg': original_error.message, "status": "error"}), 400)
    return error