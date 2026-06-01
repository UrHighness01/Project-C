import math
alpha=0.9
beta=0.33999999999999997
def phi(Q,K):
    return math.tanh(alpha*Q)*math.exp(-beta*K)
