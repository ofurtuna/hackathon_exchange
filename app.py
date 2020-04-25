import os
import overpy
import time
from textwrap import dedent
import geocoder
from shapely.geometry import Polygon, Point, mapping, MultiPolygon
import dash
import dash_core_components as dcc
import pandas as pd
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

def add_score(dang_list, results):
    nodes = [node for node in results.nodes]
    for node in nodes:
        if 'amenity' in node.tags:
            #I create a new key in the tags dictionary, called dangerscore, whose value correspond to the score in the
            #csv file for the type of amenity or shop the node is.
            node.tags['dangerscore'] = dang_list.loc[dang_list['tags'] == node.tags['amenity']]['dangerscore'].item()
        else:
            node.tags['dangerscore'] = dang_list.loc[dang_list['tags'] == node.tags['shop']]['dangerscore'].item()
    return nodes


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
        # 1. Reverse-geocoding (i.e finding geo coordinates from addresses)
        geocod_start = geocoder.osm(add_start)
        geocod_end = geocoder.osm(add_end)

        # 2. Compute the box to look for POI around
        box = [(geocod_start.lat, geocod_end.lng),
                (geocod_end.lat, geocod_end.lng),
                (geocod_end.lat, geocod_start.lng),
                (geocod_start.lat, geocod_start.lng)]

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
            if node.tags['dangerscore'] != '1':
                lat = node.lat
                lon = node.lon

                dangers_poly_coords = Point(lon, lat).buffer(0.0002).simplify(0.05)
                dangers_poly.append(dangers_poly_coords)

        danger_buffer_poly = []  # site_buffer_poly, which is the input for the avoid polygon option
        for danger_poly in dangers_poly:
            poly = Polygon(danger_poly)
            danger_buffer_poly.append(poly)

        # 5.Request the route
        route_request = {'coordinates': [[geocod_start.lng, geocod_start.lat], [geocod_end.lng, geocod_end.lat]],
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
        map = folium.Map(tiles='Stamen Toner', location=([geocod_start.lat, geocod_start.lng]), zoom_start=14)  # Create map

        # Beginning and end markers
        folium.Marker([geocod_start.lat, geocod_start.lng], popup='<i>Start</i>').add_to(map)
        folium.Marker([geocod_end.lat, geocod_end.lng], popup='<i>End</i>').add_to(map)

        # Plotting the dangerous areas
        folium.features.GeoJson(data=mapping(MultiPolygon(danger_buffer_poly)),
                                overlay=True).add_to(map)
        # Plotting the area of search
        folium.features.GeoJson(data=route_directions,
                                name='Route',
                                overlay=True).add_to(map)

        # Create the html
        updated_map_path = "C:/Users/daphn/Documents/EUvsVirus/visu/test.html"
        map.save(updated_map_path)

        return open(updated_map_path, 'r').read()



if __name__ == "__main__":

    app.run_server(debug=True)

