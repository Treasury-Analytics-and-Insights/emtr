import js
import pandas as pd
import matplotlib.pyplot as plt

from pyodide.http import open_url
from pyodide.ffi import create_proxy

data = pd.read_csv('dist_exp_data.csv')

def get_subset_data(pop_type, income_type):
    desc = {'Household': 'All households', 'Family': 'All families'}
    subset_data = data[(data['Income Type'] == 'Income Quantiles') & 
                     (data['Population Type'] == pop_type) & 
                     (data.Description == desc[pop_type]) & 
                     (data['Income Measure'] == income_type)]
    return(subset_data)

def plot(plot_data, title):
    fig, ax = plt.subplots()
    bars = ax.barh(plot_data['Income Group'], plot_data.Value.astype(int), height=0.7)
    ax.bar_label(bars)
    plt.title(title)
    display(fig, target="graph-area", append=False)

def table(subset_data):
    table_div = Element("table-area")
    table_div.element.innerHTML = subset_data.to_html(index=False)

pop_selector = js.document.getElementById("pop_type")
income_selector = js.document.getElementById("income_type")

def update():
    #display(income_selector.value, target='table-area', append=False)
    subset_data = get_subset_data(pop_selector.value, income_selector.value)
    plot(subset_data, f"{pop_selector.value}: {income_selector.value}")
    table(subset_data)

#ele_proxy = create_proxy(update)
#income_selector.addEventListener("change", ele_proxy)
