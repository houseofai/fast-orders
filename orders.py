import math

from ib_insync import IB, Stock, StopOrder, Order, TagValue, MarketOrder, LimitOrder

from util import get_time


def _validate_stop_loss(stop_loss, limit_price, action, stoploss_percent=5):
    assert limit_price > 0, "Limit price must be greater than 0."
    assert stoploss_percent > 0, "Stop Loss percentage must be greater than 0."
    assert action in ['BUY', 'SELL'], "Action must be either 'BUY' or 'SELL'."

    if stop_loss == '':
        if action == 'BUY':
            stop_loss = limit_price * (1 - stoploss_percent / 100)
        else:
            stop_loss = limit_price * (1 + stoploss_percent / 100)

    if stop_loss >= limit_price and action == 'BUY':
        raise ValueError("Input Error",
                         f"Stop Loss ({stop_loss}) must be less than the limit price: {limit_price}.")
    elif stop_loss <= limit_price and action == 'SELL':
        raise ValueError("Input Error",
                         f"Stop Loss ({stop_loss}) must be greater than the limit price: {limit_price}.")

    try:
        stop_loss = round(float(stop_loss), 2)
    except ValueError:
        raise ValueError("Input Error", "Stop Loss must be a valid number.")
    return stop_loss


def _validate_quantity(dollar_risk, dollar_threshold, limit_price, stop_loss, position):
    assert dollar_risk > 0, "Dollar risk must be greater than 0."
    assert dollar_threshold > 0, "Dollar threshold must be greater than 0."
    assert limit_price > 0, "Limit price must be greater than 0."
    assert stop_loss > 0, "Stop Loss must be greater than 0."
    assert position > 0, "Position must be greater than 0."

    total_quantity = int((dollar_risk / (limit_price - stop_loss)) * position)

    if total_quantity < 1:
        print(f"Invalid total quantity: ({dollar_risk} / ({limit_price} - {stop_loss})) * {position}")
        raise ValueError("Input Error", f"Invalid total quantity: {total_quantity}.")

    if total_quantity * limit_price > dollar_threshold:
        raise ValueError("Input Error",
                         f"Total quantity over $ threshold: {total_quantity * limit_price}.")
    return total_quantity


def get_latest_price(client, contract):
    print(f"[{get_time()}] Requesting market data for {contract.symbol}...")
    client.reqMktData(contract, '', False, False)
    ticker = client.ticker(contract)
    client.sleep(0.5)  # wait for market data

    latest_price = ticker.marketPrice() if ticker.marketPrice() > 0 else ticker.close
    print(f"[{get_time()}] Latest price for {contract.symbol} is {latest_price}")
    if latest_price is None or math.isnan(latest_price):
        raise ValueError("Market Data Error", f"Failed to retrieve the latest price for {contract.symbol}.")

    return latest_price


class IBConnection:
    def __init__(self):
        self.client = self.connect()

    def connect(self):
        if hasattr(self, 'client') and self.client.isConnected():
            print(f"[{get_time()}] Already connected to TWS.")
            return self.client

        print(f"[{get_time()}] Connecting to TWS...")
        self.client = IB()
        self.client.connect('127.0.0.1', 7497, clientId=21)

        if self.client.isConnected():
            print(f"[{get_time()}] Connected to TWS!")
        else:
            print(f"[{get_time()}] Failed to connect to TWS.")

        return self.client

    def disconnect(self):
        self.client.disconnect()
        print(f"[{get_time()}] Disconnected from TWS")


class MyOrder:
    def __init__(self, connection, dollar_risk=50, dollar_threshold=10000):
        self.cds = None
        # self.stock = None
        self.stop_loss_percentage = None
        self.invested_amount = None
        self.account_cash = None
        self.total_quantity = None
        self.limit_price = None
        self.latest_price = None
        self.contract = None
        self.stop_loss = None
        self.action = None
        self.position = None
        self.client = connection.connect()
        self.account_cash = self.get_available_cash()
        self.dollar_risk = dollar_risk
        self.dollar_threshold = dollar_threshold

    def get_contract(self, symbol):
        assert symbol.isalpha(), "Symbol must be alphabetic."
        assert symbol.isupper(), "Symbol must be uppercase."
        assert 1 <= len(symbol) <= 5, "Symbol must be between 1 and 5 characters."

        stock = Stock(symbol, "SMART", 'USD')
        cds = self.client.reqContractDetails(stock)
        if len(cds) == 0:
            raise ValueError("Contract Error", f"Failed to retrieve contract details for {symbol}.")
        contract = cds[0].contract
        return contract

    def prep_order(self, symbol, position, action, stop_loss):
        assert position in [0.25, 0.5, 1], "Position must be 0.25, 0.5, or 1."
        assert action in ['BUY', 'SELL'], "Action must be either 'BUY' or 'SELL."

        self.position = position
        self.action = action

        self.contract = self.get_contract(symbol)
        self.latest_price = get_latest_price(self.client, self.contract)

        if action == 'BUY':
            self.limit_price = round(self.latest_price * 1.01, 2)  # 1% above the latest price
        else:
            self.limit_price = round(self.latest_price * 0.99, 2)

        self.stop_loss = _validate_stop_loss(stop_loss, self.limit_price, action)
        self.total_quantity = _validate_quantity(self.dollar_risk, self.dollar_threshold, self.limit_price,
                                                 self.stop_loss, position)

        self.invested_amount = self.total_quantity * self.limit_price
        self.stop_loss_percentage = ((self.limit_price - self.stop_loss) / self.limit_price) * 100

    def get_available_cash(self):
        account_values = self.client.accountValues()
        cash_balance = next((av.value for av in account_values if av.tag == 'CashBalance' and av.currency == 'USD'),
                            None)
        return float(cash_balance) if cash_balance else None

    def place_order(self, order_type='MARKET'):

        if order_type == 'MARKET':
            order = MarketOrder(self.action, self.total_quantity)
        elif order_type == 'LIMIT':
            order = LimitOrder(self.action, self.total_quantity, self.limit_price)
        else:
            order = Order()
            order.action = self.action
            order.orderType = "MIDPRICE"
            order.lmtPrice = self.limit_price
            #order.algoStrategy = "Adaptive"
            #order.algoParams = []
            #order.algoParams.append(TagValue("adaptivePriority", "Urgent"))
            order.totalQuantity = self.total_quantity

        print(f"[{get_time()}] {order.orderType.upper()}: {self.limit_price} | Qty: {self.total_quantity}")
        order.orderId = self.client.client.getReqId()
        order.transmit = True
        parent_trade = self.client.placeOrder(self.contract, order)
        print(f"[{get_time()}] {order.orderType.upper()} sent: {order.orderId}")
        self.client.sleep(1)
        print(f"[{get_time()}] {order.orderType.upper()} status: {parent_trade.orderStatus.status}")

        # order.lmtPrice = priceCap  # optional

        slosso = StopOrder('SELL' if self.action == 'BUY' else 'BUY', self.total_quantity, self.stop_loss)
        slosso.transmit = True
        slosso.tif = 'GTC'
        slosso.parentId = order.orderId
        sl_trade = self.client.placeOrder(self.contract, slosso)
        print(f"[{get_time()}] Stop Loss order placed!")

        self.client.sleep(1)  # wait for order to be processed
        print(f"[{get_time()}] Stop Loss Order status: {sl_trade.orderStatus.status}")
