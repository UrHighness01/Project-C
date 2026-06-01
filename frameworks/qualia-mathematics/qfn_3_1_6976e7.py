import math
alpha=0.8800000000000001
beta=0.335
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
