# FrameForge_Mod / 型材框架工作台 (v0.1)

[FrameForge] modified version — AI-assisted FreeCAD workbench for aluminum profile frame design.

[FrameForge] 修改版本 — AI 协作开发的 FreeCAD 工作台，用于铝型材框架设计。

> ⚠️ This mod code is AI(Claude) generated. AI may have inaccurate understanding of FreeCAD API. Test before use, backup files before operations.
> ⚠️ 本 Mod 代码由 AI (Claude) 辅助生成。AI 对 FreeCAD API 的理解可能不准确，使用前请先测试，操作前备份文件。

<video src="https://github.com/user-attachments/assets/9b82ec2a-d3f6-48d9-b804-f1c74c3f432c"></video>

**Profile Creation Tutorial / 型材创建教程**
<video src="https://github.com/user-attachments/assets/7afd0c91-624a-48f2-9319-2409226ca223"></video>

**Profile Creation Tutorial 2 / 型材创建教程 2**
<video src="https://github.com/user-attachments/assets/af3ade0f-59d0-45e8-a84a-c17d32b5633c"></video>

**Profile Library Guide / 轮廓库教程**
<video src="https://github.com/user-attachments/assets/26157577-2dc4-4720-a9f2-5244bf8269fd"></video>

**How to Add Profiles / 如何添加型材轮廓**
<video src="https://github.com/user-attachments/assets/1b6b1319-25f9-48ca-8ac3-de276c8d5269"></video>

---

## Installation / 安装

```
%APPDATA%/FreeCAD/v1-1/Mod/FrameForge_mod/
```

Launch FreeCAD, switch workbench to **FrameForge_mod**.

启动 FreeCAD，工作台下拉选择 **FrameForge_mod**。

## Dependencies / 依赖

- FreeCAD ≥ 1.0

---

## Features / 功能列表

### Aluminium Profile Library / 铝型材库（freely editable / 可以随意编辑修改添加）

Select profiles via `.FCStd` cross-section files (AGB 20~60 series, Chinese/European standard).

通过 `.FCStd` 截面文件选择型材（20/30/40/45/50/60 系列，国标/欧标）。

**Profile location / 轮廓库位置：**
- Aluminum / 铝：`C:\Users\<user>\AppData\Roaming\FreeCAD\v1-1\Mod\FrameForge_mod\freecad\frameforgemod\resources\profiles\aluminum`
- Steel / 钢：`C:\Users\<user>\AppData\Roaming\FreeCAD\v1-1\Mod\FrameForge_mod\freecad\frameforgemod\resources\profiles\steel`

- Each `.FCStd` file is one profile cross-section; filename = model name / 每个 `.FCStd` 文件是一个型材截面，文件名即型号名
- Simple preview (lightweight box) or full preview (real FeaturePython objects) / 简易预览（轻量盒子）或全预览（完整 FeaturePython 对象）
- Simple preview does NOT support miter/gap preview / 简单预览不支持斜角、间隙预览
- Corner mode: Miter / A-over-B / B-over-A / Gap — visible in full preview only / 角模式：斜接 / A叠B / B叠A / 间隙 —— 仅完整预览可见
- Curved profile support (creates Part::Sweep) / 支持弯曲型材（创建 Part::Sweep）
- Rotation (0/90/180/270) / 旋转（0/90/180/270）
- Option A: in-place update — no new objects created when changing params / Option A 原地更新：改参数时不新建对象

### Create Profile / 创建型材

1. Select sketch edges / wires in 3D view / 选择草图边线
2. Click **Profile** → choose Material / Family / Size / 选材料/系列/型号
3. Set rotation (0/90/180/270°) and anchor alignment / 旋转角、锚点对齐
4. **OK** → parametric profiles with bevel support / 生成参数化型材（支持两端斜切）
- Cross-section types: V-Slot, T-Slot, Chinese/European standard / 截面类型：V-Slot、T-Slot、国标/欧标

### Create Custom Profile / 自定义截面型材

