# FrameForge Tutorial / 型材框架教程 (Mod)

> FrameForge is a FreeCAD workbench for creating frame structures — beams, miter cuts, trim cuts, cutouts, BOM export, and more.
>
> 型材框架工作台用于创建铝型材框架结构，支持斜切、裁切、开孔、物料清单导出等操作。

---

## 1. Create the Skeleton / 创建骨架

All profiles are mapped to edges — from a sketch, ParametricLine, or any edge shape.

型材依附于边线生成（草图边、参数化线等）。

1. New file → switch to **FrameForge_mod** workbench / 新建文件，切换到 FrameForge_mod 工作台
2. Create a sketch (e.g. XY plane) / 创建草图（如 XY 平面）

   ![Create Sketch](images/00-create-sketch.png)
   ![Select Orientation](images/01-select-orientation.png)

3. Draw a square — this will be our skeleton / 画一个矩形作为骨架

   ![Create Skeleton](images/02-create-frame-skeleton.png)

4. Close the sketch editor / 关闭草图编辑

---

## 2. Create the Frame / 创建框架

1. Click **Profile** tool / 点击 Profile 工具

   ![Profile](images/10-profiles.png)
   ![Profile Task](images/10-profiles-task.png)
   ![Profile Task 2](images/10-profiles-task-2.png)

2. Select Material → Family → Size from the lists / 选择材料 → 系列 → 型号
3. In 3D view, select the edges to profile / 在 3D 视图中选择边线

   ![Edge Selection](images/13-edge-selection.png)

   > Tip: Select the sketch **before** launching the tool — it will auto-select all edges / 可在启动工具前选中草图，自动选择所有边

4. Click **OK** — four profiles created! / 点击 OK，四条型材生成

   ![Profiles](images/14-profiles-done.png)
   ![Zoom in profile](images/14-zoom-on-profiles.png)

**Done — your first frame! / 第一个框架完成！**

You can set a Unit Price (per meter) in profile properties — used by BOM. / 可在型材属性中设置单价（每米），BOM 工具会使用。

---

## 3. Going 3D: Make a Cube / 构建 3D 立方体

### Method A: More Sketches / 方法 A：多个草图

1. Create a new sketch (same XY orientation) / 新建草图（相同 XY 方向）
2. Draw the same square / 画相同矩形
3. Set its **Placement → Position → Z** to 400 mm / 设置 Z 方向位置 400 mm

   ![Base Placement](images/20-sketch-base-placement.png)
   ![Sketch moved](images/20-sketch-base-placement-2.png)

4. Run **Profile** tool again on this sketch → second square frame / 再次运行 Profile 工具生成第二个方框

   ![Stacked Frames](images/21-stacked-frames.png)

### Method B: Parametric Lines / 方法 B：参数化线

1. Hide profiles (select + **Space**) to see the skeleton / 隐藏型材（选中+空格）露出骨架

   ![Hide profile](images/22-hide-profiles.png)

2. Select two corresponding vertices / 选取对应的两个顶点

   ![Select Vertices](images/23-select-vertexes.png)

3. Click **Parametric Line** → creates connection line / 点击 Parametric Line 生成连接线

   ![Create parametric line](images/24-create-parametric-line.png)
   ![Parametric Line](images/25-parametric-line.png)

4. Run **Profile** tool → select the parametric lines → **OK** / 运行 Profile → 选参数化线 → OK

   ![Cube Done](images/26-cube-done.png)

### Method C: Map a Sketch to a Face / 方法 C：草图映射到面

1. Create a new sketch with YZ orientation / 新建 YZ 方向草图

   ![Map Mode Sketch](images/30-mapmode-sketch.png)

2. Click `Map Mode` property → change attachment to a profile face / 修改 Map Mode 附着到型材面

   ![Map mode](images/31-mapmode.png)
   ![Map Mode dialog](images/32-mapmode-dialog.png)
   ![Map mode result](images/33-mapmode.png)

3. Edit the sketch, draw lines, then create profiles / 编辑草图画线，再生成型材

---

## 4. Bevels and Corners / 斜接与角处理

### Method A: Bevel Properties / 方法 A：型材属性斜切

1. Show only the first frame (hide the rest) / 只显示第一个框架

   ![Show first frame](images/40-show-first-frame.png)

