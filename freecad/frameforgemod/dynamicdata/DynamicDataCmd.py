# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the Dynamic Data addon.

################################################################################
#                                                                              #
#   Copyright (c) 2018 Mark Ganson ( TheMarkster )                             #
#                                                                              #
#   This library is free software; you can redistribute it and/or modify it    #
#   under the terms of the GNU Lesser General Public License as published      #
#   by the Free Software Foundation; either version 2.1 of the License, or     #
#   (at your option) any later version.                                        #
#                                                                              #
#   This library is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this library; if not, write to the Free Software Foundation,    # 
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA           #
#                                                                              #
################################################################################

__title__   = "DynamicData2"
__author__  = "Mark Ganson <TheMarkster>"
__url__     = "https://github.com/mwganson/DynamicData"
__date__    = "2025.11.26"
__version__ = "2.78"

version = float(__version__)
mostRecentTypes=[]
mostRecentTypesLength = 5 #will be updated from parameters


from FreeCAD import Gui
from PySide import QtCore, QtGui

import FreeCAD, FreeCADGui, os, math, re, ast
App = FreeCAD
Gui = FreeCADGui
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'icons' )
uiPath = os.path.join( __dir__, 'ui' )

keepToolbar = True
windowFlags = QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint

class DynamicData2BaseCommandClass:
    """Base class for all commands to provide some common code"""
    #select objects dialog class
    class SelectObjects(QtGui.QDialog):
        def __init__(self, objects, label=""):
            QtGui.QDialog.__init__(self)
            scrollContents = QtGui.QWidget()
            scrollingLayout = QtGui.QVBoxLayout(self)
            scrollContents.setLayout(scrollingLayout)
            scrollArea = QtGui.QScrollArea()
            scrollArea.setVerticalScrollBarPolicy(QtGui.Qt.ScrollBarAlwaysOn)
            scrollArea.setHorizontalScrollBarPolicy(QtGui.Qt.ScrollBarAlwaysOff)
            scrollArea.setWidgetResizable(True)
            scrollArea.setWidget(scrollContents)
            self.signalsBlocked = False

            vBoxLayout = QtGui.QVBoxLayout(self)
            vBoxLayout.addWidget(QtGui.QLabel(label))
            self.all = QtGui.QCheckBox("All")
            self.all.stateChanged.connect(self.allStateChanged)
            vBoxLayout.addWidget(self.all)
            vBoxLayout.addWidget(scrollArea)
            self.setLayout(vBoxLayout)
            buttons = QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok.__or__(QtGui.QDialogButtonBox.Cancel),
                QtCore.Qt.Horizontal, self)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            self.checkBoxes = []
            self.selected = []
            for ii,object in enumerate(objects):
                self.checkBoxes.append(QtGui.QCheckBox(object))
                self.checkBoxes[-1].setCheckState(self.all.checkState())
                self.checkBoxes[-1].stateChanged.connect(self.checkStateChanged)
                scrollingLayout.addWidget(self.checkBoxes[-1])
            vBoxLayout.addWidget(buttons)

        def checkStateChanged(self, arg):
            if not arg:
                self.signalsBlocked = True
                self.all.setCheckState(QtCore.Qt.Unchecked)
                self.signalsBlocked = False

        def allStateChanged(self, arg):
            if self.signalsBlocked:
                return
            self.checkAll(self.all.checkState())

        def checkAll(self, state):
            for cb in self.checkBoxes:
                cb.setCheckState(state)

        def accept(self):
            self.selected = []
            for cb in self.checkBoxes:
                if cb.isChecked():
                    self.selected.append(cb.text())
            super().accept()

        ### end of SelectObjects class definition

    def getSelectedObjects(self, objs, label="", checkAll=True):
        """opens a dialog with objs (strings) in a checkboxed list, returns list of selected"""
        if objs:
            dlg = DynamicData2BaseCommandClass.SelectObjects(objs,label)
            if checkAll:
                dlg.all.setCheckState(QtCore.Qt.Checked)
            else:
                dlg.all.setCheckState(QtCore.Qt.Unchecked)
            ok = dlg.exec_()
            if not ok:
                return []
            return dlg.selected
        return []

    @property
    def PropertyTypes(self):
         return [
            "Acceleration",
            "Angle",
            "Area",
            "Bool",
            "Color",
            "Direction",
            "Distance",
            "Enumeration",
            "File",
            "FileIncluded",
            "Float",
            "FloatConstraint",
            "FloatList",
            "Font",
            "Force",
            "Integer",
            "IntegerConstraint",
            "IntegerList",
            "Length",
            "Link",
            "LinkChild",
            "LinkGlobal",
            "LinkList",
            "LinkListChild",
            "LinkListGlobal",
            "LinkSubList",
            "Material",
            "MaterialList",
            "Matrix",
            "Path",
            "Percent",
            "Placement",
            "PlacementLink",
            "Position",
            "Precision",
            "Pressure",
            "Quantity",
            "QuantityConstraint",
            "Rotation",
            "Speed",
            "String",
            "StringList",
            "Temperature",
            "Vector",
            "VectorList",
            "VectorDistance",
            "Volume"]


    def getAllProperties(self, obj, includeViewProps = False, blacklist=[]):
        """get all the properties that we might want to copy or set"""
        props = [prop for prop in obj.PropertiesList if not prop in blacklist]
        if includeViewProps:
            viewProps = [f"(view) {prop}" for prop in obj.ViewObject.PropertiesList if not prop in blacklist]
        else:
            viewProps = []
        return props + viewProps

    def getDynamicProperties(self, obj):
        """get the list of the dynamic properties of obj"""
        props = [p for p in obj.PropertiesList if self.isDynamic(obj,p)]
        return props

    def getGroup(self, obj, prop):
        """return the name of the group this property is in"""
        if not obj:
            return None
        if not prop in obj.PropertiesList:
            return None
        return obj.getGroupOfProperty(prop)

    def getGroups(self,obj,skipList=[]):
        """get the groups of obj, skipping those in skipList"""
        props = [p for p in obj.PropertiesList if obj.getPropertyStatus(p) == [21]]
        groups = []
        for prop in props:
            group = obj.getGroupOfProperty(prop)
            if group and not group in groups and not group in skipList:
                groups.append(group)
        return groups

    def isDynamic(self,obj,prop):
        """checks whether prop is a dynamic property and not a built-in property
        of obj"""
        if prop == "DynamicData2":
            return False
        isSo = False
        try:
            oldGroup = obj.getGroupOfProperty(prop)
            obj.setGroupOfProperty(prop,"test")
            obj.setGroupOfProperty(prop,oldGroup)
            isSo = True
        except Exception:
            isSo = False
        return isSo

    def isDDObject(self, obj):
        """checks if this is a DynamicData2 object"""
        return hasattr(obj, "DynamicData2")

    def isUnit(self, name):
        """check if name is a reserved keyword for units, such as T or k"""
        #if parsing quantity succeeds, it means this name is a reserved keyword
        try:
            FreeCAD.Units.parseQuantity(name)
            return True
        except (ValueError, TypeError):
            return False

    def isValidName(self, obj, name):
        isUnit = self.isUnit(name)
        return name == self.fixName(obj, name) and not self.isUnit(name)

    def getNewPropertyNameCandidate(self, obj, candidate):
        """arguments: (obj, candidate) Takes candidate as a starting point and finds a new unique name based on it
        Example: candidate = "Length23" and there already exists in obj a "Length23",
        so this function would try Length24, Length25, etc. until a new unique name is found"""

        if not hasattr(obj, candidate) and not self.isUnit(candidate):
            return candidate

        # Use regular expression to extract base name and number
        match = re.match(r'^(.*?)(\d*)$', candidate)
        base_name, number_suffix = match.groups() if match else (candidate, '')
        idx = int(number_suffix) if number_suffix else 1

        if self.isUnit(base_name):
            base_name = f"{base_name}_"

        while hasattr(obj, f"{base_name}{idx}"):
            idx += 1

        new_candidate = f"{base_name}{idx}"
        return new_candidate

    def fixName(self, obj, name):
        """fixes a name so it can be a valid property name"""
        pattern = re.compile(r'^\d') #can't begin with a number
        pattern2 = re.compile(r'[^0-9a-zA-Z]') #no non-alphanumerics
        REPLACEMENTS = {
            " ": "_",
            ".": "_",
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "Ä": "Ae",
            "Ö": "Oe",
            "Ü": "Ue",
            "ß": "ss",
            "'": ""
        }
        new_name = name
        for k,v in REPLACEMENTS.items():
            new_name = new_name.replace(k, v)
        if pattern.match(new_name):
            new_name = f"_{new_name}"
        new_name = re.sub(pattern2, '_', new_name) #replace with _'s

        if self.isUnit(new_name):
            new_name = self.getNewPropertyNameCandidate(obj, new_name)
        return new_name


#######################################################################################
# Keep Toolbar active even after leaving workbench

class DynamicData2SettingsCommandClass(DynamicData2BaseCommandClass):
    """Settings, currently only whether to keep toolbar after leaving workbench"""
    global mostRecentTypes

    class DynamicData2SettingsDlg(QtGui.QDialog):

        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2")

        def __init__(self):
            super(DynamicData2SettingsCommandClass.DynamicData2SettingsDlg, self).__init__(Gui.getMainWindow())
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.setAttribute(QtCore.Qt.WA_WindowPropagation, True)
            self.form = QtGui.QWidget()
            form_lay = QtGui.QVBoxLayout(self.form)
            self.form.KeepToolbar = QtGui.QCheckBox("保持工具栏激活")
            self.form.CondensedToolbar = QtGui.QCheckBox("紧凑型工具栏")
            self.form.SupportViewObjectProperties = QtGui.QCheckBox("支持视图对象属性")
            self.form.AddToActiveContainer = QtGui.QCheckBox("创建时添加到活动容器")
            self.form.CheckForUpdates = QtGui.QCheckBox("检查更新")
            self.form.AddToFreeCADPreferences = QtGui.QCheckBox("添加到 FreeCAD 首选项 (修改需重启)")
            mru_row = QtGui.QHBoxLayout()
            mru_label = QtGui.QLabel("最近使用类型列表大小:")
            self.form.mruLength = QtGui.QSpinBox()
            self.form.mruLength.setRange(1, 100)
            mru_row.addWidget(mru_label)
            mru_row.addWidget(self.form.mruLength)
            mru_row.addStretch()
            form_lay.addWidget(self.form.KeepToolbar)
            form_lay.addWidget(self.form.CondensedToolbar)
            form_lay.addWidget(self.form.SupportViewObjectProperties)
            form_lay.addWidget(self.form.AddToActiveContainer)
            form_lay.addWidget(self.form.CheckForUpdates)
            form_lay.addWidget(self.form.AddToFreeCADPreferences)
            form_lay.addLayout(mru_row)
            form_lay.addStretch()
            self.setWindowTitle("DynamicData2 设置 v" + __version__)
            self.setWindowIcon(QtGui.QIcon(os.path.join(iconPath, "Settings.svg")))
            lay = QtGui.QVBoxLayout(self)
            lay.addWidget(self.form)
            self.setLayout(lay)
            self.form.KeepToolbar.setChecked(self.pg.GetBool('KeepToolbar', True))
            self.form.CondensedToolbar.setChecked(self.pg.GetBool('CondensedToolbar', True))
            self.form.SupportViewObjectProperties.setChecked(self.pg.GetBool('SupportViewObjectProperties', False))
            self.form.AddToActiveContainer.setChecked(self.pg.GetBool('AddToActiveContainer', False))
            self.form.CheckForUpdates.setChecked(self.pg.GetBool('CheckForUpdates', True))
            self.form.AddToFreeCADPreferences.setChecked(self.pg.GetBool("AddToFreeCADPreferences",True))
            self.form.mruLength.setValue(self.pg.GetInt('mruLength', 5))
            

        def closeEvent(self, event):
            self.pg.SetBool('KeepToolbar', self.form.KeepToolbar.isChecked())
            self.pg.SetBool('CondensedToolbar', self.form.CondensedToolbar.isChecked())
            self.pg.SetBool('SupportViewObjectProperties', self.form.SupportViewObjectProperties.isChecked())
            self.pg.SetBool('AddToActiveContainer', self.form.AddToActiveContainer.isChecked())
            self.pg.SetBool('CheckForUpdates', self.form.CheckForUpdates.isChecked())
            self.pg.SetBool('AddToFreeCADPreferences',self.form.AddToFreeCADPreferences.isChecked())
            self.pg.SetInt('mruLength', self.form.mruLength.value())
            super(DynamicData2SettingsCommandClass.DynamicData2SettingsDlg, self).closeEvent(event)

    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'Settings.svg'), # the name of an icon file available in the resources
                'MenuText': "设置(&S)",
                'Accel'   : "Ctrl+Shift+D,S",
                'ToolTip' : "打开 DynamicData2 工作台设置对话框"}

    def Activated(self):
        dlg = self.DynamicData2SettingsDlg()
        dlg.open()

    def IsActive(self):
        return True


#Gui.addCommand("DynamicData2KeepToolbar", DynamicData2KeepToolbarCommandClass())


####################################################################################
# Create the dynamic data container object

class DynamicData2CreateObjectCommandClass(DynamicData2BaseCommandClass):
    """Create Object command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateObject.svg'),
                'MenuText': "创建容器对象(&C)",
                'Accel'   : "Ctrl+Shift+D,C",
                'ToolTip' : "创建一个用于存储自定义属性的 DynamicData2 容器对象"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("CreateObject")
        a = doc.addObject("App::FeaturePython","dd")
        a.addProperty("App::PropertyStringList","DynamicData2").DynamicData2=self.getHelp()
        setattr(a.ViewObject,'DisplayMode',['0']) #avoid enumeration -1 warning
        doc.commitTransaction()
        Gui.Selection.clearSelection()
        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2")
        if pg.GetBool('AddToActiveContainer',False):
            body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
            part = Gui.ActiveDocument.ActiveView.getActiveObject("part")
            if body:
                body.Group += [a]
            elif part:
                part.Group += [a]
        Gui.Selection.addSelection(a) #select so the user can immediately add a new property
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        return True

    def getHelp(self):
        return ["Created with DynamicData2 (v"+__version__+") workbench.",
                "This is a simple container object built",
                "for holding custom properties."
]

#Gui.addCommand("DynamicData2CreateObject", DynamicData2CreateObjectCommandClass())

####################################################################################
# Create or edit an existing configuration

class DynamicData2CreateConfigurationCommandClass(DynamicData2BaseCommandClass):
    """Create or edit a configuration command"""
    class DynamicData2ConfigurationDlg(QtGui.QDialog):
        def __init__(self,dd):
            super(DynamicData2CreateConfigurationCommandClass.DynamicData2ConfigurationDlg, self).__init__(Gui.getMainWindow())
            self.setAttribute(QtCore.Qt.WA_WindowPropagation, True)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.setWindowTitle(f"DynamicData2 v{__version__} Configuration Editor")
            self.setWindowIcon(QtGui.QIcon("Resources/icons/DynamicDataCreateConfiguration.svg"))
            self.dd = dd
            self.configuration = {}
            self.curLineEdit = None #used only in event filter and handleCtrlTab()
            hasConfig = self.getConfigurationFromObject()
            lay = QtGui.QVBoxLayout(self)
            self.setLayout(lay)
            self.nameRow = QtGui.QHBoxLayout()
            lay.addLayout(self.nameRow)
            self.configurationNameLabel = QtGui.QLabel("Configuration name:")
            self.nameRow.addWidget(self.configurationNameLabel)
            self.configurationName = QtGui.QLineEdit()
            self.configurationName.setToolTip(\
"Configuration name will be the name given to \n\
the Enumeration property created and to the Group \n\
all the properties go into.")
            self.configurationName.setText(self.configuration["name"])
            self.configurationName.selectAll()
            self.configurationName.textChanged.connect(self.updateDict)
            self.nameRow.addWidget(self.configurationName)
            self.enumCountLabel = QtGui.QLabel("Enum count:")
            self.enumCount = QtGui.QSpinBox()
            self.enumCount.setMinimum(2)
            self.enumCount.setMaximum(100)
            self.enumCount.setSingleStep(1)
            self.enumCount.setValue(self.configuration["enumCount"])
            self.enumCount.valueChanged.connect(self.updateDict)
            self.enumCount.setToolTip( \
"This is the number of configuration options you \n\
will have, for example: small, medium, large would \n\
be 3.")
            self.nameRow.addWidget(self.enumCountLabel)
            self.nameRow.addWidget(self.enumCount)
            self.variableCountLabel = QtGui.QLabel("Variable count:")
            self.nameRow.addWidget(self.variableCountLabel)
            self.variableCount = QtGui.QSpinBox()
            self.variableCount.setMinimum(2)
            self.variableCount.setMaximum(100)
            self.variableCount.setSingleStep(1)
            self.variableCount.setValue(self.configuration["variableCount"])
            self.variableCount.valueChanged.connect(self.updateDict)
            self.variableCount.setToolTip( \
"This is the number of variables you will have \n\
in the configuration.  For example, if you want \n\
Height, Width, and Length, enter 3 here.")
            self.nameRow.addWidget(self.variableCount)

            self.grid_scroller = QtGui.QScrollArea()
            self.gridLayout = QtGui.QGridLayout()
            lay.addWidget(self.grid_scroller)
            #lay.addLayout(self.gridLayout)
            self.gridWidget= QtGui.QWidget()
            self.gridWidget.setLayout(self.gridLayout)
            self.grid_scroller.setWidget(self.gridWidget)
            self.grid_scroller.setWidgetResizable(True)
            self.setupGrid()
            self.buttonLayout = QtGui.QHBoxLayout()
            lay.addLayout(self.buttonLayout)
            self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok.__or__(QtGui.QDialogButtonBox.Cancel),\
                QtCore.Qt.Horizontal, self)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            self.helpCheckBox = QtGui.QCheckBox("Show help")
            self.helpCheckBox.setChecked(False)
            self.helpCheckBox.clicked.connect(self.showHelp)
            self.buttonLayout.addWidget(self.helpCheckBox)
            self.buttonLayout.addWidget(self.buttons)
            self.helpLabel = QtGui.QLabel("Help goes here.")
            self.setupHelpText()
            self.scroll_area = QtGui.QScrollArea()
            lay.addWidget(self.scroll_area)
            self.scroll_area.setWidget(self.helpLabel)
            self.scroll_area.setVisible(False)

            if hasConfig:
                self.fillUpLineEdits()

        def setupHelpText(self):
            txt = """\
A configuration is a set of properties that work together to allow you to set multiple
properties by selecting the configuration you want in an enumeration property.  The
enumeration property is at the heart of the configuration.  The Configuration name: field
will be the name of this enumeration property.  It will also be the name of the group that
the variable properties go into and the name of another group + the word "Lists" that the
list properties will go into.

For example, if the name of the configuration is "Configuration" then you will have a group
named "Configuration" and inside that group an Enumeration property also named "Configuration".
Plus, you will have another group named "Configuration Lists" and inside that group will be a
number of FloatList properties, one for each variable you have.  If you have these 3 variables:
"Height", "Width", and "Length", then in the Configuration group you will have 3 Float properties
of the same name and in the Configration List group there will be "Height List", "Width List",
and "Length List", all FloatList types.

We have 3 different property types: 1) the enumeration property that serves as the configuration
selector; 2) the variable properties (whose names are in the left column, e.g. Height, or Radius);
and 3) the list properties that hold the values the variable properties index into based on which
configuration has been selected.  All variable properties are of type Float and all list properties
are of type FloatList.  (You can replace them with Integer or String property types if you like
after building the configuration by deleting them and adding new properties with the same name,
but if you use the configuration editor to edit the configuration later they will be replaced
again with Float and FloatList types.)

