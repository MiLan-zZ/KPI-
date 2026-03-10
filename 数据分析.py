import numpy as np
import pandas as pd
from 数据加载 import *
import pymysql
from datetime import datetime


# --------------------- 原有RFM分析函数保留 ---------------------
def rfm_analysis(orders):
    # RFM分析代码（原有代码不变）
    orders_df = orders  # 真正的订单表
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    date_20251108 = pd.to_datetime('2025-11-08')

    # R----------------: 截至今天最近购买的时间差
    recent = (orders_df.groupby('customer_id')['order_date'].max().reset_index(name='recent_date'))
    recent['R_days'] = (date_20251108 - recent['recent_date']).dt.days

    # F--------营销活动时间段交易次数---------:
    # 营销活动特定时间:2025-2-23___2025-5-23
    campaigns_start_time = pd.to_datetime('2025-2-23')
    campaigns_end_time = pd.to_datetime('2025-5-23')
    # 营销活动三个月的订单
    campaigns_time = orders[(orders['order_date'] >= campaigns_start_time) &
                            (orders['order_date'] <= campaigns_end_time)]

    frequency_with_data = campaigns_time.groupby('customer_id')['order_id'].count().reset_index(name='Frequency')
    all_frequency = orders_df.groupby('customer_id')['order_id'].count().reset_index(name='all_frequency')
    frequency = all_frequency.merge(frequency_with_data, how='left', on='customer_id')
    frequency['Frequency'] = frequency['Frequency'].fillna(0).astype(int)

    # M--------营销活动期间消费额--------:
    all_time_monetary = orders.assign(总消费额=orders['quantity'] * orders['selling_price'])
    all_monetary = all_time_monetary.groupby('customer_id')['总消费额'].sum().reset_index(name='all_time_monetary')

    campaigns_time = campaigns_time.assign(
        半年消费额=campaigns_time['quantity'] * campaigns_time['selling_price'])

    monetary_with_data = campaigns_time.groupby('customer_id')['半年消费额'].sum().reset_index(name='Monetary')
    monetary = all_monetary.merge(monetary_with_data, how='left', on='customer_id')
    monetary['Monetary'] = monetary['Monetary'].fillna(0)

    # RFM----------------:
    customer_new_id = orders_df['customer_id'].sort_values().drop_duplicates().reset_index(drop=True)
    RFM = pd.DataFrame({'客户': customer_new_id,
                        'R': recent['R_days'],
                        'F': frequency['Frequency'],
                        'M': monetary['Monetary']})

    def r_score(x):
        if x <= 30:
            return 5
        elif x <= 90:
            return 4
        elif x <= 180:
            return 3
        elif x <= 240:
            return 2
        else:
            return 1

    def f_score(x):
        if x >= 7:
            return 5
        elif x >= 5:
            return 4
        elif x >= 3:
            return 3
        elif x >= 1:
            return 2
        else:
            return 1

    def m_score(x):
        if x >= 6000:
            return 5
        elif x >= 3000:
            return 4
        elif x >= 1500:
            return 3
        elif x >= 500:
            return 2
        else:
            return 1

    recent['R_score'] = recent['R_days'].apply(r_score)
    frequency['F_score'] = frequency['Frequency'].apply(f_score)
    monetary['M_score'] = monetary['Monetary'].apply(m_score)

    rfm_scores = recent[['customer_id', 'R_score']].merge(
        frequency[['customer_id', 'F_score']], on='customer_id', how='left').merge(
        monetary[['customer_id', 'M_score']], on='customer_id', how='left')

    rfm_scores['rfm'] = (rfm_scores['R_score'].astype(str) +
                         rfm_scores['F_score'].astype(str) +
                         rfm_scores['M_score'].astype(str))

    # 将rfm列合并到campaigns_time（按customer_id关联）
    campaigns_time = campaigns_time.merge(
        rfm_scores[['customer_id', 'rfm']], on='customer_id', how='left'
    )

    z_rfm = pd.DataFrame({'客户ID': rfm_scores['customer_id'],
                          'R(天)': recent['R_days'],
                          'F(次)': frequency['Frequency'],
                          'M(元)': monetary['Monetary'],
                          'R分': rfm_scores['R_score'],
                          'F分': rfm_scores['F_score'],
                          'M分': rfm_scores['M_score'],
                          'RFM总分': rfm_scores['rfm']})

    return z_rfm, rfm_scores  # 返回RFM结果供Dash使用


