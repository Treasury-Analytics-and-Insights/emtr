from enum import Enum

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import emtr

RATE_VARS = ['annual_net_income', 'emtr', 'replacement_rate', 'participation_tax_rate']

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


def figs_save_data(
        params: dict, partnered, hrly_wage, children_ages, 
        partner_hrly_wage, partner_hours, accom_cost, accom_type, as_area, 
        max_hours, wep_scaling: WEPScaling, income_choice: IncomeChoice):
    
    accom_rent = accom_type == 'Rent'
    max_wage = max_hours*hrly_wage

    weeks_in_year = {
        scenario:emtr.wks_in_year(p['modelyear']) for scenario, p in params.items()}

    # Make a sub-function of emtr that lets us vary the parameters while holding
    # the others constant
    def emtr_param_func(params_):
        return emtr.emtr(
            params_, partnered, hrly_wage, children_ages, partner_hrly_wage, 
            partner_hours, accom_cost, accom_rent, as_area, max_wage, 
            mftc_wep_scaling=wep_scaling)

    output = {}
    for name, scenario_params in params.items():
        output[name] = emtr_with_income_choice(
            emtr_param_func, scenario_params, income_choice)
    
    comp_figs = {
        scenario: amounts_net_plot(df, weeks_in_year[scenario]) 
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
    
    if var_name == 'annual_net_income':
        # display the y value to the nearest dollar (with a comma for thousands)
        fig.update_traces(hovertemplate="%{y:$,.0f}")
    else:
        # display the y value as a percentage to 1 decimal place
        fig.update_traces(hovertemplate="%{y:.1%}")
        

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
            #round ticks to nearest dollar (for the sake of the hover)
            'tickformat': ",.0f",
            'automargin': True, 'showline': True, 'mirror': True},
        
        yaxis={
            'title': y_label, 'tickformat': ".0%", 
            'automargin': True, 'showline': True, 'mirror': True},
        legend={'x': 100, 'y': 0.5},
        
        hovermode="x unified")
    
    if var_name == 'annual_net_income':
        fig.update_layout(
            yaxis={
                'title': "Income ($)", 'tickformat': "$", 
                'automargin': True, 'showline': True, 'mirror': True},
                )
    
    return fig

def str_to_ints(s):
    # Split the string at commas and remove any whitespace
    integer_strings = s.split(',')

    # Convert the integer strings to actual integers using list comprehension
    # the if statement filters out any empty strings
    integer_list = [int(num.strip()) for num in integer_strings if num.strip()]

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
        # co-pilot used this syntax for the dictionaries - can't be botherd changing it
        xaxis2=dict(overlaying="x", nticks=10, side="top", title="Hours/week", automargin=True, showline=True),
        xaxis=dict(
            title="Annual gross wage income ($)", tickprefix="$", tickformat=",.0f", automargin=True, 
            zeroline=True, showline=True, mirror=True),
        yaxis=dict(title="Income ($)", tickformat="$", automargin=True, zeroline=True, showline=True, 
                   mirror=True),
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