import translate_main_window
import sys, os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.path.dirname(os.path.abspath(__file__))+'/ffmpeg-master-latest-win64-gpl-shared/bin' + ";" + os.environ['PATH']
from PyQt5.QtWidgets import QMainWindow, QApplication
# from PyQt5.QtGui import QIcon
# os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__))+'/ffmpeg-master-latest-win64-gpl-shared/bin'+ os.pathsep + os.environ["PATH"]
# sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/ffmpeg-master-latest-win64-gpl-shared/bin')
sys.stdout = open(os.devnull, 'w')

if __name__ == '__main__':
    # 获取UIC窗口操作权限
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    # 调自定义的界面（即刚转换的.py对象）
    Ui = translate_main_window.TranslateMainWindow()  # 这里也引用了一次helloworld.py文件的名字注意
    sys.exit(app.exec_())


#打包语句：pyinstaller --upx-dir=C:\Users\xxx\Desktop\upx\upx-4.0.1-win64 -D -w pythoner_league_translate.py --copy-metadata tqdm --copy-metadata regex --copy-metadata tokenizers --copy-metadata numpy --copy-metadata regex --copy-metadata packaging --copy-metadata filelock --copy-metadata requests --copy-metadata whisper