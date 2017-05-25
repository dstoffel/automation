from automation import *

def execute(_a, order, cid=None):
        global _plugins
        order = _a.strip_accents(order)
        if cid != None and cid.strip() != '':
                m =  re.match('^(\w+)\-(\d+)$', str(cid))
                if m:
                        plugin =  m.group(1)
                        cid = int(m.group(2))
                        if plugin in _plugins and cid in _plugins[plugin].contexts:
                                _a.debug('Valid context id %s for %s' % ( cid, plugin))
                                result = _plugins[plugin].execute(order, cid)
                                if result['cid'] != None:
                                        result['cid'] = '%s-%s' % (plugin, result['cid'])
                                else:
                                        result['cid'] = ''
                                return result
                        else:
                                e = 'Invalid context id : %s-%s, plugin/context not registered' % (plugin,cid)
				cid = ''
                                _a.debug(e)
                else:
			cid = ''
                        _a.debug('Invalid context id : %s' % cid)

        for plugin in _plugins:
                _a.debug('Trying to match "%s" with plugin %s [%s]' % (order, plugin, cid))
                result = _plugins[plugin].execute(order)
                if result['cid'] != None:
                        result['cid'] = '%s-%s' % (plugin, result['cid'])
                else:
                        result['cid'] = ''
                if result['state']:
                        return result
                else:
                        _a.debug('Plugin %s NOT MATCHED' % plugin)

        return {'state': False, 'out' : "Je n'ai pas compris", 'cid': None}


class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    global _automation, clients
    def do_GET(s):
	client = s.address_string()
        e = urlparse.urlparse(s.path)
        qargs = urlparse.parse_qs(e.query, keep_blank_values=True)
        path  = e.path
        _automation.debug('New resquest received : Path : "%s"  / Args : "%s" ' % (str(path),str(qargs)))
        content_type = 'text/html'
        if path == '/':
                res = 200
                if 'q' in qargs:
                        order = qargs['q'][0]
                        if 'cid' in qargs:
                                result = execute(_automation, urlparse.unquote(order), qargs['cid'][0])
                        else:
				if client in clients:
					_automation.debug('cid from ip')
					result = execute(_automation, urlparse.unquote(order), clients[client])	
				else: 
					result = execute(_automation, urlparse.unquote(order))

                        if 'cid' not in qargs:
				print result
				clients[client] = result['cid']

                        output  = json.dumps(result)
                        content_type = 'application/json'
                        _automation.debug('Returning ouput: %s' % output)
                else:
                        output = open('form.html').read()
        else:
                res, output = 404, ''
        s.send_response(res)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write(output)

if __name__ == '__main__':
        _automation = automation()
        _plugins = {}
        loaded = []
	clients = {}
        for plugin in config.plugins:
                classfile  = 'plugins/%s/%s.py' % (plugin, plugin)
                if not os.path.isfile(classfile):
                        _automation.log('Missing %s; exiting' % classfile)
                        sys.exit(1)
                _automation.log('Trying to load plugin %s' % plugin)
		sys.path.insert(0, 'plugins/%s' % plugin)
                try:
                        module = __import__(plugin)
                        _plugins[plugin] = eval('module.'+plugin+'()')
                        _automation.log('Rules loaded : %s' % len(_plugins[plugin].rules))
                        _automation.debug("Rules : \n%s" % pprint.PrettyPrinter(indent=4).pformat(_plugins[plugin].rules))
                        loaded.append(plugin)
                        _automation.log('Plugin %s loaded' % plugin)
                except Exception, e:
                        _automation.log('Error during Loading %s :' % plugin)
                        _automation.log(traceback.print_exc())
                        pass
	if len(loaded) == 0:
		_automation.log('Need at least one plugin, exiting')
		sys.exit(1)
        _automation.log('Plugins loaded : %s ' % ', '.join(loaded))
        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((config.server_ip, config.server_port), HTTPHandler)
        _automation.log("Server Starts - %s:%s" % (config.server_ip, config.server_port))
        try:
                httpd.serve_forever()
        except KeyboardInterrupt:
                pass
        httpd.server_close()
        _automation.log("Server Stops - %s:%s" % (config.server_ip, config.server_port))

