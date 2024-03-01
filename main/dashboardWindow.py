import sys, os, csv, re, time, socket, multiprocessing
from ui import resource_rc
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph import PlotWidget, LabelItem, plot
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from resources import service, satFileHandling, loginDB, configParameter
from random import *
from operator import itemgetter
from crccheck.crc import Crc16
import numpy as np
import datetime, logging, wmi
import pandas as pd
import json, platform, sqlite3, psutil
from multiprocessing import cpu_count
from pyqtgraph import debug as debug
from os.path import exists
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QWidget,
    QVBoxLayout,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ColoredAxis(pg.AxisItem):
    def __init__(
        self,
        orientation,
        pen=None,
        textPen=None,
        axisPen=None,
        linkView=None,
        parent=None,
        maxTickLength=-5,
        showValues=True,
        text="",
        units="",
        unitPrefix="",
        **args,
    ):
        super().__init__(
            orientation,
            pen=pen,
            textPen=textPen,
            linkView=linkView,
            parent=parent,
            maxTickLength=maxTickLength,
            showValues=showValues,
            text=text,
            units=units,
            unitPrefix=unitPrefix,
            **args,
        )
        self.axisPen = axisPen
        if self.axisPen is None:
            self.axisPen = self.pen()

    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        profiler = debug.Profiler()

        p.setRenderHint(p.RenderHint.Antialiasing, False)
        p.setRenderHint(p.RenderHint.TextAntialiasing, True)

        ## draw long line along axis
        pen, p1, p2 = axisSpec
        # Use axis pen to draw axis line
        p.setPen(self.axisPen)
        p.drawLine(p1, p2)
        # Switch back to normal pen
        p.setPen(pen)
        # p.translate(0.5,0)  ## resolves some damn pixel ambiguity

        ## draw ticks
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)
        profiler("draw ticks")

        # Draw all text
        if self.style["tickFont"] is not None:
            p.setFont(self.style["tickFont"])
        p.setPen(self.textPen())
        bounding = self.boundingRect().toAlignedRect()
        p.setClipRect(bounding)
        for rect, flags, text in textSpecs:
            p.drawText(rect, int(flags), text)

        profiler("draw text")


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        global font
        font = QtGui.QFont()
        font.setPointSize(12)
        self.widget.setFont(font)
        selection = QTextEdit.ExtraSelection()
        color = QColor(Qt.yellow).lighter()
        selection.format.setBackground(color)
        selection.cursor = self.widget.textCursor()
        self.widget.setExtraSelections([selection])
        # print(selection.format.background().color().getRgb())
        # self.widget.setExtraSelections()
        self.widget.setStyleSheet(
            """QPlainTextEdit {background-color: #303;  color: #00FF00; font-family: Courier;}"""
        )

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

    def write(self, m):
        pass


