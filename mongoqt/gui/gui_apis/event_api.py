from PyQt5 import QtCore
from functools import partial
import inspect

class eventListener(QtCore.QObject):
    pipeline = [{"$match": {"operationType": {"$in":["insert","update","delete"]}}}]
    event_on = QtCore.pyqtSignal(object)
    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.database_client = None
        self.filter = {'db':'*','coll':'*'}
        self.callback = partial(print, "processed change:")

    def update_listening_properties(self, client = None, filter = None, callback = None):
        print('updating listening properties!!')
        if client!=None:
            self.database_client = client
        if filter!=None:
            assert (filter['db']=='*' or type(filter['db'])==list) and (filter['coll']=='*' or type(filter['coll'])==list), "Wrong format for filter"
            self.filter = filter
        if callback!=None:
            assert callable(callback), "the callback provided is not callable"
            self.callback = callback

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
