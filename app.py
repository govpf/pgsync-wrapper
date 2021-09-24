import logging
import os
import subprocess
import signal
import sys

from flask import Flask, jsonify, make_response
import psutil


app = Flask(__name__)


def get_process_name():
    current_process = None
 
    for proc in psutil.process_iter():
        if proc.name() in ['bootstrap', 'pgsync']:
            current_process = proc.name()
            break
    return current_process


def get_state():
    global process

    process_name = get_process_name()

    if process_name == 'bootstrap':
        state = 'INITIALIZATION'
    elif process_name == 'pgsync':
        state = 'RUNNING'
    else:
        state =  'Unknown'
    return state


def start_pgsync():
    return subprocess.Popen('/run.sh', close_fds=True, stdout=sys.stdout, stderr=sys.stderr)


process = start_pgsync()


@app.route('/kill', methods=['POST'])
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
    return jsonify({
        'status': 200,
        'state': get_state(),
    })


def main():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))


if __name__ == '__main__':
    main()
