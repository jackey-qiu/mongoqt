from functools import partial
import pandas as pd
import io
import os
from PyQt5.QtWidgets import QMessageBox,QAbstractItemView
from PyQt5.QtWidgets import QFileDialog
import codecs
from PIL import ImageGrab
from mongoqt.util.yaml_util import get_gui_dict, get_db_dict
from mongoqt.util.util import error_pop_up, image_string_to_qimage, image_to_64base_string, disable_all_tabs_but_one, PandasModel
from pymongo import MongoClient
import certifi, urllib
from ..util.yaml_util import get_tableviewer_content_dict

def connect_mongodb(url_template, user_name, password):
    """_summary_

    Args:
        url_template (str with two place holder for username and password): eg "//abc.com:{}:{}mongologin"
        user_name (str): username
        password (str): password

    Returns:
        mongodb client object: _description_
    """    
    url_complete = url_template.format(user_name,urllib.parse.quote(password.encode('utf-8')))
    try:
        client = MongoClient(url_complete,tlsCAFile=certifi.where())
    except Exception as e:
        error_pop_up('login info is incorrect. Try again!'+str(e))
        return
    return client


def update_selected_record(self, index = 0):
    """callback when clicking one row of tableview
    To get this work, it is assumed that there are pandas_model and container_ objects in the mainGUI frame

    Args:
        self: main pyqt GUI frame object
        index (int or Index, optional): tableview index object, passed via tableview signal. Defaults to 0.

    Returns:
        dict: complete information of the target record
    """    
    if type(index)!=int:
        key = self.pandas_model._data[self.config[self.database_name]['db_info']['key_name']].tolist()[index.row()]
    else:
        key = self.pandas_model._data[self.config[self.database_name]['db_info']['key_name']].tolist()[index]
    collections = [each for each in self.database.list_collection_names() if each!= 'db_info']
    data_container_list = [self.database[each].find_one({self.config[self.database_name]['db_info']['key_name']:key}) for each in collections]
    data_dict = {}
    for each in data_container_list:
        each.pop('_id')
        data_dict.update(each)
    #update magicGUI widget values
    for each in list(self.container_):
        if each.name in data_dict:
            try:
                each.value = data_dict[each.name]
            except Exception as err:
                error_pop_up(str(err))
    return data_dict

def init_pandas_model_from_db_base(self, onclicked_func = update_selected_record, constrains={},update_func = lambda a:a, pandas_data = None, table_view_widget_name='tableView_book_info'):
    """create pandas model for the tableview widget, the created model is named pandas_model refrerable via self.pandas_model

    Args:
        self: pyqt5 main gui frame object
        onclicked_func (_type_, optional): callback when clicking one row of tableviewer. Defaults to update_selected_record.
        constrains (dict, optional): constrain for extracting data. Defaults to {}, which means to extract all records.
        update_func (_type_, optional): callback when the data in pandas_model change. Defaults to lambdaa:a.
        pandas_data (_type_, optional): pandas frame to be shown in the tableviewer. Defaults to None. If given, database will not be used.
        table_view_widget_name (str, optional): tableView widget name in the main frame. Defaults to 'tableView_book_info'.
    """    
    #disable_all_tabs_but_one(self, tab_widget_name, tab_indx)
    if type(pandas_data)!=pd.DataFrame:
        data = create_pandas_data_from_db(self.mongodb_client, db_config=self.config, db_name = self.database_name, constrains=constrains)
    else:
        data = pandas_data
    header_name_map = {}
    self.pandas_model = PandasModel(data = data, tableviewer = getattr(self, table_view_widget_name), main_gui = self, column_names=header_name_map)
    #sort the table according to the first column
    try:#for some db, first column is bool checked values
        self.pandas_model.sort(0, False)
    except:
        pass
    if update_func!=None:
        self.pandas_model.dataChanged.connect(partial(update_func,self))
    getattr(self, table_view_widget_name).setModel(self.pandas_model)
    getattr(self, table_view_widget_name).resizeColumnsToContents()
    getattr(self, table_view_widget_name).setSelectionBehavior(QAbstractItemView.SelectRows)
    getattr(self, table_view_widget_name).horizontalHeader().setStretchLastSection(True)
    try:
        getattr(self, table_view_widget_name).clicked.disconnect()
    except:
        pass
    getattr(self, table_view_widget_name).clicked.connect(partial(onclicked_func,self))
    #select the first row upon init
    getattr(self, table_view_widget_name).selectRow(0)
    # populate_search_field(self, )

