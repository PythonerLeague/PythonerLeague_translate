import sys, os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
# from PyQt5 import QtCore, QtGui, QtWidgets
from translate_dt_designer import *
from PyQt5.QtWidgets import QMainWindow
from translate import *
# from multiprocessing import Queue
import queue
import threading
import ctypes
import inspect
from aciton_info import Ui_dialog# 这个是可以单独运行的窗口
sys.stdout = open(os.devnull, 'w')

class TranslateMainWindow(QMainWindow,Ui_QMainWindow):
    def __init__(self, *args, **kwargs):
        super(TranslateMainWindow, self).__init__()
        self.whisper_translate = WhisperTranslate()
        self.mes_q = queue.Queue()
        self.result_q = queue.Queue()
        self.thread_list = []
        self.setupUi(self)
        self.show()
        self.actionLoad()
        self.QComboBoxLoad()
        self.editLoad()

    def actionLoad(self):
        self.model_save_path.clicked.connect(self.ModelSavePath)
        self.pushButton_outfile_path.clicked.connect(self.PushButtonOutFilePath)
        self.pushButton_process_inputfile_path.clicked.connect(self.PushButtonProcessInputfilePath)
        self.pushButton_start_translate.clicked.connect(self.PushButton_start_translate)
        self.actions_info.triggered.connect(self.ActionsInfo)
        # self.pushButton_3.clicked.connect(self.PushButton_file_save)
        # self.pushButton_subtitle_inputfile_path.clicked.connect(self.PushButtonSubtitleInputfilePath)
        self.pushButton_start_add_subtitle.clicked.connect(self.PushButton_start_add_subtitle)
        self.pushButton_start_monitor.clicked.connect(self.PushButton_start_monitor)
        self.pushButton_end_monitor.clicked.connect(self.PushButton_end_monitor)
        self.language.currentIndexChanged.connect(self.set_language)
        self.model.currentIndexChanged.connect(self.set_model)
        self.compute_engine.currentIndexChanged.connect(self.set_compute_engine)
        self.pushButton_end.clicked.connect(self.PushButtonEnd)
        self.discriminate_language_pushButton.clicked.connect(self.DiscriminateLanguageButton)


    def QComboBoxLoad(self):
        self.language.addItems(self.whisper_translate.get_language_list())
        self.label_language = QtWidgets.QLabel("        ", self)
        self.label_language.setText(self.language.currentText())
        self.model.addItems(self.whisper_translate.get_model_name())
        self.label_model = QtWidgets.QLabel("        ", self)
        self.label_model.setText(self.model.currentText())
        self.compute_engine.addItems(['cpu','cuda'])
        self.label_compute_engine = QtWidgets.QLabel("        ", self)
        self.label_compute_engine.setText(self.compute_engine.currentText())

    def editLoad(self):
        self.LanguageCategoryEdit.setEnabled(False)#不可编辑

    def set_language(self):
        curtext = self.language.currentText()  # 获取当前文本
        self.label_language.setText(curtext)  # 获取当前文本并作为字符串传递给QLabel显示出来

    def set_model(self):
        curtext = self.model.currentText()  # 获取当前文本
        self.label_model.setText(curtext)  # 获取当前文本并作为字符串传递给QLabel显示出来

    def set_compute_engine(self):
        curtext = self.compute_engine.currentText()  # 获取当前文本
        self.label_compute_engine.setText(curtext)  # 获取当前文本并作为字符串传递给QLabel显示出来

    def PushButtonProcessInputfilePath(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "选取文件", os.getcwd(),
                                                                   "All Files(*);;Text Files(*.txt)")
        # paths.append(fileName)
        self.PendingFliePathLabel.setText(fileName)
        self.PendingFliePathLabel.adjustSize()

    def ModelSavePath(self):
        fileName =  QtWidgets.QFileDialog.getExistingDirectory(None, "选取文件", os.getcwd())
        # paths.append(fileName)
        self.label_model_save_path.setText(fileName)
        self.label_model_save_path.adjustSize()

    def PushButtonOutFilePath(self):
        fileName =  QtWidgets.QFileDialog.getExistingDirectory(None, "选取文件", os.getcwd())
        # paths.append(fileName)
        self.label_outfile_path.setText(fileName)
        self.label_outfile_path.adjustSize()

    # def PushButtonSubtitleInputfilePath(self):
    #     fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "选取文件", os.getcwd(),
    #                                                                "All Files(*);;Text Files(*.txt)")
    #     # paths.append(fileName)
    #     self.label_subtitle_inputfile_path.setText(fileName)

    def PushButton_start_translate(self):
        if len(self.thread_list) > 0:
            self.out_info_print('有文件正在被处理，请稍后再操作')
            return
        self.textBrowser.clear()
        input_file = self.PendingFliePathLabel.text()
        save_path = self.label_outfile_path.text()
        model = self.model.currentText()
        language = self.language.currentText()
        compute_engine = self.compute_engine.currentText()
        model_save_path = self.label_model_save_path.text()
        if not os.path.exists(input_file):
            self.out_info_print('待处理文件路径不存在')
            return
        if not os.path.exists(save_path):
            self.out_info_print('文件保存路径不存在')
            return
        if not model:
            self.out_info_print('需要先选择模型')
            return
        if not language:
            self.out_info_print('需要先选择翻译语言')
            return
        if not compute_engine:
            self.out_info_print('警告，未选择计算引擎，将默认为cpu')
            compute_engine = 'cpu'
        # if not model_save_path:
        #     self.out_info_print('警告，未选择模型保存路径，将默认为%s'%os.getenv(
        #     "XDG_CACHE_HOME",
        #     os.path.join(os.path.expanduser("~"), ".cache", "whisper")
        # ))
        if not model_save_path.replace('保存读取模型文件路径',''):
            self.out_info_print('警告，未选择模型读取保存路径，将默认为%s' % os.path.dirname(os.path.abspath(__file__)))
            model_save_path = os.path.dirname(os.path.abspath(__file__))

        mes_t = threading.Thread(target=self.mes_monitor)
        # mes_t.setDaemon(True)
        mes_t.start()
        whisper_translate = WhisperTranslate(model_name=model,language=language,compute_engine=compute_engine,model_path_root=model_save_path,mes_q=self.mes_q)
        # self.out_info_print('开始翻译,请等待处理结束')
        translate_t = threading.Thread(target=whisper_translate.translate_file,args=(input_file,save_path))
        # translate_t.setDaemon(True)
        translate_t.start()
        self.thread_list.extend([mes_t,translate_t])
        # result,srt_path = whisper_translate.translate_file(input_file,save_path)
        # self.out_info_print(result)
        # self.out_info_print('字幕文件路径为：%s'%srt_path)
        return

    def PushButton_start_add_subtitle(self):
        if len(self.thread_list) > 0:
            self.mes_q.put('有文件正在被处理，请稍后再操作')
            return
        self.textBrowser.clear()
        input_file = self.PendingFliePathLabel.text()
        save_path = self.label_outfile_path.text()
        model = self.model.currentText()
        language = self.language.currentText()
        compute_engine = self.compute_engine.currentText()
        model_save_path = self.label_model_save_path.text()
        if not os.path.exists(input_file):
            self.out_info_print('待处理文件路径不存在')
            return
        if not os.path.exists(save_path):
            self.out_info_print('文件保存路径不存在')
            return
        if not model:
            self.out_info_print('需要先选择模型')
            return
        if not language:
            self.out_info_print('需要先选择翻译语言')
            return
        if not compute_engine:
            self.out_info_print('警告，未选择计算引擎，将默认为cpu')
            compute_engine = 'cpu'
        if not model_save_path.replace('保存读取模型文件路径',''):
            self.out_info_print('警告，未选择模型保存读取路径，将默认为%s' % os.path.dirname(os.path.abspath(__file__)))
            model_save_path = os.path.dirname(os.path.abspath(__file__))
        mes_t = threading.Thread(target=self.mes_monitor)
        # mes_t.setDaemon(True)
        mes_t.start()
        whisper_translate = WhisperTranslate(model_name=model,language=language,compute_engine=compute_engine,model_path_root=model_save_path,mes_q=self.mes_q)
        # self.out_info_print('开始添加字幕,请等待处理结束')
        translate_t = threading.Thread(target=whisper_translate.add_subtitle,args=(input_file,save_path))
        # translate_t.setDaemon(True)
        translate_t.start()
        self.thread_list.extend([mes_t,translate_t])
        return

    def PushButton_start_monitor(self):
        self.out_info_print('功能还没时间弄，敬请期待')

    def PushButton_end_monitor(self):
        self.out_info_print('功能还没时间弄，敬请期待')

    def mes_monitor(self):
        while True:
            try:
                mes = self.mes_q.get_nowait()
                self.out_info_print(mes)
                if mes == '操作完成':
                    self.thread_list = []
                    return
                time.sleep(1)
            except Exception as e:
                time.sleep(3)

    def PushButtonEnd(self):
        for t in self.thread_list:
            if not inspect.isclass(SystemExit):
                self.out_info_print("Error Only types can be raised (not instances)")
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(t.ident), ctypes.py_object(SystemExit))
            if res == 0:
                self.out_info_print("Error invalid thread id")
            elif res != 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(t.ident, None)
                self.out_info_print("Error PyThreadState_SetAsyncExc failed")
        self.thread_list = []
        self.out_info_print('停止成功')

    def ActionsInfo(self):
        """
                想要有新的窗口， 引用其它已经写好的类
                """
        self.ui = action_details()#必须加self，放到主进程中，不然会闪退


    def out_info_print(self,mes):
        self.textBrowser.append(mes)  # 在指定的区域显示提示信息
        self.cursot = self.textBrowser.textCursor()
        self.textBrowser.moveCursor(self.cursot.End)
        QtWidgets.QApplication.processEvents()

    def DiscriminateLanguageButton(self):
        if len(self.thread_list) > 0:
            self.mes_q.put('有文件正在被处理，请稍后再操作')
            return
        input_file = self.PendingFliePathLabel.text()
        model = self.model.currentText()
        compute_engine = self.compute_engine.currentText()
        if not compute_engine:
            self.out_info_print('警告，未选择计算引擎，将默认为cpu')
            compute_engine = 'cpu'
        if not os.path.exists(input_file):
            self.out_info_print('待处理文件路径不存在')
            return
        if not model:
            self.out_info_print('需要先选择模型')
            return
        mes_t = threading.Thread(target=self.mes_monitor)
        # mes_t.setDaemon(True)
        mes_t.start()
        whisper_translate = WhisperTranslate(model_name=model, language=None, compute_engine=compute_engine,
                                             model_path_root=None, mes_q=self.mes_q)
        translate_t = threading.Thread(target=whisper_translate.Ddiscriminate_language, args=(self.LanguageCategoryEdit,input_file))
        # translate_t.setDaemon(True)
        translate_t.start()
        self.thread_list.extend([mes_t, translate_t])


class action_details(QMainWindow,Ui_dialog):
    def __init__(self, *args, **kwargs):
        super(action_details, self).__init__()
        self.setupUi(self)
        self.label.setGeometry(QtCore.QRect(120, 100, 160, 100))
        self.label.setWordWrap(True)
        # self.label.setAlignment(QtCore.Qt.AlignTop)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.show()