import pandas as pd
import matplotlib.pyplot as plt
import panel as pn


pn.extension(sizing_mode="stretch_width")
pn.extension('tabulator')

pn.widgets.Tabulator.theme = 'bootstrap4'
pn.widgets.Tabulator.pagination = 'local'
#pn.pane.Matplotlib.format = 'svg' doesn't work
#pn.widgets.WidgetBox.theme = 'dark_minimal'  probably need the right css file

subplot_dims = {
    1: (1,1), 2: (1,2), 3: (1,3), 4: (2,2), 5: (2,3), 6: (2,3), 7: (2,4), 
    8:(2,4), 9: (3,3), 10: (3,4), 11: (3,4), 12: (3,4)}

def get_figsize(n_groups):
    if n_groups <= 4:
        return {1: (10,6), 2: (15,5), 3: (18,4), 4: (15,10)}[n_groups]
    elif n_groups <= 8:
        return (18, 8)
    else: 
        return(18,12)
    
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

def pop_tick_formatter(x, pos):
    """Format the y-axis ticks as thousands."""
    return '{:,.0f}'.format(x/1000) + 'k'   

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
            # only show the x-axis label on the bottom row
            if i >= len(groups) - ncols:
                ax.set_xlabel('Population')
            if i % ncols == 0:  
                ax.set_ylabel(income_type)
            ax.set_xlim(0, max_pop)
            # format the x-axis ticks as thousands
            ax.xaxis.set_major_formatter(pop_tick_formatter)
            # draw major grid lines on the x-axis in light grey
            ax.xaxis.grid(True, color='lightgrey')
        else:
            ax.bar(plot_data['Income Group'], plot_data['Plot Population'], width=0.7)
            if i % ncols == 0:  
                ax.set_ylabel('Population')
            if i >= len(groups) - ncols:
                ax.set_xlabel(income_type)
            ax.set_ylim(0, max_pop)
            # format the y-axis ticks as thousands
            ax.yaxis.set_major_formatter(pop_tick_formatter)
            # draw major grid lines on the y-axis in light grey
            ax.yaxis.grid(True, color='lightgrey')

        # format plot in a tufte style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='both', which='major', labelsize=8)
        
        ax.set_title(group)

    fig.suptitle(f"{pop_type}: {income_measure}")
    fig.savefig('plot.svg', bbox_inches='tight')
    subset_data.drop('Plot Population', axis=1).to_csv('subset_data.csv', index=False)
    return fig

title = pn.Column(
    pn.Row(
        pn.pane.Markdown('# Income Distribution Explorer', width=600),
        pn.pane.Markdown('*Best viewed full screen*', align = ('end', 'end'))),
    pn.layout.Divider()).servable(target='title')


# all the controls are in a widget box

pop_selector = pn.widgets.Select(
    name='Population Type', options = ['Household', 'Family'])

group_selector = pn.widgets.CheckBoxGroup(
    name = 'Group', options = groups[pop_selector.value], value=[groups[pop_selector.value][0]]
    )

def update_groups(event):
    group_selector.options = groups[event.new]
    group_selector.value = [groups[event.new][0]]

pop_selector.param.watch(update_groups, 'value')

measure_selector = pn.widgets.Select(
    name='Income Measure', options = data['Income Measure'].unique().tolist()
    )

income_type_selector = pn.widgets.Select(
    name='Income Type', options = data['Income Type'].unique().tolist()
)

go_button = pn.widgets.Button(
    name='Go', button_type='success', width=100, align=('center', 'center'))

go_button_row = pn.Row(pn.pane.Markdown("Subset and plot", align = ('end', 'center')), go_button)

pn.WidgetBox(
    pop_selector, group_selector, measure_selector, income_type_selector, 
    go_button_row).servable(target='widget_box')


fig = do_plot(
    pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value)

mpl = pn.pane.Matplotlib(
    fig, tight=True, 
    sizing_mode='scale_both', 
    max_width=1000,
    max_height=800
    )

download = pn.widgets.FileDownload(
    'subset_data.csv', label='Download subset_data.csv', button_type='primary', 
    width=200, align=('center', 'center'))

table = pn.widgets.Tabulator(
    get_subset_data(
        pop_selector.value, group_selector.value, measure_selector.value, 
        income_type_selector.value).drop('Plot Population', axis=1), 
        show_index=False, width=1000, height=600)

with open('instructions.md', 'r') as f:
    instructions = pn.pane.Markdown(f.read(), name = "Instructions", width=600)

with open('definitions.md', 'r') as f:
    definitions = pn.pane.Markdown(f.read(), name = "Definitions", width=600)

with open('idi_disclaimer.md', 'r') as f:
    disclaimer = pn.pane.Markdown(f.read(), width=1000)

pn.Tabs(
    pn.Column(mpl, disclaimer, name="Plots"), 
    pn.Column(download, table, disclaimer, name="Data"), instructions, 
    definitions).servable(target='tabs')

def update(event):
    fig = do_plot(pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value)
    mpl.object=fig
    #svg.object='plot.svg'
    #table.object=get_subset_data(
    #    pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value)
    table.value=get_subset_data(
        pop_selector.value, group_selector.value, measure_selector.value, income_type_selector.value
        ).drop('Plot Population', axis=1)


go_button.on_click(update)
