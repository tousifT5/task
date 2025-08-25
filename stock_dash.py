import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
import json
from dash import dcc ,html ,Input, Output, callback ,State
import yfinance as yf
from datetime import datetime,timedelta,date
from plotly.subplots import make_subplots


# external_stylesheets = ['amazone_dash_style.css']


# ############################################################ PLOTS ############################################################

def calculate_rsi(data, window=14):
    """Calculates Relative Strength Index (RSI) manually."""
    # Ensure 'Close' column is numeric
    close_prices = data['Close'].astype("float")

    # Calculate price changes
    delta = close_prices.diff()

    # Calculate gains (upward changes) and losses (downward changes)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gains and losses over the window
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()

    # Calculate Relative Strength (RS)
    # Handle division by zero for avg_loss
    rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi


def rsi(ticker="AAPL",date="2025-08-20",interval="5m"):
    start = datetime.strptime(date, "%Y-%m-%d")
    end = start + timedelta(days=1)
    data = yf.download(ticker,start= start.strftime(format="%Y-%m-%d"),end = end.strftime(format="%Y-%m-%d") ,multi_level_index=False,interval=interval)
    data = pd.DataFrame(data)
    print(data.shape)
    data.reset_index(inplace=True)
    
    data['RSI'] = calculate_rsi(data, window=14)
    rsi = px.scatter(data ,x="Datetime",y= "RSI")
    rsi.update_traces(mode='lines')
    rsi.update_layout( template="plotly_dark",width = 1450,title_text=f'RSI for {ticker.upper()}')
    
    return rsi


def calculate_sma(data, window):
    """Calculates Simple Moving Average (SMA) manually."""
    return data['Close'].rolling(window=window).mean()

def calculate_ema(data, window):
    """Calculates Exponential Moving Average (EMA) manually."""
    return data['Close'].ewm(span=window, adjust=False).mean()


def candle(ticker="AAPL",date="2025-08-20",interval="5m"):
    start = datetime.strptime(date, "%Y-%m-%d")
    end = start + timedelta(days=1)
    data = yf.download(ticker,start= start.strftime(format="%Y-%m-%d"),end = end.strftime(format="%Y-%m-%d") ,multi_level_index=False,interval=interval)
    data = pd.DataFrame(data)
    print(data.shape)
    data.reset_index(inplace=True)
    
    data['SMA_10'] = calculate_sma(data, 10)
    data['EMA_10'] = calculate_ema(data, 10)
    # sma = px.scatter(data ,x="Datetime",y= "SMA_3",title="SMA")
    # sma.update_traces(mode='lines')

    fig = make_subplots(
    rows=1, cols=1
    )
    
    fig.add_trace(
        go.Candlestick(
            x = data.Datetime,
            open = data.Open,
            high = data.High,
            low = data.Low,
            close = data.Close,
            name='candle',
        ),
        row=1, col=1 # Add to the first row, first column
    )
    
    fig.add_trace(
        go.Scatter(
            x=data["Datetime"],
            y=data['SMA_10'],
            mode='lines',
            name='SMA 10',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=data["Datetime"],
            y=data['EMA_10'],
            mode='lines',
            name='EMA 10',
            line=dict(color='pink', width=1)
        ),
        row=1, col=1
    )
    
    fig.update_layout(
    title_text=f'{ticker.upper()} Candlestick Chart with SMA, EMA',
    xaxis_rangeslider_visible=False, # Often removed for intraday charts
    height=600, # Total height of the figure
    width = 1450,
    hovermode="x unified", # Shows hover data for all traces at a given x-point
    # Optionally, set the theme
    template="plotly_dark",
    legend_orientation="h",
    legend_y=1.02, # Position legend above the chart
    legend_x=0.1
    )

    # rsi = rsi(ticker,date,interval)
    print(ticker)
    print("sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss")
    return fig

def group_bar(ticker="AAPL"):
    data = yf.Ticker(ticker)
    data = data.recommendations
    label_mapping = {
    '0m': 'This Month',
    '-1m': 'Last Month',
    '-2m': '2 Months Ago',
    '-3m': '3 Months Ago'
    }
    data['period'] = data['period'].map(label_mapping)
    temp = pd.melt(data, id_vars=['period'])

    bar = px.histogram(temp, x="period", y="value",
             color='variable', barmode='group',
             height=400,width = 720,title=f'bar122 for {ticker.upper()}')
    return bar

