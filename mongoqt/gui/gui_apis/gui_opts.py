from magicgui import widgets
from magicgui.widgets import create_widget, Container, PushButton
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QFont
import yaml
import sys, json, os
import typing
from pathlib import Path
from mongoqt.util.yaml_util import get_gui_dict
from mongoqt.db_apis.common_db_opts import connect_mongodb, validate_and_format_mongodb_document, add_one_record, update_one_record

def connect_to_mangodb(self):
    url = self.config['mongoLogin']['url']
    user_name = self.config['mongoLogin']['login']['userName']
    password = self.config['mongoLogin']['login']['password']
    if self.config['mongoLogin']['login']['decode'] == 'sys-env':
        user_name = os.environ[user_name]
        password = os.environ[password]
    try:
        self.mongodb_client = connect_mongodb(url, user_name, password)
        # self.database = self.mongodb_client[self.database_name]
        self.statusbar.showMessage('Success to connect to MongoDB Atlas!')
    except Exception as err:
        self.statusbar.showMessage('Fail to connect to MongoDB Atlas! due to {}'.format(str(err)))

def test_add_one_record(self):
    data_dict = dict([(each.name, each.value) for each in self.container_])
    self.database['product_info'].insert_one(data_dict)

def slot_add_one_record(self):
    add_one_record(self, self.container_)

def slot_update_one_record(self):
    try:
        update_one_record(self, self.container_)
        self.statusbar.showMessage('The record is updated!')
    except Exception as err:
        self.statusbar.showMessage('The record is NOT updated! due to {}.'.format(str(err)))

def populate_DB_combobox(self):
    self.comboBox_db_type.clear()
    self.comboBox_db_type.addItems(self.config['db_info']['db_type'])
    self.comboBox_db_type.setCurrentText(self.config[self.config['db_info']['db_use']]['db_info']['db_type'])
    self.comboBox_db_list.clear()
    db_dict = {}
    for each in self.config['db_info']['db_type']:
        db_dict[each] = []
    for key, value in self.config.items():
        if key!='db_info' and ('db_info' in value):
            db_dict[value['db_info']['db_type']].append(key)
    self.comboBox_db_list.addItems(db_dict[self.comboBox_db_type.currentText()])
    self.comboBox_db_list.setCurrentText(self.config['db_info']['db_use'])

def slot_update_DB_list_combobox(self):
    self.comboBox_db_list.clear()
    db_dict = {}
    for each in self.config['db_info']['db_type']:
        db_dict[each] = []
    for key, value in self.config.items():
        if key!='db_info' and ('db_info' in value):
            db_dict[value['db_info']['db_type']].append(key)
    self.comboBox_db_list.addItems(db_dict[self.comboBox_db_type.currentText()])
    self.comboBox_db_list.setCurrentText(db_dict[self.comboBox_db_type.currentText()][0])
    '''
    self.database_name = db_dict[self.comboBox_db_type.currentText()][0]
    self.config['db_info']['db_use'] = self.database_name
    create_magic_gui_widget(self)
    self.database = self.mongodb_client[self.database_name]
    '''

def slot_switch_current_use_DB(self):
    self.database_name = self.comboBox_db_list.currentText()
    self.config['db_info']['db_use'] = self.database_name
    self.database = self.mongodb_client[self.database_name]
    create_magic_gui_widget(self)

def test_validation(self):
    data_from_client = dict([(each.name, each.value) for each in self.container_])
    return validate_and_format_mongodb_document(self.database, data_from_client, self.config, self.database_name)

def convert_clipboard_buffer_to_base64_string(self):
    # Pull image from clibpoard
    img = ImageGrab.grabclipboard()
    # Get raw bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    # Convert bytes to base64
    base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
    return base64_data, 'PNG'

def load_img_from_base64(self, widget_view_name, base64_string, base64_string_var_name = 'base64_string_img'):
    setattr(self, base64_string_var_name, base64_string)
    qimage = image_string_to_qimage(base64_string, 'PNG')
    view = getattr(self, widget_view_name)
    view.clear()
    view.loadImages([qimage])
    view.show()

#widget_view is qpageview.View instance widget
def open_image_file(self, widget_view):
    self.action.setView(widget_view)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","image file (*.*)", options=options)
    if fileName:
        base64_data = image_to_64base_string(fileName)
        self.img_in_base64_format = base64_data
        img_format =  fileName.rsplit('.')[-1]
        #self.img_format = img_format
        widget_view.clear()
        widget_view.loadImages([image_string_to_qimage(base64_data, img_format = img_format)])
        widget_view.show()
        return img_format

