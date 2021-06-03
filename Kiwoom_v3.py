import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
from datetime import datetime
from decimal import Decimal
import data_controller as injector

TR_REQ_TIME_INTERVAL = 0.2


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.opw00018_output()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)
        elif rqname == "OPT10035_req":
            self._OPT10035(rqname, trcode)
        elif rqname == "OPT10015_req":
            self._OPT10015(rqname, trcode, screen_no)


        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
        [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(gubun)
        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))


    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'

        try:
            format_data = format(int(strip_data), ',d')
        except:
            format_data = format(float(strip_data))

        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data


    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

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


    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)
    
    def opw00018_output(self):
      self.opw00018_output = {'single': [], 'multi': []}  

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_earning_rate))
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price,              
    eval_profit_loss_price, earning_rate])

    def _OPT10035(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        
        # for i in range(data_cnt):
        for i in range(100):
            code = self._comm_get_data(trcode, "", rqname, i, "종목코드")
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            diff = self._comm_get_data(trcode, "", rqname, i, "전일대비")
            d1 = self._comm_get_data(trcode, "", rqname, i, "D-1")
            d2 = self._comm_get_data(trcode, "", rqname, i, "D-2")
            d3 = self._comm_get_data(trcode, "", rqname, i, "D-3")
            sum = self._comm_get_data(trcode, "", rqname, i, "합계")

            print(name)
            print(diff)
            print(d1)
            print(d2)
            print(d3)

            # if(d1>0 and d2> 0 and d3>0 and (d1>d3) and diff<0):
            #     print(code)
            #     print(name)
            #     print(diff)

            # if(int(diff)<0):
            #     if(int(d1)>0 & int(d2) >0 & int(d3)):
            #         print(code)
            #         j+=1
                # print(date)
                # print(open)
                # print(high)
                # print(low)
                
                # print(close)
                # print(volume)


            # self.ohlcv['date'].append(date)
            # self.ohlcv['open'].append(int(open))
            # self.ohlcv['high'].append(int(high))
            # self.ohlcv['low'].append(int(low))
            # self.ohlcv['close'].append(int(close))
            # self.ohlcv['volume'].append(int(volume))


    def _OPT10015(self, rqname, trcode, stock_no):
        print(stock_no)
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        print(data_cnt)
        structured_data = []
        for i in range(data_cnt):
        # for i in data_cnt:
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            price = self._comm_get_data(trcode, "", rqname, i, "종가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            diff = self._comm_get_data(trcode, "", rqname, i, "등락율")
            print(f'{date} : {price} / {volume} , {diff}')
            temp = stock_no, datetime.strptime(date, "%Y%m%d"), abs(int(price)), Decimal(diff)
            print(temp)
            structured_data.append(temp)

        injector.insert_data(trcode, structured_data)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]

    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")