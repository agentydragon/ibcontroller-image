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
from ibapi.common import TickerId
from ibapi.contract import Contract
from ibapi.errors import CONNECT_FAIL
from ibapi.wrapper import EWrapper

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

    def check_if_done(self):
        """Checks whether we received account summary and all positions."""
        if self.account_summary_done and self.positions_done:
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
        self.reqAccountSummary(9001, "All", AccountSummaryTags.AllTags)
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

    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float):
        """Wrapper implementation."""
        super().position(account, contract, position, avgCost)
        logging.info("Position.%s Symbol=%s Type=%s Currency=%s Pos=%s "
                     "AvgCost=%s", account, contract.symbol, contract.secType,
                     contract.currency, position, avgCost)
        self.positions.append(Position(contract.symbol, contract.secType,
                                       contract.currency, position))

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
            logging.info("Attempt failed. Try again in 10 s.")
            time.sleep(10)
        else:
            app.run()
            break


if __name__ == "__main__":
    main()