1. Draw a closed-wire sketch as cross-section / 画一个闭合轮廓草图
2. Select sketch + skeleton edge → click **Custom Profile** / 选草图+骨架边
3. The sketch becomes the profile shape / 草图即截面形状

### End Miter / 端部斜接

1. Select two adjacent profile **faces** / 选两个相邻型材面
2. Click **End Miter** → auto-calculates miter angle / 自动计算斜接角度
3. Creates `TrimmedProfile` (`_Mt`) — original profile auto-hidden / 生成 `TrimmedProfile`，原型材自动隐藏
- Supports Gap parameter / 支持间隙

### End Trim / 端部裁切

1. Select profile face (to cut) + trimming boundary face / 选被裁面 + 裁切边界面
2. Click **End Trim** → `TrimmedProfile` (`_Tr`) created / 生成 `TrimmedProfile`
- Cut type: Simple fit / Perfect fit / 裁切类型：简易 / 完美贴合

### Adjust Ends / 调整端头

1. Multi-select profiles, click target face / 多选型材，点击目标面
2. Auto-detects A/B end, positive = extend, negative = shorten / 自动检测 A/B 端，正值延伸、负值缩短
3. Supports multiple target faces for cumulative adjustment / 支持多点目标面累积调整

### Hole / 打孔

1. Click profile **face** (drill direction = face normal) / 点型材面（钻孔方向 = 面法向）
2. Select sketch points / circles / lines (circle → center, line → endpoints) / 选草图点/圆/线（圆心/端点）
3. Set HoleType (Through / Blind / Counterbore) & BoltSpec (M3~M12, Pin2.5~Pin10) / 设孔类型与规格
4. **OK** → auto Part::Cut → `{SizeName}_Cut` (original + cutter auto-hidden) / 自动布尔裁切
- **Apply**: save + clear selection, continue drilling / 保存继续
- Edit hole: double-click `HoleFeature` in tree / 双击 HoleFeature 编辑

### Connector / 连接件打孔

#### Whistle Connector / 哨子连接器 (M,W)

1. Select groove face / 选凹槽面
2. Optionally select end face (position offset) / 可选端面（定位距离）
3. Auto-detects QY spec (Auto / QY16-8-30 / QY20-8-40 / QY20-10-45) / 自动检测 QY 规格
4. **OK** → auto Part::Cut / 自动打孔

#### T-Joint Connector / T 型连接器 (M,T)

1. Select B side face (connector hidden → unobstructed view) / 选 B 侧面（连接件隐藏，不挡视图）
2. Select A end face → auto-detect hole + screw match / 选 A 端面 → 自动检测孔位+匹配螺丝
3. Screw sizes: M6/M8/M10/M12/M14 / 螺丝规格
4. **OK** → auto Part::Cut / 自动打孔

### End Cap / 端盖

1. Select profile end face / 选型材端面
2. Set Type (Plate / Plug), Thickness, Gap / 选类型、厚度、偏移
3. Optional: center hole (M3~M14), chamfer / fillet / 可选：中心螺纹孔、倒角/圆角
4. **Apply**: save + continue; **OK**: save & close

### Gusset / 角撑板

1. Select two adjacent faces / 选两个相邻面
2. Set thickness, chamfer, optional center hole / 设厚度、倒角、中心孔
3. Position alignment (left/center/right), thickness alignment (front/center/rear) / 位置对齐、厚度对齐

### Extruded Cutout / 拉伸切空

1. Select profile face + sketch in 3D view / 选型材面+草图
2. Click **Extruded Cutout** → boolean cut along face normal / 沿面法向拉伸布尔裁切
3. Mode: Through All / specified depth / 贯通 / 指定深度

### Vent / 通风口

1. Select body + sketch in tree / 设计树选实体+草图
2. Click **Vent** → pick boundary + rib edges / 选边界+肋条边
3. Set rib width, fillet / 设肋宽、圆角

### Pattern Fill / 填充阵列

