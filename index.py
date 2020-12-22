  
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# see https://community.plot.ly/t/nolayoutexception-on-deployment-of-multi-page-dash-app-example-code/12463/2?u=dcomfort
from app import server, app

from layouts import base_layout
import callbacks

# see https://dash.plot.ly/external-resources to alter header, footer and favicon
# app.index_string = ''' 
# <!DOCTYPE html>
# <html>
#     <head>
#         {%metas%}
#         <title>London Borough Recommender</title>
#         {%favicon%}
#         {%css%}
#     </head>
#     <body>
#         {%app_entry%}
#         <footer>
#             {%config%}
#             {%scripts%}
#         </footer>
#         <div>London Borough Recommender</div>
#     </body>
# </html>
# '''

app.layout = html.Div([
    html.Div(id='page-content',children=[base_layout])
])

# @app.callback(Output('page-content', 'children'),
#               [Input('url', 'pathname')])
# def display_page(pathname):
#     return base_layout

if __name__ == '__main__':
    app.run_server(debug=True)