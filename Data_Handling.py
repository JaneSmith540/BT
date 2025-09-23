# 数据文件路径
file_path = r"C:\Users\chanpi\Desktop\Backtesting\测试用文件\TRD_Dalyr.csv"

import pandas as pd
import os
from datetime import datetime
import numpy as np


class StockData:
    def __init__(self):
        self.Stkcd = None  # 股票代码
        self.Opnprc = None  # 开盘价
        self.Hiprc = None  # 最高价
        self.Loprc = None  # 最低价
        self.Clsprc = None  # 收盘价
        self.Trdsta = None  # 交易状态
        # 1 = 正常交易，2 = ST，3＝*ST，4＝S（2006年10月9日及之后股改未完成），5＝SST，6＝S * ST，7 = G（2006年10月9日之前已完成股改），8 = GST，9 = G * ST，10 = U（2006年10月9日之前股改未完成），11 = UST，12 = U * ST，13 = N，14 = NST，15 = N * ST，16 = PT
        self.LimitDown = None  # 跌停价
        self.LimitUp = None  # 涨停价
        self.Dnshrtrd = None  # 交易量
        self.Dsmvosd = None  # 流通市值


def get_price(security, start_date=None, end_date=None, frequency='daily', fields=None,
              skip_paused=False, count=None, panel=True, fill_paused=True):
    """
    获取历史数据，可查询多个标的多个数据字段，返回数据格式为 DataFrame
    """
    # 数据文件路径
    file_path = r"C:\Users\chanpi\Desktop\Backtesting\测试用文件\TRD_Dalyr.csv"

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")

    # 读取CSV文件，注意处理带引号的字段
    df = pd.read_csv(file_path, dtype=str)  # 先都按字符串读取，避免格式问题

    # 转换数值字段为适当类型
    numeric_fields = ['Opnprc', 'Hiprc', 'Loprc', 'Clsprc', 'Trdsta',
                      'LimitDown', 'LimitUp', 'Dnshrtrd', 'Dsmvosd']
    for field in numeric_fields:
        if field in df.columns:
            # 去除可能存在的引号并转换为数值
            df[field] = df[field].str.replace('"', '').astype(float, errors='ignore')

    # 转换日期列的格式（去除引号）
    if 'Trddt' in df.columns:
        df['Trddt'] = pd.to_datetime(df['Trddt'].str.replace('"', ''))

    # 处理股票代码（去除引号）
    if 'Stkcd' in df.columns:
        df['Stkcd'] = df['Stkcd'].str.replace('"', '')

    # 过滤股票代码
    if isinstance(security, list):
        # 多个股票代码
        securities = [str(s).replace('"', '') for s in security]
        df = df[df['Stkcd'].isin(securities)]
    else:
        # 单个股票代码
        security_str = str(security).replace('"', '')
        df = df[df['Stkcd'] == security_str]

    # 过滤日期范围
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df['Trddt'] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df['Trddt'] <= end_date]

    # 处理停牌数据
    if skip_paused and 'Trdsta' in df.columns:
        # 只保留正常交易的数据（Trdsta == 1）
        df = df[df['Trdsta'] == 1]

    # 选择需要的字段
    available_fields = ['Stkcd', 'Trddt', 'Opnprc', 'Hiprc', 'Loprc', 'Clsprc',
                        'Trdsta', 'LimitDown', 'LimitUp', 'Dnshrtrd', 'Dsmvosd']

    if fields:
        # 检查字段是否有效
        invalid_fields = [f for f in fields if f not in available_fields]
        if invalid_fields:
            raise ValueError(f"无效的字段: {invalid_fields}，可用字段: {available_fields}")

        # 确保保留股票代码和日期
        selected_fields = fields.copy()
        if 'Stkcd' not in selected_fields:
            selected_fields.insert(0, 'Stkcd')
        if 'Trddt' not in selected_fields:
            selected_fields.insert(1, 'Trddt')

        df = df[selected_fields]

    # 按日期排序
    if 'Trddt' in df.columns:
        df = df.sort_values('Trddt')

    # 限制返回的记录数量
    if count and count > 0:
        df = df.tail(count)

    # 如果需要面板格式，设置索引
    if panel and 'Stkcd' in df.columns and 'Trddt' in df.columns:
        df = df.set_index(['Stkcd', 'Trddt'])

    return df


# 在Data_Handling.py中添加以下函数（可放在get_price函数之后）
def get_all_securities(date=None):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")

    # 读取CSV文件
    df = pd.read_csv(file_path, dtype=str)

    # 处理日期列
    if 'Trddt' in df.columns:
        df['Trddt'] = pd.to_datetime(df['Trddt'].str.replace('"', ''))

    # 处理股票代码
    if 'Stkcd' in df.columns:
        df['Stkcd'] = df['Stkcd'].str.replace('"', '').str.zfill(6)  # 统一6位代码格式

    # 按日期筛选
    if date is not None:
        target_date = pd.to_datetime(date)
        df = df[df['Trddt'] == target_date]

    # 去重并返回股票代码列表
    return df['Stkcd'].dropna().unique().tolist()
class DataHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.stock_data = self._load_data()
        self.dates = pd.DatetimeIndex(self.stock_data.index.unique(level=0)).sort_values()

    def get_previous_trading_day(self, current_date):
        """获取当前日期的上一个有效交易日"""
        current_date = pd.to_datetime(current_date)
        # 获取所有小于当前日期的交易日并排序
        previous_days = self.dates[self.dates < current_date]
        if len(previous_days) == 0:
            return None  # 没有上一个交易日
        return previous_days[-1]  # 返回最近的一个交易日

    def _load_data(self):
        """加载并预处理CSV数据"""

        df = pd.read_csv(self.file_path)
        # 转换日期、统一股票代码为字符串（补前导零至6位）
        df['Trddt'] = pd.to_datetime(df['Trddt'], errors='coerce')  # 强制转换，错误值设为NaT
        # 新增：检查日期转换情况
        invalid_dates = df['Trddt'].isna().sum()

        df = df.dropna(subset=['Trddt'])  # 删除无效日期记录

        df['Stkcd'] = df['Stkcd'].astype(str).str.zfill(6)
        df.rename(columns={'Clsprc': 'close', 'Opnprc': 'open', 'Hiprc': 'high', 'Loprc': 'low'}, inplace=True)
        return df.set_index(['Trddt', 'Stkcd'])
    def get_stock_data(self):
        """回测引擎需要的：获取所有股票数据（用于提取日期列表）"""
        df = self.stock_data.reset_index()  # 此时列：Trddt, Stkcd, close, open...
        return df.set_index('Trddt')  # 单索引：Trddt（日期）
    def get_single_day_data(self, date):
        """回测引擎需要的：获取某一天所有股票的收盘价"""
        date = pd.to_datetime(date)
        if date not in self.stock_data.index.levels[0]:
            return pd.Series([np.nan], index=[None])  # 无数据日期返回NaN
        day_data = self.stock_data.loc[date]
        return day_data['close']  # 返回 Series：index=股票代码，value=收盘价


