from flask import Flask, request
from SPVClient import SPVClient
import argparse
from threading import Thread
import _thread
from flaskthreads import ThreadPoolWithAppContextExecutor
import time
from multiprocessing import Process
import requests
import random
import json
from utils import Transaction, Block

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
to_verify = {}

parser = argparse.ArgumentParser()
parser.add_argument('-name','--name',default='James')
parser.add_argument('-ip','--ip',default='0.0.0.0')
parser.add_argument('-id','--id',default=8080,type=int)
parser.add_argument('-n','--n',default=5,type=int)
parser.add_argument('-pool','--pool',default='normal')
parser.add_argument('-role','--role',default='normal')
parser.add_argument('-mode','--mode',default=0,type=int)
args = parser.parse_args()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sanjayjameskundanbryan'
# socketio = SocketIO(app)

def run(mode):
    time.sleep(1)
    for id in range(args.n):
        if id != args.id:
            port = 8000+id
            r = requests.get('http://localhost:{}/get_id'.format(port))
            data = r.json()
            spv.contacts[data['type']].append(data)
            del data['type']
    print(spv.contacts)
    if mode == 0:
        spv.run('normal')
    elif mode == 1:
        spv.run('double spending attack')
    elif mode == 2:
        spv.run('selfish mining attack')

spv = SPVClient(args.name,args.ip,args.id+8000,args.pool,args.role)
_thread.start_new_thread( run, (args.mode,) )
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
    print('{} get notice on {}'.format(spv,transaction))
    check_when = spv.blockchain.last_block.header['depth']+2
    to_verify[check_when] = to_verify.get(check_when,[])+[transaction]
    return 'received'

if __name__ == '__main__':
    app.run(host = args.ip, port = args.id+8000,processes=1,threaded = False)