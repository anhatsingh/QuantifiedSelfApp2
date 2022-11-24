from flask import current_app as app
from flask import jsonify, make_response
from application.models import *
from flask_restful import Resource, reqparse
from flask_expects_json import expects_json
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from application import tasks
import application.data_access as da

from .response_codes import *
from .json_schema import *

class Trackers_api(Resource):
    @jwt_required()
    def get(self):
        try:
            user_id = get_jwt_identity()
            all_tracker_data = da.get_all_trackers(user_id)
            if all_tracker_data:
                final_data = []
                for tracker_data in all_tracker_data:
                    datatypes = list(set([i.datatype for i in tracker_data.ttype]))
                    data = {
                        'id': tracker_data.id,
                        'name': tracker_data.name,
                        'description': tracker_data.description,
                        'type': datatypes[0] if len(datatypes) > 0 else '',
                        'settings': [i.value for i in tracker_data.settings]
                    }
                    if data['type'] == 'ms':
                        data['choices'] = []
                        for i in tracker_data.ttype:
                            data['choices'].append({"id": i.id, "value": i.value})
                    else:
                        data['choices'] = None
                    
                    final_data.append(data)
                return make_response(jsonify(final_data), 200)
            else:
                return show_404()
        except:
            app.logger.exception("API_TA1")
            return show_500()
    

    @expects_json(add_tracker_schema)
    @jwt_required()
    def post(self):
        tracker_input_args = reqparse.RequestParser()
        tracker_input_args.add_argument('name')
        tracker_input_args.add_argument('description')
        tracker_input_args.add_argument('settings', type=str, action='append')
        tracker_input_args.add_argument('type', choices=allowed_choices)
        tracker_input_args.add_argument('choices', type=str, action='append')

        args = tracker_input_args.parse_args()
        name = args.get('name', None)
        description = args.get('description', None)
        settings = args.get('settings', None)
        ttype = args.get('type', None)
        choices = args.get('choices', None)
        
        try:
            user_id = get_jwt_identity()
            # get the new tracker's object
            new_tracker = Tracker(name = name, description = description, user_id=user_id)
            # add the detais of new tracker to database session
            db.session.add(new_tracker)
            # flushes the session, so we get the new tracker's id from database, without committing to disc yet.
            db.session.flush()
            # get all the settings, remove spaces and split by comma
            for i in settings:
                # make settings object
                new_setting = Settings(tracker_id = new_tracker.id, value = i.strip())
                # add the details of new settings to db session
                db.session.add(new_setting)
            
            # flushes the session, so we get the new tracker's id from database, without committing to disc yet.
            db.session.flush()

            # if tracker type is multiple select
            if ttype == 'ms':
                if choices != None:
                    # add each choice to the database
                    for i in choices:
                        new_choice = Tracker_type(tracker_id  = new_tracker.id, datatype = ttype, value = i.strip())
                        db.session.add(new_choice)
                
                else:
                    return show_400("choices are required with this type of tracker.")
            
            # if tracker type is integer values
            else:
                new_choice = Tracker_type(tracker_id  = new_tracker.id, datatype = ttype, value = None)
                db.session.add(new_choice)

            # commit all the changes commited to settings so far
            db.session.commit()
            da.cache.delete_memoized(da.get_all_trackers, user_id)
            return show_201("Added new tracker")
        except:
            # some internal error occurred
            app.logger.exception('API_TA2: Error occurred while adding Tracker')
            # rollback whatever the last session changes were.
            db.session.rollback()            
            # set error flash message
            return show_500()

@app.route('/api/export/tracker/<id>/<type>')
@jwt_required()
def export_logs(id, type):
    try:
            user_id = get_jwt_identity()
            if type=="pdf":
                job = tasks.generate_pdf_report.apply_async(args=[user_id, id])
            elif type == "csv":
                job = tasks.generate_csv_report.apply_async(args=[user_id, id])
            return make_response(jsonify({"msg": f"Export Task for Tracker {id} has been created. Once collected, the data shall be mailed in {type} form to you shortly."}), 200)
    except:
        return show_500()


