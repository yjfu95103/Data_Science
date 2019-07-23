# coding:utf-8
from flask import Flask, render_template,Response,jsonify,request
import numpy as np
import pandas as pd
import json
import sys
import pickle
import plotly
import geocoder
import plotly.graph_objs as go

mapbox_access_token = 'pk.eyJ1IjoiendoaXRleSIsImEiOiJjandjODZxcG0wYmtoM3puNWV1Znk4bnJpIn0.lwm7J6niQyBpEsopsl-QMg'

all_data = pd.read_csv('a_lvr_land_a.csv')
all_data = all_data.drop([0])
all_data = all_data[all_data['交易標的'] != '土地']
all_data = all_data.dropna(subset=['單價元平方公尺'])
all_data['車位數'] = all_data['交易筆棟數'].str.split('車位',expand=True)[1]
all_data['車位類別'].fillna(value='無',inplace=True)
all_data = all_data.astype(
    {'建物現況格局-房':'int32',
    '建物現況格局-廳':'int32',
    '建物現況格局-衛':'int32',
    '總價元':'int32',
    '單價元平方公尺':'float32'
    })
district = list(all_data['鄉鎮市區'].unique())
total_sell = {}
for i in district:
        total_sell[i] = all_data[all_data['鄉鎮市區'] == i]['鄉鎮市區'].count()
try:
    with open('pos.pkl','rb') as f:
        pos = pickle.load(f)
except FileNotFoundError:
    pos = {}


app = Flask(__name__)

