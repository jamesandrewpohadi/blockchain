REWARD_PER_MINE = 100 

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
    
    