import random

unique = random.randint(1000,9999)
def generate_chain(n):
    children = [random.randint(1000,9999)]
    chain = {}
    for i in range(n-1):
        new_children = []
        for child in children:
            for i in range(random.randint(0,2)):
                new_children.append(random.randint(1000,9999))
        children = new_children
