from datetime import timedelta, datetime
from json import dump, load
from ..base import Plugin
from ..models.dump import Dump

class FileDump(Plugin):

	def __init__(
		self, path,
		dump = None, interval = timedelta(minutes = 1), readable = False
	):
		super().__init__()
		self.buffer = set()
		self.work_time = datetime.now()

		self.path = path
		self.dump = dump or Dump()
		self.save_interval = interval
		self.readable = readable

	def stop_lifecycle(self):
		self.service.run_task_sync(self.flush())
		super().stop_lifecycle()

	async def save(self, obj):
		self.buffer.add(obj)
		if datetime.now() >= self.work_time + self.save_interval:
			await self.flush()

	def load(self):
		if len(self.buffer) > 0:
			self.flush()

		try:
			with open(self.path, 'r') as file:
				content = load(file)
				self.dump.data = content['data']
				self.dump.links = content['links']
		except FileNotFoundError:
			pass

	@Plugin.loop_bound
	async def flush(self):
		self.work_time = datetime.now()
		if len(self.buffer) == 0:
			return

		while len(self.buffer) > 0:
			self.dump.save(self.buffer.pop())
		with open(self.path, 'w') as file:
			dump({
				'data': self.dump.data,
				'links': self.dump.links
			}, file, indent = '\t' if self.readable else None)