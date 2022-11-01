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

		to_update = {}
		for cur_pos in current:
			try:
				symbol = Symbol(cur_pos['symbol'])
				time = datetime.fromtimestamp(cur_pos['updateTimeStamp'] / 1000)
				entry_price = float(cur_pos['entryPrice'])
				price = float(cur_pos['markPrice'])
				amount = float(cur_pos['amount'])
				profit = Profit(float(cur_pos['roe']), float(cur_pos['pnl']))

			except (LookupError, ValueError, TypeError):
				continue

			position = PlacedPosition(symbol, price, amount, profit, time)
			category = self.trader.deal_category(position)
			to_update[category] = position

		for position in self.trader.opened_position():
			if (
				self.trader.deal_category(position) not in to_update
				and self.available(position, False)
			):
				position = position.close()
				self.trader.update_position(position)
				self.events.position_updated(position)
				self.events.position_closed(position)

		for category, position in to_update.items():
			if (
				not self.trader.has_position(position)
				and self.available(position, True)
			):
				position = position.chain(self.trader.opened_position(position))
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

	def available(self, position, remember):
		return True

class BinanceTraderSafeWatch(BinanceTraderWatch):

	def __init__(self, http_service, trader, uid):
		super().__init__(http_service, trader, uid)
		self.starting_point = None
		self.opened_before_start = set()

	async def watch(self):
		self.starting_point = datetime.now()
		await super().watch()

	def available(self, position, remember):
		if not self.starting_point:
			return True
		category = self.trader.deal_category(position)
		if category in self.opened_before_start:
			if not remember:
				self.opened_before_start.remove(category)
			return False
		available = position.time > self.starting_point
		if not available and remember:
			self.opened_before_start.add(category)
		return available

class BinanceTraderProfitableWatch(BinanceTraderSafeWatch):

	def available(self, position, remember):
		if position.profit.pnl < 0:
			category = self.trader.deal_category(position)
			self.opened_before_start.discard(category)
			return True
		return super().available(position, remember)