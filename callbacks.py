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
import dash_table as dt
from dash_table.Format import Format, Scheme, Sign, Symbol
from assets.model import BoroughRecommender

# N_INPUTS = 5

# brec = BoroughRecommender(
#     data_dir="data\\", num_of_recs=N_INPUTS, auto_update=True, plot_venues=True
# )
temp_brec = BoroughRecommender(
            data_dir="data\\",
            num_of_recs=5,
            auto_update=True,
            plot_venues=False,
        )

def data_bars(df, column, min_val=None, max_val=None):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if max_val:
        max_v = max_val
    else:
        max_v = df[column].max()

    if min_val:
        min_v = min_val
    else:
        min_v = df[column].min()

    ranges = [((max_v - min_v) * i) + df[column].min() for i in bounds]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]

        max_bound_percentage = bounds[i] * 100
        print(max_bound_percentage)
        styles.append(
            {
                "if": {
                    "filter_query": (
                        "{{{column}}} >= {min_bound}"
                        + (
                            " && {{{column}}} < {max_bound}"
                            if (i < len(bounds) - 1)
                            else ""
                        )
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    "column_id": column,
                },
                "background": (
                    """
                    linear-gradient(90deg,
                    #0074D9 0%,
                    #0074D9 {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(
                        max_bound_percentage=max_bound_percentage
                    )
                ),
                "paddingBottom": 2,
                "paddingTop": 2,
            }
        )

    return styles


@app.callback(
    Output("dpn-venue-types", "options"), [Input("btn-recommend", "n_clicks")]
)
def set_categories(n_clicks):
    if n_clicks is None:
        cats = temp_brec.venue_groups
        opts = [{"label": c, "value": c} for c in cats]
        return opts
    else:
        raise PreventUpdate


@app.callback(
    [Output("results", "children"), Output("results-map", "children"),
    Output("section-results", "hidden")],
    [Input("btn-recommend", "n_clicks")],
    [
        State("chk-acm-types", "value"),
        State("slider-rent", "value"),
        State("dpn-venue-types", "value"),
        State("dpn-number-of-recs", "value"),
        State("chk-display-venues", "value"),
    ],
    prevent_initial_call=True,
)
def run_recommender(rec_click, acm_types, rent_range, venue_rank, n_recs, plot_venues):
    if rec_click:
        # rent_range = [400, 800]
        # acm_type = ['Studio', 'One Bedroom']
        # group_rank = [
        #     'Green spaces',
        #     'Groceries',
        #     'Public Transport',
        #     'Shopping',
        # ]
        if not plot_venues:
            plot_venues = False
        else:
            plot_venues = True

        brec = BoroughRecommender(
            data_dir="data\\",
            num_of_recs=n_recs,
            auto_update=True,
            plot_venues=plot_venues,
        )

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

        # columns=[{"name": i, "id": i} for i in df.columns],
        rec_table_cols = [
            {"name": "Borough", "id": "borough", "type": "text"},
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
            #style_data_conditional=data_bars(df_rec_n, "match", min_val=10),
        )

        #print(brec.df_rent)

        return [rec_table, out_map, False]
    else:
        raise PreventUpdate


@app.callback(
        Output('params-summary', 'children'),
	[
        Input('chk-acm-types', 'value'),
        Input('slider-rent', 'value'),
        Input('dpn-venue-types', 'value'),
    ],
    prevent_initial_call=True,
    )
def update_summary_paragraph(acm_types, rent_range, venue_rank):
            
        acm_types_str = ', '.join(acm_types)
        
        if venue_rank:
            venue_ranks_str = "\n\t".join([f'{i+1}. {v}' for i, v in enumerate(venue_rank)])
        else:
            venue_ranks_str = ""
        
        str_template = f"Accommodation types: {acm_types_str} \nRent range: {rent_range[0]}£ to {rent_range[1]}£ per month.\nPreference ranking: \n\t{venue_ranks_str}"

        return [str_template]

