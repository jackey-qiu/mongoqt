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

def connect_mongodb(url_template, user_name, password):
    url_complete = url_template.format(user_name,urllib.parse.quote(password.encode('utf-8')))
    try:
        client = MongoClient(url_complete,tlsCAFile=certifi.where())
    except Exception as e:
        error_pop_up('login info is incorrect. Try again!'+str(e))
        return
    return client

def create_pandas_data_from_db(mongodb_client, db_config, db, constrains = [], limit = 50):
    """extact data from database and create a pandas dataframe to be used as table model input for table 
       viewer widget

    Args:
        db_type (str, optional): database type you specify in the yaml file. Defaults to 'book'.
        single_collection (bool, optional): extract data from single collection or not. Defaults to True.
        constrains (list, optional): in the case of multiple collections, you need to give the constrains to fielter out one record.
                                     eg. ['date','2023-09-03'], this constrain will extract the record in each collection where collection.date = '2032-09-03'
    """
    data = {}
    var_column_names = get_header_name(db_config)
    collections = get_collection_name(db_config)
    assert len(collections)>=1, "no collection is provided in yaml"
    for key, value in var_column_names.items():
        data[key] = []
    for collection in collections:
        for each in mongodb_client[db][collection].find():
        # for each in self.database[collection].find().limit(limit):
            #if constrains[0] not in each:
            #    break
            assert constrains[0] in each, 'The constrain key' + {constrains[0]} + 'is not found in the database'
            if each[constrains[0]] == constrains[1]:
                for each_key in data:
                    if each_key!='collections':
                        data[each_key].append(each.get(each_key, 'NA'))
                data['collections'].append(self.db_config_info['db_types'][db_type]['collections'][collection].get('map_name', collection))
                break
    return pd.DataFrame(data)

def extract_one_record(mongo_client, db_config, collection, constrain, db, cache = None, ):
    #specify the db name if you are not using the context database
    doc_info = get_document_info_from_yaml_config(db_config)
    if cache==None:
        data_from_db = mongo_client[db][collection].find_one(constrain)
    else:
        data_from_db = cache
    NO_RECORD = False
    if data_from_db==None:
        NO_RECORD = True
    return data_from_db

def delete_one_record(main_gui, mongodb_client, db, constrain, cbs = [], silent = False, msg = 'Are you sure to delete this paper?'):
    reply = True
    if not silent:
        reply_ = QMessageBox.question(main_gui, 'Message', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        reply = reply_ == QMessageBox.Yes
    
    if reply:
        try:
            for collection in mongodb_client[db].list_collection_names():
                mongodb_client[db][collection].delete_many(constrain)
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

def update_one_record(self, widget_container):
    data_from_client = dict([(each.name, each.value) for each in widget_container])
    data_from_client, key_values = validate_and_format_mongodb_document(self.database, data_from_client, self.config, self.database_name, False)
    for collection in data_from_client:
        filter = {self.config[self.database_name]['db_info']['key_name']: key_values[collection]}
        new_values = {'$set':data_from_client[collection]}
        self.database[collection].update_one(filter, new_values)

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