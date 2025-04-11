import React, { useState, useEffect } from "react";
import "./App.css";

// Helper: Group forecast data by day (extracting date from dt_txt)
const groupForecastByDay = (list) => {
  return list.reduce((acc, item) => {
    const date = item.dt_txt.split(" ")[0];
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(item);
    return acc;
  }, {});
};

function App() {
  // Weather search state
  const [location, setLocation] = useState("");
  const [weatherData, setWeatherData] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [loading, setLoading] = useState(false);

  // CRUD (Weather Queries) state
  const [queries, setQueries] = useState([]);
  const [newQuery, setNewQuery] = useState({
    location: "",
    start_date: "",
    end_date: "",
  });
  const [editingQuery, setEditingQuery] = useState(null);
  const [crudError, setCrudError] = useState("");

  // Weather Search Functions
  const handleInputChange = (e) => {
    setLocation(e.target.value);
  };

  const getWeather = async () => {
    if (!location.trim()) {
      setSearchError("Location cannot be empty.");
      return;
    }
    setSearchError("");
    setLoading(true);
    setWeatherData(null);
    try {
      const response = await fetch(
        `http://localhost:5000/api/weather?location=${encodeURIComponent(location)}`
      );
      if (!response.ok) {
        const err = await response.json();
        setSearchError(err.error || "Error fetching weather data.");
        setLoading(false);
        return;
      }
      const data = await response.json();
      setWeatherData(data);
    } catch (err) {
      setSearchError("Failed to fetch weather data. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const getCurrentLocationWeather = () => {
    if (!navigator.geolocation) {
      setSearchError("Geolocation not supported by your browser.");
      return;
    }
    setSearchError("");
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const response = await fetch(
            `http://localhost:5000/api/weather?location=${latitude},${longitude}`
          );
          if (!response.ok) {
            const err = await response.json();
            setSearchError(err.error || "Error fetching weather data.");
            setLoading(false);
            return;
          }
          const data = await response.json();
          setWeatherData(data);
        } catch (err) {
          setSearchError("Failed to fetch weather data for current location.");
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        setSearchError("Permission to access location was denied.");
        setLoading(false);
      }
    );
  };

  const openMap = async () => {
    if (!location.trim()) {
      setSearchError("Please enter a location before opening maps.");
      return;
    }
    try {
      const response = await fetch(
        `http://localhost:5000/api/maps?location=${encodeURIComponent(location)}`
      );
      if (!response.ok) {
        const err = await response.json();
        setSearchError(err.error || "Error fetching map data.");
        return;
      }
      const data = await response.json();
      window.open(data.map_url, "_blank");
    } catch (error) {
      setSearchError("Failed to retrieve maps data.");
    }
  };


  // CRUD Functions for Weather Queries
  useEffect(() => {
    fetchQueries();
  }, []);

  const fetchQueries = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/weatherQueries");
      if (!response.ok) throw new Error("Error fetching queries.");
      const data = await response.json();
      setQueries(data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleCreateQuery = async () => {
    setCrudError("");
    if (!newQuery.location.trim() || !newQuery.start_date || !newQuery.end_date) {
      setCrudError("Please provide a location and valid date ranges (YYYY-MM-DD).");
      return;
    }
    try {
      const response = await fetch("http://localhost:5000/api/weatherQuery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newQuery),
      });
      const data = await response.json();
      if (!response.ok) {
        setCrudError(data.error || "Error creating weather query.");
        return;
      }
      setNewQuery({ location: "", start_date: "", end_date: "" });
      fetchQueries();
    } catch (error) {
      setCrudError("Failed to create weather query.");
    }
  };

  const startEditQuery = (query) => {
    setEditingQuery(query);
  };

  const handleUpdateQuery = async () => {
    if (!editingQuery.location.trim() || !editingQuery.start_date || !editingQuery.end_date) {
      setCrudError("Please provide a location and valid date ranges (YYYY-MM-DD).");
      return;
    }
    try {
      const response = await fetch(
        `http://localhost:5000/api/weatherQuery/${editingQuery.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(editingQuery),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        setCrudError(data.error || "Error updating weather query.");
        return;
      }
      setEditingQuery(null);
      fetchQueries();
    } catch (error) {
      setCrudError("Failed to update query.");
    }
  };

  const handleDeleteQuery = async (id) => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/weatherQuery/${id}`,
        { method: "DELETE" }
      );
      const data = await response.json();
      if (!response.ok) {
        setCrudError(data.error || "Error deleting weather query.");
        return;
      }
      fetchQueries();
    } catch (error) {
      setCrudError("Failed to delete query.");
    }
  };


  // Export Forecast Dates (with forecast info) Function
  const exportForecastDates = (format) => {
    if (!location.trim()) {
      setSearchError("Please enter a location before exporting forecast info.");
      return;
    }
    window.open(
      `http://localhost:5000/api/exportForecast?location=${encodeURIComponent(location)}&format=${format}`,
      "_blank"
    );
  };

  return (
    <div className="container">
      {/* HEADER */}
      <header>
        <h1>Weather App - Product Manager Accelerator</h1>
        <p>From entry-level to VP of Product, we support PM professionals through every stage of their careers.</p>
      </header>
      <main>
        {/* WEATHER SEARCH SECTION */}
        <section className="section-box">
          <h2>Search Weather</h2>
          <div className="weather-input">
            <input
              type="text"
              value={location}
              onChange={handleInputChange}
              placeholder="Enter location (City, Zip, or 'lat,lon')"
            />
            <button onClick={getWeather}>Get Weather</button>
            <button onClick={getCurrentLocationWeather}>Use Current Location</button>
            <button onClick={openMap}>Open Map</button>
          </div>
          {loading && <p>Loading...</p>}
          {searchError && <div className="error">{searchError}</div>}
          {weatherData && !loading && (
            <div className="weather-display">
              <h3>Current Weather</h3>
              <p>
                <strong>Temperature:</strong> {weatherData.current.main.temp} °C
              </p>
              <p>
                <strong>Weather:</strong> {weatherData.current.weather[0].description}
              </p>
              <h4>5-Day Forecast</h4>
              <div className="forecast-list">
                {(() => {
                  const grouped = groupForecastByDay(weatherData.forecast.list);
                  const dates = Object.keys(grouped).sort().slice(0, 5);
                  return dates.map((date) => {
                    const dayItems = grouped[date];
                    const minTemp = Math.min(...dayItems.map(item => item.main.temp_min));
                    const maxTemp = Math.max(...dayItems.map(item => item.main.temp_max));
                    return (
                      <div key={date} className="forecast-item">
                        <p><strong>Date:</strong> {date}</p>
                        <p>
                          <strong>Temp Range:</strong> {minTemp.toFixed(1)} °C - {maxTemp.toFixed(1)} °C
                        </p>
                        <p>
                          <strong>Condition:</strong> {dayItems[0].weather[0].description}
                        </p>
                      </div>
                    );
                  });
                })()}
              </div>
              <div className="export-section">
                <h4>Export 5-Day Forecast Info</h4>
                <button onClick={() => exportForecastDates("json")}>Export as JSON</button>
                <br />
                <button onClick={() => exportForecastDates("csv")}>Export as CSV</button>
              </div>
            </div>
          )}
        </section>

        {/* CRUD WEATHER QUERIES SECTION */}
        <section className="section-box">
          <h2>Manage Weather Queries</h2>
          {crudError && <div className="error">{crudError}</div>}
          <div className="crud-form">
            <h4>Create New Query</h4>
            <input
              type="text"
              placeholder="Location"
              value={newQuery.location}
              onChange={(e) =>
                setNewQuery({ ...newQuery, location: e.target.value })
              }
            />
            <input
              type="text"
              placeholder="Start Date (YYYY-MM-DD)"
              value={newQuery.start_date}
              onChange={(e) =>
                setNewQuery({ ...newQuery, start_date: e.target.value })
              }
            />
            <input
              type="text"
              placeholder="End Date (YYYY-MM-DD)"
              value={newQuery.end_date}
              onChange={(e) =>
                setNewQuery({ ...newQuery, end_date: e.target.value })
              }
            />
            <button onClick={handleCreateQuery}>Create Query</button>
          </div>
          <div className="queries-list">
            <h4>Existing Queries</h4>
            {queries.map((q) => (
              <div key={q.id} className="query-item">
                {editingQuery && editingQuery.id === q.id ? (
                  <>
                    <input
                      type="text"
                      value={editingQuery.location}
                      onChange={(e) =>
                        setEditingQuery({ ...editingQuery, location: e.target.value })
                      }
                    />
                    <input
                      type="text"
                      value={editingQuery.start_date}
                      placeholder="Start Date (YYYY-MM-DD)"
                      onChange={(e) =>
                        setEditingQuery({ ...editingQuery, start_date: e.target.value })
                      }
                    />
                    <input
                      type="text"
                      value={editingQuery.end_date}
                      placeholder="End Date (YYYY-MM-DD)"
                      onChange={(e) =>
                        setEditingQuery({ ...editingQuery, end_date: e.target.value })
                      }
                    />
                    <button onClick={handleUpdateQuery}>Save</button>
                    <button onClick={() => setEditingQuery(null)}>Cancel</button>
                  </>
                ) : (
                  <>
                    <p><strong>ID:</strong> {q.id}</p>
                    <p><strong>Location:</strong> {q.location}</p>
                    <p>
                      <strong>Date Range:</strong> {q.start_date} - {q.end_date}
                    </p>
                    <button onClick={() => startEditQuery(q)}>Edit</button>
                    <button onClick={() => handleDeleteQuery(q.id)}>Delete</button>
                  </>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>
      <footer>
        <p>
          © Product Manager Accelerator. From entry-level to VP of Product, we support PM professionals through every stage of their careers.
        </p>
      </footer>
    </div>
  );
}

export default App;
