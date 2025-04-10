// frontend/src/App.js
import React, { useState } from 'react';
import './App.css';

function App() {
  const [location, setLocation] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [error, setError] = useState('');

  // Update state as user types
  const handleInputChange = (e) => {
    setLocation(e.target.value);
  };

  // Fetch weather data from the backend
  const getWeather = async () => {
    if (!location.trim()) {
      setError("Location cannot be empty.");
      return;
    }
    setError('');
    try {
      const response = await fetch(`http://localhost:5000/api/weather?location=${location}`);
      console.log(location)
      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.error || "Error fetching weather data.");
        return;
      }
      const data = await response.json();
      setWeatherData(data);
    } catch (err) {
      setError("Failed to fetch weather data. Please try again later.");
    }
  };

  return (
    <div className="container">
      <header>
        <h1>Weather App - Naixin Lyu - Product Manager Accelerator</h1>
      </header>
      <main>
        <div className="weather-input">
          <input
            type="text"
            value={location}
            onChange={handleInputChange}
            placeholder="Enter location (zip code, city, landmarks, etc.)"
          />
          <button onClick={getWeather}>Get Weather</button>
        </div>
        {error && <div className="error">{error}</div>}
        {weatherData && (
          <div className="weather-display">
            <h2>Current Weather:</h2>
            <p>Temperature: {weatherData.current.main.temp} °C</p>
            <p>Weather: {weatherData.current.weather[0].description}</p>
            
            <h3>5-Day Forecast:</h3>
            {weatherData.forecast.list.slice(0, 5).map((forecast, index) => (
              <div key={index} className="forecast-item">
                <p>Date: {forecast.dt_txt}</p>
                <p>Temp: {forecast.main.temp} °C</p>
                <p>Condition: {forecast.weather[0].description}</p>
              </div>
            ))}
          </div>
        )}
      </main>
      <footer>
        <p>
          © NaixinLyu - Product Manager Accelerator
          From entry-level to VP of Product, we support PM professionals through every stage of their careers.
        </p>
      </footer>
    </div>
  );
}

export default App;