Enum count is how many enums we have in this configuration.  The default is 5, which are "Extra
Small", "Small", "Medium", "Large", and "Extra Large".  "Select size" is not really an enum, but
it will go into the enumeration as a default message to the user.  Edit this so it makes sense
for the enums you are using.  Edit all of these enums by changing their text.  You can remove some
by reducing the Enum count, which can be anywhere from 2 to 100.  You must have at least 2 enums
in the configuration.  Note: when you reduct Enum count or Variable count you lose those rows or
columns, including any data contained in the cells, even if you increase the count afterwards.
When you increase the count you get another row or column with generic names like Variable5 or
Enum7.

Enter the values in the cells that you want for each enum and variable.  In the example default
configuration you have Height, for example.  If you want the Height for the Extra Small enum to
be 2, enter 2 in the cell that aligns with Height and Extra Small.  Any cells left blank will be
filled with the value from the first cell in that row, or 0.0 if it is also blank.

Note: when the "Select size" enum is selected in the enumeration property all of the variable
values will be the value from the first enum, so that it won't break your model until you can
select one of the enums.  Select size is actually an additional extra set of values added to the
ends of the List properties.  You can manually edit these later if you want different defaults.
Your manually edited defaults will not be changed by the editor unless you also change the
number of enums during the edit.

You may apply a configuration to an existing object, such as a Part::Cylinder, and if your variable
names are the same as existing properties, those properties will be incorporated into the configuration.

You may have multiple configurations in the same object, but if you do so you should ensure none of
the variable are the same or else there will be a conflict and the new properties will overwrite the
existing ones.  It is recommended to only have 1 configuration per object.

Variable count is how many variables to have in the configuration.  By default we have 3.  These are:
"Height", "Length", and "Radius".  This are likely not to be the names you will want for your
configuration.  They are just there as placeholders to serve as examples in the default configuration.
You can add more or remove some by changing the Variable count value.

If you click Cancel your changes will be discarded.  If you click OK your configuration will be added
to the selected object.  ANY EXISTING PROPERTIES of the same names WILL BE REPLACED.  But have no fear,
you can use Undo to revert all your changes to the selected object.

