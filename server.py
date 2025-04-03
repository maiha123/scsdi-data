import dash
from dash import dcc, html, Input, Output, Dash
import dash_leaflet as dl
import geopandas as gpd
import pandas as pd
from flask import Flask
import shapely
import datetime
from app import app  # Assuming your Dash app is wrapped in Flask in app.py

#-----
# Initialize Flask app
server = Flask(__name__)
app = Dash(__name__, server=server, url_base_pathname="/dashboard/")  
#------

# Load dataset
dataset_path = "/Users/hanguyen/Documents/SCSDI/Data"
buffers = [gpd.read_file(f"{dataset_path}/buffer{i}.gpkg") for i in (1, 2, 34, 5, 6)]
buffer_all = gpd.GeoDataFrame(pd.concat(buffers, ignore_index=True))

# Clean date column
buffer_all['event_date'] = buffer_all['event_date'].str.split(" - ").str[0]  # Take only the start date
buffer_all["event_date"] = pd.to_datetime(buffer_all["event_date"], errors="coerce")
buffer_all = buffer_all.dropna(subset=["event_date"]) #

# Initialize Dash app
app = dash.Dash(__name__)

# Sort data by event_date
buffer_all = buffer_all.sort_values("event_date")

# Get unique countries
unique_countries = buffer_all["event_id_cnty"].dropna().unique()

app.layout = html.Div([
    html.H1("South China Sea Disputes - Interactive Map"),

    # Filters: Date Range & Country Selection
    html.Div([
        html.Label("Select date range:", style={"font-weight": "bold"}),
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=buffer_all["event_date"].min(),
            max_date_allowed=buffer_all["event_date"].max(),
            start_date=buffer_all["event_date"].min(),
            end_date=buffer_all["event_date"].max(),
            display_format="YYYY-MM-DD"  # Format for better usability
        ),
    ], style={"width": "50%", "margin": "auto", "padding": "20px"}),
    
        # Separate div to ensure "Select countries" appears on a new line

        # Country Dropdown
    html.Div([
        html.Label("Select countries:"),
        dcc.Dropdown(
            options=[{"label": country, "value": country} for country in unique_countries],
            multi=True,
            id="country-dropdown",
            placeholder="Select one or more countries"

        ),
    ], style={"width": "50%", "margin": "auto", "padding-bottom": "2px"}),

    # OK Button
    #html.Div([
    #    html.Button("OK", id="apply-filters", n_clicks=0, style={"margin-top": "10px", "width": "100px"}),

    #], style={
    #    "width": "50%",
    #    "margin": "auto",
    #    "padding": "20px",
    #    "background-color": "white",
    #    "border-radius": "10px",
    #    "box-shadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
    #    "position": "relative",
    #    "zIndex": "10000"  # Ensures dropdown is above the map
    #}),

    # Map container
    dl.Map(
        [dl.TileLayer(), dl.LayerGroup(id="geojson-layer")],
        center=[10, 110], zoom=5, style={"height": "80vh", "width": "100%"}, id="map"
    )
])

@app.callback(
    Output("geojson-layer", "children"),
    [
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("country-dropdown", "value")
    ]
)

#def update_map(start_date, end_date, selected_countries):
    # Convert date strings to datetime
#    start_date = pd.to_datetime(start_date)
#    end_date = pd.to_datetime(end_date)

    # Filter data based on selected date range
#    df = buffer_all[(buffer_all["event_date"] >= start_date) & (buffer_all["event_date"] <= end_date)]

    # Filter by country selection
#    if selected_countries:
#        df = df[df["event_id_cnty"].isin(selected_countries)]
    
    # Create GeoJSON features
#    geojson_features = [
#        dl.GeoJSON(data=df.__geo_interface__, id="filtered-geojson")
#    ]
    
#    return geojson_features

def update_map(start_date, end_date, selected_countries):
    # Convert date strings to datetime
    start_date = pd.to_datetime(start_date) if start_date else None
    end_date = pd.to_datetime(end_date) if end_date else None
#    selected_countries = selected_countries if selected_countries else unique_countries

    # Ensure selected_countries is not empty
    if not selected_countries or len(selected_countries) == 0:
        selected_countries = unique_countries  # Default to all countries

    # Filter data:
    df = buffer_all[
        (buffer_all["event_date"] >= start_date) &
        (buffer_all["event_date"] <= end_date) &
        (buffer_all["event_id_cnty"].isin(selected_countries))
    ]
    
    # Convert MultiPolygon geometries to centroids
    df["geometry"] = df["geometry"].apply(lambda g: g.centroid if g.geom_type in ["Polygon", "MultiPolygon"] else g)

    # Create CircleMarkers with fixed radius
    circle_markers = [
        dl.CircleMarker(
            center=[row.geometry.y, row.geometry.x],  # Lat, Lon from centroid
            radius=5,  # Fixed radius
            color="blue",
            fill=True,
            fillColor="blue",
            fillOpacity=0.5,
            children=dl.Tooltip(row["notes"] if pd.notna(row["notes"]) else "No notes available"),
        )
        for _, row in df.iterrows() if isinstance(row.geometry, shapely.geometry.Point)
    ]

    return circle_markers


if __name__ == "__main__":
#    server = app.server
    app.run(debug=True)
#    server.run(host="0.0.0.0", port=8000)
#    app.run(debug=False, host="0.0.0.0", port=5000)

