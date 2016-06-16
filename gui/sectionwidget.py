#-----------------------------------------------------------
#
# QGIS wincan 2 QGEP Plugin
# Copyright (C) 2016 Denis Rouzaud
#
#-----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------


from PyQt4.QtCore import pyqtSlot, Qt
from PyQt4.QtGui import QWidget, QIcon, QListWidgetItem

from qgis.core import QgsMapLayerRegistry, QgsApplication

from wincan2qgep.core.mysettings import MySettings
from wincan2qgep.core.section import findSection, sectionAtId
from wincan2qgep.gui.featureselectorwidget import CanvasExtent
from wincan2qgep.ui.ui_sectionwidget import Ui_SectionWidget

warning_icon = QgsApplication.getThemeIcon( "/mIconWarn.png" )


class SectionWidget(QWidget, Ui_SectionWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.settings = MySettings()
        self.data = {}
        self.projectId = None
        self.section_id = None

        self.section1Selector.featureIdentified.connect(self.setQgepChannelId1)
        self.section2Selector.featureIdentified.connect(self.setQgepChannelId2)
        self.section3Selector.featureIdentified.connect(self.setQgepChannelId3)

        self.inspectionWidget.importChanged.connect(self.update_status)

        self.sectionListWidget.itemChanged.connect(self.sectionItemChanged)

    def finish_init(self, iface, data):
        layer_id = self.settings.value("channelLayer")
        for selector in (self.section1Selector, self.section2Selector, self.section3Selector):
            selector.setLayer(QgsMapLayerRegistry.instance().mapLayer(layer_id))
            selector.setCanvas(iface.mapCanvas())
        self.data = data
        self.inspectionWidget.finish_init(self.data)

    def set_project_id(self, prjId = None):
        self.sectionListWidget.clear()

        if prjId is not None:
            self.projectId = prjId

        if self.projectId is None:
            return

        for s_id, section in self.data[prjId]['Sections'].items():
            title = '{0}: de {1} a {2}'.format(section['Counter'], section['StartNode'], section['EndNode'])
            item = QListWidgetItem(warning_icon, title)
            item.setData(Qt.UserRole, s_id)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if section['Import'] else Qt.Unchecked)
            self.sectionListWidget.addItem(item)
        self.update_status()

    def update_status(self):
        for r in range(0, self.sectionListWidget.count()):
            item = self.sectionListWidget.item(r)
            s_id = item.data(Qt.UserRole)
            section = self.data[self.projectId]['Sections'][s_id]
            ok = section['QgepChannelId1'] is not None or section['UsePreviousSection'] is True
            if not ok:
                ok = True
                for inspection in section['Inspections'].values():
                    if inspection['Import']:
                        ok = False
                        break
            if ok:
                item.setIcon(QIcon())
            else:
                item.setIcon(warning_icon)

    def sectionItemChanged(self, item):
        s_id = item.data(Qt.UserRole)
        if self.projectId is None:
            return
        self.data[self.projectId]['Sections'][s_id]['Import'] = bool(item.checkState())

    def setQgepChannelId1(self, feature):
        if self.projectId is None or self.section_id is None:
            return
        self.data[self.projectId]['Sections'][self.section_id]['QgepChannelId1'] = feature.attribute('obj_id')
        self.update_status()

    def setQgepChannelId2(self, feature):
        if self.projectId is None or self.section_id is None:
            return
        self.data[self.projectId]['Sections'][self.section_id]['QgepChannelId2'] = feature.attribute('obj_id')

    def setQgepChannelId3(self, feature):
        if self.projectId is None or self.section_id is None:
            return
        self.data[self.projectId]['Sections'][self.section_id]['QgepChannelId3'] = feature.attribute('obj_id')

    @pyqtSlot(bool)
    def on_usePreviousSectionCheckBox_toggled(self, checked):
        if self.projectId is None or self.section_id is None:
            return
        self.data[self.projectId]['Sections'][self.section_id]['UsePreviousSection'] = checked
        self.update_status()

    @pyqtSlot()
    def on_sectionListWidget_itemSelectionChanged(self):
            self.section1Selector.clear()
            self.section2Selector.clear()
            self.section3Selector.clear()
            self.endNodeEdit.clear()
            self.pipeDiaEdit.clear()
            self.pipeMaterialEdit.clear()
            self.pipeWidthEdit.clear()
            self.profileEdit.clear()
            self.sectionlengthEdit.clear()
            self.sectionUseEdit.clear()
            self.startNodeEdit.clear()

            self.section_id = None
            #self.inspectionWidget.clear()

            if self.projectId is None:
                return

            items = self.sectionListWidget.selectedItems()
            if len(items) < 1:
                return

            self.section_id = items[0].data(Qt.UserRole)

            # allow use of previous section if not on first section
            self.usePreviousSectionCheckBox.setEnabled(self.section_id !=  self.data[self.projectId]['Sections'].keys()[0])

            section = self.data[self.projectId]['Sections'][self.section_id]

            for i, selector in enumerate((self.section1Selector, self.section2Selector, self.section3Selector)):
                feature = sectionAtId(section['QgepChannelId{}'.format(i+1)])
                if feature.isValid():
                    selector.setFeature(feature)

            self.section1Selector.highlightFeature(CanvasExtent.Pan)

            self.usePreviousSectionCheckBox.setChecked(section['UsePreviousSection'])
            self.endNodeEdit.setText(section['EndNode'])
            self.pipeDiaEdit.setText('{}'.format(section['PipeDia']))
            self.pipeMaterialEdit.setText(section['PipeMaterial'])
            self.pipeWidthEdit.setText('{}'.format(section['PipeWidth']))
            self.profileEdit.setText(section['Profile'])
            self.sectionlengthEdit.setText('{}'.format(section['Sectionlength']))
            self.sectionUseEdit.setText(section['SectionUse'])
            self.startNodeEdit.setText(section['StartNode'])

            self.inspectionWidget.set_section(self.projectId, self.section_id)

    @pyqtSlot()
    def on_checkAllButton_clicked(self):
        for r in range(0, self.sectionListWidget.count()):
            self.sectionListWidget.item(r).setCheckState(Qt.Checked)

    @pyqtSlot()
    def on_uncheckAllButton_clicked(self):
        for r in range(0, self.sectionListWidget.count()):
            self.sectionListWidget.item(r).setCheckState(Qt.Unchecked)


"""
    @pyqtSlot()
    def on_previousButton_clicked(self):
        idx = self.sectionCombo.currentIndex()
        if idx > 0:
            self.sectionCombo.setCurrentIndex(idx-1)

    @pyqtSlot()
    def on_nextButton_clicked(self):
        idx = self.sectionCombo.currentIndex()
        if idx < self.sectionCombo.count()-1:
            self.sectionCombo.setCurrentIndex(idx+1)
"""