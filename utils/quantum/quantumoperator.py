import numpy as np

from utils.quantum.grid import *
from utils.quantum.wavefunction import *

# This script contains: 3 classes
# + class : QuantumOperator
# + class : QuantumTimePropagator
# + class : CATFloquetOperator

class QuantumOperator:
	# This class provides a discrete representation for an x/p acting operator
	def __init__(self, grid):
		self.grid=grid
		self.N=grid.N
		self.h=grid.h
		self.hermitian=False
		self.Mrepresentation="x" #x or p depending on how you fillup M
		self.M=np.zeros((self.N,self.N),dtype=np.complex_) # The operator representation
		self.eigenval=np.zeros(self.N,dtype=np.complex_) 
		self.eigenvec=[] # Eigenstates (from wave function class) id est can be used in both representation
	
	def fillM(self):
		# Fill the matrix representation of the operator
		pass
					
	def diagonalize(self):
		# Diagonalyze the matrix representation of the operator and 
		# save the wavefunctions
		self.fillM()
		eigenvec=np.zeros((self.N,self.N),dtype=np.complex_)
		if self.hermitian:
			self.eigenval,eigenvec=np.linalg.eigh(self.M)
		else:
			self.eigenval,eigenvec=np.linalg.eig(self.M)
			
		if self.Mrepresentation=="x": 
			for i in range(0,self.N):
				wf=WaveFunction(self.grid)
				wf.x=eigenvec[:,i]
				wf.x2p()
				self.eigenvec.insert(i,wf)
		elif self.Mrepresentation=="p":
			for i in range(0,self.N):
				wf=WaveFunction(self.grid)
				wf.p=np.fft.ifftshift(eigenvec[:,i])*self.grid.phaseshift
				wf.p2x()
				self.eigenvec.insert(i,wf)
	
	def saveEvec(self,husimi,wdir,index=0):
		# This functions saves a given list of eigenvectors
		if index==0:
			index=range(0, self.N)
		for i in index:
			husimi.save(self.eigenvec[i],wdir+strint(i),title=str(np.angle(self.eigenval[i])))
			self.eigenvec[i].save(wdir+string(i))
				
class QuantumTimePropagator(QuantumOperator):
	# Class to be used to described time evolution operators such has
	# |psi(t')>=U(t',t)|psi(t)> with U(t',t)=U(dt,0)^idtmax
	# It relies on splliting method with H = p**2/2m + V(x,t)
	# It can be use for :
	# - periodic V(x,t) -> dt=T0/idtmax
	# - time-indepent V(x) -> T0=1, idtmax="n" 
	# - periodic kicked system : T0 = 1, idtmax=1
	
	# /!\ Not adapted to non linear terms such a Gross-Pitaevskii
	def __init__(self,grid,potential,idtmax=1,T0=1,beta=0.0,g=0.0):
		QuantumOperator.__init__(self,grid)
		self.hermitian=False
		
		self.potential=potential
		self.T0=T0 # Length of propagation
		self.idtmax=idtmax 
		self.dt=self.T0/self.idtmax
		self.beta=beta # quasi-momentum
		self.g=g #interactions
		
		
		# In order to gain time in propagation, we pre-compute 
		# splitted propagator that appears to be constant most of time
		# NB: if you have non interactions terms, this doesn't work
		self.Up=np.zeros(self.N,dtype=np.complex_)
		self.Up=np.exp(-(1j/grid.h)*((grid.p-self.beta)**2/4)*self.dt)
		self.Ux=np.zeros((idtmax,self.N),dtype=np.complex_)
		if self.potential.isTimeDependent:
			for idt in range(0,idtmax):
				self.Ux[idt]=np.exp(-(1j/grid.h)*(self.potential.Vx(grid.x,idt*self.dt))*self.dt)
		else:
			self.Ux[0]=np.exp(-(1j/grid.h)*(self.potential.Vx(grid.x))*self.dt)
			
	def propagate(self,wf):
		# Propagate over one period/kick/arbitray time 
		for idt in range(0,self.idtmax):
			wf.p=wf.p*self.Up 
			wf.p2x() 
			wf.x=wf.x*self.Ux[idt]
			wf.x2p() 
			wf.p=wf.p*self.Up  
			
	def UxGP(self,idt,wfx):
		# Ux with interactions
		return np.exp(-(1j/self.grid.h)*(self.potential.Vx(self.grid.x,idt*self.dt)+self.g*abs(np.conj(wfx)*wfx))*self.dt)
			
	def propagateGP(self,wf):
		# Propagate over one period/kick/arbitray time with interactions
		for idt in range(0,self.idtmax):
			wf.p=wf.p*self.Up 
			wf.p2x() 
			wf.x=wf.x*self.UxGP(idt,wf.x)
			wf.x2p() 
			wf.p=wf.p*self.Up  
			
	def fillM(self):
		# Propagate N dirac in x representation, to get matrix representation
		# of the quantum time propagator
		self.Mrepresentation="x"
		for i in range(0,self.N):
			wf=WaveFunction(self.grid)
			wf.setState("diracx",i0=i) 
			self.propagate(wf)
			wf.p2x()
			self.M[:,i]=wf.x 
			
