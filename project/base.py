from asyncio import \
	new_event_loop, set_event_loop, run_coroutine_threadsafe, wrap_future
from threading import Thread

class Plugin:

	@staticmethod
	def loop_bound(method):
		def bound(self, *args, **kwargs):
			return run_coroutine(method(self, *args, **kwargs), self.loop)
		return bound

	def __init__(self):
		self.loop = new_event_loop()

	def run(self):
		self.loop.run_forever()

	def start_lifecycle(self):
		def lifecycle():
			set_event_loop(self.loop)
			self.run()
		Thread(target = lifecycle).start()

def run_coroutine(coro, loop):
	future = run_coroutine_threadsafe(coro, loop)
	future.add_done_callback(propagate_future_exception)
	return wrap_future(future)

def propagate_future_exception(future):
	if future.exception():
		raise future.exception()