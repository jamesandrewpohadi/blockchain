from utils import *
import requests
import random
import threading
import time

class Miner(Wallet):
    
    def __init__(self,name,ip,port,pool='normal',role='normal'):
        Wallet.__init__(self,name,ip,port,pool,'miner')
        self.blockchain = Blockchain.new(self)
        self.t_lock = threading.Lock()
        self.t_block = threading.Lock()
        self.status = 'normal'
        self.role = role

    def mine(self,private=False):
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
                print('{} ignored {}: transaction already exists in blockchain'.format(self,t))
                continue
            if f_b>=0 and t.validate():
                balance[t.sender] = f_b
                m.add(t)
            else:
                print('{} ignore {}: not enough balance'.format(self,t))

        # add reward
        reward = Transaction.new(Blockchain.public,self.public,100)
        reward.sign(Blockchain.private)
        m.add(reward)
        block = Block.new(last_block.header['depth']+1,last_block.hash,m.root.hash,bc.target,m)
        pow = block.proof_of_work(self)
        if not pow:
            return False
        print('{} found {}'.format(self,block))
        bc.addBlock(block)
        # broadcast the new block
        for contact in self.contacts['miner']+self.contacts['spv']:
            requests.post('{}/add_block'.format(contact['address']), json={"block": block.serialize()})
        return True

    def fork(self,block):
        bc = self.blockchain
        last_block = bc.chain[block.hash]
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
                print('{} ignored {}: transaction already exists in blockchain'.format(self,t))
                continue
            if f_b>=0 and t.validate():
                balance[t.sender] = f_b
                m.add(t)
            else:
                print('{} ignore {}: not enough balance'.format(self,t))

        # add reward
        reward = Transaction.new(Blockchain.public,self.public,100)
        reward.sign(Blockchain.private)
        m.add(reward)
        block = Block.new(last_block.header['depth']+1,last_block.hash,m.root.hash,bc.target,m)
        pow = block.proof_of_work(self)
        if not pow:
            return False
        print('{} fork {}'.format(self,block))
        bc.addBlock(block,True)
        # broadcast the new block
        for contact in self.contacts['miner']+self.contacts['spv']:
            requests.post('{}/add_block'.format(contact['address']), json={"block": block.serialize(),"pool":self.pool})
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
        print('{}: {} is not in blockchain'.format(self,transaction))
        return False

    def get_balance(self):
        bc = self.blockchain
        return bc.balance[bc.last_block.hash]

    def addBlock(self,block,private=False):
        self.blockchain.addBlock(block,private)

    def addTransaction(self,transaction):
        self.t_lock.acquire()
        self.blockchain.addTransaction(transaction)
        self.t_lock.release()

    def transfer(self,receiver,amount):
        transaction = Transaction.new(self.public,receiver['public'],amount)
        transaction.sign(self.private)
        print('{} send {} to ({}..) -> {}'.format(self,amount,receiver['public'][:6],transaction))
        self.blockchain.addTransaction(transaction)
        for miner in self.contacts['miner']:
            requests.post('{}/add_transaction'.format(miner['address']), json={"transaction": transaction.serialize()})
        requests.post('{}/receive_transaction'.format(receiver['address']), json={"transaction": transaction.serialize()})
        return transaction

    def double_spending_attack(self):
        if self.role == 'main attacker':
            while True:
                for i in range(1):
                    self.mine()
                self.blockchain.private_block = self.blockchain.last_block
                victim = random.choice([c for c in self.contacts['miner']+self.contacts['spv'] if c['pool'] != self.pool])
                transaction = self.transfer(victim,0)
                attack_when = self.blockchain.private_block.header['depth']+2
                print('### {} launch double spending attack on {} ###'.format(self,transaction))
                while self.blockchain.last_block.header['depth'] <= attack_when:
                    time.sleep(1)
                for contact in self.contacts['miner']:
                    if contact['pool'] == self.pool:
                        requests.post('{}/set_status'.format(contact['address']), json={"status": "attack"})
                self.status = 'attack'
                while self.blockchain.last_block.header['depth'] !=  self.blockchain.private_block.header['depth']:
                    self.fork(self.blockchain.private_block)
                # self.fork(self.las)
                print('### {}: Attack on {} succeed ###'.format(self,transaction))
                self.status = 'normal'
                for contact in self.contacts['miner']:
                    if contact['pool'] == self.pool:
                        requests.post('{}/set_status'.format(contact['address']), json={"status": "normal"})
                proof = self.get_proof(transaction)
                if proof == False:
                    print('{}: {} is not in blockchain'.format(self,transaction))
                else:
                    print('{}: {} is not in blockchain'.format(self,transaction))
        else:
            while True:
                if self.status == 'attack':
                    self.fork(self.blockchain.private_block)
                else:
                    self.mine()
    
    
    def selfish_mining_attack(self):
        # pass
        self.status = 'attack'
        if self.role = 'main attacker':
            while True:
        else:
            while True:
                self.mine(True)
        
    def normal(self):
        while True:
            self.mine()
            # if len(self.contacts['spv']) != 0 and random.random()<0.8:
            #     contact = random.choice(self.contacts['spv'])
            # else:
            #     contact = random.choice(self.contacts['miner'])
            # self.transfer(contact,random.randint(10,30))

    def run(self,mode):
        if mode == 'normal':
            self.normal()
        elif mode == 'double spending attack':
            self.double_spending_attack()
        elif mode == 'selfish mining attack':
            self.selfish_mining_attack()

    def __str__(self):
        return "Miner({}|{}..)".format(self.name,self.public[:6])
