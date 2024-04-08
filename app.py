# Import necessary libraries for Dash and callbacks
from dash import Dash, html, dcc, callback, Input, Output
import dash_ag_grid as dag
import dash_leaflet as dl
import pandas as pd
import json
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

# Load data for AG Grid and Leaflet Map
# Number of rows to read (including the header)
rows_to_read = 38

df_eis_lines = pd.read_csv("data/eis_lines.csv", nrows=rows_to_read)

# Parse the GeoJSON string to a dictionary
eis_lines_geojson = json.loads(gpd.read_file("data/eis_lines.geojson").to_json())

# Initialize Dash app
app = Dash(__name__)
# Ensure options are in the correct format for the Dropdown component
dropdown_options = [{'label': str(line), 'value': str(line)} for line in df_eis_lines['Name'].unique()]

# Define layout of the app
app.layout = html.Div([
    dl.Map(
        center=[37.0902, -95.7129], # Example center for map (latitude, longitude of USA)
        zoom=4, # Zoom level for map
        children=[
            dl.TileLayer(), # Base layer
            dl.GeoJSON(data=eis_lines_geojson, id="map-geojson") # GeoJSON layer for transmission lines
        ],
        style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"},
        id="leaflet-map"
    ),
    dcc.Dropdown( # Dropdown for selecting transmission lines
        id='line-selector',
        options=[{'label': line, 'value': line} for line in df_eis_lines['Name'].unique()],
        value=df_eis_lines['Name'].unique()[1], # Default value
        style={'width': '50%', 'padding': '10px'}
        multi=True,
    ),
    dag.AgGrid( # AG Grid component
        id="eis-lines-grid",
        rowData=df_eis_lines.to_dict("records"),
        columnDefs=[{'field': col} for col in df_eis_lines.columns], # Define columns based on dataframe
        style={'width': '100%', 'height': '300px'}
    ),
    dcc.Graph(id='gantt-chart'), # Placeholder for Gantt chart
])

# Callback for updating the Gantt chart based on selected line
@callback(
    Output('gantt-chart', 'figure'),
    Input('line-selector', 'value')
)
def update_gantt_chart(selected_line):
    # Filter data based on selected line
    df_selected_line = df_eis_lines[df_eis_lines['Name'] == selected_line]
    # Use "Date of NOI Publication" instead of "Start Date"
    fig = go.Figure(data=[
        go.Bar(x=df_selected_line['Date of NOI Publication'], y=df_selected_line['Name'])
    ])
    fig.update_layout(title='Gantt Chart')
    return fig

# Callback for updating the Leaflet Map based on selected line
@callback(
    Output('map-geojson', 'data'),
    Input('line-selector', 'value')
)
def update_leaflet_map(selected_line):
    # Filter GeoJSON based on selected line
    # Example placeholder logic below
    selected_geojson = {
        "type": "FeatureCollection",
        "features": [feature for feature in eis_lines_geojson['features']
                     if feature['properties']['Name'] == selected_line]
    }
    return selected_geojson

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
