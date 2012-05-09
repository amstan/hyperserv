"""This file contains all the basic commands that the server needs to be playable, this does not handle '/' type requests from clients only server-side cubescript commands"""

import sbserver

import os
from datetime import timedelta, datetime

from hyperserv.events import eventHandler, triggerServerEvent

from hypershade.config import config
from hypershade.cubescript import systemCS, CSCommand
from hypershade.usersession import UserSessionManager, PermissionError
from hypershade.util import ipLongToString, modeNumber, mastermodeNumber, formatCaller
from hypershade.files import openfile

from hypershade.bandatabase import bandatabase

class ServerError(Exception): pass

@CSCommand("vote")
def voteMap(caller,name,mode=None):
        """This command works just like the #map command except rather than directly going to a map it places a vote for the map of choice. Just like with #map, the caller can also call maps from /storage/maps. This calls the map from the server removing the need to /sendmap (as long as the maps are the same version)."""
	if mode is None:
		mode=sbserver.gameMode()
	triggerServerEvent("vote_map",[caller,modeNumber(mode),name])

@CSCommand("map","master")
def changeMap(caller,name,mode=None):
        """This command works just like the /map command except for with #map the caller can also call maps from /storage/maps. This calls the map from the server removing the need to /sendmap (as long as the maps are the same version). """
	if mode is None:
		mode=sbserver.gameMode()
	mode=modeNumber(mode)

	sbserver.setMap(name,mode)

	#load the map if it exists and mode is coop
	if modeNumber("coop")==mode:
		try:
			loadmap(caller,name)
		except:
			pass
	
	return name

@CSCommand("master","master")
def setMaster(caller):
        """This command makes the caller the master of the server. This is denoted by the green color of the callers name. Also like with #admin it does not give the caller any powers beyond what the caller had before."""
	if(caller[0]=="ingame"):
		return sbserver.setMaster(caller[1])
	raise ServerError("You are not ingame.")
	return

@CSCommand("admin","admin")
def setAdmin(caller):
        """Makes the caller the admin of the server. This is denoted by the gold color of their name. Note that this is just for show because it does not give the user any more powers."""
	if(caller[0]=="ingame"):
		return sbserver.setAdmin(caller[1])
	raise ServerError("You are not ingame.")
	return

@CSCommand("relinquish")
def relinquish(caller):
        """This command gives up the level of power that the player has (master or admin)."""
	if(caller[0]=="ingame"):
		return sbserver.resetPrivilege(caller[1])
	raise ServerError("You are not ingame.")
	return

@CSCommand("kick","master")
def kick(caller,cn):
        """This allows the caller to kick another player; however, this will not override players with higher permission. Meaning, a master level permission can not kick someone with admin or trusted permission. To prevent the player from rejoining the server, they will also be banned for the default 60 minutes."""
	cn=int(cn)
	try:
		UserSessionManager.checkPermissions(caller,UserSessionManager[("ingame",cn)][1]) #check if the other person is more privileged
	except PermissionError:
		triggerServerEvent("player_kick_failed",[caller,cn])
		raise
	
	ban(caller,sbserver.playerName(cn),"kicked by %s" % formatCaller(caller))
	triggerServerEvent("player_kicked",[caller,cn])
	return sbserver.playerKick(cn)

@CSCommand("sendto","master")
def sendto(caller,cn):
        """This command forces the specified player to /getmap. This is useful when a player is not paying attention, AFK or, for extension, if the caller wanted everyone to getmap."""
	cn=int(cn)
	return sbserver.sendMapTo(cn)

