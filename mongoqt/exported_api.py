from mongoqt.db_apis.common_db_opts import connect_mongodb, \
                                           add_one_record, \
                                           delete_one_record,\
                                           update_one_record, \
                                           init_pandas_model_from_db_base
from mongoqt.gui.gui_apis.event_api import init_event_listener
from mongoqt.gui.gui_apis.gui_opts import api_create_magic_gui_widget

"""_summary_
How to use these apis?

1. You need to impliment a maingui frame app, which can be launched. Assume the object name is main_gui.
2. You need to create a pushButton or toolbar action for connecting to database client (slot function is connect_mongodb),
   the returned obj is an mongodb_client, set an attribute (mongodb_client) for the main_gui
3. There must be a config object (with a name of config) that contain database information. The config object is a dict with a scheme structure as defined in mongoqt\gui\resource\config\app_config.yml
   This config object should be reserved for database information configuration.
4. There must be a database_name attribute under main_gui, it is a string representing database name.
5. There must be a database object (named as database) being defined, which is a reference to mongodb_client[database_name]
6. There must be a tableview object as an attribute under main_gui
7. There must be a layout object as an attribute udner main_gui. This layout is for hosting magic gui widgets. The name of layout is specified in config.
8. With all conditions above being satistfied, you should create magic gui widget first using api_create_magic_gui_widget
9. Now you can create pandas model for the tableview using init_pandas_model_from_db_base
10. you can now add a new record using add_one_record, and free to do other operations (delete, update)
11. If you want to monitor the database event, you should call init_event_listener. To call this helper function, you need to provide a callback function, which connects to database events.
    Don't forget to start the event thread in the app via main_gui.listener_thread.start(). Once started, it will run untill the maingui is close.

"""
def test_conditions(maingui):
    assert hasattr(maingui, 'config'), 'config attribute is not defined in maingui'
    config = maingui.config
    assert 'mongoLogin' in maingui.config
    assert 'db_info' in maingui.config
    assert 'db_use' in config['db_info']
    # assert hasattr(maingui, 'database_name') and maingui.database_name == config['db_info']['db_use']#
    assert 'gui_info' in config
    assert config['db_info']['db_use'] in config

def deploy_mongo_in_one_go(main_gui, tableview_name, action_connect_db = None, pushButton_connect_db = None):
    import os
    #connect to mongodb slot
    def slot_connect_mongodb():
        url = main_gui.config['mongoLogin']['url']
        user_name = main_gui.config['mongoLogin']['login']['userName']
        password = main_gui.config['mongoLogin']['login']['password']
        if main_gui.config['mongoLogin']['login']['decode'] == 'sys-env':
            user_name = os.environ[user_name]
            password = os.environ[password]
        main_gui.mongodb_client = connect_mongodb(url, user_name, password)
        main_gui.database = main_gui.mongodb_client[main_gui.config['db_info']['db_use']]
        main_gui.database_name = main_gui.config['db_info']['db_use']
    if action_connect_db!=None:
        if type(action_connect_db)==str:
            getattr(main_gui, action_connect_db).triggered.connect(slot_connect_mongodb)
        else:
            action_connect_db.triggered.connect(slot_connect_mongodb)
    if pushButton_connect_db!=None:
        if type(pushButton_connect_db)==str:
            getattr(main_gui, pushButton_connect_db).clicked.connect(slot_connect_mongodb)
        else:
            pushButton_connect_db.clicked.connect(slot_connect_mongodb)
    slot_connect_mongodb()
    def slot_event_on():
        #create magic gui widget
        api_create_magic_gui_widget(main_gui, main_gui.config, main_gui.config['db_info']['db_use'])
        #create tableview model
        init_pandas_model_from_db_base(main_gui, table_view_widget_name=tableview_name)
    slot_event_on()
    setattr(main_gui, '_slot_db_listener_event_on', slot_event_on)
    #create event listener
    init_event_listener(main_gui, '_slot_db_listener_event_on')
    #start listening thread
    main_gui.listener_thread.start()