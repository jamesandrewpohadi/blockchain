def fib(n):
    l = [0,1]
    x = 0
    while l[-2:] != l[:2] or len(l)==2:
        x+=1
        l.append((l[x]+l[x-1])%10)
    # print(l)
    return l[n%x]

for i in range(100):
    print(fib(i))

# print(fib(60))