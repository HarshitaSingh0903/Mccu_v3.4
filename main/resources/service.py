import socket, ctypes, multiprocessing
from threading import Thread
import time, os, sqlite3, csv, sys
from crccheck.crc import Crc16
from datetime import datetime
# from pythonping import ping

def read_ip_port_from_csv():
        try:
            with open("ipPortDB.csv", 'r') as csvfile:
                csv_reader = csv.reader(csvfile)
                rows = list(csv_reader)
                if len(rows) < 2:
                    print("CSV file does not contain both IP and port.")
                    return None, None
                ip = rows[0][0]
                port = rows[1][0]
                
                return ip, port
        except FileNotFoundError:
            print(f"File  not found.")
            return None, None
        
class SLSCReciever(object):
    """
    Description of SLSCReciever

    Inheritance: object
    Method :
        __init__ : constructor of class SLSCReciever
    """

    def __init__(self, host=None, port=None) -> None:
        """
        Description of __init__
        Args:
            host= host IP address
            port= connecting port
        Returns:
            None
        """
        self.host = host
        self.port = port

    def connect_to_slsc(self):
        """
        Description of connect_to_slsc
        create a socket

        Args:
            main_socket_server : create socket
        Returns:
            main_socket_server

        """
        main_socket_server = socket.socket()
        
        try:
            main_socket_server.connect((self.host, self.port))
            print("connected")
        except Exception as e:
            main_socket_server = None
            print("Connection Failed")
            time.sleep(2)
        return main_socket_server

def connectToSlsc():
    host, port = read_ip_port_from_csv()
    # print('host : ', host,  port)
    main_socket_server = socket.socket()
    main_socket_server.settimeout(0.5)
    try:
        main_socket_server.connect((host, int(port)))
        # print('connected')
    except Exception as e:
        print("Connection Failed", e)
        # time.sleep(5)
    return main_socket_server

