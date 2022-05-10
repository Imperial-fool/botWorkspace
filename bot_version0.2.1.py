
import EmailModule as emod
#These normally everyone has
import requests,time,math,json,os,csv
from os.path import exists as file_exists
from multiprocessing import Process, Array
from multiprocessing import Value as Value_mp

#I follow the path of luck
import quantumrandom


#binance lib
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

indicator = "rsi","macd","avgprice","fibonacciretracement","dmi","bbands2","adx","mfi","vwap"
api_key = "" #binance api
api_secret = "" #secret here

seconds = time.time()
amountofpairs = 25


#globalish variables 
client = Client(api_key, api_secret)

etf_mod = False


class Bot:
    def __init__(self, coina, coinb, digit, tickSize, indicator, client, index, topbyvolume):
        self.resignal = 0
        self.fieldname = ["Order_Id", "Price", "Qty", "Pair", "Side", "Removed", "Profit", "Time"]
        self.index = index
        self.client = client
        self.result = [0]*9
        self.endpoint = [0]*9
        self.pair = coinb +'/'+ coina
        self.bnb_api_pair = coinb + coina
        i = client.get_trade_fee(symbol=self.bnb_api_pair)
        self.fee = float(i[0]['makerCommission'])*15
        self.coina = coina
        self.coinb = coinb
        self.digit = float(digit)
        self.totalBuys = 0
        self.totalSells = 0
        self.orders = []
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
        self.fib = 0
        self.luck = 0
        self.count = 0
        self.plotcount = 0
        self.backpropWeights = [1]*6
        self.indicators = ["rsi", "macd", "dmi", "mfi", "adx", "vwamp"]
        self.valueOnbuy = [0],[0],[0],[0],[0],[0]
        self.valueOnsell = []*6
        self.pricehistory = []
        self.time = []

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
        
        #save info on bot run time and start info
        self.file = open('log/'+self.bnb_api_pair+".txt", "a+")
        self.file.write(self.pair+ "time: " + str(time.time())+ "\n")
        self.file.write(json.dumps(topbyvolume,indent = 5, sort_keys=True))
        self.file.close
        #checks for backprop weights saved in json file, if it does not exist creates a file and writes base info
        if file_exists('json/'+self.bnb_api_pair+'.json') == True:
            with open('json/'+self.bnb_api_pair+'.json', 'r') as backprops:
                content = json.load(backprops)
                for j,i in enumerate(content):
                    if 'last_buy' in i: 
                        self.buy_price[0] = i["last_buy"]
                    elif 'last_sell' in i:
                        self.sell_price[0] = i['last_sell']
                    else:
                        self.backpropWeights[j] = i['weight']
                
                
                backprops.close()
        else:
            self.save()
        #taapi stuff this mostly works with no issue
        for i,value in enumerate(indicator):
            self.endpoint[i] = f"https://api.taapi.io/{value}"
        self.parameters = {
    'secret': "",
    'exchange': 'binance',
    'symbol':self.pair ,
    'interval': '1m',
        }
    #fix this damn thing eventually...
        self.fib_pram = {
    'secret': "",
    'exchange': 'binance',
    'symbol':self.pair,
    'interval': '1m',
    'trend':'smart'
        }

    #save backprop values
    #adding save last buy/sell (june 18 2021)
    def save(self):
        dic = list() 
        for i in self.backpropWeights:
            dic.append({"weight":i})
        dic.append({"last_buy":self.buy_price[-1]})
        dic.append({"last_sell":self.sell_price[-1]})

            
        with open('json/'+self.bnb_api_pair+'.json', 'w') as backprops:
            json.dump(dic,backprops)
            backprops.close()
    #taapi get
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
    #check if orders are still active if true, cancels orders
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
              #checks buy orders and compares them to active orders
              for j in self.limit_order_buy:
                if i["orderId"]==j["orderId"]:
                    data = []
                    for row in writeTocsv('r',self.bnb_api_pair):
                        data.append(row)
                    writeTocsv('w',self.bnb_api_pair,data,i['orderId'])
                    for h in self.buy_price:
                        if float(j["price"]) == h:
                            del h
                    del i
                    del j
                    #this is for backprop so values that werent used for buy and sell effect results
                    del self.valueOnbuy[0][-1]
                    del self.valueOnbuy[1][-1]
                    del self.valueOnbuy[2][-1]
                    del self.valueOnbuy[3][-1]
                    del self.valueOnbuy[4][-1]
                    del self.valueOnbuy[5][-1]
              #checks sell orders and compares to active orders
              for j in self.limit_order_sell:
                if i["orderId"]==j["orderId"]:
                    writeTocsv('w',self.bnb_api_pair,writeTocsv('r',self.bnb_api_pair),i['orderId'])
                    for h in self.sell_price:
                        if float(j["askPrice"]) == h:
                            del h
                    del i
                    del j
             #binance exceptions, look into documentation about other possible exceptions     
             except BinanceAPIException as e:
              print(e)
             except BinanceOrderException as e:
              print(e)
             except ConnectionError as e:
              self.resignal = 1
              print(e)
             except:
              print("something else went wrong")

    #factor logic
    def rand(self):
        self.luck = float(quantumrandom.randint(-0.5, 0.5))
        print("are you feeling luck, this is what the oracle says: ", self.luck)

    def dmi(self):
     if self.result[4]["plusdi"] > self.result[4]["minusdi"] and self.result[4]['adx'] >  self.result[4]["plusdi"] and  self.result[4]['adx'] >   self.result[4]["minusdi"]:
        return 1
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
         return 0   
    def mfi(self):
     mfi = round(float(-((2*(self.result[0]['value']/(100-0)))-1)),2) 
     if mfi < 0.2:
         return -1
     if mfi > 0.8:
         return 1
     else:
         return mfi   
    def adx(self):
     return round(float((2*(self.result[6]['value'])/(100-0))-1),2)

    def fibr(self):
        
        if self.result[3]["trend"] == "DOWNTREND":
            self.fib = -1
        else:
            self.fib = 1

    def binance_info(self):
          self.ava_coina = float(client.get_asset_balance(asset=self.coina)['free'])
          self.ava_coinb = float(client.get_asset_balance(asset=self.coinb)['free'])
         
    def getfactor(self):
        self.rand()
        adx = self.adx()
        if(adx > 0.8):
            ad = 1
        if(adx < -0.80):
            ad = -1
        if(adx > 0):
            ad = adx
        else:
            ad = 0
        self.factor = ((self.rsi()*self.backpropWeights[0])+(self.macd()*self.backpropWeights[1])+(self.dmi()*self.backpropWeights[2])+(self.mfi()*self.backpropWeights[3])+(self.vwamp()*self.backpropWeights[4])+self.luck)*(1+(ad*self.backpropWeights[5]))
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
            if self.decimal_places == 0:
                amountIntotal = int(amountInMinQty*self.digit)
                return amountIntotal
            amountIntotal = round_decimals_down(amountInMinQty * self.digit, self.decimal_places)
            
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
         self.profits.append(((float(self.limit_order_sell[-1]["price"]) - float(self.limit_order_buy[-1]["price"]))*float(self.limit_order_sell[-1]["executedQty"])))
         self.profits[-1] -= self.fee*2
         info = writeTocsv('r',self.bnb_api_pair)
         print(info)
         writeTocsv('w',self.bnb_api_pair,info,self.limit_order_sell[-1]['orderId'],self.profits[-1])

         del self.limit_order_sell[-1]
         del self.limit_order_buy[-1]
         self.profit = sum(self.profits)
         self.backprop(self.profits[-1])
         print(self.profit)
     

    def buy(self,x):
     try:
         if x > 0:
            print('Qty: ', x, 'Price: ','%f' % round(self.result[2]['value'],self.tickSize_decimals))
            self.limit_order_buy.append(self.client.order_limit_buy(symbol=self.bnb_api_pair, quantity = '%f' % x, price = '%f' % round(self.result[2]['value'],self.tickSize_decimals)))
            self.buy_price.append(self.result[2]['value'])
            #need binance docs, get data from limit order placement then export wanted data to csv file, (price, qty, time, order id)
            dic ={"Order_Id":self.limit_order_buy[-1]["orderId"],
                   "Price":self.limit_order_buy[-1]["price"],
                   "Qty":self.limit_order_buy[-1]["origQty"],
                   "Pair":self.limit_order_buy[-1]["symbol"],
                   "Side":"Buy",
                   "Removed": "False",
                   "Profit":"",
                   "Time":self.limit_order_buy[-1]['transactTime']}
            
            writeTocsv("a+",self.bnb_api_pair,dic)       


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
          if x > 0:
            print('Qty: ', x, 'Price: ',round(self.result[2]['value'],self.tickSize_decimals))
            self.limit_order_sell.append(self.client.order_limit_sell(symbol=self.bnb_api_pair, quantity = '%f' % x, price = '%f' % round(self.result[2]['value'],self.tickSize_decimals)))
            self.sell_price.append(self.result[2]['value'])
            #need binance docs, export same data as above. in addition to a simple profit calc
            dic ={"Order_Id":self.limit_order_sell[-1]["orderId"],
                   "Price":self.limit_order_sell[-1]["price"],
                   "Qty":self.limit_order_sell[-1]["origQty"],
                   "Pair":self.limit_order_sell[-1]["symbol"],
                   "Side":"Sell",
                   "Removed": "False",
                   "Profit":"",
                   "Time":self.limit_order_sell[-1]['transactTime']}
            
            writeTocsv("a+",self.bnb_api_pair,dic) 
                
     except BinanceAPIException as e:
            # error handling goes here
                print(e)
     except BinanceOrderException as e:
            # error handling goes here
                print(e)

    def binancebot(self):
     amount_in_usd = self.ava_coinb*self.result[2]['value']
     if self.factor <= -2 and 11 <= amount_in_usd: 
             self.sell(self.quantity())
             return 0
             
     if self.ava_coina >= 15 and (self.factor >= 2):
             self.buy(self.quantity())
             return 0

     return 0

    def info(self):
        try:
            self.binance_info()
        except Exception as e:
            print(e)
            emod.error_report(str(e),'binance api not responding')
            print('binance api not responding')
        else:
            print(self.pair)
            print('----------------------------------------------------------------------------------------------')
            print('rsi: ',self.info_for_gui[0] ,'(',self.backpropWeights[0],')','macd: ',self.info_for_gui[1],'(',self.backpropWeights[1],')','dmi: ',self.info_for_gui[2],'(',self.backpropWeights[2],')', 'adx:', self.info_for_gui[3],'(',self.backpropWeights[3],')','mfi: ', self.info_for_gui[4],'(',self.backpropWeights[4],')',"vwamp:",self.info_for_gui[5],'(',self.backpropWeights[5],')')
            print('fib: ', self.fib)
            print("factor value: ",self.factor)
            print("price: ",round(self.result[2]['value'],8))
            print("last buy price: ", self.buy_price[-1])
            if self.buy_price[-1] != 0 :
                try:
                 print("price change since buy", round(((self.result[2]['value'] - self.buy_price[-1])/self.result[2]['value'])*100,2),'%')
                except:
                 print('issue with price change')
            print("last sell price: ", self.sell_price[-1])
            print('profit: ',self.profit)
            print(self.profits)
            print(self.coina, ' :',self.ava_coina)
            print(self.coinb, ' :',self.ava_coinb)

    def sellall(self):
        if self.ava_coinb > (10/self.result[2]['value']):
         self.sell(round(self.ava_coinb - self.digit, self.decimal_places))
        else:
         print('we start fresh...')
    def setClient(self):
        self.client = Client(api_key, api_secret)
    #look into this, not working right
    def backprop(self,p:float):
     if len(self.valueOnbuy[1]) > 0:
        l = 0
        for w,i in enumerate(self.valueOnbuy):
            print(i)
            j = float(i[-1])
            if p > 0:
                expected = 1
            elif p < 0:
                expected = -1
            elif p == 0.0 or p == -0.0:
                expected = 0
            else: 
                break
            print(i[-1], ": value on buy")
            transfer_dir = j*(1.0*j)
            print(transfer_dir, ": transfer dir")
            error = (expected - j) * transfer_dir
            print(error, ": error")
            if error > 0 and expected == -1:
                if j < 0:
                    l = 0.01 * (error*10)
                if j > 0:
                    l = -0.01 * (error*10)
            elif error > 0 and expected == 1:
                if j > 0:
                    l = 0.01 * (error*10)
                if j < 0:
                    l = -0.01 * (error*10)
            if 2 > self.backpropWeights[w] > 0.5:
                self.backpropWeights[w] += l
                print(self.backpropWeights[w], ": backprop weight \n")
        
        self.save()

    def mainloop(self):
         self.isrunning = 1
         self.count += 1
         if self.count % 10 == 0:
            self.setClient() 
         try:
            self.get_apidata()
         except Exception as e:
            print(e)
            print("issue with get_apidata()")
            emod.error_report(str(e)," issue with get_apidata() ", self.result)
            time.sleep(30)
            self.isrunning = 0
            return 1
         try:
            self.binance_info()
         except Exception as e:
            print(e)
            print("issue with binance api")
            emod.error_report(str(e),"issue with binance api")
         if self.count != 1:
          try:
           self.checkOrders()
          except ConnectionError as e:
            print(e)
            self.resignal = 1
            print("connection error in checkorders")
            emod.error_report(str(e),"connection error in checkorders")
     

         try:
          self.fibr()
         except Exception as e:
          print("this bot has a problem with fibr: ", self.pair)
          print(e)
          emod.error_report(str(e))
         try:
          self.getfactor()
         except Exception as e:
          print("error with getfactor()")
          print(e)
          emod.error_report(str(e)," error with getfactor()")
          
         try:
          self.binancebot()
         except Exception as e:
          print(e)
          emod.error_report(str(e)," bot has issue with binancebot()")
          print("bot has issue with binancebot()")

         self.calculateProfit()
         self.info()
         
         self.isrunning = 0

    

