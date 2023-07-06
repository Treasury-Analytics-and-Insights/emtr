import pandas as pd
import matplotlib.pyplot as plt


SUBPLOT_DIMS = {
    1: (1,1), 2: (1,2), 3: (1,3), 4: (2,2), 5: (2,3), 6: (2,3), 7: (2,4), 
    8:(2,4), 9: (3,3), 10: (3,4), 11: (3,4), 12: (3,4)}


def load_data(path):
    data = pd.read_csv(path)
    # make a Plot Population column that is the same as Population but 
    # numeric and non-numeric values are set to 0
    data['Plot Population'] = data.Population
    data.loc[~data.Population.str.isnumeric(), 'Plot Population'] = 0
    data['Plot Population'] = data['Plot Population'].astype(int)
    return data


def get_figsize(n_groups):
    if n_groups <= 4:
        return {1: (10,6), 2: (15,5), 3: (18,4), 4: (15,10)}[n_groups]
    elif n_groups <= 8:
        return (18, 8)
    else: 
        return(18,12)

def fig_table_data(data, pop_type, groups, income_measure, income_type):
    """Return a dataframe with the data for the selected population type, 
    groups, income measure and income type."""
    subset = data[
        (data['Income Type'] == income_type) & (data['Population Type'] == pop_type) & 
        (data.Description.isin(groups)) & (data['Income Measure'] == income_measure)]
    fig = do_plot(subset, pop_type, groups, income_measure, income_type)
    subset=subset.drop('Plot Population', axis=1)
    subset.to_csv('subset_data.csv', index=False)
    return fig, subset


def pop_tick_formatter(x, pos):
    """Format axis ticks as thousands.  The pos argument is required by 
    matplotlib but not used."""
    return '{:,.0f}'.format(x/1000) + 'k'   

def do_plot(subset, pop_type, groups, income_measure, income_type):
    """Plot the income distribution for the selected population type, groups, 
    income measure and income type."""
    fig = plt.figure(figsize=get_figsize(len(groups)),)
    nrows, ncols = SUBPLOT_DIMS[len(groups)]
    # get the max population for each group to set the axis limits
    max_pop = subset['Plot Population'].max()    
    for i, group in enumerate(groups):

        plot_data = subset[subset.Description == group]
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
    return fig
