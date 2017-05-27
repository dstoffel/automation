from automation import *

#TODO: heritage rdata 

Rule = automation.Rule
rules = [
	Rule(pattern='quel.*heure.*', out='echo il est $(date +"%H heure %M")', rdata={'shell':True}),
	Rule(pattern='quel.*date.*', out='echo nous sommes le $(date +"%d du %m %Y")', rdata={'shell':True}),
	Rule(pattern='merci',out='de rien'),
	Rule(pattern='repeat (.*)', out='echo (1)', rdata={'shell' : True}),
        Rule(pattern='bla', out='?', keepcontext=True,execonwait=True, waitchild=True, childs=[ Rule(pattern='oui', out='oui'), Rule(pattern='non', out='non')]),
        Rule(pattern='qsd', out='?', keepcontext=False, childs=[ Rule(pattern='oui', out='oui'), Rule(pattern='non', out='non')]),
#	Rule(pattern='envoi un mail a (.*) sujet (.*) contenu (.*)',  out='echo "(3)" | mail -s "(2)" "(1)" && echo "c\'est parti"', rdata={'shell' : True}),
	Rule(pattern='envoie? un mail', out='a qui?', childs=[
		Rule(id="to", pattern='[a-zA-Z0-9\._-]+@[a-zA-Z0-9\._-]+', decorator=['a'], out='subjet?', childs=[
			Rule(id="subject", pattern='.*', out='contenu?', waitchild=True, childs=[
				Rule(id="content", confirm=True, confirmout='confirm, envoyer mail a (:to:)?',pattern='.*', out='echo "(:content:)" | mail -s "(:subject:)" (:to:) && echo "c\'est parti"', rdata={'shell' : True})
			])
		])
	])
]
