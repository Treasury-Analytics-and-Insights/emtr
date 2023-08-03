from enum import Enum

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import emtr

RATE_VARS = ['emtr', 'replacement_rate', 'participation_tax_rate']
INCOME_VARS = ['net_income']

IncomeChoice = Enum('IncomeChoice', 'WfF Ben Max')

class WEPScaling(Enum):
    Average = 1
    Winter = 12/5
    Summer = 0


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



def fig_table_data(
        sq_params: dict, reform_params: dict, partnered, hrly_wage, children_ages, 
        partner_hrly_wage, partner_hours, accom_cost, accom_type, as_area, 
        max_hours, wep_scaling: WEPScaling, sq_income_choice: IncomeChoice, 
        reform_income_choice: IncomeChoice):
    
    accom_rent = accom_type == 'Rent'
    max_wage = max_hours*hrly_wage

    # Make a sub-function of emtr that lets us vary the parameters while holding
    # the others constant
    def emtr_param_func(params):
        return emtr.emtr(
            params, partnered, hrly_wage, children_ages, partner_hrly_wage, 
            partner_hours, accom_cost, accom_rent, as_area, max_wage, 
            mftc_wep_scaling=wep_scaling)

    sq_output = emtr_with_income_choice(emtr_param_func, sq_params, sq_income_choice)
    
    reform_output = emtr_with_income_choice(
        emtr_param_func, reform_params, reform_income_choice)

    # concatenate the two dataframes row-wise and add a column to identify the two
    # sets of results
    output = pd.concat([sq_output, reform_output], axis=0)
    output['scenario'] = ['SQ']*len(sq_output) + ['Reform']*len(reform_output)

    figs = {var: rate_plot(output, var) for var in RATE_VARS}
    
    output.to_csv('output.csv', index=False)
    return figs, output

def fig_income_data(
        sq_params: dict, reform_params: dict, partnered, hrly_wage, children_ages, 
        partner_hrly_wage, partner_hours, accom_cost, accom_type, as_area, 
        max_hours, wep_scaling: WEPScaling, sq_income_choice: IncomeChoice, 
        reform_income_choice: IncomeChoice):
    
    accom_rent = accom_type == 'Rent'
    max_wage = max_hours*hrly_wage

    # Make a sub-function of emtr that lets us vary the parameters while holding
    # the others constant
    def emtr_param_func(params):
        return emtr.emtr(
            params, partnered, hrly_wage, children_ages, partner_hrly_wage, 
            partner_hours, accom_cost, accom_rent, as_area, max_wage, 
            mftc_wep_scaling=wep_scaling)

    sq_output = emtr_with_income_choice(emtr_param_func, sq_params, sq_income_choice)
    
    reform_output = emtr_with_income_choice(
        emtr_param_func, reform_params, reform_income_choice)
    
    sq_output['net_income'] = sq_output['net_income'] *52
    reform_output['net_income'] = reform_output['net_income'] *52

    # concatenate the two dataframes row-wise and add a column to identify the two
    # sets of results
    output = pd.concat([sq_output, reform_output], axis=0)
    output['scenario'] = ['SQ']*len(sq_output) + ['Reform']*len(reform_output)

    figs = {var: income_plot(output, var) for var in INCOME_VARS}
    
    output.to_csv('output.csv', index=False)
    return figs, output


def rate_plot(output, var_name):
    y_label = {
        'emtr': 'Effective marginal tax rate',
        'replacement_rate': 'Replacement rate',
        'participation_tax_rate': 'Participation tax rate'
    }[var_name]

    # subset to the relevant columns
    plot_data = output[['gross_wage1_annual', 'hours1', var_name, 'scenario']].copy()

    # clip the values to the range 0-1.1
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
        
    return fig

def income_plot(output, var_name):
    y_label = {
        'net_income': 'Net Income'
    }[var_name]

    # subset to the relevant columns
    plot_data = output[['gross_wage1_annual', 'hours1', var_name, 'scenario']].copy()
 
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
            'title': "Income ($)", 'tickformat': "$", 
            'automargin': True, 'showline': True, 'mirror': True},
        legend={'x': 100, 'y': 0.5},
        hovermode="x")
        
    return fig

def string_to_list_of_integers(s):
    # Split the string at commas and remove any whitespace
    integer_strings = s.split(',')

    # Convert the integer strings to actual integers using list comprehension
    integer_list = [int(num.strip()) for num in integer_strings]

    return integer_list
