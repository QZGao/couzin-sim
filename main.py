import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from qfluentwidgets.common.config import qconfig

from config import Config
from interface import MainWindow


if __name__ == '__main__':
    cfg = Config()
    qconfig.load('config/config.json', cfg)
    
    # enable dpi scale
    if cfg.get(cfg.config_dpi_scale) == 'Auto':
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    else:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.config_dpi_scale))

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = MainWindow(cfg)
    w.show()
    app.exec_()
