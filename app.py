import os
import time
from textwrap import dedent
import geocoder
from shapely.geometry import Polygon
import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
from dash.dependencies import Input, Output, State

import dash_html_components as html
import folium
from openrouteservice import client

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

# Process

# Initial display: world map + input boxes
# Implement: user selection on the world map (if add_start is none then select point is start else if add_start is not none then select point is add_end)
# Compute route on inputs
# Update display

# My input
class my_input():
    def __init__(self):
        self.path_initial_map ='C:/Users/daphn/Documents/EUvsVirus/visu/base_map.html'

    def initial_map(self):
        initial_map = folium.Map(tiles='Stamen Toner', location=([0, 0]), zoom_start=3)
        initial_map.add_child(folium.LatLngPopup())
        return initial_map.save(self.path_initial_map)

## EXECUTE
my_input().path_initial_map
#to_display_map = open(my_input().path_initial_map, 'r').read()


# User input

# App
app.layout = html.Div(
    id="root",
    children=[
        html.Div(id="header",
                 children=[
                    html.H4(children="Finding the safest route to go shopping"),
                    html.P(id="description", children="Concept for EUvsCovid hackathon"),
                    ],
                 ),
    html.Div(id="app-container",
             children=
             [
                 html.Div(
                     id="left-column",
                     children=[
                         html.Div(
                             id="input-start",
                             children=[
                                 html.P(id="input-start-text",
                                        children="Type your start address"),
                                 dcc.Input(id="add_start", type="text",
                                           placeholder=""),
                             ],
                         ),
                         html.Div(
                             id="input-end",
                             children=[
                             html.P(id="input-end-text",
                                    children="Type your arrival address."),
                             dcc.Input(id="add_end", type="text",
                                       placeholder=""),
                             ],
                         ),
                         html.Button('Submit', id='button'),
                         ],
                         ),
                 html.Div(
                     id="display_map",
                     children=[
                         html.P(id="map-title", children=" Enjoy your trip"),
                         html.Iframe(id='map',
                                     srcDoc= open(my_input().path_initial_map, 'r').read(),
                                     width='100%', height='600'),
                     ]
                 )
                     ],
                 ),
             ],
             )

# @app.callback(
#     Output("summary-user-selection", "children"),
#     [Input("add_start", "value"), Input("add_end", "value")],
# )

@app.callback(
    dash.dependencies.Output("map", "srcDoc"),
    [dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State("add_start", "value"),
     dash.dependencies.State("add_end", "value")],
)

# def update_output(add_start, add_end):
#     return u'Selected starting Address: {} \n\n Selected Arrival Address: {}'.format(add_start, add_end)

def update_map(n_clicks, add_start, add_end):
    if any([add_end is None, add_start is None]):
        pass

    else:
        geocod_start = geocoder.osm(add_start)
        geocod_end = geocoder.osm(add_end)

        box = [(geocod_start.lat, geocod_end.lng),
                (geocod_end.lat, geocod_end.lng),
                (geocod_end.lat, geocod_start.lng),
                (geocod_start.lat, geocod_start.lng)]

        poly_box = Polygon(box)
        poly_box = poly_box.buffer(0.0025).simplify(0.05)

        route_request = {'coordinates': [[geocod_start.lng, geocod_start.lat], [geocod_end.lng, geocod_end.lat]],
                         # Careful long then lat and not lat then long
                         'format_out': 'geojson',
                         'profile': 'foot-walking',
                         'preference': 'shortest',
                         'instructions': False}

        api_key = '5b3ce3597851110001cf6248d14c60f017174b11b170ff63fdbf48b3'
        clnt = client.Client(key=api_key)

        route_directions = clnt.directions(**route_request)

        map = folium.Map(tiles='Stamen Toner', location=([geocod_start.lat, geocod_start.lng]), zoom_start=14)  # Create map

        folium.Marker([geocod_start.lat, geocod_start.lng], popup='<i>Start</i>').add_to(map)
        folium.Marker([geocod_end.lat, geocod_end.lng], popup='<i>End</i>').add_to(map)

        folium.features.GeoJson(data=route_directions,
                                name='Route',
                                overlay=True).add_to(map)

        updated_map_path = "C:/Users/daphn/Documents/EUvsVirus/visu/test.html"
        map.save(updated_map_path)

        return open(updated_map_path, 'r').read()


# test_output = "C:/Users/daphn/Documents/EUvsVirus/visu/test.html"
#
# # app.layout = html.Div([
# #     html.H1('My first app with folium map'),
# #     html.Iframe(id='map', srcDoc=open(test_output, 'r').read(), width='100%', height='600'),
# # ])
#
# app.layout = html.Div(
#     [
#         html.H1('My first app with folium map'),
#         html.Iframe(id='map', srcDoc=open(test_output, 'r').read(), width='100%', height='600'),
#         html.I("Try typing in input 1 & 2, and observe how debounce is impacting the callbacks. Press Enter and/or Tab key in Input 2 to cancel the delay"),
#         html.Br(),
#         dcc.Input(id="add_start", type="text", placeholder=""),
#         dcc.Input(id="add_end", type="text", placeholder="", debounce=True),
#         html.Div(id="output"),
#     ]
# )
#
#
# @app.callback(
#     Output("output", "children"),
#     [Input("add_start", "value"), Input("add_end", "value")],
# )
#
# def update_output(add_start, add_end):
#     return u'Starting Address {} and Arrival Address {}'.format(add_start, add_end)
#
# def bad_ass(add_start, add_end, test_output):
#
#     geocod_start = geocoder.osm(add_start)
#     geocod_end = geocoder.osm(add_end)
#
#     box = [(geocod_start.lat, geocod_end.lng),
#             (geocod_end.lat, geocod_end.lng),
#             (geocod_end.lat, geocod_start.lng),
#             (geocod_start.lat, geocod_start.lng)]
#
#     poly_box = Polygon(box)
#     poly_box = poly_box.buffer(0.0025).simplify(0.05)
#
#     route_request = {'coordinates': [[geocod_start.lng, geocod_start.lat], [geocod_end.lng, geocod_end.lat]],
#                      # Careful long then lat and not lat then long
#                      'format_out': 'geojson',
#                      'profile': 'foot-walking',
#                      'preference': 'shortest',
#                      'instructions': False}
#
#     route_directions = clnt.directions(**route_request)
#
#     api_key = '5b3ce3597851110001cf6248d14c60f017174b11b170ff63fdbf48b3'
#     clnt = client.Client(key=api_key)
#
#     map = folium.Map(tiles='Stamen Toner', location=([geocod_start.lat, geocod_start.lng]), zoom_start=14)  # Create map
#
#     folium.Marker([geocod_start.lat, geocod_start.lng], popup='<i>Start</i>').add_to(map)
#     folium.Marker([geocod_end.lat, geocod_end.lng], popup='<i>End</i>').add_to(map)
#
#     folium.features.GeoJson(data=route_directions,
#                             name='Route',
#                             overlay=True).add_to(map)
#
#     return map.save(test_output)


if __name__ == "__main__":

    app.run_server(debug=True)

