import pandas as pd
import plotly.express as px

import emtr

def fig_table_data(
        sq_params, reform_params, hrly_wage, max_hours, accom_cost, as_area, 
        accom_type):
    
    sq_output = emtr.emtr(
        sq_params, partnered = False, wage1_hourly = hrly_wage, children_ages=[], 
        max_wage = max_hours*hrly_wage,
        as_accommodation_costs = accom_cost, as_area = as_area, 
        as_accommodation_rent = accom_type == 'Rent')
    
    reform_output = emtr.emtr(
        reform_params, partnered = False, wage1_hourly = hrly_wage, children_ages=[], 
        max_wage = max_hours*hrly_wage,
        as_accommodation_costs = accom_cost, as_area = as_area, 
        as_accommodation_rent = accom_type == 'Rent')
    
    # concatenate the two dataframes row-wise and add a column to identify the two
    # sets of results
    output = pd.concat([sq_output, reform_output], axis=0)
    output['scenario'] = ['SQ']*len(sq_output) + ['Reform']*len(reform_output)

    fig = do_plotly(output)
    output.to_csv('output.csv', index=False)
    return fig, output


def do_plotly(output):
    fig = px.line(
        output, x='hours1', y='emtr', color='scenario', 
        title='Effective marginal tax rate')
    return fig
 
