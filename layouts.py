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
from assets.model import BoroughRecommender

brec = BoroughRecommender(data_dir="data\\", num_of_recs=5)

ABOUT = """
The application below is part of Coursera's IBM Data Science Captstone project. The goal was to create a recommender that would help user to decide which London borough to look for accommodation in based on their preferences.

The algorithm takes three user inputs:

\t1. Accommodation preferences
\t2. Rent range
\t3. Venue preferences
\t4. Number of boroughs to recommend

More information on methodology can be found in the Methodology section and in GitHub repository.
"""

acm_types = brec.ACM_TYPES
categories = brec.venue_groups
venue_opts = [{"label": c, "value": c} for c in categories]
acm_options = [{"label": acm, "value": acm} for acm in acm_types]

del brec

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
        dbc.NavItem(dbc.NavLink("Recommender", href="/recommender")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem(
                    "Methodology",
                    id="nav-methodology",
                    href="/methodology",
                    header=True,
                ),
                dbc.DropdownMenuItem(
                    "GitHub Repository",
                    id="nav-github",
                    href="https://github.com/Parnasus/data-science-capstone",
                    header=True,
                    target="_blank",
                ),
            ],
            nav=True,
            in_navbar=True,
            label="Info",
        ),
    ],
    brand="London Borough Recommender",
    brand_href="#",
    color="dark",
    dark=True,
)


