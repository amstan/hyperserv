"""Library to read and write and access config files using cubescript"""

from hypershade.cubescript import systemCS, CSCommand, escape

class CSConfig(dict):
	def order(self,x):
		order=["server","db","irc","master"]
		for i,string in enumerate(order):
			if x.startswith('cfg "'+string):
				return "%3d%s" % (i,x)
		return x
	def __str__(self):
		return "\n".join(sorted(['cfg "%s" "%s"' % (escape(key), escape(value)) for key, value in self.items()],key=self.order))

config=CSConfig()

@CSCommand("writecfg","admin")
def writecfg(caller):
	"""Prints out all of the .cfg files associated with the server."""
	print "//writecfg by %s.\n%s" % (caller, config)

@CSCommand("cfg","admin")
def cfgEntry(caller,key,*values):
	"""Changes a value in the .cfg."""
	if len(values)>0:
		config[key]=' '.join(values)
	return config[key]

@CSCommand("cfgdel","admin")
def delEntry(caller,key):
	"""Deletes a value from the .cfg. """
	return config.pop(key)

systemCS.executestring(open("../../config.cfg","r").read())
print "Configuration loaded."
