from automation import *
import generic_config as cfg
import subprocess

class generic(automation):
	def __init__(self):
		super(generic, self).__init__()
		for rule in cfg.rules:
			self.register_rule(rule)

	def callback(self, data, m, rdata):
		action = data['out']
		if rdata != None and 'shell' in rdata and rdata['shell']:
			self.log('Executing "%s"' % action)
			p = subprocess.Popen([action], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			(out, err) = p.communicate()
			self.log('STDOUT : "%s" / STDERR : "%s"' %  (out.strip(), err.strip()))
			return out.strip()
		else:
			return data['out']