def create_pandas_data_from_db(mongodb_client, db_config, db_name, constrains = {}):
    """extact data from database and create a pandas dataframe to be used as table model input for table 
       viewer widget

    Args:
        mongodb_client (mongodb client object): _description_
        db_config (dict): database config loaded from yaml config file
        db_name (str): database name
        constrains (dict, optional): _description_. Defaults to {}.

    Returns:
        pandas dataframe object: _description_
    """    

    tableviewer_info = get_tableviewer_content_dict(db_config, db_name)
    match_pd_list = []
    for coll, doc_list in tableviewer_info.items():
        pd_temp = pd.DataFrame(mongodb_client[db_name][coll].find(constrains, dict(zip(doc_list+['_id'], [1]*len(doc_list)+[0]))))
        match_pd_list.append(pd_temp)
    return pd.concat(match_pd_list, axis=1) 
    
def delete_one_record(main_gui, mongodb_client, db, constrain, cbs = [], silent = False):
    """_summary_

    Args:
        main_gui (_type_): mainGUi frame object
        mongodb_client (_type_): mongodb client for database connection
        db (str): database name
        constrain (_type_): _description_
        cbs (list, optional): callbacks to be executed after deleting action. 
                              Common callback is update the tableview. Defaults to [].
        silent (bool, optional): whether or not poping up a question dialog for confirmation. Defaults to False.
    """    
    reply = True
    if not silent:
        reply_ = QMessageBox.question(main_gui, 'Message', 'Are you sure to delete this record?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        reply = reply_ == QMessageBox.Yes
    
    if reply:
        try:
            for collection in mongodb_client[db].list_collection_names():
                mongodb_client[db][collection].delete_one(constrain)
            if main_gui!=None:
                main_gui.statusbar.clearMessage()
                main_gui.statusbar.showMessage(f'The record {constrain} is deleted from DB successfully.')
                for cb in cbs:
                    cb(main_gui)
        except Exception as e:
            error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error') 

def check_exist(db, collection, doc_key, doc_value):
    return db[collection].count_documents({doc_key: doc_value}) > 0

def validate_and_format_mongodb_document(db, data_dict, config_dict, db_key, check_unique_key = True):
    """validate and format the collection info extracted from magicGUI widgets using the schema defined in the config

    Args:
        db (mongodb database object): _description_
        data_dict (dict): current record details extracted from gui widgets
        config_dict (dict): schema information defined in the config file
        db_key (str): name of database under consideration
        check_unique_key (bool, optional): whether or not check the ubiqueous of the key. 
                                           Set it to False when updating an existing record, 
                                           set it to True when adding a new record. Defaults to True.
                                           When adding a new record, if the key is already existing, 
                                           error message dialog will be poped up.
                                           
    Returns:
        dict: formated data_dict (if check_unique_key == True)
        dict, dict: formated data_dict, key_value (collection name as keys, and the keyname as value; used as meta data for updating record)
    """
    #collections
    keys_collection = [each for each in list(config_dict[db_key].keys()) if each!='db_info']
    result = {}
    key_values = {}
    for collection in keys_collection:
        result[collection] = {}
        doc_keys = list(config_dict[db_key][collection].keys())
        for each_doc in doc_keys:
            property_dict_doc_db = get_db_dict(config_dict, db_key, collection, each_doc)
            if property_dict_doc_db['mandatory']:
                if data_dict[each_doc]=='':
                    error_pop_up(each_doc + ' needs mandatory input', 'Error')
                    return
            if property_dict_doc_db['doc_name_format']!=None:
                result[collection][each_doc] = property_dict_doc_db['doc_name_format'].format(data_dict[each_doc])
            else:
                result[collection][each_doc] = data_dict[each_doc]
            if property_dict_doc_db['unique']:
                if check_unique_key:
                    if check_exist(db, collection, each_doc, result[collection][each_doc]):
                        error_pop_up(each_doc +' is supposed to be unique, but already existing in db', 'Error')
                        return
                else:
                    key_values[collection] = result[collection].pop(each_doc)
    if check_unique_key:
        return result
    else:
        return result, key_values

def add_one_record(self, widget_container, extra_info = {}, cbs = []):
    """_summary_

    Args:
        self: maingui frame object
        widget_container (magicgui container object): _description_
        extra_info (dict, optional): extra info to add to the record. Defaults to {}.
        cbs (list, optional): a list of callbacks. Defaults to [].

    Returns:
        dict: validated and formated record information
    """
    data_from_client = dict([(each.name, each.value) for each in widget_container])
    data_from_client = validate_and_format_mongodb_document(self.database, data_from_client, self.config, self.database_name)
    #data_from_client after this validation will be a dict with collection names as the keys          
    try:
        for collection in data_from_client:
            data_from_client[collection].update(extra_info.get(collection,{}))
            self.database[collection].insert_one(data_from_client[collection])
            self.statusbar.clearMessage()
            self.statusbar.showMessage(f'Append the record sucessfully!')
        for cb in cbs:
            cb(self)
        return data_from_client
    except Exception as e:
        error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error') 

def update_one_record(self, widget_container, cbs = []):
    """_summary_

    Args:
        widget_container (magicgui container object): _description_
        cbs (list): a list of callbacks
    """
    data_from_client = dict([(each.name, each.value) for each in widget_container])
    data_from_client, key_values = validate_and_format_mongodb_document(self.database, data_from_client, self.config, self.database_name, False)
    for collection in data_from_client:
        filter = {self.config[self.database_name]['db_info']['key_name']: key_values[collection]}
        new_values = {'$set':data_from_client[collection]}
        self.database[collection].update_one(filter, new_values)
    for cb in cbs:
        cb(self)

def text_query_by_field(self, field, query_string, target_field, collection_name, database = None):
    """
    Args:
        field ([string]): in ['author','book_name','book_id','status','class']
        query_string ([string]): [the query string you want to perform, e.g. 1999 for field = 'year']
        target_filed([string]): the targeted filed you would like to extract, single string or a list of strings
        collection_name([string]): the collection name you would like to target

    Returns:
        [list]: [value list of target_field with specified collection_name]
    e.g.
    general_query_by_field(self, field='name', query_string='jackey', target_field='email', collection_name='user_info')
    means I would like to get a list of email for jackey in user_info collection in the current database
    """
    if database == None:
        database = self.database
    index_key = (database.name, collection_name, field)
    if index_key not in self.index_names:
        index_name = database[collection_name].create_index([(field,'text')])
        self.index_names[index_key] = index_name
    targets = database[collection_name].find({"$text": {"$search": "\"{}\"".format(query_string)}})
    # print([each for each in targets])
    #drop the index afterwards
    if type(target_field)==list:
        return_list = []
        for field in target_field:
            targets = database[collection_name].find({"$text": {"$search": "\"{}\"".format(query_string)}})
            #print(field)
            return_list.append([each[field] for each in targets])
    else:
        return_list = [each[target_field] for each in targets]
    # self.database.paper_info.drop_index(index_name)
    #database[collection_name].drop_index(index_name)
    return return_list  

#eg name == 'jackey' and birth_year== '1983'
#logical_opt = 'and'
#field_values_cases = [{'name': 'jackey'},{'birth_year': '1983'}]
def logical_query_within_two_fields(self, collection, logical_opt, field_value_cases, return_fields = None):
    assert type(field_value_cases)==list and len(field_value_cases)>1, "field_value_cases should be a list of dictionary"
    if return_fields==None:
        return self.database[collection].find({
            f"${logical_opt}":field_value_cases
        })
    else:
        return self.database[collection].find({
            f"${logical_opt}":field_value_cases
        }, dict(zip(return_fields,[1]*len(return_fields))))
    
#eg year > 1983
#logical_opt = 'gt', field = 'year', limit = 1983
def logical_query_one_field(self, collection, logical_opt, field, limit, return_fields = None):
    if return_fields==None:
        return self.database[collection].find({field:
            {f"${logical_opt}": limit}
        })
    else:
        return self.database[collection].find({field:
            {f"${logical_opt}":limit}
        }, dict(zip(return_fields,[1]*len(return_fields))))
    
#eg year > 1983 and year <2000
#logical_opts= ['gt','lt'], limits = [1983, 2000], field = 'year'
def logical_range_query_one_field(self, collection, logical_opts, field, limits, return_fields = None):
    assert len(logical_opts)==len(limits), "operators and limits should be of a same number!"
    if return_fields==None:
        return self.database[collection].find({"$and":
            [
            {field: {f"${logical_opts[i]}": limits[i]}}
            for i in range(len(limits))
            ]
        })
    else:
        return self.database[collection].find({"$and":
            [
            {field: {f"${logical_opts[i]}": limits[i]}}
            for i in range(len(limits))
            ]
        }, dict(zip(return_fields,[1]*len(return_fields))))