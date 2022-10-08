from asyncio import \
	new_event_loop, set_event_loop, run_coroutine_threadsafe, wrap_future
from threading import Thread

class Service:

	def __init__(self, target, run = None):
		self.loop = new_event_loop()
		self.thread = None

		self.target = target
		self.run_target = run

	def start_lifecycle(self):
		if not self.thread:
			self.thread = Thread(target = self.lifecycle)
			self.thread.start()

	def lifecycle(self):
		set_event_loop(self.loop)
		self.run()

	def run(self):
		if self.run_target:
			self.run_target(self.target)
		else:
			self.loop.run_forever()

	def send_task(self, coro):
		def propagate_future_exception(future):
			if future.exception(): raise future.exception()
		run_coroutine_threadsafe(coro, self.loop) \
			.add_done_callback(propagate_future_exception)

class Plugin:

	@staticmethod
	def loop_bound(method):
		def bound(self, *args, **kwargs):
			return wrap_future(run_coroutine_threadsafe(
				method(self, *args, **kwargs), self.service.loop
			))
		return bound

	def __init__(self, service = None):
		self.service = service or Service(None)

	def start_lifecycle(self):
		self.service.start_lifecycle()