class UI(QMainWindow):
    """
    Description of UI
    Load main window and update all the parameters at rate of 100ms
    Define working of all functions of GUI
    Inheritance:
        QMainWindow
    """

    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui//main_win.ui"),
            self,
        )
        self.i = 0
        self.logCounter = 0
        self.ConnectingCounter = 0
        self.osuErrorFlag = 0
        self.osuErrorCounter = 0
        self.satinfo = []
        self.log = []
        self.timeList = []

        # self.groupBox_13.hide()
        # self.widget_4.hide()
        self.dashboardBtn1.setChecked(True)
        self.stackedWidget.setCurrentIndex(0)
        self.homeBtn.clicked.connect(self.homePos)
        self.safeModeBtn.clicked.connect(self.Safemode)
        self.txMuteBtn1.clicked.connect(self.txMuteCheck)
        self.setManualBtn.clicked.connect(self.manualMode)
        self.changeIPCancelBtn.clicked.connect(self.cancelChangeIp)
        # self.startDemoBtn.clicked.connect(self.startDemo)
        # self.azPlotShowBtn.clicked.connect(lambda: self.azGraphWidget.show())
        self.frame_8.hide()
        self.addEditSatFrame.hide()
        self.addSatBtn.setEnabled(False)
        self.editSatBtn.setEnabled(False)
        self.delSatBtn.setEnabled(False)
        self.btnSetSat.setEnabled(False)
        # self.btnGetSat.setEnabled(False)

        self.manualCmdSetFlag = 0
        self.manualTimeCounter = 0
        self.demoClickedCounter = 0
        self.demoCounter = 0
        self.demoFlag = 0
        self.errorCounter = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        self.monitorGraph()
        self.cpuInfo()
        self.readConfig()
        self.satelliteTable.resizeRowsToContents()
        self.rollCheckBox.setChecked(True)
        self.pitchCheckBox.setChecked(True)
        self.yawCheckBox.setChecked(True)
        self.loadSatBtn.clicked.connect(self.loadSatData)
        self.btnSetSat.clicked.connect(self.setSatellite)
        self.btnGetSat.clicked.connect(self.getSatellite)
        self.delSatBtn.clicked.connect(self.delSatRow)
        self.getWizInfoBtn.clicked.connect(self.getWizInfo)
        self.changePassOKbtn.clicked.connect(self.changePassword)
        self.changePassCancelBtn.clicked.connect(self.cancelChangePass)
        self.startPlotBtn.clicked.connect(self.check_checkbox_state)
        self.clearPlotBtn.clicked.connect(self.clearGraph)
        self.restartSlscBtn1.clicked.connect(self.restartSlsc)
        self.shutdownSlscBtn1.clicked.connect(self.shutDownSlsc)
        self.satelliteTable.cellClicked.connect(self.getClickedCell)
        self.addSatBtn_2.clicked.connect(self.addSatRow)
        self.editSatBtn.clicked.connect(self.openEdit)
        self.editSatBtn_2.clicked.connect(self.editSatRow)
        # self.pdfBtn.clicked.connect(self.load_pdf)
        self.showPasscheckBox.stateChanged.connect(self.showChangePasscheckbox)
        # self.cancelAddSatBtn.clicked.connect(self.cancelAddEdit)
        self.calendarWidget.selectionChanged.connect(self.grab_date)
        self.submit_button.clicked.connect(self.show_result_time)
        # Set the selected date to today
        today = QDate.currentDate()
        self.calendarWidget.setSelectedDate(today)
        # Call grab_date to update the label with today's date
        self.grab_date()
        self.embed_3d_plot()
        self.embed_2d_plot()

        double_validator = QDoubleValidator()
        int_validator = QIntValidator()

        # Apply validators to respective input fields
        validators = [
            (self.satBfAdd, double_validator),
            (self.satLatAdd, double_validator),
            (self.satLonAdd, double_validator),
            (self.satPolAdd, double_validator),
            (self.satTwoLineAdd, double_validator),

            (self.sysTempMax, double_validator),
            (self.sysTempMin, double_validator),
            (self.rollMin, double_validator),
            (self.rollMax, double_validator),
            (self.pitchMin, double_validator),
            (self.pitchMax, double_validator),
            (self.yawMin, double_validator),
            (self.yawMax, double_validator),
            (self.beaconMin, double_validator),
            (self.beaconMax, double_validator),
            (self.tarAzMin, double_validator),
            (self.tarAzMax, double_validator),
            (self.tarElMin, double_validator),
            (self.tarElMax, double_validator),
            (self.tarPolMin, double_validator),
            (self.tarPolMax, double_validator),
            (self.currElMin, double_validator),
            (self.currElMax, double_validator),
            (self.currxElMin, double_validator),
            (self.currxElMax, double_validator),
            (self.currAzMin, double_validator),
            (self.currAzMax, double_validator),
            (self.currPolMin, double_validator),
            (self.currPolMin, double_validator),
            (self.mCurrElMin, double_validator),
            (self.mCurrElMax, double_validator),
            (self.mCurrXElMin, double_validator),
            (self.mCurrXElMax, double_validator),
            (self.mCurrAzMin, double_validator),
            (self.mCurrAzMax, double_validator),
            (self.mCurrPolMin, double_validator),
            (self.mCurrPolMax, double_validator),
            (self.bucCurrMin, double_validator),
            (self.bucCurrMax, double_validator),
            (self.ofcCurrMin, double_validator),
            (self.ofcCurrMax, double_validator),
            (self.slscCurrMin, double_validator),
            (self.slscCurrMax, double_validator),
            (self.totalCurrMin, double_validator),
            (self.totalCurrMax, double_validator),
            (self.ipSlsc1, int_validator),
            (self.ipSlsc2, int_validator),
            (self.ipSlsc3, int_validator),
            (self.ipSlsc4, int_validator),
            (self.connectingPort, int_validator),
        ]
        self.radBtnAz1.setChecked(True)
        self.radBtnEl1.setChecked(True)
        self.radBtnXel1.setChecked(True)
        self.radBtnPol1.setChecked(True)
        self.radBtnAz1.clicked.connect(lambda: self.selcAzDir.setText("(1)"))
        self.radBtnAz0.clicked.connect(lambda: self.selcAzDir.setText("(0)"))
        self.radBtnEl1.clicked.connect(lambda: self.selcElDir.setText("(1)"))
        self.radBtnEl0.clicked.connect(lambda: self.selcElDir.setText("(0)"))
        self.radBtnXel1.clicked.connect(lambda: self.selcXelDir.setText("(1)"))
        self.radBtnXel0.clicked.connect(lambda: self.selcXelDir.setText("(0)"))
        self.radBtnPol1.clicked.connect(lambda: self.selcPolDir.setText("(1)"))
        self.radBtnPol0.clicked.connect(lambda: self.selcPolDir.setText("(0)"))
        self.azSpinBox.valueChanged.connect(self.on_value_changed)
        self.elSpinBox.valueChanged.connect(self.on_value_changed)
        self.xelSpinBox.valueChanged.connect(self.on_value_changed)
        self.polSpinBox.valueChanged.connect(self.on_value_changed)
        # self.azCheckBox.setChecked(True)
        # self.elCheckBox.setChecked(True)
        # self.xelCheckBox.setChecked(True)
        # self.polCheckBox.setChecked(True)
        # Applying validators to input fields
        for field, validator in validators:
            field.setValidator(validator)
        self.current_row = 0  # Initialize the current_row to 0
        # self.changeIPOkBtn.clicked.connect(self.changeSlscIP)
        self.logTextBox = QTextEditLogger(self)
        self.verticalLayout_66.addWidget(self.logTextBox.widget)
        if not os.path.exists("OEM LOGS"):
            os.makedirs("OEM LOGS")
        log_file = os.path.join( "OEM LOGS", "OEM{}.log".format( datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")  ),)

        logging.basicConfig( filename=log_file,  format="%(asctime)s %(levelname)s %(message)s", filemode="a", )
        self.logTextBox.setFormatter( logging.Formatter("%(asctime)s - %(levelname)s - %(message)s") )
        logging.getLogger().addHandler(self.logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.DEBUG)
        self.showMaximized()
        self.wait_timer = QTimer(self)
        self.wait_timer.timeout.connect(self.restoreOriginalCursor)
        self.plotWidget_3.enableBarGraph = False
        self.plotWidget_3.minValue = 0  # set min value
        self.plotWidget_3.maxValue = 360  # set max value
        self.plotWidget_3.scalaCount = 10  # set scale
        self.plotWidget_3.updateValue(self.plotWidget_3.minValue)
        self.plotWidget_3.setGaugeTheme(1)
        self.plotWidget_3.setBigScaleColor("red")
        self.plotWidget_3.setNeedleColor(153, 255, 255, 180)
        self.plotWidget_3.setScaleValueColor(0, 0, 0, 255)
        self.plotWidget_3.setDisplayValueColor(0, 0, 0, 255)
        self.plotWidget_3.setMouseTracking(False)  # remove mouse
        self.show ()


    def on_value_changed(self):
        non_zero_values = []

        if self.azSpinBox.value() != 0:
            non_zero_values.append(f"az Angle: {round(self.azSpinBox.value(),2)}°")
        if self.elSpinBox.value() != 0:
            non_zero_values.append(f"el Angle: {round(self.elSpinBox.value(),2)}°")
        if self.xelSpinBox.value() != 0:
            non_zero_values.append(f"xel Angle: {round(self.xelSpinBox.value(),2)}°")
        if self.polSpinBox.value() != 0:
            non_zero_values.append(f"pol Angle: {round(self.polSpinBox.value(),2)}°")

        if non_zero_values:
            self.manulSetAngDir.setText(', '.join(non_zero_values))
        else:
            self.manulSetAngDir.clear()

    def showChangePasscheckbox(self, state):
        if state == 2:  
            self.newPassInput.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.prevPassInput.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.confirmPassInput.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.newPassInput.setEchoMode(QtWidgets.QLineEdit.Password)
            self.prevPassInput.setEchoMode(QtWidgets.QLineEdit.Password)
            self.confirmPassInput.setEchoMode(QtWidgets.QLineEdit.Password)

    # def load_pdf(self, file_path):
    #     doc = fitz.open(
    #         os.path.join(
    #             os.path.dirname(os.path.abspath(__file__)), "mccuUserManual_v2.pdf"
    #         )
    #     )

    #     # Assuming you want to display all pages
    #     for page_number in range(len(doc)):
    #         page = doc[page_number]
    #         print(page_number)
    #         pix = page.get_pixmap()
    #         image = QImage(
    #             pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888
    #         )

    #         # Assuming you have labels named label_0, label_1, label_2, ... in your class
    #         label_name = f"labelPdf_{page_number}"
    #         label = getattr(self, label_name)

    #         label.setPixmap(QPixmap.fromImage(image))
    #     doc.close()

    def embed_3d_plot(self):
        # Create a Matplotlib figure and axes
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)

        # Find the plotWidget_1 widget in the loaded UI
        plot_widget = self.findChild(QWidget, "plotWidget_2")
        layout = QVBoxLayout(plot_widget)
        layout.addWidget(self.canvas)

        # Create a 3D plot
        ax = self.fig.add_subplot(111, projection="3d")

        # Plot a simple 3D surface for demonstration
        x = np.linspace(-5, 5, 100)
        y = np.linspace(-5, 5, 100)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))

        ax.plot_surface(X, Y, Z, cmap="viridis")

    def embed_2d_plot(self):
        # Create a Matplotlib figure and axes
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)

        # Find the plotWidget_1 widget in the loaded UI
        plot_widget = self.findChild(QWidget, "plotWidget_1")
        layout = QVBoxLayout(plot_widget)
        layout.addWidget(self.canvas)

        ax = self.fig.add_subplot( 111, polar=True, )

        # Plot a dot at 60 degrees
        angle = 100
        theta = np.radians(angle)
        theta_left = np.radians(angle + 3)
        theta_right = np.radians(angle - 3)
        r = np.sin(theta)
        ax.plot(theta, r, "ro", label="Point at 60 degrees")
        ax.plot(theta_right, r, "rD")
        ax.plot(theta_left, r, "rD")

        # Draw a line from the center to 60 degrees
        ax.plot([0, theta], [0, r], "r--")
        # Add label next to the dot
        ax.text(theta, r, "60 degrees", verticalalignment="bottom")
        # Remove x and y axis ticks

        # ax.set_xticks([])
        ax.set_yticks([])
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        # Set clip_on to False for both radial and angular gridlines
        ax.xaxis.grid(True, linestyle="dashed", alpha=0.5, clip_on=False)
        ax.yaxis.grid(True, linestyle="dashed", alpha=0.5, clip_on=False)
        ax.legend()
        # # Customize x-axis ticks
        # ax.set_xticks(np.radians([0, 45, 90, 135, 180]))

        plt.show()

    def demoParmeters( self, azAngle, azDir, elAngle, elDir, xelAngle, xelDir, polAngle, polDir ):
        # print(azAngle, azDir,elAngle,elDir, xelAngle,xelDir,polAngle, polDir)
        angles = [polAngle * 100, elAngle * 100, xelAngle * 100, azAngle * 100]
        # print(angles)
        demoParameters = b""
        for i in angles:
            angleInBytes = i.to_bytes(2, byteorder="big")
            # print('BYTES LITTLE : ',angleInBytes)
            demoParameters += angleInBytes
        demoParameters = ( demoParameters + bytes([polDir]) + bytes([elDir]) + bytes([xelDir]) + bytes([azDir]) )
        # print(demoParameters, len(demoParameters))
        return demoParameters

    def startDemo(self):
        self.demoClickedCounter += 1
        print("demo clicked : ", self.demoClickedCounter)
        self.startDemoBtn.setEnabled(False)
        startDemoStatus = service.setDemoMode()
        if startDemoStatus == 1:
            logging.info("demo start")
            self.systemMsg.setText("demo start")
        else:
            self.systemMsg.setText("demo start")

    def getWizInfo(self):
        while True:
            command_instance = service.commands()
            wizParamList = command_instance.wizGetInfo()
            # print(wizParamList)
            try:
                wiz = wizParamList[0]
                wiz = wiz.split(":")
                if len(wizParamList) != 0:
                    self.macInput1.setText(wiz[0])
                    self.macInput2.setText(wiz[1])
                    self.macInput3.setText(wiz[2])
                    self.macInput4.setText(wiz[3])
                    self.macInput5.setText(wiz[4])
                    self.macInput6.setText(wiz[5])
                    print("break")
                    break
                else:
                    print("again")
                    self.ipConfigErrorMsg.setText("Please fill all input ")
                    break
            except IndexError:
                print("index error")

    def cpuInfo(self):
        core = cpu_count()
        self.mccuCpuCount.setText(str(core))
        cpuper = psutil.cpu_percent()
        self.mccuCpuPer.setText(str(cpuper) + "%")
        cpuMainCore = psutil.cpu_count(logical=False)
        self.mccuCpuMainCore.setText(str(cpuMainCore))

        totalram = 1.0
        totalram = psutil.virtual_memory()[0] * totalram
        totalram = totalram / (1024 * 1024 * 1024)
        self.totalRam.setText(str("{:.4f}".format(totalram) + "GB"))

        availram = 1.0
        availram = psutil.virtual_memory()[1] * availram
        availram = availram / (1024 * 1024 * 1024)
        self.avaRam.setText(str("{:.4f}".format(availram) + "GB"))

        ramused = 1.0
        ramused = psutil.virtual_memory()[3] * ramused
        ramused = ramused / (1024 * 1024 * 1024)
        self.usedRam.setText(str("{:.4f}".format(ramused) + "GB"))
        ramfree = 1.0
        ramfree = psutil.virtual_memory()[4] * ramfree
        ramfree = ramfree / (1024 * 1024 * 1024)
        self.freeRam.setText(str("{:.4f}".format(ramfree) + "GB"))

    def get_default_gateway():
        system = platform.system()

        if system == "Windows":
            import wmi

            wmi_obj = wmi.WMI()
            wmi_network_configs = wmi_obj.Win32_NetworkAdapterConfiguration( IPEnabled=True )
            for config in wmi_network_configs:
                if config.DefaultIPGateway:
                    return config.DefaultIPGateway[0]  # Return the first gateway found

        elif system == "Linux":
            import netifaces

            gateways = []
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                addrs = netifaces.gateways()
                gateway_info = addrs.get("default", [])
                for info in gateway_info:
                    if iface == info[1]:
                        gateways.append(info[0])

            return gateways  # Return all found gateways in Linux

        else:
            return "Unsupported OS"

    def machineInfo(self):
        time = datetime.datetime.now().strftime("%I:%M:%S")
        self.MccuTime.setText(str(time))
        date = datetime.datetime.now().strftime("%Y-%M-%D")
        self.mccuDate.setText(str(date))
        self.mccuMachine.setText(platform.machine())
        self.mccuVer.setText(platform.version())
        self.mccuPlatform.setText(platform.platform())
        self.mccuProcessor.setText(platform.processor())
        self.MccuDNS.setText(UI.get_default_gateway())

    def readConfig(self):
        congigParaFileExists = exists("mccuConfig.json")
        if congigParaFileExists == True:
            with open("mccuConfig.json", "r") as json_file:
                data = json.load(json_file)
            self.flagMaxValue = self.flagMax.setText(str(data["flagCheck"]["maximum"]))
            self.flagMinValue = self.flagMin.setText(str(data["flagCheck"]["minimum"]))
            self.tempMaxValue = self.sysTempMax.setText(str(data["sysTemp"]["maximum"]))
            self.tempMinValue = self.sysTempMin.setText(str(data["sysTemp"]["minimum"]))

            self.rollMaxValue = self.rollMax.setText(str(data["osuRoll"]["maximum"]))
            self.rollMinValue = self.rollMin.setText(str(data["osuRoll"]["minimum"]))
            self.pitchMaxValue = self.pitchMax.setText(str(data["osuPitch"]["maximum"]))
            self.pitchMinValue = self.pitchMin.setText(str(data["osuPitch"]["minimum"]))
            self.yawMaxValue = self.yawMax.setText(str(data["osuYaw"]["maximum"]))
            self.yawMinValue = self.yawMin.setText(str(data["osuYaw"]["minimum"]))

            self.beaconMaxValue = self.beaconMax.setText( str(data["beaconPower"]["maximum"]) )
            self.beaconMinValue = self.beaconMin.setText( str(data["beaconPower"]["minimum"]) )

            self.tarAzMaxValue = self.tarAzMax.setText(str(data["tarAz"]["maximum"]))
            self.tarAzMinValue = self.tarAzMin.setText(str(data["tarAz"]["minimum"]))
            self.tarElMaxValue = self.tarElMax.setText(str(data["tarEl"]["maximum"]))
            self.tarElMinValue = self.tarElMin.setText(str(data["tarEl"]["minimum"]))
            self.tarPolMaxValue = self.tarPolMax.setText(str(data["tarPol"]["maximum"]))
            self.tarPolMinValue = self.tarPolMin.setText(str(data["tarPol"]["minimum"]))

            self.currElMaxValue = self.currElMax.setText(str(data["currEl"]["maximum"]))
            self.currElMinValue = self.currElMin.setText(str(data["currEl"]["minimum"]))
            self.currxElMaxValue = self.currxElMax.setText( str(data["currCl"]["maximum"]))
            self.currxElMinValue = self.currxElMin.setText( str(data["currCl"]["minimum"]))
            self.currAzMaxValue = self.currAzMax.setText(str(data["currAz"]["maximum"]))
            self.currAzMinValue = self.currAzMin.setText(str(data["currAz"]["minimum"]))
            self.currPolMaxValue = self.currPolMax.setText( str(data["currPol"]["maximum"]) )
            self.currPolMinValue = self.currPolMin.setText( str(data["currPol"]["minimum"]) )
            self.mCurrElMaxValue = self.mCurrElMax.setText( str(data["motorElCurr"]["maximum"]) )
            self.mCurrElMinValue = self.mCurrElMin.setText( str(data["motorElCurr"]["minimum"]))
            self.mCurrxElMaxValue = self.mCurrXElMax.setText( str(data["motorClCurr"]["maximum"]))
            self.mCurrxElMinValue = self.mCurrXElMin.setText( str(data["motorClCurr"]["minimum"]))
            self.mCurrAzMaxValue = self.mCurrAzMax.setText( str(data["motorAzCurr"]["maximum"]))
            self.mCurrAzMinValue = self.mCurrAzMin.setText( str(data["motorAzCurr"]["minimum"]))
            self.mCurrPolMaxValue = self.mCurrPolMax.setText(str(data["motorPolCurr"]["maximum"]))
            self.mCurrPolMinValue = self.mCurrPolMin.setText(str(data["motorPolCurr"]["minimum"]))

            self.bucCurrMaxValue = self.bucCurrMax.setText(str(data["bucCurr"]["maximum"]))
            self.bucCurrMinValue = self.bucCurrMin.setText(str(data["bucCurr"]["minimum"]))
            self.ofcCurrMaxValue = self.ofcCurrMax.setText(str(data["opticalFibreCurr"]["maximum"]))
            self.ofcCurrMinValue = self.ofcCurrMin.setText(str(data["opticalFibreCurr"]["minimum"]))
            self.slscCurrMaxValue = self.slscCurrMax.setText(str(data["slscCurr"]["maximum"]))
            self.slscCurrMinValue = self.slscCurrMin.setText(str(data["slscCurr"]["minimum"]))
            self.totalCurrMaxValue = self.totalCurrMax.setText(str(data["totalCurr"]["maximum"]))
            self.totalCurrMinValue = self.totalCurrMin.setText(str(data["totalCurr"]["minimum"]))
        else:
            print("file does not exist")

    def on_saveBtn_toggled(self):
        text, ok = QInputDialog.getText( None, "Security Password", "<b><font size='3'>To add new password , enter security Password.", QLineEdit.Password,)
        if ok and text:
            if text == "123":
                self.frame_8.hide()
                self.settingsTopArea.show()
                logging.info("Configuration parameters changed ")
                tempMinValue = self.sysTempMax.text()
                tempMaxValue = self.sysTempMin.text()
                rollMinValue = self.rollMin.text()
                rollMaxValue = self.rollMax.text()
                pitchMinValue = self.pitchMin.text()
                pitchMaxValue = self.pitchMax.text()
                yawMinValue = self.yawMin.text()
                yawMaxValue = self.yawMax.text()
                beaconMinValue = self.beaconMin.text()
                beaconMaxValue = self.beaconMax.text()
                tarAzMinValue = self.tarAzMin.text()
                tarAzMaxValue = self.tarAzMax.text()
                tarElMinValue = self.tarElMin.text()
                tarElMaxValue = self.tarElMax.text()
                tarPolMinValue = self.tarPolMin.text()
                tarPolMaxValue = self.tarPolMax.text()
                currElMinValue = self.currElMin.text()
                currElMaxValue = self.currElMax.text()
                currxElMinValue = self.currxElMin.text()
                currxElMaxValue = self.currxElMax.text()
                currAzMinValue = self.currAzMin.text()
                currAzMaxValue = self.currAzMax.text()
                currPolMinValue = self.currPolMin.text()
                currPolMaxValue = self.currPolMin.text()
                mCurrElMinValue = self.mCurrElMin.text()
                mCurrElMaxValue = self.mCurrElMax.text()
                mCurrxElMinValue = self.mCurrXElMin.text()
                mCurrxElMaxValue = self.mCurrXElMax.text()
                mCurrAzMinValue = self.mCurrAzMin.text()
                mCurrAzMaxValue = self.mCurrAzMax.text()
                mCurrPolMinValue = self.mCurrPolMin.text()
                mCurrPolMaxValue = self.mCurrPolMax.text()
                bucCurrMinValue = self.bucCurrMin.text()
                bucCurrMaxValue = self.bucCurrMax.text()
                ofcCurrMinValue = self.ofcCurrMin.text()
                ofcCurrMaxValue = self.ofcCurrMax.text()
                slscCurrMinValue = self.slscCurrMin.text()
                slscCurrMaxValue = self.slscCurrMax.text()
                totalCurrMinValue = self.totalCurrMin.text()
                totalCurrMaxValue = self.totalCurrMax.text()
                configParameter.editConfigFile(
                    tempMinValue,
                    tempMaxValue,
                    rollMinValue,
                    rollMaxValue,
                    pitchMinValue,
                    pitchMaxValue,
                    yawMinValue,
                    yawMaxValue,
                    beaconMinValue,
                    beaconMaxValue,
                    tarAzMinValue,
                    tarAzMaxValue,
                    tarElMinValue,
                    tarElMaxValue,
                    tarPolMinValue,
                    tarPolMaxValue,
                    currElMinValue,
                    currElMaxValue,
                    currxElMinValue,
                    currxElMaxValue,
                    currAzMinValue,
                    currAzMaxValue,
                    currPolMinValue,
                    currPolMaxValue,
                    mCurrElMinValue,
                    mCurrElMaxValue,
                    mCurrxElMinValue,
                    mCurrxElMaxValue,
                    mCurrAzMinValue,
                    mCurrAzMaxValue,
                    mCurrPolMinValue,
                    mCurrPolMaxValue,
                    bucCurrMinValue,
                    bucCurrMaxValue,
                    ofcCurrMinValue,
                    ofcCurrMaxValue,
                    slscCurrMinValue,
                    slscCurrMaxValue,
                    totalCurrMinValue,
                    totalCurrMaxValue,
                )
                # print("save new configuration")
            else:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle("Security Password")
                msgBox.setText("Incorrect password .")
                msgBox.setWindowModality(Qt.ApplicationModal)
                reply = msgBox.exec_()

    def on_cancelBtn_toggled(self):
        self.frame_8.hide()
        self.settingsTopArea.show()
        # print("cancel")

    def changePassword(self):
        self.currentID = self.currentIdInput.text()
        self.currentPass = self.prevPassInput.text()
        self.newPass = self.newPassInput.text()
        self.confirmPass = self.confirmPassInput.text()
        # print(self.currentID, self.currentPass, self.newPass, self.confirmPass)
        if ( (len(self.currentID) != 0) and (len(self.currentPass) != 0) and (len(self.newPass) != 0) and (len(self.confirmPass) != 0)):
            self.checkLogin = loginDB.check_password(self.currentID, self.currentPass)
            if self.checkLogin == "correct":
                if self.newPass == self.confirmPass:
                    self.resetPass = loginDB.reset_password( self.currentID, self.newPass )
                    if self.resetPass == "Password reset successful":
                        self.changePassErrorMsg.setText(f"Password Changed")
                        logging.info(f"Changed password of User {self.currentID}")

                    else:
                        self.changePassErrorMsg.setText(f"{self.resetPass}")
                else:
                    self.changePassErrorMsg.setText( "new password and confirm password does not match" )
            elif self.checkLogin == "Incorrect password":
                self.changePassErrorMsg.setText("Incorrect Current password")
            else:
                self.changePassErrorMsg.setText("Incorrect Current ID")
        else:
            self.changePassErrorMsg.setText("Please fill all input")
        self.currentIdInput.clear()
        self.prevPassInput.clear()
        self.newPassInput.clear()
        self.confirmPassInput.clear()
        self.changePassErrorMsg.setText(" ")

    def cancelChangePass(self):
        self.currentIdInput.clear()
        self.prevPassInput.clear()
        self.newPassInput.clear()
        self.confirmPassInput.clear()
        self.changePassErrorMsg.setText(" ")

    def beacon_scale_conversion(value, in_min, in_max, out_min, out_max):
        """
        Description of beacon_scale_conversion
        Formula to map recieved beacon value from scale (-60) - (-80 ) to 1-100
        Returns:
            value 
            in_min
            in_max
            out_min
            out_max
        """
        input_value = ((value - out_min) / (out_max - out_min)) * (
            in_max - in_min
        ) + in_min
        return int(input_value)
        # return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def update(self):
        try:
            t1 = time.time()
            self.flag = 0
            self.data = service.getUpdateData()
            self.ConnectingCounter = 0
            # print(len(self.data))
            self.btnSetSat.setEnabled(True)
            self.btnGetSat.setEnabled(True)
            # self.setManualBtn.setEnabled(True)
            # self.startDemoBtn.setEnabled(True)
            if len(self.data) > 0:
                self.i += 1
                self.logCounter += 1

                # print(self.i)
                # logging.info('DATA RECIEVING')
                self.updateLogTable()
                self.machineInfo()
                self.updateGraph()

                self.dashboardStatusCheck()
                self.diagnostics()
                self.modelStatus()
                self.writeLogs()
                # changed_time = (datetime.datetime.utcfromtimestamp(int(self.data[19]*100)).strftime('%Y-%m-%d %H:%M:%S')).split(" ")
                # Assuming `self.data[19]` contains a timestamp in seconds
                timestamp = int(self.data[19] * 100)
                # original_datetime = datetime.datetime.utcfromtimestamp(timestamp)
                modified_datetime = datetime.datetime.utcfromtimestamp( timestamp) + datetime.timedelta(hours=5, minutes=30)
                formatted_datetime = modified_datetime.strftime("%d-%m-%Y %H:%M:%S")
                date_, time_ = formatted_datetime.split(" ")
                # print(date_, time_)
                self.satName.setText(f"{self.data[0]}")
                self.date.setText(f"{date_}")
                # print(date_, time_, self.data[20], self.data[21])
                self.time.setText(f"{time_}")
                self.temp.setText(f"{self.data[13]}°")
                self.roll.setText(f"{self.data[14]}°")
                self.pitch.setText(f"{self.data[15]}°")
                self.yaw.setText(f"{self.data[16]}°")
                self.roll_2.setText(f"{self.data[37]}°")
                self.pitch_2.setText(f"{self.data[38]}°")
                self.yaw_2.setText(f"{self.data[39]}°")
                self.beaconFreq.setText(f"{self.data[18]}")
                # self.time.setText(f"{changed_time[1]}")
                # self.date.setText(f"{changed_time[0]}")
                self.latitude.setText(f"{self.data[20]}°")
                self.longitude.setText(f"{self.data[21]}°")
                self.azTar.setText(f"{self.data[22]}°")
                self.elTar.setText(f"{self.data[23]}°")
                self.polTar.setText(f"{self.data[24]}°")

                self.elCurrPos.setText(f"{self.data[25]}°")
                self.xelAngle = self.data[26]
                # print('orignal xel:',xelAngle)
                if self.xelAngle >= 240 and self.xelAngle <= 360:
                    self.xelAngle = -(360 - self.xelAngle)
                # print('scaled xel: ',xelAngle/3)
                self.crElCurrPos.setText(f"{round((self.xelAngle/3), 2)}°")
                self.azCurrPos.setText(f"{self.data[27]}°")

                self.polAngle = self.data[28]
                if self.polAngle >= 180 and self.polAngle <= 360:
                    self.polAngle = -(360 - self.polAngle)
                self.polCurrPos.setText(f"{round((self.polAngle/2.88), 2)}°")
                self.elCurrPos_2.setText(f"{self.data[25]}°")
                self.crElCurrPos_2.setText(f"{round((self.xelAngle/3), 2)}°")
                self.azCurrPos_2.setText(f"{self.data[27]}°")
                self.polCurrPos_2.setText(f"{round((self.polAngle/2.88), 2)}°")

                self.elMotor.setText(f"{self.data[29]}A")
                self.clMotor.setText(f"{self.data[30]}A")
                self.azMotor.setText(f"{self.data[31]}A")
                self.polMotor.setText(f"{self.data[32]}A")

                self.bucCurr.setText(f"{self.data[33]}A")
                self.opticalCurr.setText(f"{self.data[34]}A")
                self.slscCurr.setText(f"{self.data[35]}A")
                self.current.setText(f"{self.data[36]}A")

                if self.manualCmdSetFlag == 1:
                    if self.max_time != 0:
                        # if self.max_time == azTime:
                        self.manualTimeCounter += 1
                        # print(self.manualTimeCounter)

                        self.setManualBtn.setCursor(Qt.ForbiddenCursor)
                        self.setCursor(Qt.ForbiddenCursor)
                        if self.manualTimeCounter == self.TimeCount:
                            # print('rotation completed ')
                            self.setManualBtn.setEnabled(True)
                            self.manualCmdSetFlag = 0
                            self.manualTimeCounter = 0
                            self.setManualBtn.setCursor(Qt.ArrowCursor)
                            self.setCursor(Qt.ArrowCursor)
                            # print(self.manualTimeCounter)
                            self.azSpinBox.setValue(0)
                            self.elSpinBox.setValue(0)
                            self.xelSpinBox.setValue(0)
                            self.polSpinBox.setValue(0) 
                            self.manulSetAngDir.setText(" ")
                    else:
                        self.setManualBtn.setEnabled(True)
                        

                # if self.data[37] == 1:
                #     self.demoFlag = 1
                #     # print(self.demoFlag)
                #     self.demoCounter = 0
                #     self.systemMsg.setText("Demo in running .........................")
                # else:
                #     self.startDemoBtn.setEnabled(True)
                #     self.demoFlag = 0
                #     self.demoCounter += 1
                #     # print(self.demoCounter)
                #     if self.demoCounter >= 5:
                #         self.systemMsg.setText("")
                #     else:
                #         self.systemMsg.setText("DEMO ENDED")

                converted_value = UI.beacon_scale_conversion(
                    float(self.data[17]), 0, 100, -80, -60
                )
                # print(self.data[17],converted_value)
                self.progressBar.setValue(converted_value)
                self.flag = 1
                self.plotWidget_3.updateValue(int(self.data[16]))
                # print(self.data[27])

            else:
                self.systemMsg.setText("Incomplete Data ")
            # print(time.time()-t1)
        except:
            self.ConnectingCounter += 1
            # print(self.ConnectingCounter)
            if self.ConnectingCounter % 5 == 0:
                # print(self.ConnectingCounter)
                self.systemMsg.setText("Connecting ............")
                self.ConnectingCounter = 0
                self.btnSetSat.setEnabled(False)
                self.btnGetSat.setEnabled(False)
                # self.setManualBtn.setEnabled(False)
                # self.startDemoBtn.setEnabled(False)

    def errorStateAdd(self):
        if self.osuErrorFlag == 1:
            self.group_box = QGroupBox("Actions")

            self.group_layout = QVBoxLayout()
            self.group_box.setLayout(self.group_layout)
            self.label = QLabel("OSU IS IN ERROR")

            self.btn_acknowledged = QPushButton("Acknowledged")
            self.btn_rectified = QPushButton("Rectified")
            self.btn_acknowledged.setStyleSheet( "height: 20px; font: bold; font-size:15px; background-color: rgb(0, 35, 52);" )
            self.btn_rectified.setStyleSheet("height: 20px; font: bold; font-size:15px; background-color: rgb(0, 35, 52);" )

            self.btn_acknowledged.setObjectName("btn_acknowledged")
            self.btn_rectified.setObjectName("btn_rectified")

            self.group_layout.addWidget(self.btn_acknowledged)
            self.group_layout.addWidget(self.btn_rectified)

            # # Add buttons to the existing groupBox_13
            # self.groupBox_13_layout = self.groupBox_13.layout()
            # self.groupBox_13_layout.addWidget(self.label)
            # self.groupBox_13_layout.addWidget(self.btn_acknowledged)
            # self.groupBox_13_layout.addWidget(self.btn_rectified)
            # self.btn_acknowledged.clicked.connect(self.acknowledged)
            # print('OSU')

    def acknowledged(self):
        print("5")

    def updateLogTable(self):
        now = datetime.datetime.now()

        current_time = now.strftime("%H:%M:%S")
        # print("Current Time =", current_time)
        self.timeList.append(current_time)
        # print(self.timeList)
        self.log.append(tuple(self.data[13:37]))
        # print(self.log)
        self.dataLogTable.setRowCount(len(self.log))
        self.dataLogTable.setColumnCount(24)
        t = ( "Sys Temp", "Roll", "Pitch", "Yaw", "Beacon Power",  "Beacom Freq", "GPS Time",
            "Latitude", "Longitude", "Target AZ", "Target EL", "Target POL", "Current EL",
            "Current xEL", "Current AZ", "Current POL", "Motor EL", "Motor xEL", "Motor AZ",
            "Motor POL", "BUC Current", "OFC Current", "SLSC Current", "TOTAL Current", )
        self.dataLogTable.setHorizontalHeaderLabels(t)
        header = self.dataLogTable.horizontalHeader()
        for i in range(24):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        r = 0
        for j in self.log:
            if r < 20:
                self.dataLogTable.setItem(r, 0, QTableWidgetItem(str(j[0])))
                self.dataLogTable.setItem(r, 1, QTableWidgetItem(str(j[1])))
                self.dataLogTable.setItem(r, 2, QTableWidgetItem(str(j[2])))
                self.dataLogTable.setItem(r, 3, QTableWidgetItem(str(j[3])))
                self.dataLogTable.setItem(r, 4, QTableWidgetItem(str(j[4])))
                self.dataLogTable.setItem(r, 5, QTableWidgetItem(str(j[5])))
                self.dataLogTable.setItem(r, 6, QTableWidgetItem(str(j[6])))
                self.dataLogTable.setItem(r, 7, QTableWidgetItem(str(j[7])))
                self.dataLogTable.setItem(r, 8, QTableWidgetItem(str(j[8])))
                self.dataLogTable.setItem(r, 9, QTableWidgetItem(str(j[9])))
                self.dataLogTable.setItem(r, 10, QTableWidgetItem(str(j[10])))
                self.dataLogTable.setItem(r, 11, QTableWidgetItem(str(j[11])))
                self.dataLogTable.setItem(r, 12, QTableWidgetItem(str(j[12])))
                self.dataLogTable.setItem(r, 13, QTableWidgetItem(str(j[13])))
                self.dataLogTable.setItem(r, 14, QTableWidgetItem(str(j[14])))
                self.dataLogTable.setItem(r, 15, QTableWidgetItem(str(j[15])))
                self.dataLogTable.setItem(r, 16, QTableWidgetItem(str(j[16])))
                self.dataLogTable.setItem(r, 17, QTableWidgetItem(str(j[17])))
                self.dataLogTable.setItem(r, 18, QTableWidgetItem(str(j[18])))
                self.dataLogTable.setItem(r, 19, QTableWidgetItem(str(j[19])))
                self.dataLogTable.setItem(r, 20, QTableWidgetItem(str(j[20])))
                self.dataLogTable.setItem(r, 21, QTableWidgetItem(str(j[21])))
                self.dataLogTable.setItem(r, 22, QTableWidgetItem(str(j[22])))
                self.dataLogTable.setItem(r, 23, QTableWidgetItem(str(j[23])))
                r += 1
            else:
                self.log.clear()
                r = 0

    def setManualParam(self):
       
        azAngle = int(self.azSpinBox.value() * 100)
        elAngle = int(self.elSpinBox.value() * 100)
        xelAngle = int(self.xelSpinBox.value() * 100)
        polAngle = int(self.polSpinBox.value() * 100)
        time_taken_az = UI.motorRampingTimeCalcy( self.azSpinBox.value(), 3.0, 20000 )
        time_taken_el = UI.motorRampingTimeCalcy( self.elSpinBox.value(), 3.0, 20000 )
        time_taken_xel = UI.motorRampingTimeCalcy( self.xelSpinBox.value(), 3.0, 20000 )
        time_taken_pol = UI.motorRampingTimeCalcy( self.polSpinBox.value(), 2.88, 25000 )
        # print(self.azSpinBox.value(), self.elSpinBox.value(), self.xelSpinBox.value(), self.polSpinBox.value())
        # print(int(self.azSpinBox.value() * 100),int(self.elSpinBox.value() * 100), int(self.xelSpinBox.value() * 100), int(self.polSpinBox.value() * 100))
        self.azTimeInput.setText(str(time_taken_az))
        self.elTimeInput.setText(str(time_taken_el))
        self.xelTimeInput.setText(str(time_taken_xel))
        self.polTimeInput.setText(str(time_taken_pol))
        self.timeTaken = [time_taken_az, time_taken_el, time_taken_xel, time_taken_pol]

        if self.radBtnAz1.isChecked():
            azDir = 1
            self.radBtnAz0.setChecked(False) 
        else:
            azDir = 0
            self.radBtnAz1.setChecked(False)
        if self.radBtnEl1.isChecked():
            elDir = 1
            predictedElAngle = round( (float(self.data[25]) + self.elSpinBox.value()), 2 )
            self.radBtnEl0.setChecked(False)
        else:
            predictedElAngle = round( (float(self.data[25]) - self.elSpinBox.value()), 2 )
            elDir = 0
            self.radBtnEl1.setChecked(False)
        if self.radBtnXel1.isChecked():
            xelDir = 1
            predictedXelAngle = round( (self.xelAngle / 3 + self.xelSpinBox.value()), 2 )
            self.radBtnXel0.setChecked(False)
        else:
            predictedXelAngle = round( (self.xelAngle / 3 - self.xelSpinBox.value()), 2 )
            xelDir = 0
            self.radBtnXel1.setChecked(False)
        if self.radBtnPol1.isChecked():
            polDir = 1
            predictedPolAngle = round( (self.polAngle / 2.88 - self.polSpinBox.value()), 2 )
            self.radBtnPol0.setChecked(False)
        else:
            polDir = 0
            predictedPolAngle = round( (self.polAngle / 2.88 + self.polSpinBox.value()), 2 )
            self.radBtnPol1.setChecked(False)
        if (5.0 <= float(self.data[25]) <= 90.0) and (-60.0 <= self.polAngle / 2.88 <= 60.0) and (-30.0 <= self.xelAngle / 3 <= 30.0):
            if ( (5.0 <= predictedElAngle <= 90.0) and (-60.0 <= predictedPolAngle <= 60.0) and (-30.0 <= predictedXelAngle <= 30.0) ) :
                self.manualLog = ( f"azimuth angle:{self.azSpinBox.value()}" + f"°({str(azDir)})" + " / " + f"elevation angle:{self.elSpinBox.value()}" + f"°({str(elDir)})" + " / "
                    + f"cross-elevation angle:{self.xelSpinBox.value()}" + f"°({str(xelDir)})" + " / " f"polarisation angle:{self.polSpinBox.value()}" + f"°({str(polDir)})" )
                print(self.manualLog)
                self.max_time = max( time_taken_az, time_taken_el, time_taken_xel, time_taken_pol )
                if self.max_time != 0:
                    self.TimeCount = int((self.max_time * 1000) / 200 + 1)
                else:
                    self.TimeCount = 0
                if not ( azAngle > 18000 or elAngle > 5000 or xelAngle > 5000 or polAngle > 5000 ):
                    angles = [polAngle, elAngle, xelAngle, azAngle]
                    print(angles)
                    # manualParameters= bytes([azAngle]) + bytes([elAngle]) + bytes([xelAngle]) + bytes([polAngle]) + bytes([azDir])+ bytes([elDir])+ bytes([xelDir])+ bytes([polDir])
                    manualParameters = b""
                    for i in angles:
                        angleInBytes = i.to_bytes(2, byteorder="big")
                        # print('BYTES LITTLE : ',angleInBytes)
                        manualParameters += angleInBytes
                    manualParameters = ( manualParameters + bytes([polDir]) + bytes([elDir]) + bytes([xelDir]) + bytes([azDir]) )
                    self.manualErrMsg.setText(" ")
                else:
                    manualParameters = None
                    # self.setManualBtn.setDisabled(False)
            else:
                manualParameters = None

        else:
            manualParameters=None
        return manualParameters

    def manualMode(self):
        manualParameters = self.setManualParam()
        # print(manualParameters)
        if self.flag == 1:
            if manualParameters != None:
                self.systemMsg.setText("Angles out of range")
                manualStatus = service.setManual(manualParameters)
                if manualStatus == 1:
                    self.setManualBtn.setEnabled(False)
                    # logging.info(self.manualLog)
                    self.systemMsg.setText("Manual mode set")
                    self.manualCmdSetFlag = 1
                else:
                    self.systemMsg.setText("Manual mode not set")

            else:
                self.manualErrMsg.setText("Angles out of range")
                self.azTimeInput.setText(str(0))
                self.elTimeInput.setText(str(0))
                self.xelTimeInput.setText(str(0))
                self.polTimeInput.setText(str(0))

    def grab_date(self):
        self.dateSelected = self.calendarWidget.selectedDate()
        date = str(self.dateSelected.toPyDate())
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        self.formatted_date = date_obj.strftime("%Y%m%d")
        print(self.formatted_date)
        self.label.setText(str(self.dateSelected.toPyDate()))

    def dataLog_setup(self):
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().strftime("%B")
        folder_name = str(current_year) + "-" + str(current_month)
        # print(folder_name)
        return folder_name

    def show_result_time(self):
        selected_hour = self.hour_combobox.currentText()
        am_pm = "AM" if self.am_radio.isChecked() else "PM"
        result_time = f"{selected_hour}{am_pm}"
        self.result_label.setText( f"Selected date and Time: {str(self.dateSelected.toPyDate())} {result_time}" )
        folder_name = self.dataLog_setup()
        file_name = "LOG_" + self.formatted_date + "_" + result_time + ".csv"
        # print(folder_name,file_name)
        # Load and display the CSV data
        # csv_filename = f"{selected_hour}{am_pm}.csv"
        if os.path.exists(os.path.join(folder_name, file_name)):
            self.load_csv_to_table(folder_name, file_name)
        else:
            # print('not exist')
            # self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.result_label.setText("No file found")

    def load_csv_to_table(self, folder_name, csv_filename):
        self.tableWidget.setRowCount(0)  # Clear existing data
        with open(os.path.join(folder_name, csv_filename), "r", newline="") as csvfile:
            csv_reader = csv.reader(csvfile)
            data = list(csv_reader)
            self.tableWidget.setRowCount(len(data))
            self.tableWidget.setColumnCount(len(data[0]))
            for row in range(len(data)):
                for column in range(len(data[row])):
                    self.tableWidget.setItem( row, column, QTableWidgetItem(data[row][column]) )

    def loadSatData(self):
        self.addSatBtn.setEnabled(True)
        self.editSatBtn.setEnabled(True)
        self.delSatBtn.setEnabled(True)
        self.btnSetSat.setEnabled(True)

        # self.satelliteTable.resizeRowsToContents()
        self.satelliteTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.satelliteTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        satTableHeader = self.satelliteTable.horizontalHeader()
        satTableVertical = self.satelliteTable.verticalHeader()
        file_exists = exists("satelliteDB.csv")
        if file_exists == True:
            with open("satelliteDB.csv") as f:
                reader = csv.reader(f)
                self.satinfo = [tuple(row) for row in reader]
                # print(data)
            # print(self.satinfo)
            self.satelliteTable.setRowCount(len(self.satinfo))
            self.satelliteTable.setColumnCount(6)
            global header
            header = ( "Satellite", "Beacon Freq.", "Latitude",
                "Longitude", "Polarization", "Norad Sat info", )
            self.satelliteTable.setHorizontalHeaderLabels(header)
            row_index = 0
            for value_tuple in self.satinfo:
                col_index = 0
                for value in value_tuple:
                    self.satelliteTable.setItem( row_index, col_index, QTableWidgetItem(str(value))  )
                    col_index += 1
                row_index += 1
            # constants.setLockSatellite()
        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setText("FILE DOES NOT EXIST.Please ADD SATELLITE INFO")
            message.setWindowModality(Qt.ApplicationModal)
            message.exec_()
            print("not FILE found .Please ADD SATELLITE INFO")

    def getClickedCell(self, row, column):
        # print('clicked!', row, column)
        current_Row = self.satelliteTable.currentRow()
        # print(current_Row)
        if current_Row >= 0:
            send_sat = []
            for i in range(6):
                item = self.satelliteTable.item(current_Row, i)
                cell_value = item.text()
                send_sat.append(cell_value)
        self.twoLineInput.setText(f"{send_sat[5]}")
        self.last_selected_row = row  # Update the last selected rowv
        return row

    def setSatellite(self):
        if int(self.data[9]) == 1:
            file_exists = exists("satelliteDB.csv")
            if file_exists == True:
                current_Row = self.satelliteTable.currentRow()
                # print(current_Row)

                if current_Row >= 0:
                    send_sat = []
                    for i in range(5):
                        item = self.satelliteTable.item(current_Row, i)
                        cell_value = item.text()
                        send_sat.append(cell_value)
                    print("selctedddddddddddddddd", send_sat)
                    text, ok = QInputDialog.getText( None, "Security Password", f"<b><font size='3'>To set Satellite {send_sat[0]}, enter security Password.", QLineEdit.Password,)
                    if ok and text:
                        if text == "123":
                            if self.flag == 1:
                                service.setLockSatellite(send_sat)
                                self.satCurr.setText(f"set satellite {send_sat[0]}")
                                logging.info( f"set Satellite (satelite name : {send_sat[0]}))" )
                                self.systemMsg.setText( f"set Satellite (satelite name : {send_sat[0]}))" )
                        else:
                            msgBox = QMessageBox(self)
                            msgBox.setIcon(QMessageBox.Information)
                            msgBox.setWindowTitle("Security Password")
                            msgBox.setText("Incorrect password .")
                            msgBox.setWindowModality(Qt.ApplicationModal)
                            reply = msgBox.exec_()

                else:
                    message = QMessageBox()
                    message.setIcon(QMessageBox.Information)
                    message.setText("please select satellite from table")
                    message.setWindowModality(Qt.ApplicationModal)
                    message.exec_()
                    # print("not FILE found .Please ADD SATELLITE INFO")
            else:
                message = QMessageBox()
                message.setIcon(QMessageBox.Information)
                message.setText("FILE DOES NOT EXIST.Please ADD SATELLITE INFO")
                message.setWindowModality(Qt.ApplicationModal)
                message.exec_()
                # print("not FILE found .Please ADD SATELLITE INFO")
            # Deselect the row
        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setWindowTitle('Warning')
            message.setText("Gps is not locked.\n Set Satellite not possible")
            message.setWindowModality(Qt.ApplicationModal)
            message.exec_()  
        self.satelliteTable.setCurrentCell(-1, -1)
        self.last_selected_row = -1  # Reset the last selected row

    def getSatellite(self):
        if self.flag == 1:
            recvResposnse = service.getLockSatellite()
            self.satCurr.setText(f"{recvResposnse}locked")
            # print(recvResposnse)

    def delSatRow(self):
        file_exists = exists("satelliteDB.csv")
        if file_exists:
            if self.satelliteTable.rowCount() > 0:
                currentRow = self.satelliteTable.currentRow()
                if currentRow != -1:
                    self.satelliteTable.removeRow(currentRow)
                    # print(self.satinfo[currentRow], currentRow)
                    del self.satinfo[currentRow]
                    # print(self.satinfo)
                    satFileHandling.delRow(currentRow)
                else:
                    message = QMessageBox()
                    message.setIcon(QMessageBox.Information)
                    message.setWindowTitle("Warning")
                    message.setText("SELECT SATTELITE TO DELETE")
                    message.setWindowModality(Qt.ApplicationModal)
                    message.exec_()

        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setWindowTitle("Warning")
            message.setText("FILE DOES NOT EXIST.\nPlease ADD SATELLITE INFO")
            message.setWindowModality(Qt.ApplicationModal)
            message.exec_()
            print("not FILE found .Please ADD SATELLITE INFO")
        self.satelliteTable.setCurrentCell(-1, -1)
        self.last_selected_row = -1  # Reset the last selected row

    def addSatRow(self):
        self.addSatBtn_2.show()
        file_exists = exists("satelliteDB.csv")
        if file_exists:
            satName = self.satNameAdd.text()
            satBF = self.satBfAdd.text()
            satLat = self.satLatAdd.text()
            satLon = self.satLonAdd.text()
            satPol = self.satPolAdd.text()
            satNomadTwoLine = self.satTwoLineAdd.text()
            # print('adddd', satName, satLat, satBF, satPol)
            addSat = (satName, satBF, satLat, satLon, satPol, satNomadTwoLine)
            if (
                len(satName) == 0
                and len(satBF) == 0
                and len(satLon) == 0
                and len(satLat) == 0
                and len(satPol)
                and len(satNomadTwoLine) == 0
            ):
                self.addSatEr.setText("Please fill all input ")
            else:
                self.satinfo.append(addSat)
                # print(addSat)
                satFileHandling.add_row_to_csv(addSat)
                UI.loadSatData(self)
                # print('DONE')
                self.satNameAdd.clear()
                self.satBfAdd.clear()
                self.satLatAdd.clear()
                self.satLonAdd.clear()
                self.satPolAdd.clear()
                self.satTwoLineAdd.clear()
                self.addEditSatFrame.hide()
        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setWindowTitle("Warning")
            message.setText("FILE DOES NOT EXIST.\nPlease ADD SATELLITE INFO")
            message.setWindowModality(Qt.ApplicationModal)
            message.exec_()
            # print('not FILE found .Please ADD SATELLITE INFO')
        # print('SATELITTE ADDED')
        self.satelliteTable.setCurrentCell(-1, -1)
        self.last_selected_row = -1  # Reset the last selected row

        self.addSatBtn.setEnabled(True)
        self.editSatBtn.setEnabled(True)
        self.delSatBtn.setEnabled(True)

    def openEdit(self):
        self.editSatBtn_2.show()
        file_exists = exists("satelliteDB.csv")
        if file_exists:
            current_Row = self.satelliteTable.currentRow()
            if current_Row >= 0:
                self.addEditSatFrame.show()
                self.addSatBtn_2.hide()
                self.addSatBtn.setEnabled(False)
                self.editSatBtn.setEnabled(False)
                self.delSatBtn.setEnabled(False)
                send_sat = []
                for i in range(6):
                    item = self.satelliteTable.item(current_Row, i)
                    cell_value = item.text()
                    send_sat.append(cell_value)
                self.satNameAdd.setText(send_sat[0])
                self.satBfAdd.setText(send_sat[1])
                self.satLatAdd.setText(send_sat[2])
                self.satLonAdd.setText(send_sat[3])
                self.satPolAdd.setText(send_sat[4])
                self.satTwoLineAdd.setText(send_sat[5])
            else:
                message = QMessageBox()
                message.setIcon(QMessageBox.Information)
                message.setWindowTitle("Warning")
                message.setText("SELECT SATTELITE TO EDIT")
                message.setWindowModality(Qt.ApplicationModal)
                message.exec_()
        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setWindowTitle("Warning")
            message.setText("FILE DOES NOT EXIST.\nPlease ADD SATELLITE INFO")
            message.setWindowModality(Qt.ApplicationModal)
            message.exec_()
            # print('not FILE found ')

    def editSatRow(self):
        current_Row = self.satelliteTable.currentRow()
        editedSatName = self.satNameAdd.text()
        editedBF = self.satBfAdd.text()
        editedLat = self.satLatAdd.text()
        editedLon = self.satLonAdd.text()
        editedPol = self.satPolAdd.text()
        editedNorad = self.satTwoLineAdd.text()
        # print(editedSatName,  editedBF, editedLat, editedLon,editedPol, editedNorad)
        satFileHandling.edit_row_in_csv(
            current_Row,
            [editedSatName, editedBF, editedLat, editedLon, editedPol, editedNorad],
        )
        UI.loadSatData(self)
        self.addEditSatFrame.hide()
        self.satelliteTable.setCurrentCell(-1, -1)
        self.last_selected_row = -1  # Reset the last selected row
        self.satNameAdd.clear()
        self.satBfAdd.clear()
        self.satLatAdd.clear()
        self.satLonAdd.clear()
        self.satPolAdd.clear()
        self.satTwoLineAdd.clear()

    def cancelAddEdit(self):
        self.satNameAdd.clear()
        self.satBfAdd.clear()
        self.satLatAdd.clear()
        self.satLonAdd.clear()
        self.satPolAdd.clear()
        self.satTwoLineAdd.clear()
        self.addEditSatFrame.hide()

    def unix_time_to_hour_and_minute(unix_time):
        # Convert Unix time to a datetime object
        real_time = datetime.datetime.fromtimestamp(unix_time)
        # Extract hour and minute parts
        hour = real_time.hour
        minute = real_time.minute
        return hour, minute

    def encoderGraph(self):
        #__________________________________AZ GRAPH _____________________________________________________
        self.lowerFrameLayout3 = QtWidgets.QHBoxLayout(self.azGraph)
        self.lowerFrameLayout3.setObjectName("horizontalLayout3")
        self.azGraphList = []
        self.azTarGraphList=[]
        
        self.azGraphWidget = pg.PlotWidget( axisItems={"bottom": pg.DateAxisItem(), "left": self.axis_az_en} )
        self.azGraphWidget.addLegend()
        self.azPlot = self.azGraphWidget.plot( self.timeAxis, self.azGraphList, pen=pg.mkPen("g", width=2) )
        self.azTarPlot = self.azGraphWidget.plot( self.timeAxis, self.azTarGraphList, pen=pg.mkPen("r", width=2) )
        self.azGraphWidget.showGrid(x=True, y=True)
        self.azGraphWidget.setBackground("w")
        self.azGraphWidget.setLabel(  "bottom", '<p style="font-size:12px;color:black">Time</p>' )
        self.azGraphWidget.setLabel( "left", '<p style="font-size:15px;color:black">Az encoder(°)</p>' )
        self.azGraphWidget.setTitle( '<p style="font:bold;font-size:10px;color:black">AZIMUTH</p>' )
        self.azGraphWidget.getAxis("bottom").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.azGraphWidget.getAxis("left").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.lowerFrameLayout3.addWidget(self.azGraphWidget)

        #__________________________________EL GRAPH _____________________________________________________
        self.lowerFrameLayout4 = QtWidgets.QHBoxLayout(self.elGraph)
        self.lowerFrameLayout4.setObjectName("horizontalLayout4")
        self.elGraphList = []
        self.elTarGraphList=[]
        self.elGraphWidget = pg.PlotWidget( axisItems={"bottom": pg.DateAxisItem(), "left": self.axis_el_en} )
        self.elPlot = self.elGraphWidget.plot( self.timeAxis, self.elGraphList, pen=pg.mkPen("g", width=2)  )
        self.elTarPlot = self.elGraphWidget.plot( self.timeAxis, self.elTarGraphList, pen=pg.mkPen("r", width=2)  )
        self.elGraphWidget.showGrid(x=True, y=True)
        self.elGraphWidget.setBackground("w")
        self.elGraphWidget.setLabel(  "bottom", '<p style="font-size:12px;color:black">Time</p>' )
        self.elGraphWidget.setLabel( "left", '<p style="font-size:15px;color:black">El encoder(°)</p>' )
        self.elGraphWidget.setTitle( '<p style="font:bold;font-size:10px;color:black">ELEVATION</p>' )
        self.elGraphWidget.getAxis("bottom").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.elGraphWidget.getAxis("left").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.lowerFrameLayout4.addWidget(self.elGraphWidget)

        #__________________________________XEL GRAPH _____________________________________________________
        self.lowerFrameLayout5 = QtWidgets.QHBoxLayout(self.xelGraph)
        self.lowerFrameLayout5.setObjectName("horizontalLayout5")
        self.xelGraphList = []
        self.xelGraphWidget = pg.PlotWidget( axisItems={"bottom": pg.DateAxisItem(), "left": self.axis_xel_en} )
        self.xelPlot = self.xelGraphWidget.plot( self.timeAxis, self.xelGraphList, pen=pg.mkPen("g", width=2)  )
        self.xelGraphWidget.showGrid(x=True, y=True)
        self.xelGraphWidget.setBackground("w")
        self.xelGraphWidget.setLabel(  "bottom", '<p style="font-size:12px;color:black">Time</p>' )
        self.xelGraphWidget.setLabel( "left", '<p style="font-size:15px;color:black">El encoder(°)</p>' )
        self.xelGraphWidget.setTitle( '<p style="font:bold;font-size:10px;color:black">CROSS ELEVATION</p>' )
        self.xelGraphWidget.getAxis("bottom").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.xelGraphWidget.getAxis("left").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.lowerFrameLayout5.addWidget(self.xelGraphWidget)

        #__________________________________pol GRAPH _____________________________________________________
        self.lowerFrameLayout6 = QtWidgets.QHBoxLayout(self.polGraph)
        self.lowerFrameLayout6.setObjectName("horizontalLayout6")
        self.polGraphList = []
        self.polTarGraphList=[]
        self.polGraphWidget = pg.PlotWidget( axisItems={"bottom": pg.DateAxisItem(), "left": self.axis_pol_en} )
        self.polPlot = self.polGraphWidget.plot( self.timeAxis, self.polGraphList, pen=pg.mkPen("g", width=2)  )
        self.polTarPlot = self.polGraphWidget.plot( self.timeAxis, self.polTarGraphList, pen=pg.mkPen("r", width=2)  )
        self.polGraphWidget.showGrid(x=True, y=True)
        self.polGraphWidget.setBackground("w")
        self.polGraphWidget.setLabel(  "bottom", '<p style="font-size:12px;color:black">Time</p>' )
        self.polGraphWidget.setLabel( "left", '<p style="font-size:15px;color:black">El encoder(°)</p>' )
        self.polGraphWidget.setTitle( '<p style="font:bold;font-size:10px;color:black">POLARIZATION</p>' )
        self.polGraphWidget.getAxis("bottom").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.polGraphWidget.getAxis("left").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.lowerFrameLayout6.addWidget(self.polGraphWidget)

    def monitorGraph(self):
        self.upperGraphLayout2 = QtWidgets.QHBoxLayout(self.osuGraph)
        self.upperGraphLayout2.setObjectName("horizontalLayout2")
        
        self.axis_az_en = ColoredAxis( orientation="left", axisPen=pg.mkPen(color="black", width=1) )
        self.axis_el_en = ColoredAxis( orientation="left", axisPen=pg.mkPen(color="black", width=1) )
        self.axis_xel_en = ColoredAxis( orientation="left", axisPen=pg.mkPen(color="black", width=1) )
        self.axis_pol_en = ColoredAxis( orientation="left", axisPen=pg.mkPen(color="black", width=1) )
        self.axis_sat = ColoredAxis( orientation="left", axisPen=pg.mkPen(color="black", width=1) )
        self.timeAxis = []

        self.osuRoll = []
        self.osuPitch = []
        self.osuYaw = []
        self.osuGraphWidget = pg.PlotWidget( axisItems={"bottom": pg.DateAxisItem(), "left": self.axis_sat} )
        self.osuGraphWidget.addLegend()
        self.osuRollPlot = self.osuGraphWidget.plot( self.timeAxis, self.osuRoll, pen=pg.mkPen("violet", width=2), symbol="+", symbolSize=10, symbolBrush="b", name="ROLL", )
        self.osuPitchPlot = self.osuGraphWidget.plot( self.timeAxis, self.osuPitch, pen=pg.mkPen("r", width=2), symbol="p", symbolSize=3, symbolBrush="y", name="PITCH", )
        self.osuYawPlot = self.osuGraphWidget.plot( self.timeAxis, self.osuYaw, pen=pg.mkPen("green", width=2), symbol="d", symbolSize=3, symbolBrush="r", name="YAW",)
        self.osuGraphWidget.showGrid(x=True, y=True)
        self.osuGraphWidget.setBackground("w")
        self.osuGraphWidget.setLabel( "bottom", '<p style="font:bold;font-size:15px;color:black">Time</p>' )
        self.osuGraphWidget.setLabel( "left", '<p style="font:bold;font-size:15px;color:black">OSU parameters</p>' )
        self.osuGraphWidget.setTitle( '<p style="font:bold;font-size:15px;color:black">OSU</p>' )
        self.osuGraphWidget.getAxis("bottom").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.osuGraphWidget.getAxis("left").setTickFont( QtGui.QFont("Arial", 10, QFont.Bold) )
        self.upperGraphLayout2.addWidget(self.osuGraphWidget)
        
        self.osuGraphWidget.getViewBox().setMouseEnabled(False, False)
        self.axis_sat.setTextPen(pg.mkPen(color="black", width=1))
        self.plot_item = self.osuGraphWidget.getPlotItem()
        self.encoderGraph()
        # self.azGraphWidget.hide()

    def updateGraph(self):
        # print(1)
        current_time = time.time()
        hour, minute = UI.unix_time_to_hour_and_minute(current_time)
        if self.i % 10 == 0:
            # print(self.osuRoll, self.i)
            if (
                (len(self.azGraphList)) <= 60 and len(self.azTarGraphList) <= 60 and len(self.elGraphList) <= 60 and len(self.elTarGraphList) <= 60
                and len(self.xelGraphList) <= 60 and len(self.polGraphList) <= 60 and len(self.polTarGraphList) <= 60 and (len(self.osuRoll)) <= 60
                and (len(self.osuPitch)) <= 60 and (len(self.osuYaw)) <= 60  ):
                self.azGraphList.append(float(self.data[27]))
                self.azTarGraphList.append(float(self.data[22]))
                self.elGraphList.append(float(self.data[25]))
                self.elTarGraphList.append(float(self.data[23]))
                self.xelGraphList.append(float(round((self.xelAngle/3), 2)))
                self.polGraphList.append(float(round((self.polAngle/2.88), 2)))
                self.polTarGraphList.append(float(self.data[24]))
                self.osuRoll.append(float(self.data[14]))
                self.osuPitch.append(float(self.data[15]))
                self.osuYaw.append(float(self.data[16]))
                self.timeAxis.append(current_time)
            else:
                self.timeAxis = self.timeAxis[1:]
                self.timeAxis.append(current_time)
                self.azGraphList = self.azGraphList[1:]
                self.azGraphList.append(float(self.data[27]))
                self.azTarGraphList = self.azTarGraphList[1:]
                self.azTarGraphList.append(float(self.data[22]))
                self.elGraphList = self.elGraphList[1:]
                self.elGraphList.append(float(self.data[25]))
                self.elTarGraphList = self.elTarGraphList[1:]
                self.elTarGraphList.append(float(self.data[23]))
                self.xelGraphList = self.elGraphList[1:]
                self.xelGraphList.append(float(round((self.xelAngle/3), 2)))
                self.polGraphList = self.polGraphList[1:]
                self.polGraphList.append(round((self.polAngle/2.88), 2))
                self.polTarGraphList = self.polTarGraphList[1:]
                self.polTarGraphList.append(float(self.data[24]))
                self.osuRoll = self.osuRoll[1:]
                self.osuRoll.append(float(self.data[14]))
                self.osuPitch = self.osuPitch[1:]
                self.osuPitch.append(float(self.data[15]))
                self.osuYaw = self.osuYaw[1:]
                self.osuYaw.append(float(self.data[16]))
            self.systemMsg.setText(" ")
            self.azPlot.setData(self.timeAxis, self.azGraphList)
            self.azTarPlot.setData(self.timeAxis, self.azTarGraphList)
            self.elPlot.setData(self.timeAxis, self.elGraphList)
            self.elTarPlot.setData(self.timeAxis, self.elTarGraphList)
            self.xelPlot.setData(self.timeAxis, self.xelGraphList) 
            self.polPlot.setData(self.timeAxis, self.polGraphList)
            self.polTarPlot.setData(self.timeAxis, self.polTarGraphList)           
            self.osuRollPlot.setData(self.timeAxis, self.osuRoll)
            self.osuPitchPlot.setData(self.timeAxis, self.osuPitch)
            self.osuYawPlot.setData(self.timeAxis, self.osuYaw)
            self.i = 0
            # print("graph")

    def check_checkbox_state(self):
        if (
            self.rollCheckBox.isChecked()
            and self.pitchCheckBox.isChecked()
            and self.yawCheckBox.isChecked()
        ):
            # print("roll ,pitch and yaw is checked")
            try:
                self.osuGraphWidget.addItem(self.osuRollPlot)
                self.osuGraphWidget.addItem(self.osuPitchPlot)
                self.osuGraphWidget.addItem(self.osuYawPlot)
            except UserWarning:
                print("NO CHANGE")
        elif (
            self.rollCheckBox.isChecked()
            and self.pitchCheckBox.isChecked()
            and not self.yawCheckBox.isChecked()
        ):
            # print("roll and pitch is checked")
            self.osuGraphWidget.removeItem(self.osuYawPlot)
            try:
                self.osuGraphWidget.addItem(self.osuRollPlot)
                self.osuGraphWidget.addItem(self.osuPitchPlot)
            except UserWarning:
                print("NO CHANGE")
        elif (
            self.pitchCheckBox.isChecked()
            and self.yawCheckBox.isChecked()
            and not self.rollCheckBox.isChecked()
        ):
            # print("pitch and yaw is checked")
            self.osuGraphWidget.removeItem(self.osuRollPlot)
            self.osuGraphWidget.addItem(self.osuYawPlot)
            self.osuGraphWidget.addItem(self.osuPitchPlot)
        elif (
            self.yawCheckBox.isChecked()
            and self.rollCheckBox.isChecked()
            and not self.pitchCheckBox.isChecked()
        ):
            # print("yaw and roll is checked")
            self.osuGraphWidget.removeItem(self.osuPitchPlot)
            self.osuGraphWidget.addItem(self.osuYawPlot)
            self.osuGraphWidget.addItem(self.osuRollPlot)
        elif (
            self.rollCheckBox.isChecked()
            and not self.pitchCheckBox.isChecked()
            and not self.yawCheckBox.isChecked()
        ):
            # print("roll is checked")
            self.osuGraphWidget.removeItem(self.osuYawPlot)
            self.osuGraphWidget.removeItem(self.osuPitchPlot)
            self.osuGraphWidget.addItem(self.osuRollPlot)
        elif (
            self.pitchCheckBox.isChecked()
            and not self.yawCheckBox.isChecked()
            and not self.rollCheckBox.isChecked()
        ):
            # print("pitch is checked")
            self.osuGraphWidget.removeItem(self.osuYawPlot)
            self.osuGraphWidget.removeItem(self.osuRollPlot)
            self.osuGraphWidget.addItem(self.osuPitchPlot)
        elif (
            self.yawCheckBox.isChecked()
            and not self.rollCheckBox.isChecked()
            and not self.pitchCheckBox.isChecked()
        ):
            # print("yaw is checked")
            self.osuGraphWidget.removeItem(self.osuRollPlot)
            self.osuGraphWidget.removeItem(self.osuPitchPlot)
            self.osuGraphWidget.addItem(self.osuPitchPlot)
        else:
            # print("Checkbox is unchecked")
            self.osuGraphWidget.removeItem(self.osuRollPlot)
            self.osuGraphWidget.removeItem(self.osuPitchPlot)
            self.osuGraphWidget.removeItem(self.osuYawPlot)

    def clearGraph(self):
        self.osuGraphWidget.removeItem(self.osuRollPlot)
        self.osuGraphWidget.removeItem(self.osuPitchPlot)
        self.osuGraphWidget.removeItem(self.osuYawPlot)
        # print('clear')

    def on_config_btn_toggled(self):
        self.frame_8.show()
        self.settingsTopArea.hide()
        # print("CONFIG")

    # Change QPushButton Checkable status when stackedWidget index changed
    def on_stackedWidget_currentChanged(self, index):
        btn_list = (
            self.icon_only_widget.findChildren(QPushButton)
            # + self.top_right_widget.findChildren(QPushButton)
        )

        for btn in btn_list:
            if index in [12]:
                btn.setAutoExclusive(False)
                btn.setChecked(False)
                print("extr")
            else:
                btn.setAutoExclusive(True)
                # btn.setChecked(True)

    def dashboardStatusCheck(self):
        # print(self.data[3])
        safe = "background-color: rgb(183, 255, 200); border-radius:5px; border :1px solid green; color :green;\n"
        danger = "	background-color: rgb(255, 112, 112); border-radius:5px; border :1px solid red;\n"
        with open("mccuConfig.json", "r") as file:
            config = json.load(file)
        maxFlag = config["flagCheck"]["maximum"]
        # DASHBOARD GPS lock check (diagnostics and dshboard)
        if int(self.data[9]) == maxFlag:
            self.flagGpsLock.setStyleSheet(safe)
        else:
            self.flagGpsLock.setStyleSheet(danger)
        # DASHBOARD Satellite lock check
        if int(self.data[10]) == maxFlag and float(self.data[17]) >= -74:
            self.flagSatLock.setStyleSheet(safe)
        else:
            self.flagSatLock.setStyleSheet(danger)
        # DASHBOARD communication btn
        if self.data:
            self.btnAdeComm.setStyleSheet(safe)
        else:
            self.systemMsg.setText("No Communication")
            self.btnAdeComm.setStyleSheet(danger)
        # Dashboard GPS
        if int(self.data[2]) == maxFlag:
            self.btnGPS.setStyleSheet(safe)
        else:
            # self.systemMsg.setText("GPS error")
            self.btnGPS.setStyleSheet(danger)

        # Dashboard OSU
        if int(self.data[1]) == maxFlag:
            self.btnOSU.setStyleSheet(safe)
        else:
            # self.systemMsg.setText("OSU error")
            self.btnOSU.setStyleSheet(danger)
        # Dashboard beacon flag check
        if int(self.data[3]) == maxFlag:
            self.btnBeacon.setStyleSheet(safe)
        else:
            # self.systemMsg.setText("BPT error")
            self.btnBeacon.setStyleSheet(danger)
        # Dashboard OFC check
        if int(self.data[4]) == maxFlag:
            self.btnFibreLink.setStyleSheet(safe)
        else:
            # self.errorCounter+=1
            # logging.error("OFC ERROR")
            # self.systemMsg.setText("OFC error")
            self.btnFibreLink.setStyleSheet(danger)
            # if self.errorCounter==5:
            #     # print(self.errorCounter)
            #     logging.error("OFC ERROR")

    def diagnostics(self):
        """
        Description of diagnostics
        Load configration and check if the recieved values is in range or not
        Args:
            maxFlag : 1
        """
        safe = "background-color: rgb(183, 255, 200); border-radius:5px; border :2px solid green; color :green;\n"
        danger = "	background-color: rgb(255, 112, 112); border-radius:5px; border :2px solid red;\n"
        with open("mccuConfig.json", "r") as file:
            config = json.load(file)
        maxFlag = config["flagCheck"]["maximum"]
        # ADE SLSC health check
        if int(self.data[11]) == maxFlag:
            self.adeSlscBtn.setStyleSheet(safe)
        else:
            self.adeSlscBtn.setStyleSheet(danger)
        # AZ current check
        if (
            config["motorAzCurr"]["minimum"]
            <= float(self.data[31])
            <= config["motorAzCurr"]["maximum"]
        ):
            self.adeAzMotorBtn.setStyleSheet(safe)
        else:
            self.adeAzMotorBtn.setStyleSheet(danger)
        # EL current check
        if (
            config["motorElCurr"]["minimum"]
            <= float(self.data[29])
            <= config["motorElCurr"]["maximum"]
        ):
            self.adeElMotorBtn.setStyleSheet(safe)
        else:
            self.adeElMotorBtn.setStyleSheet(danger)
        # CROSS EL  current check
        if (
            config["motorClCurr"]["minimum"]
            <= float(self.data[30])
            <= config["motorClCurr"]["maximum"]
        ):
            self.adexElMotorBtn.setStyleSheet(safe)
        else:
            self.adexElMotorBtn.setStyleSheet(danger)
        # POL current check
        if (
            config["motorPolCurr"]["minimum"]
            <= float(self.data[32])
            <= config["motorPolCurr"]["maximum"]
        ):
            self.adePolMotorBtn.setStyleSheet(safe)
        else:
            self.adePolMotorBtn.setStyleSheet(danger)
        # beacon power check
        if float(self.data[17]) >= -74:
            self.adebeconPowBtn.setStyleSheet(safe)
        else:
            self.adebeconPowBtn.setStyleSheet(danger)
        # system temperature check
        if (
            config["sysTemp"]["minimum"]
            <= float(self.data[13])
            <= config["sysTemp"]["maximum"]
        ):
            self.adeTempBtn.setStyleSheet(safe)
        else:
            self.adeTempBtn.setStyleSheet(danger)
        # ADE AZ ENCODER flag set
        if int(self.data[5]) == maxFlag:
            self.adeAzEnBtn.setStyleSheet(safe)
        else:
            self.adeAzEnBtn.setStyleSheet(danger)
        # ADE El ENCODER flag set
        if int(self.data[6]) == maxFlag:
            self.adeElEnBtn.setStyleSheet(safe)
        else:
            self.adeElEnBtn.setStyleSheet(danger)
        # ADE cross elevation ENCODER flag set
        if int(self.data[7]) == maxFlag:
            self.adexElEnBtn.setStyleSheet(safe)
        else:
            self.adexElEnBtn.setStyleSheet(danger)
        # ADE pol  ENCODER flag set
        if int(self.data[8]) == maxFlag:
            self.adePolEnBtn.setStyleSheet(safe)
        else:
            self.adePolEnBtn.setStyleSheet(danger)

        # ADE OSU check (dashboard and diagnostics)
        if int(self.data[1]) == maxFlag:
            self.adeOsuBtn.setStyleSheet(safe)
        else:
            self.adeOsuBtn.setStyleSheet(danger)

        # ADE GPS check
        if int(self.data[2]) == maxFlag:
            self.adeGpsBtn.setStyleSheet(safe)
        else:
            self.adeGpsBtn.setStyleSheet(danger)

        # BDE Communication
        if self.data:
            self.bdeSlscCommBtn.setStyleSheet(safe)
        else:
            self.bdeSlscCommBtn.setStyleSheet(danger)

    def modelStatus(self):
        safe = "background-color: rgb(183, 255, 200); border-radius:5px; border :2px solid green; color :green;\n"
        danger = "	background-color: rgb(255, 112, 112); border-radius:5px; border :2px solid red;\n"
        with open("mccuConfig.json", "r") as file:
            config = json.load(file)
        maxFlag = config["flagCheck"]["maximum"]
        # OSU Status check
        if int(self.data[1]) == maxFlag:
            self.osuStatus.setStyleSheet(safe)
        else:
            self.osuStatus.setStyleSheet(danger)

        # Gps Status check
        if int(self.data[2]) == maxFlag:
            self.gpsStatus.setStyleSheet(safe)
        else:
            self.gpsStatus.setStyleSheet(danger)
        # ADE bpt check
        if int(self.data[3]) == maxFlag:
            self.bptStatus.setStyleSheet(safe)
        else:
            self.bptStatus.setStyleSheet(danger)
        # Az En  Status check
        if int(self.data[5]) == maxFlag:
            self.enAzStatus.setStyleSheet(safe)
        else:
            self.enAzStatus.setStyleSheet(danger)
        # Elevation En  Status check
        if int(self.data[6]) == maxFlag:
            self.enElStatus.setStyleSheet(safe)
        else:
            self.enElStatus.setStyleSheet(danger)
        # Cross El En  Status check
        if int(self.data[7]) == maxFlag:
            self.enClStatus.setStyleSheet(safe)
        else:
            self.enClStatus.setStyleSheet(danger)
        # Pol En  Status check
        if int(self.data[8]) == maxFlag:
            self.enPolStatus.setStyleSheet(safe)
        else:
            self.enPolStatus.setStyleSheet(danger)
        # AZ MOTOR CURRENT STATUS
        if (
            config["motorAzCurr"]["minimum"]
            <= float(self.data[32])
            <= config["motorAzCurr"]["maximum"]
        ):
            self.azMotorStatus.setStyleSheet(safe)
        else:
            # print('az :',self.data[32])
            self.azMotorStatus.setStyleSheet(danger)
        # EL MOTOR CURRENT STATUS
        if (
            config["motorElCurr"]["minimum"]
            <= float(self.data[29])
            <= config["motorElCurr"]["maximum"]
        ):
            self.elMotorStatus.setStyleSheet(safe)
        else:
            # print('el :',self.data[29])
            self.elMotorStatus.setStyleSheet(danger)
        # CROSS EL MOTOR CURRENT STATUS
        if (
            config["motorClCurr"]["minimum"]
            <= float(self.data[31])
            <= config["motorClCurr"]["maximum"]
        ):
            self.clMotorStatus.setStyleSheet(safe)
        else:
            # print('xel :',self.data[31])
            self.clMotorStatus.setStyleSheet(danger)
        # POL MOTOR CURRENT STATUS
        if (
            config["motorPolCurr"]["minimum"]
            <= float(self.data[30])
            <= config["motorPolCurr"]["maximum"]
        ):
            self.polMotorStatus.setStyleSheet(safe)
        else:
            # print('pol :',self.data[30])
            self.polMotorStatus.setStyleSheet(danger)
        # BUC CURRENT STATUS
        if (
            config["bucCurr"]["minimum"]
            <= float(self.data[33])
            <= config["bucCurr"]["maximum"]
        ):
            self.BucStatus.setStyleSheet(safe)
        else:
            self.BucStatus.setStyleSheet(danger)

    def homePos(self):
        if self.flag == 1:
            homePosStatus = service.setHomePosition()
            if homePosStatus == 1:
                logging.info("home position set")
                self.systemMsg.setText("Home position set")
                print("home position")
            else:
                self.systemMsg.setText("Home position not set")

    def Safemode(self):
        if self.flag == 1:
            safeModeStatus = service.setSafemode()
            if safeModeStatus == 1:
                logging.info("System is in safeMode")
                self.systemMsg.setText("System is in safeMode")
                print("safemode")
            else:
                self.systemMsg.setText("safeMode does not set")

    def txMuteCheck(self):
        if self.flag == 1:
            safe = "background-color: rgb(183, 255, 200); border-radius:5px; border :2px solid green; color :green;\n"
            danger = "	background-color: rgb(255, 112, 112); border-radius:5px; border :2px solid red;\n"
            if self.txMuteBtn1.isChecked():
                txMuteStatus = service.TxMute()
                if txMuteStatus == 1:
                    logging.info("Tx Mute")
                    self.BucStatus.setStyleSheet(safe)
                    self.systemMsg.setText("Tx Mute")
                else:
                    self.systemMsg.setText("Tx Mute does not set")
            else:
                txMuteStatus = service.txUnmute()
                if txMuteStatus == 1:
                    self.BucStatus.setStyleSheet(danger)
                    logging.info("Tx Unmute")
                    self.systemMsg.setText("Tx Unmute")
                else:
                    self.systemMsg.setText("Tx Unmute not set")

    def restartSlsc(self):
        if self.flag == 1:
            text, ok = QInputDialog.getText(
                None,
                "Security Password",
                "<b><font size='3'>To restart SLSC , enter security Password.",
                QLineEdit.Password,
            )
            if ok and text:
                if text == "123":
                    service.setRestart()
                    logging.info("SLSC RESTART")
                    self.systemMsg.setText("SLSC RESTART")
                else:
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowTitle("Security Password")
                    msgBox.setText("Incorrect password .")
                    msgBox.setWindowModality(Qt.ApplicationModal)
                    reply = msgBox.exec_()

    def shutDownSlsc(self):
        if self.flag == 1:
            text, ok = QInputDialog.getText(
                None,
                "Security Password",
                "<b><font size='3'>To shutdown SLSC, enter security Password.</font></b>",
                QLineEdit.Password,
            )
            if ok and text:
                if text == "123":
                    service.setShutdown()
                    logging.info("SLSC shutdown")
                    self.systemMsg.setText("SLSC shutdown")
                else:
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowTitle("Security Password")
                    msgBox.setText("Incorrect password .")
                    msgBox.setWindowModality(Qt.ApplicationModal)
                    reply = msgBox.exec_()

    # ## functions for changing menu page
    def on_dashboardBtn1_toggled(self):
        self.stackedWidget.setCurrentIndex(0)

    def on_satBtn1_toggled(self):
        self.stackedWidget.setCurrentIndex(1)

    def on_antennaBtn1_toggled(self):
        self.stackedWidget.setCurrentIndex(2)

    def on_monitorBtn1_toggled(self):
        # self.stackedWidget.setCurrentIndex(3)
        self.stackedWidget.setCurrentIndex(11)

    def on_diagBtn1_toggled(self):
        self.stackedWidget.setCurrentIndex(4)

    def on_logBtn1_toggled(self):
        self.stackedWidget.setCurrentIndex(5)

    def on_fileManagerBtn_toggled(self):
        self.stackedWidget.setCurrentIndex(6)

    def on_user_btn_toggled(self):
        self.stackedWidget.setCurrentIndex(7)

    def on_settings_toggled(self):
        self.stackedWidget.setCurrentIndex(8)

    def on_oemBtn1_toggled(self):
        self.stackedWidget.setCurrentIndex(9)

    def on_oemBtn2_toggled(self):
        self.stackedWidget.setCurrentIndex(9)

    def on_helpBtn_toggled(self):
        self.stackedWidget.setCurrentIndex(10)

    def on_addSatBtn_toggled(self):
        self.addEditSatFrame.show()
        self.editSatBtn_2.hide()
        self.addSatBtn.setEnabled(False)
        self.editSatBtn.setEnabled(False)
        self.delSatBtn.setEnabled(False)

    def restoreOriginalCursor(self):
        self.setCursor(Qt.ArrowCursor)
        self.setEnabled(True)  # Enable user interaction

    def changeSlscIP(self):
        changedIP1 = self.ipSlsc1.text()
        changedIP2 = self.ipSlsc2.text()
        changedIP3 = self.ipSlsc3.text()
        changedIP4 = self.ipSlsc4.text()
        changedPort = self.connectingPort.text()

        changedIp = changedIP1 + "." + changedIP2 + "." + changedIP3 + "." + changedIP4

        if (
            (len(changedIP1) != 0)
            and (len(changedIP2) != 0)
            and (len(changedIP3) != 0)
            and (len(changedIP4) != 0)
        ):
            service_instance = service.commands()
            service_instance.broadcastSetIp(changedIp, changedPort)
            cursor = Qt.WaitCursor
            self.changeIPOkBtn.setCursor(cursor)
            self.setCursor(Qt.WaitCursor)
            self.setEnabled(False)  # Disable user interaction

            self.wait_timer.start(10000)  # Set a 30-second timer
            # dialog = CustomMessageDialog()
            # dialog.exec_()
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle("Security Password")
            msgBox.setText("wait for few seconds")
            msgBox.setWindowModality(Qt.ApplicationModal)
            msgBox.exec_()

    def cancelChangeIp(self):
        self.ipSlsc1.clear()
        self.ipSlsc2.clear()
        self.ipSlsc3.clear()
        self.ipSlsc4.clear()
        self.connectingPort.clear()

    def motorRampingTimeCalcy(Axis_Ang, GR, PPR):
        # Motor algo dynamic pulse width modulation
        rpm_min = 0.25  # absolute axis
        rpm_max = 0.25  # absolute axis
        S_exp = 2.0  # ----only variable to tune

        # Axis_Ang=5.0 #Absolute Axis
        # _____________________________________________________________
        if Axis_Ang > 0 and Axis_Ang <= 5:
            rpm_min = 1.0
            rpm_max = 1.0
        elif Axis_Ang > 5 and Axis_Ang <= 10:
            rpm_min = 1.0
            rpm_max = 1.5
        elif Axis_Ang > 10 and Axis_Ang < 15:
            rpm_min = 1.0
            rpm_max = 2.0
        elif Axis_Ang > 15 and Axis_Ang <= 30:
            rpm_min = 1.0
            rpm_max = 3.0
        elif Axis_Ang > 30 and Axis_Ang <= 60:
            rpm_min = 1.0
            rpm_max = 3.0
        elif Axis_Ang > 60:
            rpm_min = 1.0
            rpm_max = 3.75
        else:
            rpm_min = 1.0
            rpm_max = 3.75

        speed_min = (rpm_min * 360) / 60
        speed_max = (rpm_max * 360) / 60
        # PPR=3200
        # print(PPR)
        Npulses = int(Axis_Ang * GR * PPR / 360)
        if Npulses == 0:
            return 0
        if not Npulses == 0:
            if np.remainder(Npulses, 2) == 0:
                Npulses = Npulses + 1

            Fixed_S_Pulses = int(0.1 * Npulses)
            # we now always have odd pulses

            max_pwm_width = (Axis_Ang / speed_min) / Npulses  # in uS

            min_pwm_width = (Axis_Ang / speed_max) / Npulses  # in uS

            # Perfom linear ramping of pulse width during toggleing
            First_half_pulses = int((Npulses - 1) / 2)

            fmin = 1 / max_pwm_width  # min speed 0.5RPM
            fmax = 1 / min_pwm_width  # max speed 3RPM
            delta_freq = (fmax - fmin) / First_half_pulses
            if delta_freq == 0:
                delta_freq = 1

            # _________________________________________________________________________
            # Function for S-curve

            t_ang = np.arange(Fixed_S_Pulses)
            freq_S_curve = (fmax - fmin) * (
                np.sin(np.pi / 2 * t_ang / Fixed_S_Pulses)
            ) ** S_exp + fmin
            All_freq = np.zeros(Npulses)
            All_freq[0:Fixed_S_Pulses] = freq_S_curve
            All_freq[Fixed_S_Pulses : Npulses - Fixed_S_Pulses] = fmax
            All_freq[Npulses - Fixed_S_Pulses : Npulses] = np.flip(freq_S_curve)

            dynamic_pwm_S_curve = np.zeros(Npulses)
            All_PWM_S_curve = (1 / All_freq) * 1000000 / 2

            Total_Time_S_curve = np.sum(All_PWM_S_curve)

            Fixed_Start_Pulses = Fixed_S_Pulses
            Fixed_Stop_Pulses = Fixed_S_Pulses

            S_dt_up = (
                2
                * np.sqrt(fmin)
                * np.sqrt(fmax)
                * Fixed_Start_Pulses
                / (2 * fmin**2 + 2 * (fmax - fmin) * fmin)
                * 1000
                + 1 / ((fmax - fmin) / 8 + fmin) * 1000
            ) / 1000

            S_dt_Cons = (
                (Npulses - Fixed_Start_Pulses - Fixed_Stop_Pulses) * 1 / fmax * 1000
            ) / 1000
            S_dt_down = (
                2
                * np.sqrt(fmin)
                * np.sqrt(fmax)
                * Fixed_Stop_Pulses
                / (2 * fmin**2 + 2 * (fmax - fmin) * fmin)
                * 1000
                + 1 / ((fmax - fmin) / 8 + fmin) * 1000
            ) / 1000
            # print(round(S_dt_up+ S_dt_Cons+S_dt_down,2))
            return round(S_dt_up + S_dt_Cons + S_dt_down, 2)
        else:
            total_time = 0
            return total_time

    # def on_addSatBtn_toggled(self):
    #     self.frame_15.hide()

    def writeLogs(self):
        if self.logCounter % 10 == 0:  # every 2 sec log when timer = 200
            # print(self.logCounter)
            # print(self.data)
            service.write_to_slscStatusLog(self.data)
            self.logCounter = 0
            # print('graph')


class CustomMessageDialog(QDialog):
    def __init__(test):
        super().__init__()
        test.setWindowTitle("Security Password")
        test.setWindowFlags(
            test.windowFlags() | Qt.FramelessWindowHint
        )  # Remove window frame
        test.setModal(True)  # Make it modal
        test.setAutoFillBackground(True)

        layout = QVBoxLayout()

        label = QLabel("Wait for a few seconds", test)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        test.setLayout(layout)

        test.timer = QTimer(test)
        test.timer.setSingleShot(True)
        test.timer.timeout.connect(test.accept)
        test.timer.start(10000)  # Close the dialog after 5 seconds (adjust as needed)
# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     ui = UI()
#     ui.show()
#     sys.exit(app.exec_())