#searches top pairs by volume then sends values to spawnbots func after sorting
def get_pairs():
    
    print("consulting oracles...")
    info = client.get_ticker()
    usdt_info = []
    topby = []  
    w = 0
    counter = 0
    for e in info:
       
     counter += 1

     #etf modifer for determining pairs that will be used

     if etf_mod == False:
      pair = e["symbol"]

      coinb = pair.replace("USDT", "")
      count = int(e["count"])
      if count > 10000:
       if e["symbol"].endswith("USDT") and  e["symbol"].startswith("BUSD") == False and e["symbol"].startswith("USDC") == False and e["symbol"].startswith("VEN") == False and e["symbol"].startswith("HCU") == False and e["symbol"].startswith("USD") == False and 'DOWN' not in e['symbol'] and 'UP' not in e['symbol'] and 'USD' not in coinb and 'STRAT' not in coinb and e["symbol"] != "EURUSDT" and 'COS' not in coinb:
           g = e
           if float(g["volume"]) > 0 and float(g["lastPrice"]) > 0 and float(g["count"]) > 200:
            g["volume"] = float(e["lastPrice"])*float(e["volume"])
            usdt_info.append(g)

     if etf_mod == True:
       
       if "DOWN" in e["symbol"] or "UP" in e["symbol"] and e["symbol"].endswith("USDT") and e["symbol"] != "SUPERUSDT" :
           g = e
           g["volume"] = float(e["lastPrice"])*float(e["volume"])
           if float(g["volume"]) > 0 and float(g["lastPrice"]) > 0:
            usdt_info.append(g)

    sorted_usdt = sorted(usdt_info, key=lambda x: x["volume"])
    while w >= -(amountofpairs - 1):
       print(sorted_usdt[w]['symbol'], ',', sorted_usdt[w]['count'])
       volume = float(e["lastPrice"])*float(e["volume"])
       print("average value per trade: ",volume/float(sorted_usdt[w]['count']))
       for i in client.get_symbol_info(sorted_usdt[w]["symbol"])["filters"]:
           if i["filterType"] == "LOT_SIZE":
                sorted_usdt[w]["digit"] = i["minQty"]
           if i["filterType"] == "PRICE_FILTER":
                sorted_usdt[w]["tickSize"] = i["tickSize"]
       topby.append(sorted_usdt[w])
       w -= 1
    print("oracles have reaveled highest volume pairs...")
    for i in topby:
        print(i['symbol'])
    bots = []
    for w,i in enumerate(topby):
        pair = i["symbol"]

        coinb = pair.replace("USDT", "")
        coina = 'USDT'
        if w == 0 and coinb != 'BTC':
            continue
        if coinb != 'SUPER' and coinb != 'EUR':
            bots.append(Bot(coina,coinb,i["digit"],i["tickSize"],indicator,client,w+1,i))
            print("a new bot has appeared!")
    return bots   
