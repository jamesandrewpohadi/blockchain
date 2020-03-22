from utils import *
import requests
import random
import threading
import time

class Miner(Wallet):
    
    def __init__(self,name,ip,port):
        Wallet.__init__(self,name,ip,port,'miner')
        self.blockchain = Blockchain.new(self.name)
        self.t_lock = threading.Lock()
        self.t_block = threading.Lock()
        self.status = 'normal'
        self.pool = 'normal'
        self.private_block = 'genesis'

    def mine(self):
        bc = self.blockchain
        last_block = bc.last_block
        balance = bc.balance[last_block.hash].copy()
        prev_block = last_block
        prev_t = []
        while prev_block.header['previous_hash']:
            prev_t.extend(prev_block.transactions.get_list())
            prev_block = bc.chain[prev_block.header['previous_hash']]
        prev_t = set(prev_t)
        m = MerkleTree.build()
        self.t_lock.acquire()
        bc_transactions = bc.transactions
        bc.transactions = []
        self.t_lock.release()
        for t in bc_transactions:
            # validate transaction
            f_b = balance.get(t.sender,0)-t.amount
            if t.serialize() in prev_t:
                print('{} ignored {}: transaction already exists in blockchain'.format(self.name,t))
                continue
            if f_b>=0 and t.validate():
                balance[t.sender] = f_b
                m.add(t)
            else:
                print('{} ignore {}: not enough balance'.format(self.name,t))

        # add reward
        reward = Transaction.new(Blockchain.public,self.public,100)
        reward.sign(Blockchain.private)
        m.add(reward)
        block = Block.new(last_block.header['depth']+1,last_block.hash,m.root.hash,bc.target,m)
        pow = block.proof_of_work()
        print('{} found {}'.format(self.name,block))
        bc.addBlock(block)
        # broadcast the new block
        for contact in self.contacts['miner']+self.contacts['spv']:
            requests.post('{}/add_block'.format(contact['address']), json={"block": block.serialize()})
        return True

    def fork(self,block_hash):
        bc = self.blockchain
        last_block = bc.chain[block_hash]
        balance = bc.balance[last_block.hash].copy()
        prev_block = last_block
        prev_t = []
        while prev_block.header['previous_hash']:
            prev_t.extend(prev_block.transactions.get_list())
            prev_block = bc.chain[prev_block.header['previous_hash']]
        prev_t = set(prev_t)
        m = MerkleTree.build()
        self.t_lock.acquire()
        bc_transactions = bc.transactions
        bc.transactions = []
        self.t_lock.release()
        for t in bc_transactions:
            # validate transaction
            f_b = balance.get(t.sender,0)-t.amount
            if t.serialize() in prev_t:
                print('{} ignored {}: transaction already exists in blockchain'.format(self.name,t))
                continue
            if f_b>=0 and t.validate():
                balance[t.sender] = f_b
                m.add(t)
            else:
                print('{} ignore {}: not enough balance'.format(self.name,t))

        # add reward
        reward = Transaction.new(Blockchain.public,self.public,100)
        reward.sign(Blockchain.private)
        m.add(reward)
        block = Block.new(last_block.header['depth']+1,last_block.hash,m.root.hash,bc.target,m)
        pow = block.proof_of_work()
        print('{} found {}'.format(self.name,block))
        bc.addBlock(block)
        # broadcast the new block
        for contact in self.contacts['miner']+self.contacts['spv']:
            requests.post('{}/add_block'.format(contact['address']), json={"block": block.serialize()})
        return True

    def get_proof(self,transaction):
        bc = self.blockchain
        prev_block = bc.last_block
        # prev_t = []
        serialized_transaction = transaction.serialize()
        while prev_block.header['previous_hash']:
            if serialized_transaction in prev_block.transactions.get_list():
                return prev_block.hash, prev_block.transactions.get_proof(transaction)
            prev_block = bc.chain[prev_block.header['previous_hash']]
        return False

    def verify_proof(self,transaction,block_hash,proof):
        bc = self.blockchain
        prev_block = bc.last_block
        while prev_block.header['previous_hash']:
            if block_hash == prev_block.hash:
                boolean = prev_block.verify_transaction(transaction,proof)
                is_in = '' if boolean else ' not'
                print('{}: {} is{} in blockchain, {}'.format(self.name,transaction,is_in,prev_block))
                return boolean
            prev_block = bc.chain[prev_block.header['previous_hash']]
        print('{}: {} is not in blockchain'.format(self.name,transaction))
        return False

    def get_balance(self):
        bc = self.blockchain
        return bc.balance[bc.last_block.hash]

    def addBlock(self,block):
        self.blockchain.addBlock(block)

    def addTransaction(self,transaction):
        self.t_lock.acquire()
        self.blockchain.addTransaction(transaction)
        self.t_lock.release()

    def transfer(self,receiver,amount):
        transaction = Transaction.new(self.public,receiver['public'],amount)
        transaction.sign(self.private)
        print('{}({}..) send {} to ({}..) -> {}'.format(self.name,self.public[:6],amount,receiver['public'][:6],transaction))
        self.blockchain.addTransaction(transaction)
        for miner in self.contacts['miner']:
            requests.post('{}/add_transaction'.format(miner['address']), json={"transaction": transaction.serialize()})
        requests.post('{}/receive_transaction'.format(receiver['address']), json={"transaction": transaction.serialize()})
        return transaction

    def double_spending_attack(self):
        start = time.time()
        if self.status == 'attacker':
            while time.time()-start<20:
                self.mine()
            self.private_block = self.blockchain.last_block
            transaction = self.transfer()
            attack_when = self.private_block.header['depth']+3
            print('{} launch double spending attack on {}'.format(self.name,transaction))
            while self.blockchain.last_block.header['depth'] <= attack_when:
                self.mine()
            
    
    
    def selfish_mining_attack(self):
        pass
        
    def run(self):
        while True:
            self.mine()
            if len(self.contacts['spv']) != 0 and random.random()<0.8:
                contact = random.choice(self.contacts['spv'])
            else:
                contact = random.choice(self.contacts['miner'])
            self.transfer(contact,random.randint(10,30))
