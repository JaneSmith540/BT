import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class BacktestVisualization:
    def __init__(self, account, strategy_returns=None):
        self.account = account
        self.strategy_returns = strategy_returns

    def calculate_returns(self):
        """计算策略收益率"""
        if self.strategy_returns is None:
            self.strategy_returns = pd.Series(
                self.account.total_assets, index=self.account.dates
            ).pct_change().fillna(0)
        return self.strategy_returns

    def plot_results(self):
        """绘制回测结果"""
        # 计算收益率
        returns = self.calculate_returns()

        plt.figure(figsize=(12, 8))

        # 绘制资产曲线
        plt.subplot(2, 1, 1)
        plt.plot(self.account.dates, self.account.total_assets, label='Total Assets')
        plt.axhline(y=self.account.initial_cash, color='r', linestyle='--', label='Initial Capital')
        plt.title('Capital Curve')
        plt.legend()
        plt.grid(True)

        # 绘制收益率曲线
        plt.subplot(2, 1, 2)
        cumulative_returns = (1 + returns).cumprod() - 1
        plt.plot(self.account.dates, cumulative_returns, label='Strategy Cumulative Return')
        plt.title('Cumulative Returns')
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.show()

    def print_performance(self):
        """打印绩效指标"""
        # 计算总收益率
        total_return = (self.account.total_assets[-1] / self.account.initial_cash - 1) * 100

        # 计算收益率序列
        returns = self.calculate_returns()

        # 计算年化收益率
        days = (self.account.dates[-1] - self.account.dates[0]).days
        annualized_return = (1 + total_return / 100) ** (365 / days) - 1 if days > 0 else 0

        # 计算夏普比率 (假设无风险利率为0)
        sharpe_ratio = np.sqrt(252) * (returns.mean() / (returns.std() + 1e-8))

        # 计算最大回撤
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min() * 100

        print(f"\n绩效指标:")
        print(f"总收益率: {total_return:.2f}%")
        print(f"年化收益率: {annualized_return * 100:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"交易次数: {len(self.account.trade_history)}")

        # 如果有交易历史，打印交易统计
        if self.account.trade_history:
            trades = pd.DataFrame(self.account.trade_history)
            buy_trades = trades[trades['action'] == 'buy']
            sell_trades = trades[trades['action'] == 'sell']

            print(f"\n交易统计:")
            print(f"买入次数: {len(buy_trades)}")
            print(f"卖出次数: {len(sell_trades)}")