1. Select body + sketch in tree / 设计树选实体+草图
2. Click **Fill** → choose pattern (Circle / Hexagon / User sketch) / 选填充图案
3. Grid mode: Staggered / Rectangular / 网格模式：交错/矩形
4. Gradient scale from center to edge / 支持中心→边缘渐变缩放
5. Debounced sliders: smooth real-time preview / 防抖优化，拖参数不卡

### Offset Plane / 偏移基准面

1. Select a face → click **Offset Plane** / 选面 → 点击偏移面
2. Set distance → creates `PartDesign::Plane` / 设距离 → 生成基准面

### BOM / 物料清单

1. Select Part Containers / Profiles / Links / 选部件容器/型材/链接
2. Click **Create BOM** → generates Spreadsheet + CutList / 生成 BOM 表格 + 余料优化清单
3. BOM columns: Parent, ID, Family, SizeName, Length, CutAngle1/2, Qty, Material, Weight, Price / BOM 列
4. Cut List: Stock length (default 6000mm), Kerf (default 1mm), FFD algorithm / 余料清单：Stock/切口优化
- Angle notation: `@` = TrimmedProfile angle, `P` = Perfect Cut (Notch), `-/*` = Bevel direction / 角度表示法

### Populate IDs / ID 自动编号

1. Select profiles / links / containers / 选型材/链接/容器
2. Click **Populate IDs** → configure in task panel / 配置策略
3. Options: numbering type (Numbers / Letters / Combined), mode (selection / document / continue / start at) / 编号类型与模式
4. Group identical profiles → same ID + xN count / 相同型材同 ID + 数量标注
- **Reset IDs**: clear all IDs in document / 清除所有 ID

### Dynamic Data (DD) / 动态数据

Attach custom properties to any FreeCAD object. / 为任意对象附加自定义属性。

**Usage / 使用：**
1. Click **Dynamic Data** → **Create Object** / 创建 DD 对象
2. Right-click `dd` → **Add Property** (e.g. `x = 500`) / 右键添加属性
3. Reference in sketch constraints: `dd.x` / 在草图约束中引用
4. **Sliders**: real-time slider panel for DD properties / Sliders 按钮打开实时滑条面板
5. Auto-refreshes on document open / 文档打开时自动刷新

### TechDraw Balloons / 技术图纸标注

1. Create a TechDraw page + insert a View / 创建技术图纸页面+插入视图
2. Select the View + profiles/links in tree / 选择视图+型材/链接
3. Click **Create Balloons** → auto-annotated with IDs / 自动生成气球标注（带 ID）
4. **Refresh Balloons**: update arrow positions after geometry changes / 几何变更后刷新箭头位置

### Isolate / 隔离显示

1. Select object(s) → click **Isolate** / 选中对象 → 其余全部隐藏
2. Exit isolate: right-click → **Exit Isolate** / 右键退出隔离
- Configurable skip keywords (Constraint, Joint, Plane, Origin, Link...) / 可配置跳过关键词
- Assembly support: parent container + LinkedObject stay visible / 装配体支持

### Parametric Line / 参数化线

1. Select two vertices / 选两个顶点
2. Click **Parametric Line** → creates `Part::LineSegment` / 生成参数化线段

### Attached Link / 附着链接

1. Select an object in tree + click **Attached Link** / 设计树选对象 → 点击附着链接
2. Attachment editor opens → map to vertex/edge/face of skeleton / 附着到骨架顶点/边/面
3. Creates `App::Link` + `Part::AttachExtensionPython`, with PID / 生成带 PID 的附着链接
- Changes to source object propagate to all links / 源对象变更自动同步到所有链接

### Recompute / 强制更新

Recursively recompute all Profile / TrimmedProfile / ExtrudedCutout objects. / 递归重新计算所有型材/裁剪/拉伸切空对象。

### Export TechDraw / 导出技术图纸

Export all TechDraw pages to PDF with one click. / 一键将所有 TechDraw 页面导出为 PDF。