@CSCommand("spectator")
def spectator(caller,boolean=None,cn=None):
        """If there are no arguments other than #spectator then the caller will be set to spectator. The first argument is a boolen that says what state of spectating the player will be (0 for not not a spectator and 1 for spectator), anything other than 0 will result in an them being a spectator. The cn is the client number of the player that the caller want spectated. If left off it will apply to the caller."""
	#empty args
	if boolean is None:
		boolean=1
	boolean=int(boolean)
	
	if cn is None:
		if(caller[0]=="ingame"):
			cn=caller[1]
		else:
			raise ServerError("You are not ingame. Please specify cn.")
	cn=int(cn)
	
	#check if it's a self call
	if caller[1]==cn:
		if boolean==0 and sbserver.masterMode()>=2:
			UserSessionManager.checkPermissions(caller,"master")
		spectatorHelpler(boolean,cn)
	else:
		UserSessionManager.checkPermissions(caller,"master")
		spectatorHelpler(boolean,cn)

def spectatorHelpler(boolean,cn):
	if boolean:
		sbserver.spectate(cn)
	else:
		sbserver.unspectate(cn)

@CSCommand("editmute","master")
def editmute(caller,boolean=None,cn=None):
        """If there are no arguments other than #editmute then the caller will be editmuted. The first argument is a boolen that says what state of editmuted the player will be (0 for not editmuted and 1 for editmuted), anything other than 0 will result in an editmute. The cn is the client number of the player that the caller want editmuted. If left off it will apply to the caller."""
	#empty args
	if boolean is None:
		boolean=1
	
	if cn is None:
		if(caller[0]=="ingame"):
			cn=caller[1]
		else:
			raise ServerError("You are not ingame. Please specify cn.")
	cn=int(cn)
	boolean=int(boolean)
	
	if boolean:
		spectator(caller,0,cn)
		sbserver.editMute(cn)
		triggerServerEvent("player_editmuted",[cn])
	else:
		sbserver.editUnmute(cn)
		triggerServerEvent("player_editunmuted",[cn])

@CSCommand("mastermode","master")
def masterMode(caller,name=None):
        """This changes the mastermode in the same way that /mastermode does without the need to have claimed master or admin."""
	if name==None:
		return sbserver.masterMode()
	mastermode=mastermodeNumber(name)
	
	if config["serverpublic"]=="1":
		if mastermode>=2:
			UserSessionManager.checkPermissions(caller,"trusted")
	if config["serverpublic"]=="2":
		if mastermode>=3:
			UserSessionManager.checkPermissions(caller,"trusted")
	
	return sbserver.setMasterMode(mastermode)

@CSCommand("who")
def who(caller,where="ingame"):
        """This gives info on all the people logged in to the server. It tells their name, client number and IP address. Use this in conjuction with #echo. Ex: #echo (who)"""
	def cndetails(cn):
		return sbserver.playerName(cn)+" (cn"+str(cn)+"/"+ipLongToString(sbserver.playerIpLong(cn))+")"
	
	clientlist=[session[1] for session in UserSessionManager.keys() if session[0] == where]
	
	if where=="ingame":
		clientlist='; '.join(map(cndetails,clientlist))
	
	if clientlist!="" or clientlist!=[]:
		return str(clientlist)
	else:
		return "No clients for %s." % where

@CSCommand("list")
def listCommands(caller,which="hyperserv"):
	"""List all commands available. Use this in conjuction with #echo. Ex: #echo (list)"""
	if which=="all":
		commands=systemCS.functions.keys()+systemCS.external.keys()
	elif which=="cubescript":
		commands=systemCS.functions.keys()
	else:
		commands=systemCS.external.keys()
	commands.sort()
	return ' '.join(commands)

@CSCommand("say","admin")
def say(caller,*what):
        """This commad says string to the server, simialar to #notice, just without the Notice from PlayerName: MESSAGE HERE"""
	string=' '.join(map(str,what))
	triggerServerEvent("say",[string])
	return string

@CSCommand("echo")
def echo(caller,*what):
        """This is how the caller can read the output from some commands. Examples: listusersessions, list, user, who, whoami. Note that the command must be in parentheses. #echo (command)"""
	string=' '.join(map(str,what))
	triggerServerEvent("echo",[caller,string])
	return string