# --------------------- 基础交易指标（GMV、销售收入、净利润等） ---------------------
def calculate_basic_trade_metrics(orders):
    """计算GMV、销售收入、净利润、利润率、客单价"""
    orders['order_date'] = pd.to_datetime(orders['order_date'])

    # GMV（成交总额：未扣除优惠券的总金额）
    orders['gmv_single'] = orders['quantity'] * orders['selling_price']
    gmv_total = orders['gmv_single'].sum()

    #  销售收入（扣除优惠券后的实际收入）
    revenue_total = orders['revenue'].sum()

    # 净利润（造数中已计算单订单利润：profit = revenue - quantity*cost_price）
    profit_total = orders['profit'].sum()

    #  利润率（净利润/销售收入 * 100%）
    profit_margin = (profit_total / revenue_total * 100) if revenue_total != 0 else 0

    # 客单价（销售收入 / 下单用户数）
    pay_users = orders['customer_id'].nunique()
    avg_order_value = revenue_total / pay_users if pay_users != 0 else 0

    metrics = {
        'GMV(元)': round(gmv_total, 2),
        '销售收入(元)': round(revenue_total, 2),
        '净利润(元)': round(profit_total, 2),
        '利润率(%)': round(profit_margin, 2),
        '客单价(元)': round(avg_order_value, 2),
        '下单用户数': pay_users
    }
    return metrics


# --------------------- 活动ROI & CAC计算 ---------------------
def calculate_campaign_roi_cac(orders, campaigns, customers):
    """计算活动ROI（增量利润/活动成本）、CAC（用户获取成本）"""
    # 数据预处理
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    campaigns['start_date'] = pd.to_datetime(campaigns['start_date'])
    campaigns['end_date'] = pd.to_datetime(campaigns['end_date'])
    customers['registration_date'] = pd.to_datetime(customers['registration_date'])

    # 筛选活动期间订单
    campaign_orders = filter_orders_by_campaign(orders, campaigns)

    # 识别新增客户（活动期间首次消费的客户）
    # 所有订单的用户首次消费时间
    first_order_time = orders.groupby('customer_id')['order_date'].min().reset_index(name='first_order')
    # 活动时间范围
    all_campaign_start = campaigns['start_date'].min()
    all_campaign_end = campaigns['end_date'].max()
    # 新增客户：首次消费在活动期间
    new_customers = first_order_time[
        (first_order_time['first_order'] >= all_campaign_start) &
        (first_order_time['first_order'] <= all_campaign_end)
        ]['customer_id'].tolist()

    #  活动增量利润（仅新增客户在活动期间产生的利润）
    new_customer_campaign_orders = campaign_orders[campaign_orders['customer_id'].isin(new_customers)]
    incremental_profit = new_customer_campaign_orders['profit'].sum()

    #  活动总成本（所有活动预算总和）
    total_campaign_cost = campaigns['budget'].sum()

    #  活动ROI
    roi = (incremental_profit / total_campaign_cost) if total_campaign_cost != 0 else 0

    #  CAC（用户获取成本 = 活动总成本 / 新增客户数）
    new_customer_count = len(new_customers)
    cac = (total_campaign_cost / new_customer_count) if new_customer_count != 0 else 0

    metrics = {
        '活动总成本(元)': round(total_campaign_cost, 2),
        '活动新增客户数': new_customer_count,
        '活动增量利润(元)': round(incremental_profit, 2),
        '活动ROI(倍)': round(roi, 2),
        'CAC(元/人)': round(cac, 2)
    }
    return metrics


