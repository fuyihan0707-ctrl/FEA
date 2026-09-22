"""Plot the unmodified measured curves. This is not finite-element output."""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sample1_analysis'
os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/sample1-mplconfig')
local_deps = Path('/private/tmp/sample1-plot-deps')
if local_deps.exists():
    sys.path.insert(0, str(local_deps))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

font_path = next((p for p in [Path('/System/Library/Fonts/PingFang.ttc'),
                 Path('/System/Library/Fonts/STHeiti Medium.ttc')]
                 if p.exists()), None)
font = FontProperties(fname=font_path) if font_path else FontProperties()
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.unicode_minus': False})

data = {}
for kind in ['compress', 'strain']:
    record = json.loads((OUT / f'sample1-{kind}-raw.json').read_text())
    assert record['strain_unit'] == 'mm/mm' and record['stress_unit'] == 'MPa'
    data[kind] = np.array(record['rows'])
c, t = data['compress'], data['strain']
fig = plt.figure(figsize=(12, 8), facecolor='white')
gs = fig.add_gridspec(2, 2, hspace=0.50, wspace=0.27)
ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, :])
blue, orange = '#176b9b', '#ca691b'
for ax in [ax1, ax2, ax3]:
    ax.grid(alpha=.16)
    ax.set_xlabel('应变 (mm/mm)', fontproperties=font)
    ax.set_ylabel('应力 (MPa)', fontproperties=font)

ax1.plot(c[:, 0], c[:, 1], color=blue, lw=1.7)
ax1.scatter(*c[-1], color=blue, s=22)
ax1.annotate('0.40283, 34.668 MPa', xy=c[-1], xytext=(.13, 30),
             arrowprops={'arrowstyle': '-', 'color': '#708090'}, fontsize=10)
ax1.set_title('A  压缩原始曲线 | 5 mm/s', fontproperties=font, loc='left')
ax1.set_xlim(0, .425); ax1.set_ylim(0, 38)

peak = int(t[:, 1].argmax())
ax2.plot(t[:, 0], t[:, 1], color=orange, lw=1.6)
ax2.axvspan(t[peak, 0], t[-1, 0], alpha=.13, color='#bd2b39')
ax2.scatter(*t[peak], color='#a32834', s=23)
ax2.annotate('峰值 27.519 MPa\n峰后数据保留，未用于硬化拟合', xy=t[peak],
             xytext=(4.0, 26.5), fontproperties=font, fontsize=10,
             arrowprops={'arrowstyle': '-', 'color': '#708090'})
ax2.set_title('B  拉伸原始曲线 | 10 mm/s', fontproperties=font, loc='left')
ax2.set_xlim(0, 16); ax2.set_ylim(0, 32)

for a, color, label in [(c, blue, '压缩（应变、应力均按正值幅度显示）'),
                         (t, orange, '拉伸（未扣除起始应力）')]:
    sub = a[a[:, 0] <= .1]
    ax3.plot(sub[:, 0], sub[:, 1], lw=1.6, color=color, label=label)
ax3.scatter(*t[0], color=orange, s=25)
ax3.annotate('拉伸首点：0.26233 MPa', xy=t[0], xytext=(.021, .29),
             fontproperties=font, fontsize=10,
             arrowprops={'arrowstyle': '-', 'color': '#708090'})
ax3.set_title('C  原点附近检查 | 两条曲线均未平滑或校正', fontproperties=font, loc='left')
ax3.set_xlim(0, .1); ax3.set_ylim(0, 2.9)
ax3.legend(prop=font, loc='upper left', frameon=False)

fig.suptitle('Sample1 拉伸 / 压缩数据检查', fontproperties=font, fontsize=17, y=.985)
fig.text(.5, .935, '密度 1.1 g/cm³ | 泊松比 0.49 | mm/mm 为已确认单位；暂按工程量解释',
         fontproperties=font, fontsize=10, ha='center', color='#44515e')
fig.subplots_adjust(top=.855, bottom=.13)
fig.text(.08, .028, '实验曲线检查图，非有限元结果。压缩终点不代表破坏极限；拉伸峰后降载原因未确认。',
         fontproperties=font, fontsize=10, color='#44515e')
path = OUT / 'sample1-curves.png'
fig.savefig(path, dpi=180)
plt.close(fig)
print(path)
