"""Apply user-authorized first-point zeroing and audit proposed test dimensions.

This script performs data processing and analytical checks, not an FE solver run.
"""
from pathlib import Path
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sample1_analysis'
processed = {}
for name in ['compress', 'strain']:
    raw = json.loads((OUT / f'sample1-{name}-raw.json').read_text())
    a = np.asarray(raw['rows'], dtype=float)
    offset = a[0].copy()
    corrected = a - offset
    np.testing.assert_allclose(corrected + offset, a, atol=1e-12)
    assert (corrected[0] == 0).all()
    peak = int(np.argmax(corrected[:, 1]))
    negative = int(np.sum(corrected[:, 1] < 0))
    payload = {
        'source': raw['source'], 'source_sha256': raw['source_sha256'],
        'stress_unit': 'MPa', 'strain_unit': 'mm/mm',
        'engineering_or_true': 'engineering_assumed',
        'operation': 'Subtract first recorded strain and stress; first point treated as unloaded reference per user instruction.',
        'subtracted_strain': float(offset[0]), 'subtracted_stress_MPa': float(offset[1]),
        'negative_stress_rows_after_zeroing': negative,
        'negative_stress_handling': 'Preserved as measurement noise, not silently clipped.',
        'smoothing': 'none', 'rows': corrected.tolist(),
        'maximum_stress_MPa': float(corrected[peak, 1]),
        'strain_at_maximum_stress': float(corrected[peak, 0]),
        'last_strain': float(corrected[-1, 0]),
        'hardening_candidate_last_row_1based': peak + 1,
        'solver_ready': False,
        'remaining_processing': 'Monotone smoothing and a common near-origin tangent must be checked before material-card use; post-peak tension is not a hardening input.',
    }
    (OUT / f'sample1-{name}-zeroed.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    processed[name] = {k: v for k, v in payload.items() if k != 'rows'}

steel_density = 7.85  # g/cm^3, conventional approximate density for this sizing check
diameter_mm, mass_g, height_m = 10.0, 20.0, 0.2
actual_ball_mass = steel_density * math.pi / 6 * (diameter_mm / 10)**3
equivalent_diameter = 10 * (6 * mass_g / (math.pi * steel_density))**(1 / 3)
g = 9.80665
audit = {
    'status': 'analytical_preflight_only_no_OpenRadioss_Starter_or_Engine_run',
    'specimen_mm': [20, 20, 1], 'density_g_cm3': 1.1, 'poisson_ratio': .49,
    'specimen_mass_g': 20*20*1/1000*1.1,
    'support_confirmed': 'four_edges_clamped_center_unsupported',
    'proposed_clamp_width_mm': 2,
    'proposed_free_window_mm': [16, 16],
    'clamp_width_status': 'modeling_assumption_not_user_measured',
    'requested_impactor': {'diameter_mm': equivalent_diameter, 'mass_g': mass_g,
                          'description': '20 g solid steel sphere; diameter inferred from assumed steel density after user correction.'},
    'assumed_steel_density_g_cm3': steel_density,
    'consistent_10mm_solid_ball_mass_g': actual_ball_mass,
    'consistent_20g_solid_ball_diameter_mm': equivalent_diameter,
    'recommended_impactor': {
        'diameter_mm': equivalent_diameter, 'mass_g': 20,
        'description': 'Solid steel sphere modeled as rigid, with consistent mass and geometry.',
    },
    'drop_height_m': height_m,
    'speed_at_first_contact_m_s': math.sqrt(2*g*height_m),
    'free_fall_time_s': math.sqrt(2*height_m/g),
    'energy_20g_J': mass_g/1000*g*height_m,
    'energy_consistent_10mm_steel_ball_J': actual_ball_mass/1000*g*height_m,
    'strain_control': {
        'definition': 'Principal engineering strains from stretch eigenvalues: epsilon_i=lambda_i-1.',
        'conservative_first_pilot_stretch_range': [.6, 1.4],
        'warning_stretch_range': [.65, 1.35],
        'enforcement': 'Monitor integration-point stretches; stop or reduce load before exceeding the range. Never clip material strain or artificially harden to enforce a cap.',
        'note': 'The tensile upper cap is a conservative user-requested 40% deformation limit, not the tensile test range. Central deflection divided by film thickness is not material compression strain for a suspended film.',
    },
    'recommended_first_pilot': {
        'type': 'displacement_controlled_spherical_indentation',
        'candidate_indenter_displacements_mm': [.1, .2, .3],
        'selection': 'Only retain stages passing local strain and quasi-static checks; extend only if appropriate.',
        'loading': 'Smooth imposed displacement with velocity and acceleration starting at zero; gravity drop is not combined with this loading.',
        'note': 'This is a controlled indentation comparison, not a 20cm drop-impact simulation; striker mass does not determine the quasi-static stress state.',
    },
    'dynamic_followup': {
        'candidate_speeds_m_s': [.1, .3, .5, 1.0, math.sqrt(2*g*height_m)],
        'instruction': 'Sequential pilot ladder only: stop increasing speed when local strains or stability fail. No prediction that any listed speed is safe.',
        'start': 'Small gap above film with downward initial velocity; v=0 at contact without another load does not represent a 20cm drop.',
    },
    'mesh_proposal': {'solid_type': '8-node bricks with near-incompressibility treatment',
                      'thickness_layers_initial': 6,
                      'central_inplane_size_mm_initial': .2,
                      'convergence': 'Refine contact zone and thickness; compare stress fields and reaction force.'},
    'outputs': ['front_stress_map', 'central_section_stress_map'],
    'internal_checks': ['local_strain_range', 'energy_balance', 'contact_penetration', 'mesh_sensitivity'],
    'curve_processing': processed,
}
(OUT / 'sample1-preflight.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
report = f'''# Sample1 尺寸与加载预审

已完成的是数值核算和数据零点处理，尚未进行OpenRadioss Starter检查或Engine求解。

## 已确认及拟用设置

- 样品20×20×1 mm，密度1.1 g/cm³，质量约0.44 g；泊松比0.49。
- 四周夹持、中心悬空已由用户确认。
- 建议初版四周各夹持2 mm，形成16×16 mm自由窗口。夹持宽度是待与实物核对的建模假设。
- 用户已纠正为20 g实心钢球，直径由钢密度推算，不再使用10 mm直径或附加等效质量方案。
- 常用钢密度按7.85 g/cm³估计，20 g实心钢球直径约{equivalent_diameter:.3f} mm，半径约{equivalent_diameter/2:.3f} mm。
- 20 cm自由落高对应接触前速度{audit['speed_at_first_contact_m_s']:.5f} m/s；20 g钢球入射动能{audit['energy_20g_J']*1000:.3f} mJ。

## 尺寸判断

20×20×1 mm可以作为小型夹持薄膜模型。钢球直径约16.95 mm，与样品20 mm总宽度接近。实际接触斑小于球的投影尺寸，因此这不等于球一开始就覆盖整片，也不能仅凭球径大于16 mm自由窗口就判定无法压入。短程试算需检查接触区与夹持区是否相互影响，以及实物夹具是否被钢球直接碰到。若希望比较更大范围的膜内应力扩散，可另做40×40×1 mm对比；不是本次必须新增的试样。

悬空薄膜的中心挠度不等于厚度压缩；中心下挠0.4 mm不表示40%压缩。建议监测积分点主伸长比，首轮保守控制0.6≤lambda_i≤1.4，35%附近预警。40%上限应通过限制加载、停算或降低速度实现，不可对求解器中的应变直接截断或凭空增加刚度。

## 零点处理

按用户确认的仪器偏置，采用首个记录点作为无载参考，分别扣除横纵坐标首值。压缩偏置为(0,0)，拉伸偏置为(0.00019 mm/mm,0.26233 MPa)。原始文件保持不变，归零后数据另存为sample1-*-zeroed.json。拉伸归零后保留{processed['strain']['negative_stress_rows_after_zeroing']}个负应力噪声点，不静默截零。只扣常数不会改变原曲线斜率，所以原点附近的拉压一致性仍要在材料小算例中检查。

## 推荐dry-run顺序

1. 材料单元拉伸与压缩：检查应力符号、体积模量、原点平滑、曲线重现和横向变形。
2. 无损伤球形压入小算例：以平滑位移加载，候选压入量0.1、0.2、0.3 mm，逐步检查局部应变。无需运行完整自由落体。
3. 若只需一定形变的云图，可在选定压入位移结束；这属于受控压入，不应称为20 cm落球结果。
4. 若仍需真实冲击，则从接近样品表面的位置施加向下初速度。候选0.1、0.3、0.5、1.0、1.981 m/s逐级预试，但只有前一级满足应变与稳定性要求时才继续。20 cm落高不能事先保证不超过40%。

Starter只能检查输入和模型定义；必须进行短程Engine运行才能检查接触、局部应变和动态稳定性。

真正的20 cm落球可从20 cm高处以v0=0加重力释放，或在接触前直接赋予约1.981 m/s向下速度。接触位置v0=0且无其他载荷不能产生同等冲击。

## 运行环境状态

本次在FEA目录及当前命令路径中没有发现可调用的OpenRadioss Starter/Engine。不能据此断言机器其他位置没有安装。实际求解尚未执行。
'''
(OUT / 'sample1-preflight.md').write_text(report)
print(json.dumps({k: v for k, v in audit.items() if k != 'curve_processing'}, ensure_ascii=False, indent=2))
