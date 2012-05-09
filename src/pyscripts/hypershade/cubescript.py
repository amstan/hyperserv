import sys
import traceback
import threading

from lib.cubescript import CSParser, CSInterpreter, CSError

from hypershade.usersession import UserSessionManager, PermissionError

class CSInterpreterOwner(CSInterpreter):
	def executeby(self,owner,string):
		previousowner=self.owner
		self.owner=owner
		try:
			return self.executestring(string)
		finally:
			self.owner=previousowner

systemCS=CSInterpreterOwner()
systemCS.owner=("system","")

playerCS=CSInterpreterOwner(systemCS.external,systemCS.variables)
playerCS.owner=("nobody","") #have this for security, functions from playerCS should never be called as nobody

class CSCommand(object):
	def wrapper(self,f,*args):
		owner=args[0].owner
		UserSessionManager.checkPermissions(owner,self.permissionRequirement)
		return f(owner,*args[1:])
	
	def __init__(self, name, permissionRequirement="none"):
		self.name=name
		self.permissionRequirement=permissionRequirement
	
	def __call__(self,f):
		functionpointer=lambda *args: self.wrapper(f,*args)
		systemCS.external[self.name]=functionpointer
		return f

def checkUntrustedCode(code):
	if type(code) is not list:
		return
	if code[0] in ["while","loop","alias","lambda"]:
		raise PermissionError("You're not allowed to use such complex code.")
	if len(code)>1 and code[1]=="=":
		raise PermissionError("You're not allowed to use such complex code.")
	for arg in code[1:]:
		checkUntrustedCode(arg)

def checkforCS(caller,string):
	if string[0] in ['#','@']:
		cspresent=1
		string=string[1:]
		try:
			try:
				UserSessionManager.checkPermissions(caller,"trusted")
			except PermissionError:
				checkUntrustedCode(CSParser(string).parse())
			playerCS.executeby(caller,string)
		except:
			exctype,exctext,exctraceback=sys.exc_info()
			errormsg="%s: %s" % (exctype.__name__, exctext)
			playerCS.executeby(caller,"echo \"%s\"" % escape(errormsg))
			traceback.print_exc()
		finally:
			return 1
	else:
		return 0

def escape(string):
	return string.replace('"','^"')

def threaded(function):
	def threadwrapper(caller,*args):
		try:
			function(caller,*args)
		except:
			exctype,exctext,exctraceback=sys.exc_info()
			errormsg="%s: %s" % (exctype.__name__, exctext)
			playerCS.executeby(caller,"echo \"%s\"" % escape(errormsg))
			traceback.print_exc()
	
	def wrapper(*args):
		thread=threading.Thread()
		thread.run=lambda:threadwrapper(*args)
		thread.start()
	
	return wrapper