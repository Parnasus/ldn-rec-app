from dash.dependencies import Input, Output, State
from app import app
import folium
# import plotly.graph_objs as go
# from plotly import tools
from dash.exceptions import PreventUpdate

import numpy as np
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html

from assets.model import BoroughRecommender

N_INPUTS = 5

brec = BoroughRecommender(data_dir='data\\', num_of_recs=N_INPUTS, auto_update=True, plot_venues=True)

@app.callback(
        Output('dpn-venue-types', 'options'),
    [
        Input('btn-recommend', 'n_clicks'),
    ]
    )
def set_categories(n_clicks):
    if n_clicks is None:
        cats = brec.venue_groups
        opts = [{'label': c, 'value': c} for c in cats]
        return opts
    else:
        raise PreventUpdate



@app.callback(
        Output('results-map', 'children'),
	[
        Input('btn-recommend', 'n_clicks'),
    ],
    [
        State('chk-acm-types', 'value'),
        State('slider-rent', 'value'),
        State('dpn-venue-types', 'value'),
    ],
    prevent_initial_call=True,
    )
def update_output(rec_click, acm_types, rent_range, venue_rank):
    if rec_click:
        # rent_range = [400, 800]
        # acm_type = ['Studio', 'One Bedroom']
        # group_rank = [
        #     'Green spaces',
        #     'Groceries', 
        #     'Public Transport',
        #     'Shopping',         
        # ]
        brec.set_rent_range(rent_range)
        brec.set_accommodation_types(acm_types)
        brec.set_preferences(venue_rank)
        brec.recommend()
        brec.save_map('map.html')
        
        out_map = html.Iframe(srcDoc=open('map.html', 'r', encoding="utf8").read(), width='100%', height=600)
        
        return [out_map]

        