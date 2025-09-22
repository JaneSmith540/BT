from Utilities import log
import pandas as pd


class MA5Strategy:
    def __init__(self, context):
        self.context = context
        self.g = type('Global', (object,), {})  # 模拟全局变量g（替代原策略的g.security）

    def initialize(self):
        """初始化策略（对应原策略的initialize函数）"""
        log.info('初始函数开始运行且全局只运行一次')

        # 根据数据文件的格式，股票代码应该是数字格式（不带后缀）
        self.g.security = '000001'  # 使用数字格式的股票代码
        self.context['security'] = self.g.security
        self.g.previous_price = None  # 用于存储前一天的收盘价

        # 测试数据获取功能
        from Data_Handling import get_price
        # 首先，我们检查数据文件中的日期范围
        # 读取整个数据文件（不过滤日期和股票代码）
        import os
        file_path = "path/to/your/data/file.csv"  # 替换为实际的数据文件路径
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['Trddt'] = pd.to_datetime(df['Trddt'])
            log.info(f"数据文件日期范围: {df['Trddt'].min()} 至 {df['Trddt'].max()}")
            log.info(f"数据文件中的股票代码: {df['Stkcd'].unique()}")
        else:
            log.error(f"数据文件不存在: {file_path}")
            return

        test_data = get_price(self.g.security, count=5, fields=['Clsprc'])
        log.info(f"测试数据获取结果: {len(test_data)} 条记录")
        if len(test_data) > 0:
            log.info(f"测试数据示例: {test_data.head()}")

    def before_market_open(self, date):
        """开盘前运行（对应原策略的before_market_open函数）"""
        log.info(f'函数运行时间(before_market_open)：{str(date.time())}')

    def market_open(self, date):
        """开盘时运行（对应原策略的market_open函数）"""
        log.info(f'函数运行时间(market_open)：{str(date.time())}')
        security = self.g.security

        # 调用DataHandler的get_price获取当前价格
        from Data_Handling import get_price
        # 使用正确的日期格式
        current_data = get_price(security, count=1, fields=['Clsprc'], end_date=date)

        if len(current_data) == 0:
            log.info(f'无法获取当前价格数据，跳过交易：{date}')

            # 尝试获取任何可用的数据来诊断问题
            all_data = get_price(security, count=10, fields=['Clsprc'])
            log.info(f"所有可用数据: {all_data}")
            return

        # 获取当前价格
        current_price = current_data['Clsprc'].iloc[-1]
        cash = self.context['portfolio']['available_cash']
        account = self.context['account']

        # 调试信息：打印当前价格和前一天价格
        log.info(f"当前价格: {current_price}, 前一天价格: {self.g.previous_price}")

        # 如果有前一天的价格数据，执行交易逻辑
        if self.g.previous_price is not None:
            # 买入逻辑：今日股价高于昨日股价
            if (current_price > self.g.previous_price) and (cash > 0):
                # 计算可买数量（总现金 / 股价，取整数）
                buy_amount = int(cash / current_price)
                if buy_amount > 0:
                    success = account.buy(date, security, current_price, buy_amount)
                    if success:
                        log.info(f"今日价格高于昨日，买入 {security}，价格：{current_price:.2f}，数量：{buy_amount}")

            # 卖出逻辑：今日股价不高于昨日股价且有持仓
            elif (current_price <= self.g.previous_price) and (security in account.positions):
                sell_amount = account.positions[security]  # 卖出全部持仓
                success = account.sell(date, security, current_price, sell_amount)
                if success:
                    log.info(f"今日价格不高于昨日，卖出 {security}，价格：{current_price:.2f}，数量：{sell_amount}")
            else:
                log.info(f'未触发交易，跳过交易：{date}')
        else:
            log.info(f'没有前一天价格数据，跳过交易：{date}')

        # 更新前一天价格为今天的价格（供明天使用）
        self.g.previous_price = current_price

    def after_market_close(self, date):
        """收盘后运行（对应原策略的after_market_close函数）"""
        log.info(f'函数运行时间(after_market_close)：{str(date.time())}')
        # 打印交易历史（最近一笔，或全部）
        account = self.context['account']
        if account.trade_history:
            # 只打印当天的交易记录
            today_trades = [trade for trade in account.trade_history
                            if pd.to_datetime(trade['date']).date() == date.date()]
            for trade in today_trades:
                log.info(f'当日成交记录：{trade}')
        log.info('一天结束\n')