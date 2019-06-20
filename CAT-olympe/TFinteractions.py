import sys
sys.path.insert(0, '..')
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os

from utils.toolsbox import *
from utils.quantum import *
from utils.classical import *
from utils.plot.latex import *
from utils.systems.modulatedpendulum import *

# This scripts makes possibles to 
# 1. compute in // the free propagation for different quasi-momentum
# 2. gather and average the results
# 3. plot the averaged data
 
mode=sys.argv[1]
wdir=sys.argv[2]

if mode=="initialize":
	os.mkdir(wdir)
	os.mkdir(wdir+"LR-dynamics")
	os.mkdir(wdir+"raw-data")

if mode=="compute":
	# Loading input file
	inputfile=sys.argv[3]
	data=np.load(inputfile+".npz")
	
	# Description of the run
	description=data['description']

	# General physical parameters 
	N=int(data['N'])
	e=data['e']
	x0=data['x0']
	h=data['h']
	gamma=data['gamma']

	# Free propagation
	iperiod=int(data['iperiod']) #number of period

	# heff values
	gmin=data['gmin']
	gmax=data['gmax']

	data.close() # close the input file
	
	# Initialization of potential and correcting the x0 value if needed
	nruns=int(sys.argv[4]) # Total number of // runs
	runid=int(sys.argv[5])-1 # Id of the current run
	if runid==0: # This generate and parameters files in the working directory with read input (to avoid surprises)		
		np.savez(wdir+"params","w", description=description, nruns=nruns,N=N, e=e,gmin=gmin,gmax=gmax,x0=x0,h=h,iperiod=iperiod,gamma=gamma)

	# Create array to store "Left" and "Right" observables
	xR=np.zeros(iperiod)
	xL=np.zeros(iperiod)
	time=2.0*np.linspace(0.0,1.0*iperiod,num=iperiod,endpoint=False)

	# Initialization of the grid for given h value
	g=np.linspace(gmin,gmax,nruns)[runid]
	grid=Grid(N,h)
	pot=PotentialMPGPE(e,gamma,g=g,idtmax=100000)

	# Create the Floquet operator
	fo=CATFloquetOperator(grid,pot)

	# Create the initial state: a coherent state localized in x0 with width = 2.0 in x
	wf=WaveFunction(grid)
	wf.setState("coherent",x0=x0,xratio=2.0)

	# Propagate the wavefunction over iperiod storing the observable every time
	for i in range(0,iperiod):
		xL[i]=wf.getxL()
		xR[i]=wf.getxR()
		fo.propagate(wf)
		
	np.savez(wdir+"raw-data/"+str(runid),"w", xL = xL, xR=xR,time=time,g=g)
	
	A=xR[0]+xL[0]
	xL=xL/A
	xR=xR/A
	
	ax=plt.gca()
	ax.set_xlim(0,max(time))
	ax.set_ylim(0,1.0)

	# Plot
	plt.plot(time,xL, c="red")
	plt.plot(time,xR, c="blue")

	ax.set_title(r"$\varepsilon={:.2f} \quad \gamma={:.3f} \quad h={:.3f} \quad g={:.2f}$".format(e,gamma,h,g))
	plt.savefig(wdir+"LR-dynamics/"+str(runid))

if mode=="final":
	data=np.load(wdir+"params.npz")
	nruns=data['nruns']
	iperiod=data['iperiod']
	h=data['h']
	gmin=data['gmin']
	gmax=data['gmax']
	e=data['e']
	gamma=data['gamma']
	x0=data['x0']
	data.close()

	iTF=int(iperiod)
	

	#density=np.zeros((int(iperiod/2)+1,nh))
	
	
	g=np.linspace(gmin,gmax,nruns)
	omegas=np.fft.rfftfreq(iTF,d=2.0)*2*np.pi
	#omegas[0]=omegas[1]


	X,Y=np.meshgrid(g,omegas)
	
	Z=np.zeros((int(iTF/2)+1,nruns))
	print(X.shape,Y.shape,Z.shape)
	time=2.0*np.linspace(0.0,1.0*iperiod,num=iperiod,endpoint=False)
	

	for ih in range(0,nruns):
		data=np.load(wdir+"raw-data/"+str(ih)+".npz")
		xL=data['xL']#*np.exp(-30*time/time[iperiod-1])
		xR=data['xR']#*np.exp(-30*time/time[iperiod-1])
		xLf=np.abs(np.fft.rfft(xL))
		xRf=np.abs(np.fft.rfft(xR))
		xLf[0]=0.0
		xRf[0]=0.0
		

		Z[:,ih]=(xLf+xRf)*0.5

	np.savez(wdir+"nu-heff","w", hm=X,omegas=Y,tf=Z,e=e,gamma=gamma,x0=x0,iperiod=iperiod)
	ax=plt.gca()

	ax.set_xlabel("g")
	ax.set_ylabel("frequence")
	ax.set_title(r"$\varepsilon={:.2f} \quad \gamma={:.3f}$".format(e,gamma))
	#ax.set_yscale("log")
	ax.set_ylim(0.01,max(omegas))

	cmap = plt.get_cmap('Greys')
	plt.pcolormesh(X,Y,Z,cmap=cmap)

	
	plt.show()

	