"""
            self.helpLabel.setText(txt)

        def showHelp(self):
            self.scroll_area.setVisible(self.helpCheckBox.isChecked())

        def eventFilter(self, obj, event):
            if event.type() == QtGui.QKeyEvent.KeyPress:
                if bool(event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Tab):
                    self.curLineEdit = obj
                    self.handleCtrlTab(False)
                    return True  # Event handled

                elif bool(event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Backtab):
                    self.curLineEdit = obj
                    self.handleCtrlTab(True)
                    return True  # Event handled

            return super().eventFilter(obj, event)

        def handleCtrlTab(self, bShift = False):
            row,col = self.getRowColFromObjectName(self.curLineEdit.objectName())
            objName = f"{row + 1}_{col}" if not bShift else f"{row - 1}_{col}"
            next = self.getLineEditFromConfiguration(objName, bCreate = False)
            if not next:
                return
            else:
                next.setFocus()


        def getLineEditFromConfiguration(self, objName, bCreate = True):
            """get the line edit objName from dictionary if it exists, else created it"""
            lineEdit = None
            for name,obj in self.configuration["lineEdits"].items():
                if name == objName:
                    lineEdit = obj
                    break
            if not lineEdit and bCreate:
                lineEdit = QtGui.QLineEdit()
                lineEdit.setObjectName(objName)
                lineEdit.installEventFilter(self)
                lineEdit.setToolTip("Tab -> next column\nCtrl+Tab -> next row\nCtrl+Shift+Tab ->previous row\nShift+Tab -> previous column")
            elif not bCreate and not lineEdit:
                return None
            self.configuration["lineEdits"][objName] = lineEdit
            return lineEdit

        def addToGrid(self, lineEdit, row, col):
            """add the LineEdit to the grid at row, col"""
            def trigger(objName):
                self.lineEditTextChanged(objName)
            self.gridLayout.addWidget(lineEdit, row, col)
            label = ""
            if row == 0:
                try:
                    label = self.configuration["enums"][col]
                except (IndexError, KeyError):
                    label = f"Enum{col}"
                    self.configuration["enums"].append(f"Enum{col}")
            elif col == 0:
                try:
                    label = self.configuration["variables"][row-1]
                except (IndexError, KeyError):
                    self.configuration["variables"].append(f"Variable{row}")
                    label = f"Variable{row}"
            lineEdit.setText(label)
            lineEdit.textChanged.connect(lambda text,name=lineEdit.objectName(): trigger(name))
            self.gridLayout.addWidget(lineEdit,row,col)
            self.update()
            FreeCADGui.updateGui()

        def updateTabOrders(self):
            """update the tab orders when adding/removing lineEdit to/from grid"""
            def custom_sort(s):
                # Split the string into parts
                parts = s.split('_')

                # Convert the parts to integers
                x = int(parts[0])
                y = int(parts[1])

                # Combine them using a formula
                return x * 100 + y

            names = {}
            for name,obj in self.configuration["lineEdits"].items():
                names[name] = obj.objectName()
            names = sorted(names, key=custom_sort)
            edits = [self.configuration["lineEdits"][name] for name in names]
            for ii in range(len(edits)-1):
                self.setTabOrder(edits[ii], edits[ii+1])

        def removeFromGrid(self, le):
            """remove the line edit from the grid and from the dictionary"""

            if le.objectName() in self.configuration["lineEdits"].keys():
                val = self.configuration["lineEdits"].pop(le.objectName())
            row,col = self.getRowColFromObjectName(le.objectName())
            widget = self.gridLayout.itemAtPosition(row,col)
            if widget:
                widget.widget().deleteLater()
            self.update()
            FreeCADGui.updateGui()

        def setupGrid(self):
            """setup the grid based on the values in self.configuration dictionary"""
            for row in range(self.configuration["variableCount"]+1):
                for col in range(self.configuration["enumCount"]+1):
                    lineEdit = self.getLineEditFromConfiguration(f"{row}_{col}")
                    self.addToGrid(lineEdit, row, col)

        def lineEditTextChanged(self, lineEditObjectName):
            lineEdit = self.getLineEditFromConfiguration(lineEditObjectName)
            row,col = self.getRowColFromObjectName(lineEditObjectName)
            if row == 0:
                self.configuration["enums"][col] = lineEdit.text()
            elif col == 0:
                self.configuration["variables"][row-1] = lineEdit.text()

        def getRowColFromObjectName(self, objName):
            """returns a tuple (row,col) gotten from the line edit object name
               which is always in the form of row_col"""
            row,col = objName.split("_")
            row = int(row)
            col = int(col)
            return (row,col)

        def isOutOfBounds(self, lineEdit):
            """check if this line edit object needs to be removed from the grid
               by comparing its row,col to enum count and variable count"""
            row,col = self.getRowColFromObjectName(lineEdit.objectName())
            enums = self.enumCount.value()
            variables = self.variableCount.value()
            if col  > enums:
                return True
            if row  > variables:
                return True
            return False

        def updateDict(self):
            """called only when the enum count or variable count changes
               in which cases we need to update the grid of line edits
               updates the dictionary (self.configuration) based on values in form"""
            self.configuration["name"] = self.configurationName.text()
            self.configuration["enumCount"] = self.enumCount.value()
            self.configuration["variableCount"] = self.variableCount.value()

            lineEditsToRemove = [le for le in self.configuration["lineEdits"].values() if self.isOutOfBounds(le)]
            for le in lineEditsToRemove:
                row,col = self.getRowColFromObjectName(le.objectName())
                if row == 0:
                    self.configuration["enums"].pop()
                if col == 0:
                    self.configuration["variables"].pop()
                self.removeFromGrid(le)
            # if lineEditsToRemove:
            #     return
            # now we need to see if we need to add any rows or columns
            numRows = len(self.configuration["variables"])
            numCols = len(self.configuration["enums"])
            enums = self.enumCount.value()
            variables = self.variableCount.value()

            while numCols < enums + 1:
                #need to add a new column, so for each row we add one
                for row in range(numRows+1):
                    lineEdit = self.getLineEditFromConfiguration(f"{row}_{numCols}")
                    self.addToGrid(lineEdit, row, numCols)
                numCols = len(self.configuration["enums"])

            while numRows < variables:
                #need to a new row, so for each column we add one
                for col in range(numCols):
                    lineEdit = self.getLineEditFromConfiguration(f"{numRows+1}_{col}")
                    self.addToGrid(lineEdit, numRows+1, col)
                numRows = len(self.configuration["variables"])
            self.updateTabOrders()

        def getRowValues(self,row):
            """get the line edit values in row as a list"""
            ret = []
            for col,enum in enumerate(self.configuration["enums"]):
                objName = f"{row+1}_{col+1}"
                lineEdit = self.getLineEditFromConfiguration(objName)
                val = 0
                try:
                    val = float(lineEdit.text())
                except (ValueError, TypeError):
                    if lineEdit.text():
                        FreeCAD.Console.PrintWarning(f"Couldn't convert to float: {lineEdit.text()} row,col = {row},{col}\n")
                    else:
                        #take value from first cell in row and use that for default
                        firstCell = self.getLineEditFromConfiguration(f"{row+1}_{1}")
                        try:
                            val = float(firstCell.text())
                        except (ValueError, TypeError):
                            val = 0
                ret.append(val)
            return ret

        def setConfiguration(self):
            """setup the configuration"""
            dd = self.dd
            name = self.configuration["name"]
            if hasattr(dd,name):
                try:
                    dd.removeProperty(name)
                except Exception:
                    FreeCAD.Console.PrintWarning(f"Unable to remove property: {name}\n")
            if not hasattr(dd,name):
                dd.addProperty("App::PropertyEnumeration",name,name,"Configuration enumeration")
            setattr(dd,name,self.configuration["enums"])
            for row,var in enumerate(self.configuration["variables"]):
                if hasattr(dd,f"{var}List"):
                    try:
                        dd.removeProperty(f"{var}List")
                        FreeCAD.Console.PrintMessage(f"Removed property {var}List\n")
                    except Exception:
                        FreeCAD.Console.PrintWarning(f"Unable to remove property: {var}List\n")
                if not hasattr(dd,f"{var}List"):
                    dd.addProperty("App::PropertyFloatList",f"{var}List",f"{name}Lists",f"List property for {var}")
                    FreeCAD.Console.PrintMessage(f"Added property {var}List\n")
                setattr(dd,f"{var}List", self.getRowValues(row))
                if hasattr(dd,var):
                    try:
                        dd.removeProperty(var)
                        FreeCAD.Console.PrintMessage(f"Removed property {var}\n")
                    except Exception:
                        FreeCAD.Console.PrintWarning(f"Unable to remove property: {var}\n")
                if not hasattr(dd,var):
                    dd.addProperty("App::PropertyFloat",var,name,"Property to link to")
                    FreeCAD.Console.PrintMessage(f"Added property {var}\n")
                dd.setExpression(var,f"{dd.Label}.<<{dd.Label}>>.{var}List[<<{dd.Label}>>.{name}-1]")

        def getConfigurationFromObject(self):
            """return True if we imported one from an object, else False if this is a new configuration"""
            dd = self.dd
            ignored = ["MapMode"]
            props = [prop for prop in dd.PropertiesList if "Enumeration" in dd.getTypeIdOfProperty(prop) and prop not in ignored]

            if len(props) >= 1:
                default_item = 0
                props = ["New configuration"] + props
                prop, ok = QtGui.QInputDialog.getItem(self, "Select configuration", \
                                                      "Choose an enumeration to edit or create a new one\n (Cancel for a new default configuration)",\
                                                       props, default_item, editable=False)
                if not ok or prop == props[0]:
                    self.makeDefaultConfiguration()
                    return False
                else:
                    self.importConfiguration(prop)
                    return True

            else: #no existing enumerations
                self.makeDefaultConfiguration()
                return False

        def importConfiguration(self,prop):
            """imports the configuration from the object where prop is the name of the enumeration"""
            self.configuration["name"] = prop
            self.configuration["enums"] = self.dd.getEnumerationsOfProperty(prop)
            vars = [prop2 for prop2 in self.dd.PropertiesList if hasattr(self.dd,f"{prop2}List")]
            #lists = [prop for prop in dd.PropertiesList if hasattr(dd,prop[:-4])] #drop List from end of property name
            self.configuration["variables"] = vars
            self.configuration["lineEdits"] = {}
            self.configuration["enumCount"] = len(self.configuration["enums"])-1
            self.configuration["variableCount"] = len(vars)

        def makeDefaultConfiguration(self):
            self.configuration["name"] = "Configuration"
            self.configuration["enumCount"] = 5
            self.configuration["variableCount"] = 3
            self.configuration["enums"] = ["Select size","Extra Small","Small","Medium",\
                                        "Large","Extra Large"]
            self.configuration["variables"] = ["Length", "Height", "Radius"]
            self.configuration["lineEdits"] = {}

        def fillUpLineEdits(self):
            """called from __init__() only if dd object has a configuration already,
            so we are going to fill in the Line Edits from that data"""
            #look for List properties
            for var in self.configuration["variables"]:
                lists = [prop for prop in self.dd.PropertiesList if prop == f"{var}List"]
                for ls in lists:
                    values = getattr(self.dd, ls) #e.g. HeightList = [10,20,30], now values = [10,20,30]
                    row = self.configuration["variables"].index(var)
                    for col,val in enumerate(values):
                        lineEdit = self.getLineEditFromConfiguration(f"{row+1}_{col+1}")
                        lineEdit.setText(str(round(val,6)))

        def accept(self):
            self.dd.Document.openTransaction("Create/Edit Configuration")
            self.setConfiguration()
            self.dd.Document.commitTransaction()
            super().accept()

        def reject(self):
            super().reject()


    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'DynamicDataCreateConfiguration.svg'),
                'MenuText': "创建/编辑配置(&F)",
                'Accel'   : "Ctrl+Shift+D,F",
                'ToolTip' : "在选中对象中创建或编辑一套属性配置系统"}

    def __init__(self):
        self.props = []
        self.obj = None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        dlg = self.DynamicData2ConfigurationDlg(self.obj) #self.obj is the selected object
        dlg.props = self.props
        dlg.exec_()
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1:
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                return True
        return False


#Gui.addCommand("DynamicData2CreateConfiguration", DynamicData2CreateConfigurationCommandClass())


####################################################################################
# Edit an existing Enumeration property

class DynamicData2EditEnumerationCommandClass(DynamicData2BaseCommandClass):
    """Edit Enumeration command"""

    class DynamicData2EnumerationDlg(QtGui.QDialog):
        def __init__(self,dd,props):
            super(DynamicData2EditEnumerationCommandClass.DynamicData2EnumerationDlg, self).__init__(Gui.getMainWindow())
            self.dd = dd
            self.ok = False
            self.props = props
            self.items = []
            self.enumerations = {}
            self.setupEnumerations()
            self.setAttribute(QtCore.Qt.WA_WindowPropagation, True)
            self.setWindowTitle(f"DynamicData2 v{__version__} Enumeration Editor")
            lay = QtGui.QVBoxLayout(self)
            self.setLayout(lay)
            self.propertiesLabel = QtGui.QLabel("Enumeration Properties:")
            self.propertiesListBox = QtGui.QListWidget(self)

            for prop in self.props:
                item = QtGui.QListWidgetItem(prop)
                self.items.append(item)
                self.propertiesListBox.addItem(item)

            self.propertiesListBox.setSelectionMode(QtGui.QListWidget.SingleSelection)
            self.propertiesListBox.itemClicked.connect(self.handlePropertiesListBoxItemClicked)
            if self.items:
                self.propertiesListBox.setCurrentItem(self.items[0])
            lay.addWidget(self.propertiesLabel)
            lay.addWidget(self.propertiesListBox)
            self.textEditLabel = QtGui.QLabel("Edit the selected property by typing here:")
            lay.addWidget(self.textEditLabel)

            self.textEdit = QtGui.QPlainTextEdit()
            self.textEdit.textChanged.connect(self.textChanged)
            lay.addWidget(self.textEdit)
            self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok.__or__(QtGui.QDialogButtonBox.Cancel),\
                QtCore.Qt.Horizontal, self)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            lay.addWidget(self.buttons)
            self.setupTextEdit()

        def handlePropertiesListBoxItemClicked(self, item):
            """a new enumeration property was selected, so set the QPlainTextEdit"""
            self.updateTextEdit()

        def textChanged(self):
            """The QPlainTextEdit changed, so update enums"""
            self.updateEnumerations()

        def setupEnumerations(self):
            """setup enums from the dd object enumerations"""
            for prop in self.props:
                if not prop in self.enumerations:
                    self.enumerations[prop] = self.dd.getEnumerationsOfProperty(prop)

        def updateEnumerations(self):
            """update enums from QPlainTextEdit"""
            prop = self.getCurrentProp()
            self.enumerations[prop] = self.getTextEditStrings()

        def getCurrentProp(self):
            return self.props[self.propertiesListBox.currentRow()]

        def setupTextEdit(self):
            """puts the text into the QPlainTextEdit from the dd object enumeration properties"""
            if self.props:
                prop = self.props[self.propertiesListBox.currentRow()]
                enums = self.dd.getEnumerationsOfProperty(prop)
                textString = "\n".join(enums)
                self.textEdit.setPlainText(textString)

        def updateTextEdit(self):
            """update the QPlainTextEdit from enums"""
            prop = self.props[self.propertiesListBox.currentRow()]
            enums = self.enumerations[prop]
            textString = "\n".join(enums)
            self.textEdit.setPlainText(textString)

        def getTextEditStrings(self):
            """return the text edit contents as a list of strings"""
            txt = self.textEdit.toPlainText()
            split_text = txt.split("\n")
            return split_text

        def accept(self):
            self.ok = True
            super().accept()

        def reject(self):
            super().reject()


    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'DynamicDataEditEnumerations.svg'),
                'MenuText': "编辑枚举(&E)",
                'Accel'   : "Ctrl+Shift+D,E",
                'ToolTip' : "编辑选中对象中的枚举（下拉列表）类型属性"}

    def __init__(self):
        self.props = []
        self.obj = None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not self.props:
            FreeCAD.Console.PrintError("DynamicData2: Error, no property of type \
Enumeration to edit.  Create one first, and then try again.\n")
            return

        dlg = self.DynamicData2EnumerationDlg(self.obj, self.props) #the dd object
        dlg.props = self.props
        dlg.exec_()
        if dlg.ok:
            doc.openTransaction("Edit Enumeration")
            self.setEnumerations(dlg.enumerations)
            doc.commitTransaction()
        doc.recompute()
        return

    def setEnumerations(self, enum_dict):
        """set the properties of type Enumeration of the dd object from the dictionary enum_dict"""
        dd = self.obj
        for k,v in enum_dict.items():
            setattr(dd,k,v)

    def getEnumerations(self, dd):
        """get the properties of type Enumeration in the selected object
           return the list of such properties or [] if none.  We don't verify
           this is a dd object because we will support all objects, but we will
           ignore some known enumeration properties, such as MapMode"""

        ignored = ["MapMode"]
        self.props = [prop for prop in dd.PropertiesList if bool (not prop in ignored and "App::PropertyEnumeration" in dd.getTypeIdOfProperty(prop))]
        return self.props

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1 and self.getEnumerations(selection[0]):
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object if it has an enumeration property
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                if self.getEnumerations(self.obj):
                    return True
        return False


#Gui.addCommand("DynamicData2EditEnumeration", DynamicData2EditEnumerationCommandClass())

####################################################################################
# dialog for adding new property

class EvalError(Exception):
    def __init__(self, message="Evaluation error occurred"):
        self.message = message
        super().__init__(self.message)

class MultiTextInput(QtGui.QDialog):
    def __init__(self, obj, cmd):
        QtGui.QDialog.__init__(self)
        self.obj = obj
        self.cmd = cmd #cmd is the command class
        layout = QtGui.QGridLayout()
        #layout.setColumnStretch(1, 1)
        self.addAnotherProp = False
        self.label = QtGui.QLabel(self)
        self.objLabelPrefix = QtGui.QLabel("Target object:")
        self.objLabel = QtGui.QLabel("")
        self.objIcon = QtGui.QLabel()
        obj_label = self.obj.Label
        if self.obj.Name != obj_label:
            obj_label = f"{self.obj.Label} ({self.obj.Name})"
        self.objLabel.setText(obj_label)
        self.objIcon.setPixmap(self.obj.ViewObject.Icon.pixmap(32,32))
        self.label.setText("In Value field:\nUse =expr for expressions, e.g. =Box.Height\n")
        self.propertyTypeLabel = QtGui.QLabel("Select App::Property type:")
        self.listWidget = QtGui.QListWidget()
        self.listWidget.currentItemChanged.connect(self.onListWidgetCurrentItemChanged)
        self.label2 = QtGui.QLabel("")
        self.label2.setStyleSheet("color: red;")
        self.label3 = QtGui.QLabel("")
        self.label3.setStyleSheet("color: red;")
        self.label4 = QtGui.QLabel("")
        self.nameLabel = QtGui.QLabel("Name: ")
        self.nameEdit = QtGui.QLineEdit(self)
        self.nameEdit.textChanged.connect(self.on_text_changed)
        self.valueLabel = QtGui.QLabel("Value: ")
        self.valueEdit = QtGui.QLineEdit(self)
        self.valueEdit.textChanged.connect(self.on_value_changed)
        self.groupLabel = QtGui.QLabel("Group: ")
        self.groupCombo = QtGui.QComboBox(self)
        self.groupCombo.setEditable(True)
        self.tooltipLabel = QtGui.QLabel("Tooltip: ")
        self.tooltipPrependLabel = QtGui.QLabel("")
        self.tooltipEdit = QtGui.QLineEdit(self)

        layout.addWidget(self.label, 0, 0, 2, 5)
        layout.addWidget(self.objLabelPrefix, 2, 0, 1, 1)
        layout.addWidget(self.objLabel, 2, 2, 1, 2)
        layout.addWidget(self.objIcon, 2, 1, 1, 1)
        layout.addWidget(self.propertyTypeLabel, 3, 0, 1, 6)
        layout.addWidget(self.listWidget, 4, 0, 1, 6)
        layout.addWidget(self.nameLabel, 5, 0, 1, 1)
        layout.addWidget(self.nameEdit, 5, 1, 1, 5)
        layout.addWidget(self.label4, 6, 1, 1, 5)
        layout.addWidget(self.valueLabel, 7, 0, 1, 1)
        layout.addWidget(self.valueEdit, 7, 1, 1, 5)
        layout.addWidget(self.groupLabel, 8, 0, 1, 1)
        layout.addWidget(self.groupCombo, 8, 1 , 1, 5)
        layout.addWidget(self.tooltipLabel, 9, 0, 1, 1)
        layout.addWidget(self.tooltipPrependLabel, 9, 1, 1, 1)
        layout.addWidget(self.tooltipEdit, 9, 2, 1, 4)
        layout.addWidget(self.label2, 10, 0, 1, 5)
        layout.addWidget(self.label3, 11, 0, 1, 5)
        self.buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok.__or__(QtGui.QDialogButtonBox.Cancel),
            QtCore.Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.setCenterButtons(True)
        addAnother = QtGui.QPushButton("Apply", self)
        self.buttons.addButton(addAnother, QtGui.QDialogButtonBox.ActionRole)
        addAnother.clicked.connect(self.addAnotherProperty)
        layout.addWidget(self.buttons, 12, 0, 1, 5)
        self.setLayout(layout)

    def addAnotherProperty(self):
        """user has clicked Apply button, so this informs parent command
        class to reopen the dialog after adding property"""
        self.addAnotherProp = True
        self.accept()

    @property
    def Current(self):
        return self.listWidget.currentItem().text()

    def onListWidgetCurrentItemChanged(self,current,previous):
        """when the user selects a different property type, suggest a name for the property"""
        candidate = self.cmd.getNewPropertyNameCandidate(self.obj, current.text())
        self.nameEdit.setText(candidate)
        self.tooltipPrependLabel.setText(f"[{current.text()}]")
        defaults = {
            "Angle": "32 deg or pi rad or 45",
            "Color": "(255,0,0) or red or #ff0000",
            "Direction": "create(<<vector>>; 0; 0; 0)",
            "Enumeration": """["small";"medium";"large"]""",
            "File": "c:/users/username/Documents/freecad/macros",
            "FloatConstraint": "(0;-360;360;15) = (initial, min, max, step)",
            "FloatList": "(1;2;3)",
            "Font": "Arial",
            "Length": "6' + 2\" or 5m or 17",
            "Vector": "create(<<vector>>; 0; 0; 0)",
            "VectorDistance": "create(<<vector>>; 0; 0; 0)",
            "VectorList": "((1;2;3);(4;5;6))",
            "IntegerConstraint": "(0;-360;360;45) = (initial, min, max, step)",
            "IntegerList": "(1;2;3;4)",
            "Link": "ObjectNameOrLabel",
            "LinkChild": "ObjectNameOrLabel",
            "LinkGlobal": "ObjectNameOrLabel",
            #"LinkSubList": "[(Object1NameOrLabel,(Face1,Edge2)),(Object2NameOrLabel,(Vertex1))]",
            "LinkSubList": "[(Extrude,(Face1,Edge2)),(Sketch,(Vertex1))]",
            "PlacementLink": "ObjectNameOrLabel",
            "Position": "create(<<vector>>;10;20;30)",
            "Matrix": "((1;0;0;0),(0;1;0;0),(0;0;1;0),(0;0;0;1))",
            "Path": "c:/users/username/documents",
            "LinkList": "[Obj1,Obj2,Obj3]",
            "Placement": "create(<<placement>>; create(<<vector>>;10;20;30); create(<<rotation>>; create(<<vector>>;1;0;0);45))",
            "Rotation": "create(<<rotation>>; create(<<vector>>;1;0;0);45)",
            "String": "Your string here",
            "StringList": "[a;b;c]",
            "Temperature": "0.00 K",
            "Precision": "1e-7",



        }
        if current.text() in defaults.keys():
            self.valueEdit.setPlaceholderText(defaults[current.text()])
        else:
            self.valueEdit.setPlaceholderText("")
        self.on_value_changed()

    def on_value_changed(self):
        """this just provides a pre-evaluation of the value and displays in a label"""
        val = self.valueEdit.text()
        skiplist = ["StringList","Font"]
        if self.Current in skiplist:
            self.label4.setText("")
            return
        elif self.Current == "Temperature":
            if "C" in val or "F" in val:
                self.label4.setStyleSheet("color:red;")
                self.label4.setText("Note: F and C units not supported.")
            else:
                self.label4.setText(val)
                self.label4.setStyleSheet("color:black;")
            return
        elif self.Current == "LinkSubList":
            try:
                txt = self.cmd.getLinkSubList(val)
                self.label4.setText(f"{txt}")
                self.label4.setStyleSheet("color:black;")
            except EvalError as ev:
                self.label4.setText(ev.message)
                self.label4.setStyleSheet("color:red;")
            return
        elif self.Current == "LinkList" or self.Current == "LinkListGlobal" or self.Current == "LinkListChild":
            try:
                txt = self.cmd.getLinkList(val)
                self.label4.setText(f"{txt}")
                self.label4.setStyleSheet("color:black;")
            except EvalError as ev:
                self.label4.setText(ev.message)
                self.label4.setStyleSheet("color:red;")
            return
        elif self.Current == "Link" or self.Current == "LinkChild" or self.Current == "LinkGlobal":
            txt = self.cmd.getLink(val)
            self.label4.setText(f"{txt}")
            self.label4.setStyleSheet("color:black;")
            return
        elif self.Current == "Color":
            if not val:
                self.label4.setText("")
                return
            clr = self.cmd.getColor(val)
            if clr:
                self.label4.setText(f"{clr}")
                clr2 = tuple(255-c for c in clr)
                self.label4.setStyleSheet(f"color: rgb{clr2};background-color: rgb{clr};")
            else:
                self.label4.setText("Invalid color")
                self.label4.setStyleSheet("color:red;")
            return
        result = "invalid"
        if not val:
            self.label4.setText("")
            return
        if val.startswith("="):
            val = val[1:]
            try:
                result = f"{self.cmd.eval_expr(val)}"
                self.label4.setStyleSheet('color: black')
                self.label4.setText(str(result))
            except EvalError as ev:
                self.label4.setStyleSheet('color: red')
                self.label4.setText(ev.message)
        else:
            self.label4.setStyleSheet('color: black')
            self.label4.setText(val)


    def on_text_changed(self):
        """handler for the property name field when it changes"""
        name = self.nameEdit.text()
        if ";" in name:
            name = name[:name.index(";")]
        #label2 is for invalid name messages
        #later label3 shows where there is a conflict with an existing name
        if not self.cmd.isValidName(self.obj, name):
            if name:
                self.label2.setText(f"{name} is not a valid name, suggestion: {self.cmd.fixName(self.obj, name)}")
            else:
                self.label2.setText("Name field cannot be empty.")
        else:
            self.label2.setText("")

        self.on_edit_finished()

    def on_edit_finished(self):
        """we still support the original semicolon-delimited way of adding properties
        in a single QLineEdit even though that was very user-unfriendly"""
        if ";" in self.nameEdit.text():
            hasValue = False
            propertyName = self.nameEdit.text()
            split = propertyName.split(';')
            propertyName = split[0].replace(' ','_')
            if len(propertyName) == 0:
                propertyName = "Prop"
            if len(split)>1: #has a group name
                if len(split[1])>0: #allow for ;; empty string to mean use current group name
                    self.groupCombo.setCurrentText(split[1])
            if len(split)>2: #has a tooltip
                if len(split[2])>0:
                    self.tooltipEdit.setText(split[2])
            if len(split)==4: #has a value
                hasValue = True
                val = split[3]
            self.groupCombo.setEnabled(False)
            if hasValue:
                self.valueEdit.setText(val)
            self.valueEdit.setEnabled(False)
            self.tooltipEdit.setEnabled(False)
        else:
            self.groupCombo.setEnabled(True)
            self.valueEdit.setEnabled(True)
            self.tooltipEdit.setEnabled(True)
            propertyName = self.nameEdit.text()
        if hasattr(self.obj,propertyName):
            self.label3.setText(f"Property name already exists, suggestion: {self.cmd.getNewPropertyNameCandidate(self.obj, propertyName)}")
        else:
            self.label3.setText('')


######################################################################################
# Add a dynamic property to the object


class DynamicData2AddPropertyCommandClass(DynamicData2BaseCommandClass):
    """Add Property Command"""
    global mostRecentTypes
    global mostRecentTypesLength

    def __init__(self):
        #global mostRecentTypes
        global mostRecentTypesLength
        import locale
        import operator as op
        self.obj = None #set in IsActive()
        self.groupName = "DefaultGroup"
        self.defaultPropertyName = "Prop"
        self.tooltip = "tip"
        self.value = 0

        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2")
        mostRecentTypesLength = pg.GetInt('mruLength',5)
        for ii in range(0, mostRecentTypesLength):
            mostRecentTypes.append(pg.GetString('mru'+str(ii),""))

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'AddProperty.svg'),
                'MenuText': "添加属性(&A)",
                'Accel'   : "Ctrl+Shift+D,A",
                'ToolTip' : "Add a custom property to the DynamicData2 object"}

    def Activated(self):
        """Open the table-based property editor (like SW custom properties)."""
        import sys
        _dir = os.path.dirname(__file__)
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from PropertyTableEditor import PropertyTableEditor
        dlg = PropertyTableEditor(self.obj, self)
        dlg.exec_()

    def getLinkSubList(self, userstring):
        """userstring will be in form
        [(ObjectNameOrLabel,(Sub1,Sub2,Sub3...),(Object2NameOrLabel,(Face1,Vertex2,...))]
        this converts to the list of tuples needed for setting a LinkSubList property"""
        if not userstring:
            return []
        cleaned = re.sub(r'(\w+)', r'"\1"', userstring)
        try:
            names = ast.literal_eval(cleaned)
        except (ValueError, SyntaxError):
            raise EvalError(f"cannot evaluate {userstring}")
        links = [self.getObjectByNameOrLabel(name[0]) if self.getObjectByNameOrLabel(name[0]) else None for name in names ]
        links2 = []
        for idx,link in enumerate(links):
            links2.append((links[idx],names[1]))
        return links2

    def getLinkList(self, userstring):
        """userstring will be in the form:
        [ObjectNameOrLabel,Object2NameOrLabel,...]
        this converts to [<Part::Feature>,<Part::Feature>]"""
        if not userstring:
            return []
        cleaned = re.sub(r'(\w+)', r'"\1"', userstring)
        try:
            names = ast.literal_eval(cleaned)
        except (ValueError, SyntaxError):
            raise EvalError(f"cannot evaluate {userstring}")
        links = [self.getObjectByNameOrLabel(name) if self.getObjectByNameOrLabel(name) else None for name in names]
        return links

    def getLink(self, userstring):
        """userstring will be of the form ObjectNameOrLabel"""
        link = self.getObjectByNameOrLabel(userstring)
        return link

    def getObjectByNameOrLabel(self, nameOrLabel):
        """returns None if object is not found"""
        doc = self.obj.Document
        retval = doc.getObject(nameOrLabel)
        if retval:
            return retval
        retval = doc.getObjectsByLabel(nameOrLabel)
        if retval:
            return retval[0]
        return None

    def getColor(self, userstring):
        """user might enter 'red' or 'green' or (255,255,255)
           all should be returned in form of (255,255,255)"""
        # Try to match the input with a tuple
        tuple_match = re.match(r'\((\d+),(\d+),(\d+)\)', userstring.replace(";",","))
        if tuple_match:
            return tuple(map(int, tuple_match.groups()))

        # Check if the input matches a color name
        color = QtGui.QColor(userstring.replace(";",","))
        if color.isValid():
            return color.red(), color.green(), color.blue()

        # Try to match the input as a hexadecimal value
        hex_match = re.match(r'#([0-9a-fA-F]{6})', userstring.replace(";",","))
        if hex_match:
            hex_value = hex_match.group(1)
            return tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))

        # If none of the patterns match, return None or handle the case accordingly
        return None


    def eval_expr(self, expr):
        if not expr:
            return ""
        try:
            retval = self.obj.evalExpression(expr)
            return retval
        except Exception:
            try:
                retval = ast.literal_eval(expr)
                return retval
            except (ValueError, SyntaxError):
                try:
                    retval = ast.literal_eval(expr.replace(";",","))
                    return retval
                except (ValueError, SyntaxError):
                    raise EvalError(f"Cannot evaluate {expr}\n")

    def checkAddAnother(self,dlg):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier or dlg.addAnotherProp: #Ctrl+OK or Apply
            dlg.deleteLater()
            self.Activated()

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1:
            self.obj = selection[0]
            return True
        #in case nothing is selected we can use the dd object, but only if there is only 1 dd object
        objs = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj, "DynamicData2")]
        if len(objs) == 1:
            self.obj = objs[0]
            return True
        return False



#Gui.addCommand("DynamicData2AddProperty", DynamicData2AddPropertyCommandClass())

########################################################################################
# Rename group

class DynamicData2MoveToNewGroupCommandClass(DynamicData2BaseCommandClass):
    """Move properties to new group"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join(iconPath , 'MoveToGroup.svg'),
                'MenuText': "移动到新组(&G)",
                'Accel'   : "Ctrl+Shift+D,G",
                'ToolTip' : "Move dynamic properties to new group.\n\
This effectively renames a group if you move all properties.\n\
Only works with dynamic properties"}

    def getPropertiesOfGroup(self,obj,group):
        props = [p for p in obj.PropertiesList if bool(obj.getGroupOfProperty(p) == group or group == "<All groups>") and self.isDynamic(obj,p)]
        return self.getSelectedObjects(props, "Select properties to move to new group", checkAll=True)

    def Activated(self):
        doc = self.obj.Document
        selection = Gui.Selection.getSelection()
        #remove the property
        window = FreeCADGui.getMainWindow()
        items = self.getGroups(self.obj)
        if not items:
            FreeCAD.Console.PrintError(f"DynamicData2::Error -- no groups of {self.obj.Label} may be renamed\n")
            return
        if len(items)==0:
            FreeCAD.Console.PrintMessage("DynamicData2: no properties.\n")
            return
        items.insert(0,"<All groups>")
        item,ok = QtGui.QInputDialog.getItem(window,'DynamicData2','Move properties to new group tool.\n\n\
This can be used to rename a group, by moving all properties to a new group.\n\
Select source group to pick properties from, or all groups to pick from all.\n', items, 0, False, windowFlags)
        if not ok:
            return
        else:
            props = self.getPropertiesOfGroup(self.obj, item)
            if props:
                toGroup = self.getGroups(self.obj,[item])
                items2 = ["<New group>"] + toGroup
                item2,ok = QtGui.QInputDialog.getItem(window,'DynamicData2','Move properties to new group tool\n\nSelect destination group\n'\
                            ,items2, 0, False, windowFlags)
                if not ok:
                    return
                if item2 == items2[0]:
                    newName,ok = QtGui.QInputDialog.getText(window, "Group name","Enter a new name for this group:",text="DefaultGroup")
                else:
                    newName = item2
                if not ok:
                    return
                doc.openTransaction("Move to new group")
                for prop in props:
                    try:
                        self.obj.setGroupOfProperty(prop, newName)
                        FreeCAD.Console.PrintMessage(f"Property {prop} move to group {newName}\n")
                    except Exception as ex:
                        FreeCAD.Console.PrintError(f"Cannot move {prop}, only dynamic properties are supported\n")
                doc.commitTransaction()
        #refresh property view
        if self.obj in selection:
            FreeCADGui.Selection.removeSelection(self.obj)
            FreeCADGui.Selection.addSelection(self.obj)
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1 and self.getDynamicProperties(selection[0]) and self.getGroups(selection[0]):
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                return True
        return False
########################################################################################
# Rename a custom dynamic property

