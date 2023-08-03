from enum import Enum

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import emtr

RATE_VARS = ['emtr', 'replacement_rate', 'participation_tax_rate']

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

def string_to_list_of_integers(s):
    # Split the string at commas and remove any whitespace
    integer_strings = s.split(',')

    # Convert the integer strings to actual integers using list comprehension
    integer_list = [int(num.strip()) for num in integer_strings]

    return integer_list

def amounts_net_plot(params, partnered, hrly_wage, children_ages, 
        partner_hrly_wage, partner_hours, accom_cost, accom_type, as_area, 
        max_hours, inc_limit=None, weeks_in_year=52,
                     display_cols=["Net Income", "Best Start", "Winter Energy", "Accomodation Supplement",
                                   "IWTC", "FTC", "MFTC", "IETC", "Net Core Benefit", "Net Wage",
                                   "Net Wage (Partner)", "Tax on Core Benefit", "Tax on Wage and ACC"]):
    
    # Define the number of colors needed (n=12) and the palette name ("Paired")
    colours = px.colors.qualitative.Plotly
    
    # Define the set_colours dictionary
    # set_colours = {
    #     "Best Start": px.colors.cyclical.Edge[0],
    #     "Winter Energy": px.colors.cyclical.Edge[1],
    #     "Accomodation Supplement": px.colors.cyclical.Edge[2],
    #     "IWTC": px.colors.cyclical.Edge[3],
    #     "FTC": px.colors.cyclical.Edge[4],
    #     "MFTC": px.colors.cyclical.Edge[5],
    #     "IETC": px.colors.cyclical.Edge[6],
    #     "Net Core Benefit": px.colors.cyclical.Edge[7],
    #     "Net Wage": px.colors.cyclical.Edge[8],
    #     "Net Wage (Partner)": px.colors.cyclical.Edge[9],
    #     "Tax on Core Benefit": px.colors.cyclical.Edge[10],
    #     "Tax on Wage and ACC": px.colors.cyclical.Edge[11]
    # }

    set_colours = {
        "Best Start": px.colors.qualitative.Alphabet[17],
        "Winter Energy": px.colors.qualitative.Alphabet[19],
        "Accomodation Supplement": px.colors.qualitative.Alphabet[24],
        "IWTC": px.colors.qualitative.Alphabet[3],
        "FTC": px.colors.qualitative.Alphabet[1],
        "MFTC": px.colors.qualitative.Alphabet[5],
        "IETC": px.colors.qualitative.Alphabet[6],
        "Net Core Benefit": px.colors.qualitative.Alphabet[7],
        "Net Wage": px.colors.qualitative.Alphabet[8],
        "Net Wage (Partner)": px.colors.qualitative.Alphabet[9],
        "Tax on Core Benefit": px.colors.qualitative.Alphabet[10],
        "Tax on Wage and ACC": px.colors.qualitative.Alphabet[11]
    }

    accom_rent = accom_type == 'Rent'
    max_wage = max_hours*hrly_wage

    EMTR_table = emtr.emtr(
        params, partnered, hrly_wage, children_ages, partner_hrly_wage, 
        partner_hours, accom_cost, accom_rent, as_area, max_wage)
    
    X = EMTR_table.copy()
    
    # Do we need this?
    # two_adults = (X['net_benefit2'].max() > 0)
    
    # Do we need this?
    # wage1_hourly = X.loc[2, 'gross_wage1'] / X.loc[2, 'hours1']
    
    if inc_limit is None:
        inc_limit = X['gross_wage1_annual'].max()
    
    # Assuming you have already loaded the necessary libraries and defined EMTR_table

    # Calculate net_benefit as the sum of net_benefit1 and net_benefit2
    EMTR_table['net_benefit'] = EMTR_table['net_benefit1'] + EMTR_table['net_benefit2']

    # Calculate benefit_tax as -(gross_benefit1 + gross_benefit2 - net_benefit1 - net_benefit2)
    EMTR_table['benefit_tax'] = -(EMTR_table['gross_benefit1'] + EMTR_table['gross_benefit2']
                             - EMTR_table['net_benefit1'] - EMTR_table['net_benefit2'])

    # Calculate gross_wage as the sum of gross_wage1 and gross_wage2
    EMTR_table['gross_wage'] = EMTR_table['gross_wage1'] + EMTR_table['gross_wage2']

    # Calculate wage_tax_and_ACC as -(wage1_tax + wage2_tax + wage1_acc_levy + wage2_acc_levy)
    EMTR_table['wage_tax_and_ACC'] = -(EMTR_table['wage1_tax'] + EMTR_table['wage2_tax']
                                  + EMTR_table['wage1_acc_levy'] + EMTR_table['wage2_acc_levy'])

    # Calculate IETC_abated as the sum of ietc_abated1 and IETC_abated2
    EMTR_table['ietc_abated'] = EMTR_table['ietc_abated1'] + EMTR_table['ietc_abated2']

    # Calculate ftc_abated, mftc, and IWTC_abated based on relevant columns in EMTR_table

    # Calculate AS_Amount, WinterEnergy, BestStart_Total, and Net_Income based on relevant columns in EMTR_table

    # Now Y <- EMTR_table[, .(gross_wage1_annual, gross_benefit1, ... )], and perform the rest of the steps
    Y = EMTR_table[['gross_wage1_annual', 'gross_benefit1', 'gross_benefit2',
                    'net_benefit', 'net_wage1', 'net_wage2', 'benefit_tax',
                    'gross_wage', 'wage_tax_and_ACC', 'ietc_abated',
                    'ftc_abated', 'mftc', 'iwtc_abated', 'as_amount',
                    'winter_energy', 'bs_total', 'net_income']]

    # Y[, ':=' (gross_benefit1 = NULL, gross_benefit2 = NULL )]
    # Y.drop(columns=['gross_benefit1', 'gross_benefit2'], inplace=True)

    # Y <- Y[, lapply(.SD, function(x) x * weeks_in_year), by=(gross_wage1_annual)]
    Y = Y.apply(lambda x: x * weeks_in_year)

    # Now 'Y' contains the transformed DataFrame with the specified columns and weeks_in_year scaling.

    
    fig = go.Figure()
    
    # Add invisible trace for xaxis2
    fig.add_trace(go.Scatter(x=X['hours1'], y=[0] * len(X), line=dict(width=0), xaxis="x2",
                             showlegend=False, hoverinfo="skip", mode="lines"))
    
    # Layout configuration
    fig.update_layout(
        xaxis2=dict(overlaying="x", nticks=10, side="top", title="Hours/week", automargin=True, showline=True),
        xaxis=dict(title="Annual gross wage income ($)", tickformat="$", automargin=True, zeroline=True, showline=True, mirror=True),
        yaxis=dict(title="Income ($)", tickformat="$", automargin=True, zeroline=True, showline=True, mirror=True),
        legend=dict(x=100, y=0.5),
        hovermode="x"
    )
    
    if "Tax on Wage and ACC" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['wage_tax_and_ACC'], type='scatter', mode='none',
                                 name='Tax on Wage and ACC', fillcolor=set_colours["Tax on Wage and ACC"],
                                 stackgroup='one', hovertemplate="Tax on Wage and ACC: %{y:$,.0f}<extra></extra>"))
    
    if "Tax on Core Benefit" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['benefit_tax'], type='scatter', mode='none',
                                 name="Tax on Core Benefit", fillcolor=set_colours["Tax on Core Benefit"],
                                 stackgroup='one', hovertemplate="Tax on Core Benefit: %{y:$,.0f}<extra></extra>"))
    
    if "Net Wage (Partner)" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['net_wage2'], type='scatter', mode='none',
                                 name='Net Wage (Partner)', stackgroup='two', fillcolor=set_colours["Net Wage (Partner)"],
                                 hovertemplate="Net Wage (Partner): %{y:$,.0f}<extra></extra>"))
    
    if "Net Wage" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['net_wage1'], type='scatter', mode='none',
                                 name='Net Wage', stackgroup='two', fillcolor=set_colours["Net Wage"],
                                 hovertemplate="Net Wage: %{y:$,.0f}<extra></extra>"))
    
    if "Net Core Benefit" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['net_benefit'], type='scatter', mode='none',
                                 name='Net Core Benefit', fillcolor=set_colours["Net Core Benefit"],
                                 stackgroup='two', hovertemplate="Net Core Benefit: %{y:$,.0f}<extra></extra>"))
    
    if "IETC" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['ietc_abated'], type='scatter', mode='none',
                                 name='IETC', fillcolor=set_colours["IETC"],
                                 stackgroup='two', hovertemplate="IETC: %{y:$,.0f}<extra></extra>"))
    
    if "MFTC" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['mftc'], type='scatter', mode='none',
                                 name='MFTC', fillcolor=set_colours["MFTC"],
                                 stackgroup='two', hovertemplate="MFTC: %{y:$,.0f}<extra></extra>"))
    
    if "FTC" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['ftc_abated'], type='scatter', mode='none',
                                 name='FTC', fillcolor=set_colours["FTC"],
                                 stackgroup='two', hovertemplate="FTC: %{y:$,.0f}<extra></extra>"))
    
    if "IWTC" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['iwtc_abated'], type='scatter', mode='none',
                                 name='IWTC', fillcolor=set_colours["IWTC"],
                                 stackgroup='two', hovertemplate="IWTC: %{y:$,.0f}<extra></extra>"))
    
    if "Accomodation Supplement" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['as_amount'], type='scatter', mode='none',
                                 name='Accomodation Supplement', fillcolor=set_colours["Accomodation Supplement"],
                                 stackgroup='two', hovertemplate="Accomodation Supplement: %{y:$,.0f}<extra></extra>"))
    
    if "Winter Energy" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['winter_energy'], type='scatter', mode='none',
                                 name='Winter Energy', fillcolor=set_colours["Winter Energy"],
                                 stackgroup='two', hovertemplate="Winter Energy: %{y:$,.0f}<extra></extra>"))
    
    if "Best Start" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['bs_total'], type='scatter', mode='none',
                                 name='Best Start', fillcolor=set_colours["Best Start"],
                                 stackgroup='two', hovertemplate="Best Start: %{y:$,.0f}<extra></extra>"))
    
    # Adding a line for Net Income
    if "Net Income" in display_cols:
        fig.add_trace(go.Scatter(x=Y['gross_wage1_annual'], y=Y['net_income'], mode='lines',
                                 name='Net Income', line=dict(color='black'),
                                 hovertemplate="Net Income: %{y:$,.0f}<extra></extra>"))
    
    return fig