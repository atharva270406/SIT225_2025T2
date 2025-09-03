import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

df = pd.read_csv("gyro_data_20250812_153117.csv")

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Gyroscope Histogram Dashboard"),
    html.Div([
        html.Label("Select Axis for Histogram:"),
        dcc.Dropdown(
            id='axis-select',
            options=[
                {'label': 'X', 'value': 'gyro_x'},
                {'label': 'Y', 'value': 'gyro_y'},
                {'label': 'Z', 'value': 'gyro_z'}
            ],
            value='gyro_x',
            clearable=False,
            style={'width': '200px'}
        ),
    ]),
    html.Div([
        html.Label("Number of samples to display:"),
        dcc.Input(
            id='sample-count',
            type='number',
            value=200,
            min=10,
            step=10
        ),
        html.Button("Previous", id='prev-btn', n_clicks=0),
        html.Button("Next", id='next-btn', n_clicks=0)
    ], style={'margin-top': '10px'}),
    dcc.Graph(id='histogram-graph'),
    html.Div(id='data-summary', style={'margin-top': '20px'})
])

@app.callback(
    [Output('histogram-graph', 'figure'),
     Output('data-summary', 'children')],
    [Input('axis-select', 'value'),
     Input('sample-count', 'value'),
     Input('prev-btn', 'n_clicks'),
     Input('next-btn', 'n_clicks')]
)
def update_histogram(selected_axis, sample_count, prev_clicks, next_clicks):
    page = next_clicks - prev_clicks
    start = page * sample_count
    end = start + sample_count
    dff = df.iloc[start:end]
    fig = px.histogram(dff, x=selected_axis, nbins=30, title=f"Histogram of {selected_axis}")

    summary_table = dff[[selected_axis]].describe().reset_index()
    summary_html = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in summary_table.columns])),
        html.Tbody([
            html.Tr([html.Td(summary_table.iloc[i][col]) for col in summary_table.columns])
            for i in range(len(summary_table))
        ])
    ])

    return fig, html.Div([html.H4("Data Summary"), summary_html])

if __name__ == '__main__':
    app.run(debug=True)
