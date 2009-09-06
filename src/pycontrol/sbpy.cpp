/*
 *   Copyright (C) 2009 Gregory Haynes <greg@greghaynes.net>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include "sbpy.h"

#include <string>
#include <iostream>

extern int totalmillis;

namespace SbPy
{

static char *pyscripts_path;

PyMODINIT_FUNC initModule(const char *);

void loadPyscriptsPath()
{
	char *path = getenv("SB_PYSCRIPTS_PATH");
	if(!path)
		pyscripts_path = path;
}

void initEnv()
{
	char *pythonpath, *newpath;
	if(!pyscripts_path)
		return;
       	pythonpath = getenv("PYTHONPATH");
	if(!pythonpath)
	{
		newpath = new char[strlen(pyscripts_path)+1];
		strcpy(newpath, pyscripts_path);
	}
	else
	{
		newpath = new char[strlen(pyscripts_path)+strlen(pythonpath)+2];
		strcpy(newpath, pythonpath);
		strcat(newpath, ":");
		strcat(newpath, pyscripts_path);
	}
	setenv("PYTHONPATH", newpath, 1);
	delete newpath;
}

#define SBPY_ERR(x) \
	if(!x) \
	{ \
		if(PyErr_Occurred()) \
			PyErr_Print(); \
		return false;\
	}

static PyObject *eventsModule, *triggerEventFunc, *triggerPolicyEventFunc, *triggerExecQueueFunc, *triggerSocketMonitorFunc, *setTimeFunc;

bool initPy()
{
	PyObject *pFunc, *pArgs, *pValue, *pluginsModule;
	
	pluginsModule = PyImport_ImportModule("sbplugins");
	SBPY_ERR(pluginsModule)
	eventsModule = PyImport_ImportModule("sbevents");
	SBPY_ERR(eventsModule)
	pFunc = PyObject_GetAttrString(pluginsModule, "loadPlugins");
	SBPY_ERR(pFunc)
	if(!PyCallable_Check(pFunc))
	{
		fprintf(stderr, "Error: loadPlugins function could not be loaded.\n");
		return false;
	}
	pArgs = PyTuple_New(0);
	pValue = PyObject_CallObject(pFunc, pArgs);
	Py_DECREF(pArgs);
	Py_DECREF(pFunc);
	if(!pValue)
	{
		PyErr_Print();
		return false;
	}
	Py_DECREF(pValue);
	triggerEventFunc = PyObject_GetAttrString(eventsModule, "triggerEvent");
	SBPY_ERR(triggerEventFunc);
	if(!PyCallable_Check(triggerEventFunc))
	{
		fprintf(stderr, "Error: triggerEvent function could not be loaded.\n");
		return false;
	}
	triggerPolicyEventFunc = PyObject_GetAttrString(eventsModule, "triggerPolicyEvent");
	SBPY_ERR(triggerPolicyEventFunc);
	if(!PyCallable_Check(triggerPolicyEventFunc))
	{
		fprintf(stderr, "Error: triggerPolicyEvent function could not be loaded.\n");
		return false;
	}
	triggerExecQueueFunc = PyObject_GetAttrString(eventsModule, "triggerSbExecQueue");
	SBPY_ERR(triggerExecQueueFunc);
	if(!PyCallable_Check(triggerExecQueueFunc))
	{
		fprintf(stderr, "Error: triggerSbExecQueue function could not be loaded.\n");
		return false;
	}
	triggerSocketMonitorFunc = PyObject_GetAttrString(eventsModule, "triggerSocketMonitor");
	SBPY_ERR(triggerSocketMonitorFunc);
	if(!PyCallable_Check(triggerSocketMonitorFunc))
	{
		fprintf(stderr, "Error: triggerSocketMonitor function could not be loaded.\n");
		return false;
	}
	setTimeFunc = PyObject_GetAttrString(eventsModule, "setTime");
	SBPY_ERR(setTimeFunc);
	if(!PyCallable_Check(setTimeFunc))
	{
		fprintf(stderr, "Error: setTime function could not be loaded.\n");
		return false;
	}
	Py_DECREF(pluginsModule);
	setTime(totalmillis);
	return true;
}

void deinitPy()
{
	Py_Finalize();
}

bool init(const char *prog_name, const char *arg_pyscripts_path, const char *module_name)
{
	// Setup env vars and chdir
	char *pn = new char[strlen(prog_name)+1];
	if(arg_pyscripts_path[0])
	{
		pyscripts_path = new char[strlen(arg_pyscripts_path)+1];
		strcpy(pyscripts_path, arg_pyscripts_path);
	}
	else loadPyscriptsPath();
	if(!pyscripts_path)
	{
		fprintf(stderr, "Fatal Error: Could not locate a pyscripts directory.\n");
		return false;
	}
	initEnv();
	if(-1 == chdir(pyscripts_path))
	{
		perror("Could not chdir into pyscripts path.\n");
		return false;
	}

	// Set program name
	strcpy(pn, prog_name);
	Py_SetProgramName(pn);
	delete pn;

	// Initialize
	Py_Initialize();
	initModule(module_name);
	if(!initPy())
	{
		fprintf(stderr, "Error initializing python modules.\n");
		return false;
	}
	return true;
}

PyObject *callPyFunc(PyObject *func, PyObject *args)
{
	PyObject *val;
	val = PyObject_CallObject(func, args);
	Py_DECREF(args);
	if(!val)
		PyErr_Print();
	return val;
}

bool triggerFuncEvent(const char *name, std::vector<PyObject*> *args, PyObject *func)
{
	PyObject *pArgs, *pArgsArgs, *pName, *pValue;
	std::vector<PyObject*>::const_iterator itr;
	int i = 0;
	
	if(!func)
	{
		fprintf(stderr, "Python Error: Invalid handler to triggerEvent function.\n");
		return false;
	}
	pArgs = PyTuple_New(2);
	pName = PyString_FromString(name);
	SBPY_ERR(pName)
	PyTuple_SetItem(pArgs, 0, pName);
	if(args)
	{
		pArgsArgs = PyTuple_New(args->size());
		for(itr = args->begin(); itr != args->end(); itr++)
		{
			PyTuple_SetItem(pArgsArgs, i, *itr);
			i++;
		}
	}
	else
		pArgsArgs = PyTuple_New(0);
	PyTuple_SetItem(pArgs, 1, pArgsArgs);
	pValue = callPyFunc(func, pArgs);
	if(!pValue)
	{
		fprintf(stderr, "Error triggering event.\n");
		return false;
	}
	if(PyBool_Check(pValue))
	{
		bool ret = (pValue == Py_True);
		Py_DECREF(pValue);
		return ret;
	}
	Py_DECREF(pValue);
	return true;
}

#undef SBPY_ERR

bool triggerFuncEventInt(const char *name, int cn, PyObject *func)
{
	std::vector<PyObject*> args;
	PyObject *pCn = PyInt_FromLong(cn);
	args.push_back(pCn);
	return triggerFuncEvent(name, &args, func);
}

bool triggerFuncEventIntString(const char *name, int cn, const char *text, PyObject *func)
{
	std::vector<PyObject*> args;
	PyObject *pText = PyString_FromString(text);
	PyObject *pCn = PyInt_FromLong(cn);
	args.push_back(pCn);
	args.push_back(pText);
	return triggerFuncEvent(name, &args, func);
}

bool triggerEvent(const char*name, std::vector<PyObject*>* args)
{
	return triggerFuncEvent(name, args, triggerEventFunc);
}

bool triggerEventInt(const char *name, int cn)
{
	return triggerFuncEventInt(name, cn, triggerEventFunc);
}

bool triggerEventIntString(const char *name, int cn, const char *text)
{
	return triggerFuncEventIntString(name, cn, text, triggerEventFunc);
}

bool triggerEventIntInt(const char *name, int cn1, int cn2)
{
	std::vector<PyObject*> args;
	PyObject *pCn1 = PyInt_FromLong(cn1);
	PyObject *pCn2 = PyInt_FromLong(cn2);
	args.push_back(pCn1);
	args.push_back(pCn2);
	return triggerFuncEvent(name, &args, triggerEventFunc);
}

bool triggerEventStrInt(const char *name, const char *str, int n)
{
	std::vector<PyObject*> args;
	PyObject *pstr, *pn;
	pstr = PyString_FromString(str);
	pn = PyInt_FromLong(n);
	args.push_back(pstr);
	args.push_back(pn);
	return triggerFuncEvent(name, &args, triggerEventFunc);
}

bool triggerPolicyEventInt(const char *name, int cn)
{
	return triggerFuncEventInt(name, cn, triggerPolicyEventFunc);
}

bool triggerPolicyEventIntString(const char *name, int cn, const char *text)
{
	return triggerFuncEventIntString(name, cn, text, triggerPolicyEventFunc);
}

void triggerExecQueue()
{
	PyObject *pargs, *pvalue;
	pargs = PyTuple_New(0);
	pvalue = callPyFunc(triggerExecQueueFunc, pargs);
	if(pvalue)
		Py_DECREF(pvalue);
}

void triggerSocketMonitor()
{
	PyObject *pargs, *pvalue;
	pargs = PyTuple_New(0);
	pvalue = callPyFunc(triggerSocketMonitorFunc, pargs);
	if(pvalue)
		Py_DECREF(pvalue);
}

void setTime(int millis)
{
	PyObject *pargs, *pvalue, *pint;
	pint = PyInt_FromLong(millis);
	pargs = PyTuple_New(1);
	PyTuple_SetItem(pargs, 0, pint);
	pvalue = callPyFunc(setTimeFunc, pargs);
	if(pvalue)
		Py_DECREF(pvalue);
}

}
