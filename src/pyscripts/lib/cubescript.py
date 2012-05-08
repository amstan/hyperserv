#!/usr/bin/env python
import re, random, sys, traceback

class CSError(Exception):
	"""Internal Cubescript Error, syntax usually"""
	pass

class CSFunctionError(Exception):
	"""Exception happened in external function. Only unhandled if using execute directly, see executestring for implementation
		except CSFunctionError as e:
			#reraise the error from the external function
			execinfo=e.args[0]
			raise execinfo[0],execinfo[1],execinfo[2]
	"""
	pass

class CSParser:
	def __init__(self, string):
		self.string=string
		self.quotefinder=re.compile('[^^]"')
	
	def consume(self,length=1):
		self.string=self.string[length:]
	
	def parse(self,expect=""):
		"""Parses a string and outputs an sexp"""
		output=[""]
		while True:
			if self.string.startswith("("):
				self.consume()
				if not isinstance(output[-1], str):
					output.append("")
				output[-1]=self.parse(")")
			elif self.string.startswith(")"):
				if expect==")":
					self.consume()
					break
				elif expect=="begin":
					self.consume()
					if output[-1]!="":
						output.append("")
					output[-1]="begin"
				else:
					raise CSError("Unexpected ): "+self.string)
			
			elif self.string.startswith("["):
				self.consume()
				if not isinstance(output[-1], str):
					output.append("")
				output[-1]=["lambda",""]
				output[-1][1]=self.parse("]")
			elif self.string.startswith("]"):
				if expect=="]":
					self.consume()
				elif expect=="begin":
					self.consume()
					if output[-1]!="":
						output.append("")
					output[-1]="begin"
				else:
					raise CSError("Unexpected ]: "+self.string)
				break
			
			elif self.string.startswith("\""):
				try:
					position=self.quotefinder.search(self.string[1:]).start()+3
					output[-1]=self.string[1:position-1].replace('^"','"')
					self.consume(position)
					output.append("")
				except AttributeError:
					raise CSError("Unfinished \": "+self.string)
			
			elif self.string.startswith(" ") or self.string.startswith("\t"):
				self.consume()
				if output[-1]!="":
					output.append("")
			
			elif self.string.startswith(";") or self.string.startswith("\n"):
				self.consume()
				if output!=[""]:
					if output[-1]=="":
						output=output[:-1]
					output=["begin",output,self.parse("begin")]
					if output[2]==[]:
						output=output[1]
					if output[2][-1]=="begin":
						output[2]=output[2][:-1]
						return output
			
			elif self.string.startswith("//"):
				self.string=self.string.partition("\n")[2]
			
			elif self.string=="":
				break
			else:
				if not isinstance(output[-1], str):
					output.append("")
				output[-1]=output[-1]+self.string[0]
				self.consume()
				
		if output[-1]=="":
			output=output[:-1]
		return output

