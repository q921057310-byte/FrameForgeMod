# FrameForge 使用说明

> **免责声明**：本项目所有代码由 AI 辅助生成。使用前请先在小模型上测试，操作前备份文件。AI 代码可能在特定场景下产生意外行为，建议逐个功能验证后再批量作业。

---

## Profile（创建型材）

1. 选草图边线 → 点 **Profile** 工具栏
2. 选 Material（材料）→ Family（系列）→ Size（型号）
3. 设 Rotation（0/90/180/270°）和 Anchor（锚点对齐）
4. **OK** → 生成参数化型材
- 两端支持 Bevel 斜切（在属性面板设 Start/End Cut1/Cut2）
- 截面类型：V-Slot / T-Slot / 国标 / 欧标 / 自定义

---

## Custom Profile（自定义截面型材）

1. 画一个闭合截面草图
2. 选草图 + 骨架边 → 点 **Custom Profile**
3. 草图即截面形状，与标准型材一样支持斜切等操作

---

## End Miter（端部斜接）

1. 在 3D 视图中选两个相邻型材的**面**
2. 点 **End Miter** → 自动计算斜接角度
3. 生成 `TrimmedProfile`（`_Mt`），原型材自动隐藏
- 支持 Gap 参数（间隙）

---

## End Trim（端部裁切）

1. 选被裁型材面 + 裁切边界面
2. 点 **End Trim** → 生成 `TrimmedProfile`（`_Tr`）
3. CutType：Simple fit（简易）/ Perfect fit（完美贴合）
- 预选：先在 3D 视图选好裁切对象+裁切面，再点 End Trim，自动填充面板

---

## Adjust Ends（调整端头）

1. 多选型材 → 点击目标面
2. 自动检测 A/B 端，正值延伸、负值缩短
3. 支持多点目标面累积调整

---

## Hole（打孔）

1. 点型材**面**（钻孔方向 = 面法向）
2. 选草图**点/圆/线**（圆→圆心，线→两端点）
3. 调参数：
   - HoleType：Through（通孔）/ Blind（盲孔）/ Counterbore（沉头孔）
   - BoltSpec：M3~M12、Pin2.5~Pin10
4. **OK** → 自动 Part::Cut → 生成 `{SizeName}_Cut`，原材和 cutter 自动隐藏
- **Apply**：保存当前 + 清空选择 + 继续打孔
- 编辑：双击 `HoleFeature`（设计树中）改尺寸
- 底部 RotX/Y/Z 下拉调整圆柱方向（-90/0/90/180°）

---

## Connector（自动打孔）

### Whistle Connector / 哨子连接器（快捷键 M, W）

1. 选**凹槽面**（T 型槽口）
2. 可选**端面**（定位距离）
3. 自动检测 QY 规格（Auto / QY16-8-30 / QY20-8-40 / QY20-10-45）
4. **OK** → 自动 Part::Cut

### TJoint Connector / T 型连接器（快捷键 M, T）

1. 选 **B 侧面**（连接件隐藏不遮挡视图）
2. 选 **A 端面** → 自动检测孔位 + 匹配螺丝规格
3. 螺丝规格：M6 / M8 / M10 / M12 / M14（自动匹配或手动选择）
4. **OK** → 自动 Part::Cut

---

## EndCap（封盖）

1. 选型材端面
2. 参数：
   - CapType：Plate（板式）/ Plug（插入式）
   - Thickness（厚度）、Gap（偏移距）
   - PlugOffset（Plug 模式下缩小外形间隙）
3. 可选：
   - 中心孔：勾选 HoleEnabled → 选 HoleThreadSpec（M3~M12）
   - 倒角/圆角：勾选 ChamferEnabled / FilletEnabled
4. **Apply**：保存继续；**OK**：保存关闭

> T 型槽截面已有圆角的边会自动跳过倒角

---

## Gusset（角撑板）

1. 选两个相邻面
2. 设厚度、直角边倒角、锐角边倒角
3. 可选中心孔
4. 位置对齐（左/中/右）、厚度对齐（前/中/后）

---

## Extruded Cutout（拉伸切空）

1. 选型材面 + 草图（3D 视图）
2. 点 **Extruded Cutout** → 沿面法向拉伸布尔裁切
3. 选 Through All（贯通）或指定深度

---

## Vent（通风口）

1. 设计树选实体 + 草图
2. 点 **Vent** → 选边界边线 + 肋条边线
3. 设 Rib Width（肋宽）、Fillet（圆角）

---

## Pattern Fill（填充阵列）

1. 设计树选实体 + 草图
2. 点 **Fill** → 选图案：Circle（圆形）/ Hexagon（六边形）/ User Sketch（自定义）
3. 网格模式：Staggered（交错）/ Rectangular（矩形）
4. Gradient Scale：中心→边缘渐变缩放
5. **防抖优化**：拖拽参数实时预览不卡顿

---

## Offset Plane（偏移基准面）

1. 选一个面 → 点 **Offset Plane**
2. 设距离 → 生成 `PartDesign::Plane`

---

## Color Profiles（颜色管理）

自动为型材分配区分度最大的颜色。

