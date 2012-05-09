"""This file contains the required functions for the editing features"""

import base
from hypershade.cubescript import playerCS, CSCommand
from hyperserv.servercommands import ServerError

editfnumber=base.packettypenumber("EDITF")
editflength=base.packettypes[editfnumber][1]

@CSCommand("editf","trusted")
def editfcommand(caller,*args):
	editf(*map(int,args))

def editf(*args):
	if len(args)!=editflength:
		raise ServerError("EDITF must have %s arguments." % editflength)
	base.packetSendingQueue.put((editfnumber,)+args)

@CSCommand("makecube","trusted")
def makecube(caller,x,y,z,s=16):
	s=int(s)
	x=int(x)*s
	y=int(y)*s
	z=int(z)*s
	editf(x+s,y,z,1,1,1,s,0,0,2,0,2,1,-1,1)

@CSCommand("makecolumn","trusted")
def makecolumn(caller,x,y,z=0,h=16,s=16):
	s=int(s)
	h=int(h)
	x=int(x)*s
	y=int(y)*s
	z=int(z)*s
	editf(x+s,y,z,1,1,h,s,0,0,2,0,2,1,-1,1)

@CSCommand("corners","trusted")
def cornerscommand(caller,x,y,z,c0,c1,c2,c3,s=16):
	s=int(s)
	
	x=int(x)
	y=int(y)
	z=int(z)
	
	c0=int(c0)
	c1=int(c1)
	c2=int(c2)
	c3=int(c3)
	
	corners(x,y,z,(c0,c1,c2,c3),s)

def corners(x,y,z,cornerslist,s=16):
	x=x*s
	y=y*s
	z=z*s
	for index,depth in enumerate(cornerslist):
		if depth!=0:
			editf(x,y,z,1,1,1,s,5,(index%2),1,(index/2),1,1,depth,0)