class CSInterpreter:
		
	def __init__(self,external=None,variables={},helpfunc=None):
		if external is None:
			self.external={}
			self.variables={}
			self.helpfunc={}
		else:
			self.external=external
			self.variables=variables
			self.helpfunc=helpfunc
		
		self.functions = {
			"begin":  self.begin,
			"if":     self.csif,
			"loop":   self.csloop,
			"while":  self.cswhile,
			"+":      lambda params: self.numeric(sum,params),
			"-":      lambda params: self.numeric(lambda a: a[0]-a[1],params),
			"*":      lambda params: self.numeric(lambda a: reduce(lambda x,y: x*y,a),params),
			
			"=":      lambda params: self.numeric(lambda a: a[0]==a[1],params),
			"!=":     lambda params: self.numeric(lambda a: a[0]!=a[1],params),
			"<":      lambda params: self.numeric(lambda a: a[0]<a[1],params),
			">":      lambda params: self.numeric(lambda a: a[0]>a[1],params),
			"<=":     lambda params: self.numeric(lambda a: a[0]<=a[1],params),
			">=":     lambda params: self.numeric(lambda a: a[0]>=a[1],params),
			
			"div":    lambda params: self.numeric(lambda a: a[0]/a[1],params),
			"mod":    lambda params: self.numeric(lambda a: a[0]%a[1],params),
			"min":    lambda params: self.numeric(min,params),
			"max":    lambda params: self.numeric(max,params),
			
			"rnd":    lambda params: self.numeric(lambda a: random.randint(a[0],a[1]),params),
			"strcmp": lambda params: str(cmp(params[0],params[1])),
			"strstr": lambda params: str(params[0].find(params[1])),
			"strlen": lambda params: str(len(params[0])),
			"strstr": lambda params: str(params[0].find(params[1])),
		}
	
	def functionErrorWrapper(self,functionpointer,*params):
		try:
			return functionpointer(self,*params)
		except Exception as e:
			raise CSFunctionError(sys.exc_info())
	
	def assignvar(self,name,value):
		self.variables[name]=value
		return value
	
	def numeric(self,function,params):
		string=str(function(map(int,params)))
		if string=="True":
			string="1"
		if string=="False":
			string="0"
		return string
	
	def force(self,params):
		if type(params) is list:
			if params[0]=="lambda":
				params=params[1]
		return self.execute(params)
	
	def begin(self,params):
		self.execute(params[0])
		return self.execute(params[1])
	
	def csif(self,params):
		if int(params[0]):
			return self.force(params[1])
		else:
			return self.force(params[2])
	
	def csloop(self,params):
		for i in range(0,int(params[1])):
			self.assignvar(params[0],i)
			self.force(params[2])
	
	def cswhile(self,params):
		while(int(self.force(params[0]))):
			self.force(params[1])
	
	def execute(self,sexp):
		"""Executes Cubescript in sexp form, it needs to already be parsed"""
		
		if type(sexp) != list:
			if type(sexp) is str and sexp.startswith("$"): #variable?
				try:
					return str(self.variables[sexp[1:]])
				except KeyError:
					raise CSError("No such variable: "+sexp)
			else: #number/string
				return sexp
		
		if sexp==[]: #nothing to execute?
			return
		
		try: #function
			#value assignment
			if len(sexp)>1 and sexp[1]=="=":
				return self.assignvar(sexp[0],self.execute(sexp[2]))
			
			#lamba non-execution
			if sexp[0]=="lambda":
				return sexp
			
			#proceed to execute
			argumentslist=map(self.execute,sexp[1:])
			if sexp[0] in self.functions:
				return self.functions[sexp[0]](argumentslist)
			else: #must be external
				return self.functionErrorWrapper(self.external[sexp[0]],*argumentslist)
			
		except KeyError:
			raise CSError("No such command \""+sexp[0]+"\"")
		except IndexError:
			raise CSError("Missing parameter for \""+sexp[0]+"\"")
		except TypeError:
			raise CSError("Expected function, found a block: "+str(sexp[0]))
	
	def executestring(self,string):
		"""Parses and Executes Cubescript, also handles errors from external functions"""
		sexp=CSParser(string).parse()
		if len(sexp)>0 and type(sexp[0]) is list:
			sexp=sexp[0]
		
		try:
			return self.execute(sexp)
		except CSFunctionError as e:
			#reraise the error from the external function
			execinfo=e.args[0]
			raise execinfo[0],execinfo[1],execinfo[2]

if __name__ == '__main__':
	import readline,sys
	
	def print_to_stdout(interpreter,*stuff):
		print ' '.join(map(str,stuff))
	
	def cause_error(interpreter,value):
		"""Causes Error when called with a 1 or +"""
		return 1/(int(value)-1)
	
	interpreter=CSInterpreter()
	interpreter.external["echo"]=print_to_stdout
	interpreter.external["exit"]=lambda interpreter: exit()
	interpreter.external["error"]=cause_error
	interpreter.external["pycall"]=lambda interpreter, function, *arguments: eval(function)(*arguments)
	
	interpreter.executestring("echo Cubescript Python Interpreter")
	
	args=' '.join(sys.argv[1:])
	if(args!=""):
		print "cs>",args
		interpreter.executestring(args)
	
	while(1):
		string=raw_input("cs> ")
		interpreter.executestring(string)
