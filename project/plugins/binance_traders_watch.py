from datetime import timedelta, date, time, datetime, timezone
from asyncio import sleep
from events import Events
from aiohttp import ClientError
from ..base import Plugin
from ..models.trader import Symbol, Profit, Position, Trader

class BinanceTradersWatch(Plugin):

	def __init__(self, http_service, trader):
		super().__init__(http_service)
		self.events = Events((
			'trader_fetched',
			'performance_updated',
			'position_updated', 'position_opened', 'position_closed',
			'position_increased', 'position_decreased'
		))

		self.starting_point = None
		self.opened_positions = {}

		self.trader = trader

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.send_task(self.watch())

	async def watch(self):
		performance_update_time = datetime.now()
		self.starting_point = datetime.now()

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

		except (ClientError, LookupError, ValueError):
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

		to_update = {}
		for cur_pos in current:
			try:
				symbol = Symbol(cur_pos['symbol'])
				time = datetime.fromtimestamp(cur_pos['updateTimeStamp'] / 1000)
				entry_price = float(cur_pos['entryPrice'])
				price = float(cur_pos['markPrice'])
				amount = float(cur_pos['amount'])
				roe = float(cur_pos['roe'])
				pnl = float(cur_pos['pnl'])

			except (LookupError, ValueError, TypeError):
				continue

			position = Position(time, symbol, price, amount, Profit(roe, pnl))
			category = self.trader.position_category(position)
			to_update[category] = position

		for category, position in self.opened_positions.items():
			if category not in to_update:
				del self.opened_positions[category]
				if self.available(position):
					position = position.close()
					self.trader.position_stats(position).last_position = position
					self.events.position_updated(position)
					self.events.position_closed(position)

		for category, position in to_update.items():
			prev = self.opened_positions.get(category)
			if not position.chain_equal(prev):
				position = self.opened_positions[category] = \
					position.chain(prev) if prev else position
				if self.available(position):
					self.trader.position_stats(position).last_position = position
					event = self.events.position_opened if not position.prev \
						else self.events.position_increased if position.increased \
						else self.events.position_decreased
					self.events.position_updated(position)
					event(position)

	@Plugin.loop_bound
	async def trader_related_request(self, url):
		return await (await self.service.target.post(
			url,
			json = {'tradeType': 'PERPETUAL', 'encryptedUid': self.trader.id},
			proxy = self.service.get_proxy(),
			raise_for_status = True
		)).json()

	def available(self, position):
		return bool(position and self.starting_point) \
			and position.entry.time > self.starting_point