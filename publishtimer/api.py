from flask import Flask, abort, request, jsonify, make_response
from publishtimer.publishtimer.core import work_once
    
app = Flask(__name__)


tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]


@app.route('/ping')
def index():
    return "pong"


@app.route('/api/v1.0/publishschedule', methods=['PUT'])
def publish_schedule():
    if not request.json:
        abort(400)
    if 'authUid' in request.json and type(request.json['authUid']) != unicode:
        abort(400)
    if 'use_es' in request.json and type(request.json['use_es']) is not bool:
        abort(400)
    if 'use_tw' in request.json and type(request.json['use_tw']) is not bool:
        abort(400)
    if 'save_on_fly' in request.json and \
        type(request.json['save_on_fly']) is not bool:
        abort(400)
    return work_once(**request.json)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__=="__main__":
    app.run(debug=True)