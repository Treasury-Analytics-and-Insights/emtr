import panel as pn
from helpers import *

pn.extension(sizing_mode="stretch_width")
pn.extension('tabulator')
pn.widgets.Tabulator.theme = 'bootstrap4'
pn.widgets.Tabulator.pagination = 'local'


data = load_data('dist_exp_data.csv')

# each population type has a different set of groups
groups = {
    pop_type: data[data['Population Type'] == pop_type].Description.unique().tolist() 
    for pop_type in ['Household', 'Family']}
    
title = pn.Column(
    pn.Row(
        pn.pane.Markdown('# Income Distribution Explorer', width=600),
        pn.pane.Markdown('*Best viewed full screen*', align = ('end', 'end'))),
    # add a horizontal line
    pn.layout.Divider()).servable(target='title')


# all the controls are in a widget box ------------------------------------------------
pop_selector = pn.widgets.Select(
    name='Population Type', options = ['Household', 'Family'])

# the group selector options depend on the population type
group_selector = pn.widgets.CheckBoxGroup(
    name = 'Group', options = groups[pop_selector.value], 
    value=[groups[pop_selector.value][0]])

def update_groups(event):
    group_selector.options = groups[event.new]
    group_selector.value = [groups[event.new][0]]

pop_selector.param.watch(update_groups, 'value')


measure_selector = pn.widgets.Select(
    name='Income Measure', options = data['Income Measure'].unique().tolist())

income_type_selector = pn.widgets.Select(
    name='Income Type', options = data['Income Type'].unique().tolist())

go_button = pn.widgets.Button(
    name='Go', button_type='success', width=100, align=('center', 'center'))
go_button_row = pn.Row(pn.pane.Markdown("Subset and plot", align = ('end', 'center')), go_button)

pn.WidgetBox(
    pop_selector, group_selector, measure_selector, income_type_selector, 
    go_button_row).servable(target='widget_box')

# ------------------------------------------------------------------------------------

# Initial plot and table
fig, table_data = fig_table_data(
    data, pop_selector.value, group_selector.value, measure_selector.value,
    income_type_selector.value)

# Plot tab components
plot_pane = pn.pane.Matplotlib(
    fig, tight=True, sizing_mode='scale_width', width=1000)
with open('idi_disclaimer.md', 'r') as f:
    disclaimer = pn.pane.Markdown(f.read(), width=300)
plot_download = pn.widgets.FileDownload(
    'plot.svg', label='Download plot.svg', button_type='primary', 
    width=200, align=('start', 'start'))


# Data tab components
table = pn.widgets.Tabulator(table_data, show_index=False, width=1000, height=600)
data_download = pn.widgets.FileDownload(
    'subset_data.csv', label='Download subset_data.csv', button_type='primary', 
    width=200, align=('center', 'center'))

# Instructions tab
with open('instructions.md', 'r') as f:
    instructions = pn.pane.Markdown(f.read(), name = "Instructions", width=600)

# Definitions tab
with open('definitions.md', 'r') as f:
    definitions = pn.pane.Markdown(f.read(), name = "Definitions", width=800, height=600)

pn.Tabs(
    pn.Row(pn.Column(plot_download, plot_pane), disclaimer, name='Plots'), 
    pn.Row(table, pn.Column(disclaimer, data_download), name="Data"), 
    instructions, 
    definitions, width = 1500).servable(target='tabs')

#-------------------------------------------------------------------------------------

def update(event):
    """Update the plot and table when the Go button is clicked"""
    fig, table_data = fig_table_data(
        data, pop_selector.value, group_selector.value, measure_selector.value,
        income_type_selector.value)
    plot_pane.object=fig
    table.value=table_data


go_button.on_click(update)
