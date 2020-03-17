import time
import hashlib
import ecdsa
from time import time
from utils import Transaction
from utils import MerkleTree
import json

class SPVClient:
    def __init__(self):
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
    
    def receive_block_header(self,miner):
        header = []
        for block in miner.blockchain:
            header.append(block[0].header)
        return header

    def receive_transaction(self, transaction, miner):
        header = self.receive_block_header(miner)

        transaction_hash_value = hashlib.sha256(transaction.encode()).hexdigest()

        proof_of_path = MerkleTree.get_proof(transaction_hash_value) #Need to create a merkle tree of transactions by the miner in the miner class so as to prove and get the path and root
        get_root = MerkleTree.get_root()                             #Should be miner here instead of Merkle Tree

        if proof_of_path != None:
            for i in proof_of_path:
                if i[0] == 0:
                    string = str(i[1]) + str(transaction_hash_value)
                    transaction_hash_value = hashlib.sha256(string.encode()).hexdigest()

                else:
                    string = str(transaction_hash_value) + str(i[1])
                    transaction_hash_value = hashlib.sha256(string.encode()).hexdigest()
        else:
            return False
        
        for i in header:
            json_data = json.loads(i)
            if str(json_data.get('root_hash'))== str(transaction_hash_value):
                return True
        return False

    def send_transaction(self, receiver, amount, comment):
        transaction = Transaction.new(self.public_key.to_string(), receiver, amount, comment)
        transaction.sign(self.private_key.to_string())
        return transaction