### Color Profiles / 颜色管理

Automatically assign distinguishable colors to profiles. / 自动为型材分配区分度最大的颜色。
- Same specs (section + length + angle + thickness + type) = same color / 相同规格 = 同一颜色
- Different specs = different color (golden-ratio hue spacing) / 不同规格 = 不同颜色（黄金比例色相间距）
- Top-level profiles colored by **ColorProfiles** button / 手动点 ColorProfiles 按钮触发
- MW/MT/holes inherit parent profile color via signals / 子对象自动继承父型材颜色

### Sliders / 实时滑条面板

Real-time slider control for Dynamic Data properties and sketch constraints. / 为 DD 属性和草图约束提供实时滑条控制。

1. Click **Sliders** in Dynamic Data toolbar / 点 Sliders 按钮
2. Drag sliders → model updates in real time / 拖拽滑条，模型即时更新
3. Support Timeline animation and Bounce mode / 支持 Timeline 逐帧动画和 Bounce 往复动画
4. Angle constraints auto-convert degrees↔radians / Angle 约束自动度↔弧度转换
5. Window position remembered between sessions / 窗口位置自动记忆

### Known Bugs / 已知问题

- `shape` temporary files may remain in the design tree / shape 临时文件可能残留设计树
- After drilling, auto-face-hide may not work; manual Space-hide needed / 打孔后自动隐藏可能失效，需手动空格隐藏
- Creating profiles may occasionally produce duplicates / 创建型材时偶发多出型材
- DAG cycle when trimming already-trimmed profiles / 裁剪已裁剪的型材会产生循环依赖

---

## How to Add Profiles / 如何添加型材轮廓

### Getting Cross-Sections / 获取截面

- **Draw your own sketch** — Create a Sketcher sketch with a closed wire cross-section, save as `.FCStd` / 自己画草图，保存为 .FCStd
- **Extract from STP/IGS** — Open STP, create sketch from end face (Part → Create sketch from face), clean up and save / 从 STP 提取端面草图
- **Same series in one file** — Recommend putting same-series profiles in the same `.FCStd` / 同系列截面建议放同一个文件

### File Location / 文件位置

```
resources/profiles/
├── aluminum/        ← Aluminum profiles (AGB 20~60 series, CN/EU standard) / 铝型材
├── steel/           ← Steel profiles (tube, rectangular tube, light rail etc.) / 钢材
└── aluminium_extrusion.json  ← Aluminium dimension definitions / 铝型材尺寸定义
    metal.json                ← Metal structural shapes (EN standard) / 金属型材尺寸
    wood.json                 ← Timber sections (EN standard) / 木材型材
```

### Profile Families / 截面类型

#### Aluminum (JSON + .FCStd) / 铝型材

Aluminum has many specifications; currently includes AGB 20~60 series, Chinese/European standard with various groove widths. / 铝型材规格非常多，目前包含 AGB 20~60 系列、国标/欧标多种槽宽。

| Series / 系列 | Size range / 尺寸范围 | Source / 来源 |
|------|---------|---------|
| CN 30 series(6.3) | 25×25 | aluminium_extrusion.json |
| EU 20 series | 20×20 ~ 20×80 | aluminium_extrusion.json |
| EU 30 series(8.2) | 30×30, 30×60 | aluminium_extrusion.json |
| EU 40 series(10.2) | 40×40, 40×80 | aluminium_extrusion.json |
| AGB series | 20~60 series, various groove widths | `.FCStd` files |

#### Steel (.FCStd) / 钢材

Steel profiles are currently few, and any help adding more is welcome. / 钢材目前很少，后续可补充，有帮助更好。

| Profile / 型材 | File / 文件 |
|------|------|
| Square tube 40×40×1.5 | st4040-1.5.FCStd |
| Rectangular tube 50×30×2.6 | 矩型管 50 X 30 X 2.6.FCStd |
| Light rail 9kg | 轻轨 轻轨9.FCStd |
| Location / 位置：resources/profiles/steel/ | |

