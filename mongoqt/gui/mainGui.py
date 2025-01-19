import sys, json
from pathlib import Path
from PyQt5 import QtGui, uic, QtCore
from PyQt5.QtWidgets import QMessageBox, QDialog
from pyqtgraph.Qt import QtGui
from pathlib import Path
from PyQt5.QtWidgets import QMainWindow,QApplication, QLabel
from mongoqt.util.util import get_config_folder
from mongoqt.gui.gui_apis.event_api import eventListener, init_event_listener
from mongoqt.gui.gui_apis.gui_opts import test_magic_gui_widget, slot_connect_to_mangodb, \
                                          create_magic_gui_widget, slot_add_one_record,\
                                          populate_DB_combobox, slot_update_DB_list_combobox,\
                                          slot_switch_current_use_DB, slot_update_one_record,\
                                          slot_delete_one_record, slot_update_db_info_from_client
                                          
import qdarkstyle
import yaml

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(str(Path(__file__).parent / 'resource'/'ui'/'icons'/'app_logo.png')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setIconSize(QtCore.QSize(24, 24))
        # self.test_gui = test_magic_gui_widget

    def init_gui(self, ui):
        self.index_names = {}
        self.ui = ui
        uic.loadUi(ui, self)
        #setup image viewer actions
        menubar = self.menuBar()
        self.statusbar = self.statusBar()
        self.statusLabel = QLabel(f"Welcome to ccg lib management system!")
        self.statusbar.addPermanentWidget(self.statusLabel)
        self.widget_terminal.localNamespace['main_gui'] = self
        with open(str(get_config_folder()/'app_config.yml')) as f:
            self.config = yaml.safe_load(f)
            database_name = self.config['db_info']['db_use']
            assert database_name in self.config, 'The specified database is not existing in the config file. Reedit the config yaml file to correct it!'
            self.database_name = database_name 
        init_event_listener(self, 'slot_event_listener')
        slot_connect_to_mangodb(self)
        populate_DB_combobox(self)
        create_magic_gui_widget(self)
        self.connect_slots()
        # self._container = self.test_gui(self)  

    def connect_slots(self):
        self.actionDatabaseCloud.triggered.connect(lambda:slot_connect_to_mangodb(self))
        self.pushButton_add.clicked.connect(lambda: slot_add_one_record(self))
        self.pushButton_update.clicked.connect(lambda: slot_update_one_record(self))
        self.comboBox_db_type.currentTextChanged.connect(lambda: slot_update_DB_list_combobox(self))
        self.pushButton_load.clicked.connect(lambda: slot_switch_current_use_DB(self, update_listener=True))
        self.pushButton_delete.clicked.connect(lambda: slot_delete_one_record(self))
        self.pushButton_update_db_info.clicked.connect(lambda: slot_update_db_info_from_client(self))

    def slot_event_listener(self, data):
        msg_format = 'Database record has been {}ed from upstream!'.format
        if 'operationType' in data:
            msg = msg_format(data['operationType'])
        else:
            msg = msg_format('added')
        self.statusbar.showMessage(msg)
        print(data)
        slot_switch_current_use_DB(self, update_listener = False)

    def closeEvent(self, event) -> None:
        quit_msg = "Are you sure you want to exit the program? If yes, all text indexes will be deleted!"
        reply = QMessageBox.question(self, 'Message', 
                        quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if not hasattr(self,'mongo_client'):
                event.accept()
            print('remove all database index.....')
            for each in self.index_names:
                db_nm, coll, *k = each
                self.mongo_client[db_nm][coll].drop_index(self.index_names[each])
                print(self.index_names[each], 'deleted!')
            print('all done!')
            event.accept()
        else:
            event.ignore()

def app_launcher():
    ui_file = str(Path(__file__).parent/'resource'/ "ui" / 'main_gui_ui.ui')
    QApplication.setStyle("windows")
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.init_gui(ui_file)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    #app.setStyleSheet("QLabel{font-size: 11pt;}")
    myWin.setWindowTitle('MongoDB system')
    myWin.showMaximized()
    myWin.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    app_launcher()
    