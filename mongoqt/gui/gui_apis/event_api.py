from PyQt5 import QtCore
from functools import partial

class eventListener(QtCore.QObject):

    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.database_client = None
        self.pipeline = [{"$match": {"operationType": {"$in":["insert","update","delete"]}}}]
        self.filter = {'db':['p25_device_1'],'coll':'*'}
        self.callback = partial(print, "processed change:")

    def update_listening_properties(self, client, pipeline = None, filter = {'db':'*','coll':'*'}, callback = partial(print, "processed change:")):
        self.database_client = client
        if pipeline!=None:
            self.pipeline = pipeline
        self.filter = filter
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
            if all_db:
                if all_coll:
                    self.callback(change)
                else:
                    if change['ns']['coll'] in self.filter['coll']:
                        self.callback(change)
            else:
                if all_coll:
                    if change['ns']['db'] in self.filter['db']:
                        self.callback(change)
                else:
                    if (change['ns']['db'] in self.filter['db']) and \
                       (change['ns']['coll'] in self.filter['coll']):
                        self.callback(change)
