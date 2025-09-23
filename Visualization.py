from Performance_Analysis import PerformanceAnalysis


class BacktestVisualization:
    def __init__(self, account, strategy_returns=None):
        self.account = account
        self.strategy_returns = strategy_returns
        # 初始化性能分析模块（复用计算结果）
        self.performance = PerformanceAnalysis(account)

    def calculate_returns(self):
        """复用性能分析的收益率计算"""
        if self.strategy_returns is None:
            self.strategy_returns = self.performance.strategy_returns
        return self.strategy_returns

    def print_performance(self):
        """通过性能分析模块获取所有指标"""
        print(f"\n绩效指标:")
        print(f"总收益率: {self.performance.get_total_return():.2f}%")
        print(f"年化收益率: {self.performance.get_annualized_return() * 100:.2f}%")
        print(f"夏普比率: {self.performance.get_sharpe_ratio():.2f}")
        print(f"最大回撤: {self.performance.get_max_drawdown():.2f}%")
        print(f"交易次数: {self.performance.get_trade_count()}")

        # 交易统计
        buy_count, sell_count = self.performance.get_buy_sell_count()
        print(f"\n交易统计:")
        print(f"买入次数: {buy_count}")
        print(f"卖出次数: {sell_count}")
        print(f"平均每次卖出收益: {self.performance.get_avg_sell_profit():.2f}元")