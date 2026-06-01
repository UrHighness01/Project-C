import math
alpha=0.93
beta=0.355
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
