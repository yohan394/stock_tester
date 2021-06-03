from typing import Tuple
import pymysql
from datetime import datetime
import pandas as pd



def insert_data(stock_no, data):
    conn = pymysql.connect(host='localhost', user='root', password='1!2@', db='stock', charset='utf8')
    curs = conn.cursor()
    sql = """INSERT INTO data (stock_no, stock_date, price, diff) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE diff = VALUES(diff)"""
    
    curs.executemany(sql, data)
    conn.commit()
    conn.close()

def retrieve_list():
    conn = pymysql.connect(host='localhost', user='root', password='1!2@', db='stock', charset='utf8')
    curs = conn.cursor()
    sql = """SELECT * FROM  info"""
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    
    return rows

def insert_stocks():
    a = pd.read_csv('data2.csv')
    data = []
    for i in range(len(a)):
        stock_no = str(a['종목코드'][i])
        if len(stock_no) == 5:
            stock_no = "0" + stock_no
        elif len(stock_no) == 4:
            stock_no = "00" + stock_no
        elif len(stock_no) == 3:
            stock_no = "000" + stock_no
        elif len(stock_no) == 2:
            stock_no = "0000" + stock_no
        elif len(stock_no) == 1:
            stock_no = "00000" + stock_no
        temp = stock_no, a['종목명'][i], a['상장시가총액(원)'][i]
        data.append(temp)
    

    conn = pymysql.connect(host='localhost', user='root', password='1!2@', db='stock', charset='utf8')
    curs = conn.cursor()
    sql = """INSERT INTO info (stock_no, name, total_val) values (%s, %s, %s) ON DUPLICATE KEY UPDATE total_val = VALUES(total_val)"""
    curs.executemany(sql, data)
    conn.commit()
    conn.close()

insert_stocks()