class DynamicData2RenamePropertyCommandClass(DynamicData2BaseCommandClass):
    """Rename Property Command"""
    def __init__(self):
        self.obj = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join(iconPath , 'RenameProperty.svg'),
                'MenuText': "重命名属性(&N)",
                'Accel'   : "Ctrl+Shift+D,N",
                'ToolTip' : "Rename a dynamic property"}

    def getProperty(self,obj):
        props = self.getDynamicProperties(obj)
        if props:
            items = props
            if len(items) == 1:
                return items[0]
            item, ok = QtGui.QInputDialog.getItem(FreeCADGui.getMainWindow(), "Rename", "Select property to rename:", items, editable=False)
            if not ok:
                return []
            return item
        else:
            FreeCAD.Console.PrintError(f"{obj.Label} has no dynamic properties to rename\n")
            return None

    def getOutExpr(self, obj, prop):
        """get the expression set for this property, if any"""
        #expr will be a list of tuples[(propname, expression)]
        expressions = obj.ExpressionEngine
        expr = ""
        for expression in expressions:
            if prop == expression[0]:
                expr = expression[1]
        return expr

    def getNewPropertyName(self, obj, prop):
        """get from user new name for this property, ensure no conflict"""
        already = [p for p in obj.PropertiesList] #already have these property names
        newName, ok = QtGui.QInputDialog.getText(FreeCADGui.getMainWindow(), "Rename", f"Enter new name for {prop}:", QtGui.QLineEdit.EchoMode.Normal, prop)
        if not ok:
            return ""
        while ok and newName in already:
            newName, ok = QtGui.QInputDialog.getText(FreeCADGui.getMainWindow(), "Rename", f"Property already exists.  Enter new name for {prop}:", QtGui.QLineEdit.EchoMode.Normal, prop)
        return newName if ok else ""

    def getInExprs(self, obj, prop):
        """get the incoming expressions bound to this property
           returns a list of tuples in the form: [(object, propertyname, expression),]
        """
        inExprs = []
        inobjs = [obj] + [o for o in obj.InList]
        for inobj in inobjs:
            for expr in inobj.ExpressionEngine:
                if prop in expr[1]:
                    inExprs.append(tuple([inobj, expr[0], expr[1]]))
        return inExprs

    def Activated(self):
        doc = self.obj.Document
        prop = self.getProperty(self.obj) #string name of property
        if not prop:
            return
        outExpr = self.getOutExpr(self.obj, prop)
        if not outExpr:
            propval = getattr(self.obj, prop)
        newName = self.getNewPropertyName(self.obj, prop)
        if not newName:
            return

        inExprs = self.getInExprs(self.obj, prop)
        typeId = self.obj.getTypeIdOfProperty(prop)
        docu = self.obj.getDocumentationOfProperty(prop)
        group = self.obj.getGroupOfProperty(prop)
        doc.openTransaction(f"Rename {prop}")
        self.obj.addProperty(typeId, newName, group, docu)
        if outExpr:
            self.obj.setExpression(newName, outExpr)
        else:
            setattr(self.obj, newName, propval)
        for inExpr in inExprs:
            inExpr[0].setExpression(inExpr[1], inExpr[2].replace(prop,newName))
        self.obj.removeProperty(prop)
        doc.commitTransaction()
        if self.obj in FreeCADGui.Selection.getSelection():
            FreeCADGui.Selection.removeSelection(self.obj)
            FreeCADGui.Selection.addSelection(self.obj)
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1 and self.getDynamicProperties(selection[0]):
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                return True
        return False

#Gui.addCommand("DynamicData2RenameProperty", DynamicData2RenamePropertyCommandClass())
########################################################################################

# Retype a custom dynamic property

class DynamicData2RetyePropertyCommandClass(DynamicData2BaseCommandClass):
    """Retype Property Command"""
    def __init__(self):
        self.obj = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join(iconPath , 'RetypeProperty.svg'),
                'MenuText': "修改属性类型(&Y)",
                'Accel'   : "Ctrl+Shift+D,Y",
                'ToolTip' : "Retype a dynamic property"}

    def getProperty(self,obj):
        props = self.getDynamicProperties(obj)
        if props:
            items = props
            if len(items) == 1:
                return items[0]
            item, ok = QtGui.QInputDialog.getItem(FreeCADGui.getMainWindow(), "Retype", "Select property to retype:", items, editable=False)
            if not ok:
                return []
            return item
        else:
            FreeCAD.Console.PrintError(f"{obj.Label} has no dynamic properties to retype\n")
            return None

    def getNewPropertyType(self, obj, prop):
        """get from user new type for this property"""

        curType = self.obj.getTypeIdOfProperty(prop)
        newType, ok = QtGui.QInputDialog.getItem(FreeCADGui.getMainWindow(), "Retype",
        f""" <span>
Current type is {curType[13:]}.<br/><br/>
<span style='color: red;'>
THIS CANNOT BE UNDONE!  CANCEL AND SAVE YOUR FILE <br/>
JUST IN CASE IT DOES NOT WORK!<br/>
</span><br/>

Select new type for {prop}:<br/> </span>

""", self.PropertyTypes, editable=False)

        return f"App::Property{newType}" if ok else ""

    def Activated(self):
        doc = self.obj.Document
        prop = self.getProperty(self.obj) #string name of property
        if not prop:
            return
        newType = self.getNewPropertyType(self.obj, prop)
        if not newType:
            return

        docu = self.obj.getDocumentationOfProperty(prop)
        group = self.obj.getGroupOfProperty(prop)
        val = getattr(self.obj, prop)

        self.obj.removeProperty(prop)
        self.obj.addProperty(newType, prop, group, docu)
        try:
            setattr(self.obj, prop, val)
        except Exception:
            FreeCAD.Console.PrintError(f"""
DynamicData2: Unable to reset property value {val} for new property of type {newType}
for property {prop} of {self.obj.Label}, using default value for properties of
this type. You will need to set the value manually.\n""")

        if self.obj in FreeCADGui.Selection.getSelection():
            FreeCADGui.Selection.removeSelection(self.obj)
            FreeCADGui.Selection.addSelection(self.obj)
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1 and self.getDynamicProperties(selection[0]):
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                return True
        return False

#Gui.addCommand("DynamicData2RetypeProperty", DynamicData2RetypePropertyCommandClass())
########################################################################################
# Set the tooltip of a dynamic property

class DynamicData2SetTooltipCommandClass(DynamicData2BaseCommandClass):
    """Set Tooltip Command"""
    def __init__(self):
        self.obj = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join(iconPath , 'SetTooltip.svg'),
                'MenuText': "设置提示(&T)",
                'Accel'   : "Ctrl+Shift+D,T",
                'ToolTip' : "设置该属性在属性栏中显示的解释性提示文字"}

    def getProperty(self,obj):
        props = self.getDynamicProperties(obj)
        if props:
            items = props
            if len(items) == 1:
                return items[0]
            item, ok = QtGui.QInputDialog.getItem(FreeCADGui.getMainWindow(), "Set tooltip", "Select property to set tooltip for:", items, editable=False)
            if not ok:
                return []
            return item
        else:
            FreeCAD.Console.PrintError(f"{obj.Label} has no dynamic properties whose tooltips may be set\n")

    def getNewTooltip(self, obj, prop):
        """get from user new tooltip for this property"""
        curTip = obj.getDocumentationOfProperty(prop)
        newTip, ok = QtGui.QInputDialog.getText(FreeCADGui.getMainWindow(), "Set tooltip", f"Enter new tooltip for {prop}:", QtGui.QLineEdit.EchoMode.Normal, curTip)
        if not ok:
            return curTip
        else:
            return newTip

    def Activated(self):
        doc = self.obj.Document
        prop = self.getProperty(self.obj) #string name of property
        if not prop:
            return
        docu = self.obj.getDocumentationOfProperty(prop)
        newTip = self.getNewTooltip(self.obj, prop)
        if newTip == docu:
            return
        doc.openTransaction(f"Set tooltip of {prop}")
        self.obj.setDocumentationOfProperty(prop, newTip)
        doc.commitTransaction()
        #refresh property view
        if self.obj in FreeCADGui.Selection.getSelection():
            FreeCADGui.Selection.removeSelection(self.obj)
            FreeCADGui.Selection.addSelection(self.obj)
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1 and self.getDynamicProperties(selection[0]):
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                return True
        return False

#Gui.addCommand("DynamicData2SetTooltip", DynamicData2SetTooltipCommandClass())


########################################################################################
# Remove custom dynamic property


class DynamicData2RemovePropertyCommandClass(DynamicData2BaseCommandClass):
    """Remove Property Command"""

    def __init__(self):
        self.obj = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'RemoveProperty.svg'),
                'MenuText': "移除属性(&R)",
                'Accel'   : "Ctrl+Shift+D,R",
                'ToolTip' : "从对象中永久移除自定义的动态属性"}

    def getProperties(self,obj):
        """get all dynamic properties, and let user select the ones to remove in a dialog"""
        props = [p for p in obj.PropertiesList if self.isDynamic(obj, p)]
        return self.getSelectedObjects(props, "Select dynamic properties to remove", checkAll=False)

    def Activated(self):
        doc = self.obj.Document
        selection = Gui.Selection.getSelection()
        #remove the property
        window = QtGui.QApplication.activeWindow()
        items = self.getProperties(self.obj)
        if len(items) == 0: #user canceled
            return
        doc.openTransaction("Remove properties")
        for item in items:
            try:
                self.obj.removeProperty(item)
            except Exception as ex:
                FreeCAD.Console.PrintError(f"DynamicData2::Exception cannot remove {item}\n{ex}")
        doc.commitTransaction()
        if self.obj in selection: #refreshes property view
            FreeCADGui.Selection.removeSelection(self.obj)
            FreeCADGui.Selection.addSelection(self.obj)
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelection()
        if len(selection) == 1 and self.getDynamicProperties(selection[0]):
            self.obj = selection[0]
            return True
        #where nothing is selected and there is only one dd object, use that object
        if len(selection) == 0:
            dds = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj,"DynamicData2")]
            if len(dds) == 1:
                self.obj = dds[0]
                return True
        return False

#Gui.addCommand("DynamicData2RemoveProperty", DynamicData2RemovePropertyCommandClass())

########################################################################################
# Import aliases from spreadsheet


class DynamicData2ImportAliasesCommandClass(DynamicData2BaseCommandClass):
    """Import Aliases Command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'ImportAliases.svg'),
                'MenuText': "导入表格别名(&I)",
                'ToolTip' : "从选中的电子表格中导入别名作为动态属性"}

    def getExpression(self, sheet, alias, aliases):
        """Get the expression if there is one, modify it, and return it, else None if there is no expression."""

        cell = sheet.getCellFromAlias(alias)  # e.g. "B2"
        contents = sheet.getContents(cell)
        #if an expression contents will be for example: "=B2 + 3 * Box.Height"
        #this must be modified to be: "href(<<Spreadsheet.Label>>.B2) + 3 * Box.Height"
        #aliases must also be wrapped in href() and prepended with the sheet label)

        if not contents.startswith("="):
            return None #not an expression

        #remove the '='
        expression = contents[1:].strip()

        #match valid cell references like "B2", "ZY179"
        #note that spreadsheet validation disallows these to be aliases, but we
        #treat them the same anyway, so we don't care either way'
        cellRefPattern = re.compile(r'\b[A-Z]+[0-9]+\b')

        #split the expression into tokens (delimited by spaces)
        tokens = expression.split()

        moddedTokens = []
        for token in tokens:
            if token in aliases:
                moddedTokens.append(f'href(<<{sheet.Label}>>.{token})')
            #check if valid cell reference
            elif cellRefPattern.match(token):
                moddedTokens.append(f'href(<<{sheet.Label}>>.{token})')
            else:
                #all else unchanged
                moddedTokens.append(token)

        newExpression = ' '.join(moddedTokens)
        return newExpression

    def Activated(self):

        doc = self.dd.Document
        selection = Gui.Selection.getSelectionEx()
        if not selection:
            return

        #sanity check
        window = QtGui.QApplication.activeWindow()
        items = ["Do the import, I know what I\'m doing","Cancel"]
        item, ok = QtGui.QInputDialog.getItem(window,'DynamicData2: Sanity Check',
"""Warning: This will modify your spreadsheet.  Undo with Ctrl+Z Undo if it doesn't look right.

It will import the aliases from the spreadsheet and reset them to
point to the dd object.  After the import is done you should make any changes
to the dd property rather than to the alias cell in the spreadsheet.

Expressions are now imported as expressions wrapped inside href() to prevent
circular reference errors.

You should still keep your spreadsheet because other expressions referencing aliases in the
spreadsheet will still be referencing them.  The difference is now the spreadsheet cells
will be referencing the dd object.  Again, make any changes to the dd property, not to the spreadsheet.

For example:
Dependency graph:
before import: constraint -> spreadsheet
after import: constraint -> spreadsheet -> dd object

You can undo this operation using FreeCAD's Undo function, but you should probably
save your document before proceeding.""",
items, 0, False, windowFlags)
        if not ok or item == items[-1]:
            return
        doc.openTransaction("dd Import Aliases") #setup undo
        aliases=[]
        for sheet in self.sheets:
            for line in sheet.cells.Content.splitlines():
                if "<Cells Count=" in line or "</Cells>" in line:
                    continue
                if not "alias=" in line:
                    continue
                idx = line.find("alias=\"")+len("alias=\"")
                idx2 = line.find("\"",idx)
                if not line[idx:idx2][-1]=="_": #skip aliases that end in an underscore
                    aliases.append(line[idx:idx2])
                else:
                    FreeCAD.Console.PrintWarning('DynamicData2: skipping alias \"'+line[idx:idx2]+'\" because it ends in an underscore (_).\n')

            for alias in aliases:
                atr = getattr(sheet,alias)
                if "Base.Quantity" in str(type(atr)):
                    #handle quantity types
                    propertyType = atr.Unit.Type #e.g. 'Length'
                    #handle inconsistencies in naming convention between unit types and property types
                    if 'Velocity' in propertyType:
                        propertyType='Speed'
                    userString = atr.UserString
                elif "'float\'" in str(type(atr)):
                    #handle float types
                    propertyType='Float'
                    userString=atr
                elif "'int\'" in str(type(atr)):
                    #handle int types (actually, just treat them as floats
                    #since many users no doubt will expect this behavior for imported aliases)
                    propertyType='Float'
                    userString=atr
                elif "unicode" in str(type(atr)) or '<class \'str\'>' in str(type(atr)):
                    #handle unicode string types
                    propertyType='String'
                    userString=atr
                else:
                    FreeCAD.Console.PrintError('DynamicData2: please report: unknown property type error importing alias from spreadsheet ('+str(type(atr))+')\n')
                    continue

                name = self.fixName(self.dd, alias)
                if not hasattr(self.dd, name): #avoid adding the same property again
                    self.dd.addProperty('App::Property'+propertyType, name, sheet.Label, propertyType)
                    setattr(self.dd,name,userString)
                    FreeCAD.Console.PrintMessage(f"DynamicData2: adding property: {name} to {self.dd.Label}, resetting spreadsheet: \
                        {sheet.Label}.{alias} to point to {self.dd.Label}.{name}\n")
                    expr = self.getExpression(sheet, alias, aliases)
                    sheet.set(alias, f"={self.dd.Label}.{name}")

                    if expr: #will be None if not an expression
                        self.dd.setExpression(name, expr)
                else:
                    FreeCAD.Console.PrintWarning(f"DynamicData2: skipping existing property: {name}\n")
                continue

        doc.commitTransaction()
        doc.recompute()
        if len(aliases) == 0:
            FreeCAD.Console.PrintMessage('DynamicData2: No aliases found.\n')
            return
        return

    def IsActive(self):
        self.sheets = []
        self.dd = None
        selection = Gui.Selection.getSelection()
        if not selection:
            return
        self.sheets = [obj for obj in selection if obj.isDerivedFrom("Spreadsheet::Sheet")]
        dds = [obj for obj in selection if not obj in self.sheets]
        if len(dds) == 1:
            self.dd = dds[0]
        else:
            return False
        if len(self.sheets) == 0:
            return False

        return True

#Gui.addCommand("DynamicData2ImportAliases", DynamicData2ImportAliasesCommandClass())



########################################################################################
# Import named constraints from sketch


class DynamicData2ImportNamedConstraintsCommandClass(DynamicData2BaseCommandClass):
    """Import Named Constraints Command"""

    def __init__(self):
        self.dd = None
        self.sketches = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'ImportNamedConstraints.svg'),
                'MenuText': "导入命名约束(&M)",
                'ToolTip' : "从选中的草图中导入命名约束作为动态属性"}

    def getExpression(self, sketch, constraintName):
        """Check if sketch.Constraints.constraintName has an expression, if not return None"""
        #pattern to find ".Constraints" at the start or preceded by a space
        constraints_pattern = rf'(^|\s)(\.Constraints\.\S+)'

        for name, value in sketch.ExpressionEngine:
            if name.endswith(constraintName):
                #replace ".Constraints" at the start or after a space with "<<sketch.Label>>.Constraints"
                expr = re.sub(constraints_pattern, rf'\1<<{sketch.Label}>>\2', value)
                #print(f"expr = {expr} before lambda")
                #pattern to find any sketch's ".Constraints.xxx" and wrap it in href()
                #assumes Constraints.xxx is followed by a space or is at the end of the string
                expr = re.sub(r'\b(\S+\.Constraints\.\S+)\b', lambda m: f"href({m.group(0)})", expr)
                #print(f"expr = {expr} after lambda")
                #above sometimes gives <<href(sketchLabel>>.Constraints...)
                expr = expr.replace("<<href(", "href(<<")
                #print(f"massaged expr = {expr}")
                return expr
        return None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        # should never get here, so no need for this code -- command won't be active in these cases
        # if len(sketches)==0:
        #     #todo: handle no selected sketches.  For now, just return
        #     FreeCAD.Console.PrintMessage("DynamicData2: No selected sketch(es)\n")
        #     return
        # if not self.dd:
        #     #todo: handle no dd object selected.  For now, just return
        #     FreeCAD.Console.PrintMessage("DynamicData2: No selected dd object\n")
        #     return

        #sanity check
        window = QtGui.QApplication.activeWindow()
        items = ["Do the import, I know what I'm doing","Cancel"]
        item, ok = QtGui.QInputDialog.getItem(window,'DynamicData2: Sanity Check',
"""Warning: This will modify your sketch.

It will import the named constraints from the sketch and reset them to
point to the dd object.  After the import is done you should make changes
to the dd object property rather than to the constraint itself.

If the constraint contains an expression, the expression will be copied over to
the new dd property, otherwise the import will be by value.  These references
must be placed inside href() wrappers to prevent circular references, but this
can sometimes lead to the dd object still being touched after a recompute, so
you might get those error messages.  These can be ignored except they are telling
you to manually recompute the dd object so it finishes getting updated.

Constraint names ending in underscore (_) will be ignored.
Sketch labels ending in underscore (_) are also ignored.

