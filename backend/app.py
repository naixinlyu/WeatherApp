from flask import Flask, request, jsonify
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

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

API_KEY = os.getenv("OPENWEATHER_API_KEY", "763e7bb2b775a020e278917ba01b175a")


# Database Model for Weather Queries
class WeatherQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.String(20))  # Format: YYYY-MM-DD
    end_date = db.Column(db.String(20))    # Format: YYYY-MM-DD
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    weather_data = db.Column(db.Text)      # Store JSON data

with app.app_context():
    db.create_all()


# Helper: Fetch weather and forecast data for a location
def fetch_weather_data(location):
    if "," in location:
        try:
            lat, lon = location.split(",")
            lat = float(lat.strip())
            lon = float(lon.strip())
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        except ValueError:
            return None, "Invalid coordinate format. Use lat,lon."
    else:
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"

    current_response = requests.get(weather_url)
    if current_response.status_code != 200:
        return None, f"Error fetching current weather: {current_response.text}"
    weather_data = current_response.json()

    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        return None, f"Error fetching forecast: {forecast_response.text}"
    forecast_data = forecast_response.json()

    combined = {
        'current': weather_data,
        'forecast': forecast_data
    }
    return combined, None

# 1) GET WEATHER (Current + 5-day forecast)
@app.route('/api/weather', methods=['GET'])
def get_weather():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location parameter is required.'}), 400

    data, error = fetch_weather_data(location)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(data)

# 2.1 CREATE: Save a new weather query (with date range validation and location validation)
@app.route('/api/weatherQuery', methods=['POST'])
def create_weather_query():
    data = request.get_json()
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not location:
        return jsonify({'error': 'Location is required.'}), 400

    # Validate date formats
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    except Exception:
        return jsonify({'error': 'Invalid date format. Should be YYYY-MM-DD'}), 400

    if start_dt > end_dt:
        return jsonify({'error': 'Start date must not be later than end date.'}), 400

    # Validate that the location exists
    weather_data, err = fetch_weather_data(location)
    if err:
        return jsonify({'error': f'Location validation failed: {err}'}), 400

    query = WeatherQuery(
        location=location,
        start_date=start_date,
        end_date=end_date,
        weather_data=json.dumps(weather_data)
    )
    db.session.add(query)
    db.session.commit()

    return jsonify({'message': 'Weather query created successfully', 'id': query.id}), 201

# 2.2 READ: Retrieve all weather query records
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
            'weather_data': json.loads(q.weather_data) if q.weather_data else {}
        })
    return jsonify(results), 200

# 2.3 UPDATE: Update a specific weather query record (with validations)
@app.route('/api/weatherQuery/<int:query_id>', methods=['PUT'])
def update_weather_query(query_id):
    query = WeatherQuery.query.get(query_id)
    if not query:
        return jsonify({'error': 'Weather query not found'}), 404

    data = request.get_json()
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if location:
        new_data, err = fetch_weather_data(location)
        if err:
            return jsonify({'error': f'Location validation failed: {err}'}), 400
        query.location = location
        query.weather_data = json.dumps(new_data)
    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            query.start_date = start_date
        except Exception:
            return jsonify({'error': 'Invalid start_date format. Should be YYYY-MM-DD'}), 400
    if end_date:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
            query.end_date = end_date
        except Exception:
            return jsonify({'error': 'Invalid end_date format. Should be YYYY-MM-DD'}), 400

    db.session.commit()
    return jsonify({'message': 'Weather query updated successfully'}), 200

# 2.4 DELETE: Remove a weather query record
@app.route('/api/weatherQuery/<int:query_id>', methods=['DELETE'])
def delete_weather_query(query_id):
    query = WeatherQuery.query.get(query_id)
    if not query:
        return jsonify({'error': 'Weather query not found'}), 404
    db.session.delete(query)
    db.session.commit()
    return jsonify({'message': 'Weather query deleted successfully'}), 200


# 2.6 EXPORT FORECAST: Export the 5-day forecast details for a given location
#    This endpoint groups the forecast data by day and returns, for each day:
#       - date
#       - min_temp (minimum temperature)
#       - max_temp (maximum temperature)
#       - condition (weather description from the first forecast block)
@app.route('/api/exportForecast', methods=['GET'])
def export_forecast():
    location = request.args.get('location')
    export_format = request.args.get('format', 'json').lower()
    if not location:
        return jsonify({'error': 'Location parameter is required.'}), 400

    # Build forecast URL based on the provided location
    if "," in location:
        try:
            lat, lon = location.split(",")
            lat = float(lat.strip())
            lon = float(lon.strip())
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        except ValueError:
            return jsonify({'error': 'Invalid coordinate format. Use lat,lon.'}), 400
    else:
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"

    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        return jsonify({'error': 'Failed to fetch forecast data', 'details': forecast_response.text}), forecast_response.status_code
    forecast_data = forecast_response.json()

    # Group forecast data by date (using dt_txt)
    def group_by_date(forecast_list):
        grouped = {}
        for item in forecast_list:
            date = item['dt_txt'].split(" ")[0]
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(item)
        return grouped

    grouped = group_by_date(forecast_data['list'])
    sorted_dates = sorted(grouped.keys())[:5]

    # For each day, compute min and max temperatures and get a sample condition
    export_obj = []
    for date in sorted_dates:
        day_items = grouped[date]
        min_temp = min(item["main"]["temp_min"] for item in day_items)
        max_temp = max(item["main"]["temp_max"] for item in day_items)
        # Use the condition from the first forecast block of the day
        condition = day_items[0]["weather"][0]["description"]
        export_obj.append({
            "date": date,
            "min_temp": round(min_temp, 1),
            "max_temp": round(max_temp, 1),
            "condition": condition
        })

    if export_format == 'json':
        return jsonify(export_obj)
    elif export_format == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["date", "min_temp", "max_temp", "condition"])
        for obj in export_obj:
            cw.writerow([obj["date"], obj["min_temp"], obj["max_temp"], obj["condition"]])
        output = si.getvalue()
        return app.response_class(output, mimetype="text/csv")
    else:
        return jsonify({'error': 'Format not supported'}), 400
    

# Additional: Google Maps URL for a location
@app.route('/api/maps', methods=['GET'])
def get_maps_data():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location parameter is required.'}), 400
    map_url = f"https://www.google.com/maps/search/{location}"
    return jsonify({'map_url': map_url}), 200

if __name__ == '__main__':
    app.run(debug=True)
