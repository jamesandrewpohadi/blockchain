from flask import Flask, request
from Miner import Miner
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

def run(mode):
    time.sleep(1)
    for id in range(args.n):
        if id != args.id:
            port = 8000+id
            r = requests.get('http://localhost:{}/get_id'.format(port))
            data = r.json()
            miner.contacts[data['type']].append(data)
            del data['type']
    print(miner.contacts)
    if mode == 0:
        miner.run('normal')
    elif mode == 1:
        miner.run('double spending attack')
    elif mode == 2:
        miner.run('selfish mining attack')

miner = Miner(args.name,args.ip,args.id+8000,args.pool,args.role)
_thread.start_new_thread( run, (args.mode,) )
# _thread.start_new_thread( miner.run, () )

@app.route('/get_id')
def get_id():
    return miner.get_id()

@app.route('/get_balance')
def get_balance():
    return miner.get_balance()

@app.route('/get_last_block')
def get_last_block():
    return {
        'public':miner.blockchain.last_block.header['depth'],
        'private':miner.blockchain.private_block.header['depth']
    }

@app.route('/get_all_chain')
def get_all_chain():
    chain_hash = {k:v.header['previous_hash'] for k,v in miner.blockchain.chain.items()}
    return chain_hash

@app.route('/test',methods=['POST'])
def test():
    a = request.get_json()
    print(a)
    return 'ok'

@app.route('/get_status',methods=['POST'])
def get_status():
    data = request.get_json()
    miner.status = data['status']
    return 'ok'

@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.get_json()
    serialized_block = data['block']
    block = Block.deserialize(serialized_block)
    private = data.get('pool',None) == miner.pool and miner.status == 'attack'
    miner.addBlock(block,private)
    
    if to_verify.get(block.header['depth'],False):
        for t in to_verify[block.header['depth']]:
            res = miner.get_proof(t)
            if not res:
                print('{}: {} is not in blockchain'.format(miner.name,t))
                continue
            block_hash,proof = res
            result = miner.verify_proof(t,block_hash,proof)     
    return 'received'

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    serialized_transaction = data['transaction']
    transaction = Transaction.deserialize(serialized_transaction)
    miner.addTransaction(transaction)
    return 'received'

@app.route('/get_proof', methods=['POST'])
def get_proof():
    data = request.get_json()
    serialized_transaction = data['transaction']
    transaction = Transaction.deserialize(serialized_transaction)
    proof = miner.get_proof(transaction)
    if proof:
        return {'status':True,'block_hash':proof[0],'proof':proof[1]}
    else:
        return {'status':False}

@app.route('/set_status', methods=['POST'])
def set_status():
    data = request.get_json()
    miner.status = data['status']
    return 'ok'

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    data = request.get_json()
    serialized_transaction = data['transaction']
    transaction = Transaction.deserialize(serialized_transaction)
    print('{} get notice on {}'.format(miner,transaction))
    check_when = miner.blockchain.last_block.header['depth']+2
    to_verify[check_when] = to_verify.get(check_when,[])+[transaction]
    return 'received'

if __name__ == '__main__':
    app.run(host = args.ip, port = args.id+8000,processes=1,threaded = False)