# Motion Path Capture — FrameForge Sliders Panel

## Problem
SolidWorks 的 Motion Path 功能：动画播放过程中追踪选定顶点的运动轨迹，生成 3D 路径曲线。FrameForge 的 Sliders 面板目前没有此功能。

## Design

### Workflow
1. 用户在 Sliders 面板勾选 ☑ Track Points → 进入选点模式
2. 在 3D 视图中多选顶点 → 自动加入追踪列表
3. 点击 ▶ Play 播放动画 → 每帧记录所有已选顶点的坐标到内存
4. 停止后点击 [Generate] → 对每个顶点生成一条 `Part::BSplineCurve` 路径曲线
5. 每次 Generate 创建新对象，旧路径保留

### UI 元素（添加到 Sliders 面板）

```
☐ Track Points  [⟳ Select]        ← 复选框 + 选点按钮
  ├ Body.Shape.Vertex1             ← 已选点列表 (QListWidget)
  ├ Body.Shape.Vertex7
  └ Body.Shape.Vertex12
[✕ Clear Points]  [Generate Path]  ← 操作按钮
```

| 控件 | 类型 | 行为 |
|------|------|------|
| ☐ Track Points | QCheckBox | 勾选后启用选点模式 |
| [⟳ Select] | QPushButton | 调用 `Gui.Selection.clearSelection()` → 提示用户选顶点 |
| 列表 | QListWidget | 显示 `{物体Name}.{VertexX}`，可多选后按 Delete 删除 |
| [✕ Clear Points] | QPushButton | 清空追踪列表和已录数据 |
| [Generate Path] | QPushButton | 根据录制的坐标数据生成路径曲线 |

### 数据流

```
在 SliderPanel.__init__ 新增:
  self._track_points = []           # [(obj, subName), ...]
  self._capture_data = {}           # {idx: [(x,y,z), ...]}  索引对应 _track_points
  self._capturing = False           # 当前是否在录

_tick() 中:
  if self._capturing and self._track_points:
    for i, (obj, sub) in enumerate(self._track_points):
      v = obj.getSubObject(sub)
      if v and hasattr(v, 'Point'):
        self._capture_data.setdefault(i, []).append((v.Point.x, v.Point.y, v.Point.z))

_play_by_mode 中:
  开始播放时 self._capturing = True
  停止播放时 self._capturing = False

Generate 按钮回调:
  for i, (obj, sub) in enumerate(self._track_points):
    pts = self._capture_data.get(i, [])
    if len(pts) == 2:   → Part.LineSegment
    elif len(pts) >= 3: → Part.BSplineCurve (approximate with points)
    else: → 跳过
    创建 Part::Feature, Shape = curve.toShape()
    命名 "MotionPath_{obj.Name}_{sub}_{seq:03d}"
```

### 路径曲线生成规则
- `len(pts) < 2`: 跳过（数据不足）
- `len(pts) == 2`: 创建 `Part.LineSegment` Edge
- `len(pts) >= 3`: 使用 `Part.BSplineCurve.approximate(pts)` 创建 B 样条曲线
- 曲线放在文档根层级（若源对象在 Body 内则放在同一 Body），避免 Link 作用域警告

### 选点模式实现
- 用户在勾选 ☑ Track Points + 点击 Select 后，启用 `Gui.Selection.addObserver(sel_observer)`
- `sel_observer` 的 `addSelection` 回调检查是否为 `Part.Vertex`，是则加入列表
- 按 Escape 或再次点击 Select 退出选点模式
- 用 `Gui.Selection.removeObserver(sel_observer)` 清理

### 命名与编号
- 每次 Generate → 遍历已有点计数递增
- 格式: `MotionPath_{objName}_{VertexX}_{nnn}`
- 计数从文档中已有的同名对象推断，避免重复

## Dependencies
- 仅修改 `DynamicDataCmd.py`（SliderPanel 类）
- 使用 FreeCAD 标准 API: `getSubObject`, `Part.BSplineCurve`, `Gui.Selection`
- 无新增第三方依赖

## Testing
- 手动测试：选点 → 播放 → Generate 生成曲线
- 验证：Bounce/Timeline/Tracks 三种模式均能录到不同轨迹

## State Management
- Generate 按钮初始 disabled，第一次播放停止后启用
- 再次播放 → 清空 `_capture_data` 重新录制（但保留 `_track_points` 列表）
- Clear Points → 同时清空 `_track_points`、`_capture_data` 并禁用 Generate

## Error Handling
- 选点：非 Vertex 子元素自动忽略
- 录制：顶点获取失败跳过该帧，不影响其他点
- 生成：点数不足 2 时打印警告，不弹错误框