This operation can be undone.  It is advised to save your document before doing the import.""",
items, 0 , False, windowFlags)
        if not ok or item == items[-1]:
            return
        FreeCAD.ActiveDocument.openTransaction("dd Import Constraints") #setup undo
        constraints=[]
        for sketch in self.sketches:
            for con in sketch.Constraints:
                if not con.Name or con.Name[-1:]=='_': #ignore constraint names ending in underscore
                    continue
                if not con.Driving:
                    FreeCAD.Console.PrintWarning(f"\
DynamicData2: Skipping reference mode constraint: {con.Name} because linking by expression would cause a cyclic \
dependency and linking by value would produce an incorrect value should the reference value change.\n")
                    continue
                expr = self.getExpression(sketch, con.Name)
                # print(f"expr = {expr}, sketch.Label = {sketch.Label}, con.Name = {con.Name}")
                constraints.append({'expression':expr, 'constraintName':con.Name,'value':con.Value,\
                            'constraintType':con.Type,'sketchLabel':sketch.Label, 'sketch':sketch, \
                            'driving': con.Driving})

        if len(constraints) == 0:
            FreeCAD.Console.PrintMessage('DynamicData2: No named constraints found.\n')
            return

        for con in constraints:
            propertyType = "Length"
            value = con['value']
            if con['constraintType'] == 'Angle':
                propertyType = "Angle"
                value *= (180.0 / math.pi)

            name = self.fixName(self.dd, con['constraintName'])
            importedName = con['sketchLabel'] + name[0].upper() + name[1:]

            if not self.isValidName(self.dd, con['constraintName']):
                for idx,constraint in enumerate(sketch.Constraints):
                    if constraint.Name == con['constraintName']:
                        sketch.renameConstraint(idx, name)
                        FreeCAD.Console.PrintWarning(f"DynamicData2: Renaming invalid constraint name: {con['constraintName']} to {name}\n")
                        break
            if not hasattr(self.dd,importedName): #avoid adding the same property again
                self.dd.addProperty(f"App::Property{propertyType}", importedName, con['sketchLabel'],f"[{propertyType}] constraint type: [{con['constraintType']}]")
                setattr(self.dd, importedName, value)
                self.dd.setExpression(importedName, con['expression'])
                FreeCAD.Console.PrintMessage(f"DynamicData2: adding property: {importedName} to dd object\n")
                sketch = con['sketch']
                sketch.setExpression(f"Constraints.{name}", f"<<{self.dd.Label}>>.{importedName}")
            else:
                FreeCAD.Console.PrintWarning(f"DynamicData2: skipping existing property: {name}\n")
        FreeCAD.ActiveDocument.commitTransaction()
        doc.recompute()
        return

    def IsActive(self):
        self.dd = None
        self.sketches = []
        doc = FreeCAD.ActiveDocument
        selection = Gui.Selection.getSelection()
        if not selection:
            return False
        self.sketches = [obj for obj in selection if obj.isDerivedFrom("Sketcher::SketchObject") and obj.Label[-1] != '_']
        if len(self.sketches) == 0:
            return False
        dds = [obj for obj in selection if not obj in self.sketches]
        if not len(dds) == 1:
            return False
        self.dd = dds[0]
        return True

#Gui.addCommand("DynamicData2ImportNamedConstraints", DynamicData2ImportNamedConstraintsCommandClass())


########################################################################################
# Copy Property To and/or From dd <--> other object


class DynamicData2CopyPropertyCommandClass(DynamicData2BaseCommandClass):
    """Copy Property Command"""
    class CopyDlg(QtGui.QDialog):

        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2")

        def __init__(self, cmd, obj1, obj2):
            super(DynamicData2CopyPropertyCommandClass.CopyDlg, self).__init__(Gui.getMainWindow())
            self.setAttribute(QtCore.Qt.WA_WindowPropagation, True)
            self.setWindowTitle(f"DynamicData2 v{__version__} Copy / Set / Bind")
            icon = QtGui.QIcon(os.path.join(iconPath, 'CopyProperty.svg'))
            self.setWindowIcon(icon)
            self.applied = False #apply button clicked
            self.obj1 = obj1
            self.obj2 = obj2 if obj2 else obj1
            self.cmd = cmd
            self.blockSignals(True)
            self.layout = QtGui.QGridLayout()
            for ii in range(1,10):
                self.layout.setRowStretch(ii, 1)
            self.layout.setRowStretch(0, 0)
            self.setLayout(self.layout)
            label = self.obj1.Label
            name = self.obj1.Name
            same = bool(label == name)
            label = label if same else f"{label} ({name})"
            self.obj1Label = QtGui.QLabel(label)
            self.layout.addWidget(self.obj1Label, 0, 0, 1, 2)

            label = self.obj2.Label if self.obj2 else self.obj1.Label
            name = self.obj2.Name if self.obj2 else self.obj1.Name
            same = bool(label == name)
            label = label if same else f"{label} ({name})"
            self.obj2Label = QtGui.QLabel(label)
            self.layout.addWidget(self.obj2Label, 0, 3, 1, 2)

            self.obj1List = QtGui.QListWidget()
            self.obj1List.itemSelectionChanged.connect(self.updateStatus)
            self.layout.addWidget(self.obj1List, 1, 0, 9, 2)
            self.obj2List = QtGui.QListWidget()
            self.obj2List.itemSelectionChanged.connect(self.updateStatus)
            self.layout.addWidget(self.obj2List, 1, 3, 9, 2)
            self.fillUpList(self.obj1, self.obj1List, 1)
            self.fillUpList(self.obj2, self.obj2List, 2)

            self.btnGroup = QtGui.QButtonGroup()
            self.btnGroup.buttonClicked.connect(self.radioBtnClicked)
            self.copyRightBtn = QtGui.QRadioButton("Copy ->")
            self.copyRightBtn.setChecked(True)
            self.btnGroup.addButton(self.copyRightBtn)
            self.copyRightBtn.setToolTip(f"""
Arrow points in direction of data flow.
Creates copy of selected property in {self.obj1.Label} -> to new property of same type in {self.obj2.Label}""")
            self.copyRightBtn.setObjectName("copyRightBtn")
            self.layout.addWidget(self.copyRightBtn, 1, 2, 1, 1)
            self.copyLeftBtn = QtGui.QRadioButton("<- Copy")
            self.btnGroup.addButton(self.copyLeftBtn)
            self.copyLeftBtn.setToolTip(f"""
Arrow points in direction of data flow.
Creates new property in {self.obj1.Label} <- from selected property of {self.obj2.Label}""")
            self.copyLeftBtn.setObjectName("copyLeftBtn")
            self.layout.addWidget(self.copyLeftBtn, 2, 2, 1, 1)

            self.setRightBtn = QtGui.QRadioButton("Set ->")
            self.btnGroup.addButton(self.setRightBtn)
            self.setRightBtn.setToolTip(f"""
Arrow points in direction of data flow.
Sets selected existing property in {self.obj2.Label} to value of selected property in {self.obj1.Label}""")
            self.setRightBtn.setObjectName("setRightBtn")
            self.layout.addWidget(self.setRightBtn, 3, 2, 1, 1)
            self.setLeftBtn = QtGui.QRadioButton("<- Set")
            self.btnGroup.addButton(self.setLeftBtn)
            self.setLeftBtn.setToolTip(f"Sets selected existing property in {self.obj1.Label} to value of selected property in {self.obj2.Label}")
            self.setLeftBtn.setObjectName("setLeftBtn")
            self.layout.addWidget(self.setLeftBtn, 4, 2, 1, 1)

            self.bindRightBtn = QtGui.QRadioButton("Bind to ->")
            self.btnGroup.addButton(self.bindRightBtn)
            self.bindRightBtn.setToolTip(f"""
Arrow points in direction of binding, left is bound to right.
Bind selected property of {self.obj1.Label} to selected property of {self.obj2.Label} via Expressions""")
            self.bindRightBtn.setObjectName("bindRightBtn")
            self.layout.addWidget(self.bindRightBtn, 5, 2, 1, 1)
            self.bindLeftBtn = QtGui.QRadioButton("<- Bind to")
            self.btnGroup.addButton(self.bindLeftBtn)
            self.bindLeftBtn.setToolTip(f"""
Arrow points in direction of binding, right is bound to left.
Bind selected property of {self.obj2.Label} to selected property of {self.obj1.Label} via Expressions""")
            self.bindLeftBtn.setObjectName("bindLeftBtn")
            self.layout.addWidget(self.bindLeftBtn, 6, 2, 1, 1)

            self.breakBindRightBtn = QtGui.QRadioButton("Break binding ->")
            self.btnGroup.addButton(self.breakBindRightBtn)
            self.breakBindRightBtn.setToolTip(f"""
Arrow points to object being affected.
Break expression binding for selected property of {self.obj2.Label}""")
            self.breakBindRightBtn.setObjectName("breakBindRightBtn")
            self.layout.addWidget(self.breakBindRightBtn, 7, 2, 1, 1)
            self.breakBindLeftBtn = QtGui.QRadioButton("<- Break binding")
            self.btnGroup.addButton(self.breakBindLeftBtn)
            self.breakBindLeftBtn.setToolTip(f"""
Arrow points to object being affected.
Break expression binding for selected property of {self.obj1.Label}""")
            self.breakBindLeftBtn.setObjectName("breakBindLeftBtn")
            self.layout.addWidget(self.breakBindLeftBtn, 8, 2, 1, 1)

            self.statusLabel = QtGui.QLabel()
            self.statusLabel.setToolTip("Messages go here: blue text = normal message, red text = critical error in proposed action.")
            self.layout.addWidget(self.statusLabel, 11, 0, 2, 5)

            self.buttons = QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok.__or__(QtGui.QDialogButtonBox.Cancel),
                QtCore.Qt.Horizontal, self)
            self.okBtn = self.buttons.button(QtGui.QDialogButtonBox.Ok)
            self.okBtn.setText(self.copyRightBtn.text())
            self.okBtn.setToolTip("Apply action and close dialog")
            self.applyBtn = QtGui.QPushButton("Apply")
            self.buttons.addButton(self.applyBtn, QtGui.QDialogButtonBox.ApplyRole)
            # --- Container for checkbox + button box ---
            hbox = QtGui.QHBoxLayout()

            # Checkbox on the left
            self.byExpressionCheckBox = QtGui.QCheckBox("Copy expressions")
            self.byExpressionCheckBox.setToolTip(
                "If checked, properties that have expressions are set as expressions on the other side."
            )
            self.byExpressionCheckBox.stateChanged.connect(self.checkBoxClicked)
            self.byExpressionCheckBox.setChecked(self.pg.GetBool("UseExpression", False))
            self.byExpressionCheckBox.setObjectName("byExpressionCheckBox")
            self.byExpressionCheckBox.setEnabled(False)  # initially disabled

            hbox.addWidget(self.byExpressionCheckBox)

            # Spacer in between
            hbox.addStretch(1)

            # Button box (Ok / Cancel / Apply) on the right
            hbox.addWidget(self.buttons)

            # Put the whole row into the grid
            self.layout.addLayout(hbox, 14, 0, 1, 5)

            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            self.applyBtn.clicked.connect(self.apply)
            self.blockSignals(False)
            self.updateStatus()

        @property
        def Obj1Item(self):
            """currently selected item, might be None"""
            return self.obj1List.currentItem()

        @property
        def Obj2Item(self):
            """currently selected item, might be None"""
            return self.obj2List.currentItem()

        @property
        def Obj1IsView(self):
            """boolean, true if obj1 selected property is a view property"""
            item = self.Obj1Item
            if not item:
                return False
            txt = item.text()
            return txt.startswith("(view) ")

        @property
        def Obj2IsView(self):
            """boolean, true if obj2 selected property is a view property"""
            item = self.Obj2Item
            if not item:
                return False
            txt = item.text()
            return txt.startswith("(view) ")

        @property
        def Obj1PropName(self):
            """property name selected in left list"""
            item = self.Obj1Item
            if not item:
                return None
            txt = item.text()
            if txt.startswith("(view) "):
                return txt[7:]
            else:
                return txt

        @property
        def Obj2PropName(self):
            """property name selected in right list"""
            item = self.Obj2Item
            if not item:
                return None
            txt = item.text()
            if txt.startswith("(view) "):
                return txt[7:]
            else:
                return txt

        @property
        def Obj1Group(self):
            """group of the currently selected property"""
            item = self.Obj1Item
            if not item:
                return None
            if self.Obj1IsView:
                obj = self.obj1.ViewObject
            else:
                obj = self.obj1
            grp = obj.getGroupOfProperty(self.Obj1PropName)
            return grp if grp else "Base"

        @property
        def Obj2Group(self):
            """group of the currently selected property"""
            item = self.Obj2Item
            if not item:
                return None
            if self.Obj2IsView:
                obj = self.obj2.ViewObject
            else:
                obj = self.obj2
            grp = obj.getGroupOfProperty(self.Obj2PropName)
            return grp if grp else "Base"

        @property
        def Obj1Value(self):
            """value of selected property"""
            item = self.Obj1Item
            if not item:
                return None
            if not self.Obj1IsView:
                return getattr(self.obj1, self.Obj1PropName)
            else:
                try:
                    return getattr(self.obj1.ViewObject, self.Obj1PropName)
                except AttributeError:
                    return "No python counterpart"

        @property
        def Obj2Value(self):
            """value of selected property"""
            item = self.Obj2Item
            if not item:
                return None
            if not self.Obj2IsView:
                return getattr(self.obj2, self.Obj2PropName)
            else:
                try:
                    return getattr(self.obj2.ViewObject, self.Obj2PropName)
                except AttributeError:
                    return "No python counterpart"

        @property
        def Obj1Type(self):
            """type id of selected property, with 'App::Property' prefix"""
            item = self.Obj1Item
            if not item:
                return None
            if not self.Obj1IsView:
                return self.obj1.getTypeIdOfProperty(self.Obj1PropName)
            else:
                return self.obj1.ViewObject.getTypeIdOfProperty(self.Obj1PropName)

        @property
        def Obj2Type(self):
            """type id of selected property, with 'App::Property' prefix"""
            item = self.Obj2Item
            if not item:
                return None
            if not self.Obj2IsView:
                return self.obj2.getTypeIdOfProperty(self.Obj2PropName)
            else:
                return self.obj2.ViewObject.getTypeIdOfProperty(self.Obj2PropName)

        @property
        def Obj1Expression(self):
            """expression engine value for this property, if any"""
            item = self.Obj1Item
            if not item:
                return None
            if self.Obj1IsView:
                return None
            expr = self.obj1.ExpressionEngine
            exp_dict = {xp[0]:xp[1] for xp in expr}
            if self.Obj1PropName in exp_dict:
                return exp_dict[self.Obj1PropName]
            else:
                return None

        @property
        def Obj2Expression(self):
            """expression engine value for this property, if any"""
            item = self.Obj2Item
            if not item:
                return None
            if self.Obj2IsView:
                return None
            expr = self.obj2.ExpressionEngine
            exp_dict = {xp[0]:xp[1] for xp in expr}
            if self.Obj2PropName in exp_dict:
                return exp_dict[self.Obj2PropName]
            else:
                return None

        @property
        def Obj1Tip(self):
            """documentation of property, tooltip shown"""
            item = self.Obj1Item
            if not item:
                return None
            if not self.Obj1IsView:
                return self.obj1.getDocumentationOfProperty(self.Obj1PropName)
            else:
                return self.obj1.ViewObject.getDocumentationOfProperty(self.Obj1PropName)

        @property
        def Obj2Tip(self):
            """documentation of property, tooltip shown"""
            item = self.Obj2Item
            if not item:
                return None
            if not self.Obj2IsView:
                return self.obj2.getDocumentationOfProperty(self.Obj2PropName)
            else:
                return self.obj2.ViewObject.getDocumentationOfProperty(self.Obj2PropName)

        def radioBtnClicked(self, btn):
            self.updateOkButtonText()
            self.updateStatus()

        def checkBoxClicked(self, state):
            """called when checkbox is clicked, updates ok button text"""
            self.updateOkButtonText()
            self.updateStatus()

        def updateOkButtonText(self):
            btn = self.btnGroup.checkedButton()
            text = btn.text()
            if self.hasExpr() and self.byExpressionCheckBox.isChecked():
                text += " (Expr)"
            self.okBtn.setText(text)

        def updateStatus(self):
            """updates the status label to give a preview of the action to be performed"""
            if not hasattr(self, "btnGroup"):
                return #not fully initialized yet
            vobj1 = "" if not self.Obj1IsView else ".ViewObject"
            vobj2 = "" if not self.Obj2IsView else ".ViewObject"

            cyclicMatch1 = bool(self.obj2 in self.obj1.InListRecursive) #if true, obj2 depends on obj1, so obj1 cannot bind to obj2
            cyclicMatch2 = bool(self.obj1 in self.obj2.InListRecursive)
            cyclicMsg1 = f"\nCircular dependency because {self.obj2.Label} already depends on {self.obj1.Label}." if cyclicMatch1 else ""
            cyclicMsg2 = f"\nCircular dependency because {self.obj1.Label} already depends on {self.obj2.Label}." if cyclicMatch2 else ""

            typeMismatch = bool(self.Obj1Type != self.Obj2Type)
            typeMsg = f"\nType mismatch detected: {self.Obj1Type} and {self.Obj2Type}" if typeMismatch else ""
            typeClr = ["blue","red"][int(typeMismatch)]
            typeClr1 = ["blue","red"][int(typeMismatch or cyclicMatch1)]
            typeClr2 = ["blue","red"][int(typeMismatch or cyclicMatch2)]

            cyclicMatch1 = bool(self.obj2 in self.obj1.InListRecursive) #if true, obj2 depends on obj1, so obj1 cannot bind to obj2
            cyclicMatch2 = bool(self.obj1 in self.obj2.InListRecursive)
            cyclicMsg1 = f"\nCircular dependency because {self.obj2.Label} already depends on {self.obj1.Label}." if cyclicMatch1 else ""
            cyclicMsg2 = f"\nCircular dependency because {self.obj1.Label} already depends on {self.obj2.Label}." if cyclicMatch2 else ""
            cyclicClr1 = ["blue","red"][int(cyclicMatch1 or typeMismatch)]
            cyclicClr2 = ["blue","red"][int(cyclicMatch2 or typeMismatch)]
            radioBtn = self.btnGroup.checkedButton()
            msg = ""
            value_or_expression = "value"
            if radioBtn.objectName() in ["setLeftBtn", "setRightBtn", "copyLeftBtn", "copyRightBtn"]:
                if self.hasExpr():
                    self.byExpressionCheckBox.setEnabled(True)
                    if self.byExpressionCheckBox.isChecked():
                        value_or_expression = "expression"
                else:
                    self.byExpressionCheckBox.setEnabled(False)
            elif radioBtn.objectName() in ["bindLeftBtn", "bindRightBtn", "breakBindLeftBtn", "breakBindRightBtn"]:
                self.byExpressionCheckBox.setEnabled(False)
            copyLeftMsg = (f"Copy {self.obj2.Label}{vobj2}.{self.Obj2PropName} {value_or_expression} to a new property in {self.obj1.Label}","blue")
            copyRightMsg = (f"Copy {self.obj1.Label}{vobj1}.{self.Obj1PropName} {value_or_expression} to a new property in {self.obj2.Label}","blue")
            setLeftMsg = (f"Set {self.obj1.Label}{vobj1}.{self.Obj1PropName} to {value_or_expression} of {self.obj2.Label}{vobj2}.{self.Obj2PropName}{typeMsg}",typeClr)
            setRightMsg = (f"Set {self.obj2.Label}{vobj2}.{self.Obj2PropName} to {value_or_expression} of {self.obj1.Label}{vobj1}.{self.Obj1PropName}{typeMsg}",typeClr)
            if not vobj2:
                bindLeftMsg = (f"Bind {self.obj2.Label}.{self.Obj2PropName} to {self.obj1.Label}.{self.Obj1PropName}{typeMsg}{cyclicMsg2}",typeClr2)
            else:
                bindLeftMsg = (f"Cannot bind {self.obj2.Label}{vobj2}.{self.Obj2PropName} because it is a view object property.{typeMsg}","red")
            if not vobj1:
                bindRightMsg = (f"Bind {self.obj1.Label}.{self.Obj1PropName} to {self.obj2.Label}.{self.Obj2PropName}{typeMsg}{cyclicMsg1}",typeClr1)
            else:
                bindRightMsg = (f"Cannot bind {self.obj1.Label}{vobj1}.{self.Obj1PropName} because it is a view object property.","red")
            if self.Obj1Expression:
                breakBindLeftMsg = (f"Break binding of {self.obj1.Label}.{self.Obj1PropName}.","blue")
            else:
                breakBindLeftMsg = (f"No expression binding to break for {self.obj1.Label}.{self.Obj1PropName}.","red")
            if self.Obj1IsView:
                breakBindLeftMsg = (breakBindLeftMsg[0] + "\nView objects cannot be bound or unbound via expressions", "red")
            if self.Obj2Expression:
                breakBindRightMsg = (f"Break binding of {self.obj2.Label}.{self.Obj2PropName}.","blue")
            else:
                breakBindRightMsg = (f"No expression binding to break for {self.obj2.Label}.{self.Obj2PropName}.","red")
            if self.Obj2IsView:
                breakBindRightMsg = (breakBindRightMsg[0] + "\nView objects cannot be bound or unbound via expressions", "red")

            msg_map = {
                "copyLeftBtn" : copyLeftMsg,
                "copyRightBtn" : copyRightMsg,
                "setLeftBtn" : setLeftMsg,
                "setRightBtn" : setRightMsg,
                "bindLeftBtn" : bindLeftMsg,
                "bindRightBtn" : bindRightMsg,
                "breakBindLeftBtn" : breakBindLeftMsg,
                "breakBindRightBtn" : breakBindRightMsg,
            }

            dq = "\"" #double quote
            self.updateOkButtonText()
            self.okBtn.setToolTip(f"Apply {dq}{radioBtn.text()}{dq} action and close dialog")
            self.applyBtn.setToolTip(f"Apply {dq}{radioBtn.text()}{dq} action and reopen dialog")
            msgTuple = msg_map[radioBtn.objectName()]
            self.statusLabel.setStyleSheet(f"color:{msgTuple[1]};")
            self.statusLabel.setText(f"{msgTuple[0]}{msg}")

        def hasExpr(self):
            btn = self.btnGroup.checkedButton()
            return btn and btn.objectName() in ["setLeftBtn", "copyLeftBtn"] and not self.Obj1IsView and self.Obj2Expression or \
                    btn.objectName() in ["setRightBtn", "copyRightBtn"] and not self.Obj2IsView and self.Obj1Expression

        def validateExpr(self, srcObj, dstObj, expr):
            replaceLocalRe = re.compile(f"(?<!\\w\\.)\\.?({'|'.join(srcObj.PropertiesList)})\\b")
            previous = expr
            failed = False
            try:
                label = " " in srcObj.Label and f"<<{srcObj.Label}>>" or srcObj.Label
                expr = replaceLocalRe.sub(f"{label}.\\1", expr)
                dstObj.evalExpression(expr) #will raise if invalid
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"DynamicData2: expression validation failed: {expr}\n{e}\n")
                failed = True
                expr = previous
            # qt dialog to edit expression if user wants
            if previous != expr or failed:
                new_expr, ok = QtGui.QInputDialog.getText(self, "Edit Ambiguous Local Expression",
                                                f"Edit expression with label added for {dstObj.Label}.{self.Obj1PropName if dstObj==self.obj1 else self.Obj2PropName}: ", text=expr)
                if not new_expr or not ok:
                    FreeCAD.Console.PrintError("DynamicData2: operation cancelled by user.\n")
                expr = new_expr
            # no need to validate again, let setExpression handle it if it's bad
            return expr

        def getNewPropertyName(self, obj, candidate):
            """When creating a new property and already there is a property with that
            same name, we can ask the user for a preferred new property name"""
            new_candidate = self.cmd.getNewPropertyNameCandidate(obj, candidate)
            new_name, ok = QtGui.QInputDialog.getText(self, "Attribute already exists",
                                                    "Enter name for new property: ", text=new_candidate)
            if not new_name or not ok:
                return None

            return new_name

        def copyLeft(self):
            """copy the selected property from the list on the right to the object (self.obj1) on the left
            returns None if user aborts, False if there was some error, True on success
            """
            propName = self.getNewPropertyName(self.obj1, self.Obj2PropName)
            if not propName:
               return None
            try:
                self.obj1.addProperty(self.Obj2Type, propName, self.Obj2Group, self.Obj2Tip)
            except Exception:
                FreeCAD.Console.PrintError(f"DynamicData2: Error adding {propName} to {self.obj1.Label}")
                return False
            if self.hasExpr() and self.byExpressionCheckBox.isChecked():
                try:
                    self.obj1.setExpression(propName, self.validateExpr(self.obj2, self.obj1, self.Obj2Expression))
                    return True
                except Exception as e:
                    FreeCAD.Console.PrintError(f"DynamicData2: error {e} setting {self.obj1.Label}.{propName} to {self.Obj2Expression}\n")
                    return False
            else:
                try:
                    setattr(self.obj1, propName, self.Obj2Value)
                    return True
                except Exception:
                    FreeCAD.Console.PrintError(f"DynamicData2: Error setting {propName} to {self.Obj2Value}, but property was created.\n")
                    return False

        def copyRight(self):
            """copy the selected property from the list on the left to the object (self.obj2) on the right
            returns None if user aborts, False if there was some error, True on success
            """
            propName = self.getNewPropertyName(self.obj2, self.Obj1PropName)
            if not propName:
               return None

            try:
                self.obj2.addProperty(self.Obj1Type, propName, self.Obj1Group, self.Obj1Tip)
            except Exception:
                FreeCAD.Console.PrintError(f"DynamicData2: Error adding {propName} to {self.obj2.Label}")
                return False
            if self.hasExpr() and self.byExpressionCheckBox.isChecked():
                try:
                    self.obj2.setExpression(propName, self.validateExpr(self.obj1, self.obj2, self.Obj1Expression))
                    return True
                except Exception as e:
                    FreeCAD.Console.PrintError(f"DynamicData2: error {e} setting {self.obj2.Label}.{propName} to {self.Obj1Expression}\n")
                    return False
            else:
                try:
                    setattr(self.obj2, propName, self.Obj1Value)
                    return True
                except Exception:
                    FreeCAD.Console.PrintError(f"DynamicData2: Error setting {propName} to {self.Obj1Value}, but property was created.\n")
                    return False

        def setLeft(self):
            """sets an existing property of self.obj1 to the same value of selected property in right side list"""
            #first check that the property types are a match
            if self.Obj1Type != self.Obj2Type:
                FreeCAD.Console.PrintError(f"""
