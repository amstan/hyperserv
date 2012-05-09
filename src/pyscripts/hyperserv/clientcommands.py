""" handle '/' type requests from clients and translate them into cubescript"""

import sbserver
from hyperserv.events import eventHandler, triggerServerEvent
from hyperserv.servercommands import ServerError

from hypershade.config import config
from hypershade.cubescript import checkforCS, systemCS, playerCS, CSCommand
from hypershade.usersession import UserSessionManager, PermissionError
from hypershade.userdatabase import userdatabase
from hypershade.usercommands import succeedLogin

@eventHandler("player_setmaster")
def clientSetMaster(caller,text):
	caller=("ingame",caller)
	if UserSessionManager[caller][0]=="notloggedin":
		#TODO: see http://github.com/SirAlex/hyperserv/issues#issue/23
		if(config["serverpublic"]!="1"):
			simpleMasterRequest(caller)
		else:
			playerCS.executeby(caller,"echo PermissionError: You cannot claim master on this server without an account or auth.")
			raise PermissionError("You cannot claim master on this server without an account or auth.")
	else:
		checkforCS(caller,"@master")

@eventHandler("player_setmaster_off")
def clientLoseMaster(caller):
	checkforCS(("ingame",caller),"@relinquish;logout")

@eventHandler("player_request_spectate")
def clientSpectate(caller,who):
	checkforCS(("ingame",caller),"@spectator 1 %s" % who)

@eventHandler("player_request_unspectate")
def clientUnspectate(caller,who):
	checkforCS(("ingame",caller),"@spectator 0 %s" % who)

@eventHandler("player_map_vote")
def clientMapVote(caller,mapname,mode):
	caller=("ingame",caller)
	try:
		playerCS.executeby(caller,"map %s %s" % (mapname,mode))
	except PermissionError:
		triggerServerEvent("vote_map",[caller,mode,mapname])
	

@eventHandler("player_set_mastermode")
def clientMastermode(caller,mastermode):
	checkforCS(("ingame",caller),"@mastermode %s" % mastermode)

@eventHandler('player_auth_succeed')
def clientAuth(caller,name):
	authLogin(("ingame",caller),name)

@eventHandler("player_kick")
def clientKick(caller,who):
	checkforCS(("ingame",caller),"@kick %s" % who)

@eventHandler('player_set_team')
def playerSetTeam(caller,target,team):
	checkforCS(("ingame",caller),"@team %s %s" % (target,team))

@eventHandler('player_switch_team')
def playerSwitchTeam(caller,team):
	playerSetTeam(caller,caller,team)

##
#Auth and simple setmaster
def authLogin(caller,authname):
	user=userdatabase.search("auth name",authname)
	if user is not None:
		succeedLogin(caller,dict(user.items()))
	else:
		if(config["authgainmaster"]=="yes"):
			systemCS.executestring("takemaster") #logout all other tiny masters
			setSimpleMaster(caller)

def simpleMasterRequest(caller):
	#check for other privileged people
	privileged=[(session,user) for session,user in UserSessionManager.items() if session[0]=='ingame' and user[1]!='']
	
	if len(privileged)==0:
		setSimpleMaster(caller)
	else:
		playerCS.executeby(caller,"echo PermissionError: There are masters/admins present.")
		raise PermissionError("There are masters/admins present.")

def setSimpleMaster(caller):
	"""sets the caller a simple master, just like /setmaster 1 does it on a vanilla server"""
	UserSessionManager[caller]=("notloggedin","master")
	playerCS.executeby(caller,"master")

@CSCommand("givemaster","master")
def giveMaster(caller,cn):
        """This command gives master to the cn designated. This will raise an error if the player already has permssions at, or beyond, master."""
	target=("ingame",int(cn))
	if UserSessionManager[target][0]=="notloggedin":
		setSimpleMaster(target)
	else:
		raise ServerError("That player already has %s privileges." % UserSessionManager[target][1])

@CSCommand("public")
def public(caller):
	return config["serverpublic"]
