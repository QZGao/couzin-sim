import os
from typing import Union

import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QMainWindow, QDesktopWidget
from qfluentwidgets import CheckBox, PushButton, FluentIcon, InfoBarPosition, InfoBar, SettingCardGroup, \
    SwitchSettingCard, OptionsSettingCard, ExpandLayout, ScrollArea, SettingCard, LineEdit
from qfluentwidgets.common.config import qconfig
from qfluentwidgets.common.icon import FluentIconBase
from qframelesswindow.utils import win32_utils as win_utils
from qframelesswindow.windows.window_effect import WindowsWindowEffect

from canvas import MplCanvas
from config import Config


class MainWindow(QMainWindow):

    def __init__(self, cfg: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cfg = cfg

        # Setting dialog
        dlg = settingDialog(self)
        dlg.exec_()

        self.createWindow()

        self.setWindowTitle('Collective Motion Simulation')
        self.resize(1000, 1000)

        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

    def createWindow(self):
        # CheckBoxes
        self.hBoxLayout = QHBoxLayout(self)

        self.checkBox1 = CheckBox('Simulation', self)
        self.checkBox1.setChecked(self.cfg.config_plot1_show.value)
        self.checkBox1.stateChanged.connect(self.checkBoxEvent1)

        self.checkBox2 = CheckBox('Group polarization', self)
        self.checkBox2.setChecked(self.cfg.config_plot2_show.value)
        self.checkBox2.stateChanged.connect(self.checkBoxEvent2)

        self.checkBox3 = CheckBox('Correlation function', self)
        self.checkBox3.setChecked(self.cfg.config_plot3_show.value)
        self.checkBox3.stateChanged.connect(self.checkBoxEvent3)

        self.checkBox4 = CheckBox('Average distance', self)
        self.checkBox4.setChecked(self.cfg.config_plot4_show.value)
        self.checkBox4.stateChanged.connect(self.checkBoxEvent4)

        self.pushButtonEvil = PushButton('Evil random kill', self, FluentIcon.DELETE)
        self.pushButtonEvil.clicked.connect(self.pushButtonEvilEvent)

        self.pushButtonReset = PushButton('Reset parameters', self, FluentIcon.SETTING)
        self.pushButtonReset.clicked.connect(self.pushButtonResetEvent)

        self.hBoxLayout.addWidget(self.checkBox1, 1, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.checkBox2, 1, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.checkBox3, 1, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.checkBox4, 1, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pushButtonEvil, 1, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pushButtonReset, 1, Qt.AlignCenter)
        self.hWidget = QWidget(self)
        self.hWidget.setLayout(self.hBoxLayout)

        # Matplotlib canvas
        self.mplCanvas = MplCanvas(self)
        self.mplCanvas.ax1.set_visible(self.cfg.config_plot1_show.value)
        self.mplCanvas.ax2.set_visible(self.cfg.config_plot2_show.value)
        self.mplCanvas.ax3.set_visible(self.cfg.config_plot3_show.value)
        self.mplCanvas.ax4.set_visible(self.cfg.config_plot4_show.value)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.hWidget, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.mplCanvas, 1, Qt.AlignCenter)
        self.widget = QWidget(self)
        self.widget.setLayout(self.vBoxLayout)
        self.setCentralWidget(self.widget)

        # Output
        if bool(self.cfg.config_output.value):
            if not os.path.exists('output'):
                os.makedirs('output')

            with open("output/event.txt", "a", encoding='utf-8') as f:
                f.write('New event\n')

            with open("output/plot1.txt", "w", encoding='utf-8') as f:
                f.write('Current event\n')

            with open("output/plot2.txt", "w", encoding='utf-8') as f:
                f.write('Current event\n')

            with open("output/plot3.txt", "w", encoding='utf-8') as f:
                f.write('Current event\n')

            with open("output/plot4.txt", "w", encoding='utf-8') as f:
                f.write('Current event\n')

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateCanvas)
        self.time = 0
        self.overall_framerate = int(self.cfg.config_framerate.value)
        self.timer.start(self.overall_framerate)

        InfoBar.warning(
            title='Initializing...',
            content='Please wait for a moment...',
            orient=Qt.Horizontal,
            isClosable=True,  # disable close button
            position=InfoBarPosition.TOP_LEFT,
            duration=2000,
            parent=self
        )

    def checkBoxEvent1(self, state):
        if state == Qt.Checked:
            self.mplCanvas.changePlotStatus(1, True)
            self.cfg.config_plot1_show.value = True
        else:
            self.mplCanvas.changePlotStatus(1, False)
            self.cfg.config_plot1_show.value = False

    def checkBoxEvent2(self, state):
        if state == Qt.Checked:
            self.mplCanvas.changePlotStatus(2, True)
            self.cfg.config_plot2_show.value = True
        else:
            self.mplCanvas.changePlotStatus(2, False)
            self.cfg.config_plot2_show.value = False

    def checkBoxEvent3(self, state):
        if state == Qt.Checked:
            self.mplCanvas.changePlotStatus(3, True)
            self.cfg.config_plot3_show.value = True
        else:
            self.mplCanvas.changePlotStatus(3, False)
            self.cfg.config_plot3_show.value = False

    def checkBoxEvent4(self, state):
        if state == Qt.Checked:
            self.mplCanvas.changePlotStatus(4, True)
            self.cfg.config_plot4_show.value = True
        else:
            self.mplCanvas.changePlotStatus(4, False)
            self.cfg.config_plot4_show.value = False

    def pushButtonEvilEvent(self):
        uneaten = np.where(~self.mplCanvas.simulation.preys_eaten)[0]
        killNum = max(1, len(uneaten) // 4)
        randomKill = np.random.choice(uneaten, size=killNum, replace=False)

        old_preys_num = self.mplCanvas.simulation.current_num_preys()
        self.mplCanvas.simulation.preys_eaten[randomKill] = True
        new_preys_num = self.mplCanvas.simulation.current_num_preys()

        word_choice = f'{self.mplCanvas.simulation.num_preys - old_preys_num + 1} - {self.mplCanvas.simulation.num_preys - new_preys_num} were'
        if len(randomKill) < 2:
            word_choice = f'{self.mplCanvas.simulation.num_preys - new_preys_num} was'

        InfoBar.warning(
            title='Evil random kill',
            content=f"At step {self.time}, prey No. {word_choice} randomly killed.",
            orient=Qt.Horizontal,
            isClosable=True,  # disable close button
            position=InfoBarPosition.TOP_LEFT,
            duration=2000,
            parent=self
        )

        # Write event to output
        if bool(self.cfg.config_output.value):
            with open('output/event.txt', 'a', encoding='utf-8') as f:
                f.write(f'Evil: Time = {self.time}, Remain = {new_preys_num}\n')

        if self.mplCanvas.simulation.all_preys_eaten():
            InfoBar.success(
                title='All caught',
                content=f"At step {self.time}, all preys were caught.",
                orient=Qt.Horizontal,
                isClosable=True,  # disable close button
                position=InfoBarPosition.TOP_LEFT,
                duration=2000,
                parent=self
            )

            # Write event to output
            if bool(self.cfg.config_output.value):
                with open('output/event.txt', 'a', encoding='utf-8') as f:
                    f.write(f"Caught: Time = {self.time}, Remain = none\n")

            try:
                self.mplCanvas.plot1(self.time,
                                     self.mplCanvas.simulation.predators,
                                     self.mplCanvas.simulation.preys,
                                     self.mplCanvas.simulation.predators_speeds,
                                     self.mplCanvas.simulation.preys_speeds,
                                     self.mplCanvas.canvas_size)
            except:
                pass
            self.timer.stop()

    def pushButtonResetEvent(self):
        self.timer.stop()

        dlg = settingDialog(self)
        dlg.exec_()

        self.createWindow()

    def updateCanvas(self):
        self.time += 1
        result = self.mplCanvas.updateCanvas(self.time)
        if result:
            self.timer.stop()


class BetterRangeSettingCard(SettingCard):
    """ A setting card with a range.

        Parameters:
        * configItem: The config item.
        * icon: The icon of the setting card.
        * title: The title of the setting card.
        * content: The content of the setting card.
    """

    valueChanged = pyqtSignal(str)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.lineEdit = LineEdit(self)
        self.lineEdit.setText(str(configItem.value))
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.lineEdit, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        configItem.valueChanged.connect(self.setValue)
        self.lineEdit.textChanged.connect(self.__onValueChanged)

    def __onValueChanged(self, value: str):
        self.setValue(value)
        self.valueChanged.emit(value)

    def setValue(self, value):
        qconfig.set(self.configItem, value)
        self.lineEdit.setText(str(self.configItem.value))


class SettingInterface(ScrollArea):
    """Setting window."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.scrollWidget.setObjectName("scrollWidget")

        # Setting label
        self.settingLabel = QLabel(self.tr("Parameter setting"), self)
        self.settingLabel.setObjectName("settingLabel")

        # Canvas
        self.canvasGroup = SettingCardGroup(self.tr("Canvas"), self.scrollWidget)
        self.config_canvas_size = BetterRangeSettingCard(
            self.parent.parent.cfg.config_canvas_size,
            FluentIcon.ZOOM,
            self.tr("Canvas size"),
            parent=self.canvasGroup
        )
        self.config_framerate = BetterRangeSettingCard(
            self.parent.parent.cfg.config_framerate,
            FluentIcon.HISTORY,
            self.tr("Step wait time (ms)"),
            self.tr("The update time interval between each step of the simulation"),
            parent=self.canvasGroup
        )
        self.config_num_predatory = BetterRangeSettingCard(
            self.parent.parent.cfg.config_num_predatory,
            FluentIcon.SCROLL,
            self.tr("Number of predators"),
            parent=self.canvasGroup
        )
        self.config_num_prey = BetterRangeSettingCard(
            self.parent.parent.cfg.config_num_prey,
            FluentIcon.SCROLL,
            self.tr("Number of preys"),
            parent=self.canvasGroup
        )
        self.config_k_predatory = BetterRangeSettingCard(
            self.parent.parent.cfg.config_k_predatory,
            FluentIcon.SEND_FILL,
            self.tr("Repulsion parameter of predators"),
            parent=self.canvasGroup
        )
        self.config_k_prey = BetterRangeSettingCard(
            self.parent.parent.cfg.config_k_prey,
            FluentIcon.SEND_FILL,
            self.tr("Repulsion parameter of preys"),
            parent=self.canvasGroup
        )
        self.config_v_predatory = BetterRangeSettingCard(
            self.parent.parent.cfg.config_v_predatory,
            FluentIcon.SEND,
            self.tr("Velocity of predators"),
            parent=self.canvasGroup
        )
        self.config_v_prey = BetterRangeSettingCard(
            self.parent.parent.cfg.config_v_prey,
            FluentIcon.SEND,
            self.tr("Velocity of preys"),
            parent=self.canvasGroup
        )
        self.config_bound = BetterRangeSettingCard(
            self.parent.parent.cfg.config_bound,
            FluentIcon.VIDEO,
            self.tr("Initial generation boundaries (%)"),
            self.tr("The initial generation boundaries of the predators and preys, in percentage of the canvas size"),
            parent=self.canvasGroup
        )
        self.config_max_turning_angle = BetterRangeSettingCard(
            self.parent.parent.cfg.config_max_turning_angle,
            FluentIcon.SYNC,
            self.tr("Max turning angle (°)"),
            self.tr("The maximum turning angle of the predators and preys"),
            parent=self.canvasGroup
        )

        # Plot 1
        self.plot1Group = SettingCardGroup(self.tr("Simulation plot"), self.scrollWidget)
        self.config_plot1_show = SwitchSettingCard(
            FluentIcon.VIEW,
            self.tr("Show/Hide plot"),
            self.tr("Hide this plot to save CPU usage"),
            configItem=self.parent.parent.cfg.config_plot1_show,
            parent=self.plot1Group
        )
        self.config_plot1_framerate = BetterRangeSettingCard(
            self.parent.parent.cfg.config_plot1_framerate,
            FluentIcon.UPDATE,
            self.tr("Update frame interval"),
            self.tr("The number of steps to update the plot once"),
            parent=self.plot1Group
        )
        self.config_plot1_marker = OptionsSettingCard(
            self.parent.parent.cfg.config_plot1_marker,
            FluentIcon.PENCIL_INK,
            self.tr("Markers"),
            self.tr("Choose the marker of the plot"),
            texts=[
                self.tr("Arrows"),
                self.tr("Dots")
            ],
            parent=self.plot1Group
        )
        self.config_plot1_marker_size = BetterRangeSettingCard(
            self.parent.parent.cfg.config_plot1_marker_size,
            FluentIcon.HIGHTLIGHT,
            self.tr("Marker size"),
            parent=self.plot1Group
        )
        self.config_plot1_scroll = SwitchSettingCard(
            FluentIcon.MINIMIZE,
            self.tr("Enable auto-scrolling"),
            self.tr(
                "If enabled, the limits of the plot will be updated automatically to always show in a suitable range."),
            configItem=self.parent.parent.cfg.config_plot1_scroll,
            parent=self.plot1Group
        )

        # Plot 2
        self.plot2Group = SettingCardGroup(self.tr("Group polarization plot"), self.scrollWidget)
        self.config_plot2_show = SwitchSettingCard(
            FluentIcon.VIEW,
            self.tr("Show/Hide plot"),
            self.tr("Hide this plot to save CPU usage"),
            configItem=self.parent.parent.cfg.config_plot2_show,
            parent=self.plot2Group
        )
        self.config_plot2_target = OptionsSettingCard(
            self.parent.parent.cfg.config_plot2_target,
            FluentIcon.CHECKBOX,
            self.tr("Target"),
            self.tr("Choose the target of the plot (choosing preys may take longer time to calculate)"),
            texts=[
                self.tr("Preys"),
                self.tr("Predators")
            ],
            parent=self.plot2Group
        )
        self.config_plot2_framerate = BetterRangeSettingCard(
            self.parent.parent.cfg.config_plot2_framerate,
            FluentIcon.UPDATE,
            self.tr("Update frame interval"),
            self.tr("The number of steps to update the plot once"),
            parent=self.plot2Group
        )

        # Plot 3
        self.plot3Group = SettingCardGroup(self.tr("Correlation function plot"), self.scrollWidget)
        self.config_plot3_show = SwitchSettingCard(
            FluentIcon.VIEW,
            self.tr("Show/Hide plot"),
            self.tr("Hide this plot to save CPU usage"),
            configItem=self.parent.parent.cfg.config_plot3_show,
            parent=self.plot3Group
        )
        self.config_plot3_target = OptionsSettingCard(
            self.parent.parent.cfg.config_plot3_target,
            FluentIcon.CHECKBOX,
            self.tr("Target"),
            self.tr("Choose the target of the plot (choosing preys may take longer time to calculate)"),
            texts=[
                self.tr("Preys"),
                self.tr("Predators")
            ],
            parent=self.plot3Group
        )
        self.config_plot3_framerate = BetterRangeSettingCard(
            self.parent.parent.cfg.config_plot3_framerate,
            FluentIcon.UPDATE,
            self.tr("Update frame interval"),
            self.tr("The number of steps to update the plot once"),
            parent=self.plot3Group
        )
        self.config_plot3_sample = BetterRangeSettingCard(
            self.parent.parent.cfg.config_plot3_sample,
            FluentIcon.SCROLL,
            self.tr("Sample size"),
            parent=self.plot3Group
        )

        def config_plot3_framerate_valueChanged(value):
            if value < self.parent.parent.cfg.config_plot3_sample.value:
                self.config_plot3_sample.setValue(value)

        def config_plot3_sample_valueChanged(value):
            if value > self.parent.parent.cfg.config_plot3_framerate.value:
                self.config_plot3_framerate.setValue(value)

        self.config_plot3_framerate.valueChanged.connect(config_plot3_framerate_valueChanged)
        self.config_plot3_sample.valueChanged.connect(config_plot3_sample_valueChanged)

        self.config_resolution = BetterRangeSettingCard(
            self.parent.parent.cfg.config_resolution,
            FluentIcon.ZOOM_IN,
            self.tr("Resolution"),
            self.tr("The resolution of the plot"),
            parent=self.plot3Group
        )
        self.config_crop = BetterRangeSettingCard(
            self.parent.parent.cfg.config_crop,
            FluentIcon.CUT,
            self.tr("Crop area"),
            self.tr("The crop area of the plot (must be smaller than 1)"),
            parent=self.plot3Group
        )

        # Plot 4
        self.plot4Group = SettingCardGroup(self.tr("Average distance plot"), self.scrollWidget)
        self.config_plot4_show = SwitchSettingCard(
            FluentIcon.VIEW,
            self.tr("Show/Hide plot"),
            self.tr("Hide this plot to save CPU usage"),
            configItem=self.parent.parent.cfg.config_plot4_show,
            parent=self.plot4Group
        )
        self.config_plot4_target = OptionsSettingCard(
            self.parent.parent.cfg.config_plot4_target,
            FluentIcon.CHECKBOX,
            self.tr("Target"),
            self.tr("Choose the target of the plot (choosing preys may take longer time to calculate)"),
            texts=[
                self.tr("Preys"),
                self.tr("Predators")
            ],
            parent=self.plot4Group
        )
        self.config_plot4_framerate = BetterRangeSettingCard(
            self.parent.parent.cfg.config_plot4_framerate,
            FluentIcon.UPDATE,
            self.tr("Update frame interval"),
            self.tr("The number of steps to update the plot once"),
            parent=self.plot4Group
        )

        # Experimental
        self.experimentalGroup = SettingCardGroup(self.tr("Experimental"), self.scrollWidget)
        self.config_dpi_scale = OptionsSettingCard(
            self.parent.parent.cfg.config_dpi_scale,
            FluentIcon.MINIMIZE,
            self.tr("DPI scaling settings"),
            self.tr('If you encounter overlapping UI elements, try to modify this option.'),
            texts=[
                self.tr("Use system settings"),
                self.tr("1x"),
                self.tr("1.25x"),
                self.tr("1.5x"),
                self.tr("1.75x"),
                self.tr("2x")
            ],
            parent=self.experimentalGroup
        )
        self.config_output = SwitchSettingCard(
            FluentIcon.SAVE,
            self.tr("Output data"),
            self.tr("Output data to a file (inside the output folder)"),
            configItem=self.parent.parent.cfg.config_output,
            parent=self.experimentalGroup
        )

        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.settingLabel.move(60, 63)

        # add cards to group
        self.canvasGroup.addSettingCard(self.config_canvas_size)
        self.canvasGroup.addSettingCard(self.config_framerate)
        self.canvasGroup.addSettingCard(self.config_num_predatory)
        self.canvasGroup.addSettingCard(self.config_num_prey)
        self.canvasGroup.addSettingCard(self.config_k_predatory)
        self.canvasGroup.addSettingCard(self.config_k_prey)
        self.canvasGroup.addSettingCard(self.config_v_predatory)
        self.canvasGroup.addSettingCard(self.config_v_prey)
        self.canvasGroup.addSettingCard(self.config_bound)
        self.canvasGroup.addSettingCard(self.config_max_turning_angle)

        self.plot1Group.addSettingCard(self.config_plot1_show)
        self.plot1Group.addSettingCard(self.config_plot1_framerate)
        self.plot1Group.addSettingCard(self.config_plot1_marker)
        self.plot1Group.addSettingCard(self.config_plot1_marker_size)
        self.plot1Group.addSettingCard(self.config_plot1_scroll)

        self.plot2Group.addSettingCard(self.config_plot2_show)
        self.plot2Group.addSettingCard(self.config_plot2_target)
        self.plot2Group.addSettingCard(self.config_plot2_framerate)

        self.plot3Group.addSettingCard(self.config_plot3_show)
        self.plot3Group.addSettingCard(self.config_plot3_target)
        self.plot3Group.addSettingCard(self.config_plot3_framerate)
        self.plot3Group.addSettingCard(self.config_plot3_sample)
        self.plot3Group.addSettingCard(self.config_resolution)
        self.plot3Group.addSettingCard(self.config_crop)

        self.plot4Group.addSettingCard(self.config_plot4_show)
        self.plot4Group.addSettingCard(self.config_plot4_target)
        self.plot4Group.addSettingCard(self.config_plot4_framerate)

        self.experimentalGroup.addSettingCard(self.config_dpi_scale)
        self.experimentalGroup.addSettingCard(self.config_output)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.canvasGroup)
        self.expandLayout.addWidget(self.plot1Group)
        self.expandLayout.addWidget(self.plot2Group)
        self.expandLayout.addWidget(self.plot3Group)
        self.expandLayout.addWidget(self.plot4Group)
        self.expandLayout.addWidget(self.experimentalGroup)

        self.setStyleSheet("""
            SettingInterface, #scrollWidget {
                background-color: rgba(243, 243, 243, 164);
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QLabel#settingLabel {
                font: 33px 'Microsoft YaHei Light';
                background: transparent;
            }
            QScrollBar {
                background: transparent;
                width: 4px;
                margin-top: 32px;
                margin-bottom: 0;
                padding-right: 2px;
            }
            QScrollBar::sub-line {
                background: transparent;
            }
            QScrollBar::add-line {
                background: transparent;
            }
            QScrollBar::handle {
                background: rgb(122, 122, 122);
                border: 2px solid rgb(128, 128, 128);
                border-radius: 1px;
                min-height: 32px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)


class settingDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        self.setWindowTitle("Settings")
        self.setWindowIcon(FluentIcon.SETTING.icon())

        # Acrylic effect
        self.windowEffect = WindowsWindowEffect(self)
        self.windowEffect.setAcrylicEffect(self.winId(), "F2F2F299")
        if win_utils.isGreaterEqualWin11():
            self.windowEffect.setMicaEffect(self.winId())

        self.layout = QVBoxLayout(self)
        self.settingInterface = SettingInterface(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.settingInterface)

        self.setLayout(self.layout)
        self.resize(1000, 800)
        self.setStyleSheet("settingDialog{background:transparent}")

        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

        # self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Connect signals
        self.parent.cfg.config_dpi_scale.valueChanged.connect(self.__showRestartTooltip)

    def __showRestartTooltip(self):
        """ show restart tooltip
        """
        InfoBar.warning(
            title='Restart required',
            content='Restart the application to apply the changes.',
            orient=Qt.Horizontal,
            isClosable=True,  # disable close button
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
