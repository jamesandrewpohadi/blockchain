import time
import hashlib
import ecdsa
from time import time
from utils import Transaction
from utils import MerkleTree
import json

class SPVClient:
    def __init__(self):
        self.blockchain = Blockchain.new()
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) 
        vk = sk.get_verifying_key()
        self.private = sk.to_string().hex()
        self.public = vk.to_string().hex()

    def receive_block_header(self, serialized_block):
        b = Block.deserialize(serialized_block,type='simplified')
        self.blockchain.addBlock(b)
    
    # def receive_block_header(self,miner):
    #     header = []
    #     for block in miner.blockchain:
    #         header.append(block[0].header)
    #     return header

    def verify_transaction(self, transaction, proof, block_hash):
        # Verify the proof for the entry and given root. Returns boolean.
        bc = self.blockchain
        block = bc.last_block
        while block.hash != block_hash:
            if block.header['previous_hash'] == None:
                return False
            block = bc.chain[block.header['previous_hash']]
        target_hash = block.header['root_hash']
        serialized_transaction = transaction.serialize()
        curr_hash = hashlib.sha256(serialized_transaction.encode()).hexdigest()
        for node in proof:
            if node.mode == "L":
                curr_hash = hashlib.sha256((node.hash+curr_hash).encode()).hexdigest()
            elif node.mode == "R":
                curr_hash = hashlib.sha256((curr_hash+node.hash).encode()).hexdigest()
        return target_hash == curr_hash
        # header = self.receive_block_header(miner)

        # transaction_hash_value = hashlib.sha256(transaction.encode()).hexdigest()

        # proof_of_path = MerkleTree.get_proof(transaction_hash_value) #Need to create a merkle tree of transactions by the miner in the miner class so as to prove and get the path and root
        # get_root = MerkleTree.get_root()                             #Should be miner here instead of Merkle Tree

        # if proof_of_path != None:
        #     for i in proof_of_path:
        #         if i[0] == 0:
        #             string = str(i[1]) + str(transaction_hash_value)
        #             transaction_hash_value = hashlib.sha256(string.encode()).hexdigest()

        #         else:
        #             string = str(transaction_hash_value) + str(i[1])
        #             transaction_hash_value = hashlib.sha256(string.encode()).hexdi`gest()
        # else:
        #     return False`
        
        # for i in header:
        #     json_data = json.loads(i)
        #     if str(json_data.get('root_hash'))== str(transaction_hash_value):
        #         return True
        # return False

    def send_transaction(self, receiver, amount, comment):
        transaction = Transaction.new(self.public, receiver, amount, comment)
        transaction.sign(self.private)
        return transaction