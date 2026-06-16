"""
数据分析服务层
CSV/Excel 文件解析、统计计算、图表生成
"""
import os
import uuid
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm

logger = logging.getLogger(__name__)

# 设置中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 图表保存目录
CHARTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)


class DataAnalyzer:
    """数据分析器"""

    ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'xlsm'}

    @staticmethod
    def allowed_file(filename: str) -> bool:
        """检查文件扩展名是否支持"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in DataAnalyzer.ALLOWED_EXTENSIONS

    @staticmethod
    def read_file(filepath: str, filename: str) -> pd.DataFrame:
        """读取 CSV 或 Excel 文件为 DataFrame"""
        ext = filename.rsplit('.', 1)[1].lower()
        if ext == 'csv':
            return pd.read_csv(filepath, encoding='utf-8-sig')
        else:
            return pd.read_excel(filepath, engine='openpyxl')

    @staticmethod
    def get_basic_info(df: pd.DataFrame) -> dict:
        """获取数据基本信息"""
        return {
            'shape': list(df.shape),  # [rows, cols]
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_count': df.isnull().sum().to_dict(),
            'missing_total': int(df.isnull().sum().sum()),
        }

    @staticmethod
    def get_statistics(df: pd.DataFrame) -> dict:
        """计算数值列的统计指标"""
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            return {'message': '没有可计算的数值列', 'stats': {}}

        stats = {
            'count': numeric_df.count().to_dict(),
            'mean': numeric_df.mean().round(4).to_dict(),
            'std': numeric_df.std().round(4).to_dict(),
            'min': numeric_df.min().to_dict(),
            'max': numeric_df.max().to_dict(),
            'median': numeric_df.median().to_dict(),
            'q25': numeric_df.quantile(0.25).to_dict(),
            'q75': numeric_df.quantile(0.75).to_dict(),
        }
        # 将 numpy 类型转为原生 Python 类型
        for key, val_dict in stats.items():
            stats[key] = {k: (float(v) if pd.notna(v) else None) for k, v in val_dict.items()}
        return stats

    @staticmethod
    def get_head_data(df: pd.DataFrame, n: int = 10) -> list:
        """获取前 N 行数据"""
        return df.head(n).fillna('').to_dict(orient='records')

    @staticmethod
    def generate_chart(
        df: pd.DataFrame,
        chart_type: str = 'line',
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
    ) -> Optional[str]:
        """
        生成图表并保存为 PNG

        参数:
            df: 数据框
            chart_type: 'line' | 'bar' | 'pie' | 'scatter' | 'hist'
            x_col: X 轴列名（pie 不需要）
            y_col: Y 轴列名

        返回: 图表 URL 路径
        """
        # 自动选列
        columns = list(df.columns)
        if not columns:
            return None

        numeric_cols = list(df.select_dtypes(include=['number']).columns)

        filename = f"{uuid.uuid4().hex[:12]}.png"
        filepath = os.path.join(CHARTS_DIR, filename)

        try:
            fig, ax = plt.subplots(figsize=(10, 5))

            if chart_type == 'line':
                x = df[x_col] if x_col and x_col in columns else df.index
                y = df[y_col] if y_col and y_col in numeric_cols else (
                    df[numeric_cols[0]] if numeric_cols else df.iloc[:, 0]
                )
                ax.plot(x, y, marker='o', linewidth=1.5, markersize=3, color='#4f46e5')
                ax.set_xlabel(x_col or 'Index')
                ax.set_ylabel(y_col or (numeric_cols[0] if numeric_cols else 'Value'))
                ax.set_title('折线图')
                ax.grid(True, alpha=0.3)

            elif chart_type == 'bar':
                x_col = x_col or columns[0]
                y_col = y_col or (numeric_cols[0] if numeric_cols else columns[-1])
                # 限制显示前 20 条
                data = df.head(20)
                ax.bar(range(len(data)), data[y_col], color='#4f46e5', alpha=0.85)
                ax.set_xticks(range(len(data)))
                ax.set_xticklabels(data[x_col].astype(str), rotation=45, ha='right', fontsize=8)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title('柱状图 (前20条)')
                ax.grid(True, alpha=0.3, axis='y')

            elif chart_type == 'pie':
                val_col = y_col or (numeric_cols[0] if numeric_cols else columns[-1])
                label_col = x_col or columns[0]
                data = df.head(10)
                wedges, texts, autotexts = ax.pie(
                    data[val_col],
                    labels=data[label_col].astype(str),
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=plt.cm.Set3.colors,
                )
                ax.set_title('饼图 (前10条)')

            elif chart_type == 'scatter':
                x_col = x_col or (numeric_cols[0] if len(numeric_cols) > 0 else columns[0])
                y_col = y_col or (numeric_cols[1] if len(numeric_cols) > 1 else columns[-1])
                ax.scatter(df[x_col], df[y_col], alpha=0.6, color='#4f46e5', s=20)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title('散点图')
                ax.grid(True, alpha=0.3)

            elif chart_type == 'hist':
                col = y_col or (numeric_cols[0] if numeric_cols else columns[0])
                ax.hist(df[col].dropna(), bins=20, color='#4f46e5', alpha=0.85, edgecolor='white')
                ax.set_xlabel(col)
                ax.set_ylabel('频次')
                ax.set_title('直方图')
                ax.grid(True, alpha=0.3, axis='y')

            else:
                plt.close(fig)
                return None

            plt.tight_layout()
            plt.savefig(filepath, dpi=120, bbox_inches='tight')
            plt.close(fig)

            return f'/static/charts/{filename}'

        except Exception as e:
            logger.error(f'图表生成失败: {e}')
            if os.path.exists(filepath):
                os.remove(filepath)
            plt.close('all')
            return None

    @staticmethod
    def get_correlation(df: pd.DataFrame) -> dict:
        """计算数值列之间的相关系数矩阵"""
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.shape[1] < 2:
            return {'message': '至少需要两个数值列才能计算相关性', 'data': {}}

        corr = numeric_df.corr().round(4)
        return {
            'columns': list(corr.columns),
            'data': {col: {k: (float(v) if pd.notna(v) else None) for k, v in row.items()}
                     for col, row in corr.to_dict().items()},
        }
