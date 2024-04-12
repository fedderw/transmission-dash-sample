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
from dash import Dash, html, dcc, callback, Input, Output, State, no_update
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
import pandas as pd


# Load data for AG Grid and Leaflet Map
# Number of rows to read (including the header)
rows_to_read = 38

df_eis_lines = pd.read_csv(
    "data/eis_lines.csv", nrows=rows_to_read, index_col=0
)
# Drop NA values in 'Name' column
df_eis_lines = df_eis_lines.dropna(subset=["Name"])
df_eis_lines.index = df_eis_lines.index.astype(int)
df_eis_lines_urls = pd.read_csv("data/eis_lines_urls.csv", index_col=0)
# Drop NA values in 'Name' column
df_eis_lines_urls = df_eis_lines_urls.dropna(subset=["Name"])
df_eis_lines_urls.index = df_eis_lines_urls.index.astype(int)
df_eis_lines = df_eis_lines.merge(
    df_eis_lines_urls, left_index=True, right_index=True, suffixes=("", "_url")
)
df_eis_lines["Project"] = df_eis_lines.apply(
    lambda row: f'<a href="{row["Name_url"]}" target="_blank">{row["Name"]}</a>', axis=1
)
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
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    external_scripts=[{"assets/dashAgGridComponentFunctions.js"}],
)
# app.scripts.append_script({"external_scripts": "assets/dashAgGridComponentFunctions.js"})
server = app.server

# Step 1: Extract unique NEPA Trigger values
nepa_triggers = df_eis_lines['NEPA Trigger'].unique()
regions = df_eis_lines['Region'].unique()
project_drivers = df_eis_lines['Project Drivers (As determined by CThree)'].unique()
nepa_status = df_eis_lines['Status of NEPA review'].unique()
nepa_status = df_eis_lines['Status of NEPA review'].unique()
def create_chip_group_container(title, id, items):
    return dmc.Container(
        [
            html.H6(title),  # Add title above the chipgroup
            dmc.ChipGroup(
                [
                    dmc.Chip(
                        item,
                        value=item,
                        variant="outline",
                    )
                    for item in items
                ],
                id=id,
                value=[],
                multiple=True,
                mb=10,
            ),
        ],
        
        # className="col-md-6",
    )

# Step 2: Create a dbc.Collapse with dmc.Container for each unique category
chip_collapse = dbc.Collapse(
    [
        create_chip_group_container("NEPA Trigger", "nepa-trigger-chips", nepa_triggers),
        create_chip_group_container("Region", "region-chips", regions),
        create_chip_group_container("Project Drivers", "project-driver-chips", project_drivers),
        create_chip_group_container("NEPA Status", "nepa-status-chips", nepa_status),
    ],
    id="chip-collapse",
    is_open=False,
)

chip_filter=html.Div(
    [
        dbc.Button("Quick Filter Options", id="chip-collapse-button", className="mb-3", color="primary", n_clicks=0),
        chip_collapse,
    ]
)

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


