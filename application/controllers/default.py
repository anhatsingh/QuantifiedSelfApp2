from flask import Flask, request, redirect, url_for, flash, abort
from flask import render_template, make_response, jsonify
from flask import current_app as app
from flask_security import login_required
from application.models import *
from datetime import datetime


# ================================================HOME PAGE===============================================================
# default home page, required to login to see
@app.route('/')
#@login_required
def home_page():
    try:        
        return render_template('index.html')
    except:
        app.logger.exception("error occurred")
        abort(500)
# ========================================================================================================================