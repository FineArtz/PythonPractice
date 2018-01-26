from coroweb import get
import asyncio

@get('/')
@asyncio.coroutine
def index(request):
	return '<h1>Try</h1>'
	
@get('/hello')
@asyncio.coroutine
def hello(request):
	return '<h1>hello</h1>'
	
