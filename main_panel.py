import js
import panel as pn

from helpers import *
from policy_input import PolicyInput, ParamSource

pn.extension(sizing_mode="stretch_width")
pn.extension('plotly')

SRC_URL = "https://github.com/Treasury-Analytics-and-Insights/emtr"

title = pn.Column(
    pn.Row(
        pn.pane.Markdown('# Income Explorer Prototype', width=600),
        pn.pane.Markdown('*Best viewed full screen*', align = ('end', 'end')),
        # add url for source code
        pn.pane.Markdown(
            f"[Source code]({SRC_URL} '{SRC_URL}')",
            align = ('end', 'end'))),
    # add a horizontal line
    pn.layout.Divider(), width=1500).servable(target='title')


# all the controls are in a widget box ------------------------------------------------

policy_controls = [
    PolicyInput('Status Quo', source=ParamSource['built-in'], param_file='TY24'),
    PolicyInput('Reform 1', source=ParamSource['upload']),
    PolicyInput('Reform 2', source=ParamSource['upload']),
    PolicyInput('Reform 3', source=ParamSource['upload'])
]


hrly_wage_input = pn.widgets.FloatInput(name = 'Hourly Wage', value = 22.70)
max_hours_input = pn.widgets.IntInput(name = 'Max Hours', value = 50)

income_choice_input = pn.widgets.Select(
    name = 'Income Choice', options = IncomeChoice._member_names_, value = 'Max')
wep_scaling_input = pn.widgets.Select(
    name = 'WEP Scaling', options = WEPScaling._member_names_, value = 'Average')

accom_cost_input = pn.widgets.FloatInput(name = 'Weekly Accom.\n Cost', value = 450)
as_area_input = pn.widgets.Select(name = 'AS Area', options = [1, 2, 3, 4], value = 1)
accom_type_input = pn.widgets.Select(
    name = 'Accom. Type', options = ['Rent', 'Mortgage'], value = 'Rent')
child_age_input = pn.widgets.TextInput(name = 'Child Ages', value = "0, 5, 14")

#Add the "Partnered" toggle, which upon clicking, adds the controls for the second wage
partner_toggle = pn.widgets.Switch(
    name = 'Partnered', width=50, align=('start', 'center'))
partner_hrly_wage_input = pn.widgets.FloatInput(
    name = 'Partner Hourly Wage', value = 22.70, disabled = True, width=120)
partner_hours_worked_input = pn.widgets.IntInput(
    name = 'Partner Hours Worked', value = 0, disabled = True, width=120)

# watch the partner toggle to enable/disable the partner controls
def update_partner_controls(event):
    if partner_toggle.value:
        partner_hrly_wage_input.disabled = False
        partner_hours_worked_input.disabled = False
    else:
        partner_hrly_wage_input.disabled = True
        partner_hrly_wage_input.value = 22.70
        partner_hours_worked_input.disabled = True 
        partner_hours_worked_input.value = 0

partner_toggle.param.watch(update_partner_controls, 'value')   


go_button = pn.widgets.Button(
    name='Calculate !', button_type='success', width=100, height=60, align=('start', 'center'))

data_download = pn.widgets.FileDownload(
    'output.csv', label='Download output.csv', button_type='primary', 
    width=200, align=('start', 'center'))

widget_box = pn.WidgetBox(
    '### Policy parameters',
    pn.Row(pn.pane.Markdown('**Name**', width=100), 
           '**Built-in (BEFU23) or uploaded parameter file**'),
    policy_controls[0].row,
    policy_controls[1].row,
    policy_controls[2].row,
    policy_controls[3].row,
    pn.layout.Divider(),
    '### Family specification',
    pn.Row(hrly_wage_input, max_hours_input, child_age_input),
    pn.Row(accom_cost_input, as_area_input, accom_type_input), 
    pn.Row(pn.Column(pn.pane.Markdown("Partnered", margin=1), partner_toggle, width=80, height=30, 
                     align=('center', 'start')), partner_hrly_wage_input, partner_hours_worked_input, 
                     align=('center', 'center')),
    pn.layout.Divider(),
    pn.Row(income_choice_input, wep_scaling_input),
    go_button,
    data_download,
    width = 450)

# ------------------------------------------------------------------------------------

# Initial plots and table
child_ages = str_to_ints(child_age_input.value)

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
    var: pn.pane.Plotly(rate_figs[var].to_dict(), width=1000, height=400) for var in RATE_VARS}
emtr_tab = pn.Column(
    '## Net Income', rate_panes['annual_net_income'],
    '## Effective Marginal Tax Rate', rate_panes['emtr'],
    '## Replacement Rate', rate_panes['replacement_rate'],
    '## Participation Tax Rate', rate_panes['participation_tax_rate'],
    width = 1000, height=2000, name = 'EMTR')

comp_tab = pn.Column(width = 1000, height=2000, name = 'Income Composition')

def update_comp_tab(comp_figs):
    """Update the composition tab with new figures"""
    comp_tab.clear()
    for scenario, fig in comp_figs.items():
        comp_tab.append(f'## {scenario}')
        comp_tab.append(pn.pane.Plotly(fig.to_dict(), width=1000, height=450))    

update_comp_tab(comp_figs)

# Instructions tab
with open('instructions.md', 'r') as f:
    instructions = pn.pane.Markdown(
        f.read(), name = "Instructions", width=600)

tabs = pn.Tabs(
    emtr_tab, comp_tab, instructions, 
    width = 1000, height=2000, active=0)

content = pn.Row(widget_box, pn.Spacer(width=30), tabs, width=1500, height=2000).servable(target='content')

#-------------------------------------------------------------------------------------

def update(event):
    """Update the plot and table when the Go button is clicked"""

    child_ages = str_to_ints(child_age_input.value)

    params = {pc.name_input.value: pc.params for pc in policy_controls if pc.params is not None}

    rate_figs, comp_figs = figs_save_data(
        params, partner_toggle.value, hrly_wage_input.value, 
        child_ages, partner_hrly_wage_input.value, partner_hours_worked_input.value,
        accom_cost_input.value, accom_type_input.value, as_area_input.value, 
        max_hours_input.value, WEPScaling[wep_scaling_input.value],
        IncomeChoice[income_choice_input.value])
    for key in rate_figs:
        rate_panes[key].object=rate_figs[key].to_dict()

    update_comp_tab(comp_figs)
 
go_button.on_click(update)

# turn off "Loading" message
msg = js.document.getElementById("message")
msg.innerHTML = ''