def pingToWiznet():
    updateCmd = bytearray([161, 1])
    addCrc = APLCRC_Calc(updateCmd,len(updateCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    updateCmd.extend([CRC1, CRC2])
    while True:
        s = connectToSlsc()
        s.sendall(updateCmd)
        slscRecvData = s.recv(150)
        # print(slscRecvData)
        if (len(slscRecvData)) >= 2:
            status= "alive"
            # print('s :',status)
            break
        else:
            status= None
            # command_instance = commands()
            # command_instance.resetWiz() 
            print("data not found")
    print(status)
    return status
# pingToWiznet()
def dataLog_setup():
    """Description of dataLog_setup
        Create a folder name with current year and current month for Logs ,
        also check if the folder with that name already exist or not.
        If it does not exist then create folder.
    Args:
        current_year: current year
        current_month: current month
        folder_name: folder name current year and current month
    Returns:
        folder_name
    """
    current_year = datetime.now().year
    current_month = datetime.now().strftime("%B")
    folder_name = str(current_year) + "-" + str(current_month)
    if os.path.exists(folder_name):
        pass
    else:
        print("The log folder does not exist.")
        os.makedirs(folder_name)
    return folder_name

def write_to_slscStatusLog(status):
    """
    Description of write_to_slscStatusLog
    Create a csv file in log folder with name LOG-(current date)-(current time)
    Append the recieved data in this log file
    """
    current_date = time.strftime('%Y%m%d')
    # current_minute = time.strftime("%I%M%p") for minute
    current_minute = time.strftime("%I%p")
    csv_filename = os.path.join(dataLog_setup(), "LOG_{}_{}.csv".format(current_date, current_minute))
    with open(csv_filename, "a", newline="") as file:
        write = csv.writer(file)
        write.writerow(status)
        file.close()

def write_to_osuDB(status):
    with open('OSU_db.csv', "a", newline="") as file:
        write = csv.writer(file)
        write.writerow(status)
        file.close()

ip_file_name = "ip_add_database.csv"
APLCRC_INIT_VALUE = 0xFFFF
APLCRC_POLYNOMIAL = 0xA001  # Polynomial for CRC16-CCITT
_CrcTable = [0]*256

def APLCRC_Init():
    remainder = 0
    dividend = 0
    # bit = 8

    for dividend in range(256):
        remainder = dividend
        for bit in range(8,0,-1):
            if remainder & 1:
                remainder = (remainder >> 1) ^ APLCRC_POLYNOMIAL
            else:
                remainder >>= 1
        _CrcTable[dividend] = remainder
    # print(dividend) 
    
def APLCRC_Calc(_buffer,length):
    APLCRC_Init()
    _crcVal = APLCRC_INIT_VALUE

    for byte in range(length):
    # /* crc value xor with element */
        _data = (_crcVal ^ _buffer[byte]) & 0xFF
        _crcVal = _CrcTable[_data] ^ (_crcVal >> 8)
    # print(_CrcTable[_data])
    return(_crcVal)

def getUpdateData(): # 161,1 
    """
    Connect to socket and send command in form of bytes ,
    then SLSC checks the command and send the response (in bytes) according to commmand
    Recv data and check their is no data missing, by checking crc and len of data

    Args:
        slscRecvData (bytes): Data recieved in response of command send via socket
        crc (int) : crc check of recieved data
        recvData : data to upload in Gui

    Returns:
    res (list[str]): Recieved data from slsc

    """
    updateCmd = bytearray([161, 1])
    addCrc = APLCRC_Calc(updateCmd,len(updateCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    updateCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(updateCmd)
    # print("SEND :", updateCmd)
    slscRecvData = s.recv(150)
    satName = slscRecvData[2:14].decode('utf-8').rstrip('\x00')
    # print(slscRecvData[14], slscRecvData[15], slscRecvData[16], slscRecvData[17],
                # slscRecvData[18], slscRecvData[19], slscRecvData[20], slscRecvData[21], slscRecvData[22], slscRecvData[23], slscRecvData[24])
    # print( 'len data recv :', len(slscRecvData) )
    try:
        result_list = [satName,slscRecvData[14], slscRecvData[15], slscRecvData[16], slscRecvData[17],
                slscRecvData[18], slscRecvData[19], slscRecvData[20], slscRecvData[21], slscRecvData[22], slscRecvData[23], slscRecvData[24] ]
        # print(len(slscRecvData))
        if len(slscRecvData)==140:
            for i in range(26, len(slscRecvData)-2, 4):
                # print(i)
                data = ((slscRecvData[i]&0xff) )|((slscRecvData[i+1]<<8)&0xff00) | ((slscRecvData[i+2]<<16)&0xff0000) | ((slscRecvData[i+3]<<24)&0xff000000)
                result_list.append(float(ctypes.c_int(data).value/100))
                # write_to_slscStatusLog(result_list)
            result_list.append(slscRecvData[25]) # demo flag
            # print(result_list, len(result_list), result_list[29], result_list[30], result_list[31], result_list[32])
        else:
            result_list=[]
        return result_list
    except:
        
        # command_instance = commands()
        # command_instance.resetWiz()     
        print('exception')
    s.close()
    # print('close')
# while True:
#     getUpdateData()
#     time.sleep(0.5)
def getLockSatellite(): # 161,2 
    """Description of getLockSatellite
    Args :
        s : call connect_to slsc method to create socket
        get_sat : recv locked satellite from SLSC
    Returns :
        satellite_name : recieved satellite name
    """
    getLockSatCmd = bytearray([161, 2])
    addCrc = APLCRC_Calc(getLockSatCmd,len(getLockSatCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    getLockSatCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(getLockSatCmd)
    get_sat = s.recv(1000)
    # print(get_sat)
    appendedCrc = ((get_sat[-2] << 8)&0xff00 | get_sat[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(get_sat,len(get_sat)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        get_sat=get_sat[2:14].decode('utf-8')
        # print('get satellite : ',get_sat)
    else:
        get_sat='NO SATELLITE LOCKED'
        # print('*')
    return get_sat

def setLockSatellite(satinfo): # 177, 1
    # satinfo= ['GSAT-10', '11697.5', '0', '25', '90']
    satname = satinfo[0].encode('UTF-8')  # Encode 'GSAT-7' to bytes
    satname = satname.ljust(12, b'\x00')  # Pad with zero bytes to make it 12 bytes long
    # freq= 11697.50
    freqBytes = int(float(satinfo[1])*100).to_bytes(4, byteorder='big', signed=True)
    # lat= -19.05
    latBytes = int(float(satinfo[2])*100).to_bytes(4, byteorder='big', signed=True)
    # longitude = 74.12  # Example negative and floating-point longitude
    # long_int = int(longitude * 100)  # Multiply by 100 for two decimal places
    longBytes = int(float(satinfo[3])*100).to_bytes(4, byteorder='big', signed=True)  # Use signed format
    # pol = 24.25
    polBytes= int(int(float(satinfo[4])*100)).to_bytes(4, byteorder='big', signed=True)
    allSatInfo= satname+freqBytes+latBytes+longBytes+polBytes
    # print(satinfo,freqBytes, latBytes, longBytes, polBytes)
    setLockSatCmd = bytearray([177, 1])
    cmd = setLockSatCmd + allSatInfo
    addCrc = APLCRC_Calc(cmd,len(cmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    cmd.extend([CRC1, CRC2])
    # print(cmd)
    s = connectToSlsc()
    s.sendall(cmd)
    recvSetSatStatus = s.recv(1000)
    try:
        appendedCrc = ((recvSetSatStatus[-2] << 8)&0xff00 | recvSetSatStatus[-1])
        # print('LAST BYTES : ',f'{appendedCrc:04X}')
        crc_data = APLCRC_Calc(recvSetSatStatus,len(recvSetSatStatus)-2)
        # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
        if appendedCrc-crc_data==0:
            response = recvSetSatStatus[2]
            # print(response)
        else:
            response=0
            print('*')
    except:
        print('incomplte recv set satellite set')
    return response

def setSafemode(): # 177, 2
    safeModeCmd = bytearray([177, 2])
    addCrc = APLCRC_Calc(safeModeCmd,len(safeModeCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    safeModeCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(safeModeCmd)
    recvSafeModetStatus = s.recv(1000)
    appendedCrc = ((recvSafeModetStatus[-2] << 8)&0xff00 | recvSafeModetStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(recvSafeModetStatus,len(recvSafeModetStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = recvSafeModetStatus[2]
    else:
        response=0
        print('*')
    return response

def releaseSafemode(): # 177, 3
    safeModeReleaseCmd = bytearray([177, 3])
    addCrc = APLCRC_Calc(safeModeReleaseCmd,len(safeModeReleaseCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    safeModeReleaseCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(safeModeReleaseCmd)
    recvSafeModetStatus = s.recv(1000)
    appendedCrc = ((recvSafeModetStatus[-2] << 8)&0xff00 | recvSafeModetStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(recvSafeModetStatus,len(recvSafeModetStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = recvSafeModetStatus[2]
    else:
        response=0
        print('*')
    return response

def setHomePosition(): # 177, 4
    homeCmd = bytearray([177, 4])
    addCrc = APLCRC_Calc(homeCmd,len(homeCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    homeCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(homeCmd)
    recvHomePosStatus = s.recv(1000)
    appendedCrc = ((recvHomePosStatus[-2] << 8)&0xff00 | recvHomePosStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(recvHomePosStatus,len(recvHomePosStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response= recvHomePosStatus[2]
    else:
        response= 0
        print('*')
    return response

def releaseHomePosition():# 177, 5
    homeReleaseCmd = bytearray([177, 5])
    addCrc = APLCRC_Calc(homeReleaseCmd,len(homeReleaseCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    homeReleaseCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(homeReleaseCmd)
    recvHomePosStatus = s.recv(1000)
    appendedCrc = ((recvHomePosStatus[-2] << 8)&0xff00 | recvHomePosStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(recvHomePosStatus,len(recvHomePosStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response= recvHomePosStatus[2]
    else:
        response=0
        print('*')
    return response

def TxMute():# 177, 6
    TxMuteCmd = bytearray([177, 6])
    addCrc = APLCRC_Calc(TxMuteCmd,len(TxMuteCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    TxMuteCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(TxMuteCmd)
    print('send')
    TxMuteStatus = s.recv(1000)
    
    appendedCrc = ((TxMuteStatus[-2] << 8)&0xff00 | TxMuteStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(TxMuteStatus,len(TxMuteStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = TxMuteStatus[2]
    else:
        response=0
        print('*')
    return response

def txUnmute():# 177, 7
    TxUnmuteCmd = bytearray([177, 7])
    addCrc = APLCRC_Calc(TxUnmuteCmd,len(TxUnmuteCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    TxUnmuteCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(TxUnmuteCmd)
    TxUnmuteStatus = s.recv(1000)
    appendedCrc = ((TxUnmuteStatus[-2] << 8)&0xff00 | TxUnmuteStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(TxUnmuteStatus,len(TxUnmuteStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = TxUnmuteStatus[2]
    else:
        response=0
        print('*')
    return response

def setRestart():# 177, 8
    setRestartCmd = bytearray([177, 8])
    addCrc = APLCRC_Calc(setRestartCmd,len(setRestartCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    setRestartCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(setRestartCmd)
    restartStatus = s.recv(1000)
    appendedCrc = ((restartStatus[-2] << 8)&0xff00 | restartStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(restartStatus,len(restartStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = restartStatus[2]
    else:
        response=0
        print('*')
    return response

def setShutdown():# 177, 9
    setShutdownCmd = bytearray([177, 9])
    addCrc = APLCRC_Calc(setShutdownCmd,len(setShutdownCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    setShutdownCmd.extend([CRC1, CRC2])
    s = connectToSlsc()
    s.sendall(setShutdownCmd)
    shutdownStatus = s.recv(1000)
    appendedCrc = ((shutdownStatus[-2] << 8)&0xff00 | shutdownStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(shutdownStatus,len(shutdownStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = shutdownStatus[2]
    else:
        response=0
        print('*')
    return response

def setManual(manualParametrs):# 177, 9
    setManualCmd = bytearray([177, 10])
    setManualCmd= setManualCmd + manualParametrs
    addCrc = APLCRC_Calc(setManualCmd,len(setManualCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    setManualCmd.extend([CRC1, CRC2])
    # print('cmd  : ',setManualCmd, len(setManualCmd))
    s = connectToSlsc()
    s.sendall(setManualCmd)
    # print('cmd  : ',setManualCmd, len(setManualCmd))
    shutdownStatus = s.recv(1000)

    appendedCrc = ((shutdownStatus[-2] << 8)&0xff00 | shutdownStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(shutdownStatus,len(shutdownStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = shutdownStatus[2]
        # print('response manual mode : ', response)
    else:
        response=0
        print('*')
    return response

def setDemoMode():# 177, 9
    setAutoCmd = bytearray([177, 11])
    addCrc = APLCRC_Calc(setAutoCmd,len(setAutoCmd))
    CRC1 = addCrc >> 8  # High byte
    CRC2 = addCrc & 0xFF # Low byte
    setAutoCmd.extend([CRC1, CRC2])
    # print('cmd  : ',setManualCmd, len(setManualCmd))
    s = connectToSlsc()
    s.sendall(setAutoCmd)
    # print('cmd  : ',setManualCmd, len(setManualCmd))
    autoStatus = s.recv(1000)
    # print(autoStatus)
    appendedCrc = ((autoStatus[-2] << 8)&0xff00 | autoStatus[-1])
    # print('LAST BYTES : ',f'{appendedCrc:04X}')
    crc_data = APLCRC_Calc(autoStatus,len(autoStatus)-2)
    # print('calculated crc(without appended crc) : ',f'{crc_data:04X}')
    if appendedCrc-crc_data==0:
        response = autoStatus[2]
        print('response manual mode : ', response)
    else:
        response=0
        print('*')
    return response

broadcastaddr = '255.255.255.255' 
port = 50001
def udpSocket():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(0.5)
    return udp_socket

class commands:
    def __init__(self) -> None:
        self.ma = [ord('M'),ord('A')]  # ma = [0x4D, 0x41]
        self.macBroadcast =[ 0xff,0xff,0xff,0xff,0xff,0xff]
        self.pw = [ord('P'),ord('W')] # [0x50, 0x57] # password
        self.password = [ord('A'), ord('.'), ord('1'), ord('#')] # [0x41]
        self.mc= [ord('M'),ord('C')] # Check product’s MAC address
        self.vr = [ord('V'),ord('R')] # Check the product’s firmware version
        self.li = [ord('L'),ord('I')] # Product's IP address
        self.crlf = [ord('\r'),ord('\n')] #[0x0D, 0x0A]
        self.lp = [ord('L'),ord('P')] # Product’s port number
        self.st = [ord('S'),ord('T')] # Check the product operation status
        self.save= [ord('S'),ord('V')] # Save changed settings
        self.reset= [ord('R'),ord('T')] # Device reboot
        self.pt= [ord('P'),ord('T'), ord('2'), ord('0'), ord('0')]#  Data packing of serial interface (Data UART) – Data size delimiter 0: Not used / 1 ~ 65535: Data packing time (Unit: millisecond)
        self.ps= [ord('P'),ord('S')] #  DATA SIZE ,Data packing of serial interface (Data UART) – Data size delimiter 0: Not used / 1 ~ 255: Data packing size (Unit: byte)
        self.gw =  [ord('G'),ord('W')] # Product’s gateway address
        self.ds = [ord('D'),ord('S')] # Product’s DNS address
        self.sm = [ord('S'),ord('M')] # Product’s subnet mask

    def wizGetInfo(self):
        lst2 = [self.ma , self.macBroadcast, self.crlf, self.pw,self.crlf,self.mc, self.crlf, 
                self.vr,self.crlf ,self.li , self.crlf, self.lp , self.crlf, self.st , self.crlf, self.ps , self.crlf]
        getParaCmd = [item for sublist in lst2 for item in sublist]
        recvDataList=[]
        all_data=[]
        try:
            udpSock= udpSocket()
            udpSock.sendto(bytearray(getParaCmd), (broadcastaddr, port))
            print('Broadcasted:', bytearray(getParaCmd))
            data = udpSock.recv(1024)
            print('recv : ',data)
            replylists = data.split(b"\r\n")
            if len(data)>0:
                for i in range(0, len(replylists)):
                    if b'MC' in replylists[i]:
                        recvDataList.append(replylists[i][2:])
                    # if b'VR' in replylists[i]:
                    #     recvDataList.append(replylists[i][2:])
                    if b'LI' in replylists[i]:
                        recvDataList.append(replylists[i][2:])
                    if b'LP' in replylists[i]:
                        recvDataList.append(replylists[i][2:])
                for i in range(len(recvDataList)):
                    all_data.append(recvDataList[i].decode())
            print(recvDataList)
        except Exception as e:
            print("Error:", e)
        finally:
            udpSock.close()
        return all_data
    
    def broadcastSetIp(self, newIp,newPort, subnetMask,gatway, dnsServer ):
        # newIp= "192.168.13.62"
        # newPort="999"
        # subnetMask= "255.255.255.0"
        # gatway="192.168.13.1"
        # dnsServer="192.168.13.1"
        wiz = commands()
        macAdd= bytes.fromhex(wiz.wizGetInfo()[0].replace(':', ''))
        ipLst, portlst , sublist, gatewayList, dnsList= [], [], [], [], []
        ipLst[:], portlst[:], sublist[:] , gatewayList[:] , dnsList[:]= newIp, newPort , subnetMask, gatway, dnsServer
        password = [ord('A')] # [0x41]
        self.ip = [ord(char) for word in ipLst for char in word]
        self.port_change = [ord(char) for word in portlst for char in word]
        self.sbMaskSet= [ord(sb) for word in sublist for sb in word]
        self.gatewaySet= [ord(gw) for word in gatewayList for gw in word]
        self.dnsServerSet= [ord(dn) for word in dnsList for dn in word]
        self.data_size =[ord('1'),ord('5'),ord('0')]
        self.macc= bytearray(item for item in self.ma)+macAdd+bytearray(item for item in self.crlf)
        lst = [self.pw, self.crlf,self.sm, self.sbMaskSet,self.crlf, self.gw, self.gatewaySet, self.crlf,
               self.ds, self.dnsServerSet, self.crlf,self.li, self.ip, self.crlf, self.lp, self.port_change,
               self.crlf,self.ps, self.data_size,  self.crlf, self.pt, self.crlf,self.save, self.crlf, self.reset, self.crlf]
        ipPortCmd =self.macc + bytearray([item for sublist in lst for item in sublist])
        print(ipPortCmd)
        # print(bytearray(ipPortCmd))
        try:
            # print(ipLst[:], portlst[:])
            udpSock= udpSocket()
            udpSock.sendto(bytearray(ipPortCmd), (broadcastaddr, port))
            # print('Broadcasted:', bytearray(ipPortCmd))
            data = udpSock.recv(1024)
            print('recv : ',data)

        except Exception as e:
            print("Error:", e)
        finally:
            udpSock.close()
    
    def resetWiz(self):
        lst = [self.ma, self.mac, self.crlf, self.pw, self.crlf,  self.reset, self.crlf]
        ipPortCmd = [item for sublist in lst for item in sublist]
        print(ipPortCmd)
        try:
            udpSock= udpSocket()
            udpSock.sendto(bytearray(ipPortCmd), (broadcastaddr, port))
            print('Broadcasted:', bytearray(ipPortCmd))
            data = udpSock.recv(1024)
            print('recv : ',data, type(data[0:1]))

        except Exception as e:
            print("Error:", e)
        finally:
            udpSock.close()
        time.sleep(0.1)
        print('END')


           # getUpdateData()

# wiz = commands()
# wiz.broadcastSetIp()