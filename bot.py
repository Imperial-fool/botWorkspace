
# Import the requests library 
import enum
import requests, time, os, math, json, decimal,os

from multiprocessing import Process
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

indicator = "rsi","macd","avgprice","fibonacciretracement","dmi","bbands2","adx","mfi","vwap"
api_key = "ATk7OZZQE8wL5MPHg93dlIMRrCRCtkk7cjJqoCfyFnyC7qaZEfQ5Q30FcQdx2E3v" #binance api
api_secret = "lXmPJ46hPjL6B789bMtYspBF7uz6exqh87geI72bFBgJvnJop118ctV6G2gVJERc" #secret here

seconds = time.time()

client = Client(api_key, api_secret)
botlog = open("botlog.txt", "a+")
etf_mod = False
class Bot:
    def __init__(self, coina, coinb, digit, tickSize, indicator, client, index, topbyvolume):
        
        self.index = index
        self.client = client
        self.result = [0]*9
        self.endpoint = [0]*9
        self.pair = coinb +'/'+ coina
        self.bnb_api_pair = coinb + coina
        self.coina = coina
        self.coinb = coinb
        self.digit = float(digit)
        self.totalBuys = 0
        self.totalSells = 0
        self.orders = []
        count = 0
        for i in list(digit):
            if i == "0":
                count += 1
            if i == "1":
                break

        self.decimal_places = count
        count = 0
        self.tickSize = float(tickSize)
        for i in list(tickSize):
            if i == "0":
                count += 1
            if i == "1":
                break
        self.tickSize_decimals = count
        self.buy_price = [0]
        self.sell_price = [0]
        self.profit = 0
        self.profits = []
        self.factor = 0
        self.ava_coina = float(client.get_asset_balance(asset=self.coina)['free'])
        self.ava_coinb = float(client.get_asset_balance(asset='USDT')['free'])
        self.limit_order_buy = []
        self.limit_order_sell = []
        self.isrunning = 0
        self.info_for_gui = [0]*7
        self.old_pd = 0
        self.fib = 0
        self.count = 0
        self.plotcount = 0
        self.backpropWeights = [1]*7
        self.valueOnbuy = [[]]*7
        self.valueOnsell = [[]]*7
        self.pricehistory = []
        self.time = []
        
        self.topbyvolume = topbyvolume

        self.file = open(self.bnb_api_pair+".txt", "a+")
        self.file.write(self.pair+ "time: " + str(time.time())+ "\n")
        self.file.write(json.dumps(topbyvolume,indent = 5, sort_keys=True))
        
        for i,value in enumerate(indicator):
            self.endpoint[i] = f"https://api.taapi.io/{value}"
        self.parameters = {
    'secret': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImNqbW9ycmlzQGxha2VoZWFkdS5jYSIsImlhdCI6MTYyMTAyODIwNCwiZXhwIjo3OTI4MjI4MjA0fQ.2c8K_4Pg1n2xaeZ14AfcOiiUVSsqkIwi6AAwlA43q5s",
    'exchange': 'binance',
    'symbol':self.pair ,
    'interval': '1m',
        }
        self.fib_pram = {
    'secret': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImNqbW9ycmlzQGxha2VoZWFkdS5jYSIsImlhdCI6MTYyMTAyODIwNCwiZXhwIjo3OTI4MjI4MjA0fQ.2c8K_4Pg1n2xaeZ14AfcOiiUVSsqkIwi6AAwlA43q5s",
    'exchange': 'binance',
    'symbol': self.pair,
    'interval': '1m',
    'trend':'smart'
        }
        
        
    def get_apidata(self):
     try:
        for i,value in enumerate(self.endpoint):
            if value == 'https://api.taapi.io/fibonacciretracement':
                response = requests.get(url = value, params = self.fib_pram)
                self.result[i] = response.json()    
            else:
                response = requests.get(url = value, params = self.parameters)
                self.result[i] = response.json()
                
     except:
        print("API error")

    def checkOrders(self):
        try: 
         self.orders = client.get_open_orders(symbol=self.bnb_api_pair)
        except BinanceAPIException as e:
            print(e)

        
        if len(self.orders):   
            print(json.dumps(self.orders,indent=5,sort_keys=True))
            self.file.write(json.dumps(self.orders,indent = 5, sort_keys=True))
            self.file.write("-------")
            
            
            for i in self.orders:

             try:
              bnb_pair = i["symbol"]
              id = i["orderId"]
              result = client.cancel_order(symbol=bnb_pair,orderId=id)
              print(json.dumps(result,indent=5,sort_keys=True))
              self.file.write(json.dumps(result,indent=5,sort_keys=True))
              for j in self.limit_order_buy:
                if i["orderId"]==j["orderId"]:
                    for h in self.buy_price:
                        if float(j["price"]) == h:
                            del h
                    del i
                    del j
                    del self.valueOnbuy[0][-1]
                    del self.valueOnbuy[1][-1]
                    del self.valueOnbuy[2][-1]
                    del self.valueOnbuy[3][-1]
                    del self.valueOnbuy[4][-1]
                    del self.valueOnbuy[5][-1]
                    
              for j in self.limit_order_sell:
                if i["orderId"]==j["orderId"]:
                    for h in self.sell_price:
                        if float(j["askPrice"]) == h:
                            del h
                    del i
                    del j
                    
             except BinanceAPIException as e:
              print(e)
             except BinanceOrderException as e:
              print(e)
             except:
              print("something else went wrong")

             

            
                
   



    def dmi(self):
     if self.result[4]["plusdi"] > self.result[4]["minusdi"] and self.result[4]['adx'] >  self.result[4]["plusdi"] and  self.result[4]['adx'] >   self.result[4]["minusdi"]:
        return 1.5
     if  self.result[4]["adx"] > 20:
        if  self.result[4]["plusdi"] > self.result[4]["minusdi"]:
            if self.fib > 0:
                return 1
            if self.fib < 0:
                return -1
            else:
                return 0
        if  self.result[4]["plusdi"] <  self.result[4]["minusdi"]:
            if self.fib >  0:
                return 1
            if self.fib < 0:
                return -1
            else:
                return 0
        else:
            return 0
     else:
        return 0
    def vwamp(self):
     if self.result[8]['value'] < self.result[2]['value']:
        if self.fib > 0:
            return 1
        else:
            return -1
     else:
        return 0
    def macd(self):
     if abs(self.result[1]["valueMACD"] - self.result[1]["valueMACDSignal"]/self.result[1]['valueMACD']) < 0.005:
        if self.fib > 0:
            return 1
        else:
            return -1
     else:
        return 0
    def rsi(self):
     rsi = round(float(-((2*(self.result[0]['value']/(100-0)))-1)),2) 
     if rsi < 0.2:
         return -1
     if rsi > 0.8:
         return 1
     else:
         return rsi   
    def mfi(self):
     return round(float(-((2*(self.result[7]['value']/(100-0)))-1)),2)   
    def adx(self):
     return round(float((2*(self.result[6]['value'])/(100-0))-1),2)

    #def getslope(self):
    #    if self.old_pd == 0:
    #        self.old_pd = self.result[3]['value']
    #        return 0
    #    else:
    #        self.slope = self.result[3]['value'] - self.old_pd
    #        if self.count % 5 == 0:
    #         self.old_pd = self.result[3]['value']
    #        return 0
    def fibr(self):
        
        if self.result[3]["trend"] == "DOWNTREND":
            self.fib = -1
        else:
            self.fib = 1

    def binance_info(self):
          self.ava_coina = float(client.get_asset_balance(asset=self.coina)['free'])
          self.ava_coinb = float(client.get_asset_balance(asset=self.coinb)['free'])
         
    def getfactor(self):
        if(self.adx() > 0):
            ad = self.adx()
        if(self.adx() < -0.80):
            ad = -1
        else:
            ad = 0
        self.factor = ((self.rsi()*self.backpropWeights[0])+(self.macd()*self.backpropWeights[1])+(self.dmi()*self.backpropWeights[2])+(self.mfi()*self.backpropWeights[3])+(self.vwamp()*self.backpropWeights[4]))*(1+(ad*self.backpropWeights[5]))
        self.info_for_gui[0] = str(self.rsi())
        self.info_for_gui[1] = str(self.macd())
        self.info_for_gui[2] = str(self.dmi())
        self.info_for_gui[3] = str(self.adx())
        self.info_for_gui[4] = str(self.mfi())
        self.info_for_gui[5] = str(self.vwamp())
        self.info_for_gui[6] = str(self.result[2]['value'])

    def quantity(self):
        try:
            priceOfMinQty = self.digit * self.result[2]['value']
            print(priceOfMinQty)
            amountInMinQty = 15/priceOfMinQty
            print(amountInMinQty)
            amountIntotal = round(amountInMinQty * self.digit, self.decimal_places)
            if self.decimal_places == 0:
                amountIntotal = int(amountIntotal)
            print(amountIntotal)
            return amountIntotal
        except:
            print("The oracles have failed...")
            return 0

    def calculateProfit(self):
     size = len(self.limit_order_sell)
     size_buy = len(self.limit_order_buy)
     print(size)
     print(size_buy)
     if size > 0 and size_buy > 0:
         print(self.limit_order_sell)
         print(self.limit_order_buy)
         self.profits.append((float(self.limit_order_sell[-1]["price"]) - float(self.limit_order_buy[-1]["price"]))*float(self.limit_order_sell[-1]["executedQty"]))
         del self.limit_order_sell[-1]
         del self.limit_order_buy[-1]
         self.profit += self.profits[-1]
         print(self.profit)
     

    def buy(self,x):
     try:
            print('the bot is buying...')
            print('Qty: ', x, 'Price: ','%f' % round(self.result[2]['value'],self.tickSize_decimals))
            self.limit_order_buy.append(self.client.order_limit_buy(symbol=self.bnb_api_pair, quantity = '%f' % x, price = '%f' % round(self.result[2]['value'],self.tickSize_decimals)))
            self.buy_price.append(self.result[2]['value'])
            
            self.valueOnbuy[0].append(self.rsi())
            self.valueOnbuy[1].append(self.macd())
            self.valueOnbuy[2].append(self.dmi())
            self.valueOnbuy[3].append(self.mfi())
            self.valueOnbuy[4].append(self.vwamp())
            self.valueOnbuy[5].append(self.adx())
     except BinanceAPIException as e:
            # error handling goes here
                print(e)
     except BinanceOrderException as e:
            # error handling goes here
                print(e)
    def sell(self,x):

     try:
            print('the bot is selling...')
            print('Qty: ', x, 'Price: ',round(self.result[2]['value'],self.tickSize_decimals))
            self.limit_order_sell.append(self.client.order_limit_sell(symbol=self.bnb_api_pair, quantity = '%f' % x, price = '%f' % round(self.result[2]['value'],self.tickSize_decimals)))
            self.sell_price.append(self.result[2]['value'])

            
        
                
     except BinanceAPIException as e:
            # error handling goes here
                print(e)
     except BinanceOrderException as e:
            # error handling goes here
                print(e)

    def binancebot(self):

     upperbound = round(abs((self.result[5]['valueUpperBand'] - self.result[2]['value']) /self.result[5]['valueUpperBand'])*100,2)
     middlebound = round(abs((self.result[5]['valueMiddleBand'] - self.result[2]['value']) /self.result[5]['valueMiddleBand'])*100,2)
     lowerbound = round(abs((self.result[2]['value'] - self.result[5]['valueLowerBand'])/self.result[2]['value'])*100,2)
     
     if upperbound + lowerbound > .5: #if bands are too close together it wont sell
   
         if ((self.factor < 0 and (self.buy_price[-1]*1.03) < self.result[2]['value']) and self.ava_coinb > (10/self.digit*self.result[2]['value'])*self.digit) or (self.factor < -2 and self.ava_coinb > (15/self.result[2]['value'])): #market sell at 1% gain
             self.sell(round(self.ava_coinb - (self.digit*6), self.decimal_places))
             return 0
             
         if (upperbound < 0.5 and (self.fib < 0 or self.factor <= -1) and (self.buy_price[-1]*1.0045 <= self.result[2]['value']) and self.ava_coinb > (15/self.digit*self.result[2]['value'])*self.digit): #sell when near upperband,factor is less than -1 and buy price is over trade fee + 0.025% profit
             self.sell(self.quantity())
             return 0
         if self.buy_price[-1]*0.98 < self.result[2]['value'] and self.ava_coinb > (15/self.digit*self.result[2]['value'])*self.digit and self.fib < 0 and self.factor < 0 : #stop loss
             
             self.sell(self.quantity())
             return 0
     if  self.factor > 1.5 and self.ava_coina >= 15 and upperbound > 1 and self.fib > 0 : 
             
             self.buy(self.quantity())
             return 0
             
     if lowerbound < 0.3 and self.fib > 0 and self.ava_coina >= 15 and self.factor > 0:
             
             self.buy(self.quantity())
             return 0
     return 0

    def info(self):
        try:
            self.binance_info()
        except:
            print('binance api not responding')
        else:
            print(self.pair)
            print('----------------------------------------------------------------------------------------------')
            print('rsi: ',self.info_for_gui[0],'macd: ',self.info_for_gui[1],'dmi: ',self.info_for_gui[2], 'adx:', self.info_for_gui[3],'mfi: ', self.info_for_gui[4],"vwamp:",self.info_for_gui[5])
            print('fib: ', self.fib)
            print("factor value: ",self.factor)
            print("price: ",round(self.result[2]['value'],8))
            print("last buy price: ", self.buy_price[-1])
            if self.buy_price[-1] != 0 :
                print("price change since buy", round(((self.result[2]['value'] - self.buy_price[-1])/self.result[2]['value'])*100,2),'%')
            print("last sell price: ", self.sell_price[-1])
            print('profit: ',self.profit)
            print(self.coina, ' :',self.ava_coina)
            print(self.coinb, ' :',self.ava_coinb)
    def sellall(self):
        if self.ava_coinb > (10/self.result[2]['value']):
         self.sell(round(self.ava_coinb - self.digit, self.decimal_places))
        else:
         print('we start fresh...')
    def backprop(self):
        if self.profits[-1] > 0:
            for w,i in enumerate(self.valueOnbuy):
                if float(i) > 0:
                    self.backpropWeights[w] += 0.01
                if float(i) < 0:
                    self.backpropWeights[w] -= 0.01
                print(self.backpropWeights)
        if self.profits[-1] < 0:
            for w,i in enumerate(self.valueOnbuy):
                print(i)
                if float(i) > 0:
                    self.backpropWeights[w] -= 0.01
                if float(i) < 0:
                    self.backpropWeights[w] += 0.01
                print(self.backpropWeights)
    def mainloop(self):
         self.isrunning = 1
         self.count += 1
         try:
            self.get_apidata()
         except:
            print('issue with get_api')
         try:
            self.binance_info()
         except:
            print('issue with binance_info')
         if self.count != 1:
          self.checkOrders()
         if self.count == 1:
          try:
           print(json.dumps(self.result, indent = 5, sort_keys=True))
           self.buy_price.append(self.result[2]['value'])
          except:
           print("I have no clue?")

         try:
          self.fibr()
         except:
          print("this bot has a problem with fibr: ", self.pair)
         try:
          self.getfactor()
         except:
          print("issue with getfactor()")
         try:
          self.binancebot()
         except:
          print("bot has issue with binancebot()")

         #self.calculateProfit()
         self.info()
         
         
        
         
         self.isrunning = 0
        
