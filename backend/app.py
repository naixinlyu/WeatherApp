# backend/app.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from datetime import datetime
import csv
from io import StringIO
import json

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class WeatherQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    weather_data = db.Column(db.Text) 


# Endpoint to fetch current weather and 5-day forecast from an external weather API
@app.route('/api/weather', methods=['GET'])
def get_weather():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location parameter is required.'}), 400

    api_key = os.getenv("OPENWEATHER_API_KEY", "763e7bb2b775a020e278917ba01b175a")

    # Fetch current weather data from OpenWeatherMap
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    current_response = requests.get(weather_url)
    if current_response.status_code != 200:
        return jsonify({'error': 'Failed to fetch weather data', 'details': current_response.text}), current_response.status_code
    weather_data = current_response.json()

    print(f"Using API Key: {api_key}")
    print(f"Request URL: {weather_url}")

    # Fetch 5-day forecast data
    forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        forecast_data = {}
    else:
        forecast_data = forecast_response.json()

    combined_data = {
        'current': weather_data,
        'forecast': forecast_data
    }
    return jsonify(combined_data)



# CRUD Endpoints for Weather Queries
# Create: Save a new weather query with location, date range, and weather data
@app.route('/api/weatherQuery', methods=['POST'])
def create_weather_query():
    data = request.get_json()
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    weather_data = data.get('weather_data')

    # Validate date format (expected YYYY-MM-DD)
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except Exception:
        return jsonify({'error': 'Invalid date format. Should be YYYY-MM-DD'}), 400

    if not location:
        return jsonify({'error': 'Location is required.'}), 400

    query = WeatherQuery(
        location=location,
        start_date=start_date,
        end_date=end_date,
        weather_data=json.dumps(weather_data)
    )
    db.session.add(query)
    db.session.commit()

    return jsonify({'message': 'Weather query created successfully', 'id': query.id}), 201

# Read: Retrieve all weather query records
@app.route('/api/weatherQueries', methods=['GET'])
def get_weather_queries():
    queries = WeatherQuery.query.all()
    results = []
    for q in queries:
        results.append({
            'id': q.id,
            'location': q.location,
            'start_date': q.start_date,
            'end_date': q.end_date,
            'created_at': q.created_at.isoformat(),
            'weather_data': json.loads(q.weather_data)
        })
    return jsonify(results), 200

# Update: Update a specific weather query record
@app.route('/api/weatherQuery/<int:query_id>', methods=['PUT'])
def update_weather_query(query_id):
    query = WeatherQuery.query.get(query_id)
    if not query:
        return jsonify({'error': 'Weather query not found'}), 404

    data = request.get_json()
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    weather_data = data.get('weather_data')

    if location:
        query.location = location
    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            query.start_date = start_date
        except:
            return jsonify({'error': 'Invalid start_date format. Should be YYYY-MM-DD'}), 400
    if end_date:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
            query.end_date = end_date
        except:
            return jsonify({'error': 'Invalid end_date format. Should be YYYY-MM-DD'}), 400
    if weather_data:
        query.weather_data = json.dumps(weather_data)

    db.session.commit()
    return jsonify({'message': 'Weather query updated successfully'}), 200

# Delete: Remove a weather query record
@app.route('/api/weatherQuery/<int:query_id>', methods=['DELETE'])
def delete_weather_query(query_id):
    query = WeatherQuery.query.get(query_id)
    if not query:
        return jsonify({'error': 'Weather query not found'}), 404

    db.session.delete(query)
    db.session.commit()
    return jsonify({'message': 'Weather query deleted successfully'}), 200


# Data Export Endpoint
@app.route('/api/export', methods=['GET'])
def export_data():
    export_format = request.args.get('format', 'json').lower()
    queries = WeatherQuery.query.all()
    results = []
    for q in queries:
        results.append({
            'id': q.id,
            'location': q.location,
            'start_date': q.start_date,
            'end_date': q.end_date,
            'created_at': q.created_at.isoformat(),
            'weather_data': json.loads(q.weather_data)
        })
    if export_format == 'json':
        return jsonify(results)
    elif export_format == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['id', 'location', 'start_date', 'end_date', 'created_at', 'weather_data'])
        for item in results:
            cw.writerow([item['id'], item['location'], item['start_date'], item['end_date'], item['created_at'], json.dumps(item['weather_data'])])
        output = si.getvalue()
        return app.response_class(output, mimetype='text/csv')
    else:
        return jsonify({'error': 'Format not supported'}), 400

# Additional API Integration Example
@app.route('/api/maps', methods=['GET'])
def get_maps_data():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location parameter is required.'}), 400
    # Return a basic Google Maps search URL for the location
    map_url = f"https://www.google.com/maps/search/{location}"
    return jsonify({'map_url': map_url}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
