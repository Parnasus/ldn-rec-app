from dash.dependencies import Input, Output, State
from app import app
import folium

from dash.exceptions import PreventUpdate

import numpy as np
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import dash
from dash_table.Format import Format, Scheme, Sign, Symbol
from assets.model import BoroughRecommender

brec = BoroughRecommender(
    data_dir="data\\", num_of_recs=5, auto_update=True, plot_venues=False
)

@app.callback(
    [
        Output("results", "children"),
        Output("results-map", "children"),
        Output("section-results", "hidden"),
        Output("results-rent", "children"),
        Output("results-venues", "children"),
        Output("footer", "hidden"),
    ],
    [
        Input("btn-recommend", "n_clicks"),
        Input('dt-results', 'active_cell'),
    ],
    [
        State("chk-acm-types", "value"),
        State("slider-rent", "value"),
        State("dpn-venue-types", "value"),
        State("dpn-number-of-recs", "value"),
        State("chk-display-venues", "value"),
        State('dt-results', 'data'),
    ],
    prevent_initial_call=True,
)
def run_recommender(rec_click, active_cell, acm_types, rent_range, venue_rank, n_recs, plot_venues, dt_data):
    
    ctx = dash.callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'btn-recommend':
        if not rec_click:
            raise PreventUpdate
        if not plot_venues:
            plot_venues = False
        else:
            plot_venues = True

        brec.plot_venues = plot_venues
        brec.num_of_recs = n_recs 
        brec.set_rent_range(rent_range)
        brec.set_accommodation_types(acm_types)
        brec.set_preferences(venue_rank)
        brec.recommend()
        brec.save_map("map.html")

        out_map = html.Iframe(
            srcDoc=open("map.html", "r", encoding="utf8").read(),
            width="100%",
            height=600,
        )

        df_rec = brec.df_recommendation.copy()
        n_recs = brec.num_of_recs

        df_rec.loc[:, "Match"] = df_rec["Match"] * 100

        df_rec_n = df_rec.iloc[:n_recs].copy()

        df_rec_n.loc[:, "Match"] = 100 * df_rec_n["Match"] / df_rec_n["Match"].sum()
        df_rec_n.reset_index(inplace=True)
        df_rec_n.columns = ["borough", "match"]
        rec_data = df_rec_n.to_dict(orient="records")

        # Create Data table
        rec_table_cols = [
            {
                "name": "Borough",
                "id": "borough",
                "type": "text",
            },
            {
                "name": "Match Score",
                "id": "match",
                "type": "numeric",
                "format": Format(precision=3),
            },
        ]

        rec_style_cell_conditional = [
            {"if": {"column_id": "borough"}, "textAlign": "left"}
        ]

        rec_table = dt.DataTable(
            id="dt-results",
            data=rec_data,
            columns=rec_table_cols,
            style_cell_conditional=rec_style_cell_conditional,
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'textAlign': 'left',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
        )

        available_boroughs = brec.recommended_boroughs
        
        borough_opts = []
        for b in available_boroughs:
            borough_opts.append(
                {'label': b, 'value': b}
            )
        
        return [rec_table, out_map, False, None, None, False]
    else:
        row_idx = active_cell['row']
        column_id = active_cell['column_id']
        if column_id == 'borough':
            selected_borough = dt_data[row_idx]['borough']
            brec.highlight_borough_on_map(name=selected_borough)
            brec.save_map("map.html")

            out_map = html.Iframe(
                srcDoc=open("map.html", "r", encoding="utf8").read(),
                width="100%",
                height=600,
            )

            df_rent =  brec.df_rent
            accom = brec.accommodation_types

            select_cond = (df_rent['Borough']==selected_borough) & (df_rent['Category'].isin(accom))
            df_rent = df_rent.loc[select_cond]
            rent_cols = df_rent.columns
            keep_cols = rent_cols[1:]
            df_rent = df_rent[keep_cols]

            rent_data = df_rent.to_dict(orient='records')
            rent_columns = [{"name": i, "id": i} for i in df_rent.columns]
            
            for i in range(1,4):
                rent_columns[i]['type'] = "numeric"
                rent_columns[i]['format'] = Format(group=',')
                rent_columns[i]['name'] += ' (£)'

            dt_rent = dt.DataTable(
                id="dt-rents",
                data=rent_data,
                columns=rent_columns,
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'Category'},
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px', 'textAlign': 'left'},
                    {'if': {'column_id': 'Lower quartile'},
                    'minWidth': '90px', 'width': '90px', 'maxWidth': '90px', 'textAlign': 'right'},
                    {'if': {'column_id': 'Median'},
                    'minWidth': '90px', 'width': '90px', 'maxWidth': '90px', 'textAlign': 'right'},
                    {'if': {'column_id': 'Upper quartile'},
                    'minWidth': '90px', 'width': '90px', 'maxWidth': '90px', 'textAlign': 'right'},
                ]
            )

            venue_groups = brec.selected_groups

            df_venues = brec.df_venues
            select_cond = (df_venues['Borough']==selected_borough) & (df_venues['Group'].isin(venue_groups))
            df_venues = df_venues.loc[select_cond]

            # venue sorting
            sort_ord = {}
            for i, v in enumerate(venue_groups):
                sort_ord[v] = i

            df_venues.loc[:, 'sort'] = df_venues['Group'].map(sort_ord)
            df_venues.sort_values(by='sort', inplace=True)
            del df_venues['sort']
            
            url_gm = "https://www.google.com/maps/search/?api=1&query=" #<lat>,<lng>
            url_gm = "https://www.google.com/maps/search/?api=1&query={0},{1}"
            df_venues.loc[:, 'gmaps_url'] = df_venues.apply(lambda x: url_gm.format(x['Venue Latitude'], x['Venue Longitude']), axis=1)
            col_format = "[Link to Maps]({0})"
            df_venues.loc[:, 'URL'] = df_venues['gmaps_url'].apply(lambda x: col_format.format(x))
            
    
            col_order =  ['Venue', 'Group', 'Venue Category', 'URL']
            df_venues = df_venues[col_order]

            venue_data = df_venues.to_dict(orient='records')
            venue_columns = [{"name": i, "id": i} for i in df_venues.columns]
            venue_columns[-1] = {"name": "URL", "id": "URL", "type": 'text', "presentation": "markdown"}
            available_boroughs = brec.recommended_boroughs

            dt_venues = dt.DataTable(
                id="dt-venues",
                data=venue_data,
                columns=venue_columns,
                page_current=0,
                page_size=20,
                filter_action='native',
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'Venue'},
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px', 'textAlign': 'left'},
                    {'if': {'column_id': 'Group'},
                    'minWidth': '90px', 'width': '90px', 'maxWidth': '90px', 'textAlign': 'left'},
                    {'if': {'column_id': 'Venue Category'},
                    'minWidth': '90px', 'width': '90px', 'maxWidth': '90px', 'textAlign': 'left'},
                    {'if': {'column_id': 'URL'},
                    'minWidth': '90px', 'width': '90px', 'maxWidth': '90px', 'textAlign': 'center'},
                ],
                export_format='csv',
                export_headers="display",
            )
            rec_table_cols = [
                {
                    "name": "Borough",
                    "id": "borough",
                    "type": "text",
                },
                {
                    "name": "Match Score",
                    "id": "match",
                    "type": "numeric",
                    "format": Format(precision=3),
                },
            ]

            rec_style_cell_conditional = [
                {"if": {"column_id": "borough"}, "textAlign": "left"}
            ]

            rec_table = dt.DataTable(
                id="dt-results",
                data=dt_data,
                columns=rec_table_cols,
                style_cell_conditional=rec_style_cell_conditional,
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
            )



            return [rec_table, out_map, False, dt_rent, dt_venues, False]
        else:
            raise PreventUpdate

