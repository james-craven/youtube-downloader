# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ytdl.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import time
from pytube import Playlist, YouTube
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import traceback, sys
import os
import moviepy.editor as mp

class ProgressBar(QProgressBar):
    def update_value(self, value, animated=True):
        if animated:
            if hasattr(self, "animation"):
                self.animation.stop()
            else:
                self.animation = QPropertyAnimation(
                    targetObject=self, propertyName=b"value"
                )
                self.animation.setDuration(100)
            self.animation.setStartValue(self.value())
            self.animation.setEndValue(value)
            self.animation.start()
        else:
            self.setValue(value)

from proglog import ProgressBarLogger

class MyBarLogger(ProgressBarLogger):
    # `window` is the class where all the gui widgets are held
    def __init__(self, progress_callback, default_filename):
        super().__init__(init_state=None, bars=None, ignored_bars=None,
                 logged_bars='all', min_time_interval=0, ignore_bars_under=0)
        self.progress_callback = progress_callback
        self.default_filename = default_filename
    def callback(self, **changes):
        # Every time the logger is updated, this function is called with
        # the `changes` dictionnary of the form `parameter: new value`.
        # the `try` is to avoid KeyErrors before moviepy generates a `'t'` dict 
        try:
            index = self.state['bars']['chunk']['index']
            total = self.state['bars']['chunk']['total']
            percent_complete = index / total * 100
            if percent_complete < 0:
                percent_complete = 0
            if percent_complete > 100:
                percent_complete = 100

            self.progress_callback.emit({'progress': percent_complete, 'link': self.default_filename})

        except Exception as e:
            # print(e)
            pass

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal(str)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(dict)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit(self.args[0].streams.filter(file_extension='mp4').first().default_filename)  # Done


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.finished = 0
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(763, 632)
        font = QtGui.QFont()
        font.setPointSize(15)
        MainWindow.setFont(font)
        MainWindow.setFocusPolicy(QtCore.Qt.ClickFocus)
        MainWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.title = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setPointSize(42)
        font.setBold(True)
        font.setWeight(75)
        self.title.setFont(font)
        self.title.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.title.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.title.setStyleSheet("color:white;")
        self.title.setScaledContents(True)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.title.setObjectName("title")
        self.verticalLayout.addWidget(self.title)
        self.plainTextEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.plainTextEdit.setMaximumSize(QtCore.QSize(16777215, 49))
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setPointSize(29)
        font.setBold(True)
        font.setWeight(75)
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.plainTextEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
#         self.plainTextEdit.setStyleSheet("background-color: white;\n"
# "color: black;")
        self.plainTextEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.plainTextEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.plainTextEdit.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                 "stop:0 rgb(0, 58, 109), stop: 0.5 rgb(0, 221, 255), stop:1 rgb(0, 58, 109));"
                 "border: 5px solid white;"
                 "color: white;"
                 "font-weight: bold")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.label.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.label.setObjectName("label")
        shadow = QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2)
        # setting blur radius
        # adding shadow to the label
        self.label.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.title.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=3, yOffset=3))
        self.plainTextEdit.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.horizontalLayout.addWidget(self.label)
        self.spinBox = QtWidgets.QSpinBox(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.spinBox.setFont(font)
        self.spinBox.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.spinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.spinBox.setObjectName("spinBox")
        self.spinBox.setStyleSheet("QSpinBox {color: white; background-color: black; border: 3px solid black;"
        "}"
        "QSpinBox::up-button {subcontrol-origin: border; subcontrol-position: top right; /* position at the top right corner */ width: 16px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */ border-image: url(./images/border-white.png) 1; border-width: 1px; background-color: transparent; border-color:black;"
        "}"
        "QSpinBox::up-button:hover {border-image: url(:/images/spinup_hover.png) 1;"
        "}"
        "QSpinBox::up-arrow {image: url(./images/up.png);width: 15px;height: 15px;"
        "}"
        "QSpinBox::down-button {subcontrol-origin: border; subcontrol-position: bottom right; /* position at the top right corner */ width: 16px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */ border-image: url(./images/border-white.png) 1; border-width: 1px; background-color: transparent; border-color:black;"
        "}"
        "QSpinBox::down-button:hover {border-image: url(:/images/spindown_hover.png) 1;"
        "}"
        "QSpinBox::down-arrow {image: url(./images/down.png);width: 15px;height: 15px;"
        "}")
        self.spinBox.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.spinBox.setAlignment(Qt.AlignCenter)
        self.spinBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.horizontalLayout.addWidget(self.spinBox)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setBold(True)
        font.setWeight(75)
        self.pushButton.setFont(font)
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                "stop:0 rgb(0, 58, 109), stop: 0.5 rgb(0, 190, 255), stop:1 rgb(0, 58, 109));"
                "border: 5px solid white;"
                "color:white;"
                "border-style: outset;"
                "border-radius: 15px;"
                "border-color: white;"
                "padding: 8px;"
                "width: 65px")
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(lambda: self.run())
        self.pushButton.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=1, yOffset=1))
        self.label3 = QLabel(self.pushButton)
        self.label3.setText("Download")
        self.label3.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.label3.setFont(font)
        self.pushButton.resize(150, 150)
        # self.label3.resize(150, 50)
        self.horizontalLayout.addWidget(self.pushButton)

        self.label2 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label2.setFont(font)
        self.label2.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.label2.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.label2.setWordWrap(False)
        self.label2.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.label2.setObjectName("label2")
        self.label2.setStyleSheet("color: white;")
        self.label2.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=1, yOffset=1))
        self.horizontalLayout.addWidget(self.label2)
        self.label2.hide()

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtWidgets.QTableWidget(self.centralwidget)
        self.tableView.setObjectName("tableView")
        self.tableView.setStyleSheet("QTableWidget {background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "stop:0 rgb(0, 58, 109), stop: 0.5 rgb(0, 221, 255), stop:1 rgb(0, 58, 109));"
            "border: 5px solid white;"
            "color:white;"
            "border-style: inset;"
            "border-radius: 15px;"
            "padding: 8px;"
            "gridline-color: white}"
            "QTableWidget::item {border: 3px solid white;"
            "}"
            "QHorizontalHeader, QHorizontalHeaderItem {color: white;"
            "background-color: transparent;"
            "border: 5px solid white;}"
            "QHeaderView::section {background-color: transparent;border: 3px solid white; font-size: 24px; font-weight: bold;}"
            "QHeaderView {background-color: transparent;}"
            "QTableCornerButton::section {background-color: transparent;}")
        self.tableView.insertColumn(self.tableView.columnCount())
        self.tableView.insertColumn(self.tableView.columnCount())
        font = QtGui.QFont()
        font.setFamily(".New York")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.songLabel = QLabel(self.centralwidget)
        self.songLabel.setText('Song Title')
        self.songLabel.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.songLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.songLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.songLabel.setFont(font)
        item = QtWidgets.QTableWidgetItem('Song Title')
        self.tableView.insertRow(self.tableView.rowCount())
        self.tableView.setCellWidget(0, 0, self.songLabel)
        item = QtWidgets.QTableWidgetItem('Progress Bar')
        self.progressLabel = QLabel(self.centralwidget)
        self.progressLabel.setText('Progress Bar')
        self.progressLabel.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.progressLabel.setFont(font)
        self.progressLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.progressLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.tableView.setCellWidget(0, 1, self.progressLabel)
        self.tableView.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
        self.tableView.horizontalHeader().hide()
        self.verticalLayout.addWidget(self.tableView)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.title.setText(_translate("MainWindow", "YouTube Playlist Downloader"))
        self.plainTextEdit.setPlaceholderText(_translate("MainWindow", "Paste Playlist URL..."))
        self.label.setText(_translate("MainWindow", "Number of songs to download:"))
        self.label2.setText(_translate("MainWindow", "Status..."))
        self.label3.setText(_translate("MainWindow", "Download"))

    def download(self, ytlink, row_num, progress_callback):
        filename = ytlink.streams.filter(file_extension='mp4').first().default_filename.split('.mp4')[0]
        progress_callback.emit({'filename': filename, 'row_num': row_num})
        def progress_func(self, stream, bytes_remaining):
            size = self.filesize
            p = (float(abs(bytes_remaining-size)/size))*float(100)
            progress_callback.emit({'progress': int(p), 'link': self.default_filename})
        
        def completed_func(self, file_path):
            progress_callback.emit({'progress': 0, 'link': self.default_filename, 'format': 'Converting...%p%'})
            ytfile = file_path
            mp4_path = ytfile
            mp3_path = ytfile.split('.mp4')[0]+'.mp3'
            new_file = mp.AudioFileClip(mp4_path)
            mylogger = MyBarLogger(progress_callback, self.default_filename)
            new_file.write_audiofile(mp3_path, verbose=False, logger=mylogger)
            os.remove(mp4_path)

        ytlink.register_on_progress_callback(progress_func)
        ytlink.register_on_complete_callback(completed_func)
        try:
            # print(ytlink.streams.filter(file_extension='mp4').first().default_filename)
            ytlink.streams.filter(file_extension='mp4').first().download()
        except Exception as e:
            print(f'Exception: {ytlink.title}\n{e}')
            pass

    def thread_complete(self, link):
        # print(f'finished {link}')
        link = link.split('.mp4')[0]
        globals()[link].setFormat('%p% Complete!')
        self.finished = self.finished + 1
        if self.finished >= self.spinBox.value():
            self.label2.setText('Status: Complete!')
            self.label2.adjustSize()
            app.processEvents()
            self.end = time.time()
            print(f'Application Time: {self.end - self.start}')

    def progress_callback(self, n):
        try:
            link = n['link'].split('.mp4')[0]
            globals()[link].update_value(n['progress'])
        except:
            pass
        try:
            globals()[link].setFormat(n['format'])
        except:
            pass
        try:
            item = QtWidgets.QLabel(n['filename'])
            item.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2))
            itemFont = self.tableView.font()
            itemFont.setBold(True)
            itemFont.setPointSize(18)
            item.setFont(itemFont)
            ui.tableView.setCellWidget(n['row_num'], 0, item)
            globals()[n['filename']] = ProgressBar(minimum=0, maximum=100, textVisible=True, text="Downloading...", format="Downloading...%p%", alignment=Qt.AlignCenter)
            globals()[n['filename']].setStyleSheet("QProgressBar::chunk "
                "{"
                "background-color: LawnGreen;"
                "color: black;"
                "text-align: center;"
                "}"
                "QProgressBar "
                "{"
                "border: 2px solid grey;"
                "border-radius: 5px;"
                "background-color: DarkRed;"
                "color: black;"
                "text-align: center;"
                "}")
            ui.tableView.setCellWidget(n['row_num'], 1, globals()[n['filename']])
        except:
            pass

    def run(self):
        self.start = time.time()
        s = self.spinBox.value()
        self.url = self.plainTextEdit.toPlainText()
        self.p = Playlist(self.url)
        self.youtubeList = []
        for link in self.p[:s]:
            self.youtubeList.append(YouTube(link))
        self.tableView.setRowCount(len(self.youtubeList)+1)
        self.threadpool = QThreadPool()

        print(f'Multithreading with max {self.threadpool.maxThreadCount()}')
        for i in range(s):  
            row_num = i + 1
            link = self.youtubeList[i]
            worker = Worker(self.download, link, row_num)
            worker.signals.progress.connect(self.progress_callback)
            worker.signals.finished.connect(self.thread_complete)
            self.threadpool.start(worker)
        self.label2.setText('Status: Downloading!')
        self.label2.adjustSize()
        # app.processEvents()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    ui.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    MainWindow.show()
    headerSize = ui.tableView.columnWidth(0)-15
    ui.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
    for i in range(ui.tableView.columnCount()):        
        ui.tableView.setColumnWidth(i, headerSize)

    p = QPalette()
    gradient = QLinearGradient(0, 0, 768, 0)
    gradient.setColorAt(0.0, QColor(0, 58, 109))
    gradient.setColorAt(0.5, QColor(0, 221, 255))
    gradient.setColorAt(1.0, QColor(0, 58, 109))
    p.setBrush(QPalette.Window, QBrush(gradient))
    MainWindow.setPalette(p)
    p.setBrush(QPalette.Background, QBrush(gradient))
    ui.plainTextEdit.setPalette(p)
    ui.tableView.setPalette(p)
    sys.exit(app.exec_())