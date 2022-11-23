from asyncio import \
	new_event_loop, set_event_loop, \
	run_coroutine_threadsafe, wrap_future, all_tasks
from threading import Thread

class Service:

	def __init__(self):
		self.loop = new_event_loop()
		self.thread = None
		self.plugins_count = 0

	def start_lifecycle(self):
		self.plugins_count += 1
		if self.plugins_count >= 0 and not self.thread:
			self.thread = Thread(target = self.lifecycle)
			self.thread.daemon = True
			self.thread.start()

	def lifecycle(self):
		set_event_loop(self.loop)
		self.run()

	def run(self):
		self.loop.run_forever()

	def stop_lifecycle(self):
		self.plugins_count -= 1
		if self.plugins_count <= 0 and self.thread:
			self.stop()
			self.thread.join()
			self.thread = None

	def stop(self):
		if self.loop.is_running():
			for task in all_tasks(self.loop):
				task.cancel()
			self.loop.call_soon_threadsafe(self.loop.stop)

	def send_task(self, coro):
		def propagate_future_exception(future):
			if future.exception(): raise future.exception()
		run_coroutine_threadsafe(coro, self.loop) \
			.add_done_callback(propagate_future_exception)

	async def run_task(self, coro):
		return await wrap_future(run_coroutine_threadsafe(coro, self.loop))

	def run_task_sync(self, coro, timeout = None):
		return run_coroutine_threadsafe(coro, self.loop).result(timeout)

class Plugin:

	@staticmethod
	def loop_bound(method):
		def bound(self, *args, **kwargs):
			return self.service.run_task(method(self, *args, **kwargs))
		return bound

	def __init__(self, service = None):
		self.service = service or Service(None)

	def start_lifecycle(self):
		self.service.start_lifecycle()

	def stop_lifecycle(self):
		self.service.stop_lifecycle()