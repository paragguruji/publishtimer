# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 12:10:03 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

import os
import logging
import traceback
import sys
from flask import Flask, request, jsonify, make_response
from publishtimer.core import work_once as worker_function
from logging.handlers import RotatingFileHandler
from werkzeug.exceptions import Aborter
from publishtimer.custom_exceptions import WriteScheduleFailedError


ERROR_MAPPINGS = {512: WriteScheduleFailedError}

abort = Aborter(extra=ERROR_MAPPINGS)

app = Flask(__name__)


@app.route('/ping', methods=['GET'])
def index():
    """Index function to check if app is alive
    """
    return "pong"


@app.route('/api/v1.0/publishschedule', methods=['POST'])
def publish_schedule():
    """API to trigger the publishtimer for desired authUid
    
    Calls the worker_function imported from core module with received params as args and returns its response
    
    :Returns: JSON Response containing: 
            1. JSONified response recieved from save_schedule API
            2. schedule computed by publishtimer
            
    :Response format: {'response_from_save_schedule_api': <jsonifird response>,
                       'schedule_prepared': <computed_schedule>}
    
    :Request_URL: <base_url>/api/v1.0/publishschedule
    
    :Method: POST
    
    :Request_type: JSON
    
    :Request_params:
        :param authUid:     :type: unicode :decription: authUid whose schedule is to be computed
        :param use_es: [optional]   :type: bool 
                                    :description: When True, elasticsearch will be queried for existing data of given authUid and Twitter API won't be hit if data exisits.
                                    :default: True
        :param use_tw: [optional]   :type: bool 
                                    :description: When True, Twitter API will be hit if use_es is False or data doesn't exisit in ES for given authUid.
                                    :default: True
        :param save_on_fly: [optional]  :type: bool 
                                        :description: When True, Data if fetched from Twitter API, will be saved to elasticsearch for future use.
    
    :Request_format: {'authUid': u'<authUid>', 
                      'use_es': <(True/False)>,
                      'use_tw': <(True/False)>, 
                      'save_on_fly': <(True/False)>}
    """
    if not request.json:
        abort(400, description="aborting because empty request.json")
    if 'authUid' not in request.json:
        abort(400, description="aborting because authUid not in request")
    if  type(request.json['authUid']) not in [unicode, long, int, str]:
        abort(400, 
              description= \
              "aborting because authUid neither of unicode, long, int, str")
    if 'use_es' in request.json and type(request.json['use_es']) is not bool:
        abort(400, description="aborting because use_es is not bool")
    if 'use_tw' in request.json and type(request.json['use_tw']) is not bool:
        abort(400, description="aborting because use_tw is not bool")
    if 'save_on_fly' in request.json and \
            type(request.json['save_on_fly']) is not bool:
        abort(400, description="aborting because save_on_fly is not bool")
    results, write_response = worker_function(**request.json)
    if write_response.status_code == 200:
        return make_response(jsonify(results), 200)
    else:
        abort(512, **{'upstream_response': write_response,
                      'computed_schedule': results})


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 error to JSONify the response
    """
    print error.code, ': ', str(error), ' : ', error.description
    traceback.print_exc(file=sys.stdout)
    return make_response(jsonify({'error': str(error),
                                  'message': error.description}), error.code)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 error to JSONify the response
    """
    print error.code, ': ', str(error), ' : ', error.description
    traceback.print_exc(file=sys.stdout)
    return make_response(jsonify({'error': str(error), 
                                  'message': error.description}), error.code)


@app.errorhandler(500)
def internal_error(error):    
    """Handle 500 error to JSONify the response
    """
    print 500, ': ', type(error).__name__,' : ', str(error)
    traceback.print_exc(file=sys.stdout)
    return make_response(\
            jsonify({'error': '500: InternalServerError: ' + \
                              str(type(error).__name__),
                     'description': str(error),
                     'message': traceback.format_exc()}), 
                    500)


@app.errorhandler(512)
def write_api_error(error):    
    """Handle 512 error to JSONify the response
    """
    print 512, ': ', type(error).__name__,' : ', error.description
    return make_response(\
            jsonify({'error': '512: ' + type(error).__name__,
                     'message': error.description,
                     'computed_schedule': error.computed_schedule}), 
                         error.code)


def unhandled_error(error):    
    """Handle all unhandled error to JSONify the response
    """
    traceback.print_exc(file=sys.stdout)
    return make_response(\
            jsonify({'error': str(error),
                     'description': getattr(error, 
                                            'description', 
                                            'No description found'),
                     'message': traceback.format_exc()}), 
                    getattr(error, 'code', 0))


def initiate():
    '''Initiates the required parameters for the server and starts it
    '''
    host = os.environ['SERVER_NAME'].split(':')[0];
    port = int(os.environ['SERVER_NAME'].split(':')[1])
    print "*"*100
    print "\nStarting publishtimer server on ", os.environ['SERVER_NAME']
    print "Find server error logs at: publishtimer/logs/flask_server.log\n"
    print "*"*100
    if not os.path.isfile('logs/flask_server.log'):
        if not os.path.exists('logs'):
            os.mkdir('logs')
        with open('logs/flask_server.log', 'w') as fp:
            fp.write("publishtimer server error logs... \n")
    handler = RotatingFileHandler('logs/flask_server.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    '''Following for loop is the safety net for all unhandled HTTP error codes. 
        Ref.: http://stackoverflow.com/a/27760417
    '''
    for error in [i for i in range(400, 600) if i not in [400, 404, 500, 512]]:
        app.error_handler_spec[None][error] = unhandled_error
    app.logger.addHandler(handler)
    app.run(host=host, port=port)
    
    
if __name__=="__main__":
    initiate()