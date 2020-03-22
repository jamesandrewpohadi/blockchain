from utils import *
import random
import requests
import time

class SPVClient(Wallet):
    def __init__(self,name,ip,port):
        Wallet.__init__(self,name,ip,port,'spv')
        self.blockchain = Blockchain.new(self.name)
    
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

    # def get_balance(self):
    #     bc = self.blockchain
    #     return bc.balance[bc.last_block.hash]

    def addBlock(self,block):
        self.blockchain.addBlock(block)

    def transfer(self,receiver,amount):
        transaction = Transaction.new(self.public,receiver['public'],amount)
        transaction.sign(self.private)
        print('{}({}..) send {} to ({}..) -> {}'.format(self.name,self.public[:6],amount,receiver['public'][:6],transaction))
        self.blockchain.addTransaction(transaction)
        for miner in self.contacts['miner']:
            requests.post('{}/add_transaction'.format(miner['address']), json={"transaction": transaction.serialize()})
        requests.post('{}/receive_transaction'.format(receiver['address']), json={"transaction": transaction.serialize()})
        return transaction
    
    def run(self):
        while True:
            time.sleep(10)
            if random.random()<0.8:
                contact = random.choice(self.contacts['spv']+self.contacts['miner'])
                self.transfer(contact,random.randint(10,90))
