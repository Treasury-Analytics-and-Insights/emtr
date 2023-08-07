import os

import panel as pn
import yaml

from helpers import *

pn.extension(sizing_mode="stretch_width")

# these are temporary - just to easily give us things to look at while we develop
with open('parameters/TY22_BEFU23.yaml', 'r', encoding='utf-8') as f:
    default_sq_params = yaml.safe_load(f)
with open('parameters/TY23_BEFU23.yaml', 'r', encoding='utf-8') as f:
    default_reform_params = yaml.safe_load(f)
    
title = pn.Column(
    pn.Row(
        pn.pane.Markdown('# Income Explorer Prototype (UNDER CONSTRUCTION !)', width=600),
        pn.pane.Markdown('*Best viewed full screen*', align = ('end', 'end'))),
    # add a horizontal line
    pn.layout.Divider()).servable(target='title')


# all the controls are in a widget box ------------------------------------------------

example_param_file_select = pn.widgets.FileSelector(
    directory='parameters', name='Example parameters')
example_param_file_download = pn.widgets.FileDownload(
    file = 'parameters/TY23_BEFU23.yaml', filename = 'TY23_BEFU23.yaml', button_type = 'primary')

def update_example_file_download(event):
    example_param_file_download.file = example_param_file_select.value[0]
    example_param_file_download.filename = os.path.basename(example_param_file_select.value[0])

example_param_file_select.param.watch(update_example_file_download, 'value')

sq_param_input = pn.widgets.FileInput(name = 'SQ')
reform_param_input = pn.widgets.FileInput(name = 'Reform')

hrly_wage_input = pn.widgets.FloatInput(name = 'Hourly Wage', value = 20)
max_hours_input = pn.widgets.IntInput(name = 'Max Hours', value = 50)

sq_income_choice_input = pn.widgets.Select(
    name = 'SQ Income Choice', options = IncomeChoice._member_names_, value = 'WfF')
reform_income_choice_input = pn.widgets.Select(
    name = 'Reform Income Choice', options = IncomeChoice._member_names_, value = 'WfF')
wep_scaling_input = pn.widgets.Select(
    name = 'WEP Scaling', options = WEPScaling._member_names_, value = 'Average')

accom_cost_input = pn.widgets.FloatInput(name = 'Weekly Accom.\n Cost', value = 450)
as_area_input = pn.widgets.Select(name = 'AS Area', options = [1, 2, 3, 4], value = 1)
accom_type_input = pn.widgets.Select(
    name = 'Accom. Type', options = ['Rent', 'Mortgage'], value = 'Rent')
child_age_input = pn.widgets.TextInput(name = 'children_ages', value = "0, 5, 14")

#Add the "Partnered" toggle, which upon clicking, adds the controls for the second wage
partner_toggle = pn.widgets.Toggle(
    name = 'Partnered', button_type='primary', width=50, align=('start', 'center'))
partner_hrly_wage_input = pn.widgets.FloatInput(
    name = 'Partner Hourly Wage', value = 20, disabled = True)
partner_hours_worked_input = pn.widgets.IntInput(name = 'Partner Hours Worked', value = 0, disabled = True)
partner_row = pn.Row(
    partner_hrly_wage_input, partner_hours_worked_input, width = 300)

# watch the partner toggle to enable/disable the partner controls
def update_partner_controls(event):
    if partner_toggle.value:
        partner_hrly_wage_input.disabled = False
        partner_hours_worked_input.disabled = False
    else:
        partner_hrly_wage_input.disabled = True
        partner_hrly_wage_input.value = 20
        partner_hours_worked_input.disabled = True 
        partner_hours_worked_input.value = 0

partner_toggle.param.watch(update_partner_controls, 'value')   


go_button = pn.widgets.Button(
    name='Calculate !', button_type='success', width=50, align=('start', 'center'))

data_download = pn.widgets.FileDownload(
    'output.csv', label='Download output.csv', button_type='primary', 
    width=200, align=('start', 'center'))