base_layout = html.Div(
    id="mainContainer",
    children=[
        html.Div(
            id="header",
            className="container-fluid",
            children=[
                html.Div(
                    className="container",
                    children=[
                        html.Div(
                            className="container my-3 p-3 border",
                            children=[
                                html.H4("Introduction"),
                                html.P(ABOUT, style={"whiteSpace": "pre-wrap"})
                            ],
                        ),
                        html.Div(
                            className="container p-3 my-3 border",
                            children=[
                                html.H4(
                                    "Recommendation Parameters"  
                                ),

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

                                html.H5("2. Rent Range (£/month)"),
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
                                    style={
                                        "padding-top": "20px",
                                        "padding-bottom": "50px",
                                        "margin-left": "15px",
                                        "margin-right": "15px",
                                    },
                                ),
                                html.H5("3. Venue Preferences"),

                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id="categories",
                                            className="col-6",
                                            children=[
                                                dcc.Dropdown(
                                                    id="dpn-venue-types",
                                                    multi=True,
                                                    style={"width": "100%"},
                                                    options=venue_opts,
                                                )
                                            ],
                                        ),
                                        html.I(
                                            "Select venue preferences in order of importance."
                                        ),
                                    ],
                                ),
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
                                            style={
                                                "width": "15%",
                                                "margin-left": "15px",
                                            },
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
                                    style={"margin-left": "20px"},
                                ),
                            ],
                        ),
                        html.Div(
                            className="container my-3 p-3 border",
                            children=[
                                html.H3("Selection Summary"),
                                html.P(
                                    #'Looking for [Accommodation Types] within [rent_min] to [rent_max] per month, preferring: [Venue Types].',
                                    id="params-summary",
                                    style={"whiteSpace": "pre-wrap"},
                                ),
                                html.Div(
                                    className="row",
                                    children=[
                                        dbc.Button(
                                            "Recommend",
                                            id="btn-recommend",
                                            color="dark",
                                            className="mr-1",
                                            style={"margin": "10px"},
                                            disabled=True,
                                        )
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="container p-3 border",
                            hidden=True,
                            id="section-results",
                            children=[
                                html.H3("Results"),
                                html.P(
                                    "For more information about the rent and venues in a specific borough, please click on the borough in the data table."
                                ),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id="results",
                                            className="col-4",
                                            children=[dt.DataTable(id="dt-results",),],
                                        ),
                                        html.Div(
                                            id="results-map",
                                            className="col-8",
                                            children=[],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="content-segment",
                                    children=[
                                        html.Div(
                                            id="results-rent",
                                            children=[],
                                            style={"margin-top": "25px",},
                                        ),
                                        html.Div(
                                            id="results-venues",
                                            children=[],
                                            style={
                                                "margin-top": "25px",
                                                "margin-bottom": "20px",
                                            },
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="container p-3",
                            id="footer",
                            children=[
                                html.Div(
                                    className="row", children=["Data as of May 2020."]
                                )
                            ],
                            hidden=True,
                        ),
                    ],
                ),
            ],
        )
    ],
)

methodology_layout = html.Div(
    className="container-fluid",
    children=[
        html.Div(
            className="container p-3 border",
            children=[
                dcc.Markdown(
                    '''

### Data Sources

The following data sources are going to be used to recommend Greater London boroughs to the user:  

1. Rent data - available from London Datastore in *.xls format: [Average Private Rents, Borough](https://data.london.gov.uk/dataset/average-private-rents-borough)
2. List of London Boroughs and their geographical coordinates, available from Wikipedia (html table): [List of London Boroughs](https://en.wikipedia.org/wiki/List_of_London_boroughs)
3. Greater London borough boundaries in GeoJSON format, available [here](https://joshuaboyd1.carto.com/tables/london_boroughs_proper/public)
4. Information on venues in Greater London area. Available via free version of [Foursquare API](https://developer.foursquare.com/).

### Recommendation algorithm

The purpose of the algorithm is to recommend a list of boroughs to a user based on their specified preferences. 

Let __W__ be a venue matrix of dimensions *n* x *m*, where every element represents a normalized density of venue group *j* in a borough *i*:

![](assets/equation_1.jpg "Equation 1")

The user-provided preferences can be formally written as a column vector __p__:

![](assets/equation_2.jpg "Equation 2")

Recommendation matrix __R__ then can be calculated as a matrix product:

![](assets/equation_3.jpg "Equation 3")

This matrix is a column vector of length *n* where each row represents the weight of each borough. The larger the weight, the closer the borough matches users preference. 

Given a number *N* of boroughs we want to recommend, *N* largest weights are selected and the list of boroughs are returned in an order from the highest weigh *r* to the lowest.


Implementation in Python:

```python
def create_preferences(ranking=None):
    "Converts `ranking` list to normalized pandas DataFrame"
    pref_dict = {
        'Eating out': 0,
        'Entertainment': 0,
        'Green spaces': 0,
        'Groceries': 0,
        'Health and Sports': 0,
        'Nightlife': 0,
        'Other': 0,
        'Public Transport': 0,
        'Shopping': 0,
    }
    
    N = len(ranking)
    
    for i, cat in enumerate(ranking): 
        pref_dict[cat] = N - i
    
    df = pd.DataFrame.from_dict(pref_dict, orient='index', columns=['Preference'])
    df['Preference'] = df['Preference'] / df['Preference'].sum()
    
    return df
```


```python
def recommend_boroughs(W=None, p=None, n_brghs=5):
    """
    Calculates matrix product of DataFrames W and p
    
    Inputs:
        W - pandas DataFrame containing venue group density for each borough
        p - pandas DataFrame with user group preferences
        n_brghs - int, number of boroughs to recommend
    
    Returns:
        rec_boroughs - `n_brghs` number of boroughs sorted by highest match value
        df_rec - resulting recommendation matrix as pandas DataFrame
    
    """
    W_ = W.copy()
    W_.set_index(['Borough'], inplace=True)
    df_rec = (p['Preference'] * W_).sum(axis=1).to_frame()
    df_rec.columns = ['Match']
    df_rec.sort_values(by='Match', ascending=False, inplace=True)
    rec_boroughs = df_rec.head(n_brghs).index.tolist()
    return rec_boroughs, df_rec
```

#### Filtering venue matrix based

The venue density matrix __W__ is filtered in advance based on user's selection on upper and lower limits for rent: *m_min* and *m_max* and the accommodation type. The dataset for borough rent data contains first *q1* and third quartile *q3* information. Only the boroughs satisfying either of the below condition are kept in the __W__ matrix:
    
![](assets/equation_4.jpg "Equation 4")

Implementation in Python:
```python
def filter_rent_data(df=None, categories=None, rent_range=None):
    """
    Returns boroughs that satisfy the conditions for `categories` and `rent_range`
        
    Inputs:
        df - pandas DataFrame containing rent data
        categories - an iterable or a string specifying appropriate accommodation types
        rent_range - a list or a tuple with r_min and r_max rent ranges.
        
    Output:
        boroughs - a list of boroughs that match the condition
    
    """
    if isinstance(categories, str):
        cats = [categories]
    else:
        cats = categories
    
    cat_cond = df['Category'].isin(cats)
    rent_lower = rent_range[0]
    rent_higher = rent_range[1]
    
    # If invalid data provided
    if rent_lower > rent_higher:
        rent_higher = rent_lower
    
    rent_cond_1 = (df['Lower quartile'] <= rent_higher) & (df['Upper quartile'] >= rent_higher)
    rent_cond_2 = (df['Lower quartile'] <= rent_lower) & (df['Upper quartile'] >= rent_lower)
    rent_cond = rent_cond_1 | rent_cond_2
    rent_cond = (df['Lower quartile'] <= rent_higher) & (df['Upper quartile'] >= rent_lower)
    
    not_null = ~df['Median'].isnull()

    df_filtered = df.loc[(cat_cond & rent_cond & not_null)]
    
    boroughs = df_filtered['Borough'].unique().tolist()
   
    return boroughs
```

Both of the above functions are then combined into one large function: 

```python
def recommend_and_plot(df_groups, df_rent, rent_range=None, acm_type=None, ranking=None, n=5):
    """
    Recommends top n venues and plots the results on the map
    
    """
    available_boroughs = filter_rent_data(df=df_rent, categories=acm_type, rent_range=rent_range)
    p = create_preferences(ranking=ranking)
    df_grp_filtered = df_groups.loc[df_groups['Borough'].isin(available_boroughs)]
    rec_boroughs, df_rec = recommend_boroughs(W=df_grp_filtered, p=p, n_brghs=n)

    # Printing and plotting of results
    # ...  

```

'''
                )
            ],
        ),
    ],
)

recommender = html.Div([navbar, base_layout,])

methodology = html.Div([navbar, methodology_layout,])

