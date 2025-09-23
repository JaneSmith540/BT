from Utilities import log
import pandas as pd


class MA5Strategy:
    def __init__(self, context):
        self.context = context
        self.g = type('Global', (object,), {})  # 模拟全局变量g

    def initialize(self):
        """初始化策略"""
        log.info('初始函数开始运行且全局只运行一次')
        self.g.security = '000001'  # 使用数字格式的股票代码
        self.context['security'] = self.g.security
        self.g.previous_price = None  # 用于存储前一天的收盘价

        # 移除文件路径检查（因为数据文件路径不正确）
        log.info("策略初始化完成")

    def before_market_open(self, date):
        """开盘前运行"""
        log.info(f'函数运行时间(before_market_open)：{str(date)}')

    def market_open(self, date):
        """开盘时运行"""
        log.info(f'函数运行时间(market_open)：{str(date)}')
        security = self.g.security

        # 调用DataHandler的get_price获取当前价格
        from Data_Handling import get_price
        current_data = get_price(security, count=1, fields=['Clsprc'], end_date=date)

        if len(current_data) == 0:
            log.info(f'无法获取当前价格数据，跳过交易：{date}')
            return

        # 获取当前价格
        current_price = current_data['Clsprc'].iloc[-1]
        cash = self.context['portfolio']['available_cash']
        account = self.context['account']

        # 调试信息
        log.info(f"当前价格: {current_price}, 前一天价格: {self.g.previous_price}")
        log.info(f"可用现金: {cash}")

        # 如果有前一天的价格数据，执行交易逻辑
        if self.g.previous_price is not None:
            # 今日股价比昨日高则买入
            if current_price > self.g.previous_price:
                # 如果有现金，则买入
                if cash > 0:
                    # 计算可买数量（考虑手续费）
                    buy_amount = self.calculate_buy_amount(cash, current_price)
                    if buy_amount > 0:
                        success = account.buy(date, security, current_price, buy_amount)
                        if success:
                            log.info(f"🎯 买入信号触发！买入 {security}，价格：{current_price:.2f}，数量：{buy_amount}")
                            # 更新现金信息
                            self.context['portfolio']['available_cash'] = account.cash
                        else:
                            log.info(f"买入失败，可能由于现金不足")
                    else:
                        log.info(f"计算出的买入数量为0，跳过买入")
                else:
                    log.info(f"今日价格高于昨日，但现金不足，无法买入")

            # 否则卖出（今日股价不高于昨日）
            else:
                # 检查是否有持仓
                has_position = security in account.positions and account.positions[security] > 0
                log.info(
                    f"检查持仓: {security} 在持仓中: {security in account.positions}, 持仓数量: {account.positions.get(security, 0)}")

                if has_position:
                    sell_amount = account.positions[security]  # 卖出全部持仓
                    success = account.sell(date, security, current_price, sell_amount)
                    if success:
                        log.info(f"📉 卖出信号触发！卖出 {security}，价格：{current_price:.2f}，数量：{sell_amount}")
                    else:
                        log.info(f"卖出失败")
                else:
                    log.info(f"今日价格不高于昨日，但无持仓可卖，跳过交易")
        else:
            log.info(f'没有前一天价格数据，跳过交易：{date}')

        # 更新前一天价格为今天的价格（供明天使用）
        self.g.previous_price = current_price

    def calculate_buy_amount(self, cash, price):
        """计算可买入数量（考虑手续费）"""
        # 估算手续费（买入佣金万分之三，最低5元）
        # 先计算不考虑手续法的最大数量
        max_amount = int(cash / price)

        # 如果最大数量为0，直接返回0
        if max_amount == 0:
            return 0

        # 计算手续费
        cost = price * max_amount
        commission = max(0.0003 * cost, 5)
        total_cost = cost + commission

        # 如果总成本超过现金，减少买入数量
        while total_cost > cash and max_amount > 0:
            max_amount -= 1
            cost = price * max_amount
            commission = max(0.0003 * cost, 5)
            total_cost = cost + commission

        return max_amount

    def after_market_close(self, date):
        """收盘后运行"""
        log.info(f'函数运行时间(after_market_close)：{str(date)}')

        # 打印账户状态
        account = self.context['account']
        cash = account.cash
        total_assets = cash

        # 计算持仓市值
        if hasattr(self.g, 'security') and self.g.security in account.positions:
            from Data_Handling import get_price
            current_data = get_price(self.g.security, count=1, fields=['Clsprc'], end_date=date)
            if len(current_data) > 0:
                current_price = current_data['Clsprc'].iloc[-1]
                position_value = current_price * account.positions[self.g.security]
                total_assets = cash + position_value
                log.info(
                    f"持仓情况: {self.g.security} - 数量: {account.positions[self.g.security]}, 当前价格: {current_price:.2f}, 持仓市值: {position_value:.2f}")

        log.info(f"账户状态 - 现金: {cash:.2f}, 总资产: {total_assets:.2f}")

        # 打印交易历史
        if account.trade_history:
            # 只打印当天的交易记录
            today_trades = [trade for trade in account.trade_history
                            if pd.to_datetime(trade['date']).date() == date.date()]
            for trade in today_trades:
                log.info(f'当日成交记录：{trade}')
        else:
            log.info('当日无成交记录')

        log.info('一天结束\n')