def create_plot():
    data = [
        go.Pie(
            labels=list(total_sell.keys()), # assign x as the dataframe column 'x'
            values=list(total_sell.values())
        )
    ]
    layout = go.Layout(
    autosize=False,
    width=300,
    height=300,
    margin=go.layout.Margin(
        l=20,
        r=20,
        b=20,
        t=20,
        pad=4
    ),

    )
    fig = go.Figure(data=data, layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def getData(filter):
    r = all_data
    if filter['district'] != 'All':
        r = r[(all_data['鄉鎮市區'] == filter['district'])]
    if filter['price_low'] < filter['price_high']:
        r = r[(r['總價元'] >= filter['price_low']) & (r['總價元'] <= filter['price_high'])]
    if filter['room_count_low'] < filter['room_count_high']:
        r = r[(r['建物現況格局-房'] >= filter['room_count_low']) & (r['建物現況格局-房'] <= filter['room_count_high'])]
    if filter['hall_count_low'] < filter['hall_count_high']:
        r = r[(r['建物現況格局-廳'] >= filter['hall_count_low']) & (r['建物現況格局-廳'] <= filter['hall_count_high'])]
    if filter['bath_count_low'] < filter['bath_count_high']:
        r = r[(r['建物現況格局-衛'] >= filter['bath_count_low']) & (r['建物現況格局-衛'] <= filter['bath_count_high'])]
    if filter['berth'] != '無':
        r = r[(r['車位數'] != 0)]
    else:
        r = r[(r['車位數'] == 0)]

    return r

def getLatLng(address):
    if address not in pos.keys():
        g = geocoder.arcgis(address) 
        if g:
            latlng = (g.osm['x'],g.osm['y'])
            pos[address] = latlng
            with open('pos.pkl', 'wb') as f:  # Python 3: open(..., 'wb')
                print(pos)
                pickle.dump(pos, f)
            return pos[address]
    return None


def create_map(filter={
    'district':'All',
    'price_low':0,
    'price_high':sys.maxsize,
    'room_count_low':0,
    'room_count_high':sys.maxsize,
    'hall_count_low':0,
    'hall_count_high':sys.maxsize,
    'bath_count_low':0,
    'bath_count_high':sys.maxsize,
    'berth':'All'
    }
    ):
    d = getData(filter)
    points = {
        '住宅大樓(11層含以上有電梯)':{
            'name' : '住宅大樓',
            'lats' : [],
            'lons' : [],
            'text' : [],
            'color' : 'rgb(255, 0, 0)',
            'hidden':[]
        },
        '公寓(5樓含以下無電梯)':{
            'name' : '公寓',
            'lats' : [],
            'lons' : [],
            'text' : [],
            'color' : 'rgb(0, 255, 0)',
            'hidden':[]
        },
        '華廈(10層含以下有電梯)':{
            'name' : '華廈',
            'lats' : [],
            'lons' : [],
            'text' : [],
            'color' : 'rgb(0, 0, 255)',
            'hidden':[]
        },
        '透天厝':{
            'name' : '透天厝',
            'lats' : [],
            'lons' : [],
            'text' : [],
            'color' : 'rgb(255, 255, 0)',
            'hidden':[]
        },
        '其他':{
            'name' : '其他',
            'lats' : [],
            'lons' : [],
            'text' : [],
            'color' : 'rgb(255, 0, 255)',
            'hidden':[]
        }       
    }

    for i in d.values:
        if i[2] not in pos.keys():
            if not getLatLng(i[2]):
                continue
        
        hidden_info = ''
        for id,label in enumerate(all_data):
            if id != 28:
                hidden_info += '{}：{}<br />'.format(label,i[id])
            else:
                hidden_info += '{}：{}'.format(label,i[id])
        
        if i[11] in points.keys():
            points[i[11]]['lats'].append(pos[i[2]][1])
            points[i[11]]['lons'].append(pos[i[2]][0])
            # hidden_info = '鄉鎮市區：{} <br /> 交易標的：{} <br />土地區段位置建物區段門牌：{} <br />土地移轉總面積平方公尺：{} <br />交易年月日：{} <br />交易筆棟數：{}'.format(
            #     i[0],i[1],i[2],i[3],i[7],i[8]
            # )
            points[i[11]]['hidden'].append(hidden_info)
            info = '地址：{} <br />價格：{} 萬元 <br />單價：{} 萬元/平方公尺 <br />格局：{} 房 {} 廳 {} 衛 <br />車位數：{}'.format(
                i[2],i[21]/10000,i[22]/10000,i[16],i[17],i[18],i[28])
            points[i[11]]['text'].append(info)
        else:
            points['其他']['lats'].append(pos[i[2]][1])
            points['其他']['lons'].append(pos[i[2]][0])
            # hidden_info = '鄉鎮市區：{} <br /> 交易標的：{} <br />土地區段位置建物區段門牌：{} <br />土地移轉總面積平方公尺：{} <br />交易年月日：{} <br />交易筆棟數：{}'.format(
            #     i[0],i[1],i[2],i[3],i[7],i[8]
            # )
            points['其他']['hidden'].append(hidden_info)
            info = '地址：{} <br />價格：{} 萬元 <br />單價：{} 萬元/平方公尺 <br />格局：{} 房 {} 廳 {} 衛 <br />車位數：{}'.format(
                i[2],i[21]/10000,i[22]/10000,i[16],i[17],i[18],i[28])
            points['其他']['text'].append(info)    

    center_lat = 25.0422329
    center_lon = 121.5333087

    center_lat = sum([sum(points[i]['lats']) for i in points.keys()]) / sum([len(points[i]['lats']) for i in points.keys()])
    center_lon = sum([sum(points[i]['lons']) for i in points.keys()]) / sum([len(points[i]['lons']) for i in points.keys()])
    
    data = []
    for i in points.keys():
        data.append(
            go.Scattermapbox(
                lat=points[i]['lats'],
                lon=points[i]['lons'],
                mode='markers',
                name=points[i]['name'],
                marker=go.scattermapbox.Marker(
                    size=14,
                    color=points[i]['color']

                ),
                hovertext=points[i]['text'],
                hoverinfo='text',
                text=points[i]['hidden']
            )
        )

    layout = go.Layout(
        autosize=True,
        width=700,
        height=600,
        hovermode='closest',
        margin=go.layout.Margin(
        l=10,
        r=10,
        b=10,
        t=10,
        pad=4
        ),
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=center_lat,
                lon=center_lon
            ),
            pitch=0, 
            zoom=14
        ),
    )
    fig = go.Figure(data=data, layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route('/', methods=['GET', 'POST'])
def index():
    total_sell_pie = create_plot()
    if request.method == 'POST':         
        filter = {
    'district':'All',
    'price_low':0,
    'price_high':sys.maxsize,
    'room_count_low':0,
    'room_count_high':sys.maxsize,
    'hall_count_low':0,
    'hall_count_high':sys.maxsize,
    'bath_count_low':0,
    'bath_count_high':sys.maxsize,
    'berth':'All'
    }
        filter['district'] = request.form.get('districtSelect')
        filter['price_low'] = int(request.form.get('price_low_input'))
        filter['price_high'] = int(request.form.get('price_high_input'))
        filter['room_count_low'] = int(request.form.get('room_count_low_select'))
        filter['hall_count_low'] = int(request.form.get('hall_count_low_select'))
        filter['bath_count_low'] = int(request.form.get('bath_count_low_select'))
        map = create_map(filter)
    else:
        map = create_map()
    
    #return render_template('plotly.html',plot=total_sell_pie,users=['All'] + district,map=map)
    return render_template('index.html',plot=total_sell_pie,users=['All'] + district,map=map)
    
if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5001, debug=True)