def botLoop(check,buy_sell,print_items,buys,sells,account_value, restart):
 bot = get_pairs()
 seconds = time.time()
 print('starting bots')
 time.sleep(30)
 while True:
   
    for w,i in enumerate(bot):
     
      
      
      i.mainloop()
      counter = 0
      #simplest Implementation of wait; without for loop runs uninterrupted
      while i.isrunning == 1:
        counter += 1 #this literally does nothing, probably could just remove
      counter = 0
      if i.resignal == 1:
          restart.value = 1
      if w == 0:
          account_value.value += i.ava_coina
      account_value.value += i.ava_coinb * float(i.result[2]['value'])
      b = buy_sell.value
      bs = b.decode()
      
      buys.value += i.totalBuys
      sells.value += i.totalSells
      if i.coinb in bs:
        if "Buy" in bs:
         coina_val = i.ava_coina
         print(coina_val)
         if coina_val >= 15:
          j = i.quantity()
          i.buy(j)
          w = ""
          buy_sell.value = w.encode()
        if "Sell" in bs:
         coinb_val = i.ava_coinb
         print(coinb_val)
         if coinb_val > 0:
          i.sell(i.ava_coinb)
          w = ""
          buy_sell.value = w.encode()
    
    profit_compute(bot,seconds,check, buys,sells,account_value)
    dust_collector(bot)

    account_value.value = 0
    buys.value = 0
    sells.value = 0

    if print_items.value == 1:
        s = ''
        for i in bot:
            if bot[-1] != i:
                s += (i.pair+",")
            else:
                s += (i.pair)
            with open('graphinfo.txt','w') as file:
                file.write(s)
        emod.custom_message(s)
        print_items.value = 0
        print(print_items.value)

