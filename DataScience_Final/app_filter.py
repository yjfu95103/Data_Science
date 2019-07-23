# coding:utf-8
from flask import Flask, render_template,Response,jsonify,request
import numpy as np
import pandas as pd
import json
import sys
import pickle
import plotly
import plotly.graph_objs as go

mapbox_access_token = 'pk.eyJ1IjoiendoaXRleSIsImEiOiJjandjODZxcG0wYmtoM3puNWV1Znk4bnJpIn0.lwm7J6niQyBpEsopsl-QMg'
gmap_url = 'https://www.google.com.tw/maps/search/'

all_data = pd.read_csv('a_lvr_land_a.csv')
all_data = all_data.drop([0])
all_data['車位類別'].fillna(value='無',inplace=True)
all_data = all_data.astype(
    {'建物現況格局-房':'int32',
    '建物現況格局-廳':'int32',
    '建物現況格局-衛':'int32',
    '總價元':'int32'
    })
district = list(all_data['鄉鎮市區'].unique())
total_sell = {}
for i in district:
        total_sell[i] = all_data[all_data['鄉鎮市區'] == i]['鄉鎮市區'].count()
with open('pos.pkl','rb') as f:
    pos = pickle.load(f)


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
        r = r[(r['車位類別'] != '無')]
    else:
        r = r[(r['車位類別'] == '無')]

    return r

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
    lat = []
    lon = []
    text = []
    for i in d.values:
        if i[2] in pos.keys():
            lat.append(pos[i[2]][0])
            lon.append(pos[i[2]][1])
            text.append(i[2]+' ' + str(i[21]))

    center_lat = 25.0422329
    center_lon = 121.5333087

    if lat:
        center_lat = sum(lat) / len(lat)
    if lon:
        center_lon = sum(lon) / len(lon)
    data = [
        go.Scattermapbox(
            lat=lat,
            lon=lon,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=14
            ),
            text=text,
        )
    ]
    layout = go.Layout(
        autosize=True,
        width=1200,
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
    
    return render_template('plotly.html',plot=total_sell_pie,users=['All'] + district,map=map)
    
if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5001, debug=True)