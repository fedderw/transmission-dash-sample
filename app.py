# Project Overview:

# This Python script aims to facilitate the visualization and analysis of data regarding transmission line permitting, as outlined in the report published by Niskanen in collaboration with the Clean Air Task Force. The dataset encompasses statistics on 37 transmission lines that underwent federal environmental permitting review between 2010 and 2020.

# Goals:

# Data Compilation: The script compiles data scattered across various company and government websites, consolidating it into a cohesive dataset for analysis.

# Visualization Enhancement: The objective is to present the data in a more visually engaging and intuitive manner to broaden its accessibility and usability. This includes:

# Creating an interactive map displaying the 37 transmission lines, akin to the Politico piece referenced.
# Providing individual project breakouts within the map, showcasing timelines and permitting process statistics.
# Developing a sortable and interactive version of the dataset, similar to the Brookings model, to facilitate efficient data exploration.
# Interactive Features: Implementation of interactive features allows users to:

# Sort and filter the dataset based on various parameters.
# Access additional information and insights about each transmission line project.
# Potentially incorporate supplementary map layers depicting congressional districts or energy resources.

# Import necessary libraries for Dash and callbacks
from dash import Dash, html, dcc, callback, Input, Output, State
import dash_ag_grid as dag
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import json
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import random  # Add this at the beginning of your script
from datetime import datetime
import numpy as np
import re
# Load data for AG Grid and Leaflet Map
# Number of rows to read (including the header)
rows_to_read = 38

df_eis_lines = pd.read_csv(
    "data/eis_lines.csv", nrows=rows_to_read, index_col=0
)
df_eis_lines_urls = pd.read_csv("data/eis_lines_urls.csv", index_col=0)
df_eis_lines = df_eis_lines.merge(df_eis_lines_urls, left_index=True, right_index=True, suffixes=('', '_url'))
df_eis_lines['Project'] = df_eis_lines.apply(lambda row: f"[{row['Name']}]({row['Name_url']})", axis=1)
# Parse the GeoJSON string to a dictionary
eis_lines_gdf = gpd.read_file("data/eis_lines.geojson")
# Merge the GeoDataFrame with the DataFrame
eis_lines_gdf = eis_lines_gdf.merge(df_eis_lines, on="Name")
# print(eis_lines_gdf.head(5))
# Convert the GeoDataFrame back to GeoJSON
eis_lines_geojson = json.loads(eis_lines_gdf.to_json())

# Congressional Districts GeoJSON
# cds = gpd.read_file("https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_118th_Congressional_Districts/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson")
# print(type(eis_lines_geojson))
# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.scripts.append_script({"external_url": "assets/dashAgGridComponentFunctions.js"})
server = app.server

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