# --------------------- 库存周转率计算 ---------------------
def calculate_inventory_turnover(orders, inventory, products):
    """计算库存周转率 = 销售成本(COGS) / 平均库存价值"""
    #  计算销售成本（COGS：已售商品的进货成本总和）
    orders['cogs_single'] = orders['quantity'] * orders['cost_price']
    total_cogs = orders['cogs_single'].sum()

    #  计算平均库存价值
    # 库存表关联商品成本价
    inventory['last_restock_date'] = pd.to_datetime(inventory['last_restock_date'])
    inventory_with_cost = inventory.merge(
        products[['product_id', 'cost_price']],
        on='product_id',
        how='left'
    )
    # 库存价值 = 库存数量 * 进货成本
    inventory_with_cost['stock_value'] = inventory_with_cost['current_stock'] * inventory_with_cost['cost_price']
    # 平均库存价值（简化：用当前库存价值作为平均，实际应取期初+期末/2）
    avg_stock_value = inventory_with_cost['stock_value'].mean()

    #  库存周转率
    turnover_rate = (total_cogs / avg_stock_value) if avg_stock_value != 0 else 0

    metrics = {
        '销售成本(元)': round(total_cogs, 2),
        '平均库存价值(元)': round(avg_stock_value, 2),
        '库存周转率(次)': round(turnover_rate, 2)
    }
    return metrics


# --------------------- 库龄结构计算 ---------------------
def calculate_inventory_age_structure(inventory):
    """计算库龄结构：<30天、30-90天、>90天的库存数量占比"""
    # 数据预处理
    inventory['last_restock_date'] = pd.to_datetime(inventory['last_restock_date'])
    current_date = datetime.now()
    # 计算库龄（天）
    inventory['age_days'] = (current_date - inventory['last_restock_date']).dt.days

    # 分类统计库存数量
    age_less_30 = inventory[inventory['age_days'] < 30]['current_stock'].sum()
    age_30_90 = inventory[(inventory['age_days'] >= 30) & (inventory['age_days'] <= 90)]['current_stock'].sum()
    age_more_90 = inventory[inventory['age_days'] > 90]['current_stock'].sum()

    # 总库存
    total_stock = age_less_30 + age_30_90 + age_more_90
    # 占比
    ratio_less_30 = (age_less_30 / total_stock * 100) if total_stock != 0 else 0
    ratio_30_90 = (age_30_90 / total_stock * 100) if total_stock != 0 else 0
    ratio_more_90 = (age_more_90 / total_stock * 100) if total_stock != 0 else 0

    structure = {
        '库龄<30天(数量)': age_less_30,
        '库龄30-90天(数量)': age_30_90,
        '库龄>90天(数量)': age_more_90,
        '库龄<30天占比(%)': round(ratio_less_30, 2),
        '库龄30-90天占比(%)': round(ratio_30_90, 2),
        '库龄>90天占比(%)': round(ratio_more_90, 2)
    }
    return structure


# --------------------- 原有函数保留 ---------------------
def filter_orders_by_campaign(orders, campaigns):
    campaign_orders = pd.DataFrame()
    for _, campaign in campaigns.iterrows():
        mask = ((orders['order_date'] >= campaign['start_date']) & (orders['order_date'] <= campaign['end_date']))
        temp_orders = orders[mask].copy()
        temp_orders['campaign_id'] = campaign['campaign_id']
        campaign_orders = pd.concat([campaign_orders, temp_orders], ignore_index=True)
    return campaign_orders


# --------------------- 批量计算所有指标 ---------------------
def calculate_all_metrics():
    """一键计算所有KPI指标"""
    # 加载数据
    customers, products, orders, inventory, campaigns = load_data_from_mysql()
    if orders is None:
        print("数据加载失败，无法计算指标")
        return None

    # 计算各维度指标
    rfm_result, rfm_scores = rfm_analysis(orders)
    basic_trade_metrics = calculate_basic_trade_metrics(orders)
    campaign_metrics = calculate_campaign_roi_cac(orders, campaigns, customers)
    inventory_turnover_metrics = calculate_inventory_turnover(orders, inventory, products)
    inventory_age_metrics = calculate_inventory_age_structure(inventory)

    # 汇总所有指标
    all_metrics = {
        '基础交易指标': basic_trade_metrics,
        '活动ROI&CAC': campaign_metrics,
        '库存周转率': inventory_turnover_metrics,
        '库龄结构': inventory_age_metrics
    }

    return all_metrics, rfm_result, orders, inventory, campaigns


# 测试代码
if __name__ == '__main__':
    all_metrics, rfm_result, _, _, _ = calculate_all_metrics()
    if all_metrics:
        print("=== 全渠道零售KPI指标汇总 ===")
        for category, metrics in all_metrics.items():
            print(f"\n【{category}】")
            for k, v in metrics.items():
                print(f"{k}: {v}")
        print(f"\n【RFM分析结果（前5行）】")

        print(rfm_result.head())