2. Select a profile → in Properties, find **Bevel Start/End Cut 1/2** / 选择型材 → 属性面板找到 Bevel 起始终止切角

   ![Bevel properties](images/41-bevels.png)

3. Set angle values (positive/negative to control direction) / 设置角度值（正负控制方向）
4. Batch-select all profiles to apply the same bevels / 批量选择所有型材统一设置

   ![Batch bevels](images/42-batchs-bevels.png)

**Done — a clean square frame! / 干净的矩形框架完成！**

### Method B: End Miter Command / 方法 B：端部斜接命令

1. First add **Offset** to profiles (extends past the joint) / 先给型材加偏移量（伸出接头外）

   ![Add offset](images/51-add-offset.png)

   > Tip: select all profiles, set Offset once / 选所有型材，一次性设置偏移

2. Select two touching profile **faces** (in 3D view, not tree) / 选两个相邻型材的面（3D 视图，非设计树）

   ![Select touching faces](images/52-select-touching-profiles.png)

3. Click **End Miter** → creates two `TrimmedProfile` objects / 点击 End Miter → 生成两个 TrimmedProfile

   ![Create miter end](images/53-create-miter-end.png)
   ![Miter end result](images/54-miter-end.png)

4. Repeat for remaining corners / 重复处理其余角

### Method C: End Trim Command / 方法 C：端部裁切命令

When vertical profiles overlap the frame:

1. Select the vertical profile → click **+** (Trimmed object) / 选垂直型材 → 点 + 加入裁切对象

   ![Select trimmed body 1](images/63-select-trimmed-body-1.png)
   ![Select trimmed body 2](images/63-select-trimmed-body-2.png)

2. Select the **face** of the profile to trim against → click **+** (Trimming boundary) / 选目标面 → 点 + 加入裁切边界

   ![Select trimming boundaries 1](images/64-select-trimming-boundaries-1.png)
   ![Select trimming boundaries 2](images/64-select-trimming-boundaries-2.png)

3. Choose Cut Type: Simple fit / Perfect fit / 选裁切类型

   ![Cut type 1](images/64-select-cuttype-1.png)
   ![Cut type 2](images/64-select-cuttype-2.png)

4. Click **OK**

> Shortcut: Pre-select TrimmedObject + TrimmingBoundaries in 3D view, then click **Trim Profile** — auto-fills the task panel / 快捷键：先在 3D 视图中预选裁切对象+裁切面，再点击 Trim Profile，自动填充面板

---

## 5. Organizing Objects / 组织对象

### Part Container (Recommended / 推荐)

- Groups profiles, sketches, and links into a logical assembly unit / 将型材、草图、链接归为一个逻辑单元
- Close to manufacturing process: each profile is a unique item / 接近制造流程：每根型材独立可操作

![Part container](images/70-part-container.png)

> Drag objects one at a time into the container (FreeCAD limitation) / 建议逐个拖入容器

### Fusion

- Fuses profiles into a single solid / 将型材融合为单一实体
- Can be used as `BaseFeature` in PartDesign Body / 可在 PartDesign Body 中作为基础特征
- **Requirement**: profiles must be fully trimmed (no crossings) / 要求：型材必须完全裁剪，不能交叉

![Fusion](images/72-fusion.png)
![Fusion done](images/72-fusion-done.png)

#### Using Fusion for Drilling / 利用融合在 PartDesign 中打孔

1. Drag Fusion into a PartDesign Body as BaseFeature / 将融合拖入 PartDesign Body

   ![Body](images/80-body.png)
   ![base feature](images/81-basefeature.png)

2. Map sketch to any face → use PartDesign Hole / 草图映射到面 → 使用 PartDesign 孔工具

   ![Making Holes](images/82-create-sketch.png)
   ![Making Holes](images/82-making-holes.png)
   ![Holes Made](images/83-holes-made.png)

### Group Container

- Simple folder. No special behavior / 简单文件夹，无特殊功能

---

## 6. Extruded Cutout / 拉伸切空

1. Map a sketch to a profile face / 将草图映射到型材面

   ![Create sketch on face](images/90-create-sketch-on-face.png)

