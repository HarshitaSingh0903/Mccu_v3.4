import sys, os, csv, time,  ipaddress, socket, logging, platform
from resources import loginDB , service, configParameter, satFileHandling, ipDBFileHandling
from PyQt5  import *
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from dashboardWindow import UI
from os.path import exists

if getattr(sys, 'frozen', False):
    import pyi_splash
    pyi_splash.update_text("heloo")

def checkIfFileExists():
    satDBExists =  exists("satelliteDB.csv")
    if satDBExists == False:
        # sat1= ("GSAT-15",11697.50,0,25,90,"   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957")
        satFileHandling.write_csv_without_header("satelliteDB.csv")
        # print("sat file created")1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957")
        # sat2= ("GSAT-10",11697.50,0,25,90,"1 41028U 15065A   23176.33313058 -.00000243  00000+0  00000+0 0  9995,2 41028   0.0114 346.6174 0003767  95.6642  44.3444  1.00267187 27957")
        # sat3= ("GSAT-7",11697.50,0,25,90,"1 41028U 15065A
    congigParaFileExists =  exists("mccuConfig.json")
    if congigParaFileExists == False:
        configParameter.createConfigFile("mccuConfig.json")
        print("config file created")
    ipFileExists =  exists("ipPortDB.csv")
    if ipFileExists == False:
        ipDBFileHandling.create_empty_file()
        print("created a ip file ")
    checkUserDbExits =  exists("user_credentials.db")
    if checkUserDbExits == False:
        loginDB.defalut_db('1','1')
        loginDB.defalut_db('captain','samarsat')
        print("new user db")

checkIfFileExists()

