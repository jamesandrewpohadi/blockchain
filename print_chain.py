import random

unique = random.randint(1000,9999)

def generate_chain(n):
    # children = [str(random.randint(1000,9999))]
    children = ['****']
    # chain = {children[0]:None}
    chain = {}
    for i in range(n-1):
        new_children = []
        for child in children:
            for i in range(random.randint(0,2)):
                new_child = str(random.randint(1000,9999))
                chain[new_child] = child
                new_children.append(new_child)
        children = new_children
    return chain

def print_chain(chain):
    forward_chain = {}
    for e in chain.keys():
        forward_chain[chain[e]] = forward_chain.get(chain[e],[])+[e]
    
    print(forward_chain)

print('1234 --> 5678 --> 9101\n     |\n     --> 5678 --> 9101 --> 3456\n                       |\n                       --> 7891 --> 2356\n     |\n     --> 5678 --> 9101')
print('1234 __ 5678 --> 9101\n     |\n     __> 5678 --> 9101 --> 3456\n                       |\n                       --> 7891 --> 2356\n     |\n     --> 5678 --> 9101')
chain = generate_chain(4)
print('chain:\n',chain)
print_chain(chain)