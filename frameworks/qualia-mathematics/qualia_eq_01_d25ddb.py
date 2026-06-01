import math
alpha=0.8500000000000001
beta=0.32
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
