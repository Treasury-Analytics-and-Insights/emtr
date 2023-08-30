from enum import Enum
import os

import panel as pn
import yaml


ParamSource = Enum('ParamSource', 'built-in upload')


class PolicyInput:
    # list the built-in parameter files in the parameters directory, creating
    # a dictionary of tax-years and parameter files
    builtin_param_files = {
        s.split('_')[0]: s for s in os.listdir('parameters') if s.endswith('.yaml')}

    def __init__(self, name = 'Status quo', source = ParamSource['built-in'], param_file = 'TY24'):

        self.default_name = name
        # a text box for the policy name
        self.name_input = pn.widgets.TextInput(name='', value=name, width=100)
        
        # a toggle switch for built-in parameter files or a local file
        self.param_source_select = pn.widgets.Select(
            name='', options=ParamSource._member_names_, value=source.name, width=80)
        self.param_source_select.param.watch(self.update_param_source, 'value')
        
        # a select widget for the built-in parameter files
        self.builtin_param_select = pn.widgets.Select(
            name='', options=sorted(list(self.builtin_param_files.keys())), 
            value=param_file, width=80)
        self.builtin_param_select.param.watch(self.load_builtin_param_file, 'value')

        # a download button for the built-in parameter files
        self.builtin_param_download = pn.widgets.FileDownload(
            file='parameters/' + self.builtin_param_files[self.builtin_param_select.value], 
            filename=self.builtin_param_select.value + '.yaml', button_type='primary', 
            width=100, height=30, icon = 'download', label='')
        
        # a file input widget for local parameter files
        self.local_param_input = pn.widgets.FileInput(name='Local file: ')
        self.local_param_input.param.watch(self.load_local_param_file, 'value')
        
        # create a row of widgets for the parameter source controls
        # if the toggle is set to 'built-in', show the select widget and download button
        # if the toggle is set to 'local', show the file input widget
        self.row = pn.Row(
            self.name_input, self.param_source_select,
            pn.Row(self.builtin_param_select, self.builtin_param_download),
            self.local_param_input)
        
        self.update_param_source(None)
        self.params = None
        if source == ParamSource['built-in']:
            self.load_builtin_param_file(None)

    # update the parameter source controls when the toggle is changed
    def update_param_source(self, event):
        if self.param_source_select.value == ParamSource.upload.name:
            self.row[2].visible = False
            self.row[3].visible = True
            self.name_input.value = self.default_name
            self.name_input.disabled = True
            self.params = None
            self.local_param_input.value = None
        else:
            self.row[3].visible = False
            self.row[2].visible = True
            self.name_input.value = self.default_name            
            self.name_input.disabled = False
            self.load_builtin_param_file(None)

    # load the selected built-in parameter file
    def load_builtin_param_file(self, event):
        with open('parameters/' + self.builtin_param_files[self.builtin_param_select.value]) as f:
            self.params = yaml.safe_load(f)
        self.builtin_param_download.file = 'parameters/' + \
            self.builtin_param_files[self.builtin_param_select.value]
        self.builtin_param_download.filename = self.builtin_param_select.value + '.yaml'
        

    # load the local parameter file
    def load_local_param_file(self, event):
        self.params = yaml.safe_load(self.local_param_input.value.decode('utf-8'))
        self.name_input.value = self.default_name
        self.name_input.disabled = False
