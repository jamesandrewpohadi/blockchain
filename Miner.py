from utils import *
import requests

class Miner(Wallet):
    
    def __init__(self,name,ip,port):
        Wallet.__init__(self,name,ip,port,'miner')
        self.blockchain = Blockchain.new(self.name)

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
        for t in bc.transactions:
            # validate transaction
            f_b = balance.get(t.sender,0)-t.amount
            if t.serialize() in prev_t:
                print('{} ignore {}: insufficient balance'.format(self.name,t))
                # print('Ignoring transation')
                continue
            if f_b>=0 and t.validate():
                balance[t.sender] = f_b
                m.add(t)
        # add reward
        reward = Transaction.new(Blockchain.public,self.public,100)
        reward.sign(Blockchain.private)
        m.add(reward)
        block = Block.new(last_block.header['depth']+1,last_block.hash,m.root.hash,bc.target,m)
        pow = block.proof_of_work()
        print('{} found {}'.format(self.name,block))
        bc.addBlock(block)
        bc.transactions = []
        for miner in self.contacts['miner']:
            requests.post('{}/add_block'.format(miner['address']), json={"block": block.serialize()})
        # broadcast the new block
        return True

    def proof(self,transaction):
        prev_block = bc.last_block
        prev_t = []
        while prev_block.header['previous_hash']:
            prev_t.extend(prev_block.transactions.get_list())
            prev_block = bc.chain[prev_block.header['previous_hash']]

    def get_balance(self):
        bc = self.blockchain
        return bc.balance[bc.last_block.hash]

    def addBlock(self,serialized_block):
        block = Block.deserialize(serialized_block)
        self.blockchain.addBlock(block)

    def addTransaction(self,serialized_transaction):
        transaction = Transaction.deserialize(serialized_transaction)
        self.blockchain.addTransaction(transaction)

    def transfer(self,receiver,amount):
        transaction = Transaction.new(self.public,receiver['public'],amount)
        transaction.sign(self.private)
        print('{}({}..) send {} to ({}..) -> {}'.format(self.name,self.public[:6],amount,receiver['public'][:6]))
        self.blockchain.addTransaction(transaction)
        requests.post('{}/receive_transaction'.format(receiver['address']), json={"transaction": transaction.serialize()})
        # for miner in self.contacts:

    def run(self):
        while True:
            self.mine()
            # self.transfer()