@app.callback(
    Output("btn-recommend", "disabled"),
    [
        Input('dpn-venue-types', 'value'),
        Input('chk-acm-types', 'value'),
    ],
    [
        State('dpn-venue-types', 'value'),
        State('chk-acm-types', 'value'),
    ],
    prevent_initial_call=True,
)
def update_recommend_button(in_venue, in_acm, st_venue, st_acm):

    if in_venue:
        if st_acm is not None:
            return False
        else:
            raise PreventUpdate
    else:
        if st_venue is not None:
            return False
        else:
            raise PreventUpdate


@app.callback(
    Output("params-summary", "children"),
    [
        Input("chk-acm-types", "value"),
        Input("slider-rent", "value"),
        Input("dpn-venue-types", "value"),
    ],
    prevent_initial_call=True,
)
def update_summary_paragraph(acm_types, rent_range, venue_rank):
    acm_types_str = ", ".join(acm_types)

    if venue_rank:
        venue_ranks_str = "\n\t".join([f"{i+1}. {v}" for i, v in enumerate(venue_rank)])
    else:
        venue_ranks_str = ""

    str_template = f"Accommodation types: {acm_types_str} \nRent range: {rent_range[0]}£ to {rent_range[1]}£ per month.\nPreference ranking: \n\t{venue_ranks_str}"

    return [str_template]

