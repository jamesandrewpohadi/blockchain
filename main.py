import time
import hashlib
import ecdsa
from time import time
import json
import base64
import random

class Transaction:

    @classmethod
    def new(self,sender,receiver,amount,comment):
        t = Transaction()
        t.sender = sender
        t.receiver = receiver
        t.amount = amount
        t.comment = comment
        t.time = time()
        t.sk = ecdsa.SigningKey.generate()
        t.vk = t.sk.get_verifying_key()
        return t

    def serialize(self):
        string = {'sender':self.sender,'receiver':self.receiver,'amount':self.amount,'comment':self.comment,'time':self.time}
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
        return t


    def sign(self):
        s = self.serialize()
        sig = self.sk.sign(s.encode())
        self.sig = sig
        return sig

    def validate(self):
        tmp = self.sig
        self.sig = ""
        s = self.serialize()
        return self.vk.verify(tmp,s.encode())
    
    def __eq__(self,other):
        return self.sender == other.sender and self.receiver == other.receiver and self.amount == other.amount and self.comment == other.comment

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
    def __init__(self,transId):
        self.mode = None
        self.parent = None
        self.id = transId
        self.weight = 1
        self.hash = None

    def getHash(self):
        self.hash = hashlib.sha256(self.id.encode()).hexdigest()
        return self

class MerkleTree:
    
    def __init__(self,description='James Chain'):
        origin = LeaveNode('Origin').getHash()
        description = LeaveNode(description).getHash()
        self.root = TreeNode(None,origin,description).getHash()
        self.trans2leave = {}

    def add(self,transaction):
        # Add entries to tree
        serialized_transaction = transaction.serialize()
        leave = LeaveNode(serialized_transaction).getHash()
        self.trans2leave[serialized_transaction] = leave
        self.root = self.root.addLeave(leave)

    def build(self):
        # Build tree computing new root
        pass

    def get_proof(self,transaction):
        # Get membership proof for entry
        proof = []
        serialized_transaction = transaction.serialize()
        node = self.trans2leave[serialized_transaction]
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

class Block:
    def __init__(self, previous_hash,root_hash,timestamp):
        self.previous_hash = previous_hash
        self.root_hash = root_hash
        self.timestamp = timestamp
        self.nonce = 0

    @classmethod
    def new(self,transactions,previous_hash,root_hash,timestamp):
        t = Block()
        t.previous_hash = previous_hash
        t.root_hash = root_hash
        t.timestamp = timestamp
        t.nonce = nonce
        return t

    def getHash(self):
        hash = hashlib.sha256(self.serialize().encode()).hexdigest()
        return hash

    def serialize(self):
        string = {
            'previous_hash':self.previous_hash,
            'root_hash':self.root_hash,
            'timestamp':self.timestamp,
            'nonce':self.nonce
        }
        json_string = json.dumps(string)
        return base64.b64encode(json_string.encode('utf-8')).decode()

    @classmethod
    def deserialize(self,base64_string):
        json_string = base64.b64decode(base64_string.encode()).decode()
        json_data = json.loads(json_string)
        t = Block()
        t.previous_hash = json_data['previous_hash']
        t.root_hash = json_data['root_hash']
        t.timestamp = json_data['timestamp']
        t.nonce = json_data['nonce']
        return t

    def validate(self):
        pass
    
    def __eq__(self,other):
        return self.serialize() == other.serialize()

class Blockchain:
    difficulty = 5
    @classmethod
    def new(self):
        # Instantiates object from passed values
        t = Blockchain()
        t.transactions = []
        t.chain = [Block(None,None,time())]
        print(t.chain[0].getHash())
        return t

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def proof_of_work(block):
        # assert block.previous_hash == self.last_block.getHash()
        while not block.getHash().startswith('0'*Blockchain.difficulty):
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
        # print(last_block.getHash())
        transactions = self.transactions
        merkleTree = MerkleTree()
        for transaction in transactions:
            merkleTree.add(transaction)
        # print(2,last_block.getHash())
        block = Block(last_block.getHash(),merkleTree.root.hash,time())
        # print(1,merkleTree.root.hash)
        proof = self.proof_of_work(block)
        self.addBlock(block,proof)
        self.transactions = []
        return True

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
b.mine()
print(b.chain)
for i in range(10):
    b.addTransaction(Transaction.new('A','B',random.randint(10,10000),'comment'))
b.mine()
print(b.chain)

print(time()-start)