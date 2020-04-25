# Initial imports
import os
import re
import dash
import folium
import overpy
import geocoder

import numpy as np
import pandas as pd

import dash_core_components as dcc
import dash_html_components as html
from openrouteservice import client
from dash.dependencies import Input, Output, State
from shapely.geometry import Polygon, Point, mapping, MultiPolygon

# Dash app properties
# To display the wheel next to the cursor while loading
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'https://codepen.io/chriddyp/pen/brPBPO.css']
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
    external_stylesheets=external_stylesheets
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

    # def initial_map(self):
    #     initial_map = folium.Map(tiles='Stamen Toner', location=([0, 0]), zoom_start=3)
    #     initial_map.add_child(folium.LatLngPopup())
    #     return initial_map.save(self.path_initial_map)

    def initial_map(self):
        initial_map = folium.Map(tiles='Stamen Toner', location=([0, 0]), zoom_start=3)
        initial_map.add_child(folium.LatLngPopup())
        return initial_map._repr_html_()

def add_score(dang_list, results):
    nodes = [node for node in results.nodes]

    for node in nodes:
        try:
            if 'amenity' in node.tags:
                #I create a new key in the tags dictionary, called dangerscore, whose value correspond to the score in the
                #csv file for the type of amenity or shop the node is.
                node.tags['dangerscore'] = dang_list.loc[dang_list['tags'] == node.tags['amenity']]['dangerscore'].item()
            else:
                node.tags['dangerscore'] = dang_list.loc[dang_list['tags'] == node.tags['shop']]['dangerscore'].item()
        except:
            node.tags['dangerscore'] = 0

    return nodes


## EXECUTE
my_input().path_initial_map
#to_display_map = open(my_input().path_initial_map, 'r').read()
my_input().initial_map()

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
                         html.Div(
                            id="input-level",
                             children=[
                                 html.P(id="level-text",
                                        children="What level of safety?"),

                             dcc.Dropdown(
                                 id="fearlevel",
                                 options= [
                                     {'label': 'Only dangerous areas', 'value': 3},
                                     {'label': 'Dangerous areas and possibly crowded places', 'value': 2},
                                     {'label': 'I am paranoïac', 'value': 1},
                                     {'label': '-SHOW- No restrictions', 'value': 4}
                                 ],
                                 value=3
                             ),
                            html.Button('Submit', id='button'),
                         ],
                         ),
                     ],
                 ),

                html.Div(
                     id="display_map",
                     children=[
                         html.P(id="map-title", children=" Enjoy your trip"),
                         html.Iframe(id='map',
                                     #srcDoc= open(my_input().path_initial_map, 'r').read(),
                                     srcDoc=my_input().initial_map(),
                                     width='100%', height='600', contentEditable="true"),
                     ]
                 ),
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
     dash.dependencies.State("add_end", "value"),
     dash.dependencies.State("fearlevel", "value")],
)

# def update_output(add_start, add_end):
#     return u'Selected starting Address: {} \n\n Selected Arrival Address: {}'.format(add_start, add_end)

def update_map(n_clicks, add_start, add_end, fearlevel):
    if any([add_end is None, add_start is None]):
        return my_input().initial_map()
    else:
        # 1. Reverse-geocoding (i.e finding geo coordinates from addresses)
        # Also handles lat/long
        if re.match(r"(\d{1,2}\.\d{1,12})", add_start) is None:
            geocod_start = geocoder.osm(add_start)
            start_lat = geocod_start.lat
            start_lng = geocod_start.lng
        else:
            start_lat = float(add_start.split(" ")[0])
            start_lng = float(add_start.split(" ")[1])

        if re.match(r"(\d{1,2}\.\d{1,12})", add_end) is None:
            geocod_end = geocoder.osm(add_end)
            end_lat = geocod_end.lat
            end_lng = geocod_end.lng

        else:
            end_lat = float(add_end.split(" ")[0])
            end_lng = float(add_end.split(" ")[1])

        # 2. Compute the box to look for POI around
        box = [
            (start_lat, end_lng),
            (end_lat, end_lng),
            (end_lat, start_lng),
            (start_lat, start_lng)
        ]

        poly_box = Polygon(box)
        poly_box = poly_box.buffer(0.0025).simplify(0.05)

        # 3. Retrieve the POI in the area
        api = overpy.Overpass()
        result_nodes = api.query("(node['shop']{0};node['amenity']{0};);out;".format(str(poly_box.exterior.bounds)))
        result_areas = api.query("(area['shop']{0};area['amenity']{0};);out;".format(str(poly_box.exterior.bounds)))

        # 4. Filter the POI in the box to keep only the points to be avoid
        # Loading the csv for the danger levels
        dang_list = pd.read_csv('C:/Users/daphn/Documents/EUvsVirus/hackathon_exchange/DangerScoreList.csv',
                                delimiter=',')
        # Score the POI in the area
        nodes_score = add_score(dang_list, result_nodes)  # nodes_score is a list of overpy objects, with lat and lon info,

        dangers_poly = []  # sites_poly
        # I define dangerous a POI with score greater than 1
        for node in nodes_score:
            if node.tags['dangerscore'] >= fearlevel:
                lat = node.lat
                lon = node.lon

                dangers_poly_coords = Point(lon, lat).buffer(0.00099).simplify(0.05)
                dangers_poly.append(dangers_poly_coords)

        danger_buffer_poly = []  # site_buffer_poly, which is the input for the avoid polygon option
        for danger_poly in dangers_poly:
            poly = Polygon(danger_poly)
            danger_buffer_poly.append(poly)

        # 5.Request the route
        route_request = {'coordinates': [[start_lng, start_lat], [end_lng, end_lat]],
                         # Careful long then lat and not lat then long
                         'format_out': 'geojson',
                         'profile': 'foot-walking',
                         'preference': 'shortest',
                         'instructions': False,
                         'options': {'avoid_polygons': mapping(MultiPolygon(danger_buffer_poly))}}

        api_key = '5b3ce3597851110001cf6248d14c60f017174b11b170ff63fdbf48b3'
        clnt = client.Client(key=api_key)

        route_directions = clnt.directions(**route_request)


        # 6.Display the route and the dangerous points
        # Create the base map
        map = folium.Map(tiles='Stamen Toner', location=([start_lat, start_lng]), zoom_start=14)  # Create map

        # Beginning and end markers
        folium.Marker([start_lat, start_lng], popup='<i>Start</i>').add_to(map)
        folium.Marker([end_lat, end_lng], popup='<i>End</i>').add_to(map)

        # Plotting the dangerous areas
        style_danger = {'fillColor': '#f88494', 'color': '#ff334f'}
        folium.features.GeoJson(data=mapping(MultiPolygon(danger_buffer_poly)),
                                style_function=lambda x: style_danger,
                                overlay=True).add_to(map)

        # Plotting the area of search
        folium.features.GeoJson(data=route_directions,
                                name='Route',
                                overlay=True).add_to(map)

        map.add_child(folium.LatLngPopup())

        # Create the html
        #updated_map_path = "C:/Users/daphn/Documents/EUvsVirus/visu/test.html"
        #map.save(updated_map_path)

        return map._repr_html_()
        #return open(updated_map_path, 'r').read()


if __name__ == "__main__":

    app.run_server(debug=True)

