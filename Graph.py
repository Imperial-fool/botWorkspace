
import csv
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
from os.path import exists as file_exists
import requests
import math


endpoint = "https://api.taapi.io/candle"
fieldname = ["Order Id", "Price", "Qty", "Pair", "Side", "Removed", "Profit","Time"]
global first_loop
first_loop = True
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    html.Div([
        html.H4('Bot Live Feed'),
        dcc.Graph(id='live-update-graph',style={'width': '200vh', 'height': '250vh'}),

        dcc.Interval(
            id='interval-component',
            interval=60*1000, # in milliseconds
            n_intervals=0
        )
    ])
)
global counter
counter = 0
with open('graphinfo.txt', 'r') as file:
        s = file.read()
        listofPairs = s.split(',')
file.close



data = []

# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))

def update_graph_live(n):
    
    buy_sell_data = []

    # Collect some data
    global first_loop
    if first_loop == True:
        for i in listofPairs:
            result = get_apidata(i,1)
            print(result)
            l = {
                    'open':[],
                    'close':[],
                    'high':[],
                    'low':[],
                    'time':[],
                    'epochTime':[],
                    'name':i
                }
            for i in reversed(result):
                
                open = i['open']
                close = i['close']
                low = i['low']
                high = i['high']
                time = i['timestampHuman']
                human_time = time[10:-18]
                l['open'].append(open)
                l['close'].append(close)
                l['low'].append(low)
                l['high'].append(high)
                l['time'].append(human_time)
                l['epochTime'].append(i['timestamp'])
            data.append(l)
            first_loop = False
    else:
        for w,i in enumerate(listofPairs):
            result = get_apidata(i)
            if len(data[w]['time']) > 20:
                del data[w]['time'][0]
            time = result['timestampHuman']
            epoch = result['timestamp']
            human_time = time[10:-18]
            data[w]['open'].append(result['open'])
            data[w]['close'].append(result['close'])
            data[w]['low'].append(result['low'])
            data[w]['high'].append(result['high'])
            data[w]['time'].append(human_time)
            p = i.replace('/','')
            info = writeTocsv(p)
            print(info)
            if info != None:
                for row in info:
                    j = {
                        "symbol":i,
                        "time":[],
                        "price":[],
                        "side":[],
                        "removed":[]
                    }
                    t_o = int(row['Time'])
                    time_range = list(range(t_o,t_o+60))
                    print(time_range)
                    if time_range in data[w]['epochTime']:
                        j['time'].append(epoch)
                        j['price'].append(row[' Price'])
                        j['side'].append(row[' Side'])
                        j['removed'].append(row[' Removed'])

                        buy_sell_data.append(j)
                
            



       


        

    # Create the graph with subplots
    columns = int(math.sqrt(len(listofPairs)))-2 
    lines = int(math.ceil(len(listofPairs) / columns))+2
    print(lines)
    print(columns)

    
        
    fig = make_subplots(rows=lines, cols=columns)

    print(len(data))
    
    for l,i in enumerate(data):
        
        col = (l % columns) + 1
        row = (l // columns) + 1
        print(row)
        print(col)
        print('\n')
        fig.add_trace(go.Candlestick(
        x=i['time'],
        open=i['open'],
        high=i['high'],
        low=i['low'],
        close=i['close']
        ),
        col = col,
        row = row)
        buylist_x =[]
        buylist_y =[]
        selllist_x = []
        selllist_y = []
        for q in buy_sell_data:
            if q['symbol'] == i['name']:
                if q['Side'] == 'Buy':
                    buylist_x.append(q['time'])
                    buylist_y.append(q['price'])
                if q['Side'] == 'Sell':
                    selllist_x.append(q['time'])
                    selllist_y.append(q['price'])
        fig.add_trace(go.Scatter(x = buylist_x,y=buylist_y), row = row, col= col)
        fig.add_trace(go.Scatter(x = selllist_x,y=selllist_y), row = row, col = col)

        fig.update_yaxes(title_text=i['name'], row=row, col=col)
        
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(showlegend = False, autosize = True, margin_l = 1.2, margin_r = 1.2, margin_t = 0.1, margin_b = 0.1)  
    
    return fig

def get_apidata(pair:str ,backtrack = None):
     try:
        if backtrack == None and pair != '':
            parameters = {
    'secret': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImNqbW9ycmlzQGxha2VoZWFkdS5jYSIsImlhdCI6MTYyMTAyODIwNCwiZXhwIjo3OTI4MjI4MjA0fQ.2c8K_4Pg1n2xaeZ14AfcOiiUVSsqkIwi6AAwlA43q5s",
    'exchange': 'binance',
    'symbol':pair ,
    'interval': '1m'
        }

            response = requests.get(url = endpoint, params = parameters)
            result = response.json()  
            return result
        elif pair != '':
            
            parameters = {
    'secret': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImNqbW9ycmlzQGxha2VoZWFkdS5jYSIsImlhdCI6MTYyNjEyODkzMSwiZXhwIjo3OTMzMzI4OTMxfQ.ZRjn9WHm-bVsHhMkGp5nlV9yYoDfql6gS9wAf0-n0g8",
    'exchange': 'binance',
    'symbol': pair,
    'interval': '1m',
    'backtracks': '10'
        }
            response = requests.get(url = endpoint, params = parameters)
            result = response.json() 
            return result
       
     except:
        print("API error")

def writeTocsv(name:str):
    if file_exists('csv/'+name+".csv"):
        with open('csv/'+name+'.csv') as csv_file:
            reader = csv.DictReader(csv_file)
            data = []
            for row in reader:
                data.append(row)
                print(data)
            csv_file.close
            return data

if __name__ == '__main__':
    app.run_server(host = '0.0.0.0', port = 5000, debug=True)