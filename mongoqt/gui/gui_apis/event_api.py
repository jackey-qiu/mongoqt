from PyQt5 import QtCore

class eventListener(QtCore.QObject):

    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.database_client = None
        self.pipeline = [{"$match": {"operationType": {"$in":["insert","add","update","delete"]}}}]

    def update_listening_properties(self, client, pipeline = None):
        self.database_client = client
        if pipeline!=None:
            self.pipeline = pipeline

    def start_listen_server(self):
        print(f"Listening for changes...{self.pipeline}")
        if self.database_client==None:
            try:
                self.database_client = self.parent.mongodb_client
            except Exception as err:
                print(str(err))
                return
        for change in self.database_client.watch(pipeline=self.pipeline):
            print("Processed change:", change) 
