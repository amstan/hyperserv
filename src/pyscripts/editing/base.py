"""This file contains the required functions for the editing features"""

import sbserver

from twisted.internet import reactor

from hypershade.cubescript import playerCS, CSCommand
from hypershade.config import config
from hyperserv.events import eventHandler, triggerServerEvent
from hyperserv.servercommands import ServerError
from hyperserv.notices import serverNotice
from hypershade.util import formatCaller

packettypes = [('CONNECT', -1), ('SERVINFO', -1), ('WELCOME', 1), ('INITCLIENT', -1), ('POS', -1), ('TEXT', -1), ('SOUND', 1), ('CDIS', 1), ('SHOOT', -1), ('EXPLODE', -1), ('SUICIDE', 0), ('DIED', 3), ('DAMAGE', 5), ('HITPUSH', 6), ('SHOTFX', 9), ('EXPLODEFX', 3), ('TRYSPAWN', 0), ('SPAWNSTATE', 13), ('SPAWN', 2), ('FORCEDEATH', 1), ('GUNSELECT', 1), ('TAUNT', 0), ('MAPCHANGE', -1), ('MAPVOTE', -1), ('ITEMSPAWN', 1), ('ITEMPICKUP', 1), ('ITEMACC', 2), ('TELEPORT', -1), ('JUMPPAD', -1), ('PING', 1), ('PONG', 1), ('CLIENTPING', 1), ('TIMEUP', 1), ('MAPRELOAD', 0), ('FORCEINTERMISSION', 0), ('SERVMSG', -1), ('ITEMLIST', -1), ('RESUME', -1), ('EDITMODE', 1), ('EDITENT', 10), ('EDITF', 15), ('EDITT', 15), ('EDITM', 15), ('FLIP', 13), ('COPY', 13), ('PASTE', 13), ('ROTATE', 14), ('REPLACE', 16), ('DELCUBE', 13), ('REMIP', 0), ('NEWMAP', 1), ('GETMAP', 0), ('SENDMAP', -1), ('CLIPBOARD', -1), ('EDITVAR', -1), ('MASTERMODE', 1), ('KICK', 1), ('CLEARBANS', 0), ('CURRENTMASTER', 3), ('SPECTATOR', 2), ('SETMASTER', -1), ('SETTEAM', -1), ('BASES', -1), ('BASEINFO', -1), ('BASESCORE', -1), ('REPAMMO', 0), ('BASEREGEN', 5), ('ANNOUNCE', 1), ('LISTDEMOS', 0), ('SENDDEMOLIST', -1), ('GETDEMO', 1), ('SENDDEMO', -1), ('DEMOPLAYBACK', 2), ('RECORDDEMO', 1), ('STOPDEMO', 0), ('CLEARDEMOS', 1), ('TAKEFLAG', 2), ('RETURNFLAG', 3), ('RESETFLAG', 5), ('INVISFLAG', 2), ('TRYDROPFLAG', 0), ('DROPFLAG', 6), ('SCOREFLAG', 9), ('INITFLAGS', -1), ('SAYTEAM', -1), ('CLIENT', -1), ('AUTHTRY', -1), ('AUTHCHAL', -1), ('AUTHANS', -1), ('REQAUTH', -1), ('PAUSEGAME', 1), ('ADDBOT', 1), ('DELBOT', 0), ('INITAI', -1), ('FROMAI', 1), ('BOTLIMIT', 1), ('BOTBALANCE', 1), ('MAPCRC', -1), ('CHECKMAPS', 0), ('SWITCHNAME', -1), ('SWITCHMODEL', 1), ('SWITCHTEAM', -1), ('INITAI', -1), ('FROMAI', -1), ('BOTLIMIT', -1), ('BOTBALANCE', -1), ('MAPCRC', -1), ('CHECKMAPS', -1), ('SWITCHNAME', -1), ('SWITCHMODEL', -1), ('SWITCHTEAM', -1)]

class packetSendingQueue:
	consuming=False
	data=[]
	
	def consume(self):
		if self.consuming==True:
			return
		self.consuming=True
		self.consumer()
	
	def consumer(self):
		try:
			sbserver.sendPacket(*self.get())
			reactor.callLater(float(config["editpacketinterval"]),self.consumer)
		except IndexError:
			self.stop()
	
	def get(self):
		return self.data.pop(-1)
	
	def put(self,packet):
		self.data.insert(0,packet)
		self.consume()
	
	def stop(self):
		self.consuming=False
		self.data=[]
packetSendingQueue=packetSendingQueue()

@CSCommand("clearpackets","admin")
@eventHandler('no_clients')
def stopSendingPackets(caller=None):
	packetSendingQueue.stop()

def packettypename(number):
	return packettypes[int(number)][0]

def packettypenumber(name):
	for number,packettype in enumerate(packettypes):
		if packettype[0]==name:
			return number
	return int(name)
 
@CSCommand("sendpacket","admin")
def sendpacket(caller,*args):
	if len(args)==0:
		return
	packettype=packettypes[packettypenumber(args[0])]
	if (packettype[1]!=-1 and len(args)!=(packettype[1]+1)):
		raise ServerError("%s must have %s arguments." % packettype)
	packetSendingQueue.put(map(packettypenumber,args))

@eventHandler("edit_packet")
def noticeEditPacket(cn,packettype,*data):
	if config["editpacketnotices"]=="yes":
		serverNotice("Edit Packet from %s: %s %s" % (formatCaller(("ingame",cn)),packettypes[packettype][0],' '.join(map(str,data))))

@CSCommand("newmap","trusted")
def newmap(caller,size):
	size=int(size)
	if size<10:
		size=10
	if size>16:
		size=16
	packetSendingQueue.put((packettypenumber("NEWMAP"),size))
	return size
