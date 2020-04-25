# Initial imports
import os
import folium
from folium import Map, Marker, LayerControl

from openrouteservice import client
# documentation: https://openrouteservice-py.readthedocs.io/en/latest/

from shapely import geometry
from shapely.geometry import shape, Polygon, mapping, MultiPolygon, LineString, Point
import pandas as pd
# Open route service connection
# You have to create a profile on the website then in the Pane Dashboard you should create a new token
api_key = '5b3ce3597851110001cf6248d14c60f017174b11b170ff63fdbf48b3'
clnt = client.Client(key=api_key)

# 1. Input from the user on the address from and to
# 2. Reverse-geocoding of the addresses to get the two pairs of lat long
# 3. Compute the a box around
# 4. Retrieve the POI in the box
# 5. Filter the POI in the box to keep only the points to be avoid
# 6. Cluster and score dangerous areas
# 7.Request the route
# 8.Display the route and the dangerous points

# 1. Implemented as user input
# TODO create a flask app or else so that the user can enter its location and destination

# Example
start = "Nordring 78 Offenbach Am Main Germany"
end = "Hafenplatz 1-3, 63067 Offenbach am Main Germany"

# 2. Reverse-geocoding (i.e finding geo coordinates from addresses)
import geocoder

geocod_start = geocoder.osm(start)
geocod_end = geocoder.osm(end)


geocod_end.quality # Could implement a filter that tells you to wear a mask b/c supermarket, ffm, corona crisis


# TODO: if coord is None: # trick the API to find the address

# 3. Compute the box

# From geometry classes
# x1: lat start
# y1: lng start
# x2: lat end
# y2: lng end
# [(x1, y2), (x2, y2), (x2, y1), (x1, y1)]
box = [(geocod_start.lat, geocod_end.lng),
        (geocod_end.lat, geocod_end.lng),
        (geocod_end.lat, geocod_start.lng),
        (geocod_start.lat, geocod_start.lng)]

# Convert to polygon
from shapely.geometry import Polygon
poly_box = Polygon(box)

# Buffer the box to be sure not to miss to much POI that could be on the safest way
poly_box = poly_box.buffer(0.0025).simplify(0.05)
# Buffer could be a parameter on how far you are ready to go to avoid the risky places
# Atm it was more a trial-error process to select 0.0025
# Simplify is to avoid too many points in the returning geometry



# 4. Retrieve the POI in the area
import overpy # This API is better than the one of the routing, probably b/c it is the one dvp for retrieving POI...

api = overpy.Overpass()
# The queries have to be written in the overpass fashion way
# Language guide here: https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide#Tag_request_clauses_.28or_.22tag_filters.22.29
result_nodes = api.query("(node['shop']{0};node['amenity']{0};);out;".format(str(poly_box.exterior.bounds)))
# This query should be modified to be extended to other tags
len(result_nodes.nodes)

result_areas = api.query("(area['shop']{0};area['amenity']{0};);out;".format(str(poly_box.exterior.bounds)))
# This query should be modified to be extended to other tags
len(result_areas.areas)

# We will be interested in the type of POI (restaurants, hospitals, etc.)
# TODO investigate the tags to see if opening hours or else could be of interest
def extract_object(node):
    if "amenity" in node.tags:
        type_node = node.tags["amenity"]
    else:
        type_node =node.tags["shop"]
    return type_node

# Get the types of the objects
node_amenities = set([extract_object(node) for node in result_nodes.nodes])
areas_amenity = set([extract_object(area) for area in result_areas.areas])

# 5. Filter the POI in the box to keep only the points to be avoid
# 6. Cluster and score dangerous areas

#I did not use the above lists. What I try to do is to expand the tags of
#each node, adding the danger score provided in the csv file.

#Loading the csv
dang_list = pd.read_csv('C:/Users/daphn/Documents/EUvsVirus/hackathon_exchange/DangerScoreList.csv', delimiter=',')

#Defining the function to add the score:
#brute force approach to handling missing amenities in csv
def add_score(results):
    nodes = [node for node in results.nodes]

    for node in nodes:
        if 'amenity' in node.tags:
            try:
                node.tags['dangerscore'] = dang_list.loc[dang_list['tags'] == node.tags['amenity']][
                    'dangerscore'].item()
            except:
                pass
        else:
            try:
                node.tags['dangerscore'] = dang_list.loc[dang_list['tags'] == node.tags['shop']]['dangerscore'].item()
            except:
                pass
    return nodes
nodes_score = add_score(result_nodes) #nodes_score is a list of overpy objects, with lat and lon info,
# which can then be used in the routing.

#Here I try to reconstruct the element in the example code
dangers_poly = [] #sites_poly

#I define dangerous a POI with score greater than 1
#brute force approach to handling missing amenities in csv
for node in nodes_score:
    try:
        if node.tags['dangerscore'] != '1':
            lat= node.lat
            lon = node.lon
            dangers_poly_coords = Point(lon,lat).buffer(0.0001).simplify(0.05)
            dangers_poly.append(dangers_poly_coords)
    except:
        pass

# TODO I need your help here fellow data scientists

danger_buffer_poly = [] #site_buffer_poly, which is the input for the avoid polygon option
for danger_poly in dangers_poly:
    poly = Polygon(danger_poly)
    danger_buffer_poly.append(poly)

# 7.Request the route
route_request = {'coordinates': [[geocod_start.lng, geocod_start.lat], [geocod_end.lng, geocod_end.lat]], # Careful long then lat and not lat then long
                 'format_out': 'geojson',
                 'profile': 'foot-walking',
                 'preference': 'shortest',
                 'instructions': False,
                'options': {'avoid_polygons': geometry.mapping(MultiPolygon(danger_buffer_poly))}}

# TODO Integrate with the decided areas to be avoided
route_directions = clnt.directions(**route_request)

# 8.Display the route and the dangerous points
import folium
import webbrowser

def style_function(color):
    return lambda feature: dict(color=color,
                              weight=3,
                              opacity=1)
 #6.Display the route and the dangerous points
        # Create the base map
map = folium.Map(tiles='Stamen Toner', location=([geocod_start.lat, geocod_start.lng]), zoom_start=14)  # Create map

        # Beginning and end markers
folium.Marker([geocod_start.lat, geocod_start.lng], popup='<i>Start</i>').add_to(map)
folium.Marker([geocod_end.lat, geocod_end.lng], popup='<i>End</i>').add_to(map)

        # Plotting the dangerous areas
folium.features.GeoJson(data=mapping(MultiPolygon(danger_buffer_poly)),
                        style_function=style_function('red'),
                        overlay=True).add_to(map)
        # Plotting the area of search
folium.features.GeoJson(data=route_directions,
                        name='Route',
                        overlay=True).add_to(map)

# I use Pycharm and the map cannot be displayed there so save then open in browser but if you use notebooks just go for map
map.save(test_output)
webbrowser.open(test_output, new=2)