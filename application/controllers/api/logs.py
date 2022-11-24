from flask import current_app as app
from flask import jsonify, make_response
from application.models import *
from flask_restful import Resource, reqparse
from flask_expects_json import expects_json
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from datetime import datetime
import application.data_access as da

from .response_codes import *
from .json_schema import *

class Logs_api(Resource):
    @jwt_required()
    def get(self, tracker_id):
        try:
            user_id = get_jwt_identity()
            tracker_data = da.get_single_tracker(user_id, tracker_id)
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
                
                all_log_data = da.get_logs_by_tracker_id(tracker_data.id)
                if all_log_data:
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
                                choice = da.get_single_tracker_type(i.value)
                                ldata['value'].append({"choice_id": choice.id, "choice_name": choice.value})
                        
                        elif tdata['type'] == 'integer':
                            ldata['value'] = int(log_data.values[0].value)
                        
                        elif tdata['type'] == 'float':
                            ldata['value'] = float(log_data.values[0].value)
                        
                        elif tdata['type'] == 'timerange':
                            temp = str(log_data.values[0].value).split('-')
                            ldata['start'], ldata['end'] = temp[0].strip(), temp[1].strip()
                        
                        final_data.append(ldata)
                    
                    return make_response(jsonify(final_data), 200)
                else:
                    return show_404("No logs found for this tracker. Consider adding logs?")
            else:
                return show_404("Tracker not found")
        except:
            app.logger.exception("API_LA1")
            return show_500()
    
    @expects_json(add_logs_schema)
    @jwt_required()
    def post(self, tracker_id):
        user_id = get_jwt_identity()
        da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_id)
        tracker_data = da.get_single_tracker(user_id, tracker_id)
        if tracker_data:
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            data = {
                'id': tracker_data.id,
                'name': tracker_data.name,
                'description': tracker_data.description,
                'user_id': tracker_data.user_id,
                'settings': ",".join([i.value for i in tracker_data.settings]),
                'type': datatypes[0] if len(datatypes) > 0 else '',
                'choices': {i.id: (i.value if i.value else '') for i in tracker_data.ttype}
            }

            logs_input_args = reqparse.RequestParser()
            logs_input_args.add_argument('timestamp')
            logs_input_args.add_argument('note')
            #logs_input_args.add_argument('value', type=(int if (data['type'] in ['integer', 'ms']) else (float if data['type'] == 'float' else str)), action='append')
            logs_input_args.add_argument('value', action="append")

            args = logs_input_args.parse_args()
            timestamp = args.get('timestamp', None)
            note = args.get('note', None)
            values = args.get('value', None)            

            if timestamp == None:
                timestamp = datetime.strftime(datetime.now(), date_format)

            try:
                datetime.strptime(timestamp, date_format)
            except ValueError:
                return show_400(f'Timestamp is not in valid format, should be in the format {datetime.strftime(datetime.now(), date_format)}')

            if data['type'] == 'integer':
                try:
                    int(values[0])
                except:
                    return show_400(f"Value is in incorrect format. Expected {data['type']}")
            
            elif data['type'] == 'float':
                try:
                    float(values[0])
                except:
                    return show_400(f"Value is in incorrect format. Expected {data['type']}")
            
            elif data['type'] == 'ms':
                for i in values:
                    if int(i) not in data['choices']:
                        return show_400(f"choice id {i} does not exist")
            
            elif data['type'] == 'timerange':
                try:
                    temp = str(values[0]).split('-')
                    datetime.strptime(temp[0].strip(), timerange_format)
                    datetime.strptime(temp[1].strip(), timerange_format)
                except:
                    return show_400(f'Value is not in valid format, should be in the format \'{datetime.strftime(datetime.now(), timerange_format)} - {datetime.strftime(datetime.now(), timerange_format)}\'')

            try:
                log = Tracker_log(tracker_id = tracker_data.id, note = note, timestamp = datetime.strptime(timestamp, date_format))
                db.session.add(log)
                db.session.flush()
                
                if data['type'] == 'ms':
                    choices = values
                    for i in choices:
                        x = Tracker_log_value(log_id = log.id, value = i)
                        db.session.add(x)                
                else:
                    x = Tracker_log_value(log_id = log.id, value = int(values[0]) if data['type'] == 'integer' else (float(values[0]) if data['type'] == 'float' else str(values[0])))
                    db.session.add(x)

                db.session.commit()
                da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_id)
                da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_id)
                return show_201("Logged the values")
            except:
                app.logger.exception(f'API_LA2: Error ocurred while adding tracker log value')
                # if any internal error occurs, rollback the database
                db.session.rollback()
                return show_500()
        else:
            return show_404()


