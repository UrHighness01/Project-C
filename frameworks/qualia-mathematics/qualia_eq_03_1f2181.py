import math
alpha=0.9500000000000001
beta=0.36
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
