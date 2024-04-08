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

df_eis_lines = pd.read_csv(
    "data/eis_lines.csv", nrows=rows_to_read, index_col=0
)

# Parse the GeoJSON string to a dictionary
eis_lines_gdf = gpd.read_file("data/eis_lines.geojson")
# Merge the GeoDataFrame with the DataFrame
eis_lines_gdf = eis_lines_gdf.merge(df_eis_lines, on="Name")
# print(eis_lines_gdf.head(5))
# Convert the GeoDataFrame back to GeoJSON
eis_lines_geojson = json.loads(eis_lines_gdf.to_json())
# print(type(eis_lines_geojson))
# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Function to create tooltip content
def create_tooltip_content(feature):
    props = feature["properties"]
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
app.layout = dbc.Container(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    [
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
                                            children=create_tooltip_content(
                                                feature
                                            ),
                                            sticky=True,
                                        )
                                        for feature in eis_lines_geojson[
                                            "features"
                                        ]
                                    ],
                                ),
                            ],
                            style={
                                "width": "100%",
                                "height": "50vh",
                                "margin": "auto",
                                "display": "block",
                            },
                            id="leaflet-map",
                        )
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        dcc.Graph(
                            id="gantt-chart"
                        )  # Placeholder for Gantt chart
                    ],
                    width=6,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dag.AgGrid(
                            id="eis-lines-grid",
                            rowData=df_eis_lines.to_dict("records"),
                            columnDefs=[
                                {
                                    "field": col,
                                    "filter": True,  # Enable filtering on this column
                                    "sortable": True,  # Enable sorting on this column
                                    "checkboxSelection": True if col == 'Name' else False  # Add checkbox to 'Name' column only
                                }
                                for col in df_eis_lines.columns
                            ],
                            style={"width": "100%", "height": "300px"},
                            dashGridOptions={
                                "rowSelection": "multiple",
                                 "suppressRowClickSelection": True
                            },  # Enable multiple row selection for filtering
                        )
                    ]
                )
            ]
        ),
    ]
)

@app.callback(
    Output("leaflet-map", "children"),
    [
        Input("eis-lines-grid", "virtualRowData"),
        Input("eis-lines-grid", "selectedRows"),
    ],
)
def update_based_on_grid_selection(virtualRowData, selected_rows):
    if selected_rows is None:
        selected_rows = []
    print(f"Selected Rows: {selected_rows}")
    print(f"Virtual Row Data preview: {virtualRowData[:1]}")
    
    selected_names = [virtualRowData[i]['Name'] for i in selected_rows] if selected_rows else []
    print(f"Selected Names: {selected_names}")
    if not selected_names:
        # If no rows are selected, show all data
        geojson_layer = dl.GeoJSON(data=eis_lines_geojson, id="geojson")
    else:
        # Filter the GeoJSON data based on selected rows
        filtered_features = [
            feature
            for feature in eis_lines_geojson["features"]
            if feature["properties"]["Name"] in selected_names
        ]
        geojson_layer = dl.GeoJSON(data={"type": "FeatureCollection", "features": filtered_features}, id="geojson")

    # Return the updated children for the map
    return [
        dl.TileLayer(),  # Default OpenStreetMap layer
        geojson_layer,
    ]
    
    
@app.callback(
    Output("gantt-chart", "figure"),
    [
        Input("eis-lines-grid", "virtualRowData"),
        Input("eis-lines-grid", "selectedRows"),
    ],
)
def update_gantt_chart(rows, selected_rows):
    dff = df_eis_lines if rows is None else pd.DataFrame(rows)
    selected_names = [s["Name"] for s in selected_rows] if selected_rows else []

    if selected_names:
        filtered_df = dff[dff["Name"].isin(selected_names)]
    else:
        filtered_df = dff

    # Convert date columns to datetime, handling errors
    filtered_df["Date of NOI Publication"] = pd.to_datetime(
        filtered_df["Date of NOI Publication"], errors="coerce"
    )
    filtered_df["Date last ROD published"] = pd.to_datetime(
        filtered_df["Date last ROD published"], errors="coerce"
    )

    # Create figure for the timeline
    fig = px.timeline(
        filtered_df,
        x_start="Date of NOI Publication",
        x_end="Date last ROD published",
        y="Name",
        labels={"Name": "Project Name"},
        title="Project Timeline",
    )

    # Update layout for better readability
    fig.update_layout(
        {
            "xaxis_title": "Date",
            "yaxis_title": "Project",
            "yaxis": {
                "autorange": "reversed"
            },  # Reverse axis so it goes top-down
            "showlegend": False,
        }
    )

    # Return the figure
    return fig

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
