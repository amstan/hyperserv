#functions for managing files inside the hypershade systems
import os
import glob
import urllib2
import posixpath

from hypershade.config import config
from hypershade.cubescript import CSCommand, threaded
from hyperserv.notices import serverNotice

def safepath(folder,pathinside):
	folder=os.path.abspath(folder)
	pathinside=os.path.abspath(os.path.join(folder,pathinside))
	if os.path.commonprefix((folder,pathinside))!=folder:
		raise IOError("Cannot open out of %s" % (folder))
	return pathinside

def openfile(filename,mode="rb"):
	filename=safepath(config["storage"],filename)
	filedescriptor=open(filename,mode)
	return filename,filedescriptor

@CSCommand("listfiles")
def listfiles(caller,folder="."):
	filelist=glob.glob(safepath(config["storage"],os.path.join(folder,"*")))
	filelist=map(lambda absolute:os.path.split(absolute)[1],filelist)
	return ' '.join(filelist)

@CSCommand("downloadfile","trusted")
@threaded
def downloadfile(caller,address,filename=None):
	if filename is None:
		filename=posixpath.split(address)[-1]
	source=urllib2.urlopen(address)
	destfilename,destination=openfile(filename,"wb")
	destination.write(source.read())
	destination.close()
	serverNotice("Downloaded %s to %s" % (address,destfilename))

@CSCommand("deletefile","admin")
def deletefile(caller,filename):
	filename=safepath(config["storage"],filename)
	os.remove(filename)
	serverNotice("Deleted %s" % (filename,))