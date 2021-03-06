#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging; logging.basicConfig(level = logging.INFO)
import asyncio, os, json, time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
import orm
from coroweb import add_routes, add_static

def index(request):
	return web.Response(body = b'<h1>Practice</h1>')
	
def datetime_filter(t):
	delta = int(time.time() - t)
	if delta < 60:
		return u'1分钟前'
	elif delta < 3600:
		return u'%s分钟前' % (delta // 60)
	elif delta < 86400:
		return u'%s小时前' % (delta // 3600)
	elif delta < 604800:
		return u'%s天前' % (delta // 86400)
	dt = datetime.fromtimestamp(t)
	return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

def init_jinja2(app, **kw):
	logging.info('init jinja2...')
	options = dict(
		autoescape = kw.get('autoescape', True),
		block_start_string = kw.get('block_start_string', '{%'),
		block_end_string = kw.get('block_end_string', '%}'),
		variable_start_string = kw.get('variable_start_string', '{{'),
		variable_end_string = kw.get('variable_end_string', '}}'),
		auto_reload = kw.get('auto_reload', True)
	)
	path = kw.get('path', None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
	logging.info('set jinja2 template path: %s' % path)
	env = Environment(loader = FileSystemLoader(path), **options)
	filters = kw.get('filters', None)
	if filters is not None:
		for name, f in filters.items():
			env.filters[name] = f
	app['__templating__'] = env

@asyncio.coroutine
def logger_factory(app, handler):
	@asyncio.coroutine
	def logger(request):
		logging.info('Request: %s %s' % (request.method, request.path))
		return (yield from handler(request))
	return logger
	
@asyncio.coroutine
def data_factory(app, handler):
	@asyncio.coroutine
	def parse_data(request):
		if request.method == 'POST':
			if request.content_type.startswith('application/json'):
				request.__data__ = yield from request.json()
				logging.info('request json: %s' % str(request.__data__))
			elif request.content_type.startswith('application/x-www-form-urlencoded'):
				request.__data__ = yield from request.post()
				logging.info('request form: %s' % str(request.__data__))
		return (yield from handler(request))
	return parse_data

@asyncio.coroutine
def response_factory(app, handler):
	@asyncio.coroutine
	def response(request):
		logging.info('Response handler...')
		r = yield from handler(request)
		if isinstance(r, web.StreamResponse):
			return r
		elif isinstance(r, bytes):
			res = web.Response(body = r)
			res.content_type = 'application/octet-stream'
			return res
		elif isinstance(r, str):
			if r.startswith('redirect:'):
				return web.HTTPFound(r[9:])
			res = web.Response(body = r.encode('utf-8'))
			res.content_type = 'text/html;charset=utf-8'
			return res
		elif isinstance(r, dict):
			tmpl = r.get('__template__')
			if tmpl is None:
				res = web.Response(body = json.dumps(r, ensure_ascii = Flase, default = lambda o: o.__dict__).encode('utf-8'))
				res.content_type = 'application/json;charset=utr-8'
				return res 
			else:
				res = web.Response(body = app['__templating__'].get_template(tmpl).render(**r).encode('utf-8'))
				res.content_type = 'text/html;charset=utf-8'
				return res
		elif isinstance(r, int) and r >= 100 and r < 600:
			return web.Response(r)
		elif isinstance(r, tuple) and len(r) == 2:
			t, m = r
			if isinstance(t, int) and t >= 100 and t < 600:
				return web.Response(t, str(m))
		res = web.Response(body = str(r).encode('utf-8'))
		res.content_type = 'text/plain;charset=utf-8'
		return res 
	return response

@asyncio.coroutine
def init(loop):
	yield from orm.create_pool(loop = loop, host = '127.0.0.1', port = 3306, user = 'root', password = 'darkgodz', db = 'pyPractice')
	app = web.Application(loop = loop, middlewares = [logger_factory, response_factory])
	init_jinja2(app, filters = dict(datetime = datetime_filter))
	add_routes(app, 'handlers')
	add_static(app)
	srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
	logging.info('server started at http://127.0.0.1:9000...')
	return srv
	
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

if __name__ == '__main__':
	print('app.py compile success')
	
