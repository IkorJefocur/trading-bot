from datetime import timedelta, date, time, datetime, timezone
from asyncio import sleep, exceptions as asyncexc
from events import Events
from aiohttp import ClientTimeout, ClientError
from ..base import Plugin
from ..models.position import Symbol, Profit, PlacedPosition

class BinanceTraderWatch(Plugin):

	def __init__(self, http_service, trader, uid):
		super().__init__(http_service)
		self.events = Events((
			'trader_fetched',
			'performance_updated',
			'position_updated', 'position_opened', 'position_closed',
			'position_increased', 'position_decreased'
		))
		self.http_timeout = ClientTimeout(total = 5)

		self.trader = trader
		self.id = uid

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.send_task(self.watch())

	async def watch(self):
		performance_update_time = datetime.now()

		while True:
			if performance_update_time <= datetime.now():
				sleep_time = await self.update_performance()
				performance_update_time = \
					datetime.now() + timedelta(seconds = sleep_time or 0)

			sleep_time = await self.update_positions()
			self.events.trader_fetched()
			await sleep(sleep_time or 0)

	@Plugin.loop_bound
	async def update_performance(self):
		try:
			data = (await self.trader_related_request(
				'https://www.binance.com/bapi/futures/v1/public'
				+ '/future/leaderboard/getOtherPerformance'
			))['data']

			roi = float(data[0]['value'])
			pnl = float(data[1]['value'])

		except (ClientError, LookupError, ValueError, asyncexc.TimeoutError):
			return 10

		performance = self.trader.performance('daily')
		performance.current_profit = Profit(roi, pnl)
		self.events.performance_updated(performance)

		return (datetime.combine(
			date.today() + timedelta(days = 1), time(second = 5), timezone.utc
		) - datetime.now(timezone.utc)).seconds

	@Plugin.loop_bound
	async def update_positions(self):
		try:
			data = (await self.trader_related_request(
				'https://www.binance.com/bapi/futures/v1/public'
				+ '/future/leaderboard/getOtherPosition'
			))['data']
			current = list(data['otherPositionRetList'])

		except (ClientError, LookupError, TypeError):
			return 10
		except asyncexc.TimeoutError:
			return 5

		received = {}
		for cur_pos in current:
			try:
				symbol = Symbol(cur_pos['symbol'])
				time = datetime.fromtimestamp(cur_pos['updateTimeStamp'] / 1000)
				entry_price = float(cur_pos['entryPrice'])
				price = float(cur_pos['markPrice'])
				amount = float(cur_pos['amount'])
				profit = Profit(float(cur_pos['roe']), float(cur_pos['pnl']))
				leverage = int(cur_pos['leverage'])

			except (LookupError, ValueError, TypeError):
				continue

			position = PlacedPosition(
				symbol, price, amount, profit, time, leverage
			)
			received[self.trader.deal_category(position)] = position

		for position in self.trader.opened_position():
			if self.trader.deal_category(position) not in received:
				position = position.close()
				self.trader.update_position(position)
				self.events.position_updated(position)
				self.events.position_closed(position)

		for position in self.prepare_available_positions(received.values()):
			self.trader.update_position(position)
			event = self.events.position_opened if not position.prev \
				else self.events.position_increased if position.increased \
				else self.events.position_decreased
			self.events.position_updated(position)
			event(position)

	@Plugin.loop_bound
	async def trader_related_request(self, url):
		return await (await self.service.target.post(
			url,
			json = {'tradeType': 'PERPETUAL', 'encryptedUid': self.id},
			proxy = self.service.get_proxy(),
			raise_for_status = True,
			timeout = self.http_timeout
		)).json()

	def prepare_available_positions(self, positions):
		for position in positions:
			if not self.trader.has_position(position):
				yield position.chain(self.trader.opened_position(position))

class BinanceTraderSafeWatch(BinanceTraderWatch):

	def __init__(self, http_service, trader, uid):
		super().__init__(http_service, trader, uid)
		self.starting_point = None
		self.opened_before_start = set()

	async def watch(self):
		self.starting_point = datetime.now()
		await super().watch()

	def prepare_available_positions(self, positions):
		if not self.starting_point:
			return

		categories = {self.trader.deal_category(pos) for pos in positions}
		for category in self.opened_before_start:
			if category not in categories:
				self.opened_before_start.remove(category)

		for position in super().prepare_available_positions(positions):
			category = self.trader.deal_category(position)
			if (
				category not in self.opened_before_start
				and position.time >= self.starting_point
			):
				yield position
			else:
				self.opened_before_start.add(category)

class BinanceTraderProfitableWatch(BinanceTraderSafeWatch):

	def prepare_available_positions(self, positions):
		yield from super().prepare_available_positions(positions)

		for position in positions:
			category = self.trader.deal_category(position)
			if category in self.opened_before_start and position.profit.pnl < 0:
				self.opened_before_start.remove(category)
				yield position