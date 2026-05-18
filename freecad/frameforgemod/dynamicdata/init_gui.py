import os
import FreeCAD
import FreeCADGui as Gui

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, 'icons')
mainIcon = os.path.join(iconPath, 'DynamicDataLogo.svg')

pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2")
contextMenuAdded = False

class DynamicData2Workbench(Gui.Workbench):

    MenuText = "DynamicData2"
    ToolTip = "DynamicData2 - Parametric property containers with real-time sliders"
    Icon = mainIcon

    def __init__(self):
        self.list = None
        pass

    def Initialize(self):
        import freecad.frameforgemod.dynamicdata.DynamicDataCmd as DynamicDataCmd
        self.list = ["DynamicData2CreateObject", "DynamicData2AddProperty",
                    "DynamicData2EditEnumeration", "DynamicData2CreateConfiguration",
                    "DynamicData2RemoveProperty", "DynamicData2ImportNamedConstraints",
                    "DynamicData2ImportAliases","DynamicData2CopyProperty",
                    "DynamicData2RenameProperty","DynamicData2RetypeProperty",
                    "DynamicData2SetTooltip",
                    "DynamicData2MoveToNewGroup","DynamicData2Settings",
                    "DynamicData2Sliders", "DynamicData2Commands"]
        if pg.GetBool("CondensedToolbar", True):
            self.appendToolbar("DynamicData2 Commands", [self.list[-1]])
        else:
            self.appendToolbar("DynamicData2 Commands", self.list[:-6])
        self.appendMenu("&DynamicData2", self.list)

    def Activated(self):
        return

    def Deactivated(self):
        from PySide import QtCore
        QtCore.QTimer.singleShot(2000, self.showMenu)
        return

    def showMenu(self):
        global contextMenuAdded
        from PySide import QtGui
        window = QtGui.QApplication.activeWindow()
        keep = pg.GetBool('KeepToolbar', True)
        if not keep:
            return
        tb = window.findChildren(QtGui.QToolBar) if window else []
        for bar in tb:
            if "DynamicData2 Commands" in bar.objectName():
                bar.setVisible(True)

        class DDContextMenuEditor:
            def modifyContextMenu(self, recipient):
                if recipient == "View":
                    if Gui.activeWorkbench().name() != "DynamicData2Workbench":
                        return [{"append":"DynamicData2Commands", "menuItem":"Std_Delete"}]
                elif recipient == "Tree":
                    if Gui.activeWorkbench().name() != "DynamicData2Workbench":
                        return [{"append":"DynamicData2Commands", "menuItem":"Std_Delete"}]

        manip = DDContextMenuEditor()
        if hasattr(Gui, "addWorkbenchManipulator") and not contextMenuAdded:
            Gui.addWorkbenchManipulator(manip)
            contextMenuAdded = True

    def ContextMenu(self, recipient):
        self.appendContextMenu("DynamicData2", self.list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


wb = DynamicData2Workbench()
Gui.addWorkbench(wb)
