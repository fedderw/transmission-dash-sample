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
    # dcc.Dropdown( # Dropdown for selecting transmission lines
    #     id='line-selector',
    #     options=[{'label': line, 'value': line} for line in df_eis_lines['Name'].unique()],
    #     value=df_eis_lines['Name'].unique()[1], # Default value
    #     style={'width': '50%', 'padding': '10px'}
    #     multi=True,
    # ),
    dag.AgGrid(
        id="eis-lines-grid",
        rowData=df_eis_lines.to_dict("records"),
        columnDefs=[
            {'field': col, 'filter': 'agTextColumnFilter', 'sortable': True}
            for col in df_eis_lines.columns
        ],
        style={'width': '100%', 'height': '300px'},
        enableFilter=True,   # Enable filtering
        enableSorting=True,  # Enable sorting
        rowSelection='multiple',  # Enable multiple row selection for filtering
    ),
    dcc.Graph(id='gantt-chart'), # Placeholder for Gantt chart
])

# Callback for updating the Gantt chart and Leaflet Map based on AG-Grid selection
@callback(
    [Output('gantt-chart', 'figure'),
     Output('map-geojson', 'data')],
    [Input('eis-lines-grid', 'selected_rows')]
)
def update_based_on_grid_selection(selected_rows):
    if not selected_rows:
        # If no rows are selected, show default or all data
        filtered_df = df_eis_lines
        filtered_geojson = eis_lines_geojson
    else:
        # Filter the DataFrame based on selected rows
        filtered_df = df_eis_lines.iloc[selected_rows]
        filtered_names = filtered_df['Name'].tolist()
        filtered_geojson = {
            "type": "FeatureCollection",
            "features": [feature for feature in eis_lines_geojson['features']
                         if feature['properties']['Name'] in filtered_names]
        }

    # Update Gantt chart
    gantt_fig = go.Figure(data=[
        go.Bar(x=filtered_df['Date of NOI Publication'], y=filtered_df['Name'])
    ])
    gantt_fig.update_layout(title='Gantt Chart')

    # Return updated Gantt chart and GeoJSON for the map
    return gantt_fig, filtered_geojson



# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