columnDefs = [
    {
        "field": 'Project',
        "filter": True,  # Enable filtering on this column
        "sortable": True,  # Enable sorting on this column
        "checkboxSelection": True,  # Add checkbox to 'Project' column only
        "cellRenderer": "markdown",  # Add markdown renderer to 'Project' column only
    }
] + [
{
    "field": 'Details',
    "cellRenderer": 'agGroupCellRenderer',
    "cellRendererParams": {
        "innerRenderer": 'buttonRenderer',
    },
    "cellClass": 'details-button',
    "width": 100,
},
] + [
    {
        "field": col,
        "filter": True,  # Enable filtering on this column
        "sortable": True,  # Enable sorting on this column
        "checkboxSelection": False,  # No checkbox for other columns
        "cellRenderer": None,  # No markdown renderer for other columns
        "hide": True if col == 'Name' else False,  # Hide 'Name' column
    }
    for col in df_eis_lines.columns if col != 'Project' and not col.endswith('_url')  # Exclude 'Project' and '_url' columns
]
# Define layout of the app
# Define layout of the app
app.layout = dbc.Container(
    children=[
        html.H1("Transmission Line Permitting Visualization"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dl.Map(
                            center=[37.0902, -95.7129],
                            zoom=3,
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
                    width=4,
                ),
                dbc.Col(
                    [
                         dmc.LoadingOverlay(dcc.Graph(
                            id="gantt-chart"
                        ),loaderProps={"variant": "dots", "color": "orange", "size": "xl"},) # Placeholder for Gantt chart
                    ],
                    width=8,
                ),
            ]
        ),
        html.Div(style={"height": "30px"}),  # Add space between rows
        dbc.Row(
            [
                dbc.Col(
                    [
                        dag.AgGrid(
                            id="eis-lines-grid",
                            rowData=df_eis_lines.to_dict("records"),
                            columnDefs=columnDefs,
                            style={"width": "100%", "height": "300px"},
                            dashGridOptions={
                                "rowSelection": "multiple",
                                 "suppressRowClickSelection": True
                            },  # Enable multiple row selection for filtering
                            dangerously_allow_code=True,
                        )
                    ]
                )
            ]
        ),
        html.Hr(),
        html.Footer(
            "For any inquiries, please contact [Your Name] at [Your Email Address]."
        ),
        html.Div(
            [
                dmc.Button("About", id="drawer-demo-button"),
                dmc.Drawer(
                    title="Drawer Example",
                    id="drawer-simple",
                    padding="md",
                    zIndex=10000,
                ),
            ]
        ),
        dbc.Modal(
            [
                dbc.ModalHeader("Details"),
                dbc.ModalBody("Lorem ipsum dolor sit amet, consectetur adipiscing elit."),
            ],
            id="modal",
        ),
        html.Div(id='debug')
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
    gdff = eis_lines_gdf if virtualRowData is None else eis_lines_gdf.merge(pd.DataFrame(virtualRowData), on="Name", how="inner")
    selected_names = [s["Name"] for s in selected_rows] if selected_rows else []
    
    if selected_names:
        filtered_gdf = gdff[gdff["Name"].isin(selected_names)]
        filtered_geojson = json.loads(filtered_gdf.to_json())
    else:
        filtered_gdf = gdff
        filtered_geojson = json.loads(filtered_gdf.to_json())
        
    # filtered_geojson = json.loads(filtered_gdf.to_json())
    # Update the chldren of "map-geojson" with the filtered GeoJSON
    return [
        dl.TileLayer(),
        dl.GeoJSON(data=filtered_geojson, id="map-geojson", children=[
            dl.Tooltip(
                children=create_tooltip_content(feature),
                sticky=True
            ) for feature in filtered_geojson["features"]
        ])
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


    # Define color mapping
    color_mapping = {
        'Complete': '#66c2a5',  # Light green
        'Canceled': '#fc8d62',  # Light orange
        'Underway': '#8da0cb',  # Light blue
        'Unknown': '#e78ac3',  # Light pink
    }

    # Handle 'NaT' values and trailing spaces in 'Status of NEPA review' column
    filtered_df['Status of NEPA review'] = filtered_df['Status of NEPA review'].fillna('Unknown').str.strip()

    # Set 'Date last ROD published' to today's date for 'Underway' processes
    filtered_df.loc[filtered_df['Status of NEPA review'] == 'Underway', 'Date last ROD published'] = datetime.now()
    # Replace 'in progress' with NaN
    filtered_df['Year Federal EIS Issued'] = filtered_df['Year Federal EIS Issued'].replace('in progress', np.nan)


    # Convert 'Energized?' column to string and extract year
    filtered_df['Year Energized'] = filtered_df['Energized?'].astype(str).apply(lambda x: re.findall(r'\b\d{4}\b', x))
    filtered_df['Year Energized'] = filtered_df['Year Energized'].apply(lambda x: x[0] if x else np.nan)

    # Create separate dataframes for each phase
    df_proposed = filtered_df[['Name', 'Year project proposed']].copy()
    df_proposed['Phase'] = 'Proposed'
    df_proposed['Start'] = pd.to_datetime(df_proposed['Year project proposed'], format='%Y')
    df_proposed['Finish'] = pd.to_datetime(filtered_df['Date of NOI Publication'])

    df_noi = filtered_df[['Name', 'Date of NOI Publication']].copy()
    df_noi['Phase'] = 'NOI Published'
    df_noi['Start'] = pd.to_datetime(df_noi['Date of NOI Publication'])
    df_noi['Finish'] = pd.to_datetime(filtered_df['Year Federal EIS Issued'], format='%Y')

    df_eis = filtered_df[['Name', 'Year Federal EIS Issued']].copy()
    df_eis['Phase'] = 'EIS Issued'
    df_eis['Start'] = pd.to_datetime(df_eis['Year Federal EIS Issued'], format='%Y')
    df_eis['Finish'] = pd.to_datetime(filtered_df['Date last ROD published'])

    df_energized = filtered_df[['Name', 'Year Energized']].copy()
    df_energized['Phase'] = 'Energized'
    df_energized['Start'] = pd.to_datetime(df_energized['Year Energized'], format='%Y')
    df_energized['Finish'] = pd.to_datetime(df_energized['Year Energized'], format='%Y')

    # Handle 'in progress' status
    df_in_progress = filtered_df[filtered_df['Energized?'] == 'In progress'][['Name']].copy()
    df_in_progress['Phase'] = 'In progress'
    df_in_progress['Start'] = pd.to_datetime(filtered_df['Year Federal EIS Issued'], format='%Y')
    df_in_progress['Finish'] = pd.to_datetime(datetime.now().year, format='%Y')

    # Concatenate the dataframes
    df_timeline = pd.concat([df_proposed, df_noi, df_eis, df_energized, df_in_progress])

    # Create a timeline
    fig = px.timeline(df_timeline, x_start='Start', x_end='Finish', y='Name', color='Phase')

    # Update layout for better readability
    fig.update_layout(
        {
            "height": 600,  # Increase the height of the chart
            "bargap": 0.2,  # Add spacing between the bars
            "yaxis_title": None,
            "xaxis_title": None, 
            "yaxis": {
                "autorange": "reversed"
            },  # Reverse axis so it goes top-down
            "showlegend": True,  # Show legend
            "legend": {
                "orientation": "h",  # Horizontal orientation
                "yanchor": "bottom",
                "y": 1.02,  # Position it above the chart
                "xanchor": "right",
                "x": 1
            },
        }
    )

    # Return the figure
    return fig

@callback(
    Output("drawer-simple", "opened"),
    Input("drawer-demo-button", "n_clicks"),
    prevent_initial_call=True,
)
def drawer_demo(n_clicks):
    return 

# @app.callback(
#     Output('modal', 'is_open'),
#     [Input('eis-lines-grid', 'cellClicked')],
#     [State('modal', 'is_open')],
# )
# def toggle_modal(cell, is_open):
#     if cell and cell['colDef']['field'] == 'Details':
#         return not is_open
#     return is_open

@app.callback(
    Output('debug', 'children'),
    [Input('eis-lines-grid', 'cellClicked')],
)
def debug_cell_click(cell):
    if cell:
        return str(cell)
    return "No cell clicked yet"

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True,dev_tools_hot_reload_watch_interval=5)