@CSCommand("ban","trusted")
def ban(caller,who=None,reason="",time="60"):
        """This bans the person specified. If there is not a name given then the caller will be banned. If time is "perm","permanent","permanently","0" or 0 then the ban will be permanent. The default ban time is 60 minutes."""
	if who is None:
		bans(caller)
	
	try:
		who=sbserver.playerName(int(who))
	except ValueError:
		pass
	
	if time[-1]=="d":
		time=int(time[:1])*1440
	
	if time in ["perm","permanent","permanently","0",0]:
		expires=None
	else:
		expires=datetime.utcnow()+timedelta(0,int(time)*60)
	
	bandatabase[who]=(expires,reason)

@CSCommand("bans","master")
def bans(caller):
        """This returns all of the current bans in effect. Use this in conjuction with #echo. Ex: #echo (bans)"""
	return bandatabase

@CSCommand("delban","trusted")
def delban(caller,who):
        """This deletes a username from the database."""
	del bandatabase[who]

@CSCommand("minsleft")
def minsleft(caller,time=None):
        """This sets the amount of time remianing on the map. This can only be used when the mapmode is not Coopedit"""
	if time is not None:
		UserSessionManager.checkPermissions(caller,"trusted")
		sbserver.setMinsRemaining(int(time))
	return sbserver.minutesRemaining()/60 #todo, fix the api, it shouldn't return seconds...

@CSCommand("team")
def team(caller,*args):
        """This allows players to switch teams just like with /team."""
	if(len(args)==1):
		if(caller[0]=="ingame"):
			cn=caller[1]
		else:
			raise ServerError("You are not ingame. Please specify cn.")
	elif(len(args)==2):
		cn=args[0]
	else:
		raise TypeError("team takes either 1 or 2 arguments.")
	cn=int(cn)
	
	teamname=args[-1]
	
	if cn!=caller[1]:
		UserSessionManager.checkPermissions(caller,"master")
		
	sbserver.setTeam(cn,teamname)
	sbserver.suicide(cn)

@CSCommand("mute","master")
def mute(caller,*args):
        """If there are no arguments other than #mute then the caller will be muted. The first argument is a boolen that says what state of muted the player will be (0 for not muted and 1 for muted), anything other than 0 will result in an mute. The cn is the client number of the player that caller want muted. If left off it will apply to the caller."""
	if(len(args)==1):
		boolean=1
		cn=args[0]
	elif(len(args)==2):
		boolean=args[0]
		cn=args[1]
	else:
		raise TypeError("mute takes either 1 or 2 arguments.")
	boolean=int(boolean)
	cn=int(cn)
	
	triggerServerEvent("player_muted",[caller,boolean,cn])

@CSCommand("savemap","trusted")
def savemap(caller,name=None):
        """This allows players to savemaps to the server. This not only allows for easier transfer of files later on, but also allows for partial asynchronous work on a map by saving the map back to the server."""
	if name is None:
		name=sbserver.mapName()
	ogzfilename,ogz=openfile(os.path.join("maps",name+".ogz"),"wb")
	
	mapdata=sbserver.getMapDataFile()
	mapdata.seek(0)
	ogz.write(mapdata.read())
	ogz.close()
	
	triggerServerEvent("savemap",[caller,name,ogzfilename])

@CSCommand("loadmap","master")
def loadmap(caller,name=None):
        """This is the opposite of #savemap. This is automatically executed when you change to a map that the server has in storage."""
	if name is None:
		name=sbserver.mapName()
	
	ogzfilename,ogz=openfile(os.path.join("maps",name+".ogz"),"rb")
	
	mapdata=sbserver.getMapDataFile()
	mapdata.seek(0)
	mapdata.truncate(0)
	mapdata.write(ogz.read())
	mapdata.flush()
	ogz.close()
	
	triggerServerEvent("loadmap",[caller,name,ogzfilename])