def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Load the UI file dynamically
        loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui//login.ui"), self)
        # app_icon = QtGui.QIcon()
        # app_icon.addFile('ui//icon//Samarsat _Colour_ Logo.jpg', QtCore.QSize(16,16))
        # app.setWindowIcon(app_icon)
        # self.setWindowIcon(QIcon('ui//icon//Samarsat _Colour_ Logo.jpg'))
        self.forgetPassBtn.hide()
        self.funcWidget.setCurrentIndex(0)
        self.setWindowIcon(QtGui.QIcon(resource_path('ui/icon/Samarsat_taskbar.ico')))
        
        self.createBtn.clicked.connect(self.createdAccount)
        self.loginBtn.clicked.connect(self.login)
        self.registerBtn.clicked.connect(lambda: self.funcWidget.setCurrentIndex(1))
        self.backBtn_ipconfig.clicked.connect(lambda: self.funcWidget.setCurrentIndex(0))
        self.exitIpConfigBtn.clicked.connect(self.exitGui)
        self.okIpConfigBtn.clicked.connect(self.communicationWin)
        self.okBtn.clicked.connect(self.mainWin)
        self.backBtn.clicked.connect(lambda: self.funcWidget.setCurrentIndex(0))
        self.backBtn_comm.clicked.connect(lambda: self.funcWidget.setCurrentIndex(0))
        self.backBtn_forget.clicked.connect(lambda: self.funcWidget.setCurrentIndex(0))
        self.exitBtn.clicked.connect(self.exitGui)
        self.exitBtn_2.clicked.connect(self.exitGui)
        self.checkBox.stateChanged.connect(self.checkbox_state)
        self.forgetPassBtn.clicked.connect(lambda: self.funcWidget.setCurrentIndex(3))
        self.confirmBtn.clicked.connect(self.forgetPass)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        int_validator = QIntValidator(0,255)
        port_intvalidator = QIntValidator(0, 65535)
        self.sbInput_1.setValidator(int_validator)
        self.sbInput_2.setValidator(int_validator)
        self.sbInput_3.setValidator(int_validator)
        self.sbInput_4.setValidator(int_validator)
        self.gatewayInput_1.setValidator(int_validator)
        self.gatewayInput_2.setValidator(int_validator)
        self.gatewayInput_3.setValidator(int_validator)
        self.gatewayInput_4.setValidator(int_validator)
        self.avIpInput1.setValidator(int_validator)
        self.avIpInput2.setValidator(int_validator)
        self.avIpInput3.setValidator(int_validator)
        self.avIpInput4.setValidator(int_validator)
        self.avPortInput.setValidator(port_intvalidator)
        # print("GUI loaded")
        self.center()
        self.show()
        
        self.sbInput_1.textChanged.connect(self.on_text_changed)
        self.sbInput_2.textChanged.connect(self.on_text_changed)
        self.sbInput_3.textChanged.connect(self.on_text_changed)
        self.sbInput_4.textChanged.connect(self.on_text_changed)
        self.gatewayInput_1.textChanged.connect(self.on_text_changed)
        self.gatewayInput_2.textChanged.connect(self.on_text_changed)
        self.gatewayInput_3.textChanged.connect(self.on_text_changed)
        self.gatewayInput_4.textChanged.connect(self.on_text_changed)
        self.avIpInput1.textChanged.connect(self.on_text_changed)
        self.avIpInput2.textChanged.connect(self.on_text_changed)
        self.avIpInput3.textChanged.connect(self.on_text_changed)
        self.avIpInput4.textChanged.connect(self.on_text_changed)
        self.avPortInput.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        sender = self.sender()  # Identify which line edit emitted the signal
        text = sender.text()

        if text.isdigit():
            number = int(text)
            if sender == self.sbInput_1:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.sbInput_2:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.sbInput_3:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.sbInput_4:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.gatewayInput_1:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                    self.avIpInput1.setText(self.gatewayInput_1.text())
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.gatewayInput_2:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                    self.avIpInput2.setText(self.gatewayInput_2.text())
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.gatewayInput_3:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                    self.avIpInput3.setText(self.gatewayInput_3.text())
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.gatewayInput_4:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.avIpInput4:
                if 0 <= number <= 255:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
            elif sender == self.avPortInput:
                if 0 <= number <= 65535:
                    self.ipConfigErrorMsg.setText("")
                else:
                    self.ipConfigErrorMsg.setText("Octets must be between 0 and 255.")
        else:
            self.ipConfigErrorMsg.setText("Please enter a valid number.")
           
    def login(self):
        self.loginUser=self.loginUserInput.text()
        self.loginPass=self.loginPassInput.text()
        if not (len(self.loginUser)==0 and len(self.loginPass)==0):
            self.checkLogin=loginDB.check_password(self.loginUser, self.loginPass)
            if self.checkLogin=='correct':  
                ipFileExits =  exists("ipPortDB.csv")
                if ipFileExits==True:
                    if ipDBFileHandling.is_csv_empty( "ipPortDB.csv")==True:
                        self.funcWidget.setCurrentIndex(4)
                        try:
                            command_instance = service.commands()
                            wizParamList=command_instance.wizGetInfo()
                            try:
                                wiz= wizParamList[0]
                                wiz= wiz.split(":")
                                if len(wizParamList)!=0:
                                    self.macInput1.setText(wiz[0])
                                    self.macInput2.setText(wiz[1])
                                    self.macInput3.setText(wiz[2])
                                    self.macInput4.setText(wiz[3])
                                    self.macInput5.setText(wiz[4])
                                    self.macInput6.setText(wiz[5])
                                else:
                                    self.ipConfigErrorMsg.setText('Please fill all input ')
                            except IndexError:
                                self.funcWidget.setCurrentIndex(0)
                                message = QMessageBox()
                                message.setWindowModality(Qt.ApplicationModal)
                                message.setWindowTitle('Warning')
                                message.setIcon(QMessageBox.Warning)
                                message.setText('No Device present ')
                                message.setWindowIcon(QtGui.QIcon(resource_path('ui/icon/Samarsat_taskbar.ico')))
                                message.exec_()
                                # self.loginMsg.setText('No Device present ')
                                
                                # self.ipConfigErrorMsg.setText('No Device present ')admin
                                # self.funcWidget.setCurrentIndex(0)
                        except TimeoutError:
                            self.ipConfigErrorMsg.setText('No Device present ')
                            self.funcWidget.setCurrentIndex(0)
                        
                    else:
                        self.funcWidget.setCurrentIndex(2)
                        ip, port= ipDBFileHandling.read_ip_port_from_csv( "ipPortDB.csv")
                        self.splitIP= ip.split(".")
                        self.ipInput1.setText(self.splitIP[0])
                        self.ipInput2.setText(self.splitIP[1])
                        self.ipInput3.setText(self.splitIP[2])
                        self.ipInput4.setText(self.splitIP[3])
                        self.portInput.setText(port)
                    self.loginMsg.setText(" ")
                        # self.commMsg.setText('Wait for some time before connecting')
                        # print('file notempty')
            elif self.checkLogin=='Incorrect password':
                self.forgetPassBtn.show()
                self.loginMsg.setText(self.checkLogin)
                self.loginUserInput.clear()
                self.loginPassInput.clear()
            else:
                self.forgetPassBtn.show()
                self.loginMsg.setText(self.checkLogin)
                self.loginUserInput.clear()
                self.loginPassInput.clear()
        else:
            self.loginMsg.setText('Please fill all input ')
    
    def communicationWin(self):
        self.ipConfigErrorMsg.setText('CHANGING IP AND PORT.PLEASE WAIT FOR FEW SECONDS ')
        self.availableIp= self.avIpInput1.text()+'.'+self.avIpInput2.text()+'.'+self.avIpInput3.text()+'.'+self.avIpInput4.text()
        self.availablePort=self.avPortInput.text()
        # print('ip and port :', self.availableIp, self.availablePort)
        if (len(self.sbInput_1.text())!=0) and (len(self.sbInput_2.text())!=0) and (len(self.sbInput_3.text())!=0) and (len(self.sbInput_4.text())!=0):
            self.sbMask = self.sbInput_1.text() +'.'+ self.sbInput_2.text() +'.'+ self.sbInput_3.text()+'.'+ self.sbInput_4.text()
            if (len(self.gatewayInput_1.text())!=0) and (len(self.gatewayInput_2.text())!=0) and (len(self.gatewayInput_3.text())!=0) and (len(self.gatewayInput_4.text())!=0):
                self.gwInput= self.gatewayInput_1.text()+'.'+ self.gatewayInput_2.text()+'.'+ self.gatewayInput_3.text()+'.'+self.gatewayInput_4.text()
                self.dnsInput= self.gwInput
                if (len(self.avIpInput1.text())!=0 and len(self.avIpInput2.text())!=0) and (len(self.avIpInput3.text())!=0) and (len(self.avIpInput4.text())!=0) and (len(self.avPortInput.text())!=0):
                    command_instance = service.commands()
                    command_instance.broadcastSetIp(self.availableIp, self.availablePort, self.sbMask, self.gwInput, self.dnsInput)
                    self.funcWidget.setCurrentIndex(2)
                    ipDBFileHandling.write_ip(self.availableIp, self.availablePort)
                    ip, port= ipDBFileHandling.read_ip_port_from_csv( "ipPortDB.csv")
                    self.splitIP= ip.split(".")
                    self.ipInput1.setText(self.splitIP[0])
                    self.ipInput2.setText(self.splitIP[1])
                    self.ipInput3.setText(self.splitIP[2])
                    self.ipInput4.setText(self.splitIP[3])
                    self.portInput.setText(port)
                    msgBox = QMessageBox(self)  
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowModality(Qt.ApplicationModal)
                    msgBox.setWindowTitle("Information")
                    msgBox.setText("wait for few seconds")
                    msgBox.exec_() 
                    time.sleep(5)
                    
                else:
                    self.ipConfigErrorMsg.setText('Please fill ip and port  input ')
            else:
                self.ipConfigErrorMsg.setText('Please fill gateway ')
        else:
            self.ipConfigErrorMsg.setText('Please fill subnet Mask ')
    
    def createdAccount(self):
        self.registerUser= self.registerUserInput.text()
        self.registerPass= self.registerPassInput.text()
        if not (len(self.registerUser)==0 or len(self.registerPass)==0):
            text, ok = QInputDialog.getText(None, "Security Password", "<b><font size='3'>To add new User , enter security Password.", QLineEdit.Password)
            if ok and text:
                if text == '123':
                    self.createNewLogin=loginDB.register_user(self.registerUser, self.registerPass)
                    if  self.createNewLogin=='User registered successfully.':
                        self.RegisterMsg.setText('NEW ACCOUNT CREATED. Please go back to login page. ')
                        self.registerUserInput.clear()
                        self.registerPassInput.clear()
                    else:
                        self.RegisterMsg.setText(self.createNewLogin)
                else:
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowModality(Qt.ApplicationModal)
                    msgBox.setWindowTitle("Security Password")
                    msgBox.setText("Incorrect password .")
                    reply = msgBox.exec_()
        else:
            self.RegisterMsg.setText('Please fill all input ') 
            
    def mainWin(self):
        self.ip= self.ipInput1.text()+'.'+self.ipInput2.text()+'.'+self.ipInput3.text()+'.'+self.ipInput4.text()
        self.port=self.portInput.text()
        if (len(self.ip)>=13 and len(self.port)>0):
            if ipDBFileHandling.validate_ip_address(self.ip)==True:
                try:
                    ping=service.pingToWiznet() 
                    if ping=="alive":  
                        self.commMsg.setText('connection found ')
                        self.ui_main = UI()
                        self.funcWidget.addWidget(self.ui_main)
                        # self.funcWidget.setFixedSize(self.ui_main.size())
                        screen = QDesktopWidget().screenGeometry()
                        screen_width, screen_height = screen.width(), screen.height()
                        self.funcWidget.setFixedSize(1024,768)
                        # self.funcWidget.setFixedSize(screen_width,screen_height)
                        self.funcWidget.setCurrentIndex(5)
                        self.ui_main.show()
                        self.ui_main.currentUser.setText(self.loginUser)
                        self.ui_main.exitWinBtn.clicked.connect(lambda: self.close())
                        self.ui_main.logOutBtn.clicked.connect(lambda: self.backToLoginFromMainWin())
                        self.ui_main.changeIPOkBtn.clicked.connect(lambda : self.changeSlscIP())
                        logging.info(f"Login User : {self.loginUser}")
                        self.titleWidget.hide()
                        qr= self.frameGeometry()
                        qr.moveCenter(QDesktopWidget().availableGeometry().center())
                        self.move(qr.topLeft())
                        # print(self.funcWidget.currentIndex())
                        if self.loginUser!='1':
                            self.ui_main.oemBtn1.hide()
                            # self.ui_main.antennaBtn1.hide()
                            # self.ui_main.antennaBtn2.hide()
                        else:
                            self.ui_main.oemBtn1.show()   

                            # self.ui_main.antennaBtn1.show()
                            # self.ui_main.antennaBtn2.show()
                        # self.showFullScreen()
                    else:
                        instance=service.commands()
                        instance.resetWiz()
                        self.commMsg.setText('connecting ......')
                except Exception as e:
                    self.commMsg.setText('NO connection. Try again')
                    print(f"An error ochhcurred: {str(e)}")
            else:
                self.commMsg.setText('INVALID IP')
        else:
            self.commMsg.setText('incorrect ip and port')

    def changeSlscIP(self):
        
        changedIP1 = self.ui_main.ipSlsc1.text()
        changedIP2 = self.ui_main.ipSlsc2.text()
        changedIP3 = self.ui_main.ipSlsc3.text()
        changedIP4 = self.ui_main.ipSlsc4.text()
        changedPort = self.ui_main.connectingPort.text()
        changedIp = changedIP1 + '.' + changedIP2 + '.' + changedIP3 + '.' + changedIP4
        if (len(changedIP1) != 0) and (len(changedIP2) != 0) and (len(changedIP3) != 0) and (len(changedIP4) != 0):
            
            # self.ui_main.timer.stop()
            self.setEnabled(False)  # Disable user interaction
            service_instance = service.commands()
            service_instance.broadcastSetIp(changedIp, changedPort)
            # logging.info(f"IP and port chnaged to {changedIp}, {changedPort}")
            # self.ui_main.changeIPmsg.setText(f"changing ip")
            time.sleep(10)
            
            command_instance = service.commands()
            wizParamList=command_instance.wizGetInfo()
            # print(wizParamList)
            newIP, newPort = wizParamList[1], wizParamList[2]
            print(newIP, newPort)
            if newIP== changedIp and newPort == changedPort:
                print('write in file')
                ipDBFileHandling.write_ip(newIP, newPort)
                # self.ui_main.timer.start()
                self.setEnabled(True)
                message = QMessageBox()
                message.setIcon(QMessageBox.Information)
                message.setWindowModality(Qt.ApplicationModal)
                message.setText(f"Ip changed to :{newIP} and port changed to :{newPort}")
                message.exec_()
                self.ui_main.ipSlsc1.clear()
                self.ui_main.ipSlsc2.clear()
                self.ui_main.ipSlsc3.clear()
                self.ui_main.ipSlsc4.clear()
                self.ui_main.connectingPort.clear()
            else:
                self.setEnabled(True)
                print('not changed')
                message = QMessageBox()
                message.setIcon(QMessageBox.Information)
                message.setWindowModality(Qt.ApplicationModal)
                message.setText("IP PORT DOES NOT CHANGE")
                message.exec_()
                self.ui_main.ipSlsc1.clear()
                self.ui_main.ipSlsc2.clear()
                self.ui_main.ipSlsc3.clear()
                self.ui_main.ipSlsc4.clear()
                self.ui_main.connectingPort.clear()

    def update_progress(self):
        for i in range(101):
            time.sleep(0.1)  # Sleep for 10 ms (0.01 seconds)
            self.progress_bar.setValue(i)
            app.processEvents()  # Process GUI events to keep the UI responsive
        
        self.progress_bar.close()
        
    def backToLoginFromMainWin(self):
        text, ok = QInputDialog.getText(None, "Security Password", "<b><font size='3'>To logout from current user, enter security Password.", QLineEdit.Password, )
        if ok and text:
            if text == "123":
                self.titleWidget.show()
                self.funcWidget.setFixedSize(500,600)
                widget_to_delete = self.funcWidget.widget(5)
                self.funcWidget.removeWidget(widget_to_delete)
                # widget_to_delete.deleteLater()
                # self.ui_main.deleteLater()
                # self.Form.setSpacing(0)
                self.funcWidget.setCurrentIndex(0)
                self.resize(1000, 609)
                self.center()
            else:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowModality(Qt.ApplicationModal)
                msgBox.setWindowTitle("Security Password")
                msgBox.setText("Incorrect password .")
                reply = msgBox.exec_()
        
    def center(self):
        qr= self.frameGeometry()
        cp=QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def shutDownMccu(self):
        if platform.system()=="Windows": 
            os.system("shutdown -s -t 0") 

    def forgetPass(self):
        self.loginMsg.setText(" ")
        self.forgetUser= self.forgetPassUserInput.text()
        self.newPass = self.newPassInput.text()
        self.confirmPass = self.confirmPassInput.text()
        if (len(self.forgetUser)==0 or len(self.newPass)==0 or len(self.confirmPass)==0):
            self.forgetPassMsg.setText('Please fill all inputs')
        else:
            if self.newPass==self.confirmPass:
                text, ok = QInputDialog.getText(None, "Security Password", "<b><font size='3'>To add change password , enter security Password.", QLineEdit.Password)
                if ok and text:
                    if text == '123':
                        # print(123)
                        self.forgetPassSet=loginDB.reset_password(self.forgetUser, self.confirmPass)
                        if self.forgetPassSet == 'An error occurred while resetting the password.':
                            self.forgetPassMsg.setText('New Password and confirm Password does not match !')
                        elif self.forgetPassSet == ' not found in the database. Password reset failed.':
                            self.forgetPassMsg.setText(self.forgetUser + self.forgetPassSet)
                        else:
                            self.forgetPassMsg.setText('New password set ! ')
                    else:
                        msgBox = QMessageBox(self)
                        msgBox.setIcon(QMessageBox.Information)
                        msgBox.setWindowModality(Qt.ApplicationModal)
                        msgBox.setWindowTitle("Security Password")
                        msgBox.setText("Incorrect password .")
                        reply = msgBox.exec_()
            else:
                self.forgetPassMsg.setText('New Password and confirm Password does not match !')
        
    def exitGui(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Exit?")
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowModality(Qt.ApplicationModal)
        msgBox.setText("Are you sure to EXIT???")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply = msgBox.exec_()
        if reply == QMessageBox.Yes:
            self.close()

    def checkbox_state(self, state):
        """
        Description of checkbox_state
        check state of checkbox if the check box is checked then show password, else vice-versa
        Args:
            state : check state of checkbox
        """
        if state == 2:  
            self.loginPassInput.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.loginPassInput.setEchoMode(QtWidgets.QLineEdit.Password)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if getattr(sys, 'frozen', False):
        pyi_splash.close()
    widget = LoginWidget()
    widget.show()
    sys.exit(app.exec_())

 