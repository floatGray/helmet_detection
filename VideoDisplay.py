import cv2
import threading
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QCoreApplication, QSize
import os.path
import datetime
import time
from YOLOIdent import UseYOLO


class Display:
    def __init__(self, ui, mainWnd):
        self.ui = ui
        self.mainWnd = mainWnd
        # 信号槽设置

        ui.Last.clicked.connect(self.Last)
        ui.Next.clicked.connect(self.Next)

        ui.min.clicked.connect(mainWnd.showMinimized)
        ui.close.clicked.connect(QCoreApplication.instance().quit)

        ui.CamButton.clicked.connect(self.Stop)
        ui.FileButton.clicked.connect(self.Stop)
        ui.PicButton.clicked.connect(self.Stop)
        ui.PicsButton.clicked.connect(self.Stop)

        ui.CamButton.clicked.connect(self.ShowCam)
        ui.FileButton.clicked.connect(self.ShowFile)
        ui.PicButton.clicked.connect(self.ShowPic)
        ui.PicsButton.clicked.connect(self.ShowPics)

        ui.slider.valueChanged.connect(self.valuechange)

        self.old = 0
        # 创建一个关闭事件并设为未触发
        self.stopEvent = threading.Event()
        self.stopEvent.clear()

        self.YOLOIdent = UseYOLO()
        self.StartTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.RealFPS = 0  # 既保存实际fps，还是是否已经存在display视频线程的标志位
        self.num = 0
        self.i = 0

    def valuechange(self):
        print(self.mode)
        print(self.ui.slider.value())
        if self.mode == 2:
            print("d")
            self.position = self.ui.slider.value() * self.FPS
            # print(self.ui.slider.value())
            # print(self.FPS)
            # print(self.position)
        elif self.mode == 4:
            self.i = self.ui.slider.value() - 1
            self.ui.DispalyLabel.setPixmap(self.PicOutList[self.i])
            self.ui.NumHatLabel.setText("戴帽子的人数：" + self.Num[self.i][0])
            self.ui.NumPersonLabel.setText("没戴的人数： " + self.Num[self.i][1])

    # 线程在执行self.Display()时，函数self.ShowFile()或self.ShowCam()仍在运行
    # 不能同时运行两个同一函数。所以self.stopEvent.set()要写在另一个函数self.Stop()里
    def Stop(self):
        self.ui.slider.hide()
        self.ui.Last.hide()
        self.ui.Next.hide()
        # 若实际fps是初始值0，则set会直接cap.release
        if self.RealFPS != 0:
            # 关闭事件设为触发，关闭视频播放
            self.stopEvent.set()

    def ChangeMode(self, mode):
        self.mode = mode
        if self.old == 1:
            cam1 = QIcon()
            cam1.addPixmap(QPixmap("icon/cam1.png"), QIcon.Normal, QIcon.Off)
            self.ui.CamButton.setIcon(cam1)
            self.ui.CamButton.setIconSize(QSize(20, 20))
            # self.ui.CamButton.setObjectName("ChooseButton1")
            self.ui.CamButton.setStyleSheet(
                'background-color:#2B3743;''color:#4CB28A;''font-size:16px;''border-radius:23px;')
        elif self.old == 2:
            video1 = QIcon()
            video1.addPixmap(QPixmap("icon/video1.png"), QIcon.Normal, QIcon.Off)
            self.ui.FileButton.setIcon(video1)
            self.ui.FileButton.setIconSize(QSize(20, 20))
            # self.ui.FileButton.setObjectName("ChooseButton1")
            self.ui.FileButton.setStyleSheet(
                'background-color:#2B3743;''color:#4CB28A;''font-size:16px;''border-radius:23px;')
        elif self.old == 3:
            pic1 = QIcon()
            pic1.addPixmap(QPixmap("icon/pic1.png"), QIcon.Normal, QIcon.Off)
            self.ui.PicButton.setIcon(pic1)
            self.ui.PicButton.setIconSize(QSize(20, 20))
            # self.ui.PicButton.setObjectName("ChooseButton1")
            self.ui.PicButton.setStyleSheet(
                'background-color:#2B3743;''color:#4CB28A;''font-size:16px;''border-radius:23px;')
        elif self.old == 4:
            pics1 = QIcon()
            pics1.addPixmap(QPixmap("icon/pics1.png"), QIcon.Normal, QIcon.Off)
            self.ui.PicsButton.setIcon(pics1)
            self.ui.PicsButton.setIconSize(QSize(20, 20))
            # self.ui.PicsButton.setObjectName("ChooseButton1")
            self.ui.PicsButton.setStyleSheet(
                'background-color:#2B3743;''color:#4CB28A;''font-size:16px;''border-radius:23px;')
        self.old = self.mode
        if self.mode == 1:
            cam2 = QIcon()
            cam2.addPixmap(QPixmap("icon/cam2.png"), QIcon.Normal, QIcon.Off)
            self.ui.CamButton.setIcon(cam2)
            self.ui.CamButton.setIconSize(QSize(20, 20))
            # self.ui.CamButton.setObjectName("ChooseButton2")
            self.ui.CamButton.setStyleSheet(
                'background-color:#4CB28A;''color:#2B3743;''font-size:16px;''border-radius:23px;')
        elif self.mode == 2:
            video2 = QIcon()
            video2.addPixmap(QPixmap("icon/video2.png"), QIcon.Normal, QIcon.Off)
            self.ui.FileButton.setIcon(video2)
            self.ui.FileButton.setIconSize(QSize(20, 20))
            # self.ui.FileButton.setObjectName("ChooseButton2")
            self.ui.FileButton.setStyleSheet(
                'background-color:#4CB28A;''color:#2B3743;''font-size:16px;''border-radius:23px;')
        elif self.mode == 3:
            pic2 = QIcon()
            pic2.addPixmap(QPixmap("icon/pic2.png"), QIcon.Normal, QIcon.Off)
            self.ui.PicButton.setIcon(pic2)
            self.ui.PicButton.setIconSize(QSize(20, 20))
            # self.ui.PicButton.setObjectName("ChooseButton2")
            self.ui.PicButton.setStyleSheet(
                'background-color:#4CB28A;''color:#2B3743;''font-size:16px;''border-radius:23px;')
        elif self.mode == 4:
            pics2 = QIcon()
            pics2.addPixmap(QPixmap("icon/pics2.png"), QIcon.Normal, QIcon.Off)
            self.ui.PicsButton.setIcon(pics2)
            self.ui.PicsButton.setIconSize(QSize(20, 20))
            # self.ui.PicsButton.setObjectName("ChooseButton2")
            self.ui.PicsButton.setStyleSheet(
                'background-color:#4CB28A;''color:#2B3743;''font-size:16px;''border-radius:23px;')

    def ShowCam(self):
        self.ChangeMode(1)
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            th = threading.Thread(target=self.Display)
            th.start()

    def ShowFile(self):
        self.ChangeMode(2)
        self.FileName, self.FileType = QFileDialog.getOpenFileName(self.mainWnd, 'Choose file', '.', '*.mp4')
        if (self.FileName == ""):
            print("未选择视频")
            return
        else:
            self.cap = cv2.VideoCapture(self.FileName)
            print("打开")
            if self.cap.isOpened():
                print("打开成功")
                th = threading.Thread(target=self.Display)
                th.start()

    def ShowPic(self):
        self.ChangeMode(3)
        print(1)
        FileName, FileType = QFileDialog.getOpenFileName(self.mainWnd, '打开文件', '.',
                                                         'Image Files(*.jpg *.png)')  # 图像文件（*.jpg *.png）
        if (FileName == ""):
            print("未选择图片")
            return
        else:
            print("选中图片：" + FileName)
            frame = cv2.imread(FileName)
            YOLOOut = self.YOLOIdent.start(frame)
            # print(YOLOOut.shape)
            YOLOOut = QPixmap.fromImage(
                QImage(YOLOOut.data, YOLOOut.shape[1], YOLOOut.shape[0], YOLOOut.shape[1] * YOLOOut.shape[2],
                       QImage.Format_RGB888))
            self.ui.DispalyLabel.setPixmap(YOLOOut)
            with open('num.txt', 'r') as f:
                lines = f.readlines()

            self.ui.NumHatLabel.setText("戴帽子的人数：" + lines[0][:-1])  # 去除\n
            self.ui.NumPersonLabel.setText("没戴的人数： " + lines[1])

    def ShowPics(self):
        self.ChangeMode(4)
        DirName = QFileDialog.getExistingDirectory(self.mainWnd, "选取图片文件夹")
        if (DirName == ""):
            print("未选择文件夹")
            return
        else:
            self.ui.pbar.show()
            self.ui.pbar.setMaximum(0)
            print("选中文件夹：" + DirName)
            self.ui.Last.setEnabled(False)
            self.ui.Next.setEnabled(False)
            PicInList = []
            self.PicOutList = []
            self.Num = []
            self.num = 0
            self.i = 0
            print("读取中...")

            for root, dirs, files in os.walk(DirName):  # 当前目录路径,当前路径下所有子目录,当前路径下所有非目录子文件
                for file in files:
                    FileName, FileType = os.path.splitext(file)
                    print("a")
                    # if (FileType == r".jpg" or r".png"): 一定Ture
                    if (FileType == r".jpg" or FileType == r".png"):
                        print(FileType)
                        file = root + r'/' + file
                        self.num = self.num + 1
                        PicInList.append(file)
                        print(file)
                    else:
                        print("当前文件不是jpg或png格式")
                        continue
            self.ui.pbar.setMaximum(self.num)
            self.ui.slider.setMinimum(1)
            self.ui.slider.setMaximum(self.num)
            print("识别中...")
            index = 0
            for file in PicInList:
                index = index + 1
                frame = cv2.imread(file)
                YOLOOut = self.YOLOIdent.start(frame)
                print("识别成功一张")
                with open('num.txt', 'r') as f:
                    lines = f.readlines()
                self.Num.append(lines)
                YOLOOut = QPixmap.fromImage(
                    QImage(YOLOOut.data, YOLOOut.shape[1], YOLOOut.shape[0], YOLOOut.shape[1] * YOLOOut.shape[2],
                           QImage.Format_RGB888))
                self.PicOutList.append(YOLOOut)
                print(file)
                self.ui.pbar.setValue(index)
            print("识别完毕...")

            if self.num > 0:
                self.ui.DispalyLabel.setPixmap(self.PicOutList[0])
                self.ui.NumHatLabel.setText("戴帽子的人数：" + self.Num[0][0])
                self.ui.NumPersonLabel.setText("没戴的人数： " + self.Num[0][1])
                self.ui.pbar.reset()
                self.ui.pbar.hide()
                self.ui.slider.show()
                self.ui.Last.show()
                self.ui.Next.show()
                self.ui.slider.setValue(1)
            if self.num > 1:
                self.ui.Last.setEnabled(True)
                self.ui.Next.setEnabled(True)

    def Last(self):
        if self.i > 0 and self.mode == 4:
            self.i = self.i - 1
            self.ui.DispalyLabel.setPixmap(self.PicOutList[self.i])
            self.ui.NumHatLabel.setText("戴帽子的人数：" + self.Num[self.i][0])
            self.ui.NumPersonLabel.setText("没戴的人数： " + self.Num[self.i][1])
            self.ui.slider.setValue(self.i + 1)

    def Next(self):
        if self.i < self.num - 1 and self.mode == 4:
            self.i = self.i + 1
            self.ui.DispalyLabel.setPixmap(self.PicOutList[self.i])
            self.ui.NumHatLabel.setText("戴帽子的人数：" + self.Num[self.i][0])
            self.ui.NumPersonLabel.setText("没戴的人数： " + self.Num[self.i][1])
            self.ui.slider.setValue(self.i + 1)

    def ShowStatus(self, Time, num_hat, num_person):

        self.ui.ParamLabel.setText("检测参数")
        self.ui.TimeLabel.setText("时间：" + Time)
        self.ui.FPSLabel.setText("摄像头fps：" + str(self.FPS))
        self.ui.RealFPSLabel.setText("实际fps： %.2f" % (self.RealFPS))

        self.ui.ResultLabel.setText("安全帽检测结果")
        self.ui.NumHatLabel.setText("戴帽子的人数：" + str(num_hat))
        self.ui.NumPersonLabel.setText("没戴的人数： " + str(num_person))

        TimeOut = (datetime.datetime.now() - datetime.timedelta(seconds=20)).strftime("%Y-%m-%d %H:%M:%S")
        if (TimeOut == self.StartTime):
            print(self.StartTime + "已录制")
            self.StartTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def record(self):
        RecordPath = '666.mp4'
        size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fps = 15
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.vout = cv2.VideoWriter(RecordPath, fourcc, fps, size)

    def Display(self):
        self.record()
        self.FPS = self.cap.get(cv2.CAP_PROP_FPS)  # CV_CAP_PROP_FPS	5	视频的帧速
        if self.mode == 2:
            self.ui.slider.show()
            self.position = 0
            self.frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            print(self.frames)
            AllSec = self.frames / self.FPS
            print(AllSec)
            self.ui.slider.setMinimum(0)
            self.ui.slider.setMaximum(AllSec)
        while True:
            Time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            ret, frame = self.cap.read()
            if self.mode == 2:
                self.position = self.position + 1
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.position)
                print(self.position)
            # 读完视频
            if ret == False:
                break
            t1 = time.time()
            YOLOOut = self.YOLOIdent.start(frame)
            self.RealFPS = (self.RealFPS + (1. / (time.time() - t1))) / 2

            YOLOOut = QPixmap.fromImage(QImage(YOLOOut.data, YOLOOut.shape[1], YOLOOut.shape[0], QImage.Format_RGB888))
            self.ui.DispalyLabel.setPixmap(YOLOOut)
            with open('num.txt', 'r') as f:
                lines = f.readlines()
            self.ShowStatus(Time, lines[0][:-1], lines[1])
            frame = cv2.putText(frame, Time, (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1, cv2.LINE_AA)

            self.vout.write(frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stopEvent.set()
            if True == self.stopEvent.is_set():
                # 关闭事件置为未触发，清空显示label
                self.RealFPS = 0
                self.stopEvent.clear()
                self.ui.DispalyLabel.clear()
                self.vout.release()
                self.cap.release()
                self.ui.TimeLabel.setText("时间：")
                self.ui.FPSLabel.setText("摄像头fps：")
                self.ui.RealFPSLabel.setText("实际fps： ")
                self.ui.NumHatLabel.setText("戴帽子的人数：")
                self.ui.NumPersonLabel.setText("没戴的人数： ")
                break
