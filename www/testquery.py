import orm
from models import User, Blog, Comment
import asyncio

loop = asyncio.get_event_loop()

@asyncio.coroutine
def test():
	yield from orm.create_pool(loop = loop, host = '127.0.0.1', port = 3306, user = 'root', password = 'darkgodz', db='pyPractice')
	u = User(name='Test1', email='test1@example.com', password='1234567890', image='about:blank', id='1234')
	yield from u.save()
	u2 = User(name='Test2', email='test2@example.com', password='1234567890', image='about:blank', id='12345')
	yield from u2.save()

	
loop.run_until_complete(test())

if __name__ == '__main__':
	print('test query success')
