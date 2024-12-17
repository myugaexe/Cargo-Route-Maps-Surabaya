import os
import json
from flask import Flask, render_template, request, jsonify
import requests
import folium

app = Flask(__name__)
API_KEY = 'YOUR API KEY'

def read_json_file(filename):
    "Fungsi untuk membaca file JSON."
    filepath = os.path.join(app.static_folder, 'dataset', filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def get_route(start, end):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': start,
        'destination': end,
        'key': API_KEY,
        'mode': 'driving'
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        route = data['routes'][0]
        distance = route['legs'][0]['distance']['text']
        return route, distance
    else:
        return None, None

def create_map(route):
    start_location = route['legs'][0]['start_location']
    end_location = route['legs'][0]['end_location']
    start = request.form['start'] 
    end = request.form['end']  

    m = folium.Map(location=[start_location['lat'], start_location['lng']], zoom_start=15)

    folium.Marker(
        location=[start_location['lat'], start_location['lng']],
        popup=folium.Popup(f"<b>Start:</b> {start}", max_width=300),
        icon=folium.Icon(color='green', icon='user')
    ).add_to(m)

    folium.Marker(
        location=[end_location['lat'], end_location['lng']],
        popup=folium.Popup(f"<b>End:</b> {end}", max_width=300),
        icon=folium.Icon(color='red', icon='flag')
    ).add_to(m)

    points = []
    for leg in route['legs']:
        for step in leg['steps']:
            points.append([step['end_location']['lat'], step['end_location']['lng']])
    folium.PolyLine(points, color="blue", weight=5, opacity=1).add_to(m)

    bounds = [[start_location['lat'], start_location['lng']], [end_location['lat'], end_location['lng']]]
    m.fit_bounds(bounds)

    return m._repr_html_()


def estimate_price(vehicle, weight):
    base_price = 10000

    if vehicle == "truk_kecil":
        price_per_kg = 200
    elif vehicle == "truk_sedang":
        price_per_kg = 500
    elif vehicle == "truk_besar":
        price_per_kg = 1000
    else:
        price_per_kg = 0

    return base_price + (price_per_kg * weight)

@app.route('/')
def index():
    locations = read_json_file('places.json')['places']
    return render_template('main_page.html', locations=locations)

@app.route('/find-path', methods=['POST'])
def find_path():
    start = request.form['start']  
    end = request.form['end']  
    vehicle = request.form['vehicle']
    weight = float(request.form['weight'])

    max_weights = {
        "truk_kecil": 1000,
        "truk_sedang": 5000,
        "truk_besar": 10000
    }
    max_weight = max_weights.get(vehicle)

    if weight > max_weight:
        error_message = f"Berat barang melebihi batas maksimum untuk kendaraan yang dipilih ({max_weight} kg)."
        return jsonify({"error": error_message}), 400

    route, distance = get_route(start, end)

    if route:
        price = estimate_price(vehicle, weight)

        map_html = create_map(route)

        return render_template(
            'route_map.html',
            start=start,
            end=end,
            distance=distance,
            map_html=map_html,
            price=price
        )
    else:
        return jsonify({"error": "Tidak dapat menemukan rute. Pastikan titik awal dan akhir valid."}), 400

if __name__ == '__main__':
    app.run(debug=True)