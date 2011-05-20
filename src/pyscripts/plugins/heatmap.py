#!/usr/bin/env python
import sbserver
from hypershade.cubescript import playerCS, CSCommand
from hyperserv.servercommands import ServerError
from hyperserv.position import getPosition
from editing.ents import ent
from hypershade.config import config
from hyperserv.events import eventHandler

flamecolour = {
	"good": 0,
	"evil": 15,
	"neutral": 240,
}

@CSCommand("mark","trusted")
def mark(caller):
	cn=int(caller[1])
	position=map(lambda a: a*16, getPosition(cn))
	entity=(position[0],position[1],position[2]+64,5,0,0,0,flamecolour[sbserver.playerTeam(cn)],0)
	ent(entity)

@eventHandler("player_frag")
def player_frag(killer, victim):
	victimposition=map(lambda a: a*16, getPosition(victim))
	ent((victimposition[0],victimposition[1],victimposition[2]+64,1,32,0,64,127,0))
	attackerposition=map(lambda a: a*16, getPosition(killer))
	ent((attackerposition[0],attackerposition[1],attackerposition[2]+64,1,32,127,0,0,0))