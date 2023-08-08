import panel as pn

from helpers import *

pn.extension(sizing_mode="stretch_width")
pn.extension('plotly')

title = pn.Column(
    pn.Row(
        pn.pane.Markdown('# Income Explorer Prototype (UNDER CONSTRUCTION !)', width=600),
        pn.pane.Markdown('*Best viewed full screen*', align = ('end', 'end'))),
    # add a horizontal line
    pn.layout.Divider()).servable(target='title')


# all the controls are in a widget box ------------------------------------------------

policy_controls = [
    PolicyControl('Status Quo', source=ParamSource['built-in'], param_file='TY24'),
    PolicyControl('Reform 1', source=ParamSource['upload']),
    PolicyControl('Reform 2', source=ParamSource['upload']),
    PolicyControl('Reform 3', source=ParamSource['upload'])
]


hrly_wage_input = pn.widgets.FloatInput(name = 'Hourly Wage', value = 20)
max_hours_input = pn.widgets.IntInput(name = 'Max Hours', value = 50)

income_choice_input = pn.widgets.Select(
    name = 'Income Choice', options = IncomeChoice._member_names_, value = 'WfF')
wep_scaling_input = pn.widgets.Select(
    name = 'WEP Scaling', options = WEPScaling._member_names_, value = 'Average')

accom_cost_input = pn.widgets.FloatInput(name = 'Weekly Accom.\n Cost', value = 450)
as_area_input = pn.widgets.Select(name = 'AS Area', options = [1, 2, 3, 4], value = 1)
accom_type_input = pn.widgets.Select(
    name = 'Accom. Type', options = ['Rent', 'Mortgage'], value = 'Rent')
child_age_input = pn.widgets.TextInput(name = 'children_ages', value = "0, 5, 14")

#Add the "Partnered" toggle, which upon clicking, adds the controls for the second wage
partner_toggle = pn.widgets.Toggle(
    name = 'Partnered', button_type='primary', width=100, align=('start', 'center'))
partner_hrly_wage_input = pn.widgets.FloatInput(
    name = 'Partner Hourly Wage', value = 20, disabled = True, width=120)
partner_hours_worked_input = pn.widgets.IntInput(
    name = 'Partner Hours Worked', value = 0, disabled = True, width=120)
#partner_row = pn.Row(
#    partner_hrly_wage_input, partner_hours_worked_input, width = 300)

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
    pn.Row(pn.pane.Markdown('**Name**', width=100), pn.pane.Markdown('**Built-in or uploaded parameter file**')),
    policy_controls[0].row,
    policy_controls[1].row,
    policy_controls[2].row,
    policy_controls[3].row,
    pn.layout.Divider(),
    pn.pane.Markdown('### Family specification'),
    pn.Row(hrly_wage_input, max_hours_input, child_age_input),
    pn.Row(accom_cost_input, as_area_input, accom_type_input), 
    pn.Row(partner_toggle, partner_hrly_wage_input, partner_hours_worked_input),
    pn.layout.Divider(),
    pn.Row(income_choice_input, wep_scaling_input),
    go_button, data_download,
    width = 450).servable(target='widget_box')

# ------------------------------------------------------------------------------------

# Initial plots and table
child_ages = string_to_list_of_integers(child_age_input.value)

params = {pc.name_input.value: pc.params for pc in policy_controls if pc.params is not None}

# Initial plot and table
rate_figs, comp_figs = figs_save_data(
    params, partner_toggle.value, hrly_wage_input.value, 
    child_ages, partner_hrly_wage_input.value, partner_hours_worked_input.value,
    accom_cost_input.value, accom_type_input.value, as_area_input.value,
    max_hours_input.value, WEPScaling[wep_scaling_input.value],
    IncomeChoice[income_choice_input.value])

# I couldn't get a Plotly pane to update properly when the data changed.
# using html works, but it is probably slower
rate_panes = {
    var: pn.pane.HTML(rate_figs[var].to_html(), width=1000, height=400) for var in RATE_VARS}
emtr_tab = pn.Column(
    pn.pane.Markdown('## Net Income'), rate_panes['annual_net_income'],
    pn.pane.Markdown('## Effective Marginal Tax Rate'), rate_panes['emtr'],
    pn.pane.Markdown('## Replacement Rate'), rate_panes['replacement_rate'],
    pn.pane.Markdown('## Participation Tax Rate'), rate_panes['participation_tax_rate'],
    width = 1000, height=2000, name = 'EMTR')

comp_tab = pn.Column(width = 1000, height=2000, name = 'Income Composition')

def update_comp_tab(comp_figs):
    """Update the composition tab with new figures"""
    comp_tab.clear()
    for scenario, fig in comp_figs.items():
        comp_tab.append(pn.pane.Markdown(f'## {scenario}'))
        comp_tab.append(pn.pane.HTML(fig.to_html(), width=1000, height=400))    

update_comp_tab(comp_figs)

# Instructions tab
with open('instructions.md', 'r') as f:
    instructions = pn.pane.Markdown(
        f.read(), name = "Instructions", width=600)

pn.Tabs(
    emtr_tab, comp_tab, instructions, 
    width = 1500, height=2000, active=0).servable(target='tabs')

#-------------------------------------------------------------------------------------

def update(event):
    """Update the plot and table when the Go button is clicked"""
    child_ages = string_to_list_of_integers(child_age_input.value)

    params = {pc.name_input.value: pc.params for pc in policy_controls if pc.params is not None}

    rate_figs, comp_figs = figs_save_data(
        params, partner_toggle.value, hrly_wage_input.value, 
        child_ages, partner_hrly_wage_input.value, partner_hours_worked_input.value,
        accom_cost_input.value, accom_type_input.value, as_area_input.value, 
        max_hours_input.value, WEPScaling[wep_scaling_input.value],
        IncomeChoice[income_choice_input.value])
    
    for key in rate_figs:
        rate_panes[key].object=rate_figs[key].to_html()

    update_comp_tab(comp_figs)


go_button.on_click(update)
