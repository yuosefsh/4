#!/usr/bin/python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------- #
#                                                                             #
#    Plugin for iSida Jabber Bot                                              #
#    Copyright (C) diSabler <dsy@dsy.name>                                    #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #
# --------------------------------------------------------------------------- #

# [u'devel@conference.jabber.ru', u'sulci', u'moderator', u'admin', u'sulci@jabber.ru/Ocaml']

AI_PREV = {}
AI_PHRASES_FOLDER = data_folder % 'ai/%s'
AI_PHRASES_FILES = [t for t in os.listdir(AI_PHRASES_FOLDER % '') if t.endswith('.txt') and os.path.isfile(AI_PHRASES_FOLDER % t)]
AI_PHRASES = {}

for PH_LANG in AI_PHRASES_FILES:
	PH_L = PH_LANG.split('.',1)[0]
	PHRASES = readfile(AI_PHRASES_FOLDER % PH_LANG).decode('utf-8').replace('\r','').split('\n')
	for LINE in PHRASES:
		if LINE.strip() and not LINE.strip().startswith('#') and '\t' in LINE:
			if not AI_PHRASES.has_key(PH_L): AI_PHRASES[PH_L] = [LINE.split('\t',1)]
			else: AI_PHRASES[PH_L].append(LINE.split('\t',1))

def AI_PARSE(room, jid, nick, type, text):
	if not get_config(room,'ai'): return
	LOC = get_L_('%s/%s' % (room,nick))
	TEXT = ' %s ' % text.lower()
	SCORE, CMD = 1.0, []
	for PHRASES in AI_PHRASES[LOC]:
		CUR_SCORE = AI_RATING(PHRASES[1].split('||')[0], TEXT, room)
		if CUR_SCORE > SCORE: SCORE, CMD = CUR_SCORE, [PHRASES]
		elif CUR_SCORE == SCORE: CMD.append(PHRASES)
	if not CMD: return
	nowname = getResourse(cur_execute_fetchone('select room from conference where room ilike %s',('%s/%%'%room,))[0])
	if nowname == nick: return	
	pprint('AI score %s|%s|%s' % (SCORE, '|'.join([t[0] for t in CMD]), text),'cyan')
	CMD = random.choice(CMD)
	CMD_RAW = CMD[0].split()[0]
	pprint('AI selected %s' % CMD_RAW,'cyan')
	access_mode = get_level(room,nick)[0]
	if cur_execute_fetchone('select * from commonoff where room=%s and cmd=%s',(room,CMD_RAW)): return
	ptype = ''
	for t in comms:
		if t[1] == CMD_RAW:
			ptype = t[-1]
			break
	if 'nick' in ptype and '||' in CMD[1]:
		for t in CMD[1].split('||')[1].split('|'):
			text = text.replace(t,nick)
	PRM = AI_PARAMETER(text, ptype, room)
	
	if 'nick' in ptype:
		PP = None
		for t in PRM:
			if t:
				PP = True
				break
		if not PP: PRM.append(nick)

	COMMAND = CMD[0]
	COMMAND = COMMAND.replace('{TOMORROW}',time.strftime('%d.%m', time.localtime(time.time()+86400)))
	WAS_PARAM = False
	for PARAM in PRM:
		if PARAM:
			if time_nolimit: time.sleep(time_nolimit)
			com_parser(access_mode, nowname, type, room, nick, COMMAND.replace('{PAR}',PARAM), jid)
			WAS_PARAM = True
	if not WAS_PARAM:
		if time_nolimit: time.sleep(time_nolimit)
		com_parser(access_mode, nowname, type, room, nick, COMMAND, jid)
	return True

def AI_RATING(s, text, room):
	r,s = 0.0,s.split('|')
	for k in s:
		if k in text: r += 0.5
		if k in AI_PREV.get(room, ''): r += 0.34
	return r

def AI_PARAMETER(body, type, room):
	P_NICK, P_JID, P_SERVER = [], [], []
	
	if 'nick' in type:
		NICKS = [t[1] for t in megabase if t[0]==room]
		for NICK in NICKS:
			if NICK in body:
				P_NICK.append(NICK)
				break

	if 'jid' in type:
		JID = re.findall(u'[-a-z0-9а-яё_]+@[-0-9a-z\.]+',body,re.S|re.I|re.U)
		if JID: P_JID += JID

	if 'server' in type:
		SERVER = re.findall(u'[-0-9a-zа-яё\.]+\.[-a-zа-я]{2,}',body,re.S|re.I|re.U)
		if SERVER: P_SERVER += SERVER

	RESULT = []
	for t in P_NICK + P_JID + P_SERVER:
		if t not in RESULT: RESULT.append(t)
		
	return RESULT

gmessage.append(AI_PARSE)