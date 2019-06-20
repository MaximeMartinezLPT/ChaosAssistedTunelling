import sys
sys.path.insert(0, '..')
import numpy as np
from utils.toolsbox import *

inputfile="input/a_0d7"

N=100
alpha=0.7

# CFS
tmax=2000
i0=int(N/4)

# Multifractal dimensions
pNmin=4
pNmax=8
Ntable=2**np.arange(pNmin,pNmax+1) # Value of N explored
nrunsN=np.array([1024,512,256,128,64]) # Number of runs for each
Ninfo=np.empty((2,sum(nrunsN)),dtype=int)
index=0
for i in range(0,nrunsN.size):
	for j in range(0,nrunsN[i]):
		Ninfo[0,index]=int(Ntable[i]) # Value of N for given run
		Ninfo[1,index]=int(j) # Relative index for given N
		index+=1
q=np.linspace(-4.0,4.0,35)
print("/!\ if you are running Dq as function of q")
print("------> set nruns=",sum(nrunsN))


	
np.savez(inputfile,"w", N=N,alpha=alpha,tmax=tmax,i0=i0,q=q,Ntable=Ntable,nrunsN=nrunsN,Ninfo=Ninfo)
