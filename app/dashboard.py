#!/usr/bin/env python3
"""
Dash-приложение: Дашборд эффективности маркетинговых трат (ROI) с ML-прогнозированием.
Вариант 7 — Маркетинговая аналитика с ML-моделью.
"""

import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import psycopg2
from ml_model import roi_predictor
import numpy as np

# --- Подключение к БД ---
DB_HOST = os.getenv("DB_HOST", "db-service")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "marketing_db")
DB_USER = os.getenv("POSTGRES_USER", "marketing_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "changeme")

# --- Загрузка ML-модели (для Readiness Probe) ---
print("[App] Запуск приложения, начало загрузки ML-модели...")
model_load_start = time.time()
roi_predictor.load_model()  # Имитация загрузки модели (25 секунд)
model_load_time = time.time() - model_load_start
print(f"[App] Модель загружена за {model_load_time:.2f} секунд")

# --- Инициализация Dash приложения ---
app = Dash(__name__)
server = app.server  # для gunicorn


# --- Функция загрузки данных ---
def load_data():
    """Загрузка данных из PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        )
        # Добавляем вычисление ROI прямо в SQL запросе
        query = """
        SELECT 
            *,
            CASE 
                WHEN spend > 0 THEN ((revenue - spend)::float / spend::float) * 100
                ELSE 0 
            END as roi_percent
        FROM marketing_campaigns;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()


# --- Функция прогнозирования ROI ---
def predict_future_roi(channel, spend_amount):
    """Прогнозирование ROI для гипотетической кампании"""
    # Создание признаков для модели
    channels = ["Social Media", "Google Ads", "Email", "TV", "Billboard", "Partners"]
    regions = ["North", "South", "East", "West", "Central"]

    # One-hot encoding для демонстрации
    channel_encoded = channels.index(channel) if channel in channels else 0
    region_encoded = 0  # Упрощенно

    features = np.array([[spend_amount, 10000, 500, channel_encoded, region_encoded]])
    predicted_roi = roi_predictor.predict_roi(features)[0]
    return predicted_roi


# --- Health check endpoint ---
@app.server.route('/health')
def health_check():
    """Endpoint для liveness probe"""
    return {'status': 'healthy'}, 200


@app.server.route('/ready')
def ready_check():
    """Endpoint для readiness probe (проверка загрузки модели)"""
    if roi_predictor.is_model_ready():
        return {'status': 'ready', 'model_loaded': True}, 200
    else:
        return {'status': 'not ready', 'model_loaded': False}, 503


# --- Layout приложения ---
app.layout = html.Div([
    html.H1("📊 Маркетинговая аналитика: Прогнозирование ROI с ML",
            style={'textAlign': 'center', 'color': '#2c3e50'}),

    html.Div([
        html.Div([
            html.H3("Текущая статистика"),
            html.Div(id='stats-summary')
        ], style={'width': '100%', 'padding': '20px', 'backgroundColor': '#f8f9fa'}),
    ]),

    html.Div([
        html.Div([
            html.Label("Выберите канал:"),
            dcc.Dropdown(id='channel-dropdown', multi=True, placeholder="Все каналы"),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Выберите продукт:"),
            dcc.Dropdown(id='product-dropdown', multi=True, placeholder="Все продукты"),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'}),
    ]),

    html.Div([
        dcc.Graph(id='roi-by-channel-graph'),
    ]),

    html.Div([
        dcc.Graph(id='spend-vs-revenue-graph'),
    ]),

    html.Div([
        dcc.Graph(id='roi-trend-over-time'),
    ]),

    html.Div([
        html.H3("🔮 ML-прогнозирование ROI для новой кампании"),
        html.Div([
            html.Div([
                html.Label("Канал:"),
                dcc.Dropdown(
                    id='predict-channel',
                    options=[
                        {'label': 'Social Media', 'value': 'Social Media'},
                        {'label': 'Google Ads', 'value': 'Google Ads'},
                        {'label': 'Email', 'value': 'Email'},
                        {'label': 'TV', 'value': 'TV'},
                        {'label': 'Billboard', 'value': 'Billboard'},
                        {'label': 'Partners', 'value': 'Partners'}
                    ],
                    value='Google Ads'
                ),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

            html.Div([
                html.Label("Бюджет (усл. ед.):"),
                dcc.Input(id='predict-spend', type='number', value=10000, min=1000, max=100000, step=1000),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

            html.Div([
                html.Button('Прогнозировать ROI', id='predict-button', n_clicks=0,
                            style={'backgroundColor': '#27ae60', 'color': 'white', 'padding': '10px 20px'}),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        ]),
        html.Div(id='prediction-result', style={'fontSize': '24px', 'textAlign': 'center', 'padding': '20px'}),
    ], style={'backgroundColor': '#e8f4f8', 'padding': '20px', 'marginTop': '20px'}),

    dcc.Interval(id='interval-component', interval=60 * 1000, n_intervals=0)
])


# --- Callback для обновления опций Dropdown ---
@app.callback(
    [Output('channel-dropdown', 'options'),
     Output('product-dropdown', 'options')],
    [Input('interval-component', 'n_intervals')]
)
def update_dropdowns(n):
    df = load_data()
    if df.empty:
        return [], []
    channel_options = [{'label': i, 'value': i} for i in sorted(df['channel'].unique())]
    product_options = [{'label': i, 'value': i} for i in sorted(df['product'].unique())]
    return channel_options, product_options


# --- Callback для обновления статистики ---
@app.callback(
    Output('stats-summary', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_stats(n):
    df = load_data()
    if df.empty:
        return "Нет данных для отображения"

    total_campaigns = len(df)
    avg_roi = df['roi_percent'].mean()
    total_spend = df['spend'].sum()
    total_revenue = df['revenue'].sum()

    return html.Div([
        html.Span(f"Всего кампаний: {total_campaigns:,}", style={'marginRight': '30px'}),
        html.Span(f"Средний ROI: {avg_roi:.1f}%", style={'marginRight': '30px'}),
        html.Span(f"Общие траты: {total_spend:,.0f}", style={'marginRight': '30px'}),
        html.Span(f"Общая выручка: {total_revenue:,.0f}", style={'marginRight': '30px'}),
    ])


# --- Callback для обновления графиков ---
@app.callback(
    [Output('roi-by-channel-graph', 'figure'),
     Output('spend-vs-revenue-graph', 'figure'),
     Output('roi-trend-over-time', 'figure')],
    [Input('channel-dropdown', 'value'),
     Input('product-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graphs(selected_channels, selected_products, n):
    df = load_data()
    if df.empty:
        no_data_fig = go.Figure()
        no_data_fig.add_annotation(text="Нет данных или ошибка подключения к БД", showarrow=False)
        return no_data_fig, no_data_fig, no_data_fig

    # Фильтрация данных
    filtered_df = df.copy()
    if selected_channels and len(selected_channels) > 0:
        filtered_df = filtered_df[filtered_df['channel'].isin(selected_channels)]
    if selected_products and len(selected_products) > 0:
        filtered_df = filtered_df[filtered_df['product'].isin(selected_products)]

    if filtered_df.empty:
        no_data_fig = go.Figure()
        no_data_fig.add_annotation(text="Нет данных для выбранных фильтров", showarrow=False)
        return no_data_fig, no_data_fig, no_data_fig

    # 1. График ROI по каналам
    roi_by_channel = filtered_df.groupby('channel')['roi_percent'].mean().reset_index().sort_values('roi_percent',
                                                                                                    ascending=False)
    fig_roi_channel = px.bar(roi_by_channel, x='channel', y='roi_percent',
                             title='Средний ROI по каналам (%)',
                             color='roi_percent', color_continuous_scale='RdYlGn',
                             labels={'channel': 'Канал', 'roi_percent': 'ROI (%)'})

    # 2. Scatter plot: Траты vs Выручка
    fig_spend_revenue = px.scatter(filtered_df, x='spend', y='revenue', color='channel',
                                   size='clicks', hover_data=['campaign_id', 'product'],
                                   title='Зависимость Выручки от Трат',
                                   labels={'spend': 'Траты (усл. ед.)', 'revenue': 'Выручка (усл. ед.)'})
    max_val = max(filtered_df['spend'].max(), filtered_df['revenue'].max())
    fig_spend_revenue.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode='lines',
                                           line=dict(dash='dash', color='grey'), name='y=x'))

    # 3. Тренд ROI во времени
    df_time = filtered_df.copy()
    df_time['date'] = pd.to_datetime(df_time['date'])
    roi_over_time = df_time.groupby([pd.Grouper(key='date', freq='W-MON'), 'channel'])[
        'roi_percent'].mean().reset_index()
    fig_trend = px.line(roi_over_time, x='date', y='roi_percent', color='channel',
                        title='Динамика среднего ROI (по неделям)',
                        labels={'date': 'Дата', 'roi_percent': 'ROI (%)', 'channel': 'Канал'})

    return fig_roi_channel, fig_spend_revenue, fig_trend


# --- Callback для прогнозирования ---
@app.callback(
    Output('prediction-result', 'children'),
    [Input('predict-button', 'n_clicks')],
    [Input('predict-channel', 'value'),
     Input('predict-spend', 'value')]
)
def update_prediction(n_clicks, channel, spend):
    if n_clicks == 0:
        return ""

    if not roi_predictor.is_model_ready():
        return "⚠️ Модель еще загружается, попробуйте через несколько секунд..."

    try:
        predicted_roi = predict_future_roi(channel, spend)
        expected_revenue = spend * (1 + predicted_roi / 100)

        return html.Div([
            html.H4(f"Прогнозируемый ROI: {predicted_roi:.1f}%",
                    style={'color': '#27ae60' if predicted_roi > 0 else '#e74c3c'}),
            html.P(f"При бюджете {spend:,.0f} усл. ед. ожидаемая выручка: {expected_revenue:,.0f} усл. ед.")
        ])
    except Exception as e:
        return f"Ошибка прогнозирования: {e}"


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)