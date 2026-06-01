import math
alpha=0.92
beta=0.35
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
