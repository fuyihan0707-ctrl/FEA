"""Read sample1 RTF tables without changing units, zero points, or curve shapes."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sample1_analysis'
OUT.mkdir(exist_ok=True)
NUMBER = r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[Ee][+-]?\d+)?'
PAIR = re.compile(rf'^\s*({NUMBER})\s+({NUMBER})\s*$')
summary = {
    'status': 'units_confirmed_engineering_definition_assumed_for_preliminary_analysis',
    'density_as_provided': 1.1,
    'density_unit': 'g/cm^3',
    'density_kg_m3': 1100.0,
    'stress_unit': 'MPa',
    'strain_unit': 'mm/mm',
    'engineering_or_true': 'engineering_assumed_not_explicitly_confirmed',
    'poisson_ratio': 0.49,
    'processing': 'Raw row order preserved; no smoothing, zero correction, unit conversion, or truncation.',
    'curves': {},
}
for kind, speed in [('compress', 5.0), ('strain', 10.0)]:
    source = ROOT / f'sample1-{kind}.rtf'
    decoded = subprocess.run(
        ['/usr/bin/textutil', '-convert', 'txt', '-stdout', str(source)],
        check=True, capture_output=True, text=True,
    ).stdout
    rows = []
    for line in decoded.splitlines():
        match = PAIR.fullmatch(line)
        if match:
            rows.append([float(match[1]), float(match[2])])
        elif line.strip() and any(c.isdigit() for c in line) and not line.startswith('应变'):
            raise ValueError(f'Unexpected numerical line: {line!r}')
    a = np.asarray(rows)
    assert a.ndim == 2 and a.shape[1] == 2 and np.isfinite(a).all()
    # Cross-check against numeric rows embedded directly in the source RTF.
    embedded = re.findall(rf'(?m)^\s*({NUMBER})\s+({NUMBER})\s*\\?\s*$', source.read_text())
    np.testing.assert_array_equal(a, np.asarray(embedded, dtype=float))
    peak = int(a[:, 1].argmax())
    info = {
        'source': str(source),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'header': decoded.splitlines()[0],
        'crosshead_speed_mm_s': speed,
        'strain_rate_s_inverse': None,
        'row_count': len(rows),
        'first_point': rows[0],
        'last_point': rows[-1],
        'maximum_stress_point': rows[peak],
        'maximum_stress_row_1based': peak + 1,
        'maximum_recorded_strain_percent': float(100 * a[:, 0].max()),
        'stress_at_selected_strain_MPa': {
            str(x): float(np.interp(x, a[:, 0], a[:, 1]))
            for x in [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4]
            if a[0, 0] <= x <= a[-1, 0]
        },
        'decreasing_strain_steps': int((np.diff(a[:, 0]) < 0).sum()),
        'duplicate_strain_steps': int((np.diff(a[:, 0]) == 0).sum()),
        'initial_linear_fit_sensitivity_raw_units': [],
    }
    for lo, hi in [(0.0, 0.01), (0.01, 0.03), (0.03, 0.05), (0.05, 0.10)]:
        use = (a[:, 0] >= lo) & (a[:, 0] <= hi)
        if use.sum() > 2:
            slope, intercept = np.polyfit(a[use, 0], a[use, 1], 1)
            info['initial_linear_fit_sensitivity_raw_units'].append({
                'strain_window': [lo, hi], 'slope': float(slope),
                'intercept': float(intercept), 'n_points': int(use.sum()),
            })
    summary['curves'][kind] = info
    payload = {**info, 'strain_unit': 'mm/mm', 'stress_unit': 'MPa',
               'engineering_or_true': 'engineering_assumed_not_explicitly_confirmed',
               'columns': ['strain_raw', 'stress_raw'], 'rows': rows}
    (OUT / f'sample1-{kind}-raw.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))

(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
c, t = summary['curves']['compress'], summary['curves']['strain']
report = f'''# Sample1 数据初检

当前状态：应力 MPa、应变 mm/mm、密度 g/cm³ 已确认。初步分析暂按工程应力/工程应变解释，这一定义尚未由用户明确确认；mm/mm 本身仅确定量纲，不区分工程应变与对数应变。尚未生成可运行材料卡，尚未运行有限元冲击计算。

| 数据 | 压缩 | 拉伸 |
|---|---:|---:|
| 数据点数 | {c['row_count']} | {t['row_count']} |
| 加载速度（mm/s，用户提供） | 5 | 10 |
| 最大应变读数 | {c['last_point'][0]} | {t['last_point'][0]} |
| 最大记录应变（%） | {100*c['last_point'][0]:.3f} | {100*t['last_point'][0]:.3f} |
| 最大应力（MPa） | {c['maximum_stress_point'][1]} | {t['maximum_stress_point'][1]} |
| 最大应力对应应变读数 | {c['maximum_stress_point'][0]} | {t['maximum_stress_point'][0]} |

密度：1.1 g/cm³ = 1100 kg/m³；泊松比：0.49。

两份数据的应变均持续增加，没有可识别的卸载段。拉伸末端显著降载，可能涉及断裂或滑移；不能直接作为无损伤硬化曲线使用。峰值位置可以作为候选截断上限，最终截断需结合曲线和实验情况确认。压缩曲线在初始段明显较缓，不能未经检查便将这一段当作仪器空程并删除。

拉伸第一点应力读数为 0.26233，应变读数为 0.00019；目前没有自动扣除预载或修改零点。

当前保留全部数据，没有平滑、截断、外推、单位转换或基线校正。原始RTF数值与系统textutil解码后的表格已逐项比对一致。

两份记录速度分别为压缩5 mm/s、拉伸10 mm/s，不是s⁻¹应变率。压缩初始厚度和拉伸标距可用于换算应变率。简化模型不拟合速率效应。

压缩数据覆盖至40.283%，最大记录应力34.66825 MPa；拉伸数据覆盖至1533.247%，峰值27.51867 MPa，位于1467.395%。压缩测试终点不是已经测出的压缩破坏极限，拉伸末端降载也不能单凭表格确定其物理原因。

## 初始响应与材料输入

1%–3%应变区间内，压缩线性拟合斜率约3.98 MPa，拉伸约16.87 MPa；这些是指定区间的表观斜率，不是已标定的初始弹性模量。压缩0%–1%区间约0.78 MPa，初始段的窗口敏感性较强。拉伸第一点带有0.26233 MPa的非零应力；不能从一个初始读数断定应扣除多少预载。

若使用同一各向同性超弹性模型，零应变附近的拉伸和压缩应有一致的初始切线刚度。当前两条实验曲线不能未经处理直接认定为一套自洽材料模型。后续应采用共同原点附近的平滑拟合并明确拟合误差，或检查加载接触和预载记录。不能任意删除整段压缩初始数据来强行使其一致。

泊松比0.49对应的小应变关系为G0=E0/2.98，K0=E0/0.06；E0尚未标定，当前不虚构唯一K0值。最终K0属于从现有数据得到的建模参数，不要求增加独立实验。

无损伤曲线输入初稿应保留压缩实测范围，对拉伸峰后降载段单独保存而不作为硬化输入；不要向未测得的高压缩区间无依据外推。三维冲击中的主应变不等同于中心挠度除以厚度，是否超出校准范围应结合单元局部变形状态评估。

简化建模：先检查近不可压缩曲线输入模型是否适合；不加入额外速率、滞回或损伤参数。先以实测范围内、未发生破坏的工况为目标。样品几何、球质量/直径/速度和支撑方式尚未确定，不能由材料曲线唯一确定应力云图或接触力。
'''
(OUT / 'sample1-review.md').write_text(report)
print(json.dumps(summary, ensure_ascii=False, indent=2))
