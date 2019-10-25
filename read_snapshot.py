"""Gets account balance and positions from a local IBController."""


import argparse
import collections
import datetime
import json
import logging
import os.path
import sys
import time

from ibapi.account_summary_tags import AccountSummaryTags
from ibapi.client import EClient
from ibapi.common import TickerId, TickAttrib, MarketDataTypeEnum
from ibapi.contract import Contract
from ibapi.errors import CONNECT_FAIL
from ibapi.wrapper import EWrapper
from ibapi.ticktype import TickType, TickTypeEnum

Position = collections.namedtuple("Position", ["symbol", "security_type",
                                               "currency", "position"])


class TestApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        self.positions = []
        self.positions_done = False
        self.available_funds = None
        self.available_funds_currency = None
        self.account_summary_done = False
        self.connection_failed = False
        self.next_request_id = 1000
        self.request_id_to_stock = {}
        self.stocks_collected = set()

    def got_all_stock_info(self):
        need = {p.symbol for p in self.positions if p.security_type == 'STK'}
        got = set(self.stocks_collected)
        logging.info("need: %s, got: %s", need, got)
        return len(need) == len(got)

    def check_if_done(self):
        """Checks whether we received account summary and all positions."""
        if (self.account_summary_done and self.positions_done and
                self.got_all_stock_info()):
            positions = []
            for position in self.positions:
                positions.append({
                    "symbol": position.symbol,
                    "security_type": position.security_type,
                    "currency": position.currency,
                    "position": position.position
                })
            state = {"available_funds": self.available_funds,
                     "available_funds_currency": self.available_funds_currency,
                     "positions": positions}
            print(json.dumps(state))
            self.done = True

    def nextValidId(self, orderId: int):
        """Wrapper implementation."""
        super().nextValidId(orderId)
        # Booting finished and we are getting the next valid ID.
        # 9001 = unique request identifier
        # ask for delayed market data
        self.marketDataType(self.next_request_id, MarketDataTypeEnum.DELAYED)
        self.next_request_id += 1
        self.reqAccountSummary(self.next_request_id,
                               "All",
                               AccountSummaryTags.AllTags)
        self.next_request_id += 1
        self.reqPositions()

    def keyboardInterrupt(self):
        """Wrapper implementation."""
        self.done = True

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        """Wrapper implementation."""
        super().error(reqId, errorCode, errorString)
        if errorCode == CONNECT_FAIL.code():
            logging.error("Connection failed.")
            self.connection_failed = True
        logging.info("Error. Id:%s Code:%s Msg:%s",
                     reqId, errorCode, errorString)

    def accountSummary(self, reqId: int, account: str, tag: str, value: str,
                       currency: str):
        """Wrapper implementation."""
        super().accountSummary(reqId, account, tag, value, currency)
        logging.info("Acct Summary. ReqId:%s Acct:%s Tag:%s Value:%s Currency:%s", reqId, account,
                     tag, value, currency)
        if tag == AccountSummaryTags.AvailableFunds:
            if self.available_funds is not None:
                raise StandardError("received available funds tag twice")
            self.available_funds = value
            self.available_funds_currency = currency

    def accountSummaryEnd(self, reqId: int):
        """Wrapper implementation."""
        super().accountSummaryEnd(reqId)
        logging.info("AccountSummaryEnd. Req Id: %s", reqId)
        self.account_summary_done = True
        self.check_if_done()

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float,
                  attrib: TickAttrib):
        super().tickPrice(reqId, tickType, price, attrib)
        print("Tick Price. Ticker Id:", reqId, " ",
              self.request_id_to_stock[reqId], " tickType:", tickType,
              "Price:", price, "CanAutoExecute:", attrib.canAutoExecute,
              "PastLimit:", attrib.pastLimit, end=' ')
        if tickType == TickTypeEnum.BID or tickType == TickTypeEnum.ASK:
            print("PreOpen:", attrib.preOpen)
        else:
            print()

    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        super().tickSize(reqId, tickType, size)
        print("Tick Size. Ticker Id:", reqId, " ",
              self.request_id_to_stock[reqId],
              "tickType:", tickType, "Size:", size)

    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        super().tickGeneric(reqId, tickType, value)
        print("Tick Generic. Ticker Id:", reqId, " ",
              self.request_id_to_stock[reqId],
              "tickType:", tickType, "Value:", value)

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        super().tickString(reqId, tickType, value)
        print("Tick string. Ticker Id:", reqId, " ",
              self.request_id_to_stock[reqId],
              "Type:", tickType, "Value:", value)

    def tickSnapshotEnd(self, reqId: int):
        super().tickSnapshotEnd(reqId)
        print("TickSnapshotEnd:", reqId, " ",
              self.request_id_to_stock[reqId])
        self.stocks_collected.add(self.request_id_to_stock[reqId])

    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float):
        """Wrapper implementation."""
        super().position(account, contract, position, avgCost)
        logging.info("Position.%s Symbol=%s Type=%s Currency=%s Pos=%s "
                     "AvgCost=%s", account, contract.symbol, contract.secType,
                     contract.currency, position, avgCost)
        position = Position(contract.symbol, contract.secType,
                            contract.currency, position)
        self.positions.append(position)

        if position.security_type == 'STK':
            self.marketDataType(self.next_request_id,
                                MarketDataTypeEnum.DELAYED)
            self.next_request_id += 1

            logging.info("requesting for %s under %d", contract.symbol,
                         self.next_request_id)
            #self.reqMktData(self.next_request_id, contract,
            #                "221,233", snapshot=False, regulatorySnapshot=False,
            #                mktDataOptions=[])
            c = Contract()
            c.symbol = contract.symbol
            c.secType = contract.secType
            c.currency = contract.currency
            c.exchange = contract.exchange
            c.primaryExchange = contract.primaryExchange
            #c.localSymbol = contract.localSymbol
            #c.tradingClass = contract.tradingClass
            #c.secIdType = contract.secIdType
            #c.secId = contract.secId

        #self.lastTradeDateOrContractMonth = ""
        #self.strike = 0.  # float !!
        #self.right = ""
        #self.multiplier = ""
        #self.currency = ""
        #self.includeExpired = False

        #combos
        # type: str; received in open order 14 and up for all combos
        #self.comboLegsDescrip = ""
        #self.comboLegs = None     # type: list<ComboLeg>
        #self.deltaNeutralContract = None

            self.reqMktData(self.next_request_id, c,
                            "", snapshot=False, regulatorySnapshot=False,
                            mktDataOptions=[])
            self.request_id_to_stock[self.next_request_id] = contract.symbol
            self.next_request_id += 1

    def positionEnd(self):
        """Wrapper implementation."""
        super().positionEnd()
        logging.info("PositionEnd")
        self.positions_done = True
        self.check_if_done()


def main():
    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'
    timefmt = '%y%m%d_%H:%M:%S'
    logging.basicConfig(level=logging.INFO, format=recfmt, datefmt=timefmt,
                        filename='/var/log/read_snapshot.log')
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.setFormatter(logging.Formatter(recfmt))
    logging.getLogger('').addHandler(stderr_handler)

    parser = argparse.ArgumentParser("api tests")
    parser.add_argument("-p", "--port", type=int, dest="port",
                        help="The TCP port to use")
    args = parser.parse_args()
    if not args.port:
        print("Please set --port.")
        sys.exit(1)

    while True:
        logging.info("Trying to connect...")
        app = TestApp()
        app.connect("127.0.0.1", args.port, clientId=0)
        if app.connection_failed:
            logging.info("Attempt failed. Try again in 5 s.")
            time.sleep(5)
        else:
            app.run()
            break


if __name__ == "__main__":
    main()
