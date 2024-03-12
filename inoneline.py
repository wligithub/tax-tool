import csv
from datetime import datetime, timedelta

ESPP_DATE_FILE = "data/espp-date.csv"
VMW_PRICE_FILE = "data/vmw-historical-price.csv"

espp_dates = {}
stock_prices = {}

def load_historical_price():
    with open(VMW_PRICE_FILE) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            stock_prices[row[0]] = row[4]


def load_espp_dates():
    with open(ESPP_DATE_FILE) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            espp_dates[row[0]] = row[1]


def get_stock_price(date_str):
    # when date not found in dictionary, lookup previous days
    while date_str not in stock_prices:
        date = datetime.strptime(date_str, "%m/%d/%Y")
        date = date - timedelta(days=1)
        date_str = date.strftime("%m/%d/%Y")

    return float(stock_prices[date_str])


load_espp_dates()
load_historical_price()

for a in espp_dates:
    o = espp_dates[a]
    acquire_date_fmv = get_stock_price(a)
    offer_date_fmv = get_stock_price(o)

    if offer_date_fmv >= acquire_date_fmv:
        print("offer_date=%s, acquire_date=%s, offer_date_fmv=%f, acquire_date_fmv=%f" %
              (o, a, offer_date_fmv, acquire_date_fmv))