DynamicData2: Type mismatch: {self.obj2.Label}.{self.Obj2PropName} is type {self.Obj2Type}
while {self.obj1.Label}.{self.Obj1PropName} is type {self.Obj1Type}""")
                return False
            #now check to see if the property is bound by an expression already
            if self.Obj1Expression:
                FreeCAD.Console.PrintWarning(f"""
DynamicData2 warning: {self.obj1.Label}.{self.Obj1PropName} was bound by an expression:\n{self.Obj1Expression}\nbut it has now been cleared.""")
                self.obj1.setExpression(self.Obj1PropName, None)
            if self.hasExpr() and self.byExpressionCheckBox.isChecked():
                try:
                    self.obj1.setExpression(self.Obj1PropName, self.validateExpr(self.obj2, self.obj1, self.Obj2Expression))
                    return True
                except Exception as e:
                    FreeCAD.Console.PrintError(f"DynamicData2: error {e} setting {self.obj1.Label}.{self.Obj1PropName} to {self.Obj2Expression}\n")
                    return False
            else:
                try:
                    if not self.Obj2IsView:
                        setattr(self.obj1, self.Obj1PropName, self.Obj2Value)
                    else:
                        setattr(self.obj1.ViewObject, self.Obj1PropName, self.Obj2Value)
                    return True
                except Exception as e:
                    FreeCAD.Console.PrintError(f"DynamicData2: error {e} setting {self.obj1.Label}.{self.Obj1PropName} to {self.Obj2Value}\n")
                    return False

        def setRight(self):
            """sets an existing property of self.obj2 to the same value of selected property in left side list"""
            #first check that the property types are a match
            if self.Obj1Type != self.Obj2Type:
                FreeCAD.Console.PrintError(f"""
DynamicData2: Type mismatch: {self.obj2.Label}.{self.Obj2PropName} is type {self.Obj2Type}
while {self.obj1.Label}.{self.Obj1PropName} is type {self.Obj1Type}""")
                return False
            #now check to see if the property is bound by an expression already
            if self.Obj2Expression:
                FreeCAD.Console.PrintWarning(f"""
DynamicData2 warning: {self.obj2.Label}.{self.Obj2PropName} was bound by an expression:\n{self.Obj2Expression}\nbut it has now been cleared.""")
                self.obj2.setExpression(self.Obj2PropName, None)
            if not self.Obj1IsView and self.hasExpr() and self.byExpressionCheckBox.isChecked():
                try:
                    self.obj2.setExpression(self.Obj2PropName, self.validateExpr(self.obj1, self.obj2, self.Obj1Expression))
                    return True
                except Exception as e:
                    FreeCAD.Console.PrintError(f"DynamicData2: error {e} setting {self.obj2.Label}.{self.Obj2PropName} to {self.Obj1Expression}\n")
                    return False
            else:
                try:
                    if not self.Obj1IsView:
                        setattr(self.obj2, self.Obj2PropName, self.Obj1Value)
                    else:
                        setattr(self.obj2.ViewObject, self.Obj2PropName, self.Obj1Value)
                    return True
                except Exception as e:
                    FreeCAD.Console.PrintError(f"DynamicData2: error {e} setting {self.obj2.Label}.{self.Obj2PropName} to {self.Obj1Value}\n")
                    return False

        def bindRight(self):
            """bind to the property on the right"""
            #check for a type mismatch
            if self.Obj1Type != self.Obj2Type:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: Type mismatch.  {self.obj1.Label}.{self.Obj1PropName} is type {self.Obj1Type} where
{self.obj2.Label}.{self.Obj2PropName} is type {self.Obj2Type}""")
                return False
            # check for cyclic dependency
            # objects in obj.InList and obj.InListRecursive are dependent on obj
            # since this command binds a property of obj1 to obj2 we must check
            # to see if obj2 is in obj1's inlist
            if self.obj2 in self.obj1.InListRecursive:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: Cannot bind  {self.obj1.Label}.{self.Obj1PropName} to {self.obj2.Label}.{self.Obj2PropName}
because this would create a cyclic dependency.""")
                return False
            if self.Obj1IsView:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: {self.obj1.Label}.ViewObject.{self.Obj1PropName} is a view object expression,
which cannot be bound by expression.\n""")
                return False
            FreeCAD.Console.PrintMessage(f"""
DynamicData2: binding {self.obj1.Label}.{self.Obj1PropName} to {self.obj2.Label}.{self.Obj2PropName}""")
            self.obj1.setExpression(self.Obj1PropName, f"{self.obj2.Name}.{self.Obj2PropName}")
            return True

        def bindLeft(self):
            """bind to the property selected on the left"""
            #check for a type mismatch
            if self.Obj2Type != self.Obj1Type:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: Type mismatch.  {self.obj2.Label}.{self.Obj2PropName} is type {self.Obj2Type} where
{self.obj1.Label}.{self.Obj1PropName} is type {self.Obj1Type}""")
                return False
            # check for cyclic dependency
            # objects in obj.InList and obj.InListRecursive are dependent on obj
            # since this command binds a property of obj2 to obj1 we must check
            # to see if obj1 is in obj2's inlist
            if self.obj1 in self.obj2.InListRecursive:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: Cannot bind  {self.obj2.Label}.{self.Obj2PropName} to {self.obj1.Label}.{self.Obj1PropName}
because this would create a cyclic dependency.""")
                return False
            if self.Obj2IsView:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: {self.obj2.Label}.ViewObject.{self.Obj2PropName} is a view object expression,
which cannot be bound by expression.\n""")
                return False
            FreeCAD.Console.PrintMessage(f"""
DynamicData2: binding {self.obj2.Label}.{self.Obj2PropName} to {self.obj1.Label}.{self.Obj1PropName}""")
            self.obj2.setExpression(self.Obj2PropName, f"{self.obj1.Name}.{self.Obj1PropName}")
            return True

        def breakBindLeft(self):
            """Clears the expression binding the property on the left that is bound to the property on the right"""
            # check if the property on the left is already bound or not
            # if it's not bound by an expression, then the user might have selected the wrong
            # radio button by mistake, so alert to the error and return
            if not self.Obj1Expression:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: {self.obj1.Label}.{self.Obj1PropName} is not bound by an expression.\n""")
                return False
            if self.Obj2IsView:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: {self.obj2.Label}.ViewObject.{self.Obj2PropName} is a view object expression,
which cannot be bound by expression.\n""")
                return False
            self.obj1.setExpression(self.Obj1PropName, None)
            return True

        def breakBindRight(self):
            """Clears the expression binding the property on the right that is bound to the property on the left"""
            # check if the property on the right is already bound or not
            # if it's not bound by an expression, then the user might have selected the wrong
            # radio button by mistake, so alert to the error and return
            if not self.Obj2Expression:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: {self.obj2.Label}.{self.Obj2PropName} is not bound by an expression.\n""")
                return False
            #check if this is a view object property, which cannot be bound by expression
            if self.Obj2IsView:
                FreeCAD.Console.PrintError(f"""
DynamicData2 error: {self.obj2.Label}.ViewObject.{self.Obj2PropName} is a view object expression,
which cannot be bound by expression.\n""")
                return False
            self.obj2.setExpression(self.Obj2PropName, None)
            return True


        def fillUpList(self, obj, objList, idx):
            pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2")
            supportViewObjectProperties = pg.GetBool('SupportViewObjectProperties', False)
            blacklist = ["ExpressionEngine","Proxy","Shape","DynamicData2"]
            props = self.cmd.getAllProperties(obj, supportViewObjectProperties, blacklist)
            for prop in props:
                item = QtGui.QListWidgetItem(prop)
                objList.addItem(item)
                objList.setCurrentItem(item)
                if idx == 1:
                    tip = f"[{self.Obj1Type}]\nGroup: {self.Obj1Group}\nTooltip: {self.Obj1Tip}\nvalue: {self.Obj1Value}\nExpr: {self.Obj1Expression}"
                elif idx == 2:
                    tip = f"[{self.Obj2Type}]\nGroup: {self.Obj2Group}\nTooltip: {self.Obj2Tip}\nvalue: {self.Obj2Value}\nExpr: {self.Obj2Expression}"
                item.setToolTip(tip)
            if props:
                objList.setCurrentRow(0)

        def accept(self):
            func_map = {
                "copyLeftBtn" : self.copyLeft,
                "copyRightBtn" : self.copyRight,
                "setLeftBtn" : self.setLeft,
                "setRightBtn" : self.setRight,
                "bindLeftBtn" : self.bindLeft,
                "bindRightBtn" : self.bindRight,
                "breakBindLeftBtn" : self.breakBindLeft,
                "breakBindRightBtn" : self.breakBindRight,
            }
            radioBtn = self.btnGroup.checkedButton()
            if radioBtn:
                func = func_map.get(radioBtn.objectName())
                self.obj1.Document.openTransaction(f"DynamicData2: {func.__name__}")
                retval = func()
                if retval == None: #user aborted
                    self.obj1.Document.abortTransaction()
                    return #doesn't close dialog
                elif retval == False: #error, but already reported in func(), so don't repeat it here
                    self.obj1.Document.abortTransaction()
                else:
                    self.obj1.Document.commitTransaction()
            self.pg.SetBool("UseExpression", self.byExpressionCheckBox.isChecked())
            super().accept()

        def reject(self):
            self.pg.SetBool("UseExpression", self.byExpressionCheckBox.isChecked())
            print("rejected")
            super().reject()

        def apply(self):
            self.applied = True
            self.accept()

        ### end of CopyDlg class definition

    def __init__(self):
        self.obj1 = None
        self.obj2 = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CopyProperty.svg'),
                'MenuText': "复制/绑定属性(&O)",
                'ToolTip' : "在不同对象之间复制数值或建立表达式绑定"}


    def Activated(self):
        dlg = self.doDlg()
        while dlg.applied:
            dlg.deleteLater()
            dlg = self.doDlg()
        dlg.deleteLater()
        self.obj1.Document.recompute()

    def doDlg(self):
        dlg = DynamicData2CopyPropertyCommandClass.CopyDlg(self, self.obj1, self.obj2)
        dlg.exec_()
        return dlg

    def IsActive(self):
        self.obj1 = None
        self.obj2 = None
        selection = Gui.Selection.getSelection()
        if not selection:
            return False
        if len(selection) == 1:
            self.obj1 = selection[0]
            return True
        if len(selection) == 2:
            self.obj1 = selection[0]
            self.obj2 = selection[1]
            return True
        return False

class DynamicData2Commands:
    def GetCommands(self):

        return tuple(["DynamicData2CreateObject", "DynamicData2AddProperty",
                    "DynamicData2EditEnumeration", "DynamicData2CreateConfiguration",
                    "DynamicData2RemoveProperty", "DynamicData2ImportNamedConstraints",
                    "DynamicData2ImportAliases","DynamicData2CopyProperty",
                    "DynamicData2RenameProperty","DynamicData2SetTooltip",
                    "DynamicData2RetypeProperty",
                    "DynamicData2MoveToNewGroup","DynamicData2Settings"]) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used
        return 0

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateObject.svg'), 'MenuText': 'DynamicData2 Commands', 'ToolTip': 'DynamicData2 commands'}

    def IsActive(self): # optional
        return True



# ============================================================================
#  Sliders — real-time slider panel + timeline + keyframes
#  Supports: DynamicData2 object properties, Sketch constraints
# ============================================================================

# --- Data sources --------------------------------------------------------
def _get_animatable_properties(obj):
    primary = {"Length", "Width", "Height"}
    props_primary = []
    props_xyz = []
    props_other = []
    for p in obj.PropertiesList:
        if p in ("Label", "Label2", "ExpressionEngine", "Visibility", "Group"):
            continue
        try:
            attr = getattr(obj, p)
        except Exception:
            continue
        if isinstance(attr, bool):
            continue
        if isinstance(attr, (int, float)):
            entry = (p, obj.getTypeIdOfProperty(p))
        elif isinstance(attr, App.Units.Quantity):
            entry = (p, obj.getTypeIdOfProperty(p))
        else:
            continue
        if p in primary:
            props_primary.append(entry)
        else:
            props_other.append(entry)
    if hasattr(obj, "Placement"):
        props_xyz.append(("Placement.Base.x", "PropertyFloat"))
        props_xyz.append(("Placement.Base.y", "PropertyFloat"))
        props_xyz.append(("Placement.Base.z", "PropertyFloat"))
        props_other.append(("Placement.Rotation.Angle", "PropertyAngle"))
    return props_primary + props_xyz + props_other


class _DD2Source:
    def __init__(self, dd, plist):
        self.obj = dd; self._items = plist
        self._type_map = {n: t for n, t in plist}
    @property
    def label(self): return self.obj.Label
    def items(self): return self._items
    def get(self, name):
        parts = name.split(".")
        v = self.obj
        for p in parts: v = getattr(v, p)
        if hasattr(v, 'Value'):
            v = v.Value
        if "Angle" in self._type_map.get(name, "") and name.startswith("Placement.Rotation"):
            import math
            v = math.degrees(v)
        return v
    def set(self, name, val):
        if "Angle" in self._type_map.get(name, "") and name.startswith("Placement.Rotation"):
            import math
            val = math.radians(val)
        parts = name.split(".")
        target = self.obj
        for p in parts[:-1]: target = getattr(target, p)
        setattr(target, parts[-1], val)
    def recompute(self): FreeCAD.ActiveDocument.recompute()
    def meta(self, name, ptype):
        if "Angle" in ptype: return ("\u00b0", 1)
        if "Integer" in ptype: return ("", 0)
        if "Length" in ptype or "Distance" in ptype: return (" mm", 2)
        if "Speed" in ptype: return (" mm/s", 2)
        if "Force" in ptype: return (" N", 2)
        if "Pressure" in ptype: return (" Pa", 2)
        if "Volume" in ptype: return (" mm\u00b3", 2)
        if "Area" in ptype: return (" mm\u00b2", 2)
        return ("", 2)

class _SketchSource:
    SKIP_TYPES = {"Block","Fixed","PointOnObject","Coincident","Parallel","Perpendicular",
        "Horizontal","Vertical","Tangent","Equal","Symmetric","SnellsLaw","InternalAlignment"}
    def __init__(self, sketch):
        self.obj = sketch
        self._items = []
        for i, c in enumerate(sketch.Constraints):
            if c.Type in self.SKIP_TYPES: continue
            if not hasattr(c, 'Value'): continue
            nm = getattr(c, 'Name', None) or c.Type + str(i)
            self._items.append((nm, c.Type, i))
    @property
    def label(self): return self.obj.Label
    def items(self): return self._items
    def get(self, name):
        try:
            for i, c in enumerate(self.obj.Constraints):
                if (getattr(c,'Name',None) or c.Type+str(i)) == name:
                    v = c.Value
                    if c.Type == "Angle":
                        v = __import__("math").degrees(v)
                    return v
        except (AttributeError, IndexError): pass
        return 0
    def set(self, name, val):
        try:
            for i, c in enumerate(self.obj.Constraints):
                if (getattr(c,'Name',None) or c.Type+str(i)) == name:
                    try:
                        if c.Type == "Angle":
                            val = __import__("math").radians(val)
                        self.obj.setDatum(i, val)
                    except (TypeError, RuntimeError): pass
                    break
        except (AttributeError, IndexError): pass
    def recompute(self):
        try: FreeCAD.ActiveDocument.recompute()
        except Exception: pass
    def meta(self, name, ptype):
        if ptype == "Angle": return ("\u00b0", 1)
        if ptype in ("Distance","DistanceX","DistanceY"): return (" mm", 2)
        if ptype == "Radius": return (" R", 2)
        if ptype == "Diameter": return (" \u00d8", 2)
        return ("", 2)


