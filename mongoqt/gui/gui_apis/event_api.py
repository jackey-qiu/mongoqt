from PyQt5 import QtCore
from functools import partial
import inspect

def init_event_listener(self, callback_obj_name):
    """start a new thread for listening event
    After this initialization step, there is a listener and listener_thread attribute created in the main gui frame object
    In the app, one needs to define the slot func to start the thread (self.listener_thread.start()), 
           and connect it to widget event (eg pushButton clicked). Once started, the thread will be running as long as the livetime of main gui.
  
    Args:
    self (MainWindow object): main gui frame object
    callback_obj_name(str): name of slot func (defined in main gui frame) to be connected to the event_on signal defined in the listener.
           the some_callable should take in one argument from the listener, and the value of the argument is change_data of type of dict.
    example script for such a callback function defined in main gui frame
    def slot_event_listener(self, data):
        msg_format = 'Database record has been {}ed from upstream!'.format
        if 'operationType' in data:
            msg = msg_format(data['operationType'])
        else:
            msg = msg_format('added')
        self.statusbar.showMessage(msg)
        print(data)
        slot_switch_current_use_DB(self, update_listener = False)
    """
    self.listener = eventListener(self)
    self.listener_thread = QtCore.QThread()
    self.listener.moveToThread(self.listener_thread)
    self.listener_thread.started.connect(self.listener.start_listen_server)
    assert hasattr(self, callback_obj_name), callback_obj_name+' not existing in the main gui'
    self.listener.event_on.connect(getattr(self, callback_obj_name))

class eventListener(QtCore.QObject):
    pipeline = [{"$match": {"operationType": {"$in":["insert","update","delete"]}}}]
    event_on = QtCore.pyqtSignal(object)
    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.database_client = None
        self.filter = {'db':'*','coll':'*'}

    def update_listening_properties(self, client = None, filter = None):
        print('updating listening properties!!')
        if client!=None:
            self.database_client = client
        if filter!=None:
            assert (filter['db']=='*' or type(filter['db'])==list) and (filter['coll']=='*' or type(filter['coll'])==list), "Wrong format for filter"
            self.filter = filter

    def start_listen_server(self):
        print(f"Listening for changes...{self.pipeline}")
        if self.database_client==None:
            try:
                self.database_client = self.parent.mongodb_client
            except Exception as err:
                print(str(err))
                return
        for change in self.database_client.watch(pipeline=self.pipeline):
            all_db = False
            all_coll = False
            if self.filter['db']=='*':
                all_db = True
            if self.filter['coll']=='*':
                all_coll = True
            try:
                if all_db:
                    if all_coll:
                        self.event_on.emit(change)
                        #self.callback(change)
                    else:
                        if change['ns']['coll'] in self.filter['coll']:
                            self.event_on.emit(change)
                            #self.callback(change)
                else:
                    if all_coll:
                        if change['ns']['db'] in self.filter['db']:
                            self.event_on.emit(change)
                            #self.callback(change)
                    else:
                        if (change['ns']['db'] in self.filter['db']) and \
                        (change['ns']['coll'] in self.filter['coll']):
                            self.event_on.emit(change)
                            #self.callback(change)
            except Exception as err:
                print('Error', str(err))
