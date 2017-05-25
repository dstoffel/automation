# -*- coding: utf-8 -*-
import os,sys, time, re, urlparse,traceback,pprint,random,json, BaseHTTPServer
import requests
requests.packages.urllib3.disable_warnings()
import config

class automation(object):
	def __init__(self, plugins=[]):
		self.debuglevel = config.debug
		self.classname = self.__class__.__name__
		self.logprefix = self.classname
#		self.logfile = open(config.logfile, 'a')
		self.rules = []
		self.contexts = {}
		self.decorator = []

	def debug(self,m):
		if self.debuglevel: self.log(m)
	 
	def log(self, m):
		if self.logprefix == '':
			logline = '%s | %s' %  (time.asctime(), m)
		else:
			logline = '%s | %s | %s' %  (time.asctime(), self.logprefix, m)
			
#		self.logfile.write(logline+"\n")
#		self.logfile.flush()
		print logline
		sys.stdout.flush()

	def strip_accents(self, string):
		za = ['é', 'è', 'ê', 'à', 'ù', 'û', 'ç', 'ô', 'î', 'ï', 'â']
		wa=  ['e', 'e', 'e', 'a', 'u', 'u', 'c', 'o', 'i', 'i', 'a']
		for i in xrange(len(za)):
			string = string.replace(za[i], wa[i])
		return string

		print logline

	def create_context(self, rule, data):
		global contexts
		cid = self.get_context_id()
		self.debug('Registering context %s' % cid)
		self.contexts[cid] = {
			'rules' : rule['childs'],
			'data' : data,
			'keepcontext' : rule['keepcontext'],
			'parentout' : rule['out'],
			'escapecontext': rule['escapecontext'],
			'escapeout' : rule['escapeout'],
			'rdata' : rule['rdata'],
		}
		return cid

	def delete_context(self, cid):
		self.debug('Deleting context %s' % cid)
		if cid in self.contexts:
			del self.contexts[cid]

	def get_context_id(self):
		i = int(random.randint(1,999))
		if i in self.contexts:
			return self.get_context_id()
		return i

	def register_rule(self, rule): 
		if rule != False:
			self.rules.append(rule)

	@classmethod
	def Rule(	self,
			id=None,
			pattern=None,
			out=None,
			waitchild=False,
			childs=[],
			keepcontext = True,
			escapecontext=False,
			escapeout='',
			rdata=None,
			execonwait=False,
			decorator=None,
			ichild = None
		):
		"""
		Create a rule object
		@Params:
			id : capture the global output of the pattern if saved it into data returned to the callback with the givne id	
			out : output to send to the callback or to the client if child exists. will be formated. (:__ID__:) or (x) replaced
			waitchild: the rule will not try to match childs rules. out will be returned with the same rule as out() and a new context will be returned
			keepcontext : if True and a context is defined, it will stay in this context if any childs match the input unless a escapecontext is defined
			escapecontext : pattern to match to execute and detroy a context. generic pattern coming from the configuration
			escapeout: output to return if the escapecontext pattern match
			rdata : arbitrary data returned to the callback
			execonwait: callback will be executed
			decorator: decorator to used between parent pattern and child pattern. Eg Turnon the light of. deco : the, of
			ichild = implicit child rule to add if childs is empty, execonwait is turn on
		"""
		rule = {}
		if id != None : rule['id'] = id
		rule['pattern'] = pattern
		rule['out'] = out
		if len(childs) != 0 and ichild != None:
			i = 0
			for c in childs:
				if len(c['childs']) == 0:
					print 'add implicit child to ' + str(childs[i])
					childs[i]['childs'] = [ichild]
					childs[i]['execonwait'] = True
				i = i+1
		print "================="
		print childs
		print "==============="
		rule['childs'] = childs
		rule['waitchild'] = waitchild
		rule['keepcontext'] = keepcontext
		rule['escapecontext'] = escapecontext
		rule['escapeout'] = escapeout
		rule['rdata'] = rdata
		rule['execonwait'] = execonwait
		if decorator==None:
			decorator=['du','le','la','les','de la']
		if len(decorator) != 0:
			prefix = '(?:'+'|'.join(decorator)+')*\s*'
		else:
			prefix = ''
		if id != None :
			pattern_id_b = '(?P<%s>' % id
			pattern_id_e = ')'
		else:
			pattern_id_b = ''
			pattern_id_e = ''
		if waitchild:
			cc = ''
		else:
			if len(childs) != 0:
				cc = '(?P<sub>.*)'
			else:
				cc = ''
		rule['regex'] = '^'+prefix+pattern_id_b+pattern+pattern_id_e+cc+'$'
		try:
			rule['p'] = re.compile(rule['regex'], re.IGNORECASE)
		except:
                        traceback.print_exc()
                        return False

		if len(childs) != 0 and keepcontext:
			if escapecontext == False:
				escapecontext = '(abandonne|oublie|tais toi|tg|ta gueule|arrete)'
				rule['escapeout'] = 'jarrete'
			try: 
				p = re.compile(escapecontext, re.IGNORECASE)
				rule['escapecontext'] = p
			except:
				traceback.print_exc()
				return False
		print '--------------------'
		print rule
		print '--------------------'
		return rule

	def format_out(self, data, m):
		out = data['out']
		if type(out) != type(''):
			return out
		for j in re.findall('\(:([\w]+):\)', out):
                        if j in data:
                                out = out.replace('(:%s:)' % j, data[j])
                i = 1
                for g in m.groups():
                        out = out.replace('(%s)' % i, g)
                        i = i+1
		return out

	def match(self, order, rules, data):
		for rule in rules:
			self.debug('matching %s with %s' % (order, rule['regex']))
			data['out'] = rule['out']
			m = rule['p'].match(order)
			if m:
				self.debug('pattern %s MATCHED' % rule['pattern'])
				if 'id' in rule:
					data[rule['id']] = m.group(rule['id'])
				data['out'] = self.format_out(data, m)
				if len(rule['childs']) != 0:
					if rule['waitchild'] == False:
						order = m.group('sub').strip()
						if order == '':
							if rule['execonwait']: 
