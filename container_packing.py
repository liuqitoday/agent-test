#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集装箱装载优化计算
3D Bin Packing Problem Solver
"""

import json
from typing import List, Tuple, Dict
from dataclasses import dataclass
import copy

@dataclass
class Box:
    """货物箱子"""
    name: str
    length: float  # 米
    width: float   # 米
    height: float  # 米
    quantity: int
    id: int = 0
    
    def volume(self):
        return self.length * self.width * self.height
    
    def dimensions(self):
        return (self.length, self.width, self.height)
    
    def get_rotations(self):
        """获取所有可能的旋转方向"""
        l, w, h = self.length, self.width, self.height
        rotations = [
            (l, w, h),
            (l, h, w),
            (w, l, h),
            (w, h, l),
            (h, l, w),
            (h, w, l)
        ]
        # 去重
        unique_rotations = []
        for rot in rotations:
            if rot not in unique_rotations:
                unique_rotations.append(rot)
        return unique_rotations

@dataclass
class Position:
    """位置信息"""
    x: float
    y: float
    z: float
    length: float
    width: float
    height: float
    box_name: str
    box_id: int

class Container:
    """集装箱"""
    def __init__(self, length: float, width: float, height: float):
        self.length = length
        self.width = width
        self.height = height
        self.placed_boxes: List[Position] = []
        
    def volume(self):
        return self.length * self.width * self.height
    
    def used_volume(self):
        return sum(p.length * p.width * p.height for p in self.placed_boxes)
    
    def available_volume(self):
        return self.volume() - self.used_volume()
    
    def can_place(self, x: float, y: float, z: float, 
                  length: float, width: float, height: float) -> bool:
        """检查是否可以在指定位置放置货物"""
        # 检查是否超出容器边界
        if x + length > self.length + 0.001:  # 添加小的容差
            return False
        if y + width > self.width + 0.001:
            return False
        if z + height > self.height + 0.001:
            return False
        
        # 检查是否与已放置的货物重叠
        for placed in self.placed_boxes:
            if self._intersects(x, y, z, length, width, height, placed):
                return False
        
        return True
    
    def _intersects(self, x: float, y: float, z: float,
                    length: float, width: float, height: float,
                    placed: Position) -> bool:
        """检查两个箱子是否相交"""
        return not (x + length <= placed.x + 0.001 or
                   placed.x + placed.length <= x + 0.001 or
                   y + width <= placed.y + 0.001 or
                   placed.y + placed.width <= y + 0.001 or
                   z + height <= placed.z + 0.001 or
                   placed.z + placed.height <= z + 0.001)
    
    def find_placement_position(self, box_length: float, box_width: float, 
                               box_height: float) -> Tuple[bool, float, float, float]:
        """寻找可以放置货物的位置"""
        # 尝试的候选位置
        candidate_positions = [(0, 0, 0)]
        
        # 基于已放置的箱子生成候选位置
        for placed in self.placed_boxes:
            # 在已放置箱子的右侧、前侧、上方生成候选位置
            candidate_positions.append((placed.x + placed.length, placed.y, placed.z))
            candidate_positions.append((placed.x, placed.y + placed.width, placed.z))
            candidate_positions.append((placed.x, placed.y, placed.z + placed.height))
        
        # 对候选位置排序：优先选择z值小的（从底部开始），然后是x值小的，最后是y值小的
        candidate_positions.sort(key=lambda p: (p[2], p[0], p[1]))
        
        for x, y, z in candidate_positions:
            if self.can_place(x, y, z, box_length, box_width, box_height):
                return True, x, y, z
        
        return False, 0, 0, 0
    
    def place_box(self, box: Box, box_id: int) -> bool:
        """尝试放置一个箱子"""
        # 尝试所有可能的旋转方向
        for length, width, height in box.get_rotations():
            can_place, x, y, z = self.find_placement_position(length, width, height)
            if can_place:
                position = Position(x, y, z, length, width, height, box.name, box_id)
                self.placed_boxes.append(position)
                return True
        return False

def solve_packing_problem():
    """解决装箱问题"""
    # 集装箱尺寸（米）
    container_length = 11.9
    container_width = 2.34
    container_height = 2.67
    
    container = Container(container_length, container_width, container_height)
    
    print(f"集装箱尺寸: {container_length}m × {container_width}m × {container_height}m")
    print(f"集装箱容积: {container.volume():.2f} 立方米\n")
    
    # 定义货物（转换为米）
    boxes = []
    
    # 1. lyocell：117×70×110cm，7包
    boxes.extend([Box("lyocell", 1.17, 0.70, 1.10, 1, i+1) for i in range(7)])
    
    # 2. viscose：110×110×80cm，2包
    boxes.extend([Box("viscose", 1.10, 1.10, 0.80, 1, i+1) for i in range(2)])
    
    # 3. 仿羽绒：130×88×80cm，8包
    boxes.extend([Box("仿羽绒", 1.30, 0.88, 0.80, 1, i+1) for i in range(8)])
    
    # 5. 面料一：总体积6.5m³，长度2.2m，数量71
    # 估算其他尺寸：假设每件体积约为 6.5/71 ≈ 0.0915 m³
    # 如果长度是2.2m，那么横截面积约为 0.0915/2.2 ≈ 0.0416 m²
    # 假设是方形截面，边长约为 0.204m
    fabric1_volume_per_item = 6.5 / 71
    fabric1_cross_section = fabric1_volume_per_item / 2.2
    fabric1_side = fabric1_cross_section ** 0.5
    boxes.extend([Box("面料一", 2.2, fabric1_side, fabric1_side, 1, i+1) for i in range(71)])
    
    # 6. 面料二：总体积18.89m³，长度2.2m，数量未知
    # 假设每件尺寸与面料一类似
    fabric2_items = int(18.89 / fabric1_volume_per_item)
    boxes.extend([Box("面料二", 2.2, fabric1_side, fabric1_side, 1, i+1) for i in range(fabric2_items)])
    
    print("货物清单:")
    cargo_summary = {}
    for box in boxes:
        if box.name not in cargo_summary:
            cargo_summary[box.name] = {"count": 0, "volume": 0}
        cargo_summary[box.name]["count"] += 1
        cargo_summary[box.name]["volume"] += box.volume()
    
    for name, info in cargo_summary.items():
        print(f"  {name}: {info['count']}件, 总体积 {info['volume']:.2f} m³")
    
    total_volume = sum(info['volume'] for info in cargo_summary.values())
    print(f"\n已知货物总体积: {total_volume:.2f} m³")
    
    # 按体积从大到小排序（启发式策略）
    boxes.sort(key=lambda b: b.volume(), reverse=True)
    
    # 放置货物
    placed_count = 0
    failed_boxes = []
    
    print("\n开始装载货物...")
    for box in boxes:
        if container.place_box(box, box.id):
            placed_count += 1
        else:
            failed_boxes.append(box)
    
    print(f"成功放置: {placed_count}/{len(boxes)} 件货物")
    print(f"已使用体积: {container.used_volume():.2f} m³")
    print(f"剩余体积: {container.available_volume():.2f} m³")
    print(f"空间利用率: {(container.used_volume()/container.volume()*100):.1f}%")
    
    if failed_boxes:
        print(f"\n警告: {len(failed_boxes)} 件货物无法放入:")
        for box in failed_boxes:
            print(f"  - {box.name} (ID: {box.id})")
    
    # 4. 尝试放置HCS：130×88×80cm
    hcs_box = Box("HCS", 1.30, 0.88, 0.80, 1, 0)
    hcs_count = 0
    hcs_id = 1
    
    print(f"\n尝试放置HCS货物 (尺寸: {hcs_box.length}m × {hcs_box.width}m × {hcs_box.height}m, 体积: {hcs_box.volume():.3f} m³)...")
    
    while True:
        hcs_test = Box("HCS", hcs_box.length, hcs_box.width, hcs_box.height, 1, hcs_id)
        if container.place_box(hcs_test, hcs_id):
            hcs_count += 1
            hcs_id += 1
        else:
            break
    
    print(f"\n最多可以放入 HCS: {hcs_count} 包")
    print(f"HCS 总体积: {hcs_count * hcs_box.volume():.2f} m³")
    print(f"\n最终使用体积: {container.used_volume():.2f} m³")
    print(f"最终剩余体积: {container.available_volume():.2f} m³")
    print(f"最终空间利用率: {(container.used_volume()/container.volume()*100):.1f}%")
    
    return container, cargo_summary, hcs_count, failed_boxes

def generate_html_report(container: Container, cargo_summary: Dict, 
                        hcs_count: int, failed_boxes: List[Box]):
    """生成HTML可视化报告"""
    
    # 统计每种货物的放置情况
    placement_summary = {}
    for pos in container.placed_boxes:
        if pos.box_name not in placement_summary:
            placement_summary[pos.box_name] = []
        placement_summary[pos.box_name].append(pos)
    
    # 颜色映射
    colors = {
        "lyocell": "#FF6B6B",
        "viscose": "#4ECDC4",
        "仿羽绒": "#45B7D1",
        "面料一": "#FFA07A",
        "面料二": "#98D8C8",
        "HCS": "#F7DC6F"
    }
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>集装箱装载方案</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
        }}
        
        .summary-card h3 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .summary-card .unit {{
            color: #718096;
            font-size: 0.9em;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-size: 1.8em;
        }}
        
        .cargo-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .cargo-table thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .cargo-table th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .cargo-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .cargo-table tbody tr:hover {{
            background-color: #f7fafc;
        }}
        
        .color-box {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 10px;
            vertical-align: middle;
            border: 1px solid #ddd;
        }}
        
        .highlight {{
            background: #ffd700;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #f39c12;
        }}
        
        .highlight h3 {{
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        .highlight .big-number {{
            font-size: 3em;
            font-weight: bold;
            color: #e67e22;
        }}
        
        .visualization {{
            margin-top: 30px;
            padding: 20px;
            background: #f7fafc;
            border-radius: 10px;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            padding: 8px 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s;
        }}
        
        .detail-table {{
            width: 100%;
            margin-top: 20px;
            font-size: 0.9em;
        }}
        
        .detail-table th {{
            background: #edf2f7;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
        }}
        
        .detail-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .warning {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        .warning h4 {{
            color: #856404;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚢 集装箱装载优化方案</h1>
            <p>Container Loading Optimization Report</p>
        </div>
        
        <div class="content">
            <!-- 关键指标 -->
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>集装箱容积</h3>
                    <div class="value">{container.volume():.2f}</div>
                    <div class="unit">立方米</div>
                </div>
                <div class="summary-card">
                    <h3>已使用体积</h3>
                    <div class="value">{container.used_volume():.2f}</div>
                    <div class="unit">立方米</div>
                </div>
                <div class="summary-card">
                    <h3>剩余体积</h3>
                    <div class="value">{container.available_volume():.2f}</div>
                    <div class="unit">立方米</div>
                </div>
                <div class="summary-card">
                    <h3>空间利用率</h3>
                    <div class="value">{(container.used_volume()/container.volume()*100):.1f}%</div>
                    <div class="unit">利用率</div>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(container.used_volume()/container.volume()*100):.1f}%">
                    {(container.used_volume()/container.volume()*100):.1f}% 已使用
                </div>
            </div>
            
            <!-- HCS 结果高亮 -->
            <div class="highlight">
                <h3>💡 HCS 最大装载量</h3>
                <div class="big-number">{hcs_count} 包</div>
                <p>在装载所有其他货物后，最多可以放入 <strong>{hcs_count}</strong> 包 HCS (每包尺寸: 130×88×80cm)</p>
                <p>HCS 总体积: <strong>{hcs_count * 1.30 * 0.88 * 0.80:.2f}</strong> 立方米</p>
            </div>
            
            <!-- 货物统计 -->
            <div class="section">
                <h2>📦 货物装载统计</h2>
                <table class="cargo-table">
                    <thead>
                        <tr>
                            <th>货物名称</th>
                            <th>单件尺寸 (cm)</th>
                            <th>数量</th>
                            <th>总体积 (m³)</th>
                            <th>占比</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # 添加货物统计行
    for name in sorted(placement_summary.keys()):
        positions = placement_summary[name]
        count = len(positions)
        if count > 0:
            sample = positions[0]
            volume = sum(p.length * p.width * p.height for p in positions)
            percentage = (volume / container.used_volume() * 100) if container.used_volume() > 0 else 0
            color = colors.get(name, "#CCCCCC")
            
            html += f"""
                        <tr>
                            <td>
                                <span class="color-box" style="background-color: {color};"></span>
                                <strong>{name}</strong>
                            </td>
                            <td>{sample.length*100:.0f} × {sample.width*100:.0f} × {sample.height*100:.0f}</td>
                            <td>{count} 包</td>
                            <td>{volume:.2f}</td>
                            <td>{percentage:.1f}%</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
