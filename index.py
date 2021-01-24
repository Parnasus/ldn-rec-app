  
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import server, app

from layouts import recommender, methodology
import callbacks


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content',
            children=[recommender],
    )
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/recommender':
        return recommender
    elif pathname == '/methodology':
        return methodology
    else:
        return recommender


if __name__ == '__main__':
    app.run_server(debug=True)