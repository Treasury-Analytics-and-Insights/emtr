from enum import Enum
import os

import pandas as pd
import panel as pn
import plotly.express as px
import plotly.graph_objects as go
import yaml

import emtr

RATE_VARS = ['annual_net_income', 'emtr', 'replacement_rate', 'participation_tax_rate']

ParamSource = Enum('ParamSource', 'built-in upload')

IncomeChoice = Enum('IncomeChoice', 'WfF Ben Max')

class WEPScaling(Enum):
    Average = 1
    Winter = 12/5
    Summer = 0




# a class the holds the widgets for the policy controls

class PolicyControl:
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
            filename=self.builtin_param_select.value + '.yaml', button_type='primary', width=150, height=30)
        
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


    



def emtr_with_income_choice(emtr_param_func, params: dict, income_choice: IncomeChoice):
    
    wff_emtr = emtr_param_func(params)
    if income_choice == IncomeChoice.WfF:
        return wff_emtr
    
    # disable IWTC
    ben_params = params.copy()
    ben_params['FamilyAssistance_IWTC_Rates_UpTo3Children'] = 0
    ben_params['FamilyAssistance_IWTC_Rates_SubsequentChildren'] = 0
    ben_emtr = emtr_param_func(ben_params)
    if income_choice == IncomeChoice.Ben:
        return ben_emtr
    
    # for each row, choose the dataframe row with the highest net_income column
    ben_indices = ben_emtr['net_income'] > wff_emtr['net_income']
    max_emtr = wff_emtr.copy()
    max_emtr.loc[ben_indices] = ben_emtr.loc[ben_indices]
    return max_emtr



def figs_save_data(
        params: dict, partnered, hrly_wage, children_ages, 
        partner_hrly_wage, partner_hours, accom_cost, accom_type, as_area, 
        max_hours, wep_scaling: WEPScaling, income_choice: IncomeChoice):
    
    accom_rent = accom_type == 'Rent'
    max_wage = max_hours*hrly_wage

    # Make a sub-function of emtr that lets us vary the parameters while holding
    # the others constant
    def emtr_param_func(params):
        return emtr.emtr(
            params, partnered, hrly_wage, children_ages, partner_hrly_wage, 
            partner_hours, accom_cost, accom_rent, as_area, max_wage, 
            mftc_wep_scaling=wep_scaling)

    output = {}
    for name, scenario_params in params.items():
        output[name] = emtr_with_income_choice(
            emtr_param_func, scenario_params, income_choice)
    
    comp_figs = {
        scenario: amounts_net_plot(df, weeks_in_year = 52) 
        for scenario, df in output.items()}
    
    # concatenate the results into a single dataframe with a column identifying
    # the scenario
    long = pd.concat(output, axis=0)
    long['scenario'] = long.index.get_level_values(0)
    long.index = long.index.droplevel(0)
    
    rate_figs = {var: rate_plot(long, var) for var in RATE_VARS}

    long.to_csv('output.csv', index=False)

    return rate_figs, comp_figs

def rate_plot(output, var_name):
    y_label = {
        'annual_net_income': 'Net Income',
        'emtr': 'Effective marginal tax rate',
        'replacement_rate': 'Replacement rate',
        'participation_tax_rate': 'Participation tax rate'
    }[var_name]

    # subset to the relevant columns
    plot_data = output[['gross_wage1_annual', 'hours1', var_name, 'scenario']].copy()

    # clip the values to the range 0-1.1
    if var_name != 'annual_net_income':
        plot_data[var_name] = plot_data[var_name].clip(lower=0, upper=1.1)

    fig = px.line(
        plot_data, x='gross_wage1_annual', y=var_name, color='scenario', 
        labels={"gross_wage1_annual": "Annual gross wage income ($)", var_name: y_label},
        line_dash="scenario",
        color_discrete_sequence=["#56B4E9", "#E69F00"], 
        template="plotly_white")
    
    fig.update_traces(hovertemplate=None)

    fig.add_trace(
        go.Scatter(
            x=plot_data['hours1'], y=[0]*len(plot_data), line=dict(width=0),
            xaxis="x2", hoverinfo="skip", mode="lines", showlegend=False))
    
    fig.update_layout(
        xaxis2={
            'overlaying': "x", 'nticks': 10, 'side': "top", 'title': "Hours/week", 
            'automargin': True, 'showline': True},
        xaxis={
            'title': "Annual gross wage income ($)", 'tickprefix': "$",
            'automargin': True, 'showline': True, 'mirror': True},
        
        yaxis={
            'title': y_label, 'tickformat': ".0%", 
            'automargin': True, 'showline': True, 'mirror': True},
        legend={'x': 100, 'y': 0.5},
        hovermode="x")
    
    if var_name == 'annual_net_income':
        fig.update_layout(
            yaxis={
                'title': "Income ($)", 'tickformat': "$", 
                'automargin': True, 'showline': True, 'mirror': True},
                )
    
    return fig

