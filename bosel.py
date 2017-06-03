import requests
import re
from xml.dom.minidom import parse, parseString
from os import system
import time
import automation
import tempfile
import os.path
import json

_a = automation.automation()
_a.logprefix = 'bose'


boses = {'salon' : '192.168.0.27'}

cache_dir  = 'cache_output/'
cache_index = cache_dir + 'cache'
cache = {}

if os.path.isfile(cache_index):
	with open(cache_index,'r') as o:
		cache = json.load(o)

def gen(msg):
	global _a,cache, cache_dir
	_c = 'cache_output/'
	tmpfile = tempfile.mkstemp(dir=cache_dir)
	d = tmpfile[1]+'.wav'
	_a.debug('generating %s in %s' % (msg, d))
#	system('/usr/bin/pico2wave -l fr-FR --wave /tmp/out.wav "%s" && ffmpeg -i /tmp/out.wav -ar 44100 -ac 2 -y %s; rm /tmp/out.wav; rm %s' % (msg, d, tmpfile[1]))
	system('./bing.py "%s" %s; rm %s' % (msg, d, tmpfile[1]))
	cache[msg] = d
	with open(cache_index,'w') as o:
		json.dump(cache, o)

def sendkey(room, key):
	_req(room, 'key', data='<key state="press" sender="Gabbo">%s</key>' % key)
	_req(room, 'key', data='<key state="release" sender="Gabbo">%s</key>' % key)

def play(room, msg):
	global _a,cache
	msg = msg.lower()
	_a.debug('start playing "%s"' % msg)
	previous_pid,  previous_source, previous_volume, previous_state = get_current_status(room)
	volume(room, 75)
	if msg not in cache:
		gen(msg)

	system('cp -f %s /var/tmp/minidlna/Music/in.wav -f' % cache[msg])

	r = _req(room, 'key', data='<key state="press" sender="Gabbo">PRESET_6</key>')
	r = _req(room, 'key', data='<key state="release" sender="Gabbo">PRESET_6</key>')
	wait2finish(room)
	volume(room, previous_volume)
	if previous_source != 'STANDBY' and previous_source != 'INVALID_SOURCE' and 'PLAY' in previous_state:
		_req(room, 'key', data='<key state="press" sender="Gabbo">PRESET_%s</key>' % previous_pid)
		_req(room, 'key', data='<key state="release" sender="Gabbo">PRESET_%s</key>' % previous_pid)
		if not 'PLAY' in previous_state:
			wait4play(room)
			_req(room, 'key', data='<key state="press" sender="Gabbo">STOP</key>')
			_req(room, 'key', data='<key state="release" sender="Gabbo">STOP</key>')
	else:
		if previous_source != 'STANDBY' and previous_source != 'INVALID_SOURCE':
			_req(room, 'key', data='<key state="press" sender="Gabbo">PRESET_%s</key>' % previous_pid)
			_req(room, 'key', data='<key state="release" sender="Gabbo">PRESET_%s</key>' % previous_pid)
			wait4play(room)
			_req(room, 'key', data='<key state="press" sender="Gabbo">STOP</key>')
			_req(room, 'key', data='<key state="release" sender="Gabbo">STOP</key>')

	_a.debug('done')

def _req(room, path, data=None):
	global _a,boses

	url = 'http://%s:8090/%s' % (boses[room], path)
	_a.debug('_req(%s, %s, %s)' % ( room, path, data))
	if data == None:
		response = requests.get(url)
	else:
		response = requests.post(url, data=data)

	if response.status_code != 200:
		_a.debug('error: %s' % response.content)
		return False
	try:
		return parseString(response.content)
	except:
		_a.debug('error during xml conversion')
		return False

def volume(room, volume=None):
	global _a
	if volume != None:
		_a.debug('setting volume to %s' % volume)
		_req(room, 'volume', '<volume>%s</volume>' % volume)
	else:
		e = _req(room, 'volume')
		return e.getElementsByTagName('actualvolume')[0].firstChild.nodeValue


def wait4play(room):
	global _a
	r = _req(room, 'now_playing')
	p = r.getElementsByTagName('playStatus')
	if len(p) != 0 and p[0].firstChild.nodeValue == 'PLAY_STATE':
		_a.debug('playing detected')
		return True
	time.sleep(0.5)
	return wait4play(room)

def wait2finish(room):
	global _a
	r = _req(room, 'now_playing')
	p = r.getElementsByTagName('playStatus')
	c = r.getElementsByTagName('ContentItem')
	if len(p) == 0 and len(c) != 0 and c[0].attributes['source'].value == 'INVALID_SOURCE':  
		_a.debug('terminated')
		return True
	time.sleep(1)
	return wait2finish(room)


presets = _req('salon', 'presets')

def get_current_status(room):
	global _a, presets
	""" return (PRESET_ID,SOURCE,VOLUME,PLAYING_STATE) """
	_a.debug('getting status for room %s' % room)
	nowplay = _req(room, 'now_playing')
	e = nowplay.getElementsByTagName('ContentItem')[0]
	current_source = e.attributes['source'].value
	if current_source == 'STANDBY':
		current_location = ''
		current_state = 'PAUSE_STATE'
		current_preset = 6
	else:
		if e.attributes['source'].value == 'INVALID_SOURCE':
			current_preset = 6
			current_state = 'PAUSE_STATE'
		else:
			current_location = e.attributes['location'].value
			current_state = nowplay.getElementsByTagName('playStatus')[0].firstChild.nodeValue
			current_preset = 6
			for i in presets.getElementsByTagName('preset'):
				ii = i.attributes['id'].value
				if 'location="%s"' % current_location in i.toxml():
					current_preset = ii
	current_volume  = volume(room)
	_a.debug('status, PRESET_ID : %s / SOURCE : %s  / VOLUME : %s / STATE: %s' % (current_preset, current_source, current_volume, current_state))
	return (current_preset, current_source, current_volume, current_state)

