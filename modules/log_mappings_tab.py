from qtpy import QtWidgets
from modules.tab_base_class import StandardTab
from modules.csiem_adapter import SumoLogMappingAdapter
from modules.multithreading import Worker, ProgressDialog


class_name = 'LogMappingsTab'

# Log mappings carry a 'source' field: 'user' for custom mappings, 'jask' for
# Sumo's built-in mappers. Filtering server-side keeps the custom view fast (the
# built-in catalog is ~1700 mappings); 'All' has no filter and fetches everything.
CUSTOM_QUERY = 'source:"user"'
ALL_QUERY = ''
ALL_TOOLTIP = ('Shows all log mappings including Sumo built-in mappers '
               '(~1700). This list is large and may take a minute or more to load.')


class LogMappingsTab(StandardTab):

    def __init__(self, mainwindow):
        super().__init__(mainwindow)
        self.tab_name = 'Log Mappings'
        self.cred_usage = 'both'
        self.listWidgetLeft.params = {'extension': '.sumologmapping.json',
                                      'query': CUSTOM_QUERY}
        self.listWidgetRight.params = {'extension': '.sumologmapping.json',
                                       'query': CUSTOM_QUERY}

        self.QRadioButtonLeftCustomMappings = QtWidgets.QRadioButton('Custom')
        self.QRadioButtonLeftCustomMappings.setChecked(True)
        self.QRadioButtonLeftAllMappings = QtWidgets.QRadioButton('All')
        self.QRadioButtonLeftAllMappings.setToolTip(ALL_TOOLTIP)
        self.QRadioButtonGroupLeft = QtWidgets.QButtonGroup()
        self.QRadioButtonGroupLeft.addButton(self.QRadioButtonLeftCustomMappings, 0)
        self.QRadioButtonGroupLeft.addButton(self.QRadioButtonLeftAllMappings, 1)
        self.horizontalLayoutTopPushButtonsLeft.insertWidget(3, self.QRadioButtonLeftCustomMappings)
        self.horizontalLayoutTopPushButtonsLeft.insertWidget(4, self.QRadioButtonLeftAllMappings)

        self.QRadioButtonRightCustomMappings = QtWidgets.QRadioButton('Custom')
        self.QRadioButtonRightCustomMappings.setChecked(True)
        self.QRadioButtonRightAllMappings = QtWidgets.QRadioButton('All')
        self.QRadioButtonRightAllMappings.setToolTip(ALL_TOOLTIP)
        self.QRadioButtonGroupRight = QtWidgets.QButtonGroup()
        self.QRadioButtonGroupRight.addButton(self.QRadioButtonRightCustomMappings, 0)
        self.QRadioButtonGroupRight.addButton(self.QRadioButtonRightAllMappings, 1)
        self.horizontalLayoutTopPushButtonsRight.insertWidget(3, self.QRadioButtonRightCustomMappings)
        self.horizontalLayoutTopPushButtonsRight.insertWidget(4, self.QRadioButtonRightAllMappings)

        self.QRadioButtonGroupLeft.buttonClicked.connect(lambda: self.radio_button_changed(
            self.listWidgetLeft,
            self.left_adapter,
            self.QRadioButtonGroupLeft.checkedId(),
            self.labelPathLeft
        ))

        self.QRadioButtonGroupRight.buttonClicked.connect(lambda: self.radio_button_changed(
            self.listWidgetRight,
            self.right_adapter,
            self.QRadioButtonGroupRight.checkedId(),
            self.labelPathRight
        ))

    def radio_button_changed(self, list_widget, adapter, button_id, path_label=None):
        if button_id == 0:
            list_widget.params['query'] = CUSTOM_QUERY
        elif button_id == 1:
            list_widget.params['query'] = ALL_QUERY
        self.update_item_list(list_widget, adapter, path_label=path_label)

    def update_item_list(self, list_widget, adapter, path_label=None):
        # Override the synchronous base loader: the 'All' view fetches the entire
        # built-in mapper catalog (~1700 items, paged), which would freeze the UI.
        # Run the fetch in a worker thread behind a ProgressDialog instead.
        if adapter is None:
            return
        mode_param = {'mode': list_widget.mode}
        merged_params = {**list_widget.params, **mode_param}
        # min == max == 0 makes the progress bar indeterminate (a busy animation).
        # The page count isn't known until the paged fetch finishes, so a real
        # percentage would be fabricated; 'increment' on finished closes the dialog.
        self.list_load_progress = ProgressDialog('Loading log mappings...', 0, 0,
                                                 self.mainwindow.threadpool, self.mainwindow)
        worker = Worker(adapter.list, params=merged_params)
        worker.signals.result.connect(
            lambda contents: self.populate_item_list(list_widget, adapter, contents, path_label))
        worker.signals.error.connect(self.handle_worker_error)
        worker.signals.finished.connect(self.list_load_progress.increment)
        self.mainwindow.threadpool.start(worker)

    def populate_item_list(self, list_widget, adapter, contents, path_label=None):
        self.update_list_widget(list_widget, adapter, contents, path_label=path_label)
        self.clear_filters(list_widget)

    def reset_stateful_objects(self, side='both'):
        super().reset_stateful_objects(side=side)

        if self.left:
            self.QRadioButtonLeftCustomMappings.setEnabled(False)
            self.QRadioButtonLeftAllMappings.setEnabled(False)
            if ':' not in self.left_creds['service']:
                self.QRadioButtonLeftCustomMappings.setEnabled(True)
                self.QRadioButtonLeftAllMappings.setEnabled(True)
                self.left_adapter = SumoLogMappingAdapter(self.left_creds, 'left', self.mainwindow)

        if self.right:
            self.QRadioButtonRightCustomMappings.setEnabled(False)
            self.QRadioButtonRightAllMappings.setEnabled(False)
            if ':' not in self.right_creds['service']:
                self.QRadioButtonRightCustomMappings.setEnabled(True)
                self.QRadioButtonRightAllMappings.setEnabled(True)
                self.right_adapter = SumoLogMappingAdapter(self.right_creds, 'right', self.mainwindow)
