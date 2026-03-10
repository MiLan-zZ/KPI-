import pandas as pd
from sqlalchemy import create_engine

"""
pd.read_sql(): Pandas函数，执行SQL查询并返回DataFrame
'SELECT * FROM customers': SQL查询语句，获取customers表的所有数据
con=conn: 指定数据库连接
customers = ...: 将查询结果存储到变量customers中
"""

# 获取MySql连接
def create_engine_connection():
    engine = create_engine('mysql+pymysql://root:root@localhost:3306/retail_kpi?charset=utf8')
    return engine
# 从mysql加载数据的完整函数
def load_data_from_mysql():
    engine = create_engine_connection()
    try:
        customers = pd.read_sql("select * from retail_customers", con=engine)
        products = pd.read_sql('select * from retail_products', con=engine)
        orders = pd.read_sql('select * from retail_orders', con=engine)
        inventory = pd.read_sql('SELECT * FROM retail_inventory', con=engine)
        campaigns = pd.read_sql('SELECT * FROM retail_campaigns', con=engine)
        # print(f"客户表{len(customers)}行")
        # print(f"产品表{len(products)}行")
        # print(f"订单表{len(orders)}行")
        # print(f"库存表{len(inventory)}行")
        # print(f"活动表{len(campaigns)}行")
        return customers, products, orders, inventory, campaigns
    except Exception as e:
        print(f"加载失败：{e}")
        return None, None, None, None, None

# latest_5 = pd.read_sql("""
#     SELECT order_id, order_date
#     FROM retail_orders
#     ORDER BY order_date DESC
#     LIMIT 5;
# """, create_engine_connection())
#
# print(latest_5)

# 执行数据加载
if __name__ == '__main__':
    customers, products, orders, inventory, campaigns = load_data_from_mysql()

