from flask import Flask, request
from SPVClient import SPVClient
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
from utils import Transaction, Block

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
to_verify = {}

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
            spv.contacts[data['type']].append(data)
            del data['type']
    print(spv.contacts)
    spv.run()
    # while True:
        # if fork:
        #     fork = False
        #     fork(spv_hash)
        # spv.mine()

spv = SPVClient(args.name,args.ip,args.port)
_thread.start_new_thread( run, () )
# _thread.start_new_thread( spv.run, () )

@app.route('/get_id')
def get_id():
    return spv.get_id()

@app.route('/get_last_block')
def get_last_block():
    return str(spv.blockchain.last_block)

@app.route('/get_all_chain')
def get_all_chain():
    chain_hash = {k:v.header['previous_hash'] for k,v in spv.blockchain.chain.items()}
    return chain_hash
    # return json.dumps(spv.blockchain.chain)

@app.route('/test',methods=['POST'])
def test():
    a = request.get_json()
    print(a)
    return 'ok'

@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.get_json()
    serialized_block = data['block']
    block = Block.deserialize(serialized_block,'simplified')
    spv.addBlock(block)
    if to_verify.get(block.header['depth'],False):
        miner = random.choice(spv.contacts['miner'])
        for t in to_verify[block.header['depth']]:
            r = requests.post('{}/get_proof'.format(miner['address']),json={"transaction":t.serialize()})
            data = r.json()
            if not data['status']:
                print('{}: {} is not in blockchain'.format(spv.name,t))
                continue
            block_hash,proof = data['block_hash'],data['proof']
            result = spv.verify_proof(t,block_hash,proof)            
    return 'received'

def get_proof(serialize_transaction):
    time.sleep(10)
    r = requests.post('{}/get_proof'.format(spv['address']), json={"transaction":serialize_transaction})
    transaction = Transaction.deserialize(serialize_transaction)
    data = r.json()
    if spv.bc.verify_proof(data):
        print('{} verified {}'.format(self.name,transaction))

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    data = request.get_json()
    serialized_transaction = data['transaction']
    transaction = Transaction.deserialize(serialized_transaction)
    print('{} get notice on {}'.format(spv.name,transaction))
    check_when = spv.blockchain.last_block.header['depth']+2
    to_verify[check_when] = to_verify.get(check_when,[])+[transaction]
    return 'received'

if __name__ == '__main__':
    # socketio.run(app, host = '0.0.0.0', port = 8080, debug = True) #running at http://127.0.0.1:5000
    # _thread.start_new_thread(app.run,(args.host, args.port,1,False))
    app.run(host = args.ip, port = args.port,processes=1,threaded = False)