import math
a=0.8400000000000001; b=0.32999999999999996; c=0.02; d=0.6
def phi(Q,K,T):
    return 1/(1+math.exp(-(a*Q+b*K-c*T))) + d*math.cos(K*Q)*math.exp(-c*T)