class CATFloquetOperator(QuantumTimePropagator):
	# This class is specific for CAT purpose:
	# WIP: a bit dirty.
	def __init__(self,grid,potential,idtmax=1,T0=1,beta=0.0,g=0.0):
		QuantumTimePropagator.__init__(self,grid,potential,idtmax=idtmax,T0=T0,beta=beta,g=0.0)
		self.proj=np.zeros(grid.N)
		self.qE=np.zeros(grid.N) # quasi energies
		self.index=np.array([],dtype=int)
		self.iqgs=0 #quasi ground state
		self.iqfes=0 # quasi first excited state
		
	def propagateQuarter(self,wf,i0=0):
		# Propagate over one period/kick/arbitray time 
		# i0=0,1,2,3
		it0=i0*int(self.idtmax/4)
		for idt in range(0,int(self.idtmax/4)):
			wf.p=wf.p*self.Up 
			wf.p2x() 
			wf.x=wf.x*self.Ux[it0+idt]
			wf.x2p() 
			wf.p=wf.p*self.Up 
			
	def propagateQuarterGP(self,wf,i0=0):
		# Propagate over one period/kick/arbitray time 
		# i0=0,1,2,3
		it0=i0*int(self.idtmax/4)
		for idt in range(0,int(self.idtmax/4)):
			wf.p=wf.p*self.Up 
			wf.p2x() 
			wf.x=wf.x*self.UxGP(it0+idt,wf.x)
			wf.x2p() 
			wf.p=wf.p*self.Up  
	
	def findTunellingStates(self,wf):
		# Find the two states that tunnels given a wavefunction
		
		# Check the overlap with the given wave function
		for i in range(0,self.N):
			self.proj[i]=self.eigenvec[i]//wf
			self.qE[i]=-np.angle(self.eigenval[i])*(self.h/self.T0)
			if self.proj[i]>0.01:
				self.index=np.append(self.index,[i])
			
		# Find the two states that tunnels
		max1=np.argmax(self.proj)
		proj1=self.proj[max1]
		self.proj[max1]=0.0
		max2=np.argmax(self.proj)
		self.proj[max1]=proj1
		
		# Eigenvectors are ordered by quasi-energies qE1<qE2
		# This can be differents to projections ordering!
		
		# Check basic ordering
		if self.qE[max1]<self.qE[max2]:
			self.iqgs=max1
			self.iqfes=max2
		else:
			self.iqgs=max2
			self.iqfes=max1
		
		# Check if this is not a 
		if self.diffqE1qE2(self.iqfes,self.iqgs)<0:
			self.iqfes,self.iqgs=self.iqgs,self.iqfes
			
	def getTunnelingPeriod(self):
		# Get the tunneling period
		return 2*np.pi*self.h/(self.T0*(self.diffqE1qE2(self.iqfes,self.iqgs)))
		
	def getQEs(self,n):
		# Returns the n states with the largest projections on coherent states
		qes=np.zeros(n)
		ind=np.flipud(np.argsort(self.proj))
		for i in range(0,n):
			qes[i]=self.qE[ind[i]]
		return qes	
		
	def getQE(self,i0):
		# Returns either the quasi-energy of quasi-ground state or quasi-first excited state
		if i0==0:
			i=self.iqgs
		else:
			i=self.iqfes
		return self.qE[i]
		
	def getEvec(self,i0):
		# Same as getQE but returns the state instead of quasi energy
		if i0==0:
			i=self.iqgs
		else:
			i=self.iqfes
		return self.eigenvec[i]
			
	def getQETh(self,i0,pot):
		# Returns expected value of quasi-energies according to 
		# perturbation theory up to 3rd order for a given potential
		V00=pot.braketVxasym(self.eigenvec[0],self.eigenvec[0])
		V11=pot.braketVxasym(self.eigenvec[1],self.eigenvec[1])
		V01=pot.braketVxasym(self.eigenvec[0],self.eigenvec[1])
		V10=pot.braketVxasym(self.eigenvec[1],self.eigenvec[0])
		E0mE1=self.diffqE1qE2(0,1)
		E1mE0=-E0mE1
		
		if i0==0:
			e0=self.qE[self.iqgs]
			e1=abs(V00)
			e2=abs(V01)**2/E0mE1
			e3=abs(V01)**2/(E0mE1)**2*(abs(V11)-abs(V00))
			#e4=abs(V01)**2*abs(V11)**2/E0mE1**3-e2*abs(V10)**2/E0mE1**4-2*abs(V00)*abs(V01)**2*abs(V11)/E0mE1**3+abs(V00)**2*abs(V01)**2/E0mE1**3
		elif i0==1:
			e0=self.qE[self.iqfes]
			e1=abs(V11)
			e2=abs(V01)**2/E1mE0
			e3=abs(V01)**2/(E0mE1)**2*(abs(V00)-abs(V11))
			#e4=abs(V11)**2*abs(V00)**2/E1mE0**3-e2*abs(V10)**2/E1mE0**4-2*abs(V11)*abs(V01)**2*abs(V00)/E1mE0**3+abs(V11)**2*abs(V01)**2/E1mE0**3
		
		e=e0 +e1 +e2 #+e3
		return e	
		
	def diffqE1qE2(self,i1,i2):
		# This returns the difference on a circle
		qE1=self.qE[i1]
		qE2=self.qE[i2]
		dE=np.pi*(self.h/self.T0)
		diff=qE1-qE2
		if diff>dE:
			return diff-2*dE
		elif diff<-dE:
			return diff+2*dE
		else:
			return diff
		
