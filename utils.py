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
    def new(self,sender,receiver,amount,comment=''):
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
        data = {
            'sender':self.sender,
            'receiver':self.receiver,
            'amount':self.amount,
            'comment':self.comment,
            'time':self.time,
            'sig':self.sig
        }
        json_string = json.dumps(data)
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
            vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(self.sender), curve=ecdsa.SECP256k1)
            sig = self.sig
            sig_bytes = bytes.fromhex(self.sig)
            self.sig = ''
            s = self.serialize()
            self.sig = sig
            return vk.verify(sig_bytes,s.encode())
        except:
            return False
    
    def __eq__(self,other):
        return self.id == other.id

    def __str__(self):
        return 'Transaction({}..)'.format(self.id[:6])

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

    def add(self,transaction):
        # Add entries to tree
        serialized_transaction = transaction.serialize()
        leave = LeaveNode(transaction).getHash()
        if self.val2leave.get(serialized_transaction,None) != None:
            print('Transaction rejected since already exist in the MerkleTree')
            return False
        self.val2leave[serialized_transaction] = leave
        self.root = self.root.addLeave(leave)
        return True

    @classmethod
    def build(self,description='James Chain'):
        # Build tree computing new root
        m = MerkleTree()
        m.description = description
        t_origin = Transaction.new(None,None,0,'Origin')
        t_description = Transaction.new(None,None,0,description)
        t_origin.time = 0
        t_description.time = 0
        origin = LeaveNode(t_origin).getHash()
        description = LeaveNode(t_description).getHash()
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

    def get_list(self):
        return list(self.val2leave.keys())

    def serialize(self):
        serialized_transactions = list(self.val2leave.keys())
        data = {
            'description':self.description,
            'transactions':serialized_transactions
        }
        json_string = json.dumps(data)
        return base64.b64encode(json_string.encode('utf-8')).decode()

    @classmethod
    def deserialize(self,base64_string):
        json_string = base64.b64decode(base64_string.encode()).decode()
        json_data = json.loads(json_string)
        # origin = LeaveNode('Origin').getHash()
        # description = LeaveNode(json_data['description']).getHash()
        
        m = MerkleTree.build(json_data['description'])
        for st in json_data['transactions']:
            transaction = Transaction.deserialize(st)
            m.add(transaction)
        return m

    @staticmethod
    def validate(node):
        if not isinstance(node,LeaveNode):
            concat = node.childLeft.hash + node.childRight.hash
            hash = hashlib.sha256(concat.encode()).hexdigest()
            return node.hash == hash and MerkleTree.validate(node.childLeft) and MerkleTree.validate(node.childRight)
        else:
            return True

    # @staticmethod
    # def verify_proof():


    def __eq__(self,other):
        if not isinstance(other,MerkleTree):
            return False
        return self.description == other.description and self.root.hash == other.root.hash

class Block:

    @classmethod
    def new(self, depth, previous_hash, root_hash, bits, transactions=None):
        b = Block()
        b.header = {
            'depth':depth,
            'previous_hash': previous_hash,
            'root_hash':root_hash,
            'timestamp':time(),
            'bits':bits,
            'nonce':0
        }
        b.getHash()
        b.transactions = transactions
        return b

    def proof_of_work(self):
        while not int(self.hash,16)<int(self.header['bits'],16):
            self.header['nonce'] += 1
            self.getHash()
        return self.hash

    def getHash(self):
        json_string = json.dumps(self.header)
        hash = hashlib.sha256(json_string.encode()).hexdigest()
        self.hash = hash
        return hash

    def serialize(self):
        data_dict = {
            'header': self.header,
            'transactions': self.transactions.serialize()
        }
        json_string = json.dumps(data_dict)
        return base64.b64encode(json_string.encode('utf-8')).decode()

    @classmethod
    def deserialize(self,base64_string, type='full'):
        b = Block()
        json_string = base64.b64decode(base64_string.encode()).decode()
        json_data = json.loads(json_string)
        b.header = json_data['header']
        b.getHash()
        if type == 'full':
            b.transactions = MerkleTree.deserialize(json_data['transactions'])
        elif type == 'simplified':
            b.transactions = None
        return b

    def validate(self):
        # validate merkle tree hashes
        return MerkleTree.validate(self.transactions.root)
    
    def __eq__(self,other):
        return json.dumps(self.header) == json.dumps(other.header)

    def __str__(self):
        return 'Block(..{})'.format(self.hash[-6:])

