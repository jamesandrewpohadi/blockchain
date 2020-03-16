import time
import hashlib
import ecdsa
from time import time
import json
import base64
import random
import Crypto.Random
from Crypto.PublicKey import RSA
import binascii
from collections import OrderedDict

class Transaction:

    @classmethod
    def new(self,sender,receiver,amount,comment):
        t = Transaction()
        t.sender = sender
        t.receiver = receiver
        t.amount = amount
        t.comment = comment
        t.time = time()
        t.sig = ''
        id = json.dumps({
            'sender':t.sender,
            'receiver':t.receiver,
            'amount':t.amount,
            'time':t.time
        })
        t.id = hashlib.sha256(id.encode()).hexdigest()
        # t.sk = ecdsa.SigningKey.generate()
        # t.vk = t.sk.get_verifying_key()
        return t

    def serialize(self):
        string = {
            'sender':self.sender,
            'receiver':self.receiver,
            'amount':self.amount,
            'comment':self.comment,
            'time':self.time,
            'sig':self.sig
        }
        json_string = json.dumps(string)
        return base64.b64encode(json_string.encode('utf-8')).decode()

    @classmethod
    def deserialize(self,base64_string):
        json_string = base64.b64decode(base64_string.encode()).decode()
        json_data = json.loads(json_string)
        t = Transaction()
        t.sender = json_data['sender']
        t.receiver = json_data['receiver']
        t.amount = json_data['amount']
        t.comment = json_data['comment']
        t.time = json_data['time']
        t.sig = json_data['sig']
        id = json.dumps({
            'sender':t.sender,
            'receiver':t.receiver,
            'amount':t.amount,
            'time':t.time
        })
        t.id = hashlib.sha256(id.encode()).hexdigest()
        return t

    def sign(self, private_key):
        sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
        self.sig = ''
        s = self.serialize()
        sig = sk.sign(s.encode()).hex()
        self.sig = sig
        return sig

    def validate(self):
        try:
            vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(self.receiver), curve=ecdsa.SECP256k1)
            tmp = bytes.fromhex(self.sig)
            self.sig = ''
            s = self.serialize()
            return self.vk.verify(tmp,s.encode())
        except:
            return False
    
    def __eq__(self,other):
        return self.id == other.id
        # return self.sender == other.sender and self.receiver == other.receiver and self.amount == other.amount and self.comment == other.comment

class TreeNode:
    def __init__(self,parent,childLeft,childRight):
        self.mode = None
        self.parent = parent
        self.childLeft = childLeft
        self.childRight = childRight
        self.childLeft.parent = self
        self.childLeft.mode = "L"
        self.childRight.parent = self
        self.childRight.mode = "R"
        self.weight = self.childLeft.weight + self.childRight.weight
        self.hash = None

    def getHash(self):
        concat = self.childLeft.hash + self.childRight.hash
        self.hash = hashlib.sha256(concat.encode()).hexdigest()
        return self

    def addLeave(self, leave):
        if self.childLeft.weight > self.childRight.weight:
            if isinstance(self.childRight,TreeNode):
                self.childRight = self.childRight.addLeave(leave)
                self.childRight.mode = "R"
            else:
                self.childRight = TreeNode(self,self.childRight,leave).getHash()
                self.childRight.mode = "R"
            self.weight += 1
            returnNode = self
        elif self.childLeft.weight==self.childRight.weight:
            returnNode = TreeNode(self.parent,self,leave).getHash()
        self.getHash()
        return returnNode

class LeaveNode:
    def __init__(self,val):
        self.mode = None
        self.parent = None
        self.val = val
        self.weight = 1
        self.hash = None

    def getHash(self):
        self.hash = hashlib.sha256(self.val.serialize().encode()).hexdigest()
        return self

class MerkleTree:
    
    # def __init__(self,description='James Chain'):
    #     pass

    def add(self,transaction):
        # Add entries to tree
        serialized_transaction = transaction.serialize()
        leave = LeaveNode(transaction).getHash()
        self.val2leave[serialized_transaction] = leave
        self.root = self.root.addLeave(leave)

    @classmethod
    def build(self,description='James Chain'):
        # Build tree computing new root
        m = MerkleTree()
        origin = LeaveNode('Origin').getHash()
        description = LeaveNode(description).getHash()
        m.description = description
        m.root = TreeNode(None,origin,description).getHash()
        m.val2leave = OrderedDict()
        return m

    def get_proof(self,transaction):
        # Get membership proof for entry
        proof = []
        serialized_transaction = transaction.serialize()
        node = self.val2leave[serialized_transaction]
        while node.parent != None:
            if node.parent.childLeft.hash == node.hash:
                proof.append(node.parent.childRight)
            else:
                proof.append(node.parent.childLeft)
            node = node.parent
        return proof

    def get_root(self):
        # Return the current root
        return self.root.hash

    def serialize(self):
        pass

    def deserialize(self):
        pass

