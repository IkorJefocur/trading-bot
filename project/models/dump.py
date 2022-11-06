from weakref import WeakKeyDictionary, WeakValueDictionary
from datetime import date, datetime
from itertools import chain
from inspect import getmro
from .position import \
	Symbol, Profit, Position, PlacedPosition, ReflectivePosition
from .statistics import PositionStats, Performance
from .trader import Trader

class Dump:

	def __init__(self, formats = None, data = {}, links = {}):
		if not formats:
			formats = [
				ProfitFormat(),
				PositionFormat(),
				PlacedPositionFormat(),
				ReflectivePositionFormat(),
				TraderFormat()
			]
		self.cls_formats = {formatter.cls: formatter for formatter in formats}
		self.name_formats = {formatter.name: formatter for formatter in formats}
		if len(formats) > len(self.name_formats):
			raise ValueError('Formats name conflict')

		self.id = ID()
		self.ref = RefFormat()

		self.data = data
		self.links = links

	@property
	def data(self):
		strong_refs = {*chain.from_iterable(
			self.all_ref_ids(self.ref.raw(link)) for link in self.links.values()
		)}
		for id_num in [*self.raw_data.keys()]:
			if not id_num in strong_refs:
				del self.raw_data[id_num]

		return self.raw_data
	@data.setter
	def data(self, value):
		self.raw_data = {int(id_num): obj for id_num, obj in value.items()}
		if len(value) > 0:
			self.id.last = max(self.raw_data.keys())

	def all_ref_ids(self, data):
		ref = self.ref.obj(data)
		if ref != None:
			yield ref
			yield from self.all_ref_ids(self.raw_data.get(ref))

		if type(data) == dict:
			data = [*data.values()]
		if type(data) == list:
			for value in data:
				yield from self.all_ref_ids(value)

	def save(self, obj):
		data = obj
		for Cls in getmro(type(data)):
			if Cls in self.cls_formats:
				formatter = self.cls_formats[Cls]
				data = {'type': formatter.name, **formatter.raw(data)}
				break

		if type(data) == dict:
			data = {key: self.save(value) for key, value in data.items()}
			if 'type' in data:
				id_num = self.id.identify(obj)
				self.raw_data[id_num] = data
				return self.ref.raw(id_num)

		if type(data) == list:
			return [self.save(value) for value in data]
		return data

	def load(self, data):
		ref = self.ref.obj(data)
		if ref != None:
			loaded = self.id.get(ref)
			if loaded:
				return loaded
			if ref not in self.raw_data:
				return None
			data = self.load(self.raw_data[ref])
			self.id.identify(data, ref)

		if type(data) == dict:
			data = {key: self.load(value) for key, value in data.items()}
			if data.get('type') in self.name_formats:
				return self.name_formats[data['type']].obj(data)

		if type(data) == list:
			return [self.load(value) for value in data]
		return data

	def assoc(self, link, obj):
		if obj != None:
			self.links[link] = self.ref.obj(self.save(obj))
		elif link in self.links:
			del self.links[link]

	def follow(self, link):
		if link in self.links:
			return self.load(self.ref.raw(self.links[link]))

class ID:

	def __init__(self, last = -1):
		self.id_objects = WeakValueDictionary()
		self.objects_id = WeakKeyDictionary()
		self.last_id = last

	@property
	def last(self):
		return self.last_id
	@last.setter
	def last(self, value):
		if value > self.last_id:
			self.last_id = value

	def get(self, id_num):
		return self.id_objects.get(id_num)

	def identify(self, obj, preferred_id = None):
		if obj not in self.objects_id:
			if preferred_id == None:
				preferred_id = self.last + 1
			self.last = preferred_id
			self.objects_id[obj] = preferred_id
			self.id_objects[preferred_id] = obj
		return self.objects_id[obj]

class RefFormat:

	def raw(self, ref):
		return {'type': 'ref', 'id': ref}

	def obj(self, ref):
		if type(ref) == dict and ref.get('type') == 'ref':
			return ref.get('id')

class Format:

	cls = object
	name = ''

	def raw(self, data):
		return data

	def obj(self, data):
		return data

class ProfitFormat(Format):

	cls = Profit
	name = 'Profit'

	def raw(self, profit):
		return {'roe': profit.roe, 'pnl': profit.pnl}

	def obj(self, profit):
		return Profit(profit['roe'], profit['pnl'])

class PositionFormat(Format):

	cls = Position
	name = 'Position'

	def raw(self, position):
		return {
			'symbol': position.symbol.value,
			'price': position.price,
			'amount': position.amount
		}

	def obj(self, position):
		return Position(
			Symbol(position['symbol']),
			position['price'],
			position['amount']
		)

class PlacedPositionFormat(PositionFormat):

	cls = PlacedPosition
	name = 'PlacedPosition'

	def raw(self, position):
		return {
			**super().raw(position),
			'profit': position.profit,
			'time': position.time.timestamp()
		}

	def obj(self, position):
		return PlacedPosition(
			Symbol(position['symbol']),
			position['price'],
			position['amount'],
			position['profit'],
			datetime.fromtimestamp(position['time'])
		)

class ReflectivePositionFormat(PositionFormat):

	cls = ReflectivePosition
	name = 'ReflectivePosition'

	def raw(self, position):
		return {
			'symbol': position.symbol.value,
			'price': position.price,
			'parts': [{
				'key': key,
				'amount': amount
			} for key, amount in position.parts_chain]
		}

	def obj(self, position):
		return ReflectivePosition(
			Symbol(position['symbol']),
			position['price'],
			[{part['key']: part['amount']} for part in position['parts']]
		)

class TraderFormat(Format):

	cls = Trader
	name = 'Trader'

	def raw(self, trader):
		return {
			'positions': trader.opened_position(),

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

			'positions_stats': {
				category: {
					'position': pos.last_position,
					'min_pnl': pos.min_pnl_profit,
					'max_pnl': pos.max_pnl_profit,
					'min_roe': pos.min_roe_profit,
					'max_roe': pos.max_roe_profit
				} for category, pos in trader.position_stats()
			}
		}

	def obj(self, trader):
		return Trader(
			trader['positions'],

			[Performance(
				period, date.fromisocalendar(*perf['date']), perf['total'],
				perf['current'], perf['min'], perf['max'], perf['average']
			) for period, perf in trader['performance'].items()],

			{category: PositionStats(
				pos['position'],
				pos['min_pnl'], pos['max_pnl'], pos['min_roe'], pos['max_roe']
			) for category, pos in trader['positions_stats'].items()}
		)