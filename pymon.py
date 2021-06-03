from data_controller import retrieve_list
import sys
from PyQt5.QtWidgets import *
import Kiwoom_v3 as Kiwoom
import time
from pandas import DataFrame
import datetime

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

class PyMon:
    def __init__(self):
        self.kiwoom = Kiwoom.Kiwoom()
        self.kiwoom.comm_connect()
        self.get_code_list()

    def get_code_list(self):
        self.kospi_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSPI)
        self.kosdaq_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSDAQ)

    def get_ohlcv(self, code, start):
        self.kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        time.sleep(0.2)

        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'],
                       index=self.kiwoom.ohlcv['date'])
        return df


    def retrieveForeignerTrading(self): 
        try:
            self.kiwoom.set_input_value("시장구분", "000")
            self.kiwoom.set_input_value("매매구분", "2")
            self.kiwoom.set_input_value("기준일구분", "0")
            self.kiwoom.comm_rq_data("OPT10035_req", "OPT10035", "0", "2000")
        except Exception as e:
            print(e)

    def checkTradingDetail(self, stock_no): 
        try:
            self.kiwoom.set_input_value("종목코드", stock_no)
            # self.kiwoom.set_input_value("시작일자", "20210501")
            self.kiwoom.comm_rq_data("OPT10015_req", "OPT10015", "0", stock_no)
        except Exception as e:
            print(e)

    def check_speedy_rising_volume(self, code):
        today = datetime.datetime.today().strftime("%Y%m%d")
        df = self.get_ohlcv(code, today)
        volumes = df['volume']

        if len(volumes) < 21:
            return False

        sum_vol20 = 0
        today_vol = 0

        for i, vol in enumerate(volumes):
            if i == 0:
                today_vol = vol
            elif 1 <= i <= 20:
                sum_vol20 += vol
            else:
                break

        avg_vol20 = sum_vol20 / 20
        if today_vol > avg_vol20 * 10:
            return True

    def update_buy_list(self, buy_list):
        f = open("buy_list.txt", "wt")
        for code in buy_list:
            f.writelines("매수;", code, ";시장가;10;0;매수전")
        f.close()

    def run(self):
        stock_list = retrieve_list()
        
        for item in list(stock_list):
            self.checkTradingDetail(item[0])
            time.sleep(5)
        # self.retrieveForeignerTrading()

    # def run(self):
    #     buy_list = []
    #     num = len(self.kosdaq_codes)
    #     j=0
    #     print(self.kosdaq_codes)
    #     for i, code in enumerate(self.kosdaq_codes):
    #         print(i, '/', num)
    #         if(j==10): 
    #             break
    #         if self.check_speedy_rising_volume(code):
    #             buy_list.append(code)
    #         j+=1

    #     self.update_buy_list(buy_list)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pymon = PyMon()
    pymon.run()