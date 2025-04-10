# Weather App Technical Assessment

## Overview
This project is a weather application built as a full-stack solution:
- **Frontend:** React application for user interaction and responsive display.
- **Backend:** Flask-based API service with full CRUD functionality, live weather integration (via OpenWeatherMap), additional API integration, and data export options.

The app allows users to:
- Enter a location (e.g., Zip Code, City, Landmarks).
- View current weather information and a 5-day forecast.
- See error messages if an invalid location is provided or if API calls fail.
- (For backend demo) Create, read, update, and delete weather query records, as well as export data in JSON or CSV format.

---

## Backend (Flask)

### Requirements
- Python 3.x
- Pip (Python package installer)

### How to Run the Backend
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the Flask application:
   ```bash
   python3 app.py
   ```
4. The Flask server should now be running at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Frontend (React)

### Requirements
- Node.js & npm

### How to Run the Frontend
1. Open a new terminal (while keeping the backend server running).
2. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start the React application:
   ```bash
   npm start
   ```
5. Visit [http://localhost:3000](http://localhost:3000) to use the application.

---

## Usage
1. Enter a location (Zip Code, City name, etc.) in the search bar.
2. View current weather and a 5-day forecast.
3. Error messages will display for invalid input or API issues.
4. Use backend API endpoints for full CRUD operations and export data in JSON or CSV format.