class Each_Tracker_api(Resource):
    @jwt_required()
    def get(self, id):
        try:
            user_id = get_jwt_identity()
            tracker_data = da.get_single_tracker(user_id, id)
            if tracker_data:
                datatypes = list(set([i.datatype for i in tracker_data.ttype]))
                data = {
                    'id': tracker_data.id,
                    'name': tracker_data.name,
                    'description': tracker_data.description,
                    'type': datatypes[0] if len(datatypes) > 0 else '',
                    'settings': [i.value for i in tracker_data.settings]
                }
                if data['type'] == 'ms':
                    data['choices'] = []
                    for i in tracker_data.ttype:
                        data['choices'].append({"id": i.id, "value": i.value})
                else:
                    data['choices'] = None

                return make_response(jsonify(data), 200)
            else:
                return show_404("API_ETA1")
        except:
            app.logger.exception("API_ETA1")
            return show_500()
    
    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        da.cache.delete_memoized(da.get_single_tracker, user_id, id)
        tracker_data = da.get_single_tracker(user_id, id)
        # if it exists, proceed.
        if tracker_data:
            try:            
                db.session.delete(tracker_data)
                db.session.commit()
                da.cache.delete_memoized(da.get_single_tracker, user_id, id)
                da.cache.delete_memoized(da.get_all_trackers, user_id)
            except:
                app.logger.exception(f'API_ETA2: Error ocurred while deleting tracker with id {id}')
                # if any internal error occurs, rollback the database
                db.session.rollback()
                return show_500()
            
            return show_200(f'Deleted Tracker with ID {id}')
        else:
            return show_404('API_ETA2')

    @expects_json(patch_tracker_schema)
    @jwt_required()
    def patch(self, id):
        tracker_patch_args = reqparse.RequestParser()
        tracker_patch_args.add_argument('name')
        tracker_patch_args.add_argument('description')
        tracker_patch_args.add_argument('settings', type=str, action='append')
        tracker_patch_args.add_argument('type', choices=allowed_choices)
        tracker_patch_args.add_argument('choices', type=dict, action='append')
        tracker_patch_args.add_argument('delete_choices')

        # if the request method is get
        # check if a tracker with the provided id and made by current user exists or not.
        user_id = get_jwt_identity()
        da.cache.delete_memoized(da.get_single_tracker, user_id, id)
        tracker_data = da.get_single_tracker(user_id, id)
        # if it exists, proceed.
        if not tracker_data:
            return show_404()

        try:
            args = tracker_patch_args.parse_args()
            name = args.get('name', None)
            description = args.get('description', None)
            settings = args.get('settings', None)
            ttype = args.get('type', None)
            choices = args.get('choices', None)
            delete_choices = args.get('delete_choices', False)

            tracker_data.name = name if name != None else tracker_data.name
            tracker_data.description = description if description != None else tracker_data.description
            
            if settings != None:
                for i in Settings.query.filter_by(tracker_id=id).all():
                    db.session.delete(i)
                
                for i in settings:
                    # make settings object
                    new_setting = Settings(tracker_id = tracker_data.id, value = i.strip())
                    # add the details of new settings to db session
                    db.session.add(new_setting)
            
            if ttype == None:
                datatypes = list(set([i.datatype for i in tracker_data.ttype]))
                ttype = datatypes[0] if len(datatypes) > 0 else '' 
            
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            oldtype = datatypes[0] if len(datatypes) > 0 else ''                
            
            if oldtype != ttype:
                for i in tracker_data.ttype:
                    db.session.delete(i)
                da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_data.id)                                
                old_logs = da.get_logs_by_tracker_id(tracker_data.id)
                for ol in old_logs:
                    db.session.delete(ol)
                # if tracker type is multiple select
                if ttype == 'ms':
                    if choices != None:
                        for i in choices:
                            new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = i['value'].strip())
                            db.session.add(new_choice)
                    else:
                        return show_400('choices can\'t be empty if changing type to multi-select')
                
                # if tracker type is integer values
                else:
                    new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = None)
                    db.session.add(new_choice)
            
            else:
                # if tracker type is multiple select
                if ttype == 'ms':
                    if choices != None and not delete_choices:                        
                        for x in choices:                            
                            if 'id' in x and x['id'] != None and x['id'] != "":
                                new_value = x['value']
                                da.cache.delete_memoized(da.get_single_tracker_type, x['id'])                                
                                choice_db = da.get_single_tracker_type(x['id'])
                                if choice_db != None:
                                    if new_value != '':                                
                                            choice_db.value = new_value                                
                                    else:
                                        vals = db.delete(Tracker_log_value).where(Tracker_log_value.value.in_([choice_db.id]))                                    
                                        db.session.execute(vals)
                                        db.session.delete(choice_db)
                                else:
                                    return show_400(f'Choice with id {x["id"]} does not exist')
                            else:                            
                                if x['value'] != '' and x['value'] != None:
                                    new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = x['value'].strip())
                                    db.session.add(new_choice)
                                else:
                                    return show_400(f'value cannot be empty if adding new choice')
            
            if ttype == 'ms' and delete_choices:
                da.cache.delete_memoized(da.get_all_tracker_type, tracker_data.id)
                all_choices = da.get_all_tracker_type(tracker_data.id)
                for x in all_choices:
                    vals = db.delete(Tracker_log_value).where(Tracker_log_value.value.in_([x.id]))                                    
                    db.session.execute(vals)
                    db.session.delete(x)
                
                new_choice = Tracker_type(tracker_id = tracker_data.id, datatype=ttype, value="placeholder choice")
                db.session.add(new_choice)
                

                # commit all the above changes to the database
            db.session.commit()
            da.cache.delete_memoized(da.get_all_tracker_type, tracker_data.id)
            da.cache.delete_memoized(da.get_logs_by_tracker_id, tracker_data.id)
            da.cache.delete_memoized(da.get_all_trackers, user_id)
            da.cache.delete_memoized(da.get_single_tracker, user_id, tracker_data.id)
            return show_200()
        except:
            app.logger.exception(f'API_ETA3: Error ocurred while editing tracker with id {id}')
            # if any internal error occurs, rollback the database
            db.session.rollback()
            return show_500()
