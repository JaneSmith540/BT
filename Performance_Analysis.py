import pandas as pd
import numpy as np


class PerformanceAnalysis:
    def __init__(self, account):
        self.account = account
        self.strategy_returns = None  # 策略日收益率序列
        self.cumulative_returns = None  # 累计收益率序列

        # 初始化时计算基础收益率
        self.calculate_returns()
        self.calculate_cumulative_returns()

    def calculate_returns(self):
        """计算策略日收益率（从账户总资产推导）"""
        if len(self.account.total_assets) == 0:
            raise ValueError("没有可用的资产数据用于计算收益率")

        # 从账户总资产和日期生成收益率序列
        self.strategy_returns = pd.Series(
            self.account.total_assets,
            index=self.account.dates
        ).pct_change().fillna(0)  # 首日收益率为0
        return self.strategy_returns

    def calculate_cumulative_returns(self):
        """计算累计收益率"""
        if self.strategy_returns is None:
            self.calculate_returns()
        self.cumulative_returns = (1 + self.strategy_returns).cumprod() - 1
        return self.cumulative_returns

    def get_total_return(self):
        """计算总收益率"""
        if len(self.account.total_assets) < 2:
            return 0.0
        return (self.account.total_assets[-1] / self.account.initial_cash - 1) * 100

    def get_annualized_return(self):
        """计算年化收益率"""
        if len(self.account.dates) < 2:
            return 0.0
        days = (self.account.dates[-1] - self.account.dates[0]).days
        if days == 0:
            return 0.0
        total_return = self.get_total_return() / 100  # 转换为小数
        return (1 + total_return) ** (365 / days) - 1

    def get_sharpe_ratio(self, risk_free_rate=0):
        """计算夏普比率（默认无风险利率为0）"""
        if self.strategy_returns is None:
            self.calculate_returns()
        excess_returns = self.strategy_returns - risk_free_rate / 252  # 日均无风险利率
        return np.sqrt(252) * (excess_returns.mean() / (excess_returns.std() + 1e-8))

    def get_max_drawdown(self):
        """计算最大回撤"""
        if self.cumulative_returns is None:
            self.calculate_cumulative_returns()
        peak = self.cumulative_returns.expanding().max()
        drawdown = (self.cumulative_returns - peak) / peak
        return drawdown.min() * 100  # 转换为百分比

    def get_trade_count(self):
        """获取总交易次数"""
        return len(self.account.trade_history)

    def get_buy_sell_count(self):
        """获取买入/卖出次数"""
        if not self.account.trade_history:
            return 0, 0
        trades = pd.DataFrame(self.account.trade_history)
        buy_count = len(trades[trades['action'] == 'buy'])
        sell_count = len(trades[trades['action'] == 'sell'])
        return buy_count, sell_count

    def get_avg_sell_profit(self):
        """计算平均每次卖出收益"""
        if not self.account.trade_history:
            return 0.0
        trades = pd.DataFrame(self.account.trade_history)
        sell_trades = trades[trades['action'] == 'sell']
        if sell_trades.empty:
            return 0.0
        # 收益 = 卖出收入 - 买入成本（需匹配对应的买入记录，此处简化为卖出收入直接计算）
        return (sell_trades['revenue']).mean()