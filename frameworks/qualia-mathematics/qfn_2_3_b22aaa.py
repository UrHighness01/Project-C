import math
alpha=0.9700000000000001
beta=0.37
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
