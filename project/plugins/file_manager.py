from datetime import date
from json import dumps, loads
from ..base import Plugin
from ..models.position import Profit
from ..models.trader import PositionStats, Performance, Trader

class FileManager(Plugin):

	def __init__(self, path, formatter, save_interval = 15):
		super().__init__()
		self.buffer = None
		self.work_time = 0

		self.path = path
		self.format = formatter
		self.interval = save_interval

	def __del__(self):
		self.flush()

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
		return dumps(data, indent = '\t')

	def parse(self, data):
		return loads(data)

class TraderFormat(Format):

	def dump(self, trader):
		return super().dump({
			'uid': trader.id,

			'performance': {
				perf.period: {
					'date': perf.current_date.isocalendar(),
					'total': perf.total_records,
					'current': self.dump_profit(perf.current_profit),
					'min': self.dump_profit(perf.min_deposit_profit),
					'max': self.dump_profit(perf.max_deposit_profit),
					'average': perf.average_deposit
				} for perf in trader.performance()
			},

			'positions': {
				category: {
					'min_pnl': self.dump_profit(pos.min_pnl_profit),
					'max_pnl': self.dump_profit(pos.max_pnl_profit),
					'min_roe': self.dump_profit(pos.min_roe_profit),
					'max_roe': self.dump_profit(pos.max_roe_profit)
				} for category, pos in trader.position_stats()
			}
		})

	def parse(self, trader):
		trader = super().parse(trader)
		return Trader(
			trader['uid'],

			[Performance(
				period, date.fromisocalendar(*perf['date']), perf['total'],
				self.parse_profit(perf['current']),
				self.parse_profit(perf['min']),
				self.parse_profit(perf['max']),
				perf['average']
			) for period, perf in trader['performance'].items()],

			{category: PositionStats(
				None,
				self.parse_profit(pos['min_pnl']),
				self.parse_profit(pos['max_pnl']),
				self.parse_profit(pos['min_roe']),
				self.parse_profit(pos['max_roe'])
			) for category, pos in trader['positions'].items()}
		)

	def dump_profit(self, profit):
		return {
			'roe': profit.roe,
			'pnl': profit.pnl
		}

	def parse_profit(self, profit):
		return Profit(profit['roe'], profit['pnl'])