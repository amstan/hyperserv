from hypershade.cubescript import CSCommand, systemCS, playerCS, escape

from hypershade.usersession import UserSessionManager, PermissionError
from hypershade.userdatabase import userdatabase

from hypershade.util import formatCaller

from lib.cubescript import CSError

import hashlib
def hashPassword(password):
	return hashlib.sha224(password).hexdigest()

@CSCommand("login")
def login(caller,*params):
	"""Allows the caller to login to the server."""
	username=None
	password=None
	
	if UserSessionManager[caller][0]!="notloggedin":
		username=UserSessionManager[caller][0]
		logout(caller)
	
	#extract username and password
	if len(params)==2:
		username=params[0]
		password=params[1]
	elif len(params)==1:
		password=params[0]
	
	#guess username
	if username is None:
		if caller[0]=="irc":
			user=userdatabase.search("irc nick",formatCaller(caller))
		elif caller[0]=="ingame":
			user=userdatabase.search("sauerbraten name",formatCaller(caller))
		else:
			raise ValueError("Could not determine your login name.")
		if user is None:
			raise ValueError("Could not determine your login name. Use \"@login username password\" to specify.")
	else:
		user=userdatabase[username]
	
	#temporarly cache the user instance
	userInterface=user
	user=dict(user.items())
	
	#authenticate with everything's that's available
	if password is None:
		if caller[0]=="irc":
			#call an ident message, TODO
			pass
		#check hostname TODO
	else:
		if hashPassword(password) in userInterface["password"]:
			succeedLogin(caller,user)
			return
	
	raise PermissionError("Denied to login.")

def succeedLogin(caller,user):
	UserSessionManager[caller]=(user["username"],user["privileges"])
	systemCS.executestring('notice "%s"' % escape("%s has logged in from %s as %s" % (formatCaller(caller), caller[0], user["username"])))

@CSCommand("logout","master")
def logout(caller,everything="no"):
	"""This logs the caller out. If everything="everything" then the caller will be logged out in every case of the UserSessionManager."""
	if everything=="everything":
		username=UserSessionManager[caller][0]
		for session in UserSessionManager:
			if UserSessionManager[session][0]==username:
				playerCS.executeby(session,"logout")
	else:
		del UserSessionManager[caller]
		playerCS.executeby(caller,"echo You have logged out.")

@CSCommand("whoami")
def whoami(caller,param=""):
	"""This gives all the information about your conection: where you are and what cn you are. Add "+login" to view that as well. Use this in conjuction with #echo. Ex: #echo (whoami)"""
	if param=="+login":
		return "%s - %s" % (str(caller),str(UserSessionManager[caller]))
	return str(caller)

@CSCommand("listusersessions","admin")
def listusersessions(caller):
	"""Tells all the people that are connected to the server. Use this in conjuction with #echo. Ex: #echo (listusersessions)"""
	return str(UserSessionManager)

##
#User Management
@CSCommand("adduser","admin")
def addUser(caller,username,privileges):
	"""Creates a user with with the desired name and permission level. This can be used in conjuction with #echo. Ex: #echo (user)"""
	userdatabase[username]=privileges

@CSCommand("deluser","admin")
def delUser(caller,username):
	"""Deletes a username from the database."""
	del userdatabase[username]

@CSCommand("user","trusted")
def userKey(caller,key=None,*values):
	"""Allows users to change account details like: "password", "sauerbraten name" and "irc nick".  """
	username=UserSessionManager[caller][0]
	if key=="privileges":
		raise PermissionError("You cannot change your privileges level.")
	return userKeyAdmin(caller,username,key,*values)

@CSCommand("useradmin","admin")
def userKeyAdmin(caller,username=None,key=None,*values):
	"""Allows the administration of user accounts the same as the #user command."""
	#if called with no arguments, list the user/keys
	if key is None:
		if username is None:
			return userdatabase
		else:
			return userdatabase[username]
	if len(values)==0:
		return userdatabase[username][key]
	if values[0]=="delete":
		del userdatabase[username][key]
		return
	
	#change what there is to be changed
	if key=="username":
		raise Exception("Usernames cannot be changed, only created and deleted.")
	if key=="password":
		userdatabase[username][key]=map(hashPassword,values)
	else:
		userdatabase[username][key]=values

@CSCommand("loginother","trusted")
def loginOther(caller,where,who,username=None):
	"""Logs in another player. This does not allow someone to login someone with higher permissions."""
	if where=="ingame":
		who=int(who)
	if username is None:
		username=UserSessionManager[caller][0]
	else:
		UserSessionManager.checkPermissions(caller,"admin")
	aswho=dict(userdatabase[username].items())
	succeedLogin((where,who),aswho)

@CSCommand("takemaster","trusted")
def takeMaster(caller):
	"""Takes master from the person that currently has it."""
	masters=[session for session,user in UserSessionManager.items() if session[0]=='ingame' and user[1]=='master']
	for master in masters:
		playerCS.executeby(master,"relinquish; logout")

@CSCommand("help")
def helpCommand(caller, command="help"):
	"""Gives the various help information about commands in hyperserv."""
	if command in systemCS.helpfunc.keys():
		f = systemCS.helpfunc[command][0]
		permission = systemCS.helpfunc[command][1]
		docstring = f.__doc__.replace('\n', ' ')
		if f.func_defaults:
			nDefault = len(f.func_defaults)
			defaults = zip(f.func_code.co_varnames[1:f.func_code.co_argcount][-nDefault:],f.func_defaults)
			args = f.func_code.co_varnames[1:f.func_code.co_argcount][:-nDefault]
			d = [x[0]+'='+str(x[1]) for x in defaults]
			if args:
								string = command+'('+', '.join(args)+', '+', '.join(d)+') (Permission: '+permission+') '+docstring
						else:
								string = command+'(' + ', '.join(d)+') (Permission: '+permission+') '+docstring
		else:
			args = f.func_code.co_varnames[1:f.func_code.co_argcount]
			string = command+'('+', '.join(args)+') (Permission: '+permission+') '+docstring
		#triggerServerEvent("echo",[caller,string])
				return string
		else:
				raise CSError("No such command \""+command+"\"")
