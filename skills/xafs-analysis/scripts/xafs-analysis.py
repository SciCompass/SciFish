# -*- coding: utf-8 -*-
"""
全自动化XAFS预处理分析流程
按照需求文档实现四个阶段的分析
"""

import sys
import io
import argparse
# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置Nature/Science级别的绘图风格
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'SimHei']
rcParams['font.size'] = 11
rcParams['axes.linewidth'] = 1.5
rcParams['axes.labelsize'] = 13
rcParams['axes.titlesize'] = 14
rcParams['xtick.labelsize'] = 11
rcParams['ytick.labelsize'] = 11
rcParams['xtick.major.width'] = 1.5
rcParams['ytick.major.width'] = 1.5
rcParams['xtick.major.size'] = 5
rcParams['ytick.major.size'] = 5
rcParams['xtick.direction'] = 'in'
rcParams['ytick.direction'] = 'in'
rcParams['legend.fontsize'] = 10
rcParams['legend.frameon'] = True
rcParams['legend.edgecolor'] = 'black'
rcParams['legend.fancybox'] = False
rcParams['axes.unicode_minus'] = False
rcParams['mathtext.default'] = 'regular'

try:
    from larch import Interpreter
    from larch.io import read_ascii
    from larch.xafs import pre_edge, autobk, xftf, find_e0
    from larch.xray import xray_edge  # 导入Larch的X射线数据库
    LARCH_AVAILABLE = True
except ImportError:
    LARCH_AVAILABLE = False
    xray_edge = None
    print("警告: Larch库未安装，将使用基础NumPy实现")


