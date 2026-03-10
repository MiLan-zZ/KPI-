import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from 数据分析 import calculate_all_metrics, rfm_analysis
import pandas as pd

# 初始化Dash应用
app = dash.Dash(__name__, title="全渠道零售智能KPI监控系统")
server = app.server  # 部署用

# 加载所有指标和数据（增加空数据处理）
try:
    all_metrics, rfm_result, orders, inventory, campaigns = calculate_all_metrics()
    # 空数据兜底
    if all_metrics is None:
        # 初始化空指标，避免报错
        all_metrics = {
            '基础交易指标': {'GMV(元)': 0, '销售收入(元)': 0, '净利润(元)': 0, '利润率(%)': 0, '客单价(元)': 0,
                             '下单用户数': 0},
            '活动ROI&CAC': {'活动总成本(元)': 0, '活动新增客户数': 0, '活动增量利润(元)': 0, '活动ROI(倍)': 0,
                            'CAC(元/人)': 0},
            '库存周转率': {'销售成本(元)': 0, '平均库存价值(元)': 0, '库存周转率(次)': 0},
            '库龄结构': {'库龄<30天(数量)': 0, '库龄30-90天(数量)': 0, '库龄>90天(数量)': 0,
                         '库龄<30天占比(%)': 0, '库龄30-90天占比(%)': 0, '库龄>90天占比(%)': 0}
        }
    if rfm_result.empty:
        rfm_result = pd.DataFrame({
            '客户ID': ['无数据'], 'R(天)': [0], 'F(次)': [0], 'M(元)': [0],
            'R分': [0], 'F分': [0], 'M分': [0], 'RFM总分': ['000']
        })
except Exception as e:
    print(f"数据加载失败：{e}")
    # 完全兜底
    all_metrics = {
        '基础交易指标': {'GMV(元)': 0, '销售收入(元)': 0, '净利润(元)': 0, '利润率(%)': 0, '客单价(元)': 0,
                         '下单用户数': 0},
        '活动ROI&CAC': {'活动总成本(元)': 0, '活动新增客户数': 0, '活动增量利润(元)': 0, '活动ROI(倍)': 0,
                        'CAC(元/人)': 0},
        '库存周转率': {'销售成本(元)': 0, '平均库存价值(元)': 0, '库存周转率(次)': 0},
        '库龄结构': {'库龄<30天(数量)': 0, '库龄30-90天(数量)': 0, '库龄>90天(数量)': 0,
                     '库龄<30天占比(%)': 0, '库龄30-90天占比(%)': 0, '库龄>90天占比(%)': 0}
    }
    rfm_result = pd.DataFrame({
        '客户ID': ['无数据'], 'R(天)': [0], 'F(次)': [0], 'M(元)': [0],
        'R分': [0], 'F分': [0], 'M分': [0], 'RFM总分': ['000']
    })
    orders = pd.DataFrame({'channel': ['无数据'], 'revenue': [0]})

