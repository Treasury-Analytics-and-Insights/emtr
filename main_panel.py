import pandas as pd
import matplotlib.pyplot as plt
import panel as pn


pn.extension(sizing_mode="stretch_width")

subplot_dims = {
    1: (1,1), 2: (1,2), 3: (1,3), 4: (2,2), 5: (2,3), 6: (2,3), 7: (2,4), 
    8:(2,4), 9: (3,3), 10: (3,4), 11: (3,4), 12: (3,4)}

def get_figsize(n_groups):
    return {1: (10,8), 2: (18,8), 3: (18,8)}.get(n_groups, (18, 14))
    
data = pd.read_csv('dist_exp_data.csv')
# make a Plot Population column that is the same as Population but 
# numeric and non-numeric values are set to 0
data['Plot Population'] = data.Population
data.loc[~data.Population.str.isnumeric(), 'Plot Population'] = 0
data['Plot Population'] = data['Plot Population'].astype(int)

# each population type has a different set of groups
groups = {
    pop_type: data[data['Population Type'] == pop_type].Description.unique().tolist() 
    for pop_type in ['Household', 'Family']}
    

def get_subset_data(pop_type, groups, income_measure, income_type):
    """Return a subset of the data based on the population type, income measure and groups."""
    subset_data = data[(data['Income Type'] == income_type) & 
                     (data['Population Type'] == pop_type) & 
                     (data.Description.isin(groups)) & 
                     (data['Income Measure'] == income_measure)]
    return subset_data


def do_plot(pop_type, groups, income_measure, income_type):
    fig = plt.figure(figsize=get_figsize(len(groups)))
    nrows, ncols = subplot_dims[len(groups)]
    subset_data = get_subset_data(pop_type, groups, income_measure, income_type)
    # get the max population for each group to set the axis limits
    max_pop = subset_data['Plot Population'].max()    
    for i, group in enumerate(groups):

        plot_data = subset_data[subset_data.Description == group]
        ax = fig.add_subplot(nrows, ncols, i+1)

        # if income_type is Income_band, then make the barplot horizontal
        if income_type == 'Income Bands':
            ax.barh(plot_data['Income Group'], plot_data['Plot Population'], height=0.7)
            ax.set_xlabel('Population')
            ax.set_ylabel(income_type)
            ax.set_xlim(0, max_pop)
        else:
            ax.bar(plot_data['Income Group'], plot_data['Plot Population'], width=0.7)
            ax.set_ylabel('Population')
            ax.set_xlabel(income_type)
            ax.set_ylim(0, max_pop)
        ax.set_title(group)

    fig.suptitle(f"{pop_type}: {income_measure}")
    return fig

title = pn.pane.Markdown('# Income Distribution Explorer').servable(target='title')

pop_selector = pn.widgets.Select(
    name='Population Type', options = ['Household', 'Family']).servable(target='pop_type')

group_selector = pn.widgets.CheckBoxGroup(
    name = 'Group', options = groups[pop_selector.value], value=[groups[pop_selector.value][0]]
    ).servable(target='groups')

def update_groups(event):
    group_selector.options = groups[event.new]
    group_selector.value = [groups[event.new][0]]

pop_selector.param.watch(update_groups, 'value')

measure_selector = pn.widgets.Select(
    name='Income Measure', options = data['Income Measure'].unique().tolist()
    ).servable(target='income_measure')

income_type_selector = pn.widgets.Select(
    name='Income Type', options = data['Income Type'].unique().tolist()
).servable(target='income_type')

go_button = pn.widgets.Button(name='Click me', button_type='primary').servable(target='go_button')

fig = do_plot(
    pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value)

mpl = pn.pane.Matplotlib(
    fig, tight=True, 
    sizing_mode='scale_both', 
    max_height=800, max_width=1000
    ).servable(target='plot-area')

# I want to make this table appear with scroll bars when it gets too big
table = pn.pane.DataFrame(
    get_subset_data(pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value), 
    index=False, sizing_mode="stretch_both", max_height=300).servable(target="table-area")

text = pn.pane.Markdown(
    "These results are not official statistics. They have been created for research purposes from the "
    "Integrated Data Infrastructure (IDI) which is carefully managed by Stats NZ. For more information "
    "about the IDI please visit https://www.stats.govt.nz/integrated-data/. The results are based in part "
    "on tax data supplied by Inland Revenue to Stats NZ under the Tax Administration Act 1994 for "
    "statistical purposes. Any discussion of data limitations or weaknesses is in the context of using "
    "the IDI for statistical purposes, and is not related to the data’s ability to support Inland Revenue’s "
    "core operational requirements.").servable(target='text-area')

def update(event):
    fig = do_plot(pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value)
    mpl.object=fig
    table.object=get_subset_data(
        pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value)


go_button.on_click(update)