#stolen round down function, made one before but this was here for the taking plus i lost my old code base

def dust_collector(bots:list):
    if bots[0].count % 256 == 0: #this should be a function if it works!
        account_info = client.get_account()
        to_be_dusted = ''
        print(len(to_be_dusted))
        for i in account_info['balances']:
            if float(i['free']) > 0 and 'BNB' not in i['asset'] and 'USDT' not in i['asset']:
                print(i)
                avg_dic = client.get_avg_price(symbol=(i['asset']+'USDT'))
                print(avg_dic)
                price = float(avg_dic['price'])
                free = float(i['free'])
                print(price)
                if 10 > free*price > 0.0000001:
                    if len(to_be_dusted) == 0:
                     to_be_dusted += i['asset']
                    else:
                     to_be_dusted += (','+i['asset'])
                     
        print(to_be_dusted)
        if len(to_be_dusted) > 0:
            transfer = client.transfer_dust(asset= to_be_dusted)
            print(transfer)
        
        time.sleep(60)
def profit_compute(bots,seconds:float,check, buys,sells,account_value):
    
    profit = 0
    print('profit')
    for i in bots:
         profit = profit + i.profit
      
    print('time running (min) since last epoch:', (time.time() - seconds)/60)
    print('profit: ', profit)
    with open("log/botlog.txt", "a+") as botlog:
        botlog.write("time running: "+  str(time.time() - seconds) + "\n")
        botlog.write("profit: " + str(profit)+"\n")
        botlog.close
    
    if bots[0].count % 80 == 0 or check.value == 1:
        check.value = 0
        emod.checkin(profit,seconds,buys.value,sells.value,account_value)