class Blockchain:

    private = '3e59b1763f5191b0ab15975c7a6b77f8a55c922f68baddbf1c1c7348884d1736'
    public = '2fba45a1f17dd07e75092fb63b6d7dd79896d05a0c2afc2504706a6ce60e1f9458c47de9651808418fb197209b385cd2b5ba839c865989e187bcad1190704f83'
    target = '0000181df3c6c88c98e4f6064fb5e8804812de0fadd6a4d47efa38f8db36346c'
    
    @classmethod
    def new(self,name):
        # Instantiates object from passed values
        t = Blockchain()
        t.name = name
        t.transactions = []
        t.balance = {'genesis':{}}
        genesis_block = Block.new(0, None, None, Blockchain.target, transactions=MerkleTree.build())
        genesis_block.hash = 'genesis'
        t.chain = {'genesis':genesis_block}
        t.longest = t.chain['genesis']
        return t

    @property
    def last_block(self):
        return self.longest

    def addTransaction(self,transaction):
        if self.transaction.validate():
            print('{} added {}'.format(self.name,transaction))
            self.transactions.append(transaction)

    def get_proof(self,transaction):
        bc = self.blockchain
        block = bc.last_block
    
    def addBlock(self, block):
        block_hash = block.getHash()
        valid = self.validate(block)
        if not valid:
            print('{} dropped {}'.format(self.name,block))
            return False
        self.balance[block_hash] = valid
        self.chain[block_hash] = block
        self.resolve(block)
        print('{} added {}'.format(self.name,block))
        return True

    def validate(self,block):
        block_hash = block.getHash()
        # check hash
        if not int(block_hash,16)<int(block.header['bits'],16):
            return False
        # check previous hash
        if not block.header['previous_hash'] in self.chain:
            return False
        # check transactions validity
        if not block.transactions == None:
            prev_block = self.last_block
            prev_t = []
            while prev_block.header['previous_hash']:
                prev_t.extend(prev_block.transactions.get_list())
                prev_block = self.chain[prev_block.header['previous_hash']]
            prev_t = set(prev_t)
            # h = self.last_block.hash
            # prev_t = []
            # for i in range(6):
            #     prev_t.extend(self.chain[h].transactions.get_list())
            # prev_t = set(prev_t)
            balance = self.balance[block.header['previous_hash']].copy()
            t_l = block.transactions.get_list()
            for t_s in t_l:
                if t_s in prev_t:
                    return False
                t = block.transactions.val2leave[t_s].val
                f_b = balance.get(t.sender,0)-t.amount
                if f_b<0 and not t.sender == Blockchain.public:
                    return False
                else:
                    if not t.sender == Blockchain.public:
                        balance[t.sender] = f_b
                    balance[t.receiver] = balance.get(t.receiver,0)+t.amount
        return balance

    def resolve(self,added_block):
        if added_block.header['depth'] >= self.longest.header['depth']:
            self.longest = added_block

    # def add(...):
    #     # Sign object with private key passed
    #     # That can be called within new()
    #     ...

    # def validate(...):
    #     # Validate transaction correctness.
    #     # Can be called within from_json()
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
    def __init__(self,name,ip,port,type='miner'):
        self.name = name
        self.ip = ip
        self.port = port
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) 
        vk = sk.get_verifying_key()
        self.private = sk.to_string().hex()
        self.public = vk.to_string().hex()
        self.type = type
        self.contacts = {
            'miner':[],
            'spv':[]
        }

    def get_id(self):
        return {
            'address':'http://{}:{}'.format(self.ip,self.port),
            'public':self.public,
            'type':self.type
        }

    # def new_wallet(self):
    #     random_gen = Crypto.Random.new().read
    #     private_key = RSA.generate(1024, random_gen)
    #     public_key = private_key.publickey()
    #     response = {
    #         'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
    #         'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    #     }
    #     print(response)
    #     return response