class XAFSAnalyzer:
    """XAFS数据自动化分析类"""

    def __init__(self, element='Mn', edge='K', require_larch=True):
        """
        初始化分析器

        参数:
            element: 吸收元素，如'Mn'
            edge: 吸收边类型，如'K'
            require_larch: 是否要求使用Larch（默认True，以确保与Demeter一致）
        """
        self.element = element
        self.edge = edge
        self.edge_name = f"{element} {edge}-edge"
        self.require_larch = require_larch

        # 检查Larch可用性
        if not LARCH_AVAILABLE:
            if self.require_larch:
                raise ImportError(
                    "Larch库未安装！为确保与Demeter结果一致，必须安装Larch。\n"
                    "请运行: pip install xraylarch\n"
                    "或设置 require_larch=False 使用基础NumPy实现（结果会有差异）"
                )
            else:
                print("=" * 60)
                print("警告: Larch库未安装，将使用基础NumPy实现")
                print("结果可能与Demeter软件存在差异！")
                print("建议安装Larch: pip install xraylarch")
                print("=" * 60)

        self.data_groups = []  # 存储所有数据组
        self.larch = Interpreter() if LARCH_AVAILABLE else None

        # 使用Larch内置的X射线数据库（支持所有元素和吸收边）
        # 如果Larch不可用，使用备用的手动数据库
        if LARCH_AVAILABLE and xray_edge is not None:
            print(f"[INFO] 使用Larch内置X射线数据库（支持所有元素）")
        else:
            print(f"[INFO] 使用备用手动数据库（仅支持部分元素）")

    def get_standard_edge_energy(self, element, edge):
        """
        获取标准吸收边能量

        参数:
            element: 元素符号，如'Mn', 'Fe'
            edge: 吸收边类型，如'K', 'L3', 'L2', 'L1', 'M5'

        返回:
            标准吸收边能量(eV)，如果找不到则返回None
        """
        if LARCH_AVAILABLE and xray_edge is not None:
            try:
                # 使用Larch的xray_edge函数获取吸收边能量
                edge_data = xray_edge(element, edge)
                if edge_data is not None:
                    return edge_data.energy
            except Exception as e:
                print(f"[WARNING] 无法从Larch数据库获取{element} {edge}边能量: {e}")

        # 备用手动数据库（仅包含常见元素的K边）
        fallback_edges = {
            'Ti K': 4966.0,
            'V K': 5465.0,
            'Cr K': 5989.0,
            'Mn K': 6539.0,
            'Fe K': 7112.0,
            'Co K': 7709.0,
            'Ni K': 8333.0,
            'Cu K': 8979.0,
            'Zn K': 9659.0,
            'Mo K': 20000.0,
            'Ag K': 25514.0,
            'Sn K': 29200.0,
            'Pt K': 78395.0,
            'Au K': 80725.0,
        }

        edge_key = f"{element} {edge}"
        return fallback_edges.get(edge_key, None)

    def read_data(self, filepath):
        """
        阶段一：数据解析
        读取原始数据文件并计算吸收系数μ(E)

        参数:
            filepath: 数据文件路径

        返回:
            data_group: 包含能量和吸收系数的数据对象
        """
        print(f"\n{'='*60}")
        print(f"阶段一：数据解析 - {os.path.basename(filepath)}")
        print(f"{'='*60}")

        # 检查文件扩展名
        file_ext = os.path.splitext(filepath)[1].lower()

        if file_ext == '.prj':
            # 读取Athena .prj格式文件
            return self._read_prj_file(filepath)
        else:
            # 读取普通文本格式文件
            return self._read_text_file(filepath)

    def _fix_inverted_spectrum(self, energy, mu, filename):
        energy_array = np.asarray(energy, dtype=float)
        mu_array = np.asarray(mu, dtype=float)

        if len(energy_array) < 20 or len(mu_array) != len(energy_array):
            return mu_array, False, 0.0

        sort_idx = np.argsort(energy_array)
        energy_sorted = energy_array[sort_idx]
        mu_sorted = mu_array[sort_idx]

        if np.any(np.diff(energy_sorted) <= 0):
            unique_mask = np.concatenate(([True], np.diff(energy_sorted) > 0))
            energy_sorted = energy_sorted[unique_mask]
            mu_sorted = mu_sorted[unique_mask]

        if len(energy_sorted) < 20:
            return mu_array, False, 0.0

        derivative = np.gradient(mu_sorted, energy_sorted)
        e0_idx = int(np.argmax(np.abs(derivative)))

        half_window = max(5, len(energy_sorted) // 25)
        pre_start = max(0, e0_idx - 2 * half_window)
        pre_end = max(pre_start + 3, e0_idx - half_window)
        post_start = min(len(energy_sorted) - 3, e0_idx + half_window)
        post_end = min(len(energy_sorted), e0_idx + 2 * half_window)

        if pre_end <= pre_start or post_end <= post_start:
            return mu_array, False, 0.0

        pre_mean = float(np.mean(mu_sorted[pre_start:pre_end]))
        post_mean = float(np.mean(mu_sorted[post_start:post_end]))
        edge_step = post_mean - pre_mean

        if edge_step < 0:
            corrected_sorted = -mu_sorted
            corrected_mu = np.empty_like(mu_array)
            corrected_mu[sort_idx] = corrected_sorted
            print(f"[INFO] 检测到吸收谱倒立，已自动执行Invert修正: {filename}")
            print(f"  - 原始边跃迁方向: {edge_step:.4f} (负值)")
            return corrected_mu, True, edge_step

        return mu_array, False, edge_step

    def _read_prj_file(self, filepath):
        """
        读取Athena项目文件(.prj格式)

        参数:
            filepath: .prj文件路径

        返回:
            data_group: 包含能量和吸收系数的数据对象
        """
        import gzip
        import re

        # 解压并读取.prj文件
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()

        # 提取能量数据 @x
        x_match = re.search(r"@x = \((.*?)\);", content, re.DOTALL)
        if not x_match:
            raise ValueError("无法在.prj文件中找到能量数据(@x)")

        # 提取信号数据 @y 或 @signal
        y_match = re.search(r"@y = \((.*?)\);", content, re.DOTALL)
        if not y_match:
            y_match = re.search(r"@signal = \((.*?)\);", content, re.DOTALL)
        if not y_match:
            raise ValueError("无法在.prj文件中找到信号数据(@y或@signal)")

        # 解析数据
        energy_str = x_match.group(1).replace("'", "").replace(" ", "")
        energy = np.array([float(x) for x in energy_str.split(',') if x])

        mu_str = y_match.group(1).replace("'", "").replace(" ", "")
        mu = np.array([float(x) for x in mu_str.split(',') if x])

        # 创建数据组对象
        class DataGroup:
            pass

        data_group = DataGroup()
        data_group.filename = os.path.basename(filepath)
        data_group.energy = energy
        corrected_mu, was_inverted, edge_step_direction = self._fix_inverted_spectrum(
            data_group.energy, mu, data_group.filename
        )
        data_group.mu = corrected_mu
        data_group.i0 = np.ones_like(energy)  # .prj文件通常已经是归一化的
        data_group.i1 = np.ones_like(energy)
        data_group.inverted = was_inverted
        data_group.raw_edge_step_direction = edge_step_direction

        print(f"[INFO] 检测到Athena .prj格式")
        print(f"[OK] 成功读取数据文件")
        print(f"  - 数据点数: {len(energy)}")
        print(f"  - 能量范围: {energy.min():.2f} - {energy.max():.2f} eV")
        print(f"  - μ(E)范围: {data_group.mu.min():.4f} - {data_group.mu.max():.4f}")

        return data_group

    def _read_text_file(self, filepath):
        """
        读取普通文本格式数据文件

        参数:
            filepath: 文本文件路径

        返回:
            data_group: 包含能量和吸收系数的数据对象
        """
        # 检测是否有表头
        has_header = False
        import re

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='gbk') as f:
                    first_line = f.readline().strip()
            except:
                with open(filepath, 'r', encoding='latin-1') as f:
                    first_line = f.readline().strip()

        # 如果第一行包含非数字字符（除了空格、点、负号、科学计数法e/E），则判断为表头
        # 检查是否包含字母（排除科学计数法的e/E）
        # 移除科学计数法中的e/E（如1.23e-5）
        test_line = re.sub(r'[0-9]+\.?[0-9]*[eE][+-]?[0-9]+', '', first_line)
        # 如果还有字母，说明是表头
        if re.search(r'[a-zA-Z]', test_line):
            has_header = True

        # 读取数据，尝试不同的方式处理可能的编码和格式问题
        skiprows = 1 if has_header else 0
        try:
            data = np.loadtxt(filepath, skiprows=skiprows, encoding='utf-8')
        except (ValueError, UnicodeDecodeError):
            # 如果UTF-8失败，尝试其他编码
            try:
                data = np.loadtxt(filepath, skiprows=skiprows, encoding='gbk')
            except:
                data = np.loadtxt(filepath, skiprows=skiprows, encoding='latin-1')

        # 提取列数据 - 自动检测文件格式
        num_cols = data.shape[1]

        if has_header:
            print(f"[INFO] 检测到表头，已自动跳过")
            print(f"  - 表头内容: {first_line}")

        if num_cols == 2:
            # 2列格式: Energy, Transmission 或 Energy, Normalized_mu 或 Energy, ln(Count0/Count1)
            energy = data[:, 0]
            second_col = data[:, 1]

            # 判断第二列的数据类型
            # 1. ln(Count0/Count1) 或 ln(I0/I1): 通常为负数或小正数（-3.0到3.0）
            # 2. Transmission (I1/I0 或 Count0): 通常在0.5-1.5范围内，接近1.0
            # 3. 小数值 (归一化μ或小比值): 很小的正数（0.001-0.05）
            # 4. Normalized μ: 较大范围（-0.5到3.0）

            mean_val = np.mean(second_col)
            std_val = np.std(second_col)
            min_val = second_col.min()
            max_val = second_col.max()

            # 判断逻辑
            if min_val < 0 and max_val < 0.5:
                # 全部为负数或接近0的小数 → ln(Count0/Count1) 或 ln(I0/I1) 格式
                # 这种格式已经是对数形式，直接使用
                mu = second_col
                i0 = np.ones_like(energy)
                i1 = np.ones_like(energy)
                print(f"[INFO] 检测到2列格式 (Energy, ln(Count0/Count1)) - 固探模式")
                print(f"  - ln(Count0/Count1)范围: {min_val:.6f} - {max_val:.6f}")
            elif 0.5 < mean_val < 1.5 and std_val < 0.5:
                # 值接近1.0，范围较窄 → Transmission格式 (I1/I0 或 HPGeCounter/Count0)
                # 计算 μ(E) = -ln(Transmission) = -ln(I1/I0) = ln(I0/I1)
                mu = -np.log(second_col)
                i0 = np.ones_like(energy)
                i1 = second_col
                print(f"[INFO] 检测到2列格式 (Energy, Transmission/HPGeCounter) - 固探模式")
                print(f"  - Transmission范围: {min_val:.6f} - {max_val:.6f}")
            elif max_val < 0.1 and mean_val < 0.05:
                # 很小的正数 → 可能是归一化的小比值或荧光信号
                # 直接使用作为μ(E)
                mu = second_col
                i0 = np.ones_like(energy)
                i1 = np.ones_like(energy)
                print(f"[INFO] 检测到2列格式 (Energy, Small_Ratio) - 固探模式")
                print(f"  - 数值范围: {min_val:.6f} - {max_val:.6f}")
            else:
                # 其他情况 → Normalized μ格式
                mu = second_col
                i0 = np.ones_like(energy)
                i1 = np.ones_like(energy)
                print(f"[INFO] 检测到2列格式 (Energy, Normalized_mu)")
                print(f"  - Normalized μ范围: {min_val:.6f} - {max_val:.6f}")

        elif num_cols == 3:
            # 3列格式: Energy, I0, I1
            energy = data[:, 0]
            i0 = data[:, 1]
            i1 = data[:, 2]
            mu = np.log(i0 / i1)
            print(f"[INFO] 检测到3列格式 (Energy, I0, I1)")

        elif num_cols == 4:
            # 4列格式: No., Energy, I0, I1 或 Energy, I0, I1, ln(I0/I1)
            # 检查第一列是否是序号（通常是整数且递增）
            first_col = data[:, 0]
            if np.allclose(first_col, np.arange(1, len(first_col) + 1), atol=1):
                # 第一列是序号: No., Energy, I0, I1
                energy = data[:, 1]
                i0 = data[:, 2]
                i1 = data[:, 3]
                mu = np.log(i0 / i1)
                print(f"[INFO] 检测到4列格式 (No., Energy, I0, I1)")
            else:
                # Energy, I0, I1, ln(I0/I1)
                energy = data[:, 0]
                i0 = data[:, 1]
                i1 = data[:, 2]
                mu = data[:, 3]
                print(f"[INFO] 检测到4列格式 (Energy, I0, I1, ln(I0/I1))")

        elif num_cols >= 5:
            # 5列格式: No., Energy, I0, I1, ln(I0/I1) 或 No., Energy, I0, I1, I1/I0 或 No., Energy, I0, Lytle, Lytle/I0
            energy = data[:, 1]
            i0 = data[:, 2]
            i1 = data[:, 3]
            fifth_col = data[:, 4]

            # 优先根据表头判断测试模式
            mode_detected_by_header = None
            if has_header:
                header_lower = first_line.lower()
                if 'lytle' in header_lower:
                    mode_detected_by_header = 'fluorescence'
                elif 'hpgecounter' in header_lower or 'count' in header_lower:
                    mode_detected_by_header = 'solid_state'
                elif 'ln' in header_lower or 'log' in header_lower:
                    mode_detected_by_header = 'logarithm'

            # 根据表头判断结果或数值特征判断模式
            if mode_detected_by_header == 'fluorescence':
                # 表头明确指示荧光模式：Lytle
                mu = fifth_col
                print(f"[INFO] 检测到{num_cols}列格式 (No., Energy, I0, Lytle, Lytle/I0) - 荧光模式")
                print(f"  - 识别依据: 表头包含'Lytle'")
                print(f"  - Lytle/I0范围: {fifth_col.min():.6f} - {fifth_col.max():.6f}")
            elif mode_detected_by_header == 'logarithm':
                # 表头明确指示对数模式：ln(I0/I1)
                mu = fifth_col
                print(f"[INFO] 检测到{num_cols}列格式 (No., Energy, I0, I1, ln(I0/I1))")
                print(f"  - 识别依据: 表头包含'ln'或'log'")
                print(f"  - ln(I0/I1)范围: {fifth_col.min():.4f} - {fifth_col.max():.4f}")
            else:
                # 没有表头或表头不明确，使用数值判断
                # 计算理论值进行对比
                theoretical_ratio = i1 / i0  # I1/I0 或 Lytle/I0
                theoretical_ln = np.log(i0 / i1)  # ln(I0/I1)

                # 计算与第5列的相关性
                ratio_diff = np.mean(np.abs(fifth_col - theoretical_ratio))
                ln_diff = np.mean(np.abs(fifth_col - theoretical_ln))

                # 判断是否为荧光模式：第5列值很小（< 0.05）且与理论比值接近
                max_fifth = fifth_col.max()
                mean_fifth = np.mean(fifth_col)

                if ratio_diff < ln_diff:
                    # 第5列是比值（I1/I0 或 Lytle/I0）
                    if max_fifth < 0.05 and mean_fifth < 0.02:
                        # 荧光模式：Lytle/I0
                        mu = fifth_col
                        print(f"[INFO] 检测到{num_cols}列格式 (No., Energy, I0, Lytle, Lytle/I0) - 荧光模式")
                        print(f"  - 识别依据: 数值特征（最大值<0.05，平均值<0.02）")
                        print(f"  - Lytle/I0范围: {fifth_col.min():.6f} - {fifth_col.max():.6f}")
                    else:
                        # 透射模式：I1/I0
                        mu = -np.log(fifth_col)
                        print(f"[INFO] 检测到{num_cols}列格式 (No., Energy, I0, I1, I1/I0) - 透射模式")
                        print(f"  - 识别依据: 数值特征（比值格式）")
                        print(f"  - I1/I0范围: {fifth_col.min():.4f} - {fifth_col.max():.4f}")
                else:
                    # 第5列是ln(I0/I1)
                    mu = fifth_col
                    print(f"[INFO] 检测到{num_cols}列格式 (No., Energy, I0, I1, ln(I0/I1))")
                    print(f"  - 识别依据: 数值特征（对数格式）")
                    print(f"  - ln(I0/I1)范围: {fifth_col.min():.4f} - {fifth_col.max():.4f}")

        else:
            raise ValueError(f"不支持的数据格式: {num_cols}列")

        # 创建数据组对象
        class DataGroup:
            pass

        data_group = DataGroup()
        data_group.filename = os.path.basename(filepath)
        data_group.energy = energy
        corrected_mu, was_inverted, edge_step_direction = self._fix_inverted_spectrum(
            data_group.energy, mu, data_group.filename
        )
        data_group.mu = corrected_mu
        data_group.i0 = i0
        data_group.i1 = i1
        data_group.inverted = was_inverted
        data_group.raw_edge_step_direction = edge_step_direction

        print(f"[OK] 成功读取数据文件")
        print(f"  - 数据点数: {len(energy)}")
        print(f"  - 能量范围: {energy.min():.2f} - {energy.max():.2f} eV")
        print(f"  - μ(E)范围: {data_group.mu.min():.4f} - {data_group.mu.max():.4f}")

        return data_group

    def _detect_element_from_edge(self, e0_measured):
        """
        根据测量的吸收边能量自动检测元素

        参数:
            e0_measured: 测量的吸收边能量 (eV)

        返回:
            检测到的元素符号，如果无法匹配则返回None
        """
        min_diff = float('inf')
        detected_element = None

        # 定义要检测的元素列表（按原子序数排序）
        # 包含常见的XAFS测量元素
        elements_to_check = [
            'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',  # 3d过渡金属
            'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',  # 4d过渡金属
            'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',   # 5d过渡金属
            'Al', 'Si', 'P', 'S', 'Cl',  # 轻元素
            'Ga', 'Ge', 'As', 'Se', 'Br',  # 其他元素
            'In', 'Sn', 'Sb', 'Te', 'I',
            'Pb', 'Bi',
            'Ce', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',  # 稀土元素
        ]

        # 同时检查 K 边和 L 边，找到全局最近匹配
        for element in elements_to_check:
            for edge in ['K', 'L3', 'L2', 'L1']:
                e0_standard = self.get_standard_edge_energy(element, edge)
                if e0_standard is not None:
                    diff = abs(e0_measured - e0_standard)
                    # 允许±500 eV的误差范围
                    if diff < min_diff and diff < 500:
                        min_diff = diff
                        detected_element = element

        return detected_element

    def detect_edge_type(self, element, e0_measured):
        """
        根据测量的E0与Larch内置边能对照表，判断是K边还是L边

        步骤:
          1. 在μ(E)谱里找到吸收边位置E0（由调用方提供）
          2. 查询该元素的K/L1/L2/L3标准边能（Larch内置数据库）
          3. 找到与E0差值最小的边，即为测量边类型

        参数:
            element: 元素符号，如'Mn', 'Fe'
            e0_measured: 测量的吸收边能量 (eV)

        返回:
            detected_edge: 检测到的边类型，如'K', 'L3', 'L2', 'L1'；失败时返回None
        """
        if element in ('Unknown', '', None):
            print(f"[WARNING] 元素未知，无法进行边类型判断")
            return None

        edges_to_check = ['K', 'L3', 'L2', 'L1']
        best_edge = None
        best_energy = None
        best_diff = float('inf')
        edge_results = {}

        for edge in edges_to_check:
            energy = self.get_standard_edge_energy(element, edge)
            if energy is not None:
                diff = abs(e0_measured - energy)
                edge_results[edge] = (energy, diff)
                if diff < best_diff:
                    best_diff = diff
                    best_edge = edge
                    best_energy = energy

        if not edge_results:
            print(f"[WARNING] 无法获取{element}的边能数据，保持当前边类型: {self.edge}")
            return None

        # 打印对照表
        print(f"\n[INFO] {element}元素吸收边能量对照 (测量E0 = {e0_measured:.2f} eV):")
        for edge in edges_to_check:
            if edge in edge_results:
                energy, diff = edge_results[edge]
                marker = "  ← 最佳匹配" if edge == best_edge else ""
                print(f"  - {edge:3s}: {energy:9.2f} eV  (差值: {diff:7.2f} eV){marker}")

        edge_desc = {
            'K':  'K-edge  (1s轨道)',
            'L1': 'L1-edge (2s轨道)',
            'L2': 'L2-edge (2p1/2轨道)',
            'L3': 'L3-edge (2p3/2轨道)',
        }
        desc = edge_desc.get(best_edge, f'{best_edge}-edge')
        print(f"[OK] 边类型判断结果: {element} {desc}")
        print(f"     标准能量: {best_energy:.2f} eV，与测量值差: {best_diff:.2f} eV")

        return best_edge

    def calibrate_energy(self, data_group, reference_group=None):
        """
        能量校准：使用参考箔校准能量

        参数:
            data_group: 待校准的数据组
            reference_group: 参考箔数据组（如果提供）
        """
        if reference_group is not None:
            # 找到参考箔的吸收边位置（一阶导数最大值）
            derivative = np.gradient(reference_group.mu, reference_group.energy)
            e0_measured = reference_group.energy[np.argmax(derivative)]

            # 获取标准吸收边能量（使用Larch数据库或备用数据库）
            e0_standard = self.get_standard_edge_energy(self.element, self.edge)
            if e0_standard is None:
                print(f"[WARNING] 未找到{self.element} {self.edge}边的标准能量，使用测量值")
                e0_standard = e0_measured

            # 计算能量偏移
            delta_e = e0_measured - e0_standard

            # 校准能量
            data_group.energy_calibrated = data_group.energy - delta_e
            data_group.delta_e = delta_e

            print(f"[OK] 能量校准完成")
            print(f"  - 测量吸收边: {e0_measured:.3f} eV")
            print(f"  - 标准吸收边: {e0_standard:.3f} eV")
            print(f"  - 能量偏移: {delta_e:.3f} eV")
        else:
            # 如果没有参考箔，不进行校准
            data_group.energy_calibrated = data_group.energy.copy()
            data_group.delta_e = 0.0

    def normalize(self, data_group):
        """
        阶段二：预处理
        边前区拟合、背景扣除和归一化

        参数:
            data_group: 数据组对象
        """
        print(f"\n{'='*60}")
        print(f"阶段二：预处理与归一化 - {data_group.filename}")
        print(f"{'='*60}")

        energy = data_group.energy_calibrated
        mu = data_group.mu

        if LARCH_AVAILABLE and self.larch is not None:
            # 使用Larch进行归一化
            try:
                # 创建Larch数据组
                larch_group = self.larch.symtable.create_group()
                larch_group.energy = energy
                larch_group.mu = mu

                # 执行pre_edge归一化
                pre_edge(larch_group, _larch=self.larch)

                data_group.e0 = larch_group.e0
                data_group.norm = larch_group.norm
                data_group.pre_edge = larch_group.pre_edge
                data_group.post_edge = larch_group.post_edge
                data_group.edge_step = larch_group.edge_step

                print(f"[OK] 使用Larch完成归一化处理（与Demeter一致）")
                print(f"  - 吸收边E₀: {data_group.e0:.2f} eV")
                print(f"  - 边跃迁高度: {data_group.edge_step:.4f}")

            except Exception as e:
                if self.require_larch:
                    raise RuntimeError(f"Larch处理失败: {e}\n无法确保与Demeter结果一致")
                print(f"[WARNING] Larch处理失败，使用基础方法（结果会与Demeter不同）: {e}")
                self._normalize_basic(data_group)
        else:
            if self.require_larch:
                raise RuntimeError("Larch不可用，无法确保与Demeter结果一致")
            # 使用基础NumPy实现
            self._normalize_basic(data_group)

    def _normalize_basic(self, data_group):
        """基础归一化方法（不依赖Larch）"""
        energy = data_group.energy_calibrated
        mu = data_group.mu

        # 找到吸收边位置（一阶导数最大值）
        derivative = np.gradient(mu, energy)
        e0_idx = np.argmax(derivative)
        e0 = energy[e0_idx]

        # 边前区拟合（E0前50 eV）
        pre_edge_mask = energy < (e0 - 50)
        if np.sum(pre_edge_mask) > 2:
            pre_edge_coeffs = np.polyfit(energy[pre_edge_mask], mu[pre_edge_mask], 1)
            pre_edge_line = np.polyval(pre_edge_coeffs, energy)
        else:
            pre_edge_line = np.zeros_like(energy)

        # 边后区拟合（E0后50 eV以上）
        post_edge_mask = energy > (e0 + 50)
        if np.sum(post_edge_mask) > 2:
            post_edge_coeffs = np.polyfit(energy[post_edge_mask], mu[post_edge_mask], 2)
            post_edge_line = np.polyval(post_edge_coeffs, energy)
        else:
            post_edge_line = np.ones_like(energy) * mu.max()

        # 计算边跃迁高度
        edge_step = post_edge_line[e0_idx] - pre_edge_line[e0_idx]

        # 归一化
        norm = (mu - pre_edge_line) / edge_step

        data_group.e0 = e0
        data_group.norm = norm
        data_group.pre_edge = pre_edge_line
        data_group.post_edge = post_edge_line
        data_group.edge_step = edge_step

        print(f"[OK] 使用基础方法完成归一化处理")
        print(f"  - 吸收边E₀: {e0:.2f} eV")
        print(f"  - 边跃迁高度: {edge_step:.4f}")

    def extract_exafs(self, data_group, rbkg=1.0, kweight=2):
        """
        阶段三：K空间转换
        提取EXAFS信号χ(k)

        参数:
            data_group: 数据组对象
            rbkg: 背景去除参数
            kweight: k权重
        """
        print(f"\n{'='*60}")
        print(f"阶段四：K空间转换 - {data_group.filename}")
        print(f"{'='*60}")

        energy = data_group.energy_calibrated
        mu = data_group.mu
        e0 = data_group.e0

        if LARCH_AVAILABLE and self.larch is not None:
            try:
                # 确保能量数据严格递增（Larch要求）
                energy_sorted_idx = np.argsort(energy)
                energy_sorted = energy[energy_sorted_idx]
                mu_sorted = mu[energy_sorted_idx]

                # 去除重复的能量点
                unique_mask = np.concatenate(([True], np.diff(energy_sorted) > 0))
                energy_unique = energy_sorted[unique_mask]
                mu_unique = mu_sorted[unique_mask]

                # 创建Larch数据组
                larch_group = self.larch.symtable.create_group()
                larch_group.energy = energy_unique
                larch_group.mu = mu_unique
                larch_group.e0 = e0

                # 执行autobk提取EXAFS信号
                autobk(larch_group, rbkg=rbkg, kweight=kweight, _larch=self.larch)

                data_group.k = larch_group.k
                data_group.chi = larch_group.chi
                data_group.kweight = kweight

                print(f"[OK] 使用Larch提取EXAFS信号（与Demeter一致）")
                print(f"  - k范围: {data_group.k.min():.2f} - {data_group.k.max():.2f} Å⁻¹")
                print(f"  - χ(k)范围: {data_group.chi.min():.4f} - {data_group.chi.max():.4f}")

            except Exception as e:
                if self.require_larch:
                    raise RuntimeError(f"Larch处理失败: {e}\n无法确保与Demeter结果一致")
                print(f"[WARNING] Larch处理失败，使用基础方法（结果会与Demeter不同）: {e}")
                self._extract_exafs_basic(data_group, kweight)
        else:
            if self.require_larch:
                raise RuntimeError("Larch不可用，无法确保与Demeter结果一致")
            self._extract_exafs_basic(data_group, kweight)

    def _extract_exafs_basic(self, data_group, kweight=2):
        """基础EXAFS提取方法"""
        energy = data_group.energy_calibrated
        mu = data_group.mu
        e0 = data_group.e0

        # 只使用E0以上的数据，尽可能扩展k空间范围
        mask = energy > e0
        e = energy[mask]
        mu_above = mu[mask]

        # 转换到k空间：k = sqrt(2m(E-E0)/ħ²)
        # 使用精确的物理常数: k(Å⁻¹) = 0.512317 * sqrt(E-E0(eV))
        # 这个常数来自 sqrt(2*m_e) / hbar，确保能达到更大的k值
        k = 0.512317 * np.sqrt(e - e0)

        # 对μ(E)进行平滑作为背景μ0
        from scipy.ndimage import uniform_filter1d
        window_size = min(51, len(mu_above) // 10)
        if window_size % 2 == 0:
            window_size += 1
        mu0 = uniform_filter1d(mu_above, size=window_size)

        # 计算χ(k) = (μ - μ0) / μ0
        chi = (mu_above - mu0) / mu0

        data_group.k = k
        data_group.chi = chi
        data_group.kweight = kweight

        print(f"[OK] 使用基础方法提取EXAFS信号")
        print(f"  - k范围: {k.min():.2f} - {k.max():.2f} Å⁻¹")
        print(f"  - χ(k)范围: {chi.min():.4f} - {chi.max():.4f}")

    def fourier_transform(self, data_group, kmin=3.0, kmax=12.0, kweight=2, dk=1):
        """
        阶段四：R空间转换
        傅里叶变换得到χ(R)

        参数:
            data_group: 数据组对象
            kmin: k范围最小值（默认3.0，匹配Demeter）
            kmax: k范围最大值
            kweight: k权重
            dk: 窗口宽度
        """
        print(f"\n{'='*60}")
        print(f"阶段五：R空间转换 - {data_group.filename}")
        print(f"{'='*60}")

        if not hasattr(data_group, 'k') or not hasattr(data_group, 'chi'):
            print("[WARNING] 请先执行K空间转换")
            return

        k = data_group.k
        chi = data_group.chi

        k_data_min = float(np.min(k))
        k_data_max = float(np.max(k))

        kmin_eff = max(kmin, k_data_min + 0.5)
        kmax_eff = min(kmax, k_data_max - 0.5)

        if kmax_eff <= kmin_eff:
            kmin_eff = max(k_data_min + 0.05, 0.0)
            kmax_eff = k_data_max - 0.05

        if kmax_eff <= kmin_eff:
            r = np.arange(0, 6, 0.02)
            data_group.r = r
            data_group.chir_mag = np.zeros_like(r)
            data_group.chir_re = np.zeros_like(r)
            data_group.chir_im = np.zeros_like(r)
            print("[WARNING] k空间有效范围过窄，R空间结果置零")
            return

        if LARCH_AVAILABLE and self.larch is not None:
            try:
                # 创建Larch数据组
                larch_group = self.larch.symtable.create_group()
                larch_group.k = k
                larch_group.chi = chi

                # 执行傅里叶变换
                xftf(larch_group, kmin=kmin_eff, kmax=kmax_eff, kweight=kweight, dk=dk, _larch=self.larch)

                data_group.r = larch_group.r
                data_group.chir_mag = larch_group.chir_mag
                data_group.chir_re = larch_group.chir_re
                data_group.chir_im = larch_group.chir_im

                print(f"[OK] 使用Larch完成傅里叶变换（与Demeter一致）")
                print(f"  - R范围: {data_group.r.min():.2f} - {data_group.r.max():.2f} Å")
                print(f"  - k范围: {kmin_eff:.1f} - {kmax_eff:.1f} Å⁻¹")

            except Exception as e:
                print(f"[WARNING] Larch傅里叶变换失败，自动缩窗重试: {e}")
                retry_kmin = max(k_data_min + 0.05, 0.0)
                retry_kmax = k_data_max - 0.05
                if retry_kmax > retry_kmin:
                    try:
                        larch_group = self.larch.symtable.create_group()
                        larch_group.k = k
                        larch_group.chi = chi
                        xftf(larch_group, kmin=retry_kmin, kmax=retry_kmax, kweight=kweight, dk=dk, _larch=self.larch)
                        data_group.r = larch_group.r
                        data_group.chir_mag = larch_group.chir_mag
                        data_group.chir_re = larch_group.chir_re
                        data_group.chir_im = larch_group.chir_im
                        print(f"[OK] 使用Larch缩窗重试成功")
                        print(f"  - k范围: {retry_kmin:.1f} - {retry_kmax:.1f} Å⁻¹")
                        return
                    except Exception as e2:
                        print(f"[WARNING] Larch缩窗重试失败: {e2}")
                if self.require_larch:
                    r = np.arange(0, 6, 0.02)
                    data_group.r = r
                    data_group.chir_mag = np.zeros_like(r)
                    data_group.chir_re = np.zeros_like(r)
                    data_group.chir_im = np.zeros_like(r)
                    print("[WARNING] 当前样品k范围不足，已输出零R谱以保证批处理不中断")
                    return
                print(f"[WARNING] 使用基础方法继续处理")
                self._fourier_transform_basic(data_group, kmin_eff, kmax_eff, kweight)
        else:
            if self.require_larch:
                raise RuntimeError("Larch不可用，无法确保与Demeter结果一致")
            self._fourier_transform_basic(data_group, kmin_eff, kmax_eff, kweight)

    def _fourier_transform_basic(self, data_group, kmin, kmax, kweight):
        """基础傅里叶变换方法"""
        k = data_group.k
        chi = data_group.chi

        # 选择k范围
        mask = (k >= kmin) & (k <= kmax)
        k_ft = k[mask]
        chi_ft = chi[mask]

        # k权重
        chi_weighted = k_ft**kweight * chi_ft

        # Hanning窗函数
        window = np.hanning(len(k_ft))
        chi_windowed = chi_weighted * window

        # 傅里叶变换
        # 创建R空间网格
        dr = 0.02
        r = np.arange(0, 6, dr)

        # 执行FT
        chir = np.zeros(len(r), dtype=complex)
        for i, r_val in enumerate(r):
            integrand = chi_windowed * np.exp(2j * np.pi * k_ft * r_val)
            chir[i] = np.trapz(integrand, k_ft)

        data_group.r = r
        data_group.chir_mag = np.abs(chir)
        data_group.chir_re = np.real(chir)
        data_group.chir_im = np.imag(chir)

        print(f"[OK] 使用基础方法完成傅里叶变换")
        print(f"  - R范围: {r.min():.2f} - {r.max():.2f} Å")

    def plot_stage1_raw(self, data_group, output_dir='output/figures/generic-xafs-analysis'):
        """
        绘制阶段一：原始μ(E)谱图
        """
        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(data_group.energy_calibrated, data_group.mu, 'b-', linewidth=2)
        ax.set_xlabel('Energy (eV)', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'$\mu$(E)', fontsize=13, fontweight='bold')
        ax.set_title(f'Stage 1: Raw Absorption Spectrum - {data_group.filename}',
                    fontsize=14, fontweight='bold', pad=10)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.tick_params(axis='both', which='major', direction='in',
                      top=True, right=True, length=5, width=1.5)

        filename = f"stage1_raw_{os.path.splitext(data_group.filename)[0]}"
        filepath = os.path.join(output_dir, f"{filename}.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 阶段一谱图已保存: {filepath}")

    def plot_stage2_normalized(self, data_group, output_dir='output/figures/generic-xafs-analysis'):
        """
        绘制阶段二：归一化XANES谱图
        """
        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(data_group.energy_calibrated, data_group.norm, 'r-', linewidth=2)
        ax.axvline(data_group.e0, color='green', linestyle='--', linewidth=2,
                  label=f'$E_0$ = {data_group.e0:.2f} eV')
        ax.set_xlabel('Energy (eV)', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'Normalized $\mu$(E)', fontsize=13, fontweight='bold')
        ax.set_title(f'Stage 2: Normalized XANES - {data_group.filename}',
                    fontsize=14, fontweight='bold', pad=10)
        ax.legend(fontsize=11, loc='best', frameon=True, edgecolor='black')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.tick_params(axis='both', which='major', direction='in',
                      top=True, right=True, length=5, width=1.5)

        filename = f"stage2_normalized_{os.path.splitext(data_group.filename)[0]}"
        filepath = os.path.join(output_dir, f"{filename}.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 阶段二谱图已保存: {filepath}")

    def plot_stage3_xanes_comparison(self, output_dir='output/figures/generic-xafs-analysis'):
        """
        绘制阶段三：XANES对比谱图（所有数据）
        """
        if len(self.data_groups) == 0:
            print("[WARNING] 没有数据可绘制")
            return

        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 7))

        # 使用更专业的配色方案
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        for i, data_group in enumerate(self.data_groups):
            label = f"{os.path.splitext(data_group.filename)[0]} ($E_0$={data_group.e0:.2f} eV)"
            ax.plot(data_group.energy_calibrated, data_group.norm,
                   linewidth=2.5, color=colors[i % len(colors)], label=label, alpha=0.9)
            ax.axvline(data_group.e0, color=colors[i % len(colors)], linestyle=':',
                      linewidth=1.5, alpha=0.6)

        ax.set_xlabel('Energy (eV)', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'Normalized $\mu$(E)', fontsize=13, fontweight='bold')
        ax.set_title(f'Stage 3: {self.edge_name} XANES Comparison',
                    fontsize=14, fontweight='bold', pad=10)
        ax.legend(fontsize=10, loc='best', frameon=True, edgecolor='black',
                 fancybox=False, shadow=False)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.tick_params(axis='both', which='major', direction='in',
                      top=True, right=True, length=5, width=1.5)

        filepath = os.path.join(output_dir, f"stage3_xanes_comparison_{self.element}.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 阶段三对比谱图已保存: {filepath}")

    def plot_stage3_xanes_zoomed(self, output_dir='output/figures/generic-xafs-analysis'):
        """
        绘制阶段三b：吸收边近邻区域的放大对比谱图（E₀ ± 50 eV）
        """
        if len(self.data_groups) == 0:
            print("[WARNING] 没有数据可绘制")
            return

        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 7))

        # 使用更专业的配色方案
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        # 计算所有样品E₀的平均值作为中心
        e0_center = np.mean([dg.e0 for dg in self.data_groups])
        e_min = e0_center - 50
        e_max = e0_center + 50

        for i, data_group in enumerate(self.data_groups):
            # 只绘制E₀ ± 50 eV范围内的数据
            mask = (data_group.energy_calibrated >= e_min) & (data_group.energy_calibrated <= e_max)

            label = f"{os.path.splitext(data_group.filename)[0]} ($E_0$={data_group.e0:.2f} eV)"
            ax.plot(data_group.energy_calibrated[mask], data_group.norm[mask],
                   linewidth=2.5, color=colors[i % len(colors)], label=label, alpha=0.9)
            ax.axvline(data_group.e0, color=colors[i % len(colors)], linestyle=':',
                      linewidth=1.5, alpha=0.6)

        ax.set_xlabel('Energy (eV)', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'Normalized $\mu$(E)', fontsize=13, fontweight='bold')
        ax.set_title(f'Stage 3b: {self.edge_name} XANES Near-Edge Region ($E_0$ ± 50 eV)',
                    fontsize=14, fontweight='bold', pad=10)
        ax.legend(fontsize=10, loc='best', frameon=True, edgecolor='black',
                 fancybox=False, shadow=False)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.tick_params(axis='both', which='major', direction='in',
                      top=True, right=True, length=5, width=1.5)
        ax.set_xlim(e_min, e_max)

        filepath = os.path.join(output_dir, f"stage3b_xanes_zoomed_{self.element}.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 阶段三b放大谱图已保存: {filepath}")

    def plot_stage4_k_space(self, output_dir='output/figures/generic-xafs-analysis'):
        """
        绘制阶段四：K空间对比谱图
        """
        if len(self.data_groups) == 0:
            print("[WARNING] 没有数据可绘制")
            return

        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 7))

        # 使用更专业的配色方案
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        for i, data_group in enumerate(self.data_groups):
            if hasattr(data_group, 'k') and hasattr(data_group, 'chi'):
                k = data_group.k
                kweight = data_group.kweight if hasattr(data_group, 'kweight') else 2
                chi_weighted = k**kweight * data_group.chi

                label = os.path.splitext(data_group.filename)[0]
                ax.plot(k, chi_weighted, linewidth=2.5, color=colors[i % len(colors)],
                       label=label, alpha=0.9)

        ax.set_xlabel(r'$k$ (Å$^{-1}$)', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'$k^2\chi(k)$ (Å$^{-2}$)', fontsize=13, fontweight='bold')
        ax.set_title(f'Stage 4: {self.edge_name} $k$-Space Comparison',
                    fontsize=14, fontweight='bold', pad=10)
        ax.legend(fontsize=10, loc='best', frameon=True, edgecolor='black',
                 fancybox=False, shadow=False)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.tick_params(axis='both', which='major', direction='in',
                      top=True, right=True, length=5, width=1.5)
        ax.set_xlim(0, 14)  # 设置k空间范围为0-14 Å⁻¹

        filepath = os.path.join(output_dir, f"stage4_k_space_{self.element}.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 阶段四K空间谱图已保存: {filepath}")

    def plot_stage5_r_space(self, output_dir='output/figures/generic-xafs-analysis'):
        """
        绘制阶段五：R空间对比谱图
        """
        if len(self.data_groups) == 0:
            print("[WARNING] 没有数据可绘制")
            return

        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 7))

        # 使用更专业的配色方案
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        for i, data_group in enumerate(self.data_groups):
            if hasattr(data_group, 'r') and hasattr(data_group, 'chir_mag'):
                label = os.path.splitext(data_group.filename)[0]
                ax.plot(data_group.r, data_group.chir_mag,
                       linewidth=2.5, color=colors[i % len(colors)], label=label, alpha=0.9)

        ax.set_xlabel(r'$R$ (Å)', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'|$\chi(R)$| (Å$^{-3}$)', fontsize=13, fontweight='bold')
        ax.set_title(f'Stage 5: {self.edge_name} $R$-Space Comparison',
                    fontsize=14, fontweight='bold', pad=10)
        ax.legend(fontsize=10, loc='best', frameon=True, edgecolor='black',
                 fancybox=False, shadow=False)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.tick_params(axis='both', which='major', direction='in',
                      top=True, right=True, length=5, width=1.5)
        ax.set_xlim(0, 6)

        filepath = os.path.join(output_dir, f"stage5_r_space_{self.element}.png")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 阶段五R空间谱图已保存: {filepath}")

    def _get_narrative_groups(self):
        groups = [dg for dg in self.data_groups if hasattr(dg, 'e0')]
        non_foil_groups = [dg for dg in groups if 'foil' not in dg.filename.lower()]
        candidate_groups = non_foil_groups if len(non_foil_groups) > 0 else groups
        if len(candidate_groups) <= 1:
            return candidate_groups
        sorted_groups = sorted(candidate_groups, key=lambda dg: dg.e0)
        energy_threshold = 50.0
        clusters = [[sorted_groups[0]]]
        for dg in sorted_groups[1:]:
            if abs(dg.e0 - clusters[-1][-1].e0) <= energy_threshold:
                clusters[-1].append(dg)
            else:
                clusters.append([dg])
        best_cluster = max(clusters, key=lambda c: len(c))
        return best_cluster

    def _get_report_samples(self):
        groups = [dg for dg in self.data_groups if hasattr(dg, 'e0')]
        non_foil_groups = [dg for dg in groups if 'foil' not in dg.filename.lower()]
        return non_foil_groups if len(non_foil_groups) > 0 else groups

    def _collect_k_space_quality_records(self, groups):
        quality_records = []
        for dg in groups:
            if not hasattr(dg, 'k') or not hasattr(dg, 'chi') or len(dg.k) < 10:
                continue
            k = np.asarray(dg.k, dtype=float)
            chi = np.asarray(dg.chi, dtype=float)
            kweight = dg.kweight if hasattr(dg, 'kweight') else 2

            valid_mask = k < 12.0
            if np.sum(valid_mask) < 10:
                continue
            k_eval = k[valid_mask]
            chi_eval = chi[valid_mask]
            oscillation = (k_eval ** kweight) * chi_eval

            signal_mask = (k_eval >= 3.0) & (k_eval <= 9.0)
            if np.sum(signal_mask) < 5:
                fallback_signal_mask = k_eval <= 9.0
                signal_mask = fallback_signal_mask if np.sum(fallback_signal_mask) >= 5 else np.ones_like(k_eval, dtype=bool)
            signal_osc = oscillation[signal_mask]
            rms_signal = float(np.sqrt(np.mean(signal_osc ** 2)))

            noise_mask = (k_eval > 9.0) & (k_eval < 12.0)
            if np.sum(noise_mask) < 5:
                n_tail = max(5, int(0.2 * len(oscillation)))
                tail_osc = oscillation[-n_tail:]
            else:
                tail_osc = oscillation[noise_mask]
            rms_noise = float(np.sqrt(np.mean((tail_osc - np.mean(tail_osc)) ** 2)))
            snr = rms_signal / (rms_noise + 1e-12)
            sample_name = os.path.splitext(dg.filename)[0]
            quality_records.append({
                "sample_name": sample_name,
                "snr": snr,
                "high_k_rms": rms_noise
            })
        return quality_records

    def _get_low_quality_sample_names(self, quality_records):
        if len(quality_records) == 0:
            return set()
        high_k_rms_values = [rec["high_k_rms"] for rec in quality_records]
        high_k_rms_threshold = float(np.percentile(high_k_rms_values, 75))
        low_quality_records = [
            rec for rec in quality_records
            if rec["snr"] < 1.2 and rec["high_k_rms"] >= high_k_rms_threshold
        ]
        return {rec["sample_name"] for rec in low_quality_records}

    def _extract_e_space_narrative(self, groups):
        if len(groups) == 0:
            return "", "", False, [], [], ""
        sorted_groups = sorted(groups, key=lambda dg: dg.e0)
        sorted_names = [os.path.splitext(dg.filename)[0] for dg in sorted_groups]
        e0_entries = [f"{os.path.splitext(dg.filename)[0]}(E0={dg.e0:.2f} eV)" for dg in sorted_groups]
        if len(sorted_names) == 1:
            order_text = sorted_names[0]
            comparable = False
        else:
            order_text = " < ".join(sorted_names)
            comparable = True
        edge_text = self.edge_name
        foil_candidates = [
            dg for dg in self.data_groups
            if hasattr(dg, 'e0') and 'foil' in dg.filename.lower()
        ]
        relation_clauses = []
        ref_name = ""
        if len(foil_candidates) > 0:
            group_mean_e0 = float(np.mean([dg.e0 for dg in sorted_groups]))
            ref_foil = min(foil_candidates, key=lambda dg: abs(dg.e0 - group_mean_e0))
            ref_name = os.path.splitext(ref_foil.filename)[0]
            ref_e0 = float(ref_foil.e0)
            for dg in sorted_groups:
                delta_e0 = float(dg.e0 - ref_e0)
                abs_delta = abs(delta_e0)
                if abs_delta < 0.3:
                    relation_text = "接近"
                elif abs_delta < 1.5:
                    relation_text = "略大于" if delta_e0 > 0 else "略小于"
                else:
                    relation_text = "明显高于" if delta_e0 > 0 else "明显低于"
                sample_name = os.path.splitext(dg.filename)[0]
                relation_clauses.append(
                    f"{sample_name}样品中{self.element}的价态{relation_text}{ref_name}(ΔE0={delta_e0:+.2f} eV)"
                )
        return edge_text, order_text, comparable, relation_clauses, e0_entries, ref_name

    def _extract_k_space_quality(self, groups):
        quality_records = self._collect_k_space_quality_records(groups)
        if len(quality_records) == 0:
            return "low", "样品"

        low_quality_names = self._get_low_quality_sample_names(quality_records)
        if len(low_quality_names) == 0:
            return "good", ""

        weak_candidates = [rec for rec in quality_records if rec["sample_name"] in low_quality_names]
        weak_record = min(weak_candidates, key=lambda x: x["snr"])
        weak_sample = weak_record["sample_name"]
        return "low", weak_sample

    def _extract_r_space_peaks(self, groups):
        from scipy.signal import find_peaks
        peak_sentences = []
        for dg in groups:
            if not hasattr(dg, 'r') or not hasattr(dg, 'chir_mag'):
                continue
            r = np.asarray(dg.r, dtype=float)
            mag = np.asarray(dg.chir_mag, dtype=float)
            if len(r) < 10 or len(mag) < 10:
                continue
            max_mag = float(np.max(mag))
            if max_mag <= 0:
                continue
            peak_indices, _ = find_peaks(mag, prominence=max_mag * 0.1)
            if len(peak_indices) == 0:
                continue
            sorted_peaks = sorted(peak_indices, key=lambda idx: mag[idx], reverse=True)[:3]
            sorted_peaks = sorted(sorted_peaks, key=lambda idx: r[idx])
            peak_values = [f"{r[idx]:.2f} Å" for idx in sorted_peaks]
            sample_name = os.path.splitext(dg.filename)[0]
            peak_sentences.append(
                f"编号{sample_name}样品在{('、'.join(peak_values))}附近存在明显配位峰（表观峰位）"
            )
        return peak_sentences

    def _generate_auto_interpretation_text(self):
        groups = self._get_narrative_groups()
        edge_text, order_text, comparable, relation_clauses, e0_entries, _ = self._extract_e_space_narrative(groups)
        k_quality_status, weak_sample = self._extract_k_space_quality(groups)
        r_peak_sentences = self._extract_r_space_peaks(groups)

        if edge_text == "":
            return ""

        e_body = (
            f"E空间图中简单分析平均价态范围，仅供参考，{edge_text}一般根据吸收边位置分析对比价态，"
            "吸收边越偏向高能侧可能价态越大，可以看出，"
        )
        if len(relation_clauses) > 0:
            e_body += "，".join(relation_clauses) + "；"
            if comparable:
                e_body += f"各样品价态由低到高依次可能为：{order_text}。"
        else:
            if comparable:
                e_body += "同组样品E0排序如下：" + "、".join(e0_entries) + "；"
                e_body += f"各样品价态由低到高依次可能为：{order_text}。"
            elif len(e0_entries) == 1:
                e_body += f"{e0_entries[0]}。"
        e_paragraph = (
            "E空间（价态分析）\n"
            + e_body
            + "\n注意：如果标样为和样品的非同批次测试标样，和样品的价态对比可能不准，仅供参考。"
        )

        if k_quality_status == "good":
            k_paragraph = (
                "K空间（数据质量判断）\n"
                "k空间主要用来判断数据质量，从 k 空间看，样品数据曲线整体震荡平滑规律，数据质量良好。"
            )
        else:
            weak_sample_label = weak_sample if weak_sample else "样品"
            k_paragraph = (
                "K空间（数据质量判断）\n"
                f"k空间主要用来判断数据质量，从 k 空间看，整体震荡规律尚可，编号 {weak_sample_label} 样品在较高 k 端区域信号弱化较明显，建议结合实际样品情况综合判断。"
            )

        if len(r_peak_sentences) == 0:
            r_main = "根据 R 空间图可初步观察配位壳层分布，当前样品峰位特征不明显。"
        else:
            r_main = "根据 R 空间图可初步观察配位壳层分布，" + "，".join(r_peak_sentences) + "。"

        r_paragraph = (
            "R空间（配位结构分析）\n"
            + r_main
            + "注意：R 空间图谱中的峰位为表观值，受相移影响，实际配位距离需经 EXAFS 拟合后才能确定，"
            + "具体配位类型请结合样品实际结构及相关文献进行分析。"
        )

        closing = "综合说明：以上分析仅供参考，具体分析描述请结合样品自身情况和其他相关表征及相关参考文献。"
        return e_paragraph + "\n\n" + k_paragraph + "\n\n" + r_paragraph + "\n\n" + closing

    def _collect_stage_figure_paths(self, output_dir):
        figures = {
            "stage1": [],
            "stage2": [],
            "stage3": None,
            "stage3b": None,
            "stage4": None,
            "stage5": None,
        }

        stage1_seen = set()
        stage2_seen = set()
        for dg in self.data_groups:
            base_name = os.path.splitext(dg.filename)[0]
            stage1_path = os.path.join(output_dir, f"stage1_raw_{base_name}.png")
            stage2_path = os.path.join(output_dir, f"stage2_normalized_{base_name}.png")
            if os.path.exists(stage1_path) and stage1_path not in stage1_seen:
                figures["stage1"].append(stage1_path)
                stage1_seen.add(stage1_path)
            if os.path.exists(stage2_path) and stage2_path not in stage2_seen:
                figures["stage2"].append(stage2_path)
                stage2_seen.add(stage2_path)

        stage3_path = os.path.join(output_dir, f"stage3_xanes_comparison_{self.element}.png")
        stage3b_path = os.path.join(output_dir, f"stage3b_xanes_zoomed_{self.element}.png")
        stage4_path = os.path.join(output_dir, f"stage4_k_space_{self.element}.png")
        stage5_path = os.path.join(output_dir, f"stage5_r_space_{self.element}.png")
        figures["stage3"] = stage3_path if os.path.exists(stage3_path) else None
        figures["stage3b"] = stage3b_path if os.path.exists(stage3b_path) else None
        figures["stage4"] = stage4_path if os.path.exists(stage4_path) else None
        figures["stage5"] = stage5_path if os.path.exists(stage5_path) else None
        return figures

    def _build_group_report_payload(self, output_dir, text_report_path):
        report_samples = self._get_report_samples()
        edge_text, order_text, comparable, relation_clauses, e0_entries, _ = self._extract_e_space_narrative(report_samples)
        k_quality_status, weak_sample = self._extract_k_space_quality(report_samples)
        k_quality_records = self._collect_k_space_quality_records(report_samples)
        low_quality_names = self._get_low_quality_sample_names(k_quality_records)
        r_peak_sentences = self._extract_r_space_peaks(report_samples)

        e0_table = []
        for dg in sorted(report_samples, key=lambda item: item.e0):
            e0_table.append({
                "sample_name": os.path.splitext(dg.filename)[0],
                "e0": float(dg.e0)
            })

        return {
            "edge_name": edge_text if edge_text else self.edge_name,
            "element": self.element,
            "edge": self.edge,
            "sample_names": [os.path.splitext(dg.filename)[0] for dg in report_samples],
            "e0_table": e0_table,
            "order_text": order_text if comparable else "",
            "relation_clauses": relation_clauses,
            "k_quality_status": k_quality_status,
            "weak_sample": weak_sample,
            "k_quality_records": k_quality_records,
            "low_quality_names": low_quality_names,
            "r_peak_sentences": r_peak_sentences,
            "interpretation_text": self._generate_auto_interpretation_text(),
            "figures": self._collect_stage_figure_paths(output_dir),
            "output_dir": output_dir,
            "text_report_path": text_report_path,
        }

    def _to_abs_markdown_path(self, filepath):
        return Path(filepath).resolve().as_posix()

    def generate_combined_markdown_report(self, group_payloads, data_dir, report_dir):
        from datetime import datetime

        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_path = os.path.join(report_dir, f"xafs_combined_report_{timestamp}.report.md")

        total_samples = sum(len(payload["sample_names"]) for payload in group_payloads)
        lines = [
            "# XAFS 合并分析报告",
            "",
            "## 结果",
            "",
            f"- 数据目录：`{self._to_abs_markdown_path(data_dir)}`",
            f"- 有效样品数：{total_samples}",
            f"- 分组数量：{len(group_payloads)}",
            "",
        ]

        key_figure_paths = []

        for idx, payload in enumerate(group_payloads, 1):
            lines.extend([
                f"### 第 {idx} 组：{payload['edge_name']}",
                "",
                f"- 样品数量：{len(payload['sample_names'])}",
                f"- 样品列表：{', '.join(payload['sample_names']) if payload['sample_names'] else '无'}",
                "",
                "#### E 空间分析",
                "",
            ])

            if payload["e0_table"]:
                lines.extend([
                    "| 样品 | E0 (eV) |",
                    "| --- | ---: |",
                ])
                for row in payload["e0_table"]:
                    lines.append(f"| {row['sample_name']} | {row['e0']:.2f} |")
                lines.append("")
            else:
                lines.extend(["- 未提取到可用的 E0 数值。", ""])

            if payload["relation_clauses"]:
                lines.append("- 相对价态趋势线索：")
                for clause in payload["relation_clauses"]:
                    lines.append(f"  - {clause}")
                lines.append("")
            elif payload["order_text"]:
                lines.extend([f"- 相对 E0 排序：{payload['order_text']}", ""])

            lines.extend([
                "#### k 空间数据质量",
                "",
            ])
            if payload["k_quality_records"]:
                lines.extend([
                    "| 样品 | SNR | 高 k 端 RMS | 质量标签 |",
                    "| --- | ---: | ---: | --- |",
                ])
                for row in payload["k_quality_records"]:
                    quality_label = "低 SNR + 高噪声尾部" if row["sample_name"] in payload["low_quality_names"] else "振荡质量可接受"
                    lines.append(
                        f"| {row['sample_name']} | {row['snr']:.2f} | {row['high_k_rms']:.4f} | {quality_label} |"
                    )
                lines.append("")
            else:
                lines.extend(["- 未提取到有效的 k 空间质量指标。", ""])

            if payload["k_quality_status"] == "low":
                lines.extend([f"- 需重点关注的低质量样品：{payload['weak_sample']}", ""])

            lines.extend([
                "#### R 空间表观峰位",
                "",
            ])
            if payload["r_peak_sentences"]:
                for sentence in payload["r_peak_sentences"]:
                    lines.append(f"- {sentence}")
            else:
                lines.append("- 未能稳健识别主导表观峰位。")
            lines.append("")

            lines.extend([
                "#### 图谱",
                "",
                "##### Stage 1 - 原始 E 空间",
            ])
            if payload["figures"]["stage1"]:
                for fig_path in payload["figures"]["stage1"]:
                    lines.append(f"![{Path(fig_path).stem}]({self._to_abs_markdown_path(fig_path)})")
                    if len(key_figure_paths) < 10:
                        key_figure_paths.append(fig_path)
            else:
                lines.append("- 未生成 Stage 1 图。")
            lines.append("")

            lines.append("##### Stage 2 - 归一化 E 空间")
            if payload["figures"]["stage2"]:
                for fig_path in payload["figures"]["stage2"]:
                    lines.append(f"![{Path(fig_path).stem}]({self._to_abs_markdown_path(fig_path)})")
            else:
                lines.append("- 未生成 Stage 2 图。")
            lines.append("")

            for stage_key, stage_title in [
                ("stage3", "Stage 3 - XANES 对比"),
                ("stage3b", "Stage 3b - XANES 放大图"),
                ("stage4", "Stage 4 - k 空间对比"),
                ("stage5", "Stage 5 - R 空间对比"),
            ]:
                lines.append(f"##### {stage_title}")
                fig_path = payload["figures"][stage_key]
                if fig_path:
                    lines.append(f"![{Path(fig_path).stem}]({self._to_abs_markdown_path(fig_path)})")
                    key_figure_paths.append(fig_path)
                else:
                    lines.append(f"- 未找到 {stage_title} 图。")
                lines.append("")

        lines.extend([
            "## 讨论",
            "",
        ])

        for idx, payload in enumerate(group_payloads, 1):
            lines.append(f"### 第 {idx} 组：{payload['edge_name']}")
            lines.append("")
            interpretation_text = payload["interpretation_text"].strip()
            if interpretation_text:
                lines.extend(interpretation_text.splitlines())
            else:
                lines.append("已提取 E/K/R 空间趋势，但未生成自动解读文本。")
            lines.append("")

        lines.extend([
            "## 结论与边界",
            "",
            "- 基于吸收边位置的价态趋势仅反映相对变化。",
            "- R 空间峰位为表观峰位，受相移效应影响。",
            "- 精确配位距离与壳层归属需结合 EXAFS 拟合确认。",
            "- 涉及机理判断时，建议结合多种表征手段交叉验证。",
            "",
        ])

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return report_path, key_figure_paths

    def generate_analysis_report(self, output_dir='output/figures/generic-xafs-analysis'):
        """
        生成详细的分析报告

        参数:
            output_dir: 输出文件夹路径
        """
        import os
        from datetime import datetime

        os.makedirs(output_dir, exist_ok=True)
        report_file = os.path.join(output_dir, f"XAFS_Analysis_Report_{self.element}.txt")

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"XAFS自动分析报告 - {self.edge_name}\n")
            f.write("="*80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析元素: {self.element}\n")
            f.write(f"吸收边: {self.edge} edge\n")
            f.write(f"样品数量: {len(self.data_groups)}\n")
            f.write("\n")

            # 详细样品信息
            f.write("="*80 + "\n")
            f.write("样品详细信息\n")
            f.write("="*80 + "\n\n")

            for i, dg in enumerate(self.data_groups, 1):
                f.write(f"{i}. {dg.filename}\n")
                f.write("-" * 80 + "\n")
                f.write(f"   数据点数: {len(dg.energy)}\n")
                f.write(f"   能量范围: {dg.energy[0]:.2f} - {dg.energy[-1]:.2f} eV\n")

                if hasattr(dg, 'energy_calibrated'):
                    f.write(f"   校准后能量范围: {dg.energy_calibrated[0]:.2f} - {dg.energy_calibrated[-1]:.2f} eV\n")
                    if hasattr(dg, 'energy_offset'):
                        f.write(f"   能量偏移: {dg.energy_offset:.3f} eV\n")

                if hasattr(dg, 'e0'):
                    f.write(f"   吸收边E0: {dg.e0:.2f} eV\n")

                if hasattr(dg, 'edge_step'):
                    f.write(f"   边跃迁高度: {dg.edge_step:.4f}\n")

                if hasattr(dg, 'k'):
                    f.write(f"   K空间范围: {dg.k[0]:.2f} - {dg.k[-1]:.2f} Angstrom^-1\n")
                    f.write(f"   K空间数据点数: {len(dg.k)}\n")

                if hasattr(dg, 'r'):
                    f.write(f"   R空间范围: {dg.r[0]:.2f} - {dg.r[-1]:.2f} Angstrom\n")
                    f.write(f"   R空间数据点数: {len(dg.r)}\n")
                    if hasattr(dg, 'chir_mag') and len(dg.chir_mag) > 0:
                        max_r_idx = np.argmax(dg.chir_mag)
                        f.write(f"   主峰位置: R = {dg.r[max_r_idx]:.3f} Angstrom\n")
                        f.write(f"   主峰强度: {dg.chir_mag[max_r_idx]:.4f}\n")

                f.write("\n")

            # 对比分析
            f.write("="*80 + "\n")
            f.write("对比分析\n")
            f.write("="*80 + "\n\n")

            # E0对比
            f.write("吸收边E0对比:\n")
            for i, dg in enumerate(self.data_groups, 1):
                if hasattr(dg, 'e0'):
                    f.write(f"  {dg.filename}: {dg.e0:.2f} eV\n")
            f.write("\n")

            # 边跃迁高度对比
            f.write("边跃迁高度对比:\n")
            for i, dg in enumerate(self.data_groups, 1):
                if hasattr(dg, 'edge_step'):
                    f.write(f"  {dg.filename}: {dg.edge_step:.4f}\n")
            f.write("\n")

            # R空间主峰对比
            f.write("R空间主峰位置对比:\n")
            for i, dg in enumerate(self.data_groups, 1):
                if hasattr(dg, 'r') and hasattr(dg, 'chir_mag'):
                    max_r_idx = np.argmax(dg.chir_mag)
                    f.write(f"  {dg.filename}: R = {dg.r[max_r_idx]:.3f} Angstrom, |chi(R)| = {dg.chir_mag[max_r_idx]:.4f}\n")
            f.write("\n")

            # 生成的文件列表
            f.write("="*80 + "\n")
            f.write("生成的文件\n")
            f.write("="*80 + "\n\n")

            f.write("原始谱图 (Stage 1):\n")
            for dg in self.data_groups:
                basename = f"stage1_raw_{os.path.splitext(dg.filename)[0]}"
                f.write(f"  - {basename}.png\n")
            f.write("\n")

            f.write("归一化谱图 (Stage 2):\n")
            for dg in self.data_groups:
                basename = f"stage2_normalized_{os.path.splitext(dg.filename)[0]}"
                f.write(f"  - {basename}.png\n")
            f.write("\n")

            f.write("对比谱图:\n")
            f.write(f"  - stage3_xanes_comparison_{self.element}.png (XANES完整对比)\n")
            f.write(f"  - stage3b_xanes_zoomed_{self.element}.png (XANES放大对比, E0±50eV)\n")
            f.write(f"  - stage4_k_space_{self.element}.png (K空间对比)\n")
            f.write(f"  - stage5_r_space_{self.element}.png (R空间对比)\n")
            f.write("\n")

            interpretation_text = self._generate_auto_interpretation_text()
            if interpretation_text:
                f.write("="*80 + "\n")
                f.write("自动解读（E/K/R空间）\n")
                f.write("="*80 + "\n\n")
                f.write(interpretation_text + "\n\n")

            f.write("="*80 + "\n")
            f.write("分析完成\n")
            f.write("="*80 + "\n")

        print(f"[OK] 分析报告已保存: {report_file}")
        return report_file

    def group_files_by_edge_energy(self, data_files, energy_threshold=50.0):
        """
        根据吸收边能量E0对文件进行分组

        参数:
            data_files: 数据文件路径列表
            energy_threshold: E0能量差异阈值(eV)，小于此值的文件归为同一组

        返回:
            groups: 分组结果列表，每组包含 {'files': [...], 'e0_mean': float, 'element': str, 'edge': str}
        """
        print(f"\n{'='*60}")
        print(f"预扫描文件，根据E0能量进行分组")
        print(f"{'='*60}")

        # 第一步：提取每个文件的E0值
        file_e0_list = []
        for filepath in data_files:
            try:
                # 读取数据
                data_group = self.read_data(filepath)

                # 计算E0（使用一阶导数最大值）
                derivative = np.gradient(data_group.mu, data_group.energy)
                e0 = data_group.energy[np.argmax(derivative)]

                file_e0_list.append({
                    'filepath': filepath,
                    'filename': os.path.basename(filepath),
                    'e0': e0
                })
                print(f"  {os.path.basename(filepath):40s} E0 = {e0:8.2f} eV")

            except Exception as e:
                print(f"  [WARNING] 无法读取文件 {os.path.basename(filepath)}: {e}")
                continue

        if not file_e0_list:
            print("[ERROR] 没有成功读取任何文件")
            return []

        # 第二步：基于E0值进行聚类分组
        print(f"\n使用能量阈值 {energy_threshold} eV 进行分组...")

        groups = []
        used_indices = set()

        for i, file_info in enumerate(file_e0_list):
            if i in used_indices:
                continue

            # 创建新组
            group_files = [file_info]
            used_indices.add(i)

            # 查找E0接近的其他文件
            for j, other_info in enumerate(file_e0_list):
                if j in used_indices:
                    continue

                if abs(file_info['e0'] - other_info['e0']) <= energy_threshold:
                    group_files.append(other_info)
                    used_indices.add(j)

            # 计算组的平均E0
            e0_values = [f['e0'] for f in group_files]
            e0_mean = np.mean(e0_values)
            e0_std = np.std(e0_values)

            # 自动检测元素和边类型
            detected_element = self._detect_element_from_edge(e0_mean)
            detected_edge = None

            if detected_element:
                detected_edge = self.detect_edge_type(detected_element, e0_mean)

            groups.append({
                'files': [f['filepath'] for f in group_files],
                'filenames': [f['filename'] for f in group_files],
                'e0_mean': e0_mean,
                'e0_std': e0_std,
                'e0_range': (min(e0_values), max(e0_values)),
                'element': detected_element if detected_element else 'Unknown',
                'edge': detected_edge if detected_edge else 'K'
            })

        # 第三步：输出分组结果
        print(f"\n{'='*60}")
        print(f"分组结果: 共 {len(groups)} 组")
        print(f"{'='*60}")

        for idx, group in enumerate(groups, 1):
            print(f"\n组 {idx}: {group['element']} {group['edge']}-edge")
            print(f"  平均E0: {group['e0_mean']:.2f} ± {group['e0_std']:.2f} eV")
            print(f"  E0范围: {group['e0_range'][0]:.2f} - {group['e0_range'][1]:.2f} eV")
            print(f"  文件数量: {len(group['files'])}")
            for filename in group['filenames']:
                print(f"    - {filename}")

        return groups

    def _is_likely_numeric_text_file(self, filepath):
        if not os.path.isfile(filepath):
            return False
        try:
            if os.path.getsize(filepath) == 0:
                return False
        except OSError:
            return False
        encodings = ["utf-8", "gbk", "latin-1"]
        lines = []
        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding, errors="strict") as f:
                    for raw_line in f:
                        line = raw_line.strip()
                        if line:
                            lines.append(line)
                        if len(lines) >= 30:
                            break
                break
            except Exception:
                lines = []
                continue
        if len(lines) < 3:
            return False
        import re
        numeric_lines = 0
        for line in lines:
            tokens = [t for t in re.split(r"[\s,;]+", line) if t]
            if len(tokens) < 2:
                continue
            valid_count = 0
            for token in tokens:
                try:
                    float(token)
                    valid_count += 1
                except ValueError:
                    continue
            if valid_count >= 2 and valid_count / max(len(tokens), 1) >= 0.6:
                numeric_lines += 1
        return numeric_lines >= max(3, int(len(lines) * 0.5))

    def process_all_files(self, data_dir, output_dir='output/figures/generic-xafs-analysis', auto_group=True, energy_threshold=50.0, report_dir=None):
        """
        处理文件夹中的所有XAFS数据文件

        参数:
            data_dir: 数据文件夹路径
            output_dir: 输出文件夹路径
            auto_group: 是否自动根据E0分组（默认True）
            energy_threshold: E0能量差异阈值(eV)，用于分组
            report_dir: 合并Markdown报告输出目录
        """
        print(f"\n{'#'*60}")
        print(f"# 开始XAFS全自动分析流程")
        print(f"# 数据目录: {data_dir}")
        print(f"# 自动分组: {'启用' if auto_group else '禁用'}")
        print(f"{'#'*60}")

        # ��取所有数据文件
        data_files = []
        reference_files = []

        valid_extensions = {'.prj', '.txt', '.dat', '.csv', '.xmu'}
        filtered_files = []
        for file in os.listdir(data_dir):
            filepath = os.path.join(data_dir, file)
            if os.path.isfile(filepath):
                file_ext = os.path.splitext(file)[1].lower()
                accepted = False
                if file_ext in valid_extensions:
                    accepted = True
                elif file_ext == '' and self._is_likely_numeric_text_file(filepath):
                    accepted = True
                    print(f"[INFO] 识别为无扩展名文本数据文件: {file}")
                else:
                    reason = f"不支持的扩展名: '{file_ext}'" if file_ext else "无扩展名且未识别为数值型文本文件"
                    filtered_files.append((file, reason))
                if not accepted:
                    continue
                # 识别参考箔文件
                if 'foil' in file.lower():
                    reference_files.append(filepath)
                else:
                    data_files.append(filepath)

        print(f"\n找到 {len(data_files)} 个样品文件")
        if filtered_files:
            print(f"\n[INFO] 已过滤 {len(filtered_files)} 个文件:")
            for filename, reason in filtered_files:
                print(f"  - {filename} | {reason}")
        if reference_files:
            print(f"找到 {len(reference_files)} 个参考箔文件")
            for ref_file in reference_files:
                print(f"  - {os.path.basename(ref_file)}")

        if len(data_files) == 0:
            raise RuntimeError(f"未识别到可处理的样品文件: {data_dir}")

        # 如果启用自动分组，先对文件进行分组
        group_payloads = []
        if auto_group and len(data_files) > 0:
            groups = self.group_files_by_edge_energy(data_files, energy_threshold)

            if len(groups) == 0:
                print("[ERROR] 分组失败，没有可处理的文件")
                raise RuntimeError(f"分组失败，目录中未形成有效数据组: {data_dir}")

            # 对每一组分别处理
            for group_idx, group in enumerate(groups, 1):
                print(f"\n{'#'*60}")
                print(f"# 处理第 {group_idx}/{len(groups)} 组")
                print(f"# 元素: {group['element']} {group['edge']}-edge")
                print(f"# 文件数: {len(group['files'])}")
                print(f"{'#'*60}")

                resolved_element = group['element']
                resolved_edge = group['edge']
                group_reference = None
                for ref_file in reference_files:
                    try:
                        ref_group = self.read_data(ref_file)
                        derivative = np.gradient(ref_group.mu, ref_group.energy)
                        ref_e0 = ref_group.energy[np.argmax(derivative)]

                        if abs(ref_e0 - group['e0_mean']) <= energy_threshold:
                            group_reference = ref_file
                            detected_element = self._detect_element_from_edge(ref_e0)
                            if detected_element:
                                resolved_element = detected_element
                                detected_edge = self.detect_edge_type(detected_element, ref_e0)
                                if detected_edge:
                                    resolved_edge = detected_edge
                            print(f"\n[INFO] 为该组找到匹配的参考箔: {os.path.basename(ref_file)}")
                            print(f"  参考箔E0: {ref_e0:.2f} eV, 组平均E0: {group['e0_mean']:.2f} eV")
                            break
                    except:
                        continue

                group_output_dir = os.path.join(
                    output_dir,
                    f"Group{group_idx}_{resolved_element}_{resolved_edge}"
                )

                group_analyzer = XAFSAnalyzer(
                    element=resolved_element,
                    edge=resolved_edge,
                    require_larch=self.require_larch
                )

                group_payload = group_analyzer._process_single_group(
                    group['files'],
                    group_reference,
                    group_output_dir
                )
                group_payloads.append(group_payload)

            print(f"\n{'#'*60}")
            print(f"# [OK] 所有组处理完成！")
            print(f"# 结果已保存到: {output_dir}")
            print(f"{'#'*60}\n")

        else:
            # 不启用自动分组，使用原有逻辑处理所有文件
            reference_file = reference_files[0] if reference_files else None
            group_payload = self._process_single_group(data_files, reference_file, output_dir)
            group_payloads.append(group_payload)

        if report_dir is None:
            report_dir = os.path.join("workspace", "reports", os.path.basename(os.path.normpath(data_dir)))
        combined_report_path, key_figure_paths = self.generate_combined_markdown_report(group_payloads, data_dir, report_dir)
        print(f"[OK] 合并Markdown报告已保存: {combined_report_path}")
        if key_figure_paths:
            print("[INFO] 关键图像路径:")
            for fig_path in key_figure_paths[:6]:
                print(f"  - {fig_path}")
        return True

    def _process_single_group(self, data_files, reference_file, output_dir):
        """
        处理单个组的文件（内部方法）

        参数:
            data_files: 数据文件路径列表
            reference_file: 参考箔文件路径（可选）
            output_dir: 输出文件夹路径
        """
        # 处理参考箔（如果有）并计算能量偏移
        reference_group = None
        energy_offset = 0.0

        if reference_file:
            reference_group = self.read_data(reference_file)

            # 计算能量偏移量（仅计算一次）
            derivative = np.gradient(reference_group.mu, reference_group.energy)
            e0_measured = reference_group.energy[np.argmax(derivative)]

            # 自动检测元素：根据测量的吸收边能量匹配最接近的标准元素
            detected_element = self._detect_element_from_edge(e0_measured)
            if detected_element:
                self.element = detected_element

            # 判断边类型（K边还是L边），使用Larch内置对照表
            detected_edge = self.detect_edge_type(self.element, e0_measured)
            if detected_edge:
                self.edge = detected_edge
            self.edge_name = f"{self.element} {self.edge}-edge"
            if detected_element:
                print(f"\n[INFO] 自动检测到吸收元素: {self.element} {self.edge}-edge (测量吸收边 ≈ {e0_measured:.1f} eV)")

            # 获取标准吸收边能量（使用Larch数据库或备用数据库）
            e0_standard = self.get_standard_edge_energy(self.element, self.edge)
            if e0_standard is None:
                print(f"[WARNING] 未找到{self.element} {self.edge}边的标准能量，使用测量值")
                e0_standard = e0_measured
            energy_offset = e0_measured - e0_standard

            print(f"[OK] 能量校准参数计算完成")
            print(f"  - 参考箔测量吸收边: {e0_measured:.3f} eV")
            print(f"  - 标准吸收边能量: {e0_standard:.3f} eV")
            print(f"  - 能量偏移量ΔE: {energy_offset:.3f} eV")
            print(f"  - 此偏移量将应用于所有{self.element}样品\n")

            # 校准参考箔自身
            reference_group.energy_calibrated = reference_group.energy - energy_offset
            reference_group.energy_offset = energy_offset

            self.normalize(reference_group)

            # 阶段一和二：也为参考箔生成谱图
            self.plot_stage1_raw(reference_group, output_dir)
            self.plot_stage2_normalized(reference_group, output_dir)

            # 阶段四和五：参考箔也做K空间和R空间转换
            self.extract_exafs(reference_group, rbkg=1.0, kweight=2)
            self.fourier_transform(reference_group, kmin=3.0, kmax=12.0, kweight=2)

            # 将参考箔也添加到数据组列表，用于对比图
            self.data_groups.append(reference_group)

        # 处理所有样品文件（使用统一的能量偏移）
        edge_type_detected = reference_file is not None  # 有参考箔时已在上方完成检测
        for filepath in data_files:
            # 阶段一：读取数据
            data_group = self.read_data(filepath)

            # 应用统一的能量校准
            data_group.energy_calibrated = data_group.energy - energy_offset
            data_group.energy_offset = energy_offset

            if energy_offset != 0.0:
                print(f"[OK] 应用能量校准 (ΔE = {energy_offset:.3f} eV)")
                print(f"  - 校准前能量范围: {data_group.energy[0]:.2f} - {data_group.energy[-1]:.2f} eV")
                print(f"  - 校准后能量范围: {data_group.energy_calibrated[0]:.2f} - {data_group.energy_calibrated[-1]:.2f} eV")

            # 阶段二：归一化
            self.normalize(data_group)

            # 无参考箔时，在第一个样品文件归一化后检测边类型
            if not edge_type_detected:
                detected_edge = self.detect_edge_type(self.element, data_group.e0)
                if detected_edge:
                    self.edge = detected_edge
                    self.edge_name = f"{self.element} {self.edge}-edge"
                edge_type_detected = True

            # 绘制单个文件的谱图
            self.plot_stage1_raw(data_group, output_dir)
            self.plot_stage2_normalized(data_group, output_dir)

            # 阶段四：K空间转换
            self.extract_exafs(data_group, rbkg=1.0, kweight=2)

            # 阶段五：R空间转换
            self.fourier_transform(data_group, kmin=3.0, kmax=12.0, kweight=2)

            # 保存到数据组列表
            self.data_groups.append(data_group)

        # 绘制对比谱图
        print(f"\n{'='*60}")
        print(f"绘制所有对比谱图")
        print(f"{'='*60}")

        self.plot_stage3_xanes_comparison(output_dir)
        self.plot_stage3_xanes_zoomed(output_dir)  # 新增：放大对比谱图
        self.plot_stage4_k_space(output_dir)
        self.plot_stage5_r_space(output_dir)

        # 生成分析报告
        text_report_path = self.generate_analysis_report(output_dir)

        print(f"\n{'#'*60}")
        print(f"# [OK] 分析完成！")
        print(f"# 所有结果已保存到: {output_dir}")
        print(f"{'#'*60}\n")
        return self._build_group_report_payload(output_dir, text_report_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="datasets/generic-xafs-analysis")
    parser.add_argument("--output-dir", default="output/figures/generic-xafs-analysis")
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--element", default="Unknown")
    parser.add_argument("--edge", default="K")
    parser.add_argument("--energy-threshold", type=float, default=50.0)
    parser.add_argument("--no-auto-group", action="store_true")
    parser.add_argument("--allow-numpy-fallback", action="store_true")
    args = parser.parse_args()

    data_dir = str(Path(args.data_dir))
    output_dir = str(Path(args.output_dir))
    require_larch = not args.allow_numpy_fallback
    analyzer = XAFSAnalyzer(element=args.element, edge=args.edge, require_larch=require_larch)
    try:
        analyzer.process_all_files(
            data_dir,
            output_dir,
            auto_group=not args.no_auto_group,
            energy_threshold=args.energy_threshold,
            report_dir=args.report_dir
        )
    except Exception as exc:
        print(f"[ERROR] 分析失败: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
