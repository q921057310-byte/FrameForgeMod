# Sliders 通用化 — 驱动任意 FreeCAD 物体的数值属性

## 问题

DynamicData 的 Sliders 面板目前只接受两种数据源：
- DynamicData2 对象（`hasattr(o, "DynamicData2")`）
- 草图约束（`hasattr(o, 'Constraints') and hasattr(o, 'setDatum')`）

用户在多实体装配场景下，需要 Sliders 能驱动任意选中物体的数值属性（`Length`、`Width`、`Placement.Base.x` 等）。

## 改动范围

修改文件：`freecad/frameforgemod/dynamicdata/DynamicDataCmd.py`

3 处改动，约 30 行。

### 1. 属性发现函数（新增）

```python
def _get_animatable_properties(obj):
    """从任意 FreeCAD 对象中找出可动画的数值属性"""
    props = []
    for p in obj.PropertiesList:
        if p in ("Label", "Label2", "ExpressionEngine", "Visibility", "Group"):
            continue
        attr = getattr(obj, p, None)
        if attr is None:
            continue
        if isinstance(attr, (int, float)):
            props.append((p, obj.getTypeIdOfProperty(p)))
        elif isinstance(attr, App.Units.Quantity):
            props.append((p, obj.getTypeIdOfProperty(p)))
    if hasattr(obj, "Placement"):
        props.append(("Placement.Base.x", "PropertyFloat"))
        props.append(("Placement.Base.y", "PropertyFloat"))
        props.append(("Placement.Base.z", "PropertyFloat"))
        props.append(("Placement.Rotation.Angle", "PropertyAngle"))
    return props
```

### 2. `_DD2Source.get/set` 支持加点号路径（修改）

```python
def get(self, name):
    parts = name.split(".")
    v = self.obj
    for p in parts: v = getattr(v, p)
    return v

def set(self, name, val):
    parts = name.split(".")
    target = self.obj
    for p in parts[:-1]: target = getattr(target, p)
    setattr(target, parts[-1], val)
```

这样 `"Placement.Base.x"` 等路径属性可读写。

### 3. `Activated()` 属性收集逻辑（修改）

原逻辑（三循环）：
- 循环 1：选中中找 DD2 对象 → `_DD2Source`
- 循环 2：选中中找 草图 → `_SketchSource`
- 循环 3：全文档扫 DD2/草图（fallback）

新逻辑（通用循环）：
- 遍历选中物体（或 fallback 全文档）
- 对每个物体调用 `_get_animatable_properties()`
- 有属性则包成 `_DD2Source`（或 `_SketchSource`）
- `_MultiSource` 聚合

```python
# 伪代码
for o in sel:
    props = _get_animatable_properties(o)
    if props:
        subs.append((o.Label, _DD2Source(o, props)))
        continue
    if hasattr(o, 'Constraints') and hasattr(o, 'setDatum'):
        s = _SketchSource(o)
        if s.items(): subs.append((o.Label, s))
```

## 不动的

- Sliders UI（`_add_row`、`_build`、`_interpolate`、关键帧、导出）
- `_SketchSource` 类（草图约束保持原功能）
- `_MultiSource` 类（多物体聚合）
- 工具栏注册 / 按钮位置

## 验证方法

1. 创建立方体 → 选中 → 打开 Sliders → 能看到 `Length`、`Width`、`Height`、`Placement.Base.x` 等属性
2. 拖动滑块 → 立方体实时变化
3. 关键帧 + 播放 → 插值正确
4. 选中多个物体 → `_MultiSource` 聚合显示
5. 选中草图的尺寸约束 → 仍能驱动（原功能不坏）
