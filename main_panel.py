import panel as pn
import yaml

from helpers import *

pn.extension(sizing_mode="stretch_width")

with open('parameters/TY2022.yaml', 'r', encoding='utf-8') as f:
    sq_params = yaml.safe_load(f)

with open('parameters/TY2022_reform.yaml', 'r', encoding='utf-8') as f:
    reform_params = yaml.safe_load(f)
    
title = pn.Column(
    pn.Row(
        pn.pane.Markdown('# Income Explorer Prototype', width=600),
        pn.pane.Markdown('*Best viewed full screen*', align = ('end', 'end'))),
    # add a horizontal line
    pn.layout.Divider()).servable(target='title')


# all the controls are in a widget box ------------------------------------------------

hrly_wage_input = pn.widgets.FloatInput(name = 'Hourly Wage', value = 20)
max_hours_input = pn.widgets.IntInput(name = 'Max Hours', value = 50)

accom_cost_input = pn.widgets.FloatInput(name = 'Weekly Accom.\n Cost', value = 450)
as_area_input = pn.widgets.Select(name = 'AS Area', options = [1, 2, 3, 4], value = 1)
accom_type_input = pn.widgets.Select(
    name = 'Accom.', options = ['Rent', 'Mortgage'], value = 'Rent')


go_button = pn.widgets.Button(
    name='Calculate !', button_type='success', width=200, align=('center', 'center'))

pn.WidgetBox(
    pn.Row(hrly_wage_input, max_hours_input),
    pn.Row(accom_cost_input, as_area_input), accom_type_input,
    go_button, width = 300).servable(target='widget_box')

# ------------------------------------------------------------------------------------

# Initial plots and table
figs, table_data = fig_table_data(
    sq_params, reform_params, hrly_wage_input.value, max_hours_input.value, 
    accom_cost_input.value, as_area_input.value, accom_type_input.value)

# The I couldn't get a Plotly pane to update properly when the data changed.
# using html works, but it is probably slower
rate_panes = {}
for var in RATE_VARS:
    rate_panes[var] = pn.pane.HTML(figs[var].to_html(), width=1000)

emtr_tab = pn.Column(
    pn.pane.Markdown('## Net Income \n\n Not done yet'),
    pn.pane.Markdown('## Effective Marginal Tax Rate'), rate_panes['emtr'],
    pn.pane.Markdown('## Replacement Rate'), rate_panes['replacement_rate'],
    pn.pane.Markdown('## Participation Tax Rate'), rate_panes['participation_tax_rate'],
    width = 1000, height=2000, name = 'EMTR')

poverty_tab = pn.Column(
    pn.pane.Markdown('## Equivalised Income \n\n Not done yet'),
    pn.pane.Markdown('## BHC Poverty\n\nNot done yet'),
    pn.pane.Markdown('## AHC Poverty\n\nNot done yet'),
    width = 1000, height=2000, name = 'Poverty')

composition_tab = pn.Column(
    pn.pane.Markdown('## Status Quo \n\n Not done yet'),
    pn.pane.Markdown('## Reform \n\n Not done yet'),
    width = 1000, height=2000, name = 'Income Composition')

# Instructions tab
with open('instructions.md', 'r') as f:
    instructions = pn.pane.Markdown(
        f.read(), name = "Instructions", width=600)

# Definitions tab
with open('definitions.md', 'r') as f:
    definitions = pn.pane.Markdown(
        f.read(), name = "Definitions", width=800, height=600)

pn.Tabs(
    emtr_tab, poverty_tab, composition_tab, instructions, definitions, 
    width = 1500, height=2000).servable(target='tabs')

#-------------------------------------------------------------------------------------

def update(event):
    """Update the plot and table when the Go button is clicked"""
    figs, table_data = fig_table_data(
        sq_params, reform_params, hrly_wage_input.value, max_hours_input.value, 
        accom_cost_input.value, as_area_input.value, accom_type_input.value)
    for key in figs:
        rate_panes[key].object=figs[key].to_html()


go_button.on_click(update)
