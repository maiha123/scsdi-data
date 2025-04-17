import dash
from dash import dcc, html, Input, Output, Dash
import dash_leaflet as dl
import geopandas as gpd
import pandas as pd
from flask import Flask
import shapely
import datetime
import requests
import os

# Initialize Flask app

app = Dash(__name__)
server = app.server

# Load dataset
#dataset_path = "/Users/hanguyen/Documents/SCSDI/Data/data"
dataset_path = os.path.join(os.path.dirname(__file__), "data")

buffers = [gpd.read_file(f"{dataset_path}/buffer{i}.gpkg") for i in (1, 2, 34, 5, 6)]
buffer_all = gpd.GeoDataFrame(pd.concat(buffers, ignore_index=True))

# Clean date column
buffer_all['event_date'] = buffer_all['event_date'].str.split(" - ").str[0]
buffer_all["event_date"] = pd.to_datetime(buffer_all["event_date"], errors="coerce")
buffer_all = buffer_all.dropna(subset=["event_date"])

# Sort data by event_date
buffer_all = buffer_all.sort_values("event_date")

# Split combined country codes and get unique individual countries
buffer_all['countries'] = buffer_all['event_id_cnty'].str.split('/')  # Split into lists
all_countries = buffer_all['countries'].explode().unique()             # Get individual countries
all_countries = [c for c in all_countries if c is not None]            # Remove any None values

app.layout = html.Div([
    # html.H1("South China Sea Disputes - Interactive Map"),
    
    # Filters: Date Range & Country Selection
    html.Div([
        html.Label("Select date range:", style={"font-weight": "bold"}),
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=buffer_all["event_date"].min(),
            max_date_allowed=buffer_all["event_date"].max(),
            start_date=buffer_all["event_date"].min(),
            end_date=buffer_all["event_date"].max(),
            display_format="YYYY-MM-DD"
        ),
    ], style={"width": "50%", "margin": "auto", "padding": "20px"}),
    
    html.Div([
        html.Label("Select countries:", style={"font-weight": "bold"}),
        dcc.Dropdown(
            options=[{"label": c, "value": c} for c in all_countries],
            multi=True,
            id="country-dropdown",
            placeholder="Select one or more individual countries"
        ),
    ], style={"width": "50%", "margin": "auto", "padding-bottom": "2px"}),

    dl.Map(
        [dl.TileLayer(), dl.LayerGroup(id="geojson-layer")],
        center=[10, 110], zoom=5, style={"height": "80vh", "width": "100%"}, id="map"
    ), 

    # Hidden div to store clicked event data (optional for advanced use)
    html.Div(id="hidden-event-data", style={"display": "none"})

])

@app.callback(
    Output("geojson-layer", "children"),
    [
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("country-dropdown", "value")
    ]
)
def update_map(start_date, end_date, selected_countries):
    # Convert date strings to datetime
    start_date = pd.to_datetime(start_date) if start_date else None
    end_date = pd.to_datetime(end_date) if end_date else None
    
    # Filter by date first
    date_mask = (
        (buffer_all["event_date"] >= start_date) &
        (buffer_all["event_date"] <= end_date)
    )
    df = buffer_all[date_mask]
    
    # Filter by countries if any are selected
    if selected_countries:
        country_mask = df['countries'].apply(
            lambda x: any(c in selected_countries for c in x)
        )
        df = df[country_mask]
    
    # Convert geometries to centroids if needed
    df["geometry"] = df["geometry"].apply(
        lambda g: g.centroid if g.geom_type in ["Polygon", "MultiPolygon"] else g
    )

    # Create CircleMarkers with clickable popups
    circle_markers = []
    for _, row in df.iterrows():
        if isinstance(row.geometry, shapely.geometry.Point):
            # Build popup content
            popup_content = html.Div([
                html.H4(f"Event ID: {row.get('event_id', 'N/A')}"),
                html.P(f"Countries: {row['event_id_cnty']}"),
                html.P(f"Notes: {row['notes']}"),
                html.P(f"Source: {row.get('source', 'N/A')}"),
                html.P(f"Ships Involved: {row.get('ships_involved', 'N/A')}"),
		
		# Add hyperlink if a source URL exists
                html.A("Source Link", href=row.get("source_url"), target="_blank") 
                if pd.notna(row.get("source_url")) else html.P()
                ],
                style={
                    "userSelect": "text",  # Allow text selection
                    "cursor": "text",      # Show text cursor
                    "fontFamily": "Arial",
                    "fontSize": "14px"
                }
            )
            
            # Create marker with tooltip (hover) and popup (click)
            marker = dl.CircleMarker(
                center=[row.geometry.y, row.geometry.x],
                radius=5,
                color="#1f77b4",
                fill=True,
                fillColor="#1f77b4",
                fillOpacity=0.5,
                children=[
                #   dl.Tooltip(row["notes"] if pd.notna(row["notes"]) else "No notes available"),
                    dl.Popup(popup_content)  # This adds the clickable popup
                ],
                id=f"marker-{row.name}"  # Optional: for advanced interactivity
            )
            circle_markers.append(marker)
    
    return circle_markers

if __name__ == "__main__":
    app.run(debug=False)