widget_box = pn.WidgetBox(
    pn.pane.Markdown('### Policy parameters'),
    pn.Row(pn.pane.Markdown('Status Quo:', width = 60),sq_param_input), 
    pn.Row(pn.pane.Markdown("Reform:", width = 60), reform_param_input),
    pn.pane.Markdown('For help creating your own parameter file, see the "Example Parameters" tab'),
    pn.pane.Markdown('### Family specification'),
    pn.Row(hrly_wage_input, max_hours_input),
    pn.Row(sq_income_choice_input, reform_income_choice_input),
    pn.Row(accom_cost_input, as_area_input), 
    pn.Row(accom_type_input, wep_scaling_input),
    partner_toggle, partner_row, child_age_input,
    go_button, data_download,
    width = 300).servable(target='widget_box')

# ------------------------------------------------------------------------------------

# Params tab

params_tab = pn.WidgetBox(
    pn.pane.Markdown(
        'To help create your own parameter file, choose one of the examples below to download, and edit '
        'it in a text editor. Only the first file selected will be downloaded.'),
        example_param_file_select, example_param_file_download, 
        name = 'Example Parameters', width = 600, height = 500
)

# Initial plots and table
child_ages = string_to_list_of_integers(child_age_input.value)

# Initial plot and table
figs, table_data, comps_reform, comps_sq = fig_table_data(
    default_sq_params, default_reform_params, partner_toggle.value, hrly_wage_input.value, 
    child_ages, partner_hrly_wage_input.value, partner_hours_worked_input.value,
    accom_cost_input.value, accom_type_input.value, as_area_input.value,
    max_hours_input.value, WEPScaling[wep_scaling_input.value],
    IncomeChoice[sq_income_choice_input.value], 
    IncomeChoice[reform_income_choice_input.value])

# I couldn't get a Plotly pane to update properly when the data changed.
# using html works, but it is probably slower
rate_panes = {var: pn.pane.HTML(figs[var].to_html(), width=1000, height=400) for var in RATE_VARS}


emtr_tab = pn.Column(
    pn.pane.Markdown('## Net Income'), rate_panes['net_income'],
    pn.pane.Markdown('## Effective Marginal Tax Rate'), rate_panes['emtr'],
    pn.pane.Markdown('## Replacement Rate'), rate_panes['replacement_rate'],
    pn.pane.Markdown('## Participation Tax Rate'), rate_panes['participation_tax_rate'],
    width = 1000, height=2000, name = 'EMTR')

reform_pane = pn.pane.HTML(comps_reform.to_html(), width=1000, height=500)
sq_pane = pn.pane.HTML(comps_sq.to_html(), width=1000, height=500)

composition_tab = pn.Column(
    pn.pane.Markdown('## Status Quo \n\n Almost done'), sq_pane,
    pn.pane.Markdown('## Reform \n\n Almost done'), reform_pane,
    width = 1000, height=2000, name = 'Income Composition')

# Instructions tab
with open('instructions.md', 'r') as f:
    instructions = pn.pane.Markdown(
        f.read(), name = "Instructions", width=600)

pn.Tabs(
    params_tab, emtr_tab, composition_tab, instructions, 
    width = 1500, height=2000, active=1).servable(target='tabs')

#-------------------------------------------------------------------------------------



def update(event):
    """Update the plot and table when the Go button is clicked"""
    if sq_param_input.value:
        # decode the bytes to a string, and then decode the yaml
        sq_params = yaml.safe_load(sq_param_input.value.decode('utf-8'))
    else:
        sq_params = default_sq_params
    if reform_param_input.value:
        reform_params = yaml.safe_load(reform_param_input.value.decode('utf-8'))
    else:
        reform_params = default_reform_params

    child_ages = string_to_list_of_integers(child_age_input.value)

    figs, table_data , comps_reform, comps_sq = fig_table_data(
        sq_params, reform_params, partner_toggle.value, hrly_wage_input.value, 
        child_ages, partner_hrly_wage_input.value, partner_hours_worked_input.value,
        accom_cost_input.value, accom_type_input.value, as_area_input.value, 
        max_hours_input.value, WEPScaling[wep_scaling_input.value],
        IncomeChoice[sq_income_choice_input.value], 
        IncomeChoice[reform_income_choice_input.value])
    

    for key in figs:
        rate_panes[key].object=figs[key].to_html()


go_button.on_click(update)