#								cid = self.create_context(rule, data)
								return (self.callback(data, m, rule['rdata']), None)
							else:
								return (data['out'], self.create_context(rule, data))

						c = self.match(order, rule['childs'], data=data)
						if c != False:
							return c
						else:
							self.debug('__HERE__')
							cid = self.create_context(rule, data)
							if rule['execonwait']: 
								return (self.callback(data, m, rule['rdata']), cid)

							else:
								return (data['out'], cid)
					else:
						if rule['execonwait']: 
							return (self.callback(data, m, rule['rdata']), self.create_context(rule, data))
						else:
							return (data['out'], self.create_context(rule, data))
				else:
					return (self.callback(data,m, rule['rdata']), None)
		return (False,None)


	def execute(self, order, cid=None):
		global rules,contexts
		in_cid=False
		default_out = "pas compris"
		if cid != None:
			if cid in self.contexts:
				in_cid = True
				context = self.contexts[cid]
				rules = context['rules']
				data = context['data']
		if not in_cid:
			rules = self.rules
			data = {}

		out, newcid = self.match(order, rules, data)
		if out != False:
			if in_cid:
				self.delete_context(cid)
			return {'state': True, 'cid' : newcid, 'out': out}
		else:
			if in_cid:
				if context['keepcontext']:
					if context['escapecontext'].match(order):
						self.debug('Escaping context %s' % cid)
						self.delete_context(cid)
						return {'state': False, 'cid' : None, 'out' : context['escapeout']}
					else:	
						self.debug('Keeping context %s' % cid)
						return {'state': False, 'cid' : cid, 'out' : context['parentout']}
				else:
					self.delete_context(cid)
					return {'state': False, 'cid' : None, 'out': default_out}
			else:
				return {'state': False, 'cid' : newcid, 'out': default_out}

