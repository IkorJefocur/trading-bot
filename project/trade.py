from asyncio import sleep
from pybit import usdt_perpetual

# order_params = {
# 	'side' :"Buy",
# 	'coin' : "BTCUSDT",
# 	'close': 20000,
# 	'pivot': 18600
# }

class Trade:

	def __init__(self, endpoint, api_key, api_secret):
		self.endpoint = endpoint
		self.api_key = api_key
		self.api_secret = api_secret

	async def make_order(
		self, order_side, order_coin, order_last_close, order_last_pivot
	):
		print(f'{order_side} signal')
		justopenedorders = list()
		order_candle_shadow = order_last_close - order_last_pivot
		order_stepsize = int(order_candle_shadow / 3 * 0.95)
		session = usdt_perpetual.HTTP(
			endpoint = self.endpoint,
			api_key = self.api_key,
			api_secret = self.api_secret
		)
		depo = session.get_wallet_balance(coin="USDT") \
			['result']['USDT']['wallet_balance']
		usdt_quanty = (depo / order_last_close / 100 * 1)
		print(depo)
		print(usdt_quanty)
		for order_step in range(4):
			order_candle_shadow = order_last_close - order_last_pivot
			order_stepsize = int(order_candle_shadow / 3 * 0.95)
			order_entry = order_last_close - order_stepsize * order_step
			buy_limit = session.place_active_order(
				symbol = order_coin,
				side = order_side,
				order_type = "Limit",
				qty = round(usdt_quanty,3),
				price = order_entry,
				take_profit = order_entry / 100 * (order_step + 1) + order_entry,
				time_in_force = "GoodTillCancel",
				reduce_only = False,
				close_on_trigger = False,
				is_isolated = 'true',
				leverage = 5
			)
			print(order_entry / 100 * (order_step +1) + order_entry)
			buy_limit
			orderid = buy_limit['result']['order_id']
			print(buy_limit['result']['price'])
			justopenedorders.append(orderid)
		print(justopenedorders)
		await sleep(10)
		print(f'orders timed out {len(justopenedorders)}')
		for i in range(len(justopenedorders)):
			session.cancel_all_active_orders(symbol="BTCUSDT")
			print('timedout order deleted')