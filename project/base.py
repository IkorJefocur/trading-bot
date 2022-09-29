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

class Plugin:

	@staticmethod
	def loop_bound(method):
		async def bound(self, *args, **kwargs):
			return await wrap_future(run_coroutine_threadsafe(
				method(self, *args, **kwargs), self.service.loop
			))
		return bound

	def __init__(self, service = None):
		self.service = service or Service(None)

	def start_lifecycle(self):
		self.service.start_lifecycle()