topbyvolume = []
custompairs = ['avax'] 

def get_pairs():
   print("consulting oracles...")
   try:
    info = client.get_ticker()
    ticker = []
    usdt_info = []
    print(json.dumps(info, indent=5, sort_keys=True))
    w = -40
    counter = 0
    for e in info:
       
     counter += 1
     if etf_mod == False:
       if e["symbol"].endswith("USDT") and  e["symbol"].startswith("BUSD") == False and e["symbol"].startswith("USDC") == False and e["symbol"].startswith("VEN") == False and e["symbol"].startswith("HCU") == False and e["symbol"].startswith("USD") == False:
           g = e
           if float(g["volume"]) > 0 and float(g["lastPrice"]) > 0 and float(g["count"]) > 200:
            g["volume"] = float(e["lastPrice"])*float(e["volume"])
            usdt_info.append(g)
            print(json.dumps(g, indent = 5, sort_keys=True))
     if etf_mod == True:
       
       if "DOWN" in e["symbol"] or "UP" in e["symbol"] and e["symbol"].endswith("USDT") and e["symbol"] != "SUPERUSDT":
           g = e
           g["volume"] = float(e["lastPrice"])*float(e["volume"])
           if float(g["volume"]) > 0 and float(g["lastPrice"]) > 0:
            usdt_info.append(g)
            print(json.dumps(g, indent = 5, sort_keys=True))
    sorted_usdt = usdt_info
    sorted_usdt = sorted(usdt_info, key=lambda x: x["volume"])
    while w >= -15:
       sorted_usdt[w]["digit"] = client.get_symbol_info(sorted_usdt[w]["symbol"])["filters"][2]["minQty"]
       sorted_usdt[w]["tickSize"] = client.get_symbol_info(sorted_usdt[w]["symbol"])["filters"][0]["tickSize"]
       topbyvolume.append(sorted_usdt[w])
       w -= 1
    print("oracles have reaveled highest volume pairs...")
    botlog.write(json.dumps(topbyvolume,indent=5,sort_keys=True))
   except:
    print("The oracles have been denied visions of the highest volume pairs...")
   time.sleep(60)
   spawnBots()

   



