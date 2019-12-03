

import socket
import sys
import os
import random
from math import *
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QFileDialog, QPushButton, \
QLineEdit, QTableWidgetItem, QMessageBox, QProgressBar, QMenu, QAbstractItemView, QListView, QListWidget, QListWidgetItem
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal, QSize
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon

from Constants import Constants



class MainClient(QObject):
    '''
    描述：pyqt主客户端, 类似FTP客户端
    '''
    InitializeFinished = pyqtSignal()


    def __init__(self):
        '''
        描述：构造函数
        参数：无
        '''
        super(QObject,self).__init__()

        #ip，端口等
        self.IP = "127.0.0.1"
        self.ClientControlPort = Constants.UNDEFINED_NUMBER
        self.ClientDataPort = self.GenerateRandomPort()
        self.ServerIP = Constants.SERVER_ADDR
        self.ServerControlPort = Constants.MAIN_SERVER_CONTROL_PORT

        #连接
        self.ControlSocket = None
        self.ListenSocket = None
        self.DataSocket = None

        #文件
        self.FileName = "kebab.jpg"
        self.SaveDir = "Info"
        self.PictureBack = ".jpg"
        self.SubtitleBack = ".srt"

        #文件列表
        self.PlayList = []
        self.DownloadList = []
        self.DownloadPlace = 0
        #元素：文件名，时长，已经播放时长，帧数，已经播放帧数，是否有字幕

        #状态
        self.WhetherPlaying = False
        self.Valid = True
        self.WhetherSendingFinished = False
        self.WhetherSendingSuccess = True
        self.RequestSent = ""


        #session，seq等
        self.ControlSequence = 0
        self.Session = Constants.UNDEFINED_NUMBER

        #初始化ui
        self.MainWindow = loadUi("mainwindow.ui")
        self.ConnectToServer()
        self.OpenDataPort()
        self.SetupLink()
        

        
        self.ConnectSignalAndSlot()
    
    def ConnectSignalAndSlot(self):
        '''
        描述：连接各种信号和槽
        参数：无
        返回：无
        '''
        self.InitializeFinished.connect(self.InitializeGUI)
        '''
        self.MainWindow.FileListTable.setSelectionBehavior(QAbstractItemView.SelectRows) ###设置一次选中一行
        self.MainWindow.FileListTable.setEditTriggers(QAbstractItemView.NoEditTriggers) ###设置表格禁止编辑
        self.MainWindow.FileListTable.setContextMenuPolicy(Qt.CustomContextMenu)######允许右键产生子菜单
        self.MainWindow.FileListTable.customContextMenuRequested.connect(self.GenerateMenu)   ####右键菜单
        
        self.LoginWindow.LoginButton.clicked.connect(self.InitAndLogin)
        self.MainWindow.RefreshButton.clicked.connect(self.RefreshPath)
        self.MainWindow.RefreshButton.clicked.connect(self.GetFileList)
        self.MainWindow.QuitButton.clicked.connect(self.Disconnect)
        self.MainWindow.GoToButton.clicked.connect(self.ChangeDir)
        self.MainWindow.NewButton.clicked.connect(self.MakeDir)
        self.MainWindow.BackButton.clicked.connect(self.GoBack)
        self.MainWindow.RootButton.clicked.connect(self.ChangeToRoot)
        self.MainWindow.UploadButton.clicked.connect(self.ShowUploadDialog)

        self.MainWindow.DownloadTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.MainWindow.UploadTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        '''

	#网络连接相关操作，包括数据端口连接服务器，控制端口开启等
    def ConnectToServer(self):
        '''
        描述：控制连接服务器
        参数：无
        返回：无
        '''	
        self.ControlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.ControlSocket.connect((self.ServerIP, self.ServerControlPort))
        except:
            QMessageBox.warning(self.MainWindow,'Connection Fail',"Unable to connect to the Server",QMessageBox.Yes)	


    def OpenDataPort(self):
        '''
        描述：开启数据端口，接收服务器数据
        参数：无
        返回：无
        '''	
        self.ListenSocket = socket.socket()
        try:
            self.ListenSocket.bind(("", self.ClientDataPort))
            self.ListenSocket.listen(5)
        except:
            QMessageBox.warning(self.MainWindow,'Connection Fail',"Unable to bind the data port",QMessageBox.Yes)

    def CloseDataPort(self):
        '''
        描述：关闭数据端口
        参数：无
        返回：无
        '''	
        try:
            self.DataSocket.shutdown(socket.SHUT_RDWR)
            self.DataSocket.close()
        except:
            donothing = True

	#绑定事件处理相关操作，包括建立连接，获取文件列表，建立数据连接，下载文件，关闭客户端
    def SetupLink(self):
        '''
        描述：Setup操作
        参数：无
        返回：无
        '''		
        self.SendControlRequest("SETUP")
	
    def TearDownLink(self):
        '''
        描述：Teardown操作，关闭连接
        参数：无
        返回：无
        '''	
        self.SendControlRequest("TEARDOWN")		

         
    def GetPlayList(self):
        '''
        描述：获取视频文件列表
        参数：无
        返回：无
        '''	
        self.SendControlRequest("LIST")

    def BeforeDownload(self):
        '''
        描述：下载一个文件前做好准备
        参数：无
        返回：无
        '''	
        self.WhetherSendingFinished = False
        self.SendControlRequest("PORT")

    def DownloadFile(self):
        '''
        描述：下载一个文件
        参数：无
        返回：无
        '''	
        self.SendControlRequest("RETR")


	#控制连接相关函数，包括发送请求，处理收到的回复，处理请求等
    def SendControlRequest(self, TheRequestType):
        '''
        描述：向服务器发送控制请求
        参数：请求类型
        返回：无
        '''	
        if TheRequestType == "SETUP":
            self.ControlSequence += 1
            threading.Thread(target = self.ReceiveControlReply).start()
            TheRequest = 'SETUP ' + self.FileName + ' RTSP/1.0\n' \
            + 'CSeq: ' + str(self.ControlSequence) + \
            '\nTransport: TCP; client_port= ' + str(self.ClientDataPort)
            self.RequestSent = "SETUP"
		
        elif TheRequestType == "LIST":
            self.ControlSequence += 1
            TheRequest = 'LIST ' + self.FileName + ' RTSP/1.0\n' \
            + 'CSeq: ' + str(self.ControlSequence) \
            + '\nSession: ' + str(self.Session)
            self.RequestSent = "LIST"

        elif TheRequestType == "PORT":
            self.ControlSequence += 1
            TheRequest = 'PORT ' + self.FileName + ' RTSP/1.0\n' \
            + 'CSeq: ' + str(self.ControlSequence) \
            + '\nSession: ' + str(self.Session)
            self.RequestSent = "PORT"

        elif TheRequestType == "RETR":
            self.ControlSequence += 1
            TheRequest = 'RETR ' + self.FileName + ' RTSP/1.0\n' \
            + 'CSeq: ' + str(self.ControlSequence) \
            + '\nSession: ' + str(self.Session)
            self.RequestSent = "RETR"
		
        elif TheRequestType == "TEARDOWN":
            self.ControlSequence += 1
            TheRequest = 'TEARDOWN ' + self.FileName + ' RTSP/1.0\n' \
            + 'CSeq: ' + str(self.ControlSequence) \
            + '\nSession: ' + str(self.Session)
            self.RequestSent = "TEARDOWN"
        else:
            return
        self.ControlSocket.send(TheRequest.encode())		
        print(TheRequest)
        print("-----------------------------")

	
    def ReceiveControlReply(self):
        '''
        描述：接收服务器的控制连接回复
        参数：无
        返回：无
        '''	
        while True:
            TheReply = self.ControlSocket.recv(Constants.CONTROL_SIZE)
            print(TheReply.decode("utf-8"))
            print("-----------------------------")
            if TheReply: 
                self.HandleControlReply(TheReply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.RequestSent == "TEARDOWN":
                try:
                    self.ControlSocket.shutdown(socket.SHUT_RDWR)
                    self.ControlSocket.close()
                except:
                    donothing = True
                break
	
    def HandleControlReply(self, TheReply):
        '''
        描述：处理服务器的控制连接回复
        参数：回复内容
        返回：无
        '''	
        Lines = str(TheReply).split('\n')
        TheSequenceNum = int(Lines[1].split()[1])
		
        # Process only if the server reply's sequence number is the same as the request's
        if TheSequenceNum == self.ControlSequence:
            TheSession = int(Lines[2].split()[1])
            # New RTSP session ID
            if self.Session == Constants.UNDEFINED_NUMBER:
                self.Session = TheSession
			
            # Process only if the session ID is the same
            if self.Session == TheSession:
                if int(Lines[0].split()[1]) == Constants.STATUS_CODE_SUCCESS: 
                    if self.RequestSent == "SETUP":
                        self.GetPlayList()
                        self.InitDir()
                    elif self.RequestSent == "LIST":
                        self.SetPlayList(str(TheReply))
                        self.GetAllFiles()
                    elif self.RequestSent == "PORT":
                        self.DownloadFile()
                        threading.Thread(target = self.DataLinkReceive).start()
                    elif self.RequestSent == "TEARDOWN":
                        self.Valid = False
                        self.InitializeFinished.emit()
                else:
                    if self.RequestSent == "PORT":
                        self.WhetherSendingFinished = True
                        self.WhetherSendingSuccess = False
                        if self.DownloadPlace % 2 == 0:
                            self.PlayList[round(self.DownloadPlace / 2)]["WhetherHasSubtitle"] = False
                        self.DownloadPlace += 1
                        self.ControlDownloadOne()

	#数据连接部分：接收数据，存储在文件里
    def DataLinkReceive(self):		
        '''
        描述：处理服务器的控制连接回复
        参数：回复内容
        返回：无
        '''	
        self.DataSocket, Address = self.ListenSocket.accept()
        self.DataSocket.settimeout(0.5)
        print("Accepted the link of ", Address)
        TheData = self.DataSocket.recv(Constants.DATA_PACKET_SIZE)
        self.WriteFile(TheData)
        print("Dropped the link of ", Address)
        self.CloseDataPort()
        if self.DownloadPlace % 2 == 0:
            self.PlayList[round(self.DownloadPlace / 2)]["WhetherHasSubtitle"] = True
        self.DownloadPlace += 1
        self.ControlDownloadOne()

					
    def WriteFile(self, TheData):
        '''
        描述：写入文件
        参数：数据内容
        返回：无
        '''	
        TheCacheName = self.GetCacheFileName()
        File = open(TheCacheName, "ab")
        File.write(TheData)
        File.close()

    #获取和下载全部文件
    def SetPlayList(self, TheReply):
        '''
        描述：解析文件列表和数据
        参数：待解析的数据内容
        返回：无
        '''	
        Lines = TheReply.split('\n')
        TheFileList = Lines[3].split()
        TheItem = {}
        for i in range(len(TheFileList)):
            if i % 3 == 0:
                TheItem["FileName"] = TheFileList[i]
            elif i % 3 == 1:
                TheItem["TotalFrameNumber"] = int(TheFileList[i])
                TheItem["CurrentFrameNumber"] = 0
            else:
                TheItem["TotalTime"] = self.GetPlayTime(TheItem["TotalFrameNumber"], int(TheFileList[i]))
                TheItem["CurrentTime"] = self.GetPlayTime(0, int(TheFileList[i]))
                self.PlayList.append(TheItem)
                TheItem = {}
        #print(self.PlayList)

    def GetAllFiles(self):
        '''
        描述：控制从服务器下载全部文件
        参数：数据内容
        返回：无
        '''
        for item in self.PlayList:
            ThePictureName = self.GetDownloadFileName(item["FileName"], True)
            TheSubtitleName = self.GetDownloadFileName(item["FileName"], False)
            self.DownloadList.append(TheSubtitleName)
            self.DownloadList.append(ThePictureName)
        print(self.DownloadList)
        self.ControlDownloadOne()

    def ControlDownloadOne(self):
        '''
        描述：控制从服务器下载一个文件
        参数：数据内容
        返回：无
        '''
        time.sleep(0.01)
        if self.DownloadPlace >= len(self.DownloadList):
            self.TearDownLink()
            return
        self.FileName = self.DownloadList[self.DownloadPlace]
        self.BeforeDownload()

    #基本操作函数，比如随机生成端口，生成完整文件名
    def InitDir(self):
        if os.path.exists(self.SaveDir) == False:
            os.mkdir(self.SaveDir)
        if os.path.exists(self.SaveDir + '/' + str(self.Session)) == False:
            os.mkdir(self.SaveDir + '/' + str(self.Session))

    def GenerateRandomPort(self):	
        '''
        描述：生成随机的自身数据端口
        参数：无
        返回：一个随机数port
        '''
        ThePort = random.randint(10001, 65535)
        return ThePort

    def GetCacheFileName(self):
        '''
        描述：根据session，前缀等生成图片，字幕文件名
        参数：无
        返回：文件名
        '''
        TheFileName = self.SaveDir + '/' + str(self.Session) + '/' + self.FileName
        return TheFileName

    def GetDownloadFileName(self, TheFileName, Type):
        '''
        描述：生成待下载的图片，字幕文件名
        参数：无
        返回：文件名
        '''
        Back = ""
        if Type == True:
            Back = self.PictureBack
        else:
            Back = self.SubtitleBack
        TheFileNameDownload = TheFileName[0:-4] + Back
        return TheFileNameDownload
    
    def GetIconFileName(self, TheFileName):
        return self.SaveDir + '/' + str(self.Session) + '/' + TheFileName[0:-4] + self.PictureBack

    def GetSubtitleFileName(self, TheFileName):
        return self.SaveDir + '/' + str(self.Session) + '/' + TheFileName[0:-4] + self.SubtitleBack

    def GetPlayTime(self, TheFrameNumber, TheFramePerSecond):
        '''
        描述：根据播放帧数计算播放时间
        参数：帧数,帧率
        返回：字符串，代表时间
        '''
        TotalSecond = round(TheFrameNumber / TheFramePerSecond)
        TheHour = floor(TotalSecond / 3600)
        TheMinute = floor((TotalSecond - TheHour * 3600) / 60)
        TheSecond = TotalSecond % 60
        TheString = str(TheHour) + ":" + str(TheMinute).zfill(2) + ":" + str(TheSecond).zfill(2)
        return TheString

    #GUI相关函数
    def InitializeGUI(self):
        #self.MainWindow.show()
        self.InitializePlayList()
        self.MainWindow.show()



    def InitializePlayList(self):
        self.MainWindow.VideoList.setViewMode(QListView.IconMode)
        self.MainWindow.VideoList.setIconSize(QSize(200,200))
        self.MainWindow.VideoList.setSpacing(12)
        for item in self.PlayList:
            NewItem = QListWidgetItem()
            TheIconName = self.GetIconFileName(item["FileName"])
            NewItem.setIcon(QIcon(TheIconName))
            NewItem.setText(item["FileName"])
            self.MainWindow.VideoList.addItem(NewItem)

class ListWidget(QListWidget):
    def clicked(self, item):
        QMessageBox.information(self, "ListWidget", "你选择了: " + item.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    TheClient = MainClient()
    sys.exit(app.exec_())





    '''app = QApplication(sys.argv)
    #实例化对象，目的只是单纯的使用里面的槽函数............
    listWidget = ListWidget()
    listWidget.setViewMode(QListView.IconMode)
    listWidget.setIconSize(QSize(100,100))
    listWidget.setSpacing(12)
    item1 = QListWidgetItem()
    item1.setIcon(QIcon('奥利给.jpg'))
    item1.setText("马克思")
    item2 = QListWidgetItem()
    item2.setIcon(QIcon('奥利给.jpg'))
    item2.setText("奥利给")
    item3 = QListWidgetItem()
    item3.setIcon(QIcon('奥利给.jpg'))
    item3.setText("影流之主")

    #设置初始大小，增加条目，设置标题
    listWidget.resize(300, 120)
    listWidget.addItem(item1)
    listWidget.addItem(item2)
    listWidget.addItem(item3)
    listWidget.setWindowTitle('QListwidget 例子')

    #单击触发绑定的槽函数
    listWidget.itemClicked.connect(listWidget.clicked)


    listWidget.show()
    sys.exit(app.exec_())'''
