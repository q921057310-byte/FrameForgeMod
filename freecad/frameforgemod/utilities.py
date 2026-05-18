import os
from collections import Counter

import FreeCAD
import FreeCADGui
import TechDrawGui
from PySide import QtCore, QtGui
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets = QtGui

import freecad.frameforgemod._utils as ffu
from freecad.frameforgemod.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate

# TechDraw PDF Gen


class ExportTechDrawCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "gen_techdraw.svg"),
            "MenuText": translate("frameforgemod", "Export TechDraw to PDF"),
            "Accel": "M, E",
            "ToolTip": translate(
                "frameforgemod",
                "Export all TechDraw pages in the document to PDF files.",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument

        if doc is None:
            raise RuntimeError("No active document")

        # Output directory
        if doc.FileName:
            out_dir = QtWidgets.QFileDialog.getExistingDirectory(None, "Export folder", os.path.dirname(doc.FileName))
        else:
            out_dir = FreeCAD.getUserAppDataDir()

        for obj in doc.Objects:
            if obj.TypeId == "TechDraw::DrawPage":
                pdf_name = "".join(c for c in obj.Label if c.isalnum() or c in (" ", ".", "_")).rstrip()
                pdf_path = os.path.join(out_dir, f"{pdf_name}.pdf")

                TechDrawGui.exportPageAsPdf(obj, pdf_path)

                FreeCAD.Console.PrintMessage(f"Exported: {pdf_path}\n")

        FreeCAD.Console.PrintMessage("All TechDraw pages exported.\n")


FreeCADGui.addCommand("frameforgemod_ExportTechDraw", ExportTechDrawCommand())


class RecomputeFrameForgeObjectsCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "recompute.svg"),
            "MenuText": translate("frameforgemod", "Recursive Recompute"),
            "Accel": "M, Shift+R",
            "ToolTip": translate(
                "frameforgemod",
                "Recursively recompute all FrameForge objects and their dependencies.",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        stats = []

        def recursive_recompute(objs):
            for obj in objs:
                if ffu.is_profile(obj) or ffu.is_trimmedbody(obj) or ffu.is_extrudedcutout(obj):
                    recursive_recompute(obj.OutList)

                    FreeCAD.Console.PrintMessage(f"{obj.Label} ...")

                    obj.recompute()

                    stats.append(obj.Label)
                    FreeCAD.Console.PrintMessage("ok\n")

        recursive_recompute(FreeCAD.ActiveDocument.Objects)

        cs = Counter(stats)
        for k in cs:
            FreeCAD.Console.PrintMessage(f"{k} = {cs[k]}\n")
        # FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("frameforgemod_RecomputeFrameForgeObjects", RecomputeFrameForgeObjectsCommand())


class ColorProfilesCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "profile.svg"),
            "MenuText": "Color Profiles / 型材着色",
            "ToolTip": "Color identical profiles (same Family + Size + Length + CutAngles).\n相同型材（同系列+同尺寸+同长度+同切角）分配同色。",
        }

    def IsActive(self):
        return True

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            return
        sel = FreeCADGui.Selection.getSelection()
        objs = sel if sel else doc.Objects

        def to_float(v):
            """Extract numeric value from string or Quantity."""
            v = getattr(v, "Value", v)  # handle Quantity
            if v is None:
                return 0.0
            try:
                return float(v)
            except (ValueError, TypeError):
                import re
                m = re.search(r"[\d\.\-]+", str(v))
                return float(m.group()) if m else 0.0

        def get_profile(obj):
            """Get (Family, SizeName, Length, CutA, CutB) from profile or trimmed."""
            if hasattr(obj, "ProfileWidth") and hasattr(obj, "ProfileHeight"):
                return (getattr(obj, "Family", ""),
                        getattr(obj, "SizeName", ""),
                        round(to_float(getattr(obj, "Length", 0)), 1),
                        round(to_float(getattr(obj, "CuttingAngleA", None)), 1),
                        round(to_float(getattr(obj, "CuttingAngleB", None)), 1))
            if hasattr(obj, "TrimmedBody") and obj.TrimmedBody:
                p = obj.TrimmedBody
                return (getattr(p, "Family", ""),
                        getattr(p, "SizeName", ""),
                        round(to_float(getattr(obj, "Length", 0) or 0), 1),
                        round(to_float(getattr(p, "CuttingAngleA", None) or 0), 1),
                        round(to_float(getattr(p, "CuttingAngleB", None) or 0), 1),
                        getattr(obj, "CutType", ""),
                        getattr(obj, "TrimmedProfileType", ""),
                        round(to_float(getattr(obj, "Gap", 0) or 0), 1))
            # Find parent profile for attached objects
            parent = None
            # Gusset: Face1 / Face2
            for fprop in ("Face1", "Face2"):
                if hasattr(obj, fprop):
                    try:
                        fv = getattr(obj, fprop)
                        if fv and len(fv) > 0:
                            parent = fv[0] if hasattr(fv[0], "ProfileWidth") else (fv[0][0] if isinstance(fv[0], (list, tuple)) else None)
                    except Exception:
                        pass
                    if parent is not None:
                        break
            # End cap: BaseObject
            if parent is None and hasattr(obj, "BaseObject") and obj.BaseObject:
                try:
                    parent = obj.BaseObject[0] if isinstance(obj.BaseObject, (list, tuple)) else obj.BaseObject
                except Exception:
                    pass
            # ExtrudedCutout / general: Base
            if parent is None and hasattr(obj, "Base") and obj.Base:
                try:
                    parent = obj.Base[0] if isinstance(obj.Base, (list, tuple)) else obj.Base
                except Exception:
                    pass
            # WhistleConnector: DrillFace / EndFace
            if parent is None and hasattr(obj, "DrillFace") and obj.DrillFace:
                try:
                    parent = obj.DrillFace[0]
                except Exception:
                    pass
            if parent is None and hasattr(obj, "EndFace") and obj.EndFace:
                try:
                    parent = obj.EndFace[0]
                except Exception:
                    pass
            # Boolean cut: Base / Tool
            if parent is None and obj.TypeId in ("Part::Cut", "Part::MultiCommon", "Part::Fuse"):
                for cand in (getattr(obj, "Base", None), getattr(obj, "Tool", None)):
                    if cand is not None and hasattr(cand, "ProfileWidth"):
                        parent = cand
                        break
            if parent is not None and hasattr(parent, "ProfileWidth"):
                fam = getattr(parent, "Family", "")
                szn = getattr(parent, "SizeName", "")
                # Include object-specific properties in key
                props = []
                if hasattr(obj, "LegLength1"):
                    props += [round(to_float(getattr(obj, "LegLength1", 0) or 0), 1),
                             round(to_float(getattr(obj, "LegLength2", 0) or 0), 1),
                             round(to_float(getattr(obj, "Thickness", 0) or 0), 1)]
                elif hasattr(obj, "BaseObject"):
                    props += [getattr(obj, "Type", ""),
                             round(to_float(getattr(obj, "Thickness", 0) or 0), 1)]
                else:
                    props += [round(to_float(getattr(obj, "Length", 0) or 0), 1),
                             round(to_float(getattr(obj, "CuttingAngleA", None) or 0), 1),
                             round(to_float(getattr(obj, "CuttingAngleB", None) or 0), 1)]
                return (fam, szn) + tuple(props)
            return None

        groups = {}
        for o in objs:
            key = get_profile(o)
            if key:
                groups.setdefault(key, []).append(o)

        if not groups:
            FreeCAD.Console.PrintMessage("No profiles or trimmed profiles found.\n")
            return

        # High-contrast fixed palette
        PALETTE = [
            (1.0, 0.0, 0.0),   # red
            (0.0, 0.5, 1.0),   # blue
            (0.0, 0.8, 0.0),   # green
            (1.0, 0.6, 0.0),   # orange
            (0.8, 0.0, 0.8),   # purple
            (0.0, 0.8, 0.8),   # cyan
            (1.0, 1.0, 0.0),   # yellow
            (1.0, 0.4, 0.7),   # pink
            (0.5, 0.3, 0.0),   # brown
            (0.5, 0.5, 0.5),   # gray
        ]

        sorted_keys = sorted(groups.keys(), key=str)
        import hashlib, colorsys

        def spec_color(key):
            h = int(hashlib.md5(str(key).encode()).hexdigest()[:8], 16)
            # Golden ratio hue spacing
            hue = (h * 0.618033988749895) % 1.0
            sat = 0.85  # high saturation for vivid colors
            lit = 0.35 + (h % 30 - 15) / 60.0  # -0.25 to +0.25 variation
            r, g, b = colorsys.hls_to_rgb(hue, lit, sat)
            return (round(r, 2), round(g, 2), round(b, 2))

        for key in sorted_keys:
            objs = groups[key]
            color = spec_color(key)
            for o in objs:
                try:
                    o.ViewObject.ShapeColor = color
                except Exception:
                    pass
            FreeCAD.Console.PrintMessage(f"{key[0]} {key[1]} L={key[2]} T={key[3]} → color\n")

        doc.recompute()


FreeCADGui.addCommand("frameforgemod_ColorProfiles", ColorProfilesCommand())
