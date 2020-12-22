import pandas as pd
import json
import flask

import dash
import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

ACCOMMODATION_TYPES = [
    "Room",
    "Studio",
    "One Bedroom",
    "Two Bedroom",
    "Three Bedroom",
    "Four Bedroom",
]

acm_options = [{"label": acm, "value": acm} for acm in ACCOMMODATION_TYPES]

RENT_MIN = 0
RENT_MAX = 3200
STEP = 200

MAX_RECS = 6

rent_marks = {r: {"label": f"{r}"} for r in range(RENT_MIN, RENT_MAX + STEP, STEP)}

# First and last rent marks get "£"
rent_first = list(rent_marks.keys())[0]
rent_last = list(rent_marks.keys())[-1]

rent_marks[rent_first] = {"label": f"{rent_first}£"}
rent_marks[rent_last] = {"label": f"{rent_last}£"}

# Number of recommendations
n_rec_options = [{"label": rec, "value": rec} for rec in range(1, MAX_RECS + 1)]


navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Page 1", href="#")),
        dbc.DropdownMenu(
            children=[
                # dbc.DropdownMenuItem("More pages", header=True),
                # dbc.DropdownMenuItem("Page 2", href="#"),
                # dbc.DropdownMenuItem("Page 3", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="London Borough Recommender",
    brand_href="#",
    color="primary",
    dark=True,
)

base_layout = html.Div(
    id="mainContainer",
    children=[
        html.Div(  # <------------------------------------------------------- App title container
            id="header",
            className="container-fluid",
            children=[
                navbar,
                html.Div(
                    className="container",
                    children=[
                        html.Div(
                            className="col-12",
                            children=[
                                # html.H3(
                                #     "Recommendation Parameters"  # < ------------- App title
                                # )
                            ],
                        ),
                        html.Div(
                            className="container p-3 my-3 border",
                            children=[
                                html.H4(
                                    "Recommendation Parameters"  # < ------------- App title
                                ),
                                # dbc.Label('Accommodation Types:'),
                                html.Br(),
                                html.H5("1. Accommodation Types"),
                                dcc.Checklist(
                                    id="chk-acm-types",
                                    options=acm_options,
                                    value=[],
                                    labelStyle={
                                        "display": "inline-block",
                                        "margin-left": "5px",
                                    },
                                    inputStyle={
                                        "margin-left": "5px",
                                        "margin-right": "5px",
                                    },
                                ),
                                # dbc.Label('Rent Range:'),
                                html.H5("2. Rent Range"),
                                html.Div(
                                    children=[
                                        dcc.RangeSlider(
                                            id="slider-rent",
                                            min=RENT_MIN,
                                            max=RENT_MAX,
                                            step=100,
                                            value=[400, 1200],
                                            marks=rent_marks,
                                            allowCross=False,
                                        )
                                    ],
                                    style={"padding-top": "20px",
                                           "padding-bottom": "50px",
                                           'margin-left': '15px',
                                           "margin-right": '15px',
                                           },
                                ),
                                html.H5("3. Venue Preferences"),
                                # html.Div(
                                #     className="row",
                                #     children=[
                                    html.Div(className='row',
                                children=[
                                html.Div(
                                    id="categories",
                                    className="col-6",
                                    children=[
                                        # dbc.Label('Venue Preferences'),
                                        dcc.Dropdown(
                                            id="dpn-venue-types",
                                            multi=True,
                                            style={"width": "100%"},
                                        )
                                    ],
                                ),
                                html.I('Select venue preferences in order of importance.'),
                                ]),
                                html.Br(),
                                html.H5("4. Recommendation Settings"),
                                html.Div(
                                    className="row",
                                    children=[
                                        dbc.Label("Number of Boroughs:"),
                                        dcc.Dropdown(
                                            id="dpn-number-of-recs",
                                            options=n_rec_options,
                                            value=5,
                                            style={"width": "15%", "margin-left": "15px"},
                                            clearable=False,
                                        ),
                                        html.Div(
                                            children=[
                                                dcc.Checklist(
                                                    id="chk-display-venues",
                                                    options=[
                                                        {
                                                            "label": "Display Venues on the Map",
                                                            "value": "Y",
                                                        }
                                                    ],
                                                    value=[],
                                                    inputStyle={
                                                        "margin-left": "5px",
                                                        "margin-right": "5px",
                                                    },
                                                    labelStyle={"margin-left": "5px"},
                                                )
                                            ],
                                            style={"vertical-align": "center"},
                                        ),
                                    ],
                                    style={'margin-left': '20px'},
                                ),
                            ],
                        ),
                        html.Div(
                            className='container my-3 p-3',
                            children=[
                                html.P( 
                                    'Looking for [Accommodation Types] within [rent_min] to [rent_max] per month, preferring: [Venue Types].',
                                    id='params-summary',
                                    ),
                                html.Div(
                                    className="row",
                                    children=[
                                        dbc.Button(
                                            "Recommend",
                                            id="btn-recommend",
                                            color="primary",
                                            className="mr-1",
                                            style={"margin-top": "20px"},
                                        )
                                    ],
                                ),
                            ]
                        ),
                        html.Div(
                            className="container p-3",
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id="results-map",
                                            className="col-8",
                                            children=[],
                                        )
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
    ],
)
