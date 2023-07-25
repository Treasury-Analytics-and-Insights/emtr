import plotly.express as px
import emtr

def fig_table_data(parameters, hrly_wage, max_hours, accom_cost, as_area, accom_type):
    
    output = emtr.emtr(
        parameters, partnered = False, wage1_hourly = hrly_wage, children_ages=[], max_wage = max_hours*hrly_wage,
        as_accommodation_costs = accom_cost, as_area = as_area, 
        as_accommodation_rent = accom_type == 'Rent')
    
    fig = do_plotly(output)
    output.to_csv('subset_data.csv', index=False)
    return fig, output


def do_plotly(output):
    fig = px.line(output, x='hours1', y='emtr', title='Effective marginal tax rate')
    return fig
 