# --------------------- 页面布局 ---------------------
app.layout = html.Div(
    style={
        'font-family': 'Arial, sans-serif',
        'padding': '20px',
        'background-color': '#f5f5f5',
        'max-width': '1400px',  
        'margin': '0 auto',  
        'overflow': 'hidden'  
    },
    children=[
        # 标题
        html.H1("全渠道零售智能KPI监控与分析系统",
                style={'text-align': 'center', 'color': '#2c3e50', 'margin-bottom': '30px'}),

        # 第一行：核心交易指标卡片
        html.Div(
            style={
                'display': 'grid',
                'grid-template-columns': 'repeat(auto-fit, minmax(200px, 1fr))',  
                'gap': '20px',
                'margin': '30px 0',
                'max-height': '300px', 
                'overflow-y': 'auto'  
            },
            children=[
                # GMV卡片
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '180px'},  
                    children=[
                        html.H3("GMV（成交总额）", style={'color': '#3498db', 'margin': '0 0 10px 0'}),
                        html.P(f"{all_metrics['基础交易指标']['GMV(元)']:,} 元",
                               style={'font-size': '24px', 'font-weight': 'bold', 'margin': 0})
                    ]
                ),
                # 销售收入卡片
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '180px'},
                    children=[
                        html.H3("销售收入", style={'color': '#2ecc71', 'margin': '0 0 10px 0'}),
                        html.P(f"{all_metrics['基础交易指标']['销售收入(元)']:,} 元",
                               style={'font-size': '24px', 'font-weight': 'bold', 'margin': 0})
                    ]
                ),
                # 净利润卡片
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '180px'},
                    children=[
                        html.H3("净利润", style={'color': '#e74c3c', 'margin': '0 0 10px 0'}),
                        html.P(f"{all_metrics['基础交易指标']['净利润(元)']:,} 元",
                               style={'font-size': '24px', 'font-weight': 'bold', 'margin': 0})
                    ]
                ),
                # 利润率卡片
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '180px'},
                    children=[
                        html.H3("利润率", style={'color': '#9b59b6', 'margin': '0 0 10px 0'}),
                        html.P(f"{all_metrics['基础交易指标']['利润率(%)']} %",
                               style={'font-size': '24px', 'font-weight': 'bold', 'margin': 0})
                    ]
                ),
                # 客单价卡片
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '180px'},
                    children=[
                        html.H3("客单价", style={'color': '#f39c12', 'margin': '0 0 10px 0'}),
                        html.P(f"{all_metrics['基础交易指标']['客单价(元)']} 元",
                               style={'font-size': '24px', 'font-weight': 'bold', 'margin': 0})
                    ]
                ),
                # 库存周转率卡片
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '180px'},
                    children=[
                        html.H3("库存周转率", style={'color': '#1abc9c', 'margin': '0 0 10px 0'}),
                        html.P(f"{all_metrics['库存周转率']['库存周转率(次)']} 次",
                               style={'font-size': '24px', 'font-weight': 'bold', 'margin': 0})
                    ]
                )
            ]
        ),

        # 第二行：活动ROI+CAC + 库龄结构
        html.Div(
            style={
                'display': 'grid',
                'grid-template-columns': '1fr 1fr',
                'gap': '20px',
                'margin': '30px 0',
                'max-height': '400px'  #
            },
            children=[
                # 活动ROI&CAC
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '380px',
                           'overflow-y': 'auto'},  # 内容超出则滚动
                    children=[
                        html.H3("营销活动效果（ROI & CAC）", style={'color': '#2c3e50', 'margin-top': 0}),
                        html.Div([
                            html.P(f"活动总成本：{all_metrics['活动ROI&CAC']['活动总成本(元)']:,} 元",
                                   style={'margin': '10px 0'}),
                            html.P(f"新增客户数：{all_metrics['活动ROI&CAC']['活动新增客户数']} 人",
                                   style={'margin': '10px 0'}),
                            html.P(f"增量利润：{all_metrics['活动ROI&CAC']['活动增量利润(元)']:,} 元",
                                   style={'margin': '10px 0'}),
                            html.P(f"活动ROI：{all_metrics['活动ROI&CAC']['活动ROI(倍)']} 倍",
                                   style={'font-weight': 'bold', 'margin': '10px 0'}),
                            html.P(f"CAC：{all_metrics['活动ROI&CAC']['CAC(元/人)']} 元/人",
                                   style={'font-weight': 'bold', 'margin': '10px 0'})
                        ])
                    ]
                ),
                # 库龄结构饼图（固定图表高度）
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '380px'},
                    children=[
                        html.H3("库存库龄结构", style={'color': '#2c3e50', 'margin-top': 0}),
                        dcc.Graph(
                            figure=px.pie(
                                values=[
                                    all_metrics['库龄结构']['库龄<30天占比(%)'],
                                    all_metrics['库龄结构']['库龄30-90天占比(%)'],
                                    all_metrics['库龄结构']['库龄>90天占比(%)']
                                ],
                                names=['<30天', '30-90天', '>90天'],
                                title='库龄占比分布',
                                color_discrete_map={
                                    '<30天': '#2ecc71',
                                    '30-90天': '#f39c12',
                                    '>90天': '#e74c3c'
                                }
                            ),
                            style={'height': '300px'}  # 固定图表高度
                        )
                    ]
                )
            ]
        ),

        # 第三行：RFM分析表格 + RFM分布柱状图
        html.Div(
            style={
                'display': 'grid',
                'grid-template-columns': '1fr 1fr',
                'gap': '20px',
                'margin': '30px 0',
                'max-height': '500px'
            },
            children=[
                # RFM分析表格
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '480px',
                           'overflow-y': 'auto'},
                    children=[
                        html.H3("RFM客户分层结果（前20行）", style={'color': '#2c3e50', 'margin-top': 0}),
                        dash_table.DataTable(
                            data=rfm_result.head(20).to_dict('records'),
                            columns=[{'name': col, 'id': col} for col in rfm_result.columns],
                            style_table={'overflowX': 'auto', 'height': '380px'},  
                            style_cell={'padding': '8px', 'font-size': '12px'},
                            style_header={'backgroundColor': '#3498db', 'color': 'white', 'font-weight': 'bold'}
                        )
                    ]
                ),
                # RFM评分分布
                html.Div(
                    style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                           'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'height': '480px'},
                    children=[
                        html.H3("RFM评分分布", style={'color': '#2c3e50', 'margin-top': 0}),
                        dcc.Graph(
                            figure=go.Figure(
                                data=[
                                    go.Histogram(x=rfm_result['R分'], name='R分', marker_color='#3498db'),
                                    go.Histogram(x=rfm_result['F分'], name='F分', marker_color='#2ecc71'),
                                    go.Histogram(x=rfm_result['M分'], name='M分', marker_color='#e74c3c')
                                ],
                                layout=go.Layout(
                                    barmode='overlay',
                                    title='R/F/M评分分布',
                                    xaxis_title='评分',
                                    yaxis_title='客户数',
                                    height=380  # 图表内部高度
                                )
                            ),
                            style={'height': '400px'}  # 容器高度
                        )
                    ]
                )
            ]
        ),

        # 第四行：销售渠道分布
        html.Div(
            style={'background': 'white', 'padding': '20px', 'border-radius': '8px',
                   'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '30px 0',
                   'height': '400px'},  
            children=[
                html.H3("销售渠道分布", style={'color': '#2c3e50', 'margin-top': 0}),
                dcc.Graph(
                    figure=px.bar(
                        orders.groupby('channel')['revenue'].sum().reset_index(),
                        x='channel',
                        y='revenue',
                        title='各渠道销售收入',
                        labels={'channel': '销售渠道', 'revenue': '销售收入（元）'},
                        color='channel',
                        color_discrete_map={
                            'Online': '#3498db',
                            'Offline': '#e74c3c',
                            'WeChat Mini Program': '#2ecc71',
                            '无数据': '#95a5a6'
                        }
                    ),
                    style={'height': '320px'} 
                )
            ]
        )
    ]
)

# 运行应用（关闭debug的热重载，避免样式异常）
if __name__ == '__main__':

    app.run(debug=False, port=8050)  