columnDefs = (
    [
        {
            "field": "Project",
            "filter": True,  # Enable filtering on this column
            "sortable": True,  # Enable sorting on this column
            "checkboxSelection": True,  # Add checkbox to 'Project' column only
            "cellRenderer": "markdown",  # Add markdown renderer to 'Project' column only
            # Set width of 'Project' column 
            "width": 400,
        }
    ]
    + [
        {
            "field": "Details",
            "cellRenderer": "agGroupCellRenderer",
            "cellRendererParams": {
                "innerRenderer": "DBC_Button",
            },
            "cellClass": "details-button",
            "width": 100,
        },
    ]
    + [
        {
            "field": col,
            "filter": True,  # Enable filtering on this column
            "sortable": True,  # Enable sorting on this column
            "checkboxSelection": False,  # No checkbox for other columns
            "cellRenderer": None,  # No markdown renderer for other columns
            "hide": True if col == "Name" else False,  # Hide 'Name' column
        }
        for col in df_eis_lines.columns
        if col != "Project"
        and not col.endswith("_url")  # Exclude 'Project' and '_url' columns
    ]
)
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
                        dmc.LoadingOverlay(
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
                            ),
                            loaderProps={
                                "variant": "dots",
                                "color": "orange",
                                "size": "xl",
                            },
                        )
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        dmc.LoadingOverlay(
                            dcc.Graph(id="gantt-chart"),
                            loaderProps={
                                "variant": "dots",
                                "color": "orange",
                                "size": "xl",
                            },
                        )  # Placeholder for Gantt chart
                    ],
                    width=8,
                ),
            ]
        ),
        html.Div(style={"height": "30px"}),  # Add space between rows
        dbc.Row(chip_filter),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dmc.LoadingOverlay(
                            dag.AgGrid(
                                id="eis-lines-grid",
                                rowData=df_eis_lines.to_dict("records"),
                                columnDefs=columnDefs,
                                style={"width": "100%", "height": "300px"},
                                dashGridOptions={
                                    "rowSelection": "multiple",
                                    "suppressRowClickSelection": True,
                                },  # Enable multiple row selection for filtering
                                dangerously_allow_code=True,
                                filterModel={},
                                className="ag-theme-quartz",
                            ),
                            loaderProps={
                                "variant": "dots",
                                "color": "orange",
                                "size": "xl",
                            },
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
                dbc.ModalHeader("Details",id="modal-header"),
                dbc.ModalBody(
                    dmc.LoadingOverlay(
                        dmc.Timeline(
                            active=1,
                            bulletSize=15,
                            lineWidth=2,
                            children=[],
                        ),
                        loaderProps={
                            "variant": "dots",
                            "color": "orange",
                            "size": "xl",
                        },
                    ),
                    id="modal-body",
                ),
            ],
            id="modal",
        ),
        html.Div(id="debug"),
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
    gdff = (
        eis_lines_gdf
        if virtualRowData is None
        else eis_lines_gdf.merge(
            pd.DataFrame(virtualRowData), on="Name", how="inner"
        )
    )
    selected_names = (
        [s["Name"] for s in selected_rows] if selected_rows else []
    )

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
        dl.GeoJSON(
            data=filtered_geojson,
            id="map-geojson",
            children=[
                dl.Tooltip(
                    children=create_tooltip_content(feature), sticky=True
                )
                for feature in filtered_geojson["features"]
            ],
        ),
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
    selected_names = (
        [s["Name"] for s in selected_rows] if selected_rows else []
    )

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
        "Complete": "#66c2a5",  # Light green
        "Canceled": "#fc8d62",  # Light orange
        "Underway": "#8da0cb",  # Light blue
        "Unknown": "#e78ac3",  # Light pink
    }

    # Handle 'NaT' values and trailing spaces in 'Status of NEPA review' column
    filtered_df["Status of NEPA review"] = (
        filtered_df["Status of NEPA review"].fillna("Unknown").str.strip()
    )

    # Set 'Date last ROD published' to today's date for 'Underway' processes
    filtered_df.loc[
        filtered_df["Status of NEPA review"] == "Underway",
        "Date last ROD published",
    ] = datetime.now()
    # Replace 'in progress' with NaN
    filtered_df["Year Federal EIS Issued"] = filtered_df[
        "Year Federal EIS Issued"
    ].replace("in progress", np.nan)

    # Convert 'Energized?' column to string and extract year
    filtered_df["Year Energized"] = (
        filtered_df["Energized?"]
        .astype(str)
        .apply(lambda x: re.findall(r"\b\d{4}\b", x))
    )
    filtered_df["Year Energized"] = filtered_df["Year Energized"].apply(
        lambda x: x[0] if x else np.nan
    )

    # Create separate dataframes for each phase
    df_proposed = filtered_df[["Name", "Year project proposed"]].copy()
    df_proposed["Phase"] = "Proposed"
    df_proposed["Start"] = pd.to_datetime(
        df_proposed["Year project proposed"], format="%Y"
    )
    df_proposed["Finish"] = pd.to_datetime(
        filtered_df["Date of NOI Publication"]
    )

    df_noi = filtered_df[["Name", "Date of NOI Publication"]].copy()
    df_noi["Phase"] = "NOI Published"
    df_noi["Start"] = pd.to_datetime(df_noi["Date of NOI Publication"])
    df_noi["Finish"] = pd.to_datetime(
        filtered_df["Year Federal EIS Issued"], format="%Y"
    )

    df_eis = filtered_df[["Name", "Year Federal EIS Issued"]].copy()
    df_eis["Phase"] = "EIS Issued"
    df_eis["Start"] = pd.to_datetime(
        df_eis["Year Federal EIS Issued"], format="%Y"
    )
    df_eis["Finish"] = pd.to_datetime(filtered_df["Date last ROD published"])

    df_energized = filtered_df[["Name", "Year Energized"]].copy()
    df_energized["Phase"] = "Energized"
    df_energized["Start"] = pd.to_datetime(
        df_energized["Year Energized"], format="%Y"
    )
    df_energized["Finish"] = pd.to_datetime(
        df_energized["Year Energized"], format="%Y"
    )

    # Handle 'in progress' status
    df_in_progress = filtered_df[filtered_df["Energized?"] == "In progress"][
        ["Name"]
    ].copy()
    df_in_progress["Phase"] = "In progress"
    df_in_progress["Start"] = pd.to_datetime(
        filtered_df["Year Federal EIS Issued"], format="%Y"
    )
    df_in_progress["Finish"] = pd.to_datetime(datetime.now().year, format="%Y")

    # Concatenate the dataframes
    df_timeline = pd.concat(
        [df_proposed, df_noi, df_eis, df_energized, df_in_progress]
    )

    # Create a timeline
    fig = px.timeline(
        df_timeline, x_start="Start", x_end="Finish", y="Name", color="Phase"
    )

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
                "x": 1,
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
    return True