def startUpcheck():
    if os.path.isdir("log") == False:
        os.mkdir("log")
    if os.path.isdir("csv") == False:
        os.mkdir("csv")
    if os.path.isdir("json") == False:
        os.mkdir("json")
def start_process():
    #shared memory
    check_in_on_next = Value_mp('i', 0)
    buy_sell_arr = Array("c", 10)
    shutdown = Value_mp('i',0)
    restart = Value_mp('i',0)
    print_items = Value_mp('i',0)
    account_value = Value_mp('d', 0.0)
    buys = Value_mp('i', 0)
    sells = Value_mp('i', 0)
    
    p = Process(target=emod.emailcontroller, args=[check_in_on_next,shutdown,restart,buy_sell_arr,print_items])
    botProcess = Process(target=botLoop, args=[check_in_on_next,buy_sell_arr,print_items,buys,sells,account_value, restart])
    p.daemon = True
    botProcess.daemon = True

    
    p.start()
    botProcess.start()
    while True:
        if shutdown == 1:
            p.kill()
            botProcess.kill()
            emod.custom_message("Processes have been killed")
            exit()
        if restart == 1:
            p.kill()
            botProcess.kill()
            p.start()
            botProcess.start()
            emod.custom_message("Succesful restart")
            restart = 0
        time.sleep(1800)
            
