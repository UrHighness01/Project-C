import math
alpha=0.8700000000000001
beta=0.33
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
