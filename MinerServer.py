from flask import Flask, request
from Miner import Miner
import argparse
from threading import Thread
import _thread
from flaskthreads import ThreadPoolWithAppContextExecutor
import time
from multiprocessing import Process
from config import processes
import requests
import random
import json

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

parser = argparse.ArgumentParser()
parser.add_argument('-n','--name',default='James')
parser.add_argument('-i','--ip',default='0.0.0.0')
parser.add_argument('-p','--port',default=8080,type=int)
args = parser.parse_args()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sanjayjameskundanbryan'
# socketio = SocketIO(app)

def run():
    time.sleep(1)
    for process in processes:
        if process != args.port:
            r = requests.get('http://localhost:{}/get_id'.format(process))
            data = r.json()
            miner.contacts[data['type']].append(data)
            del data['type']
    print(miner.contacts)
    miner.run()

miner = Miner(args.name,args.ip,args.port)
_thread.start_new_thread( run, () )
# _thread.start_new_thread( miner.run, () )

@app.route('/get_id')
def get_id():
    return miner.get_id()

@app.route('/get_balance')
def get_balance():
    return miner.get_balance()

@app.route('/get_last_block')
def get_last_block():
    return str(miner.blockchain.last_block)

@app.route('/get_all_chain')
def get_all_chain():
    chain_hash = {k:v.header['previous_hash'] for k,v in miner.blockchain.chain.items()}
    return chain_hash
    # return json.dumps(miner.blockchain.chain)

@app.route('/test',methods=['POST'])
def test():
    a = request.get_json()
    print(a)
    return 'ok'

@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.get_json()
    serialized_block = data['block']
    miner.addBlock(serialized_block)
    return 'received'
    # return miner.get_balance()

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    serialized_transaction = data['transaction']
    miner.addTransaction(serialized_transaction)
    return 'received'

def get_proof(serialize_transaction):
    time.sleep(10)
    r = requests.post('{}/get_proof'.format(miner['address']), json={"transaction":serialize_transaction})
    transaction = Transaction.deserialize(serialize_transaction)
    data = r.json()
    if miner.bc.verify_proof(data):
        print('{} verified {}'.format(self.name,transaction))

# @app.route('/verify_proof', methods=['POST'])
# def verify_proof():


@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    data = request.get_json()
    serialized_transaction = data['transaction']
    _thread.start_new_thread( get_proof, (serialized_transaction) )
    # miner.addTransaction(serialized_transaction)
    return 'received'

# def messageReceived(methods=['GET', 'POST']):
#     print('Transaction received!!!')

# @socketio.on('my event')
# def handle_my_custom_event(json, methods=['GET', 'POST']):
#     print('Event received --- ' + str(json))
#     socketio.emit('my response', json, callback=messageReceived)

if __name__ == '__main__':
    # socketio.run(app, host = '0.0.0.0', port = 8080, debug = True) #running at http://127.0.0.1:5000
    # _thread.start_new_thread(app.run,(args.host, args.port,1,False))
    app.run(host = args.ip, port = args.port,processes=1,threaded = False)