def writeTocsv(writerHead:str, name:str ,Data = None, ObjectId = None, Profit = None):
        file = os.path.isfile('csv/'+name+".csv")
        if writerHead == "r" and Data == None and file:
            with open('csv/'+name+'.csv') as csv_file:
                reader = csv.DictReader(csv_file)
                data = []
                linecount = 0
                for row in reader:
                    if linecount == 0:
                        continue
                    data.append(row)
                    print(data)
                    linecount += 1
                csv_file.close
                return data
        else:
            #["Order Id", "Price", "Qty", "Pair", "Side", "Removed", "Profit", "Time"]
            with open('csv/'+name+'.csv',writerHead, newline='') as csv_file:
                if writerHead == "a+":
                    writer = csv.writer(csv_file)
                    if not file:
                        writer.writerow(Data.keys())
                    writer.writerow(Data.values())
                if writerHead == "w" and ObjectId != None and file:
                    print(Data)
                    linecount = 0
                    for row in Data:
                        print(row)
                        if Profit == None:
                            if row['Order_Id'] == ObjectId:
                                row['Removed'] = 'True'
                        else:
                            if row['Order_Id'] == ObjectId:
                                row['Profit'] = Profit
                        writer = csv.writer(csv_file)
                        writer.writerow(row)
                        linecount += 1
                csv_file.close
        
def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor      
                     


if __name__ == '__main__':
    startUpcheck()
    start_process()

    
 
    