def spawnBots():
   
   for w,i in enumerate(topbyvolume):
    pair = i["symbol"]

    coinb = pair.replace("USDT", "")

    if coinb == 'MATI':
        coinb = 'MATIC'
    coina = 'USDT'
    if coinb != 'STRAT' or 'SUPER':
     print(coinb)
     bots.append(Bot(coina,coinb,i["digit"],i["tickSize"],indicator,client,w+1,i))
     time.sleep(1)
     print("a new bot has appeared!")
   botLoop()

bots = []


def botLoop():
 profit = 0
 seconds = time.time()
 while True:
    for i in bots:
     try:
      i.mainloop()
      counter = 0
      while i.isrunning == 1:
        counter += 1
      counter = 0
      time.sleep(1)
     except ConnectionError as e:
         print(e)
     except BinanceAPIException as e:
         print(e)
     

    
    for i in bots:
         profit = profit + i.profit
         i.profit = 0
      
    print('time running (min) since last epoch:', (time.time() - seconds)/60)
    print('profit: ', profit)
    botlog.write("time running: "+  str(time.time() - seconds) + "\n")
    botlog.write("profit: " + str(profit)+"\n")
    if (time.time() - seconds)/28800 >= 1:
        seconds = time.time()
        for i in bots:
            i.sellall()
            i.file.close
            del i
        get_pairs()


        


get_pairs()


