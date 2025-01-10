
#create pandas table viewer model and connect to the table viewer widget
def init_pandas_model_from_db_base(main_gui, table_viewer_widget, db_config, onclicked_func, update_func = None, pandas_data = None):
    header_name_map = {}
    if len(pandas_data)!=0:
        header_name_map = get_header_name(db_config)
    main_gui.pandas_model = PandasModel(data = pandas_data, tableviewer = table_viewer_widget, main_gui = main_gui, column_names=header_name_map)
    #sort the table according to the first column
    try:#for some db, first column is bool checked values
        main_gui.pandas_model.sort(0, False)
    except:
        pass
    if update_func!=None:
        main_gui.pandas_model.dataChanged.connect(partial(update_func,main_gui))
    table_viewer_widget.setModel(main_gui.pandas_model)
    table_viewer_widget.resizeColumnsToContents()
    table_viewer_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    table_viewer_widget.horizontalHeader().setStretchLastSection(True)
    try:
        table_viewer_widget.clicked.disconnect()
    except:
        pass
    table_viewer_widget.clicked.connect(partial(onclicked_func,main_gui))
    #select the first row upon init
    table_viewer_widget.selectRow(0)
    populate_search_field(self, )