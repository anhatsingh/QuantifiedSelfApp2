from flask import current_app as app
from flask import jsonify, make_response
from application.models import *
from flask_restful import Resource, reqparse
from flask_expects_json import expects_json
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

from .response_codes import *
from .json_schema import *
from datetime import datetime, timedelta
import scipy.stats as ss
import numpy as np
import collections
import application.data_access as da


@app.route("/api/tracker/<int:id>/stats/<string:period>", methods=["GET"])
@jwt_required()
def stats(id, period):
    try:
        user_id = get_jwt_identity()
        tracker_data = da.get_single_tracker(user_id, id)
        # if it exists, proceed.
        if tracker_data:
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            tdata = {
                'id': tracker_data.id,
                'name': tracker_data.name,
                'description': tracker_data.description,
                'user_id': tracker_data.user_id,
                'settings': ",".join([i.value for i in tracker_data.settings]),
                'type': datatypes[0] if len(datatypes) > 0 else '',
                'choices': {i.id: (i.value.strip() if i.value else '') for i in tracker_data.ttype}
            }
            log_data = []
            if tdata['type'] != 'timerange':
                chart_data = {}
            else:
                chart_data = []
            
            all_values = []
            for i in tracker_data.values:
                this_data = {
                    'id': i.id,
                    'timestamp': i.timestamp,
                    'note': i.note,
                    'value': [tdata['choices'][int(x.value)] for x in i.values] if tdata['type'] == 'ms' else [x.value for x in i.values]
                }
                log_data.append(this_data)

                if tdata['type'] == 'ms':                
                    options = list(set(this_data['value']))
                    for x in options:
                        if x in chart_data:
                            chart_data[x] += this_data['value'].count(x)
                        else:
                            chart_data[x] = this_data['value'].count(x)
                
                elif tdata['type'] in ['integer', 'float']:
                    all_values.append(int("".join(this_data['value'])) if tdata['type'] == 'integer' else float("".join(this_data['value'])))
                    include = False
                    difference_in_time = datetime.today() - this_data['timestamp']
                    if period == 'w' and difference_in_time.days <= 7:
                        ts = datetime.strftime(i.timestamp, "%Y-%m-%d")
                        include = True
                    elif period == 'm' and difference_in_time.days <= 30:
                        ts = datetime.strftime(i.timestamp, "%Y-%m-%d")                
                        include = True
                    elif period == 'd' and difference_in_time.days <= 0:
                        ts = datetime.strftime(i.timestamp, "%H:%M")                    
                        include = True
                    elif period == 'a':
                        ts = datetime.strftime(i.timestamp, "%Y-%m-%d")
                        include = True
                    
                    if include:
                        if ts in chart_data:
                            chart_data[ts] += int("".join(this_data['value'])) if tdata['type'] == 'integer' else float("".join(this_data['value']))
                        else:
                            chart_data[ts] = int("".join(this_data['value'])) if tdata['type'] == 'integer' else float("".join(this_data['value']))
                
                else:
                    theTime = ("".join(this_data['value'])).split('-')
                    start = theTime[0].strip()
                    end = theTime[1].strip()

                    difference_in_time = datetime.today() - datetime.strptime(start, timerange_format)
                    if period == 'w' and difference_in_time.days > 7:
                        start = datetime.strftime(datetime.today() - timedelta(7), timerange_format)
                    elif period == 'm' and difference_in_time.days > 30:
                        start = datetime.strftime(datetime.today() - timedelta(30), timerange_format)
                    elif period == 'd' and difference_in_time.days > 0:
                        start = datetime.strftime(datetime.today(), timerange_format)
                    elif period == 'a':
                        start = start
                    
                    endTimeDiff = datetime.today() - datetime.strptime(end, timerange_format)
                    if period == 'w' and endTimeDiff.days > 7:
                        end = start
                    elif period == 'm' and endTimeDiff.days > 30:
                        end = start
                    elif period == 'd' and endTimeDiff.days > 0:
                        end = start
                    elif period == 'a':
                        end = end

                    timeData = {
                        "id": this_data['id'],
                        "note": this_data['note'],
                        "start": start,
                        "end" :  end
                    }
                    if start != end:
                        chart_data.append(timeData)

            if tdata['type'] in ['integer', 'float']:
                if period == 'w':
                    delta = 7
                    for i in range(delta):
                        key = datetime.strftime(datetime.today()-timedelta(i), "%Y-%m-%d")
                        if key not in chart_data:
                            chart_data[key] = 0
                elif period == 'm':
                    delta = 30
                    for i in range(delta):
                        key = datetime.strftime(datetime.today()-timedelta(i), "%Y-%m-%d")
                        if key not in chart_data:
                            chart_data[key] = 0
                elif period == 'd':
                    delta = 24
                    for i in range(delta):
                        key = datetime.strftime(datetime.today()-timedelta(hours=i), "%H:00")
                        if key not in chart_data:
                            chart_data[key] = 0
            log_data = sorted(log_data, key=lambda d: d['timestamp'],reverse=True)
            extra = {}
            if tdata['type'] in ['integer', 'float'] and len(all_values) > 0:
                extra['mean'] = np.mean(all_values)
                extra['median'] = np.median(all_values)
                extra['25th'] = np.percentile(all_values, 25)
                extra['75th'] = np.percentile(all_values, 75)

            return make_response(jsonify(extra=extra, period = period, total=len(tracker_data.values), chart=collections.OrderedDict(sorted(chart_data.items())) if tdata['type'] != 'timerange' else chart_data), 200)
    except:
        db.session.rollback()
        app.logger.exception("API_REGISTER: Error occurred")
        return show_500()

