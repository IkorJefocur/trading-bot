from datetime import timedelta, date, time, datetime
from asyncio import sleep, gather
from events import Events
from aiohttp import ClientError
from ..base import Plugin
from ..models.trader import Profit, Position, Trader

class BinanceTradersWatch(Plugin):

	def __init__(self, http_service, traders):
		super().__init__(http_service)
		self.events = Events((
			'trader_fetched',
			'performance_updated',
			'position_opened', 'position_updated', 'position_closed'
		))

		self.traders = traders

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.send_task(self.watch())

	async def watch(self):
		await gather(*(
			self.watch_trader(trader) for trader in self.traders
		))

	async def watch_trader(self, trader):
		performance_update_time = datetime.now()

		while True:
			if performance_update_time <= datetime.now():
				sleep_time = await self.update_performance(trader)
				performance_update_time = \
					datetime.now() + timedelta(seconds = sleep_time or 0)

			sleep_time = await self.update_positions(trader)
			self.events.trader_fetched(trader)
			await sleep(sleep_time or 0)

	@Plugin.loop_bound
	async def update_performance(self, trader):
		try:
			data = (await self.trader_related_request(
				'https://www.binance.com/bapi/futures/v1/public'
				+ '/future/leaderboard/getOtherPerformance',
				trader
			))['data']

			roi = float(data[0]['value'])
			pnl = float(data[1]['value'])

		except (ClientError, LookupError, ValueError):
			return 10

		performance = trader.performance('daily')
		performance.update(Profit(roi, pnl))
		self.events.performance_updated(performance, trader)

		return (datetime.combine(
			date.today() + timedelta(days = 1),
			time(second = 5)
		) - datetime.now()).seconds

	@Plugin.loop_bound
	async def update_positions(self, trader):
		try:
			data = (await self.trader_related_request(
				'https://www.binance.com/bapi/futures/v1/public'
				+ '/future/leaderboard/getOtherPosition',
				trader
			))['data']
			current_positions = list(data['otherPositionRetList'])
			current_symbols = {pos['symbol'] for pos in current_positions}

		except (ClientError, LookupError, TypeError):
			return 10

		for cur_pos in current_positions:
			try:
				symbol = cur_pos['symbol']
				stats = trader.position_stats(symbol)
				time = datetime.fromtimestamp(cur_pos['updateTimeStamp'] / 1000)
				if stats.last_position and stats.last_position.time == time:
					continue

				entry_price = float(cur_pos['entryPrice'])
				price = float(cur_pos['markPrice'])
				amount = float(cur_pos['amount'])
				roe = float(cur_pos['roe'])
				pnl = float(cur_pos['pnl'])

			except (LookupError, ValueError, TypeError):
				continue

			position = Position(
				time, symbol, price, amount, Profit(roe, pnl)
			).chain(stats.last_position)
			stats.update(position)
			event = self.events.position_updated \
				if position.prev and price != entry_price \
				else self.events.position_opened
			event(position, trader)

		for stats in trader.position_stats():
			if stats.symbol not in current_symbols:
				position = stats.last_position
				stats.update(None)
				self.events.position_closed(position, trader)

	@Plugin.loop_bound
	async def trader_related_request(self, url, trader):
		return await (await self.service.target.post(
			url,
			json = {'tradeType': 'PERPETUAL', 'encryptedUid': trader.id},
			proxy = self.service.get_proxy(),
			raise_for_status = True
		)).json()