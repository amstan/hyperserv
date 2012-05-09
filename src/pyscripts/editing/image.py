"""This file contains the required functions for the editing features"""

import Image
import math
import os

import base
import cubes

from hypershade.cubescript import playerCS, CSCommand, threaded
from hyperserv.servercommands import ServerError
from hyperserv.notices import serverNotice
from hypershade.files import openfile

@CSCommand("loadimage1","trusted")
@threaded
def loadimage1(caller,imagename,s=16,maxh=20):
	s=int(s)
	(xsize, ysize, heights)=loadheightmap(imagename,int(maxh))
	
	serverNotice("Loading image %s for blocky heightmaps. %sx%sx%s" % (imagename,xsize,ysize,s))
	
	mapsize=base.newmap(caller,math.ceil(max(math.log(xsize*s,2),math.log(ysize*s,2))))
	middleheight=2**(mapsize-1)/s
	
	for y in xrange(ysize):
		for x in xrange(xsize):
			cubes.makecolumn(caller,x,y,middleheight,heights[x][y],s)
	
	serverNotice("Done filling packet queue with heightmap.")

@CSCommand("loadimage2","trusted")
@threaded
def loadimage2(caller,imagename,s=16,maxh=20):
	s=int(s)
	(xsize, ysize, heights)=loadheightmap(imagename,int(maxh)*8)
	
	serverNotice("Loading image %s for smooth heightmaps. %sx%sx%s" % (imagename,xsize,ysize,s))
	
	mapsize=base.newmap(caller,math.ceil(max(math.log(xsize*s,2),math.log(ysize*s,2))))
	middleheight=2**(mapsize-1)/s
	
	for y in xrange(ysize-1):
		for x in xrange(xsize-1):
			neighbourheights=(heights[y][x],heights[y][x+1],heights[y+1][x],heights[y+1][x+1])
			cubeheight=(max(neighbourheights)-1)/8+1
			cubes.makecolumn(caller,x,y,middleheight,cubeheight,s)
			cubes.corners(x,y,middleheight+cubeheight-1,(cubeheight*8-h for h in neighbourheights),s)
	
	serverNotice("Done filling packet queue with heightmap.")

def loadheightmap(imagename,maxh):
	im = Image.open(openfile(os.path.join("heightmaps",imagename))[1])
	pixels = im.load()
	(xsize, ysize) = im.size
	heights=[]
	for y in xrange(ysize):
		heights.append([])
		for x in xrange(xsize):
			heights[y].append(sum(pixels[x,y])*maxh/256/3)
	return xsize, ysize, heights