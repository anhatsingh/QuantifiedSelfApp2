from application.workers import celery
from application.helpers import send_mail
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask import current_app as app
from flask import render_template
from datetime import datetime, date
from application.models import *
from celery.schedules import crontab
import csv
from weasyprint import HTML
from application.controllers.api.json_schema import *
from application.database import db
import calendar, traceback, requests
import application.data_access as da
from application.helpers import make_file, delete_file

webhook_url = "https://chat.googleapis.com/v1/spaces/AAAA6eU_b5A/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=tMbTPwgBkqMyfWChWDSqEawkoEsU6cT9BJxbN2cS3rw%3D"

@app.template_filter()
def format_datetime(value, format='datetime'):
    if format == 'date':
        format="%d %b %Y"
    elif format == 'time':
        format="%H:%M"
    else:
        format="%H:%M, %d %b %Y"
    return datetime.strptime(value, date_format).strftime(format)

@app.template_filter()
def format_timerange(value, format='datetime'):
    format="%H:%M, %d %b %Y"
    return datetime.strptime(value, timerange_format).strftime(format)

@celery.on_after_configure.connect
def setup_monthly_report(sender, **kwargs):
    ids = [(u.id, u.email, u.username) for u in User.query.all()]
    for user in ids:
        sender.add_periodic_task(
            crontab(day_of_month=1),
            #10 * 60, # 10 minutes
            generate_monthly_report.s(user[0], user[1], user[2])
        )
        sender.add_periodic_task(
            crontab(hour=20),
            #10 * 60, # 10 minutes
            daily_reminder.s(user[0], user[2])
        )

@celery.task
def generate_monthly_report(user_id, user_mail, user_name):    
    tracker_data = da.get_monthly_data(user_id)    
    if(tracker_data):
        year = datetime.now().year
        month = datetime.now().month - 1 if datetime.now().month - 1 != 0 else 12
        endDate = calendar.monthrange(year, month)[1]
        data = {
            "username": user_name,
            "email": user_mail,
            "from_date": f'01-{month}-{year}',
            "to_date": f'{endDate}-{month}-{year}',
            "tdata": tracker_data
        }
        out_html = render_template("export_monthly.html", data=data)
        file = make_file(out_html, "pdf")        
        send_mail(user_mail, f"{month}-{year} Monthly Report", f"Dear {user_name},<br />Please find attached your monthly report for the term of 01-{month}-{year} to {endDate}-{month}-{year}. The file is in PDF Format.", file)
        delete_file(file)

@celery.task()
def generate_pdf_report(user_id, id):
    tracker, logs = da.get_single_tracker_with_all_logs(user_id, id)
    mail_id = User.query.filter_by(id=user_id).one_or_none().email
    current_date = datetime.now().strftime('%H:%M, %d %b %Y')
    
    out_html = render_template("export_single.html", tracker=tracker, logs=logs, user_id = user_id, user_mail = mail_id, today=current_date)
    file = make_file(out_html, "pdf")

    send_mail(mail_id, "Exported Data (PDF)", f"Dear User,<br />Please find attached all the data for your tracker <i>{tracker['name']}</i>. The file is in PDF Format.", file)

    delete_file(file)


@celery.task()
def generate_csv_report(user_id, id):
    tracker, logs = da.get_single_tracker_with_all_logs(user_id, id)
    mail_id = User.query.filter_by(id=user_id).one_or_none().email

    file = make_file([{"tracker": tracker, "logs": logs}], "csv")
    send_mail(mail_id, "Exported Data (CSV)", f"Dear User,<br />Please find attached all the data for your tracker <i>{tracker['name']}</i>. The file is in CSV Format.", file)
    delete_file(file)
    
@celery.task()
def daily_reminder(user_id, user_name):
    dt = date.today()    
    trackers = [t.id for t in Tracker.query.filter_by(user_id=user_id).all()]
    log_count = Tracker_log.query.filter(Tracker_log.tracker_id in trackers).filter(Tracker_log.timestamp.between(datetime.combine(dt, datetime.min.time()), dt)).count()
    if(log_count <= 0):        
        # sending get request and saving the response as response object
        r = requests.post(url = webhook_url, json = {"text": f"Hi {user_name}, You have not logged any value today. C'mon, don't leave me without values :("})
        # extracting data in json format
        data = r.json()