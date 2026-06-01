import math
alpha=0.91
beta=0.345
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
