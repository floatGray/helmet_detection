# -------------------------------------#
#       程序入口
# -------------------------------------#
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

import DisplayUI
from QSS import Style
from VideoDisplay import Display

if __name__ == '__main__':
    app = QApplication(sys.argv)
    qss = Style()
    app.setStyleSheet(qss.style())
    mainWnd = QMainWindow()
    ui = DisplayUI.Ui_MainWindow()
    # 可以理解成将创建的 ui 绑定到新建的 mainWnd 上
    ui.setupUi(mainWnd)
    display = Display(ui, mainWnd)
    mainWnd.show()
    sys.exit(app.exec_())
