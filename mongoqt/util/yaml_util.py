import yaml
from magicgui import widgets
from magicgui.widgets import create_widget, Container, PushButton

def get_collection_list_from_yaml(self, db_type):
    return list(self.db_config_info['db_types'][db_type]['collections'].keys()) + \
           list(self.db_config_info['db_types']['share']['collections'].keys())

def get_document_info_from_yaml(self, db_type, collection):
    if collection in list(self.db_config_info['db_types']['share']['collections'].keys()):
        return self.db_config_info['db_types']['share']['collections'][collection]
    else:
        return self.db_config_info['db_types'][db_type]['collections'][collection]

def get_tableviewer_info_from_yaml(self, db_type, collection):
    if list(self.db_config_info['db_types'][db_type]['table_viewer'].keys()) == ['all_collections']:
        return self.db_config_info['db_types'][db_type]['table_viewer']['all_collections']
    else:
        return self.db_config_info['db_types'][db_type]['table_viewer'][collection]


def parse_template(config_dict, key_template):
    result = {}
    def _parse_str_key(key):        
        result = config_dict['doc_property_template'][key]
        inner_key_template = result.get('template',None)
        if inner_key_template!=None:
            if type(inner_key_template)==str:
                result.update(config_dict['doc_property_template'][inner_key_template])
            elif type(inner_key_template)==list:
                for each_inner_key in inner_key_template:
                    result.update(config_dict['doc_property_template'][each_inner_key])
            return result
        else:
            return result
    if type(key_template)==str:
        result.update(_parse_str_key(key_template))
    elif type(key_template)==list:
        for each in key_template:
            result.update(_parse_str_key(each))
    return result

def get_gui_dict(config_dict, db_key, collection_key, doc_key, return_content = 'all'):
    #return_content in ['all','magicgui','tableviewer]
    DB_properties = ['doc_name_format', 'unique', 'mandatory']
    template_tag = ['template']
    full = get_full_dict(config_dict, db_key, collection_key, doc_key)
    result = dict([(each, full[each]) for each in full if (each not in DB_properties + template_tag)])
    if ('label' in result) and result['label']=='default':
        result['label'] = doc_key
    if ('name' in result) and result['name']=='default':
        result['name'] = doc_key
    if return_content=='all':
        return result
    elif return_content=='magicgui':
        mggui_args = {}
        #remove key for table viewer first
        for each in ['show_in_table_viewer']:
            result.pop(each)
        #collect kwargs
        for each in ['value', 'name', 'label','widget_type']:
            mggui_args[each] = result.pop(each)
        mggui_args['options'] = result
        return mggui_args
    elif return_content=='tableviewer':
        return dict([(each, result[each]) for each in ['show_in_table_viewer']])
    return result

def get_full_dict(config_dict, db_key, collection_key, doc_key):
    result = config_dict[db_key][collection_key][doc_key]
    template_key = result.get('template',None)
    if template_key!=None:
        result_template = parse_template(config_dict, template_key)
        result_template.update(result)
        return result_template
    else:
        return result

def get_db_dict(config_dict, db_key, collection_key, doc_key):
    DB_properties = ['doc_name_format', 'unique', 'mandatory']
    full = get_full_dict(config_dict, db_key, collection_key, doc_key)
    return dict([(each, full[each]) for each in DB_properties if each in full])

"""
with open('C:\\Users\\qiucanro\\apps\\mongoqt\\src\\gui\\resource\\config\\app_config.yml','r') as f:
    result = yaml.safe_load(f)
    print(result['p25_orders_1']['product_info'])
    get_full_dict(result,'p25_orders_1','product_info','product_name')
"""


