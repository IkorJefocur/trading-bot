from math import floor
from asyncio import sleep
from pybit import usdt_perpetual

class Trade:

	def __init__(self, endpoint, key, secret):
		self.endpoint = endpoint
		self.key = key
		self.secret = secret

		self.usdt_perpetual = usdt_perpetual.HTTP(
			endpoint = self.endpoint,
			api_key = self.key,
			api_secret = self.secret
		)

	async def make_order(self, order):
		session = self.usdt_perpetual

		depo = session.get_wallet_balance(coin = 'USDT') \
			['result']['USDT']['wallet_balance']
		usdt_quanty = round(depo / order.close / 100)
		if usdt_quanty == 0:
			return

		just_opened_orders = []
		stepsize = floor(order.candle_shadow / 3 * .95)

		for step in range(4):
			entry = order.close - stepsize * step
			buy_limit = session.place_active_order(
				symbol = order.coin,
				side = 'Buy' if order.buy else 'Sell',
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
			just_opened_orders.append(buy_limit['result']['order_id'])

		await sleep(10)

		for order_id in just_opened_orders:
			session.cancel_active_order(symbol = order.coin, order_id = order_id)