@app.callback(
    [Output("modal", "is_open"), Output("modal-body", "children"),Output("modal-header", "children")],
    [Input("eis-lines-grid", "cellClicked")],
    [State("modal", "is_open")],
    suppress_callback_exceptions=True,
)
def toggle_modal(cell, is_open):
    if cell and cell["colId"] == "Details":
        row = df_eis_lines.loc[(int(cell["rowId"])+1)]
        name = row["Name"]
        def determine_active_step_index(row):
            # Check each condition and return the corresponding index

            # If 'Date of NOI Publication' is not available, project is before the NOI stage
            if pd.isna(row['Date of NOI Publication']):
                return 0  # Assuming this is the index for "Proposed" or before "NOI Published"

            # If 'Year Federal EIS Issued' is 'In Progress' or not available, it's in the EIS Issuing stage
            if row['Year Federal EIS Issued'] == 'In Progress' or pd.isna(row['Year Federal EIS Issued']):
                return 1  # Index for "Federal EIS Issued"

            # If 'Date last ROD published' is not available, it's in the ROD Publishing stage
            if pd.isna(row['Date last ROD published']):
                return 2  # Index for "Record of Decision Published"

            # Check if the NEPA review is complete, but project is not yet energized
            if row['Status of NEPA review'] == 'Complete' and row['Energized?'] not in ['Project complete', 'Canceled']:
                return 3  # Index for "Status of NEPA review"

            # Finally, if the project is energized or canceled
            if row['Energized?'] in ['Project complete', 'Canceled']:
                return 4  # Index for "Energized?"

            # Default case if none of the above conditions are met
            return 5  # Assuming this is the index for a default or unknown status


        active_step_index = determine_active_step_index(row)

        steps = [
            {"title": "NOI Published", "text": row['Date of NOI Publication']},
            {"title": "Federal EIS Issued", "text": row['Year Federal EIS Issued']},
            {"title": "Record of Decision Published", "text": row['Date last ROD published']},
            {"title": "NEPA review", "text": row['Status of NEPA review']},
            {"title": "Final project status", "text": row['Energized?']},
        ]

        # Generate the timeline items without setting 'active' here
        timeline_items = [
            dmc.TimelineItem(
                title=step["title"],
                children=[dmc.Text(step["text"], size="sm")]
            )
            for step in steps
        ]

        # Calculate the average line length
        avg_line_length = df_eis_lines.loc[df_eis_lines["Name"] != name, "Line Length (mi)"].mean()

        # Create the bar chart for line length comparison
        bar_chart_line_length = dcc.Graph(
            figure={
                "data": [
                    {
                        "x": ["Selected Project", "Average"],
                        "y": [row["Line Length (mi)"], avg_line_length],
                        "type": "bar",
                    }
                ],
                "layout": {
                    "title": "Line Length Comparison",
                    # "xaxis": {"title": "Category"},
                    "yaxis": {"title": "Line Length (mi)"},
                },
            }
        )

        # Calculate the average dominant line voltage
        avg_dominant_voltage = df_eis_lines.loc[df_eis_lines["Name"] != name, "Dominant Line Voltage (kV)"].mean()

        # Create the bar chart for dominant line voltage comparison
        bar_chart_dominant_voltage = dcc.Graph(
            figure={
                "data": [
                    {
                        "x": ["Selected Project", "Average"],
                        "y": [row["Dominant Line Voltage (kV)"], avg_dominant_voltage],
                        "type": "bar",
                    }
                ],
                "layout": {
                    "title": "Dominant Line Voltage Comparison",
                    # "xaxis": {"title": "Category"},
                    "yaxis": {"title": "Dominant Line Voltage (kV)"},
                },
            }
        )
        
        # Filter out the selected project
        df_excluding_selected = df_eis_lines[df_eis_lines['Name'] != name]

        # Calculate the average time in days excluding the selected project
        avg_time = df_excluding_selected["Time in Days (NOI to last ROD)"].mean()

        # Create the bar chart
        bar_chart_time = go.Figure(data=[
            go.Bar(x=[name], y=[row["Time in Days (NOI to last ROD)"]], name="Selected Project"),
            go.Bar(x=["Average"], y=[avg_time], name="Average")
        ])

        bar_chart_time.update_layout(
            title="Time in Days (NOI to last ROD) Comparison",
            xaxis_title="Project",
            yaxis_title="Time in Days (NOI to last ROD)",
            showlegend=False,
        )

        bar_chart_time_component = dcc.Graph(figure=bar_chart_time)

        return not is_open, [dmc.Timeline(
            active=active_step_index,  # Set the active step in the Timeline component
            bulletSize=15, 
            lineWidth=2, 
            children=timeline_items
        ), bar_chart_line_length, bar_chart_dominant_voltage, bar_chart_time_component], name

    return is_open, no_update, no_update
   