#### Metal structural shapes (JSON) / 金属型材

| Series / 系列 | Size range / 尺寸 | Note / 说明 |
|------|---------|------|
| Equal Leg Angles | 16×16×3 ~ 250×250×35 | EN 10056-1 |
| Unequal Leg Angles | 30×20×3 ~ 250×150×15 | EN 10056-1 |
| Flat Sections | 10×3 ~ 200×65 | EN10025 |

#### V-Slot / T-Slot (parametric / 程序生成)

| Type / 类型 | Size / 尺寸 | Note / 说明 |
|------|------|------|
| V-Slot 20 | 20×20 ~ 20×80 | Generated / 程序生成 |
| T-Slot 20 | 20×20 (1~3 grooves, symmetrical/opposing) | Generated / 程序生成 |
| CN/EU standard | 20/30/40/45 series | Generated / 程序生成 |

---

## Toolbar Layout / 工具栏布局

| Toolbar / 工具栏 | Commands / 命令 |
|--------|------|
| Drawing Primitives | Sketcher_NewSketch, Part_Box, ParametricLine, SubShapeBinder |
| Frameforge | AluminumProfileLibrary ▼, Trim ▼, EndMiter, ExtrudedCutout, EndCap, Gusset, H |
| Profile Group | Std_Group, Std_Part |
| Part Primitives | AttachedLink, Part_Fuse, Part_Cut, PartDesign_Body |
| FrameForge output | PopulateIDs, ResetIDs, CreateBalloons, RefreshBalloons, CreateBOM |
| Dynamic Data | CreateObject, AddProperty, CopyProperty, CreateConfiguration, Sliders |
| Other Tools | AddVent, PatternFill, OffsetPlane, ColorProfiles |
| Utilities | Recompute, ExportTechDraw, Isolate, IsolateSettings |

---

## Usage Notes / 使用备注

This plugin code was generated with AI (Claude) assistance. Known AI issues / 已知 AI 常见问题：

- FreeCAD API misunderstanding (e.g. `Part.makeRegularPolygon` doesn't exist) / API 理解偏差
- `addObject` + transaction missmatching (`abortTransaction` not paired) / 事务管理遗漏
- Frequent `recompute()` causing lag / 频繁 recompute 导致卡顿
- Bad cache design → stale geometry / 缓存设计不合理
- Edge cases not covered (null selection, shapeless objects) / 边界情况未覆盖

Recommendations / 操作建议：
1. Verify on small models first / 先在小模型上验证
2. Save/backup before operations / 操作前保存/备份
3. Turn off FreeCAD auto-save or shorten interval / 关闭自动保存或缩短间隔

---

## Maintainer / 维护者

xingxing — q921057310@gmail.com

## Credits / 致谢

| Project | Author | Description |
|---------|--------|-------------|
| [FrameForge](https://github.com/lukh/frameforge) | lukh | Original workbench / 原始工作台 |
| [MetalWB](https://framagit.org/Veloma/freecad_metal_workbench) | Veloma | FrameForge predecessor / FrameForge 前身 |
| [Dynamic Data](https://github.com/mwganson/DynamicData) | Mark Ganson | Dynamic properties (v2.78, bundled) / 动态属性系统 |
| [EasyProfileFrame](https://github.com/ovo-Tim/EasyProfileFrame) | ovo-Tim | Profile frame workbench (code referenced) / 型材框架工作台（参考代码） |
| [BOLTS](https://github.com/boltsparts/BOLTS) | Johannes Reinhardt | Open Technical Specs library / 开源技术规格库 |

### Special thanks / 特别感谢
- **大海** — Provided aluminum extrusion profile library / 提供铝合金型材轮廓库
- Vincent B, Quentin Plisson, rockn, Jonathan Wiedemann
- [FreeCAD forum thread](https://forum.freecad.org/viewtopic.php?style=5&t=72389)

## License / 许可证

LGPL-3.0-only
