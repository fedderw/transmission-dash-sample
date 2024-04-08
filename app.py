# Import necessary libraries for Dash and callbacks
from dash import Dash, html, dcc, callback, Input, Output
import dash_ag_grid as dag
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import json
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import random  # Add this at the beginning of your script

# Load data for AG Grid and Leaflet Map
# Number of rows to read (including the header)
rows_to_read = 38

df_eis_lines = pd.read_csv("data/eis_lines.csv", nrows=rows_to_read, index_col=0)

# Parse the GeoJSON string to a dictionary
eis_lines_gdf = gpd.read_file("data/eis_lines.geojson")
# Merge the GeoDataFrame with the DataFrame
eis_lines_gdf = eis_lines_gdf.merge(df_eis_lines, on="Name")
print(eis_lines_gdf.head(5))
# Convert the GeoDataFrame back to GeoJSON
eis_lines_geojson = json.loads(eis_lines_gdf.to_json())
print(type(eis_lines_geojson))
# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Function to create tooltip content
def create_tooltip_content(feature):
    props = feature['properties']
    tooltip_content = (
        f"Name: {props.get('Name', 'N/A')}<br/>"
        f"Category: {props.get('Category', 'N/A')}<br/>"
        f"Line Length: {props.get('Line Length (mi)', 'N/A')} mi<br/>"
        f"Voltage: {props.get('Dominant Line Voltage (kV)', 'N/A')} kV<br/>"
        f"States: {props.get('States', 'N/A')}<br/>"
        f"Status: {props.get('Status of NEPA review', 'N/A')}<br/>"
        # Add more properties as needed
    )
    return tooltip_content


# Define layout of the app
# Define layout of the app
app.layout = dbc.Container(children=[
    dbc.Row([
        dbc.Col([
            dl.Map(
                center=[37.0902, -95.7129],
                zoom=4,
                children=[
                    dl.TileLayer(),
                    dl.GeoJSON(
                        data=eis_lines_geojson,
                        id="map-geojson",
                        children=[
                            dl.Tooltip(
                                children=create_tooltip_content(feature),
                                sticky=True
                            ) for feature in eis_lines_geojson['features']
                        ]
                    )
                ],
                style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"},
                id="leaflet-map"
            )
        ], width=6),
        dbc.Col([
            dcc.Graph(id='gantt-chart')  # Placeholder for Gantt chart
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dag.AgGrid(
                id="eis-lines-grid",
                rowData=df_eis_lines.to_dict("records"),
                columnDefs=[
                    {
                        'field': col,
                        'filter': True,  # Enable filtering on this column
                        'sortable': True # Enable sorting on this column
                    }
                    for col in df_eis_lines.columns
                ],
                style={'width': '100%', 'height': '300px'},
                dashGridOptions={"rowSelection": "multiple"}  # Enable multiple row selection for filtering
            )
        ])
    ])
])

# Callback for updating the Gantt chart and Leaflet Map based on AG-Grid selection
@app.callback(
    Output('map-geojson', 'data'),
    [Input("eis-lines-grid", "virtualRowData"),Input('eis-lines-grid', 'selectedRowKeys')]
)
def update_based_on_grid_selection(rows,selected_row_keys):
    if not selected_row_keys:
        # If no rows are selected, show default or all data
        filtered_geojson = eis_lines_geojson
    else:
        # Filter the DataFrame based on selected rows
        selected_rows = [int(row_id) for row_id in selected_row_keys if selected_row_keys[row_id]]
        filtered_df = df_eis_lines.iloc[selected_rows]
        filtered_names = filtered_df['Name'].tolist()
        filtered_geojson = {
            "type": "FeatureCollection",
            "features": [feature for feature in eis_lines_geojson['features']
                         if feature['properties']['Name'] in filtered_names]
        }

    # Return updated GeoJSON for the map
    return filtered_geojson

# Callback for updating the Gantt chart based on AG-Grid selection
@app.callback(
    Output('gantt-chart', 'figure'),
    [Input("eis-lines-grid", "virtualRowData"),Input('eis-lines-grid', 'selectedRowKeys')]
)
def update_gantt_chart(rows, selected_row_keys):
    if selected_row_keys:
        selected_rows = [int(row_id) for row_id in selected_row_keys if selected_row_keys[row_id]]
        selected_names = [df_eis_lines.iloc[i]['Name'] for i in selected_rows]
        filtered_df = df_eis_lines[df_eis_lines['Name'].isin(selected_names)]
    else:
        filtered_df = df_eis_lines
    
    # Convert date columns to datetime, handling errors
    filtered_df['Date of NOI Publication'] = pd.to_datetime(filtered_df['Date of NOI Publication'], errors='coerce')
    filtered_df['Date last ROD published'] = pd.to_datetime(filtered_df['Date last ROD published'], errors='coerce')

    # Create figure for the timeline
    fig = px.timeline(
        filtered_df,
        x_start='Date of NOI Publication',
        x_end='Date last ROD published',
        y='Name',
        labels={'Name': 'Project Name'},
        title='Project Timeline'
    )

    # Update layout for better readability
    fig.update_layout({
        'xaxis_title': 'Date',
        'yaxis_title': 'Project',
        'yaxis': {'autorange': 'reversed'},  # Reverse axis so it goes top-down
        'showlegend': False
    })

    # Return the figure
    return fig

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
