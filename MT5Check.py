import MetaTrader5 as mt5
mt5.initialize()
print(mt5.account_info())
mt5.shutdown()