@app.route('/tracker/<int:tracker_id>/autolog/<int:size>', methods=["GET"])
@jwt_required()
def auto_log(tracker_id, size):
    try:
        user_id = get_jwt_identity()
        tracker_data = da.get_single_tracker(user_id, tracker_id)
        # if it exists, proceed.
        if tracker_data:
            # get datatype of the tracker
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            # collect all the data about the current tracker being edited.
            data = {
                'id': tracker_data.id,
                'name': tracker_data.name,
                'description': tracker_data.description,
                'user_id': tracker_data.user_id,
                'settings': ",".join([i.value for i in tracker_data.settings]),
                # set datatype to empty if no type is defined earlier
                'type': datatypes[0] if len(datatypes) > 0 else '',
                # get all the choices of the tracker, replace NULL values with ''
                'choices': [i.id for i in tracker_data.ttype] if len(datatypes) > 0 else ''
            }

            if data['type'] == 'integer':
                x = np.arange(-10, 11)
                xU, xL = x + 0.5, x - 0.5 
                prob = ss.norm.cdf(xU, scale = 3) - ss.norm.cdf(xL, scale = 3)
                prob = prob / prob.sum() # normalize the probabilities so their sum is 1
                random_num = np.random.choice(x, size = size, p = prob)
                for i in range(len(random_num)):
                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = int(random_num[i]))
                    db.session.add(x)
                
                db.session.commit()
            
            elif data['type'] == 'float':
                random_num = np.random.random(size=size)
                for i in range(len(random_num)):
                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = float(random_num[i] * size))
                    db.session.add(x)
                
                db.session.commit()
            
            elif data['type'] == 'ms':
                random_num = np.random.choice(data['choices'], size=size)
                for i in range(len(random_num)):
                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = int(random_num[i]))
                    db.session.add(x)
                
                db.session.commit()
            
            elif data['type'] == 'timerange':            
                for i in range(size):
                    rands = np.random.randint(low=1, high=1000, size=2)
                    start = datetime.now() - timedelta(int(max(rands)))
                    end = datetime.now() - timedelta(int(min(rands)))
                    start = datetime.strftime(start, timerange_format)
                    end = datetime.strftime(end, timerange_format)

                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = str(start + ' - ' + end))
                    db.session.add(x)
                
                db.session.commit()
                da.cache.delete_memoized(da.get_all_tracker_type, tracker_data.id)
                da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_data.id)
                da.cache.delete_memoized(da.get_all_trackers, user_id)
                da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_data.id)
                
            return show_200("Autogen Success")
        else:
            return show_404()
    except:
        app.logger.exception("error occurred")
        return show_500()

@app.route('/tracker/<int:tracker_id>/logs/delete_all', methods = ['DELETE'])
@jwt_required()
def delete_all_tracker_logs(tracker_id):
    try:
        # check if a tracker with the provided id and made by current user exists or not.
        user_id = get_jwt_identity()
        tracker_data = da.get_single_tracker(user_id, tracker_id)
        # if it exists, proceed.
        if tracker_data:
            all_log_data = da.get_logs_by_tracker_id(tracker_data.id)
            if all_log_data:
                try:
                    for log_data in all_log_data:                                
                        db.session.delete(log_data)
                    db.session.commit()
                    da.cache.delete_memoized(da.get_all_tracker_type, tracker_data.id)
                    da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_data.id)
                    da.cache.delete_memoized(da.get_all_trackers, user_id)
                    da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_data.id)
                except:
                    app.logger.exception(f'Error ocurred while deleting all logs')
                    # if any internal error occurs, rollback the database
                    db.session.rollback()                    
                    return show_500()
                            
                return show_200("Deleted all logs")
            else:
                return show_404()
        else:
            return show_404()
    except:
        app.logger.exception("error occurred")
        return show_500()