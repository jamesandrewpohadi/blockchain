from utils import *

REWARD_PER_MINE = 100 

class Miner:
    
    def __init__(self):
        self.blockchain = Blockchain.new()
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) 
        vk = sk.get_verifying_key()
        self.private = sk.to_string().hex()
        self.public = vk.to_string().hex()

    def mine(self):
        bc = self.blockchain
        balance = bc.balance[bc.last_block.hash].copy()
        m = MerkleTree.build()
        for t in bc.transactions:
            # validate transaction
            f_b = balance.get(t.sender,0)-t.amount
            if f_b>=0 and t.validate():
                balance[t.sender] = f_b
                m.add(t)
        # add reward
        reward = Transaction.new(Blockchain.public,self.public,100)
        reward.sign(Blockchain.private)
        m.add(reward)
        block = Block.new(bc.last_block.header['depth']+1,bc.last_block.hash,m.root.hash,bc.target,m)
        pow = block.proof_of_work()
        bc.addBlock(block)
        bc.transactions = []
        # broadcast the new block
        return True

    def proof(self,transaction):
        pass

    def broadcast(self):
        pass

    def transfer(self,receiver,amount):
        transaction = Transaction.new(self.public,receiver,amount)
        self.blockchain.add(transaction)

# class SPVClient:

# m = Miner()
# m.mine()
# print(m.blockchain.chain)
# print(m.blockchain.balance)
# m.mine()
# print(m.blockchain.chain)
# print(m.blockchain.balance)
# m.mine()
# print(m.blockchain.chain)
# print(m.blockchain.balance)
# m.mine()
# print(m.blockchain.chain)
# print(m.blockchain.balance)


"""
class Miner:
    
    def __init__(self, blockchain):
        self.target = 'FFFFFFFFFFFFFFFFF'
        self.blockchain = blockchain
        self.reward = 0

    def get_reward(self):
        self.reward += REWARD_PER_MINE

    def add_successful_block(self, blockchain, block):
        proof = self.proof_of_work(block)
        self.blockchain.addBlock(block, proof)

    def proof_of_work(self, block): 
        # assert block.previous_hash == self.last_block.getHash()
        # nonce = random.getrandbits(32) #Try different nonce each time
        # block_data = str(block.previous) + str(nonce)
        hash_result = block.getHash()
        # if (int(hash_result, 16) <= int(self.target, 16) and hash_result.startswith('0' * Blockchain.difficulty)):
        if int(hash_result, 16) <= int(self.target, 16):
            print("The corresponding hash of the block is: ", hash_result)
            return hash_result, block.nonce
        print("Mining successful...")
        self.add_successful_block(self.blockchain, block)
        # while not block.getHash().startswith('0' * Blockchain.difficulty):
        #     block.nonce += 1
        # print(1,block.getHash())
        # return block.getHash()
"""
    