class Each_Log_api(Resource):
    @jwt_required()
    def get(self, tracker_id, log_id):
        try:
            user_id = get_jwt_identity()
            tracker_data = da.get_single_tracker(user_id, tracker_id)
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
                
                log_data = da.get_single_log(tracker_data.id, log_id)
                if log_data:                    
                    ldata = {
                        'id': log_data.id,
                        'timestamp': datetime.strftime(log_data.timestamp, date_format),
                        'note': log_data.note
                    }                    
                    if tdata['type'] == 'ms':
                        ldata['value'] = []
                        for i in log_data.values:
                            choice = da.get_single_tracker_type(i.value)
                            ldata['value'].append({"choice_id": choice.id, "choice_name": choice.value})
                    
                    elif tdata['type'] == 'integer':
                        ldata['value'] = int(log_data.values[0].value)
                    
                    elif tdata['type'] == 'float':
                        ldata['value'] = float(log_data.values[0].value)
                    
                    elif tdata['type'] == 'timerange':
                        temp = str(log_data.values[0].value).split('-')
                        ldata['start'], ldata['end'] = temp[0].strip(), temp[1].strip()
                    
                    return make_response(jsonify(ldata), 200)
                else:
                    return show_404()
            else:
                return show_404()
        except:
            app.logger.exception("API_ELA1")
            return show_500()
    
    @jwt_required()
    def delete(self, tracker_id, log_id):
        user_id = get_jwt_identity()
        # check if a tracker with the provided id and made by current user exists or not.
        da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_id)
        tracker_data = da.get_single_tracker(user_id, tracker_id)
        # if it exists, proceed.
        if tracker_data:
            da.cache.delete_memoized(da.get_single_log, log_id)
            log_data = da.get_single_log(tracker_data.id, log_id)
            if log_data:
                try:            
                    db.session.delete(log_data)
                    db.session.commit()
                    da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_id)                    
                    da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_id)
                except:
                    app.logger.exception(f'API_ELA2: Error ocurred while deleting tracker log with id {log_id}')
                    # if any internal error occurs, rollback the database
                    db.session.rollback()
                    return show_500()
            
                return show_200(f"Log with ID {log_id} deleted")
            else:
                return show_404()
        else:
            return show_404()
    
    @expects_json(patch_logs_schema)
    @jwt_required()
    def patch(self, tracker_id, log_id):
        user_id = get_jwt_identity()
        tracker_data = da.get_single_tracker(user_id, tracker_id)
        if tracker_data:
            da.cache.delete_memoized(da.get_single_log, tracker_data.id, log_id)
            log_data = da.get_single_log(tracker_data.id, log_id)
            if log_data:
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

                ldata = {
                    'id': log_data.id,
                    'timestamp': datetime.strftime(log_data.timestamp, date_format),
                    'note': log_data.note,
                    'value': [i.value for i in log_data.values]
                }


                logs_patch_args = reqparse.RequestParser()
                logs_patch_args.add_argument('timestamp')
                logs_patch_args.add_argument('note')
                logs_patch_args.add_argument('value', type=(int if (tdata['type'] in ['integer', 'ms']) else (float if tdata['type']=='float' else str)), action='append')

                args = logs_patch_args.parse_args()
                timestamp = args.get('timestamp', None)
                note = args.get('note', None)
                values = args.get('value', None)

                if timestamp == None:
                    timestamp = ldata['timestamp']

                try:
                    datetime.strptime(timestamp, date_format)
                except ValueError:
                    return show_400(f'Timestamp is not in valid format, should be in the format {datetime.strftime(datetime.now(), date_format)}')

                if values != None:
                    if tdata['type'] == 'integer' or tdata['type'] == 'float':
                        try:
                            int(values[0])
                        except:
                            return show_400(f"Value is in incorrect format. Expected {tdata['type']}")
                    
                    elif tdata['type'] == 'ms':
                        for i in values:
                            if i not in tdata['choices']:
                                return show_400(f"choice id {i} does not exist")
                    
                    elif tdata['type'] == 'timerange':
                        try:
                            temp = str(values[0]).split('-')
                            datetime.strptime(temp[0].strip(), timerange_format)
                            datetime.strptime(temp[1].strip(), timerange_format)
                        except:
                            return show_400(f'Value is not in valid format, should be in the format \'{datetime.strftime(datetime.now(), timerange_format)} - {datetime.strftime(datetime.now(), timerange_format)}\'')

                try:
                    log_data.timestamp = datetime.strptime(timestamp, date_format)
                    log_data.note = note if note != None else ldata['note']
                    
                    if values != None:
                        for i in log_data.values:
                            db.session.delete(i)

                        if tdata['type'] == 'ms':
                            choices = values
                            for i in choices:
                                x = Tracker_log_value(log_id = log_data.id, value = i)
                                db.session.add(x)                        
                        else:
                            x = Tracker_log_value(log_id = log_data.id, value = values[0])
                            db.session.add(x)
                    
                    db.session.commit()
                    da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_id)                    
                    da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_id)
                    da.cache.delete_memoized(da.get_all_tracker_type, tracker_data.id)
                    da.cache.delete_memoized(da.get_single_log, tracker_data.id, log_id)
                    return show_200("updated log")

                except:
                    app.logger.exception(f'Error ocurred while editing tracker log with id {log_id}')
                    # if any internal error occurs, rollback the database
                    db.session.rollback()
                    return show_500()
            else:
                return show_404()
        else:
            return show_404()