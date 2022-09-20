from threading import Thread
from asyncio import new_event_loop, set_event_loop, run_coroutine_threadsafe

def run(server, bot):
	def run_server():
		server.run()
	Thread(target = run_server).start()

	bot_loop = new_event_loop()
	def run_bot():
		set_event_loop(bot_loop)
		bot.run()
	bot_thread = Thread(target = run_bot)
	bot_thread.start()

	def bridge(data):
		run_coroutine_threadsafe(bot.send(data), bot_loop) \
			.add_done_callback(propagate_future_exception)
	server.add_receiver(bridge)

	bot_thread.join()

def propagate_future_exception(future):
	if future.exception():
		raise future.exception()