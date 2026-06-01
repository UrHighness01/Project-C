import math
alpha=0.9800000000000001
beta=0.375
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