- **相同规格**（截面+长度+角度+厚度+类型完全一致）= 同一颜色
- **不同规格** = 不同颜色，黄金比例色相间距确保最大区分度
- 自动着色：MW/MT/打孔继承父型材颜色
- 手动触发：点 **ColorProfiles** 按钮为选中对象着色
- 算法：MD5 哈希 + 黄金比例色相偏移（0.618 × 哈希值）

---

## Dynamic Data / Sliders（动态数据与滑条面板）

1. 点 **Create Object** → 生成 `dd` 对象
2. 右键 `dd` → **Add Property**（如 `x = 500`、`width = 200`）
3. 在草图约束表达式中引用：`dd.x`
4. 点 **Sliders** → 打开实时滑条面板
   - 拖拽滑条，模型即时更新
   - 支持 Timeline 逐帧动画和 Bounce 往复动画
   - 支持 Angle 约束（自动度→弧度转换）
   - 关闭面板时保存窗口位置，下次自动恢复

> 注：DD 对象在文档打开时自动刷新。

---

## BOM / Cut List（物料清单）

1. 选 Part 容器 / 型材 / Links
2. 点 **Create BOM** → 生成两个 Spreadsheet

**BOM 列**：Parent / ID / Family / SizeName / Length / CutAngle1 / CutAngle2 / Drill/Cutout / Qty / Material / Weight / UnitPrice / Name

**Cut List**：余料优化切割方案
- Stock 长度（默认 6000mm）、Kerf（默认 1mm）
- First-Fit-Decreasing 算法
- 按角度分组优化

**角度表示**：
| 符号 | 含义 |
|------|------|
| `@` | TrimmedProfile 计算角度 |
| `P` | Perfect Cut（缺口贴合）|
| `-` | 同向斜切 |
| `*` | 90° 旋转斜切 |

> BOM 生成后请核对数据。

---

## Populate IDs / Reset IDs（ID 编号）

**Populate IDs**：自动为型材和 Links 分配 ID

1. 选中对象（型材 / Links / 容器）→ 点 **Populate IDs**
2. 配置：
   - ID 类型：数字 / 字母 / 组合（型材数字 + 链接字母，或反之）
   - 允许重复？重置编号？
   - 模式：仅选中 / 全文档 / 继续当前 / 从指定开始
3. 相同型材 → 同一 ID + xN 计数

**Reset IDs**：清除文档中所有 ID

---

## TechDraw Balloons（气泡标注）

1. 创建 TechDraw 页面 → 插入视图
2. 设计树选中视图 + 型材/Links
3. 点 **Create Balloons** → 自动生成带 ID 的气泡标注
4. **Refresh Balloons**：模型变更后刷新箭头位置

---

## Isolate（隔离显示）

1. 选中对象 → 点 **Isolate** → 其余全部隐藏
2. 退出隔离：点 **Exit Isolate**（右键或工具栏）
- 可配置跳过关键词（Constraint / Joint / Plane / Origin / Link 等）
- 支持装配体：父容器和 LinkedObject 保持可见

---

## Parametric Line（参数化线）

1. 选两个顶点
2. 点 **Parametric Line** → 生成 `Part::LineSegment`

---

## Attached Link（附着链接）

1. 设计树选中外部零件 → 点 **Attached Link**
2. 附着编辑器 → 映射到骨架的顶点/边/面
3. 生成 `App::Link` + `Part::AttachExtensionPython` + PID
4. 源零件变更自动同步到所有链接

---

## Recompute（强制更新）

递归重新计算所有 Profile / TrimmedProfile / ExtrudedCutout。

---

## Export TechDraw（导出 PDF）

一键将所有 TechDraw 页面导出为 PDF 文件。

---

## 工具栏布局

| 工具栏 | 命令 |
|--------|------|
| Drawing Primitives | 新建草图、Part 盒子、参数化线、SubShapeBinder |
| FrameForge | 型材库 ▼、裁剪 ▼、斜接、拉伸切空、封盖、角撑板、打孔 |
| Profile Group | 组、Part 容器 |
| Part Primitives | 附着链接、布尔合并、布尔切割、PartDesign Body |
| FrameForge Output | 编号、重置编号、生成气泡、刷新气泡、生成 BOM |
| Dynamic Data | 创建 DD、添加属性、复制属性、创建配置、Sliders |
| Other Tools | 通风口、填充阵列、偏移面、ColorProfiles |
| Utilities | 强制更新、导出 PDF、隔离、隔离设置 |

## 快捷键

| 工具 | 快捷键 |
|------|--------|
| Whistle Connector | M, W |
| T-Joint Connector | M, T |

## 命名规则

- 打孔结果：`{SizeName}_Cut`（如 `4040_Cut`）
- 裁剪结果：`{SizeName}_Tr` / `{SizeName}_Mt`（如 `4040_Tr`）
- 未匹配到 SizeName 时回退到 Label

## 已知限制

- **T 型槽封盖倒角**：截面已有圆角处自动跳过
- **裁剪延伸 Apply**：已移除（循环依赖问题）
- **首选项面板**：FreeCAD 1.1 暂不支持 Python 类 `addPreferencePage`
- **保存时 JSON 警告**：`Part::Solid/Compound` 不可 JSON 化，不影响功能
- **DAG 循环**：已在 TrimmedProfile 上再做裁剪会报 `Graph must be a DAG`，不建议在已裁型材上再裁
