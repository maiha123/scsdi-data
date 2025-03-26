import dash
from dash import dcc, html, Input, Output
import dash_leaflet as dl
import geopandas as gpd
import pandas as pd

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

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("South China Sea Disputes - Interactive Map"),

    # Filters: Date Range & Country Selection
    html.Div([
        html.Label("Select date range:"),
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=buffer_all["event_date"].min(),
            max_date_allowed=buffer_all["event_date"].max(),
            start_date=buffer_all["event_date"].min(),
            end_date=buffer_all["event_date"].max(),
            display_format="YYYY-MM-DD"  # Format for better usability
        ),

        # Country Dropdown
        html.Label("Select countries:"),
        dcc.Dropdown(
            options=[{"label": country, "value": country} for country in buffer_all["event_id_cnty"].dropna().unique()],
            multi=True,
            id="country-dropdown"
        ),
    ], style={"width": "50%", "margin": "auto", "padding": "20px"}),

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

def update_map(start_date, end_date, selected_countries):
    # Convert date strings to datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter data based on selected date range
    df = buffer_all[(buffer_all["event_date"] >= start_date) & (buffer_all["event_date"] <= end_date)]

    # Filter by country selection
    if selected_countries:
        df = df[df["event_id_cnty"].isin(selected_countries)]
    
    # Create GeoJSON features
    geojson_features = [
        dl.GeoJSON(data=df.__geo_interface__, id="filtered-geojson")
    ]
    
    return geojson_features

if __name__ == "__main__":
#    app.run(debug=True)
    server.run(host="0.0.0.0", port=8000)
