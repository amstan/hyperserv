"""This file contains all the even handlers for notices"""
import sbserver
from hyperserv.events import eventHandler, triggerServerEvent
from hyperserv.util import modeName, mastermodeName

def serverNotice(string):
	triggerServerEvent("notice",[string])

@eventHandler('player_connect')
def noticePlayerConnect(cn):
	serverNotice("Connected: "+sbserver.playerName(cn)+"("+str(cn)+")")

@eventHandler('player_disconnect')
def noticePlayerDisconnect(cn):
	serverNotice("Disconnected: "+sbserver.playerName(cn)+"("+str(cn)+")")

@eventHandler('map_changed')
def noticeMapChanged(name,mode):
	serverNotice("Map: "+name+" ("+modeName(mode)+")")

@eventHandler('intermission_begin')
def noticeIntermissionBegin():
	serverNotice("Intermission.")