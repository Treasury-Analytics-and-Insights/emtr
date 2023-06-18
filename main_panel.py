import js
import pandas as pd
import matplotlib.pyplot as plt
import panel as pn

from pyodide.http import open_url
from pyodide.ffi import create_proxy

pn.extension(sizing_mode="stretch_width")

data = pd.read_csv('dist_exp_data.csv')

def get_subset_data(pop_type, income_type):
    desc = {'Household': 'All households', 'Family': 'All families'}
    subset_data = data[(data['Income Type'] == 'Income Quantiles') & 
                     (data['Population Type'] == pop_type) & 
                     (data.Description == desc[pop_type]) & 
                     (data['Income Measure'] == income_type)]
    return(subset_data)

def plot(ax, plot_data, title):
    
    bars = ax.barh(plot_data['Income Group'], plot_data.Value.astype(int), height=0.7)
    ax.bar_label(bars)
    plt.title(title)

def do_plot(fig, pop_type, income_type):
    subset_data = get_subset_data(pop_type, income_type)
    fig.clear()
    ax = fig.subplots()
    plot(ax, subset_data, f"{pop_selector.value}: {measure_selector.value}")
    
def table(subset_data):
    table_div = Element("table-area")
    table_div.element.innerHTML = subset_data.to_html(index=False)


pop_selector = pn.widgets.Select(
    name='Population Type', options = ['Household', 'Family']).servable(target='pop_type')

measure_selector = pn.widgets.Select(
    name='Income Measure', options = data['Income Measure'].unique().tolist()).servable(target='income_type')

go_button = pn.widgets.Button(name='Click me', button_type='primary').servable(target='go_button')

fig = plt.figure(figsize=(10,8))
do_plot(fig, pop_selector.value, measure_selector.value)

mpl = pn.pane.Matplotlib(fig).servable(target='plot-area')


def update(event):
    do_plot(fig, pop_selector.value, measure_selector.value)
    mpl.param.trigger('object')
    
    
    
    #table(subset_data)

go_button.on_click(update)

#ele_proxy = create_proxy(update)
#income_selector.addEventListener("change", ele_proxy)