def line(ticker="AAPL",start="2020-01-01",end="2025-01-01",interval="1mo"):
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")
    data = yf.download(ticker,start= start.strftime(format="%Y-%m-%d"), end = end.strftime(format="%Y-%m-%d"),multi_level_index=False,interval=interval)
    data.reset_index(inplace=True)
    print(data.shape)
    line_chart = px.line(data , x = "Date" , y = "Close",title=f'line for {ticker.upper()}')
    return line_chart

# ############################################################ WIDGETS ############################################################

ticker_input = dcc.Input(
    id="ticker-input",
    type="text", 
    placeholder="AAPL",
    value="AAPL"
)


today_date = datetime.now().date()

# Corrected dcc.DatePickerRange
date_range = dcc.DatePickerRange(
    id='date_range',
    display_format='MMM Do, YY',
    # Corrected: Use .date() to get a date object from datetime.now()
    min_date_allowed=date(1980, 1, 1),
    minimum_nights=91,
    max_date_allowed=today_date, # Corrected
    initial_visible_month=today_date, # Corrected: only one instance, set to today

)

# Corrected dcc.DatePickerSingle
single_date = dcc.DatePickerSingle(
    id='single_date_picker', # Added an ID for consistency, you might need it for callbacks
    display_format='MMM Do, YY',
    min_date_allowed=today_date-timedelta(40),
    max_date_allowed=today_date, 

    initial_visible_month=today_date, 
    placeholder='Select A Date',
    date=today_date,
    style={"width":"100%"}
)

# dcc.Dropdown was already correct
dropdown_choice = dcc.Dropdown(
    options=[{"label": "Monthly", "value": "1mo"}, {"label": "3 Monthly", "value": "3mo"}], 
    value="Monthly",
    id="line_choice",
    style={"width":"100%"}
)

candle_interval_dropdown = dcc.Dropdown(
    options=[{"label": "1m", "value": "1m"}, {"label": "2m", "value": "2m"},
            {"label": "5m", "value": "5m"}, {"label": "15m", "value": "15m"}], 
    value="5m",
    id="interval",
    style={'width': '100%'}
)

submit_candle_button = html.Button(
    'Update Candlestick Chart',
    id='submit-candle-button',
    n_clicks=0,
    style={'marginLeft': '10px', 'padding': '8px 15px', 'backgroundColor': '#28a745', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}
)

