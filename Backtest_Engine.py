import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
# 账户
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from Visualization import BacktestVisualization  # 导入新的可视化类


# 账户类
class Account:
    def __init__(self, initial_cash=100000):
        """初始化账户"""
        self.initial_cash = initial_cash  # 初始资金
        self.cash = initial_cash  # 当前现金
        self.positions = {}  # 持仓情况 {股票代码: 持股数量}
        self.trade_history = []  # 交易历史
        self.total_assets = []  # 每日总资产记录
        self.dates = []  # 日期记录


    def buy(self, date, stock_code, price, amount):
        """买入股票"""
        cost = price * amount
        # 计算手续费（买入佣金万分之三，最低5元）
        commission = max(0.0003 * cost, 5)
        total_cost = cost + commission

        if self.cash >= total_cost:
            self.cash -= total_cost
            if stock_code in self.positions:
                self.positions[stock_code] += amount
            else:
                self.positions[stock_code] = amount

            # 记录交易
            self.trade_history.append({
                'date': date,
                'stock_code': stock_code,
                'action': 'buy',
                'price': price,
                'amount': amount,
                'cost': total_cost
            })
            return True
        return False

    def sell(self, date, stock_code, price, amount):
        """卖出股票"""
        if stock_code not in self.positions or self.positions[stock_code] < amount:
            return False

        revenue = price * amount
        # 计算手续费（卖出佣金万分之三+印花税千分之一，最低5元）
        commission = max(0.0003 * revenue, 5)
        tax = 0.001 * revenue
        total_cost = commission + tax

        self.cash += revenue - total_cost
        self.positions[stock_code] -= amount
        if self.positions[stock_code] == 0:
            del self.positions[stock_code]

        # 记录交易
        self.trade_history.append({
            'date': date,
            'stock_code': stock_code,
            'action': 'sell',
            'price': price,
            'amount': amount,
            'revenue': revenue - total_cost
        })
        return True

    def calculate_total_assets(self, date, stock_prices):
        """计算总资产（现金+持仓市值）"""
        position_value = 0
        for stock_code, amount in self.positions.items():
            if stock_code in stock_prices:
                position_value += stock_prices[stock_code] * amount

        total = self.cash + position_value
        self.total_assets.append(total)
        self.dates.append(date)
        return total

# 回测引擎类
class BacktestEngine:
    def __init__(self, data_handler, strategy_class, initial_cash=100000):
        self.data_handler = data_handler
        self.strategy_class = strategy_class
        self.account = Account(initial_cash)

        stock_data = self.data_handler.get_stock_data()
        # 先获取唯一日期的 Series，再转换为 DatetimeIndex
        unique_dates = stock_data.index.unique()
        self.dates = pd.DatetimeIndex(unique_dates).sort_values()  # 排序后的 DatetimeIndex

        self.benchmark_returns = None
        self.strategy_returns = None

        # 初始化上下文（其余代码不变）
        self.context = {
            'account': self.account,
            'data_handler': data_handler,
            'current_dt': None,
            'portfolio': {
                'available_cash': self.account.cash,
                'positions': self.account.positions
            }
        }

        self.strategy = self.strategy_class(self.context)

    def run(self, start_date=None, end_date=None):
        """运行回测"""
        # 打印原始日期范围
        print(f"原始数据日期范围: {self.dates.min()} 至 {self.dates.max()}")

        # 筛选回测日期范围
        if start_date and end_date:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            mask = (self.dates >= start_date) & (self.dates <= end_date)
            trade_dates = self.dates[mask]
            # 打印筛选后的日期范围
            print(f"筛选后日期范围: {start_date} 至 {end_date}")
            print(f"有效交易日数量: {len(trade_dates)}")
        else:
            trade_dates = self.dates

        # 新增：检查筛选后是否有有效日期
        if len(trade_dates) == 0:
            raise ValueError("没有找到符合条件的交易日期，请检查日期范围是否在数据范围内")

        # 初始化策略
        self.strategy.initialize()

        # 开始回测（后续代码不变）
        print(f"回测开始: {trade_dates[0].strftime('%Y-%m-%d')}")
        print(f"回测结束: {trade_dates[-1].strftime('%Y-%m-%d')}")

        for date in trade_dates:
            self.context['current_dt'] = date
            self.context['portfolio']['available_cash'] = self.account.cash

            # 每日交易前
            self.strategy.before_market_open(date)

            # 每日交易
            self.strategy.market_open(date)

            # 每日交易后
            self.strategy.after_market_close(date)

            # 计算当日资产
            daily_stock_data = self.data_handler.get_single_day_data(date)
            security = self.context['security']

            # 检查目标股票是否在当日数据中
            if security in daily_stock_data:
                stock_price = daily_stock_data[security]
                self.account.calculate_total_assets(date, {security: stock_price})
            else:
                # 如果目标股票不在当日数据中，则使用 NaN 作为价格
                self.account.calculate_total_assets(date, {security: np.nan})

        print("回测完成!")
        self.calculate_returns()

        # 创建可视化实例
        self.visualization = BacktestVisualization(self.account, self.strategy_returns)

        # 显示结果
        self.visualization.plot_results()
        self.visualization.print_performance()

    def calculate_returns(self):
        """计算策略收益率"""
        self.strategy_returns = pd.Series(
            self.account.total_assets, index=self.account.dates
        ).pct_change().fillna(0)