@app.callback(
    Output("debug", "children"),
    [Input("eis-lines-grid", "cellClicked")],
)
def debug_cell_click(cell):
    if cell:
        return str(cell)
    return "No cell clicked yet"

@app.callback(
    Output("eis-lines-grid", "filterModel"),
    [
        Input("nepa-trigger-chips", "value"),
        Input("region-chips", "value"),
        Input("project-driver-chips", "value"),
        Input("nepa-status-chips", "value"),
    ],
    State("eis-lines-grid", "filterModel"),
    prevent_initial_call=True,
)
def update_grid_based_on_selections(nepa_triggers, regions, project_drivers, nepa_status, model):
    model["NEPA Trigger"] = {
        "filterType": "text",
        "operator": "OR",
        "conditions": [
            {"filterType": "text", "type": "equals", "filter": trigger}
            for trigger in nepa_triggers
        ],
    }
    model["Region"] = {
        "filterType": "text",
        "operator": "OR",
        "conditions": [
            {"filterType": "text", "type": "equals", "filter": region}
            for region in regions
        ],
    }
    model["Project Drivers (As determined by CThree)"] = {
        "filterType": "text",
        "operator": "OR",
        "conditions": [
            {"filterType": "text", "type": "equals", "filter": driver}
            for driver in project_drivers
        ],
    }
    model["Status of NEPA review"] = {
        "filterType": "text",
        "operator": "OR",
        "conditions": [
            {"filterType": "text", "type": "equals", "filter": status}
            for status in nepa_status
        ],
    }
    return model


@app.callback(
    Output("chip-collapse", "is_open"),
    [Input("chip-collapse-button", "n_clicks")],
    [State("chip-collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True, dev_tools_hot_reload_watch_interval=60)
