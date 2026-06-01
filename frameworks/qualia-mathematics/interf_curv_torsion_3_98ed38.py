import math
a=0.92; b=0.39; c=0.06; d=0.8
def phi(Q,K,T):
    return 1/(1+math.exp(-(a*Q+b*K-c*T))) + d*math.cos(K*Q)*math.exp(-c*T)
