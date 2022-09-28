from math import floor
from asyncio import sleep
from concurrent.futures import ThreadPoolExecutor
from pybit import usdt_perpetual
from ..base import Plugin

class Trade(Plugin):

	def __init__(self, endpoint, key, secret):
		super().__init__()
		self.executor = ThreadPoolExecutor()

		self.endpoint = endpoint
		self.key = key
		self.secret = secret

		self.usdt_perpetual = usdt_perpetual.HTTP(
			endpoint = self.endpoint,
			api_key = self.key,
			api_secret = self.secret
		)

	@Plugin.loop_bound
	async def make_order(self, candle):
		run = self.service.loop.run_in_executor
		opened_ids = await run(self.executor, lambda: self.open_order(candle))
		await sleep(10)
		await run(self.executor, lambda: self.close_order(candle, opened_ids))

	def open_order(self, candle):
		session = self.usdt_perpetual

		depo = session.get_wallet_balance(coin = 'USDT') \
			['result']['USDT']['wallet_balance']
		usdt_quanty = round(depo / candle.close / 100)
		if usdt_quanty == 0:
			return

		opened_ids = []
		stepsize = floor(candle.shadow / 3 * .95)

		for step in range(4):
			entry = candle.close - stepsize * step
			buy_limit = session.place_active_order(
				symbol = candle.coin,
				side = 'Buy' if candle.buy else 'Sell',
				order_type = 'Limit',
				qty = usdt_quanty,
				price = entry,
				take_profit = round(entry / 100 * (step + 1) + entry, 3),
				time_in_force = 'GoodTillCancel',
				reduce_only = False,
				close_on_trigger = False,
				is_isolated = True,
				leverage = 5
			)
			opened_ids += [buy_limit['result']['order_id']]

		return opened_ids

	def close_order(self, candle, opened_ids):
		for order_id in opened_ids:
			session.cancel_active_order(symbol = candle.coin, order_id = order_id)