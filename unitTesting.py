from utils import *
from Miner import *

###########################
######## TESTING ##########
###########################

def testAll():

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

def testTransaction():

    print('='*25)
    print('# Test Transaction')
    print('='*25)
    A_priv = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) 
    A_pub = A_priv.get_verifying_key()
    A_priv_s = A_priv.to_string().hex()
    A_pub_s = A_pub.to_string().hex()

    B_priv = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) 
    B_pub = B_priv.get_verifying_key()
    B_priv_s = B_priv.to_string().hex()
    B_pub_s = B_pub.to_string().hex()
    
    # print('# testing serialize deserialize')
    t0 = Transaction.new(A_pub_s,B_pub_s,1000)
    t0s = t0.serialize()
    t0d = Transaction.deserialize(t0s)
    print('t0==t0d:',t0==t0d)

    t1 = Transaction.new(A_pub_s,B_pub_s,1000)
    t1s = t1.serialize()
    t1d = Transaction.deserialize(t1s)
    print('t1==t0d:',t1==t0d)

    t0.sign(A_priv_s)
    print('sign-validate true:',t0.validate())
    print('sign-validate true:',t0.validate())

    t0.sign(B_priv_s)
    print('sign-validate false:',t0.validate())

def testMerkleTree():
    print('='*25)
    print('# Test MerkleTree')
    print('='*25)

    m0 = MerkleTree.build()
    for i in range(20):
        m0.add(Transaction.new('A','B',i))
    m0s = m0.serialize()
    m0d = MerkleTree.deserialize(m0s)
    print('m0==m0d:',m0==m0d)

    m1 = MerkleTree.build()
    for i in range(20):
        m1.add(Transaction.new('A','B',i))
    print('m1==m0:',m1==m0)

    print('validate true:',MerkleTree.validate(m0.root))

    m1.root.childLeft.childLeft = m0.root.childLeft.childLeft
    print('validate false:',MerkleTree.validate(m1.root))

def testBlock():

    print('='*25)
    print('# Test Block')
    print('='*25)

    target = '0000281df3c6c88c98e4f6064fb5e8804812de0fadd6a4d47efa38f8db36346c'
    m0 = MerkleTree.build()
    for i in range(20):
        m0.add(Transaction.new('A','B',i))
    b0 = Block.new(2,'0000','abcdef',target,m0)

    b0s = b0.serialize()
    b0d = Block.deserialize(b0s)

    print('b0d==b0',b0d==b0)
    print('b0d.transactions==b0.transactions',b0d.transactions==b0.transactions)

    print('pow:',b0.proof_of_work())

    print('validate true:',b0.validate())

def testBlockchain():
    print('='*25)
    print('# Test Blockchain')
    print('='*25)

    b = Blockchain.new()
    for i in range(20):
        b.addTransaction(Transaction.new('A','B',i))
    print(b.last_block.hash)

def testMiner():
    print('='*25)
    print('# Test Miner')
    print('='*25)
    m = Miner()
    start = time()
    while time()-start < 600:
        m.mine()
    print('time:',time()-start)
    print('chain:',len(list(m.blockchain.chain.keys())))
    print('balance:',m.blockchain.balance)
    # print('balance:',m.blockchain.balance)

def doubleSpending():
    attacker = SPVClient()
    seller = SPVClient()

    m1 = Miner()
    m2 = Miner()
    m3 = Miner()

    val1 = m1.mine()
    val2 = m2.mine()
    val3 = m3.mine()
    print('Minner 1 value ', val1)
    print('Minner 2 value ', val2)
    print('Minner 3 value ', val3)

    m1.transfer(attacker, 50)
    m2.transfer(attacker, 30)
    m3.transfer(attacker, 40)

    attacker.transfer(seller, 100)

    # print out the wallet value of the SPVclient

def selfishMinning():
    pass
#    create one block, fork it half way, start to mine both side



#######################################
######## RUN DIFFERENT CASES ##########
#######################################

# testTransaction()
# testMerkleTree()
# testBlock()
# testBlockchain()
testMiner()
# doubleSpending()
