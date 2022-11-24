from flask import current_app
from application.models import *
from flask_caching import Cache
from datetime import datetime, date
import calendar, traceback
from application.controllers.api.json_schema import date_format, timerange_format

cache = Cache(current_app)
current_app.app_context().push()

@cache.memoize(50)
def get_all_trackers(user_id):
    return Tracker.query.filter_by(user_id=user_id).all()


@cache.memoize(50)
def get_single_tracker(user_id, id):
    return Tracker.query.filter_by(user_id=user_id, id=id).one_or_none()

@cache.memoize(50)
def get_single_log(tracker_id, log_id):
    return Tracker_log.query.filter_by(tracker_id=tracker_id, id=log_id).one_or_none()

@cache.memoize(50)
def get_logs_by_tracker_id(tracker_id):
    return Tracker_log.query.filter_by(tracker_id = tracker_id).all()

@cache.memoize(50)
def get_single_tracker_type(tracker_id):
    return Tracker_type.query.filter_by(id=tracker_id).one_or_none()

@cache.memoize(50)
def get_all_tracker_type(tracker_id):
    return Tracker_type.query.filter_by(tracker_id=tracker_id).all()

@cache.memoize(50)
def get_monthly_data(user_id):
    try:
        trackers = [t for t in get_all_trackers(user_id)]
        data = []
        for i in trackers:            
            datatypes = list(set([x.datatype for x in i.ttype]))
            tdata = {
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'type': datatypes[0] if len(datatypes) > 0 else '',                
            }
            if tdata['type'] == 'ms':
                tdata['choices'] = []
                for x in i.ttype:
                    tdata['choices'].append({"id": x.id, "value": x.value})
            else:
                tdata['choices'] = None

            year = datetime.now().year
            month = datetime.now().month - 1 if datetime.now().month - 1 != 0 else 12
            endDate = calendar.monthrange(year, month)[1]
            all_log_data = Tracker_log.query.filter(Tracker_log.tracker_id == i.id).filter(Tracker_log.timestamp.between(date(year, month, 1), date(year, month, endDate))).all()

            if(tdata["type"] == 'integer' or tdata["type"] == 'float'):
                final_log_data = {
                    "count": 0,
                    "total": 0,
                    "mean": 0,
                    "max": -10000,
                    "min": 10000
                }
            elif(tdata['type'] == 'timerange'):
                final_log_data = {
                    "count": 0,
                    "time_spent": 0,
                    "max": 0,
                    "favorite": None
                }
            else:
                final_log_data = {
                    "count": 0,
                    "choices": {}
                }

            for log_data in all_log_data:
                if(tdata["type"] == 'integer'):
                    final_log_data["count"] += 1
                    final_log_data["total"] += int(log_data.values[0].value)
                    final_log_data["mean"] = float("{:.1f}".format(final_log_data["total"] / final_log_data["count"]))
                    final_log_data["max"] = int(log_data.values[0].value) if int(log_data.values[0].value) > final_log_data["max"] else final_log_data["max"]
                    final_log_data["min"] = int(log_data.values[0].value) if int(log_data.values[0].value) < final_log_data["min"] else final_log_data["min"]
                
                elif(tdata["type"] == 'float'):
                    final_log_data["count"] += 1
                    final_log_data["total"] += float("{:.1f}".format(float(log_data.values[0].value)))
                    final_log_data["mean"] = float("{:.1f}".format(final_log_data["total"] / final_log_data["count"]))
                    final_log_data["max"] = float("{:.1f}".format(float(log_data.values[0].value) if float(log_data.values[0].value) > final_log_data["max"] else final_log_data["max"]))
                    final_log_data["min"] = float("{:.1f}".format(float(log_data.values[0].value) if float(log_data.values[0].value) < final_log_data["min"] else final_log_data["min"]))

                elif(tdata["type"] == 'timerange'):
                    final_log_data["count"] += 1
                    temp = str(log_data.values[0].value).split('-')
                    difference = datetime.strptime(temp[1].strip(), date_format) - datetime.strptime(temp[0].strip(), date_format)
                    final_log_data["time_spent"] += divmod(difference.total_seconds(), 60)[0]
                    oldmax = final_log_data["max"]
                    final_log_data["max"] = divmod(difference.total_seconds(), 60)[0] if divmod(difference.total_seconds(), 60)[0]>final_log_data["max"] else final_log_data["max"]
                    if(oldmax != final_log_data["max"]):
                        final_log_data["favorite"] = log_data.note

                else:
                    final_log_data["count"] += 1
                    for i in log_data.values:
                        choice = get_single_tracker_type(i.value)
                        if choice.value in final_log_data["choices"]:
                            final_log_data["choices"][choice.value] += 1
                        else:
                            final_log_data["choices"][choice.value] = 1
            data.append({"tracker": tdata, "logs": final_log_data})
        return data
            
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_single_tracker_with_all_logs(user_id, id):
    try:
        tracker_data = get_single_tracker(user_id, id)
        if not tracker_data:
            print(tracker_data)
            return None,None
        datatypes = list(set([i.datatype for i in tracker_data.ttype]))
        tdata = {
            'id': tracker_data.id,
            'name': tracker_data.name,
            'description': tracker_data.description,
            'type': datatypes[0] if len(datatypes) > 0 else '',
            'settings': [i.value for i in tracker_data.settings]
        }
        if tdata['type'] == 'ms':
            tdata['choices'] = []
            for i in tracker_data.ttype:
                tdata['choices'].append({"id": i.id, "value": i.value})
        else:
            tdata['choices'] = None
        
        all_log_data = get_logs_by_tracker_id(tracker_data.id)
        
        if not all_log_data:
            print(all_log_data)
            return None,None
        
        final_data = []
        
        for log_data in all_log_data:
            ldata = {
                'id': log_data.id,
                'timestamp': datetime.strftime(log_data.timestamp, date_format),
                'note': log_data.note
            }                    
            if tdata['type'] == 'ms':
                ldata['value'] = []
                for i in log_data.values:
                    choice = get_single_tracker_type(i.value)
                    ldata['value'].append({"id": choice.id, "value": choice.value})
            
            elif tdata['type'] == 'integer':
                ldata['value'] = int(log_data.values[0].value)
            
            elif tdata['type'] == 'float':
                ldata['value'] = float(log_data.values[0].value)
            
            elif tdata['type'] == 'timerange':
                temp = str(log_data.values[0].value).split('-')
                ldata['start'], ldata['end'] = temp[0].strip(), temp[1].strip()
            
            final_data.append(ldata)
        return tdata, final_data
    
    except Exception as e:
        print(traceback.format_exc())
        return None, None