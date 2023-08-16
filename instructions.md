## Introduction
This is a prototype tool that looks at the the components of income for specified families and how their effective marginal tax rate (EMTR), and related measures, change as they work more hours, taking into account New Zealand's tax and transfer system, and modifications thereof.

The application is written in Python and uses Pyscript (http://pyscript.net) to run the Python in your browser.  No data is sent to the internet.  Pyscript and Panel(https://panel.holoviz.org), which is used to create the user interface, are both relatively new and fast-moving projects, which may impact on the stability of this application.

## Inputs
### Specifying policy parameters

The app comes with a set of built-in policy settings, which correspond to the legislated settings for given tax-years.  For example the settings for the 2020/21 tax-year (April 2020 to March 2021) are labelled "TY21".  TY21 settings would be selected by choosing "built-in" from the first dropdown list, and "TY21" from the second dropdown list.  

If you want to investigate changes to the tax and transfer system, you can specify your own policy settings.  To do this you can click the Download button beside the built-in settings for the desired tax-year, and then edit the downloaded YAML file.  This is just a plain text file, so to edit it it, go to the Downloads folder, right-click on the file and choose "Open with" and then "Notepad" (or your preferred text editor).  The file can then be edited and saved.  

For instance to increase the Winter Energy Payment by $200 p.a. you would change the lines:

```
# Winter energy payment amount. Given to families receiving a core benefit or NZ super. 
Benefits_WinterEnergy_Rates_Single: 450 
Benefits_WinterEnergy_Rates_CoupleOrDeps: 700
```  

to 

```
# Winter energy payment amount. Given to families receiving a core benefit or NZ super. 
Benefits_WinterEnergy_Rates_Single: 650 
Benefits_WinterEnergy_Rates_CoupleOrDeps: 900
```

and then upload the edited file by selecting "upload" on the first dropdown list of an unused policy row and clicking the "Choose File" button to select the edited file.

Once parameters have been chosen you can edit the Name field on the left, which will be used to label plots.

Up to four different policy settings can be modelled at once.  When the app starts the legislated settings for the current tax-year are modelled and labelled "Status Quo".


### Specifying family circumstances

Most of the family parameters should be self-explanatory.  

To specify the number of children and their ages enter a comma separated list of ages in the "Child ages" field.  For no children, leave this field blank.  For example, to specify a family with two children aged 3 and 5, enter "3,5".  

"AS Area" corresponds to the area of residence, and is used to determine the Accommodation Supplement (https://www.msd.govt.nz/about-msd-and-our-work/newsroom/2017/budget-2017/new-regions.html).  

### Income choice

This setting determines the choice between taking a benefit or the in-work-tax-credit and/or minimum family tax credit, which are only accessible if not receiving a benefit.   The default, "Max", chooses the option that gives the maximum net income for a given number of hours worked.

### WEP scaling

The Winter Energy Payment (WEP) is only payed over the winter months (May to September).  The WEP Scaling setting chooses whether to show net income over the winter months (where there is full payment), the summer months (where there is none), or to show the average over the whole year (the default).

### Running the model

Click the green "Calculate" button to run the model.  This may take a few seconds.  Once the model has run the plots in the "EMTR" and "Income Components" tabs will be updated.

## Outputs

### EMTR tab

This tab shows four plots:

**Net Income**:  the sum of all income components, including transfers, minus tax.

**Effective marginal tax rate (EMTR)**:  This is the percentage of each additional dollar earned that is lost to tax and reduced transfers. 

**Replacement rate**:  This is the percentage of each dollar of lost income that is replaced by transfers.  

**Participation tax rate**:  Fraction of additional gross earnings lost to either higher taxes or lower benefits when a jobless person takes up employment

### Income components tab

This tab shows the components of income for each policy setting for a range of hours worked.  

### Downloading the data

The data contained in the output plots can be downloaded in CSV format with the "Download output.csv" button at the bottom of the control sidebar.
