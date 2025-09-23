from Utilities import log
import pandas as pd
from Data_Handling import get_price, get_all_securities  # 导入所需函数


class MA5Strategy:
    def __init__(self, context):
        self.context = context
        self.g = type('Global', (object,), {})  # 模拟全局变量g
        # 存储所有股票的前一日价格（键：股票代码，值：前一日收盘价）
        self.g.previous_prices = {}
        # 存储当前关注的股票池
        self.g.stock_pool = []

    def initialize(self):
        """初始化策略"""
        log.info('初始函数开始运行且全局只运行一次')
        # 初始化时不指定固定股票，改为动态获取
        log.info("策略初始化完成，将在每日开盘前获取全市场股票列表")

    def before_market_open(self, date):
        """开盘前运行：获取当日所有可交易股票"""
        log.info(f'函数运行时间(before_market_open)：{str(date)}')

        # 获取当日所有可交易股票
        self.g.stock_pool = get_all_securities(date=date)
        log.info(f"当日可交易股票数量: {len(self.g.stock_pool)}")

        # 为新出现的股票初始化前一日价格
        for stock in self.g.stock_pool:
            if stock not in self.g.previous_prices:
                self.g.previous_prices[stock] = None

    def market_open(self, date):
        """开盘时运行：遍历所有股票执行交易逻辑"""
        log.info(f'函数运行时间(market_open)：{str(date)}')
        account = self.context['account']
        cash = self.context['portfolio']['available_cash']

        # 遍历当日所有可交易股票
        for stock in self.g.stock_pool:
            # 获取当前股票的最新价格
            current_data = get_price(stock, count=1, fields=['Clsprc'], end_date=date)
            if len(current_data) == 0:
                log.info(f'股票 {stock} 无当前价格数据，跳过')
                continue

            current_price = current_data['Clsprc'].iloc[-1]
            previous_price = self.g.previous_prices[stock]

            # 调试信息
            log.info(f"股票 {stock} - 当前价格: {current_price}, 前一天价格: {previous_price}")

            # 执行交易逻辑
            if previous_price is not None:
                # 今日股价高于昨日则买入
                if current_price > previous_price:
                    if cash > 0:
                        # 计算可买数量（考虑手续费）
                        buy_amount = self.calculate_buy_amount(cash, current_price)
                        if buy_amount > 0:
                            success = account.buy(date, stock, current_price, buy_amount)
                            if success:
                                log.info(f"🎯 买入 {stock}，价格：{current_price:.2f}，数量：{buy_amount}")
                                # 更新可用现金
                                cash = account.cash  # 实时更新现金，避免重复计算
                            else:
                                log.info(f"买入 {stock} 失败")
                    else:
                        log.info(f"股票 {stock} 触发买入信号，但现金不足")

                # 今日股价不高于昨日则卖出
                else:
                    # 检查是否有持仓
                    if stock in account.positions and account.positions[stock] > 0:
                        sell_amount = account.positions[stock]  # 卖出全部持仓
                        success = account.sell(date, stock, current_price, sell_amount)
                        if success:
                            log.info(f"📉 卖出 {stock}，价格：{current_price:.2f}，数量：{sell_amount}")
                            cash = account.cash  # 实时更新现金
                        else:
                            log.info(f"卖出 {stock} 失败")
                    else:
                        log.info(f"股票 {stock} 触发卖出信号，但无持仓")

            # 更新前一日价格
            self.g.previous_prices[stock] = current_price

        # 更新上下文现金信息
        self.context['portfolio']['available_cash'] = cash

    def calculate_buy_amount(self, cash, price):
        """计算可买入数量（考虑手续费）"""
        # 估算手续费（买入佣金万分之三，最低5元）
        max_amount = int(cash / price)
        if max_amount == 0:
            return 0

        # 计算总成本（含手续费）
        cost = price * max_amount
        commission = max(0.0003 * cost, 5)
        total_cost = cost + commission

        # 确保总成本不超过可用现金
        while total_cost > cash and max_amount > 0:
            max_amount -= 1
            cost = price * max_amount
            commission = max(0.0003 * cost, 5)
            total_cost = cost + commission

        return max_amount

    def after_market_close(self, date):
        """收盘后运行：打印账户状态"""
        log.info(f'函数运行时间(after_market_close)：{str(date)}')

        account = self.context['account']
        cash = account.cash
        total_assets = cash

        # 计算持仓市值
        position_value = 0
        for stock, amount in account.positions.items():
            current_data = get_price(stock, count=1, fields=['Clsprc'], end_date=date)
            if len(current_data) > 0:
                current_price = current_data['Clsprc'].iloc[-1]
                stock_value = current_price * amount
                position_value += stock_value
                log.info(f"持仓: {stock} - 数量: {amount}, 价格: {current_price:.2f}, 市值: {stock_value:.2f}")

        total_assets += position_value
        log.info(f"账户状态 - 现金: {cash:.2f}, 总资产: {total_assets:.2f}")

        # 打印当日交易记录
        today_trades = [trade for trade in account.trade_history
                        if pd.to_datetime(trade['date']).date() == date.date()]
        if today_trades:
            for trade in today_trades:
                log.info(f'当日成交: {trade}')
        else:
            log.info('当日无成交记录')

        log.info('一天结束\n')