class Block:

    @classmethod
    def new(self, version, previous_hash, root_hash, timestamp, bits, transactions=None):
        b = Block()
        b.header = {
            'version':None,
            'previous_hash': previous_hash,
            'root_hash':root_hash,
            'timestamp':timestamp,
            'bits':bits,
            'nonce':0
        }
        b.transactions = transactions
        return b

    def proof_of_work(self):
        while not int(self.getHash(),16)<int(self.header['bits'],16):
            self.header['nonce'] += 1
        return self.getHash()

    def getHash(self):
        json_string = json.dumps(self.header)
        hash = hashlib.sha256(json_string.encode()).hexdigest()
        return hash

    def serialize(self):
        transactions = list(self.transactions.val2leave.keys())
        # MerkleTree
        data_dict = {
            'header': self.header,
            'transactions': 
        }
        json_string = json.dumps(data_dict)
        return base64.b64encode(json_string.encode('utf-8')).decode()

    @classmethod
    def deserialize(self,base64_string):
        b = Block()
        json_string = base64.b64decode(base64_string.encode()).decode()
        json_data = json.loads(json_string)
        b.header = json_data['header']
        b.transactions = 
        return b

    def validate(self):
        pass
    
    def __eq__(self,other):
        return self.serialize() == other.serialize()

class Blockchain:
    difficulty = 4
    target = '0000281df3c6c88c98e4f6064fb5e8804812de0fadd6a4d47efa38f8db36346c'
    @classmethod
    def new(self):
        # Instantiates object from passed values
        t = Blockchain()
        t.transactions = []
        # t.chain = [Block(None,None,time())]
        t.chain = {'genesis':Block(None,None,time())}
        print(t.chain[0].getHash())
        return t

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def proof_of_work(block):
        # assert block.previous_hash == self.last_block.getHash()
        # while not block.getHash().startswith('0'*Blockchain.difficulty):
        while not block.getHash()<Blockchain.target:
            block.nonce += 1
        print(1,block.getHash())
        return block.getHash()

    def addTransaction(self,transaction):
        self.transactions.append(transaction)
    
    def addBlock(self, block, proof):
        if block.previous_hash != self.last_block.getHash():
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def mine(self):
        if len(self.transactions)==0:
            return False
        last_block = self.last_block
        transactions = self.transactions
        merkleTree = MerkleTree.build()
        for transaction in transactions:
            merkleTree.add(transaction)
        # print(2,last_block.getHash())
        block = Block(last_block.getHash(),merkleTree.root.hash,time())
        # print(1,merkleTree.root.hash)
        proof = self.proof_of_work(block)
        self.addBlock(block,proof)
        self.transactions = []
        return True

    def resolve():
        pass

    @classmethod
    def validate(self):
        pass

    # def add(...):
    #     # Sign object with private key passed
    #     # That can be called within new()
    #     ...

    # def validate(...):
    #     # Validate transaction correctness.
    #     # Can be called within from_json()
    #     ...

    # def __eq__(...):
    #     # Check whether transactions are the same
    #     ...

def verify_proof(entry, proof, root):
    # Verify the proof for the entry and given root. Returns boolean.
    target_hash = root.hash
    serialized_entry = entry.serialize()
    curr_hash = hashlib.sha256(serialized_entry.encode()).hexdigest()
    for node in proof:
        if node.mode == "L":
            curr_hash = hashlib.sha256((node.hash+curr_hash).encode()).hexdigest()
        elif node.mode == "R":
            curr_hash = hashlib.sha256((curr_hash+node.hash).encode()).hexdigest()
    return target_hash == curr_hash

class Wallet:      
    def new_wallet(self):
        random_gen = Crypto.Random.new().read
        private_key = RSA.generate(1024, random_gen)
        public_key = private_key.publickey()
        response = {
            'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        }
        print(response)
        return response
        
###########################
######## TESTING ##########
###########################

a = Transaction()

# b = Block('a','b','c','d')
# print(json.dump(b.__dict__))
start = time()
transactions = []
for i in range(1000):
    transactions.append(Transaction.new('A','B',random.randint(10,10000),'comment'))

b = Blockchain.new()
print(b.chain)
for i in range(10):
    b.addTransaction(Transaction.new('A','B',random.randint(10,10000),'comment'))
start = time()
b.mine()
print('time:',time()-start)
print(b.chain)
for i in range(10):
    b.addTransaction(Transaction.new('A','B',random.randint(10,10000),'comment'))
start = time()
b.mine()
print(b.chain)
print('time:',time()-start)

#Generating wallet
wallet = Wallet()
wallet.new_wallet()