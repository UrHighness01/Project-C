import math
alpha=0.8600000000000001
beta=0.325
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