"""
    
    # 如果有无法放入的货物，显示警告
    if failed_boxes:
        html += """
            <div class="warning">
                <h4>⚠️ 警告：部分货物无法放入</h4>
                <p>以下货物由于空间限制无法放入集装箱：</p>
                <ul>
"""
        for box in failed_boxes:
            html += f"                    <li>{box.name} (ID: {box.id})</li>\n"
        html += """
                </ul>
            </div>
"""
    
    # 详细摆放信息
    html += """
            <div class="section">
                <h2>📋 详细摆放信息</h2>
                <p>以下是每个货物在集装箱中的具体位置（坐标单位：米）</p>
"""
    
    for name in sorted(placement_summary.keys()):
        positions = placement_summary[name]
        color = colors.get(name, "#CCCCCC")
        
        html += f"""
                <h3 style="margin-top: 20px; color: {color};">
                    <span class="color-box" style="background-color: {color};"></span>
                    {name} ({len(positions)} 包)
                </h3>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>位置 X</th>
                            <th>位置 Y</th>
                            <th>位置 Z</th>
                            <th>长 (m)</th>
                            <th>宽 (m)</th>
                            <th>高 (m)</th>
                            <th>体积 (m³)</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for pos in sorted(positions, key=lambda p: p.box_id):
            volume = pos.length * pos.width * pos.height
            html += f"""
                        <tr>
                            <td>{pos.box_id}</td>
                            <td>{pos.x:.2f}</td>
                            <td>{pos.y:.2f}</td>
                            <td>{pos.z:.2f}</td>
                            <td>{pos.length:.2f}</td>
                            <td>{pos.width:.2f}</td>
                            <td>{pos.height:.2f}</td>
                            <td>{volume:.3f}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
"""
    
    html += """
            </div>
            
            <!-- 图例 -->
            <div class="visualization">
                <h3>🎨 颜色图例</h3>
                <div class="legend">
"""
    
    for name, color in colors.items():
        if name in placement_summary or name == "HCS":
            count = len(placement_summary.get(name, [])) if name != "HCS" else hcs_count
            if count > 0 or name == "HCS":
                html += f"""
                    <div class="legend-item">
                        <span class="color-box" style="background-color: {color};"></span>
                        <span>{name}</span>
                    </div>
"""
    
    html += """
                </div>
            </div>
            
            <div class="section" style="margin-top: 40px; padding: 20px; background: #edf2f7; border-radius: 10px;">
                <h3>📝 说明</h3>
                <ul style="line-height: 1.8; color: #4a5568;">
                    <li>集装箱尺寸：11.9m (长) × 2.34m (宽) × 2.67m (高)</li>
                    <li>装载算法：采用启发式3D装箱算法（First Fit Decreasing）</li>
                    <li>坐标系统：原点(0,0,0)位于集装箱左下后角</li>
                    <li>面料一和面料二：由于缺少完整尺寸信息，根据总体积和长度进行估算</li>
                    <li>货物可能会自动旋转以获得最佳摆放</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    print("=" * 60)
    print("集装箱装载优化计算程序")
    print("=" * 60)
    print()
    
    # 执行装箱计算
    container, cargo_summary, hcs_count, failed_boxes = solve_packing_problem()
    
    # 生成HTML报告
    print("\n生成HTML报告...")
    html_content = generate_html_report(container, cargo_summary, hcs_count, failed_boxes)
    
    with open("/workspace/container_loading_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML报告已生成: container_loading_report.html")
    print("\n" + "=" * 60)
    print("计算完成！")
    print("=" * 60)