class _MultiSource:
    """Aggregates multiple DD/Sketch sources into one, prefixing names."""
    def __init__(self, sources):
        self.sources = dict(sources)  # label -> source
        self._items = []
        self._map = {}  # full_name -> (label, inner_name)
        for pref, s in self.sources.items():
            for nm, pt, *rest in s.items():
                fn = pref + "." + nm
                self._items.append((fn, pt, pref, nm))
                self._map[fn] = (pref, nm)
    @property
    def label(self): return "+".join(self.sources)
    def items(self): return self._items
    def get(self, name):
        pref, inner = self._map.get(name, (None, name))
        return self.sources[pref].get(inner) if pref else self.sources[list(self.sources)[0]].get(name)
    def set(self, name, val):
        pref, inner = self._map.get(name, (None, name))
        (self.sources[pref] if pref else self.sources[list(self.sources)[0]]).set(inner, val)
    def meta(self, name, ptype):
        pref, inner = self._map.get(name, (None, name))
        return (self.sources[pref] if pref else self.sources[list(self.sources)[0]]).meta(inner, ptype)
    def recompute(self): FreeCAD.ActiveDocument.recompute()

class DynamicData2SlidersCommandClass:
    """Sliders for any object properties or Sketch constraints."""

    def GetResources(self):
        return {'Pixmap': os.path.join(iconPath,'Sliders.svg'),
                'MenuText': 'Sliders', 'ToolTip': 'Sliders with timeline & keyframes'}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        from PySide import QtCore, QtGui

        sel = FreeCADGui.Selection.getSelection()
        subs = []

        for o in sel:
            if hasattr(o, 'Constraints') and hasattr(o, 'setDatum'):
                s = _SketchSource(o)
                if s.items(): subs.append((o.Label, s))
                continue
            pl = _get_animatable_properties(o)
            if pl:
                subs.append((o.Label, _DD2Source(o, pl)))
        if not subs:
            for o in FreeCAD.ActiveDocument.Objects:
                pl = _get_animatable_properties(o)
                if pl: subs.append((o.Label, _DD2Source(o, pl))); break
        if not subs:
            for o in FreeCAD.ActiveDocument.Objects:
                if hasattr(o, 'Constraints') and hasattr(o, 'setDatum'):
                    s = _SketchSource(o)
                    if s.items(): subs.append((o.Label, s)); break
        if not subs:
            QtGui.QMessageBox.warning(None,"Sliders","Select object(s) with numeric properties or a Sketch with dimensions.")
            return
        src = _MultiSource(subs) if len(subs) > 1 else subs[0][1]

        # ------------------------------------------------------------------
        #  Timeline bar widget (painted)
        # ------------------------------------------------------------------
        class TimelineBar(QtGui.QWidget):
            def __init__(self, panel):
                super().__init__()
                self.panel = panel
                self.setFixedHeight(30)
                self.setMinimumWidth(200)
                self._drag = False

            def _f2x(self, f):
                return int(f / max(self.panel.maxFrame,1) * (self.width()-2)) + 1

            def paintEvent(self, event):
                p = QtGui.QPainter(self)
                w, h = self.width(), self.height()
                p.fillRect(0, 0, w, h, QtGui.QColor(45,45,45))
                # frame ticks
                step = max(1, self.panel.maxFrame // 20)
                p.setPen(QtGui.QColor(80,80,80))
                for f in range(0, self.panel.maxFrame+1, step):
                    x = self._f2x(f)
                    p.drawLine(x, h-12, x, h-2)
                # keyframe diamonds
                p.setPen(QtGui.QColor(255,200,50))
                p.setBrush(QtGui.QColor(255,200,50))
                for f in self.panel.keyframes:
                    x = self._f2x(f)
                    pts = [QtCore.QPoint(x, h-4),QtCore.QPoint(x+4, h-10),
                           QtCore.QPoint(x, h-16),QtCore.QPoint(x-4, h-10)]
                    p.drawPolygon(pts)
                # playhead
                x = self._f2x(self.panel.currentFrame)
                p.setPen(QtGui.QPen(QtGui.QColor(255,80,80),2))
                p.drawLine(x, 2, x, h-2)
                p.drawText(x-15, 2, 30, 12, QtCore.Qt.AlignCenter, str(self.panel.currentFrame))
                p.end()

            def mousePressEvent(self, e):
                if e.button() == QtCore.Qt.LeftButton:
                    self._drag = True
                    self._move(e.x())
            def mouseMoveEvent(self, e):
                if self._drag: self._move(e.x())
            def mouseReleaseEvent(self, e):
                self._drag = False
            def _move(self, mx):
                f = int(mx / self.width() * self.panel.maxFrame)
                f = max(0, min(self.panel.maxFrame, f))
                self.panel.currentFrame = f
                self.panel._interpolate()
                self.panel._sync_display()
                self.update()

        # ------------------------------------------------------------------
        #  Slider panel
        # ------------------------------------------------------------------
        class SliderPanel(QtGui.QWidget):
            def __init__(self):
                super().__init__(None)
                self.src = src
                self.slots = {}
                self.keyframes = {}
                self.currentFrame = 0
                self.maxFrame = 100
                self.fps = 24
                self._anim = None
                self._tracks = []
                self._timer = QtCore.QTimer(self)
                self._timer.timeout.connect(self._tick)
                self._busy = False
                self._restore = {}
                self._collapsed = False
                self._expanded_h = 0
                self._force_close = False
                self._pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/DynamicData2/SlidersPanel")
                self._plist = list(self.src.items())
                self._build(self._plist)
                self._open_restore = {pn: self.src.get(pn) for pn in self.slots}
                self._restore_state()
                for pn, sl in self.slots.items():
                    cb = sl.get("cb")
                    if cb: cb.setChecked(self._pg.GetBool("perm_"+pn, False))
                self._restore_geo()
            def _build(self, plist):
                self.setWindowTitle("Sliders — " + self.src.label)
                self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
                self.setMinimumWidth(380)
                lo = QtGui.QVBoxLayout(); lo.setSpacing(4); lo.setContentsMargins(8,8,8,8)
                # top bar (always visible)
                tr = QtGui.QHBoxLayout()
                self._sel = QtGui.QComboBox()
                for pn, pt, *rest in plist: self._sel.addItem(pn, pn)
                self._sel.currentIndexChanged.connect(lambda i: (self._sel2.blockSignals(True), self._sel2.setCurrentIndex(i), self._sel2.blockSignals(False), self._update_range()))
                tr.addWidget(self._sel)
                self._cplay = QtGui.QPushButton("Play"); self._cplay.setCheckable(True)
                self._cplay.setFixedWidth(50)
                self._cplay.toggled.connect(self._play_by_mode)
                self._cplay.setStyleSheet("QPushButton:checked{background:#4caf50;color:#fff;font-weight:bold}")
                tr.addWidget(self._cplay)
                tr.addWidget(QtGui.QLabel("Spd"))
                self._stp = QtGui.QDoubleSpinBox()
                self._stp.setRange(0.01,99999); self._stp.setValue(5.0); self._stp.setFixedWidth(60)
                self._stp.valueChanged.connect(lambda v: (
                    self._stp2.blockSignals(True), self._stp2.setValue(v), self._stp2.blockSignals(False),
                    setattr(self,'step',v),
                    self._anim.update({'step':v}) if self._anim else None,
                    self._timer.setInterval(self._timer_interval()) if self._timer.isActive() else None
                ) and None)
                tr.addWidget(self._stp)
                self._addbtn = QtGui.QPushButton("+"); self._addbtn.setFixedWidth(24)
                self._addbtn.setToolTip("Add properties from selected object(s)")
                self._addbtn.clicked.connect(self._add_sources)
                tr.addWidget(self._addbtn)
                self._fold = QtGui.QPushButton("▾"); self._fold.setFixedWidth(24)
                self._fold.setToolTip("Click to collapse  |  Right-click to close")
                self._fold.clicked.connect(self._toggle_collapse)
                self._fold.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
                self._fold.customContextMenuRequested.connect(lambda _: self.close())
                tr.addWidget(self._fold)
                lo.addLayout(tr)
                # content (collapsible)
                self._content = QtGui.QWidget()
                cx = QtGui.QVBoxLayout(self._content); cx.setSpacing(4); cx.setContentsMargins(0,0,0,0)
                if not plist:
                    cx.addWidget(QtGui.QLabel("No numeric properties or constraints"))
                else:
                    for pn, pt, *rest in plist:
                        self._add_row(cx, pn, pt)
                af = QtGui.QGroupBox("Animation")
                al = QtGui.QVBoxLayout(); al.setSpacing(3)
                mr = QtGui.QHBoxLayout()
                mr.addWidget(QtGui.QLabel("Mode:"))
                self._mode = QtGui.QComboBox()
                self._mode.addItems(["Timeline", "Bounce", "Tracks"])
                self._mode.currentTextChanged.connect(self._mode_changed)
                mr.addWidget(self._mode); mr.addStretch()
                self._save = QtGui.QPushButton("Save"); self._save.clicked.connect(self._save_kf)
                mr.addWidget(self._save)
                self._load = QtGui.QPushButton("Load"); self._load.clicked.connect(self._load_kf)
                mr.addWidget(self._load)
                self._export = QtGui.QPushButton("Export"); self._export.clicked.connect(self._export_frames)
                mr.addWidget(self._export)
                al.addLayout(mr)
                # timeline controls
                self._tl_w = QtGui.QWidget()
                tw = QtGui.QVBoxLayout(self._tl_w); tw.setContentsMargins(0,0,0,0)
                self.tbar = TimelineBar(self)
                tw.addWidget(self.tbar)
                fr = QtGui.QHBoxLayout()
                fr.addWidget(QtGui.QLabel("Frame:"))
                self._frm = QtGui.QSpinBox(); self._frm.setRange(0,9999)
                self._frm.valueChanged.connect(lambda v: self._set_frame(v))
                fr.addWidget(self._frm)
                fr.addWidget(QtGui.QLabel("/"))
                self._maxf = QtGui.QSpinBox(); self._maxf.setRange(1,9999); self._maxf.setValue(100)
                self._maxf.valueChanged.connect(lambda v: setattr(self,'maxFrame',v) or self._maxf_changed())
                fr.addWidget(self._maxf)
                fr.addWidget(QtGui.QLabel("FPS:"))
                self._fps = QtGui.QSpinBox(); self._fps.setRange(1,120); self._fps.setValue(24)
                self._fps.valueChanged.connect(lambda v: setattr(self,'fps',v) or (self._timer.setInterval(self._timer_interval()) if self._timer.isActive() else None))
                fr.addWidget(self._fps); tw.addLayout(fr)
                kr = QtGui.QHBoxLayout()
                self._addk = QtGui.QPushButton("+ Key"); self._addk.clicked.connect(self._add_key)
                kr.addWidget(self._addk)
                self._delk = QtGui.QPushButton("- Key"); self._delk.clicked.connect(self._del_key)
                kr.addWidget(self._delk)
                self._clear = QtGui.QPushButton("Clear"); self._clear.clicked.connect(self._clear_kf)
                kr.addWidget(self._clear); kr.addStretch()
                tw.addLayout(kr)
                al.addWidget(self._tl_w)
                # bounce controls
                self._bo_w = QtGui.QWidget()
                bw = QtGui.QVBoxLayout(self._bo_w); bw.setContentsMargins(0,0,0,0)
                r1 = QtGui.QHBoxLayout()
                r1.addWidget(QtGui.QLabel("Param:"))
                self._sel2 = QtGui.QComboBox()
                for pn, pt, *rest in plist: self._sel2.addItem(pn, pn)
                self._sel2.currentIndexChanged.connect(lambda i: (self._sel.blockSignals(True), self._sel.setCurrentIndex(i), self._sel.blockSignals(False), self._update_range()))
                r1.addWidget(self._sel2); bw.addLayout(r1)
                r2 = QtGui.QHBoxLayout()
                r2.addWidget(QtGui.QLabel("Range:"))
                self._lo = QtGui.QDoubleSpinBox(); self._lo.setRange(-99999,99999)
                self._hi = QtGui.QDoubleSpinBox(); self._hi.setRange(-99999,99999)
                self._lo.setValue(0); self._hi.setValue(360)
                self._update_range()
                r2.addWidget(self._lo); r2.addWidget(QtGui.QLabel("~")); r2.addWidget(self._hi)
                bw.addLayout(r2)
                r3 = QtGui.QHBoxLayout()
                r3.addWidget(QtGui.QLabel("Spd"))
                self._stp2 = QtGui.QDoubleSpinBox()
                self._stp2.setRange(0.01,99999); self._stp2.setValue(5.0)
                self._stp2.valueChanged.connect(lambda v: (
                    self._stp.blockSignals(True), self._stp.setValue(v), self._stp.blockSignals(False),
                    self._anim.update({'step':v}) if self._anim else None,
                    self._timer.setInterval(self._timer_interval()) if self._timer.isActive() else None
                ) and None)
                r3.addWidget(self._stp2); r3.addStretch()
                bw.addLayout(r3)
                self._bo_w.setVisible(False)
                al.addWidget(self._bo_w)
                # ---- tracks controls ----
                self._seq_w = QtGui.QWidget()
                sqw = QtGui.QVBoxLayout(self._seq_w); sqw.setContentsMargins(0,0,0,0)
                # track list
                self._track_area = QtGui.QScrollArea()
                self._track_content = QtGui.QWidget()
                self._track_layout = QtGui.QVBoxLayout(self._track_content)
                self._track_area.setWidget(self._track_content)
                self._track_area.setWidgetResizable(True)
                self._track_area.setFixedHeight(150)
                sqw.addWidget(self._track_area)
                # + add button
                ar = QtGui.QHBoxLayout()
                self._add_track_btn = QtGui.QPushButton("+ Add Track")
                self._add_track_btn.clicked.connect(self._add_track)
                ar.addWidget(self._add_track_btn); ar.addStretch()
                sqw.addLayout(ar)
                self._seq_w.setVisible(False)
                al.addWidget(self._seq_w)
                af.setLayout(al); cx.addWidget(af)
                # status
                bh = QtGui.QHBoxLayout()
                self._status = QtGui.QLabel(""); bh.addWidget(self._status)
                bh.addStretch()
                cx.addLayout(bh)
                sa = QtGui.QScrollArea()
                sa.setWidgetResizable(True)
                sa.setWidget(self._content)
                lo.addWidget(sa)
                # unified Play + Loop row (bottom)
                pr = QtGui.QHBoxLayout()
                self._bottom_play = QtGui.QPushButton("Play"); self._bottom_play.setCheckable(True)
                self._bottom_play.toggled.connect(self._play_by_mode)
                self._bottom_play.setStyleSheet("QPushButton:checked{background:#4caf50;color:#fff;font-weight:bold}")
                self._bottom_play.setFixedHeight(32)
                pr.addWidget(self._bottom_play)
                self._sq_loop = QtGui.QCheckBox("Loop")
                pr.addWidget(self._sq_loop); pr.addStretch()
                lo.addLayout(pr)
                self.setLayout(lo)
            def _update_range(self):
                pn = self._sel.currentData()
                for name, ptype, *rest in self._plist:
                    if name == pn:
                        if "Angle" in ptype:
                            self._lo.setRange(0, 360)
                            self._hi.setRange(0, 360)
                        else:
                            self._lo.setRange(-99999, 99999)
                            self._hi.setRange(-99999, 99999)
                        break
            def _add_row(self, lo, pn, pt):
                v = self.src.get(pn)
                sfx, dec = self.src.meta(pn, pt)
                sp = QtGui.QDoubleSpinBox()
                if "Angle" in pt:
                    sp.setRange(0, 360)
                else:
                    sp.setRange(-99999, 99999)
                sp.setValue(v)
                sp.setSuffix(sfx); sp.setDecimals(dec)
                s = QtGui.QSlider(QtCore.Qt.Horizontal)
                if "Angle" in pt:
                    scale = 10; half = 0
                    s.setRange(0, 3600)
                    s.setValue(int(v * scale))
                    s.valueChanged.connect(lambda x, sp=sp, sc=scale: sp.setValue(x / sc))
                    sp.valueChanged.connect(lambda x, pn=pn: self._ch(pn, x))
                else:
                    scale = 10; half = max(abs(v)*3, 100)*scale
                    s.setRange(0, int(half*2))
                    s.setValue(int(half + v*scale))
                    s.valueChanged.connect(lambda x, sp=sp, sc=scale, hh=half: sp.setValue((x-hh)/sc))
                    sp.valueChanged.connect(lambda x, pn=pn: self._ch(pn, x))
                cb = QtGui.QCheckBox("Perm")
                vl = QtGui.QLineEdit(); vl.setPlaceholderText("0,50,100"); vl.setFixedWidth(80); vl.setVisible(False)
                g = QtGui.QGroupBox(pn)
                gl = QtGui.QVBoxLayout()
                h = QtGui.QHBoxLayout(); h.addWidget(s, stretch=2); h.addWidget(sp, stretch=1); h.addWidget(cb); h.addWidget(vl)
                gl.addLayout(h); g.setLayout(gl); lo.addWidget(g)
                self.slots[pn] = {"s":s,"sp":sp,"scale":scale,"half":half,"cb":cb,"vl":vl}
            def _ch(self, pn, v):
                if self._busy: return
                self._busy = True
                self.src.set(pn, v)
                sl = self.slots[pn]
                sv = int(sl["half"] + v*sl["scale"])
                if sv < sl["s"].minimum() or sv > sl["s"].maximum():
                    r = max(abs(sv)*2, 1000)
                    sl["s"].setRange(min(0, -r), max(0, r))
                sl["s"].blockSignals(True); sl["s"].setValue(sv); sl["s"].blockSignals(False)
                sl["sp"].blockSignals(True); sl["sp"].setValue(v); sl["sp"].blockSignals(False)
                self._busy = False
                self._defer_recompute()
            def _defer_recompute(self):
                t = getattr(self, '_rt', None)
                if not t:
                    t = QtCore.QTimer(self); t.setSingleShot(True)
                    t.timeout.connect(lambda: self.src.recompute())
                    self._rt = t
                t.start(50)
            # ---- geometry ----
            def _restore_geo(self):
                x = self._pg.GetInt("geoX", -1)
                y = self._pg.GetInt("geoY", 60)
                w = self._pg.GetInt("geoW", 400)
                h = self._pg.GetInt("geoH", 500)
                on_screen = False
                if x >= 0:
                    from PySide import QtGui
                    app = QtGui.QGuiApplication.instance()
                    if app:
                        for screen in app.screens():
                            sg = screen.availableGeometry()
                            if sg.x() <= x <= sg.right() - 100 and sg.y() <= y <= sg.bottom() - 30:
                                on_screen = True
                                break
                if x < 0 or not on_screen:
                    mw = FreeCADGui.getMainWindow()
                    if mw:
                        g = mw.geometry(); p = self.geometry()
                        self.move(g.right() - p.width() - 40, g.top() + 60)
                else:
                    self.setGeometry(x, y, w, h)
            # ---- close ----
            def closeEvent(self, event):
                if self._force_close:
                    self._save_close(event)
                    event.accept(); return
                if self._pg.GetBool("closeNoPrompt", False):
                    self._save_close(event)
                    event.accept(); return
                if self._timer.isActive():
                    r = QtGui.QMessageBox.question(self, "Animation Running",
                        "Animation is still running.\nStop and close?",
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                    if r == QtGui.QMessageBox.No: event.ignore(); return
                    self._timer.stop()
                else:
                    cb = QtGui.QCheckBox("Don't show again / 下次不提醒")
                    msg = QtGui.QMessageBox(self)
                    msg.setWindowTitle("Close Sliders")
                    msg.setText("Close the Sliders panel?")
                    msg.setCheckBox(cb)
                    msg.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                    r = msg.exec_()
                    if r == QtGui.QMessageBox.No: event.ignore(); return
                    if cb.isChecked(): self._pg.SetBool("closeNoPrompt", True)
                self._save_close(event)

            def _save_close(self, event):
                if self._timer.isActive():
                    self._timer.stop()
                self._restore_vals()
                g = self.geometry()
                self._pg.SetInt("geoX", g.x()); self._pg.SetInt("geoY", g.y())
                self._pg.SetInt("geoW", g.width()); self._pg.SetInt("geoH", g.height())
                self._save_state()
                event.accept()
            # ---- persist ----
            def _restore_state(self):
                mode = self._pg.GetString("mode", "Timeline")
                idx = self._mode.findText(mode)
                if idx >= 0: self._mode.setCurrentIndex(idx)
                self.maxFrame = self._pg.GetInt("maxFrame", 100)
                self.fps = self._pg.GetInt("fps", 24)
                self._maxf.setValue(self.maxFrame)
                self._fps.setValue(self.fps)
                pn = self._pg.GetString("bounceParam", "")
                for i in range(self._sel.count()):
                    if self._sel.itemText(i) == pn: self._sel.setCurrentIndex(i); break
                self._lo.setValue(self._pg.GetFloat("bounceLo", 0))
                self._hi.setValue(self._pg.GetFloat("bounceHi", 360))
                self._stp.setValue(self._pg.GetFloat("bounceStep", 0.3))
                import json
                for td in json.loads(self._pg.GetString("tracks", "[]")):
                    f = td.get("from") or td.get("target")
                    t = td.get("to") or f
                    self._add_track(prop=td.get("prop"), from_val=f, to_val=t, dur=td.get("dur"))
                self._sq_loop.setChecked(self._pg.GetBool("seqLoop", False))
            def _save_state(self):
                self._pg.SetString("mode", self._mode.currentText())
                self._pg.SetInt("maxFrame", self.maxFrame)
                self._pg.SetInt("fps", self.fps)
                self._pg.SetString("bounceParam", self._sel.currentText())
                self._pg.SetFloat("bounceLo", self._lo.value())
                self._pg.SetFloat("bounceHi", self._hi.value())
                self._pg.SetFloat("bounceStep", self._stp.value())
                for pn, sl in self.slots.items():
                    self._pg.SetBool("perm_"+pn, sl.get("cb",QtGui.QCheckBox()).isChecked())
                import json
                track_data = [{"prop": t["prop_cb"].currentText(), "from": t["from_w"].value(), "to": t["to_w"].value(), "dur": t["dur_w"].value()} for t in self._tracks]
                self._pg.SetString("tracks", json.dumps(track_data))
                self._pg.SetBool("seqLoop", self._sq_loop.isChecked())
            # ---- snapshot / restore ----
            def _snapshot(self):
                self._restore = {}
                for pn in self.slots: self._restore[pn] = self.src.get(pn)
            def _restore_vals(self):
                src = self._restore if self._restore else self._open_restore
                changed = False
                for pn, v in src.items():
                    if pn in self.slots:
                        if self.slots[pn].get("cb") and self.slots[pn]["cb"].isChecked(): continue
                        try:
                            self._busy = True
                            self.src.set(pn, v)
                            changed = True
                            sl = self.slots[pn]
                            sv = int(sl["half"] + v*sl["scale"])
                            sl["s"].blockSignals(True); sl["s"].setValue(sv); sl["s"].blockSignals(False)
                            sl["sp"].blockSignals(True); sl["sp"].setValue(v); sl["sp"].blockSignals(False)
                            self._busy = False
                        except Exception:
                            self._busy = False
                if changed:
                    try: self.src.recompute()
                    except Exception: pass
                if self._restore: self._status.setText("Restored")
                self._restore = {}
            # ---- mode switch ----
            def _mode_changed(self, mode):
                self._timer.stop(); self._anim = None
                self._set_play_buttons(False)
                self._restore_vals()
                self._tl_w.setVisible(mode == "Timeline")
                self._bo_w.setVisible(mode == "Bounce")
                self._seq_w.setVisible(mode == "Tracks")
                self._save_state()
            # ---- tracks ----
            def _add_track(self, prop=None, from_val=None, to_val=None, dur=None):
                w = QtGui.QWidget()
                r = QtGui.QHBoxLayout(w); r.setContentsMargins(0,0,0,0)
                cb = QtGui.QComboBox()
                cb.blockSignals(True)
                for pn, pt, *rest in self._plist:
                    cb.addItem(pn, pn)
                if prop is not None and cb.findText(str(prop)) >= 0:
                    cb.setCurrentText(str(prop))
                cb.blockSignals(False)
                cb.setMinimumWidth(120)
                r.addWidget(cb); r.addWidget(QtGui.QLabel("→"))
                pn = cb.currentText()
                try:
                    v = self.src.get(pn)
                except Exception:
                    v = 0
                fw = QtGui.QDoubleSpinBox(); fw.setRange(-99999, 99999); fw.setDecimals(3)
                fw.setValue(from_val if from_val is not None else v)
                tw = QtGui.QDoubleSpinBox(); tw.setRange(-99999, 99999); tw.setDecimals(3)
                tw.setValue(to_val if to_val is not None else v)
                r.addWidget(fw); r.addWidget(QtGui.QLabel("→")); r.addWidget(tw)
                td = QtGui.QDoubleSpinBox(); td.setRange(0.01, 9999); td.setValue(dur if dur else 1.0); td.setSuffix(" s"); td.setDecimals(2)
                r.addWidget(td)
                rm = QtGui.QPushButton("×"); rm.setFixedWidth(24)
                r.addWidget(rm)
                self._track_layout.addWidget(w)
                entry = {"prop_cb": cb, "from_w": fw, "to_w": tw, "dur_w": td, "widget": w}
                self._tracks.append(entry)
                def _on_prop_changed(text, cb=cb, fw=fw, tw=tw):
                    try:
                        if text in [p[0] for p in self._plist]:
                            v = self.src.get(text)
                            fw.setValue(v); tw.setValue(v)
                    except Exception: pass
                cb.currentTextChanged.connect(_on_prop_changed)
                rm.clicked.connect(lambda checked, e=entry: self._remove_track(e))
                self._save_state()
            def _remove_track(self, entry):
                if entry in self._tracks: self._tracks.remove(entry)
                w = entry["widget"]
                self._track_layout.removeWidget(w); w.deleteLater()
                self._save_state()
            def _clear_tracks(self):
                while self._tracks:
                    entry = self._tracks.pop()
                    w = entry["widget"]
                    self._track_layout.removeWidget(w); w.deleteLater()
                self._save_state()
            def _repopulate_track_combos(self):
                for t in self._tracks:
                    cb = t["prop_cb"]
                    old = cb.currentText()
                    cb.blockSignals(True); cb.clear()
                    for pn, pt, *rest in self._plist:
                        cb.addItem(pn, pn)
                    idx = cb.findText(old)
                    if idx >= 0: cb.setCurrentIndex(idx)
                    cb.blockSignals(False)
            # ---- add sources ----
            def _add_sources(self):
                sel = FreeCADGui.Selection.getSelection()
                if not sel:
                    self._status.setText("Select object(s) first"); return
                new_subs = []
                for o in sel:
                    if hasattr(o,'Constraints') and hasattr(o,'setDatum'):
                        s = _SketchSource(o)
                        if s.items(): new_subs.append((o.Label, s))
                        continue
                    pl = _get_animatable_properties(o)
                    if pl: new_subs.append((o.Label, _DD2Source(o, pl)))
                if not new_subs: return
                old = self.src
                if isinstance(old, _MultiSource):
                    cur = dict(old.sources)
                else:
                    cur = {old.label: old}
                new_labels = [l for l,_ in new_subs if l not in cur]
                if not new_labels:
                    self._status.setText("Already added"); return
                cur.update((l,s) for l,s in new_subs if l in new_labels)
                self.src = _MultiSource(list(cur.items())) if len(cur)>1 else list(cur.values())[0]
                saved = {}
                for pn in self.slots:
                    try: saved[pn] = self.src.get(pn)
                    except: pass
                self._plist = list(self.src.items())
                cx = self._content.layout()
                while cx.count() > 2:
                    item = cx.takeAt(0)
                    w = item.widget()
                    if w: w.deleteLater()
                self.slots = {}
                for pn, pt, *rest in self._plist:
                    self._add_row(cx, pn, pt)
                self._sel.clear(); self._sel2.clear()
                for pn, pt, *rest in self._plist:
                    self._sel.addItem(pn, pn); self._sel2.addItem(pn, pn)
                for pn in self.slots:
                    if pn in saved: self.src.set(pn, saved[pn])
                self._open_restore = {pn: self.src.get(pn) for pn in self.slots}
                self._repopulate_track_combos()
                self._status.setText("+ " + ", ".join(new_labels))
            # ---- keyframes ----
            def _toggle_collapse(self):
                self._collapsed = not self._collapsed
                if self._content: self._content.setVisible(not self._collapsed)
                self._fold.setText("▸" if self._collapsed else "▾")
                self._fold.setToolTip(
                    "Click to expand  |  Right-click to close" if self._collapsed
                    else "Click to collapse  |  Right-click to close")
                if self._collapsed:
                    self._expanded_h = self.height()
                    self.setFixedHeight(self.minimumSizeHint().height())
                else:
                    self.setMinimumHeight(0); self.setMaximumHeight(16777215)
                    self.resize(self.width(), self._expanded_h)
            def _clear_kf(self):
                self.keyframes.clear()
                self.tbar.update(); self._status.setText("Cleared")
            def _add_key(self):
                vals = {}
                for pn in self.slots: vals[pn] = self.src.get(pn)
                self.keyframes[self.currentFrame] = vals
                self.tbar.update(); self._status.setText("Key @" + str(self.currentFrame))
            def _del_key(self):
                self.keyframes.pop(self.currentFrame, None)
                self.tbar.update(); self._status.setText("Del @" + str(self.currentFrame))
            # ---- save / load ----
            def _save_kf(self):
                import json
                path, _ = QtGui.QFileDialog.getSaveFileName(self, "Save Keyframes", "", "JSON (*.json)")
                if not path: return
                with open(path, 'w') as f: json.dump({"keyframes": self.keyframes}, f, indent=2)
                self._status.setText("Saved " + os.path.basename(path))
            def _load_kf(self):
                import json
                path, _ = QtGui.QFileDialog.getOpenFileName(self, "Load Keyframes", "", "JSON (*.json)")
                if not path: return
                with open(path, 'r') as f: data = json.load(f)
                self.keyframes = {int(k): v for k, v in data.get("keyframes", {}).items()}
                self._status.setText("Loaded " + os.path.basename(path)); self.tbar.update()
            def _export_frames(self):
                import os
                folder = QtGui.QFileDialog.getExistingDirectory(self, "Select output folder")
                if not folder: return
                was_active = self._timer.isActive()
                if was_active: self._timer.stop()
                saved_frame = self.currentFrame
                self._status.setText("Exporting...")
                QtGui.QApplication.processEvents()
                view = FreeCADGui.activeDocument().activeView()
                for f in range(self.maxFrame + 1):
                    self.currentFrame = f
                    if self._mode.currentText() == "Timeline":
                        self._interpolate()
                    else:
                        pn = self._sel.currentData()
                        t = f / max(self.maxFrame, 1)
                        v = self._lo.value() + (self._hi.value() - self._lo.value()) * t
                        self.src.set(pn, v)
                    self.src.recompute()
                    QtGui.QApplication.processEvents()
                    fp = os.path.join(folder, f"frame_{f:04d}.png")
                    try:
                        view.saveImage(fp)
                    except Exception: pass
                self.currentFrame = saved_frame
                self._interpolate(); self._sync_display()
                if was_active: self._timer.start(self._timer_interval())
                self._status.setText("Exported " + str(self.maxFrame+1) + " frames")
            # ---- interpolation ----
            def _interpolate(self, frame=None):
                if frame is None: frame = self.currentFrame
                sf = sorted(self.keyframes.keys())
                if not sf: return
                if frame <= sf[0]: vals = self.keyframes[sf[0]]
                elif frame >= sf[-1]: vals = self.keyframes[sf[-1]]
                else:
                    lo = max(f for f in sf if f <= frame); hi = min(f for f in sf if f >= frame)
                    if lo == hi: vals = self.keyframes[lo]
                    else:
                        t = (frame - lo) / (hi - lo); vals = {}
                        for p in self.slots:
                            if p in self.keyframes[lo] and p in self.keyframes[hi]:
                                vlo, vhi = self.keyframes[lo][p], self.keyframes[hi][p]
                                vals[p] = vlo + (vhi - vlo) * t
                            elif p in self.keyframes[lo]: vals[p] = self.keyframes[lo][p]
                            else: vals[p] = self.keyframes[hi].get(p, 0)
                for p, v in vals.items():
                    if p in self.slots: self.src.set(p, v)
                try: self.src.recompute()
                except Exception: pass
            def _sync_display(self):
                self._frm.blockSignals(True); self._frm.setValue(self.currentFrame); self._frm.blockSignals(False)
                for pn, sl in self.slots.items():
                    v = self.src.get(pn)
                    sv = int(sl["half"] + v*sl["scale"])
                    sl["s"].blockSignals(True); sl["s"].setValue(sv); sl["s"].blockSignals(False)
                    sl["sp"].blockSignals(True); sl["sp"].setValue(v); sl["sp"].blockSignals(False)
                self.tbar.update()
            def _set_frame(self, f): self.currentFrame = f; self._interpolate(); self._sync_display()
            def _maxf_changed(self): self.tbar.update()
            # ---- play (unified) ----
            def _set_play_buttons(self, on):
                for b in (self._cplay, self._bottom_play):
                    b.blockSignals(True); b.setChecked(on); b.blockSignals(False)
            def _timer_interval(self):
                return int(1000/(self.fps*max(self._stp.value(),0.1)))
            def _play_by_mode(self, on):
                m = self._mode.currentText()
                if m == "Timeline":
                    self._tog(on)
                elif m == "Bounce":
                    self._btog(on)
                else:
                    self._stog(on)
            # ---- play: timeline ----
            def _tog(self, on):
                self._set_play_buttons(on)
                if on:
                    self._snapshot()
                    ti = int(1000 / self.fps) if self.keyframes else self._timer_interval()
                    self._timer.start(ti)
                else:
                    self._timer.stop(); self._restore_vals()
            # ---- play: bounce ----
            def _btog(self, on):
                self._set_play_buttons(on)
                if on:
                    self._snapshot()
                    pn = self._sel.currentData()
                    self._anim = {"mode": "bounce", "prop": pn, "lo": self._lo.value(), "hi": self._hi.value(), "step": self._stp.value()}
                    self._timer.start(self._timer_interval())
                else:
                    self._timer.stop(); self._anim = None; self._restore_vals()
            # ---- play: tracks ----
            def _stog(self, on):
                self._set_play_buttons(on)
                if on:
                    if not self._tracks:
                        self._status.setText("Add tracks first"); self._set_play_buttons(False); return
                    self._snapshot()
                    tracks = []
                    for t in self._tracks:
                        pn = t["prop_cb"].currentText()
                        if pn not in self.slots: continue
                        start = t["from_w"].value()
                        target = t["to_w"].value()
                        dur = t["dur_w"].value()
                        tracks.append({"prop": pn, "start": start, "target": target, "dur": max(dur, 0.01)})
                    if not tracks:
                        self._status.setText("No valid tracks"); self._set_play_buttons(False); return
                    self._anim = {"mode": "tracks", "tracks": tracks, "loop": self._sq_loop.isChecked(), "elapsed": 0.0}
                    self._timer.start(self._timer_interval())
                else:
                    self._timer.stop(); self._anim = None; self._restore_vals()
            def _eval_exprs(self): pass
            def _has_exprs(self): return False
            def _tick(self):
                if self._anim:
                    a = self._anim
                    if a.get("mode") == "tracks":
                        dt = self._timer_interval() / 1000.0
                        elapsed = a["elapsed"] + dt
                        a["elapsed"] = elapsed
                        all_done = True
                        for tr in a.get("tracks", []):
                            if elapsed < tr["dur"]:
                                t = elapsed / tr["dur"]
                                v = tr["start"] + (tr["target"] - tr["start"]) * t
                                self.src.set(tr["prop"], v)
                                all_done = False
                            else:
                                self.src.set(tr["prop"], tr["target"])
                        self.src.recompute(); self._sync_display()
                        if all_done:
                            if a.get("loop"):
                                a["elapsed"] = 0.0
                            else:
                                self._set_play_buttons(False)
                    elif a.get("mode") == "bounce":
                        v = self.src.get(a["prop"]) + a.get("step", 0.3)
                        if v >= a.get("hi", 360): v = a.get("lo", 0)
                        self.src.set(a["prop"], v)
                        self.src.recompute()
                        self._sync_display()
                elif self.keyframes:
                    self.currentFrame += 1
                    if self.currentFrame > self.maxFrame: self.currentFrame = 0
                    self._interpolate(); self._sync_display()
                else:
                    self._set_play_buttons(False)

        if hasattr(self, 'panel') and self.panel:
            self.panel._force_close = True
            self.panel._timer.stop(); self.panel.close(); self.panel.deleteLater()
        self.panel = SliderPanel()
        self.panel.show(); self.panel.raise_(); self.panel.activateWindow()


Gui.addCommand("DynamicData2CreateObject", DynamicData2CreateObjectCommandClass())
Gui.addCommand("DynamicData2AddProperty", DynamicData2AddPropertyCommandClass())
Gui.addCommand("DynamicData2RemoveProperty", DynamicData2RemovePropertyCommandClass())
Gui.addCommand("DynamicData2EditEnumeration",DynamicData2EditEnumerationCommandClass())
Gui.addCommand("DynamicData2CreateConfiguration", DynamicData2CreateConfigurationCommandClass())
Gui.addCommand("DynamicData2MoveToNewGroup", DynamicData2MoveToNewGroupCommandClass())
Gui.addCommand("DynamicData2ImportNamedConstraints", DynamicData2ImportNamedConstraintsCommandClass())
Gui.addCommand("DynamicData2ImportAliases", DynamicData2ImportAliasesCommandClass())
Gui.addCommand("DynamicData2RenameProperty",DynamicData2RenamePropertyCommandClass())
Gui.addCommand("DynamicData2RetypeProperty", DynamicData2RetyePropertyCommandClass())
Gui.addCommand("DynamicData2SetTooltip", DynamicData2SetTooltipCommandClass())
Gui.addCommand("DynamicData2Settings", DynamicData2SettingsCommandClass())
Gui.addCommand("DynamicData2CopyProperty", DynamicData2CopyPropertyCommandClass())
Gui.addCommand("DynamicData2Sliders", DynamicData2SlidersCommandClass())
Gui.addCommand("DynamicData2Commands", DynamicData2Commands())