#widget_view is qpageview.View instance widget
def paste_image_to_viewer_from_clipboard(self, widget_view, base64_string_var_name = 'base64_string_img'):
    self.action.setView(widget_view)
    # Pull image from clibpoard
    img = ImageGrab.grabclipboard()
    # Get raw bytes
    img_bytes = io.BytesIO()
    try:
        img.save(img_bytes, format='PNG')
        # Convert bytes to base64
        base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
        setattr(self, base64_string_var_name, base64_data)
        #self.base64_string_temp = base64_data
        widget_view.clear()
        widget_view.loadImages([image_string_to_qimage(base64_data, img_format = 'PNG')])
        widget_view.show()
    except:
        error_pop_up('Fail to paste image from clipboard.','Error')
        return

def findMainWindow() -> typing.Union[QMainWindow, None]:
    # Global function to find the (open) QMainWindow in application
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            return widget
    return None

def populate_search_field(self, field_comboBox_widget_name='comboBox_search_item'):
    name_map = list(self.db_config_info['db_types'][self.database_type]['table_viewer'].values())[0]
    fields = list(name_map.values())
    getattr(self, field_comboBox_widget_name).clear()
    getattr(self, field_comboBox_widget_name).addItems(fields)

def make_magic_gui_container(main_gui, magic_gui_dict, gui_host):
    widget_list = []
    for par_name, par_value in magic_gui_dict.items():
        if par_value['value']==None:
            par_value.pop('value')
        widget_list.append(create_widget(**par_value))
    container = Container(widgets = widget_list)
    delete_widgets_from_layout(getattr(main_gui, gui_host))
    for each in container.native.children()[1:]:
        row = each.children()[1:]
        row[0].setFont(QFont('Arial', 13))
        getattr(main_gui, gui_host).addRow(*row)
    #getattr(main_gui, gui_host).addWidget(container.native)
    # for each in widget_list:
        # setattr(main_gui, each.name, each)
    return container 

def delete_widgets_from_layout(layout):
    for i in reversed(range(layout.count())): 
        layout.itemAt(i).widget().setParent(None)

def example_callback_update_database(mg_container):
    kwargs = dict([(each.name, each.value) for each in mg_container])
    print(kwargs)

def example_callback_pull_data_from_database(data_from_db_dict, mg_container):
    for each in mg_container:
        temp_value = data_from_db_dict.get(each.name, None)
        if temp_value!=None:
            each.value = temp_value

def connect_pushbutton_slots(button, mg_container, cb=example_callback_update_database):
    #first disconnect slot if any
    try:
        button.clicked.disconnect()
    except:
        pass
    button.clicked.connect(lambda state, a=mg_container, cb=cb:cb(a))

def create_magic_gui_widget(parent):
    result = parent.config
    collection_keys = list(parent.config[parent.database_name].keys())
    #assume two collections only: db_info and the other one
    collection = [each for each in collection_keys if each!='db_info']
    assert len(collection)==1, "only two collections are allowed for each database!"
    collection = collection[0]
    doc_keys = list(parent.config[parent.database_name][collection].keys())
    magic_gui_dict = {}
    for each in doc_keys:
        magic_gui_dict[each] = get_gui_dict(result, parent.database_name,collection,each,'magicgui')
    #verticalLayout_magic_gui is layout object that can be referred from parent as parent.verticalLayout_magic_gui
    # container_ = make_magic_gui_container(parent, magic_gui_dict, 'verticalLayout_collection_list')
    container_ = make_magic_gui_container(parent, magic_gui_dict, 'formLayout')
    parent.container_ = container_

def test_magic_gui_widget(parent, db = 'p25_orders_1', collection='product_info'):
    #parent is the main gui frame object
    
    result = parent.config
    doc_keys = list(result[db][collection].keys())
    magic_gui_dict = {}
    for each in doc_keys:
        magic_gui_dict[each] = get_gui_dict(result, db,collection,each,'magicgui')
    #verticalLayout_magic_gui is layout object that can be referred from parent as parent.verticalLayout_magic_gui
    # container_ = make_magic_gui_container(parent, magic_gui_dict, 'verticalLayout_collection_list')
    container_ = make_magic_gui_container(parent, magic_gui_dict, 'formLayout')
    parent.container_ = container_
    #pushButton_magic is pushbutton object that can be referred from parent as parent.pushButton_magic
    connect_pushbutton_slots(parent.pushButton_add, container_, example_callback_update_database)
    return container_