submit_ticker_button = html.Button(
    'Update Ticker Data',
    id='submit-ticker-button',
    n_clicks=0,
    style={'marginLeft': '10px', 'padding': '8px 15px', 'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}
)

submit_line_button = html.Button(
    'Update Line Plot',
    id='submit-line-button',
    n_clicks=0,
    style={'marginLeft': '10px', 'padding': '8px 15px', 'backgroundColor': '#ffc107', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}
)


# ############################################################ LAYOUT ############################################################

def init_dash_app(flask_app):
    dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname='/dashboard/')


    dash_app.layout = html.Div([html.H2(children="Stock dashboard",
                        id="heading"),

                        html.Div([
                        html.Label("Ticker Symbol:", style={'marginRight': '5px', 'fontWeight': 'bold'}),
                        ticker_input,
                        submit_ticker_button,
                        html.Div(
                            "For better results, try adding an exchange suffix, e.g., 'TATAMOTORS.NS' or 'D05.SI'.",
                            id="suggestion_message",
                            style={'fontSize': '0.8em', 'color': '#777', 'marginTop': '5px', 'display': 'inline-block', 'marginLeft': '10px', 'maxWidth': '300px'}
                        ),
                        ], id="ticker_container", style={'textAlign': 'center', 'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#f2f2f2', 'borderRadius': '8px', 'maxWidth': 'fit-content', 'margin': '0 auto 30px auto'}),

                        html.Hr(style={'borderColor': '#ccc'}),

                        html.Br(),

                        html.Div(children=[
                        html.Div([
                            html.Label("Date ", style={'marginRight': '5px', 'fontWeight': 'bold'}),
                            single_date # dcc.DatePickerSingle component
                        ], style={"display": "flex", "alignItems": "center"}), # Each label-input pair in its own flex div

                        html.Div([
                            html.Label("Interval ", style={'marginRight': '5px', 'fontWeight': 'bold'}),
                            candle_interval_dropdown # dcc.Dropdown component
                        ], style={"display": "flex", "alignItems": "center", "width": "200px"}), # Also set width here

                        html.Div(submit_candle_button) # The submit button
                        ],
                        id="candle_input_container",
                        style={"display": "flex", "gap": "15px", "alignItems": "center", "flexWrap": "wrap"} # Align items to center vertically
                        ),

                        html.Br(),
                        
                        html.Div([

                            html.Div([
                            html.Div(dcc.Graph(figure=candle(),id="candle")),
                                ],
                                style={"display": "flex","gap": "15px","width":"100px"}
                                ),

                            html.Br(),
                            html.Div([
                            html.Div(dcc.Graph(figure=rsi(),id="rsi")),
                            ],
                            style={"display": "flex", "gap": "15px","width":"100px"}
                            ),

                            html.Br(),

                        #     html.Div(dcc.Graph(figure=tree()),id="tree"),

                            html.Div([
                                html.Div(dcc.Graph(figure=group_bar(),id="bar1"),
                                id="state"
                                ),

                                html.Div(dcc.Graph(figure=group_bar(),id="bar2"),
                                id="month"
                                ),],

                                id="inpt_container",
                                style={"display": "flex", "gap": "15px","width":"100px"}
                                ),

                            html.Br(),

                            html.Div([
                            # Date Range Picker

                            html.Div([
                                html.Label("Select Date ", style={'marginRight': '5px', 'fontWeight': 'bold'}),
                                date_range # dcc.DatePickerRange component
                            ], style={"display": "flex", "alignItems": "center", "width": "380px"}), # Set width for this container

                            # Interval Dropdown
                            html.Div([
                                html.Label("Interval ", style={'marginRight': '5px', 'fontWeight': 'bold'}),
                                dropdown_choice
                            ], style={"display": "flex", "alignItems": "center", "width": "300px"}), # Set width for this container

                            # Submit Button
                            html.Div(submit_line_button)
                            ], style={"display": "flex", "gap": "15px", "alignItems": "center", "flexWrap": "wrap"}), # Align items and allow wrap

                            html.Div([
                            html.Div(dcc.Graph(figure=line(),id="line")),
                                ],),

                            
                            html.Br(),

                        ],
                        id="graph_container"
                        )

                    ])

    # ############################################################ CALLBACK ############################################################

    # @callback(Output(component_id="candle",component_property="figure"),
    #         Output(component_id="rsi",component_property="figure"),
    #         Input(component_id="ticker",component_property="value"))
    # def change_candle_rsi(ticker):
    #     print(ticker)
    #     print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
    #     return candle(ticker),rsi(ticker)


    # dashboard
    @callback(
        Output('candle', 'figure',allow_duplicate=True),
        Output('rsi', 'figure',allow_duplicate=True),
        Output('bar1', 'figure'),
        Output('bar2', 'figure'),
        Output('line', 'figure'),
        Input('submit-ticker-button', 'n_clicks'),
        State('ticker-input', 'value'),
        prevent_initial_call=True
    )
    def update_on_ticker_submit(n_clicks, ticker_val):
        if n_clicks is None or n_clicks == 0:
            return None

        candle_chart = candle(ticker_val)
        rsi_chart = rsi(ticker_val)
        group_bar_chart = group_bar(ticker_val)
        line_chart = line(ticker_val)

        return candle_chart, rsi_chart, group_bar_chart, group_bar_chart, line_chart


    @callback(
        Output('candle', 'figure',allow_duplicate=True),
        Output('rsi', 'figure',allow_duplicate=True),
        Input('submit-candle-button', 'n_clicks'),
        State('ticker-input', 'value'),
        State('single_date_picker', 'date'),
        State('interval', 'value'),
        prevent_initial_call=True
    )
    def update_on_candle_submit(n_clicks, ticker_val,single_date,candle_interval):
        if n_clicks is None or n_clicks == 0:
            return None
        candle_chart = candle(ticker_val,single_date,candle_interval)
        rsi_chart = rsi(ticker_val,single_date,candle_interval)


        return candle_chart, rsi_chart

    @callback(
        Output('line', 'figure',allow_duplicate=True),
        Input('submit-line-button', 'n_clicks'),
        State('ticker-input', 'value'),
        State('date_range', 'start_date'),
        State('date_range', 'end_date'),
        State('line_choice', 'value'),
        prevent_initial_call=True
    )
    def update_on_line_submit(n_clicks, ticker_val,start_date,end_date,line_choice):
        if n_clicks is None or n_clicks == 0:
            return None
        print(ticker_val)
        print(start_date)
        print(end_date)
        print(line_choice)
        line_chart = line(ticker_val,start_date,end_date,line_choice)

        return line_chart

    return dash_app
        
