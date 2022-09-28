from threading import Thread
from asyncio import new_event_loop, set_event_loop, run_coroutine_threadsafe

def run(server, trade, bot):
	def run_server():
		server.run()
	server_thread = Thread(target = run_server)
	server_thread.start()

	trade_loop = new_event_loop()
	def run_trade():
		set_event_loop(trade_loop)
		trade_loop.run_forever()
	Thread(target = run_trade).start()

	bot_loop = new_event_loop()
	def run_bot():
		set_event_loop(bot_loop)
		bot.run()
	Thread(target = run_bot).start()

	def bridge(order):
		run_coroutine(trade.make_order(order), trade_loop)
		run_coroutine(bot.send(order), bot_loop)
	server.events.order_added += bridge

	server_thread.join()

def run_coroutine(coro, loop):
	run_coroutine_threadsafe(coro, loop) \
		.add_done_callback(propagate_future_exception)

def propagate_future_exception(future):
	if future.exception():
		raise future.exception()