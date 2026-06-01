import math
a=0.88; b=0.36; c=0.04; d=0.7
def phi(Q,K,T):
    return 1/(1+math.exp(-(a*Q+b*K-c*T))) + d*math.cos(K*Q)*math.exp(-c*T)
