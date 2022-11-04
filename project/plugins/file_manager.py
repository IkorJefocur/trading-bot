from datetime import date
from json import dumps, loads
from inspect import getmro
from ..base import Plugin
from ..models.position import Profit
from ..models.trader import PositionStats, Performance, Trader

class FileManager(Plugin):

	def __init__(self, path, formatter = None, save_interval = 15):
		super().__init__()
		self.buffer = None
		self.work_time = 0

		self.path = path
		self.format = formatter \
			or MultiFormat([ProfitFormat(), TraderFormat()])
		self.interval = save_interval

	def stop_lifecycle(self):
		self.flush()
		super().stop_lifecycle()

	def save(self, data):
		self.work_time += 1
		self.buffer = data

		if self.work_time == self.interval:
			self.flush()

	def load(self):
		if self.buffer != None:
			return self.flush()

		try:
			with open(self.path, 'r') as file:
				return self.format.parse(file.read())
		except FileNotFoundError:
			return None

	def flush(self):
		if self.buffer == None:
			return None

		data = self.format.dump(self.buffer)
		with open(self.path, 'w') as file:
			file.write(data)

		self.work_time = 0
		self.buffer = None
		return data

class Format:

	def dump(self, data):
		return dumps(self.raw(data), indent = '\t')

	def parse(self, data):
		return self.obj(loads(data))

	def raw(self, data):
		return data

	def obj(self, data):
		return data

class MultiFormat(Format):

	def __init__(self, formats):
		self.cls_formats = {formatter.domain: formatter for formatter in formats}
		self.name_formats = {formatter.name: formatter for formatter in formats}

	def raw(self, data):
		for Cls in getmro(type(data)):
			if Cls in self.cls_formats:
				formatter = self.cls_formats[Cls]
				data = {'type': formatter.name, **formatter.raw(data)}
				break
		if type(data) == dict:
			return {key: self.raw(value) for key, value in data.items()}
		if type(data) == list:
			return [self.raw(value) for value in data]
		return data

	def obj(self, data):
		if type(data) == dict:
			data = {key: self.obj(value) for key, value in data.items()}
			if data.get('type') in self.name_formats:
				return self.name_formats[data.get('type')].obj(data)
		if type(data) == list:
			return [self.obj(value) for value in data]
		return data

class DomainFormat(Format):

	domain = object
	name = ''

class ProfitFormat(DomainFormat):

	domain = Profit
	name = 'Profit'

	def raw(self, profit):
		return {'roe': profit.roe, 'pnl': profit.pnl}

	def obj(self, profit):
		return Profit(profit['roe'], profit['pnl'])

class TraderFormat(DomainFormat):

	domain = Trader
	name = 'Trader'

	def raw(self, trader):
		return {
			'performance': {
				perf.period: {
					'date': perf.current_date.isocalendar(),
					'total': perf.total_records,
					'current': perf.current_profit,
					'min': perf.min_deposit_profit,
					'max': perf.max_deposit_profit,
					'average': perf.average_deposit
				} for perf in trader.performance()
			},

			'positions': {
				category: {
					'min_pnl': pos.min_pnl_profit,
					'max_pnl': pos.max_pnl_profit,
					'min_roe': pos.min_roe_profit,
					'max_roe': pos.max_roe_profit
				} for category, pos in trader.position_stats()
			}
		}

	def obj(self, trader):
		return Trader(
			[Performance(
				period, date.fromisocalendar(*perf['date']), perf['total'],
				perf['current'], perf['min'], perf['max'], perf['average']
			) for period, perf in trader['performance'].items()],

			{category: PositionStats(
				None,
				pos['min_pnl'], pos['max_pnl'], pos['min_roe'], pos['max_roe']
			) for category, pos in trader['positions'].items()}
		)