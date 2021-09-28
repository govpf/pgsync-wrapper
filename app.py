import logging
import os
import signal
import subprocess
import sys
from functools import wraps

import psutil
from flask import Flask, abort, jsonify, make_response, request


app = Flask(__name__)


def get_process_name():
    current_process = None
 
    for proc in psutil.process_iter():
        if proc.name() in ['bootstrap', 'pgsync']:
            current_process = proc.name()
            break
    return current_process


def get_state():
    process_name = get_process_name()

    if process_name == 'bootstrap':
        state = 'INITIALIZATION'
        message = 'Initialisation'
    elif process_name == 'pgsync':
        state = 'RUNNING'
        message = 'OK'
    else:
        state =  'DOWN'
        message = "PGSync n'a pas pu démarrer. Veuillez vérifier les logs."
    return state, message


def start_pgsync():
    return subprocess.Popen('/run.sh', close_fds=True, stdout=sys.stdout, stderr=sys.stderr)


process = start_pgsync()


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = os.environ.get('API_KEY', 'zzGvtoVbBg43+JnVVvbhsvgHXJNFIqL7')
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == key:
            return f(*args, **kwargs)
        else:
            abort(make_response(jsonify(message="Not authorized"), 401))
    return decorated_function


@app.route('/kill', methods=['POST'])
@require_api_key
def kill():
    global process

    current_process = get_process_name()

    if current_process not in ['bootstrap', 'pgsync']:
        return jsonify({
            'status': 200,
            'message': f'PGSync is not running'
        })

    parent = psutil.Process(process.pid)
    for child in parent.children(recursive=True):
        child.send_signal(signal.SIGINT)
    parent.send_signal(signal.SIGINT)
    parent.wait()
    logging.info('PGSync stopped')
    return jsonify({
        'status': 200,
        'message': 'PGSync stopped'
    })


@app.route('/start', methods=['POST'])
@require_api_key
def start():
    global process

    current_process = get_process_name()

    if current_process in ['bootstrap', 'pgsync']:
        return make_response(jsonify({
            'status': 400,
            'message': f'PGSync is already running. Current state is: {get_state()}'
        }), 400)

    process = start_pgsync()
    logging.info(f'{process.pid} - PGSync started')
    return jsonify({
        'status': 200,
        'message': 'Started',
    })


@app.route('/health', methods=['GET'])
def healthcheck():
    stage, message = get_state()
    return jsonify({
        'status': 200,
        'state': stage,
        'message': message,
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
