import math
alpha=0.9600000000000001
beta=0.365
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