2. Draw the cutout shape (external geometry works too) / 画切空形状（可引用外部几何）

   ![Draw sketch](images/90-draw-sketch.png)

3. Select the face + sketch in 3D view → click **Extruded Cutout** / 选面+草图 → 点击 Extruded Cutout

   ![Extruded Cutout](images/91-extrudedcutout.png)
   ![Cutout done](images/92-extrudedcutout-done.png)

---

## 7. Attached Link / 附着链接

Add external parts (laser-cut plates, welded nuts, etc.) to your frame design.

将外部零件（激光切割板、焊接螺母等）附着到框架设计中。

1. Create the reference part (Part, PartDesign, SheetMetal, etc.) / 创建参考零件
2. Select it in tree → click **Attached Link** / 设计树选中 → 点击 Attached Link
3. Attachment editor opens → map to vertex/edge/face of skeleton / 附着到骨架顶点/边/面
4. OK → creates `App::Link` with PID, auto-moves into Part Container / 生成带 PID 的附着链接
5. Changes to the original part propagate to all links / 源零件变更自动同步
- A **Price** property can be added for BOM inclusion / 可添加 Price 属性纳入 BOM

---

## 8. Populate IDs / ID 自动编号

1. Select profiles, links, or containers / 选择型材/链接/容器
2. Click **Populate IDs** → configure in task panel / 配置
   - ID type: Numbers / Letters / Combined / ID 类型
   - Duplicate allowed? / 允许重复？
   - Reset numbering before filling? / 重置编号？
   - Mode: selection / document / continue / start at / 填充模式
3. Click **OK** → IDs assigned

**Reset IDs**: clears all IDs in the document / 清除文档中所有 ID

---

## 9. TechDraw Balloons / 技术图纸气泡标注

1. Create a TechDraw page → insert a View / 创建技术图纸页面 + 插入视图
2. In tree, select the View + profiles/links to annotate / 设计树选视图+型材/链接
3. Click **Create Balloons** → auto-generated with ID labels / 自动生成带 ID 的气泡标注

   > Balloon arrows point at part centers; drag balloons to reposition / 箭头指向部件中心，可拖拽调整位置

4. After geometry changes → select balloons in tree → click **Refresh Balloons** / 模型变更后刷新箭头位置

---

## 10. BOM / Cut List / 物料清单与余料清单

1. Select Part Containers / Profiles / Links / 选择部件容器/型材/链接
2. Click **Create BOM** → generates two spreadsheets / 生成两个表格

**BOM Columns / BOM 列**: Parent, ID, Family, SizeName, Length, CutAngle1, CutAngle2, Drill/Cutout, Qty, Material, Weight, UnitPrice, Name

**Cut List**: stock-optimized cutting plan (First-Fit-Decreasing algorithm) / 余料优化切割方案

**Angle notation / 角度表示**:
| Symbol | Meaning / 含义 |
|--------|----------------|
| `@` | TrimmedProfile calculated angle / 裁剪型材计算角度 |
| `P` | Perfect Cut (Notch) / 完美贴合（缺口） |
| `-` / `*` | Bevel direction (same / 90° rotated) / 斜切方向 |

> Always verify your BOM for errors. / 请务必核对 BOM 数据。

---

## Credits / 致谢

| Project / 项目 | Author / 作者 | Link / 链接 |
|---|---|---|
| **FrameForge** | lukh | [github.com/lukh/frameforge](https://github.com/lukh/frameforge) |
| **MetalWB** | Veloma | [framagit.org/Veloma/freecad_metal_workbench](https://framagit.org/Veloma/freecad_metal_workbench) |
| **Dynamic Data** | Mark Ganson | [github.com/mwganson/DynamicData](https://github.com/mwganson/DynamicData) |
| **EasyProfileFrame** | ovo-Tim | [github.com/ovo-Tim/EasyProfileFrame](https://github.com/ovo-Tim/EasyProfileFrame) |
| **BOLTS** | Johannes Reinhardt | [github.com/boltsparts/BOLTS](https://github.com/boltsparts/BOLTS) |

- **大海** — Aluminum extrusion profile library / 铝合金型材轮廓库
  - Bilibili: [space.bilibili.com/3546652184938824](https://space.bilibili.com/3546652184938824)

See [README](../README.md) for full credits / 完整致谢请参见 README
