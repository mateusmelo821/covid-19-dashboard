import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pycountry

def get_cases(df):
    return df['New_Cases_Confirmed'].sum()
def get_deaths(df):
    return df['New_Cases_Death'].sum()
def get_incidence(df):
    return round(get_cases(df)/df.groupby('Country')['Population'].max().sum(), 3)
def get_mortality(df):
    return round(get_deaths(df)/df.groupby('Country')['Population'].max().sum(), 3)
def get_lethality(df):
    return round(get_deaths(df)/get_cases(df), 3)

def get_kpi(indicator, title):
    fig = go.Figure(go.Indicator(
        mode = "number",
        value = indicator,
        number = {'font':{'size':36}, 'font_color':'black'},
        title = {'text': title, 'font_size':16, 'font_color':'black'},
        domain = {'x': [0, 1], 'y': [0, 1]}
    ),layout= go.Layout(height=50))
    return fig
def cases_deaths_by_country(df):
    cases_suffix = ''
    deaths_suffix = ''
    temp_df = df.groupby(['Code', 'Country'])[['New_Cases_Confirmed', 'New_Cases_Death']].sum().reset_index()
    if temp_df['New_Cases_Confirmed'].max()>10**6:
        cases_suffix = 'M'
        temp_df['New_Cases_Confirmed'] = temp_df['New_Cases_Confirmed']/10**6
    elif temp_df['New_Cases_Confirmed'].max()>10**3:
        cases_suffix = 'K'
        temp_df['New_Cases_Confirmed'] = temp_df['New_Cases_Confirmed']/10**3
    if temp_df['New_Cases_Death'].max()>10**6:
        deaths_suffix = 'M'
        temp_df['New_Cases_Death'] = temp_df['New_Cases_Death']/10**6
    elif temp_df['New_Cases_Confirmed'].max()>10**3:
        deaths_suffix = 'K'
        temp_df['New_Cases_Death'] = temp_df['New_Cases_Death']/10**3
    return [temp_df, cases_suffix, deaths_suffix]
    
    

def get_bubble_map(df_suffixex, title):
    df = df_suffixex[0]
    cases_suffix = df_suffixex[1]
    deaths_suffix = df_suffixex[2]
    fig = px.scatter_geo(df, locations="Code", color="New_Cases_Confirmed",
                     hover_name="Country",
                     hover_data={"Code":False,
                                 "New_Cases_Confirmed":":.2f",
                                 "New_Cases_Death":":.2f"},
                     size="New_Cases_Death",
                     color_continuous_scale=px.colors.sequential.YlOrRd,
                     title = title,
                     size_max = 40,
                     labels = {"New_Cases_Confirmed":"Cases ({})".format(cases_suffix),
                               "New_Cases_Death":"Deaths ({})".format(deaths_suffix)},
                     projection="natural earth")
    return fig

def get_cases_day(df):
    return df.groupby('Date')['New_Cases_Confirmed'].sum().reset_index()
def get_deaths_day(df):
    return df.groupby('Date')['New_Cases_Death'].sum().reset_index()

def get_line_chart(df, title, column):
    fig = px.line(df, x='Date', y=column, labels={column:title}, title=title+" by Day")
    return fig

covid_df = pd.read_csv('data/final_dataset.csv')
covid_df['Date'] = pd.to_datetime(covid_df['Date'])

date_dict = {}
for i,date in enumerate(covid_df['Date'].unique()):
    date_dict[i]=str(pd.to_datetime(date).date().strftime('%m/%d/%Y'))

countries = ['All']
countries.extend(list(covid_df['Country'].unique()))

app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Covid-19 Analytics Dashboard"), md=10), align="start", justify="evenly", style={"height": 100}),
    dbc.Row([
        dbc.Col(html.Div("Select the country:"), md=2),
        dbc.Col(html.Div("Select the period:"), md=8)
        
    ], align="start", justify="evenly"),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='my-dropdown',
                    options=countries,
                     multi=False,
                     clearable=False,
                     value='All',
                    ), md=2),
        dbc.Col(dcc.RangeSlider(min=0,
                   max=1142,
                   value=[0, 1142],
                   marks={0:date_dict[0], 366:date_dict[366], 366+365:date_dict[366+365], 1142:date_dict[1142] },
                    id='my-slider'), md=8)
    ], align="start", justify="evenly"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='cases_kpi', figure={}, responsive=True,  style={"height": "100%"}), md=2, style={"height": "100%"}),
        dbc.Col(dcc.Graph(id='deaths_kpi', figure={}, responsive=True, style={"height": "100%"}), md=2, style={"height": "100%"}),
        dbc.Col(dcc.Graph(id='incidence_kpi', figure={}, responsive=True, style={"height": "100%"}), md=2, style={"height": "100%"}),
        dbc.Col(dcc.Graph(id='mortality_kpi', figure={}, responsive=True, style={"height": "100%"}), md=2, style={"height": "100%"}),
        dbc.Col(dcc.Graph(id='lethality_kpi', figure={}, responsive=True,  style={"height": "100%"}), md=2, style={"height": "100%"})
    ], align="start", justify="evenly", style={"height": 100}),
    dbc.Row([
        dbc.Col(dcc.Graph(id='map', figure={}, responsive=True), md=10)
    ], align="start", justify="evenly"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='cases_line', figure={}, responsive=True), md=10)
    ], align="start", justify="evenly"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='deaths_line', figure={}, responsive=True), md=10)
    ], align="start", justify="evenly")
], fluid=True)

@app.callback(
    Output('cases_kpi', 'figure'),
    Output('deaths_kpi', 'figure'),
    Output('incidence_kpi', 'figure'),
    Output('mortality_kpi', 'figure'),
    Output('lethality_kpi', 'figure'),
    Output('map', 'figure'),
    Output('cases_line', 'figure'),
    Output('deaths_line', 'figure'),
    Input('my-slider', 'value'),
    Input('my-dropdown', 'value')
)
def update_output(period, country):
    dt_ini=pd.to_datetime(date_dict[period[0]])
    dt_fin=pd.to_datetime(date_dict[period[1]])
    query = '(Date>=@dt_ini)&(Date<=@dt_fin)'
    if country != 'All':
        query = query + '&(Country==@country)'
    fig_cases = get_kpi(get_cases(covid_df.query(query)), 'Cases')
    fig_deaths = get_kpi(get_deaths(covid_df.query(query)), 'Deaths')
    fig_incidence = get_kpi(get_incidence(covid_df.query(query)), 'Incidence')
    fig_mortality = get_kpi(get_mortality(covid_df.query(query)), 'Mortality')
    fig_lethality = get_kpi(get_lethality(covid_df.query(query)), 'Lethality')
    fig_map = get_bubble_map(cases_deaths_by_country(covid_df.query(query)), 'Cases and Deaths by Country')
    
    fig_cases_line = get_line_chart(get_cases_day(covid_df.query(query)), 'Cases', 'New_Cases_Confirmed')
    fig_deaths_line = get_line_chart(get_deaths_day(covid_df.query(query)), 'Deaths', 'New_Cases_Death')
    return fig_cases, fig_deaths, fig_incidence, fig_mortality, fig_lethality, fig_map, fig_cases_line, fig_deaths_line


app.run(debug=True, port=8050)