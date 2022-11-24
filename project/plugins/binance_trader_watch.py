from datetime import timedelta, date, time, datetime, timezone
from asyncio import sleep
from events import Events
from aiohttp import ClientTimeout
from traceback import print_exc
from ..base import Plugin
from ..models.position import Symbol, Profit, PlacedPosition

class BinanceTraderWatch(Plugin):

	def __init__(self, http_service, trader, meta, check_rate = 1):
		super().__init__(http_service)
		self.events = Events((
			'trader_fetched',
			'performance_updated',
			'position_updated', 'position_opened', 'position_closed',
			'position_increased', 'position_decreased'
		))

		self.trader = trader
		self.trader_meta = meta
		self.check_rate = check_rate

	def start_lifecycle(self):
		super().start_lifecycle()
		self.service.run_task_sync(self.update_meta())
		self.service.send_task(self.watch())

	async def watch(self):
		performance_update_time = datetime.now()

		while True:
			if performance_update_time <= datetime.now():
				try:
					sleep_time = await self.update_performance()
					performance_update_time = \
						datetime.now() + timedelta(seconds = sleep_time or 0)
				except Exception:
					print_exc()
					await sleep(1)
					continue

			try:
				sleep_time = await self.update_positions()
				self.events.trader_fetched()
			except Exception:
				print_exc()
				sleep_time = 2
			check_rate = self.check_rate / self.service.proxies_count
			await sleep(max(sleep_time or 0, 1) * check_rate)

	@Plugin.loop_bound
	async def update_meta(self):
		data = (await self.trader_related_request(
			'https://www.binance.com/bapi/futures/v2/public'
			+ '/future/leaderboard/getOtherLeaderboardBaseInfo',
			trade_type = None
		))['data']

		self.trader_meta.nickname = data['nickName']

	@Plugin.loop_bound
	async def update_performance(self):
		data = (await self.trader_related_request(
			'https://www.binance.com/bapi/futures/v1/public'
			+ '/future/leaderboard/getOtherPerformance'
		))['data']

		roi = float(data[0]['value'])
		pnl = float(data[1]['value'])

		performance = self.trader.performance('daily')
		performance.current_profit = Profit(roi, pnl)
		self.events.performance_updated(performance)

		return (datetime.combine(
			date.today() + timedelta(days = 1), time(second = 5), timezone.utc
		) - datetime.now(timezone.utc)).seconds

	@Plugin.loop_bound
	async def update_positions(self):
		data = (await self.trader_related_request(
			'https://www.binance.com/bapi/futures/v1/public'
			+ '/future/leaderboard/getOtherPosition'
		))['data']
		current = list(data['otherPositionRetList'] or [])

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
				print_exc()
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
	async def trader_related_request(self, url, trade_type = 'PERPETUAL'):
		return await (await self.service.get_session().post(
			url,
			json = {
				**({'tradeType': trade_type} if trade_type else {}),
				'encryptedUid': self.trader_meta.id
			},
			proxy = self.service.get_proxy(),
			raise_for_status = True
		)).json()

	def prepare_available_positions(self, positions):
		for position in positions:
			if not self.trader.has_position(position):
				yield position.chain(self.trader.opened_position(position))

class BinanceTraderSafeWatch(BinanceTraderWatch):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.starting_point = None
		self.opened_before_start = set()

	async def watch(self):
		self.starting_point = datetime.now()
		await super().watch()

	def prepare_available_positions(self, positions):
		if not self.starting_point:
			return

		categories = {self.trader.deal_category(pos) for pos in positions}
		for category in [*self.opened_before_start]:
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