def string_to_list_of_integers(s):
    # Split the string at commas and remove any whitespace
    integer_strings = s.split(',')

    # Convert the integer strings to actual integers using list comprehension
    integer_list = [int(num.strip()) for num in integer_strings]

    return integer_list


def amounts_net_plot(emtr_output, weeks_in_year):
    
    cmap = px.colors.qualitative.Alphabet
    colour_indices = {
        "Best Start": 17, "Winter Energy": 19, "Accomodation Supplement": 24,
        "IWTC": 3, "FTC": 1, "MFTC": 5, "IETC": 6, "Net Core Benefit": 7,
        "Net Wage": 8, "Net Wage (Partner)": 9, "Tax on Core Benefit": 10,
        "Tax on Wage and ACC": 11
    }
    
    gross_wage_annual = emtr_output['gross_wage1_annual']
    
    annuals = emtr_output[
        ['net_benefit1', 'net_benefit2', 'gross_benefit1', 'gross_benefit2', 
         'gross_wage1', 'gross_wage2', 'net_wage1', 'net_wage2', 'wage1_tax', 
         'wage2_tax', 
         'wage1_acc_levy',
         'wage2_acc_levy', 'ietc_abated1', 'ietc_abated2', 'ftc_abated', 'mftc', 
         'iwtc_abated', 'as_amount', 'winter_energy', 'bs_total', 'net_income']
         ]*weeks_in_year
                           
        
    annuals['net_benefit'] = annuals['net_benefit1'] + annuals['net_benefit2']
    annuals['benefit_tax'] = -(annuals['gross_benefit1'] + annuals['gross_benefit2']
                             - annuals['net_benefit1'] - annuals['net_benefit2'])
    annuals['gross_wage'] = annuals['gross_wage1'] + annuals['gross_wage2']
    annuals['wage_tax_and_ACC'] = -(annuals['wage1_tax'] + annuals['wage2_tax']
                          + annuals['wage1_acc_levy'] + annuals['wage2_acc_levy'])
    annuals['ietc_abated'] = annuals['ietc_abated1'] + annuals['ietc_abated2']

    fig = go.Figure()
    
    # Add invisible trace for xaxis2
    fig.add_trace(
        go.Scatter(x=emtr_output['hours1'], y=[0] * len(emtr_output), line=dict(width=0), 
                   xaxis="x2", showlegend=False, hoverinfo="skip", mode="lines"))
    
    # Layout configuration
    fig.update_layout(
        xaxis2=dict(overlaying="x", nticks=10, side="top", title="Hours/week", automargin=True, showline=True),
        xaxis=dict(title="Annual gross wage income ($)", tickformat="$", automargin=True, zeroline=True, showline=True, mirror=True),
        yaxis=dict(title="Income ($)", tickformat="$", automargin=True, zeroline=True, showline=True, mirror=True),
        legend=dict(x=100, y=0.5),
        hovermode="x"
    )

    def add_trace(col_name, long_name, stack_group='two'):
        fig.add_trace(
            go.Scatter(x=gross_wage_annual, y=annuals[col_name], type='scatter', mode='none',
                        name=long_name, fillcolor=cmap[colour_indices[long_name]],
                        stackgroup=stack_group, 
                        hovertemplate=f"{long_name}: %{{y:$,.0f}}<extra></extra>"))  

    add_trace('wage_tax_and_ACC', 'Tax on Wage and ACC', 'one')
    add_trace('benefit_tax', 'Tax on Core Benefit', 'one')
    add_trace('net_wage2', 'Net Wage (Partner)')
    add_trace('net_wage1', 'Net Wage')
    add_trace('net_benefit', 'Net Core Benefit')
    add_trace('ietc_abated', 'IETC')
    add_trace('mftc', 'MFTC')
    add_trace('ftc_abated', 'FTC')
    add_trace('iwtc_abated', 'IWTC')
    add_trace('as_amount', 'Accomodation Supplement')
    add_trace('winter_energy', 'Winter Energy')
    add_trace('bs_total', 'Best Start')
    
    
    # Adding a line for Net Income
    fig.add_trace(go.Scatter(x=gross_wage_annual, y=annuals['net_income'], mode='lines',
                                 name='Net Income', line=dict(color='black'),
                                 hovertemplate="Net Income: %{y:$,.0f}<extra></extra>"))
    
    return fig