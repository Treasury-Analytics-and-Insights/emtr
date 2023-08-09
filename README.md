# Income Explorer prototype

This is a prototype tool that looks at the the components of income for specified families and how their effective marginal tax rate (EMTR) changes as they work more hours, take into account New Zealand's tax and transfer system and modifications thereof.

This is based on an earlier R shiny implementation, but migrated to python to allow for serverless deployment with pyscript.

The latest version is published on github pages here: https://treasury-analytics-and-insights.github.io/emtr/


# Running the unit tests

There are several tests in the `test/` folder.  These confirm that all of the
binaries/scripts are working.  To run all of these:

```
PS C:\Users\DavisC\sandpit\emtr> python -m unittest discover -s test -v
test_emtr (test_emtr.TestEmtr.test_emtr)
1.      Single parent, children aged 0, 1, 10, AS area 1, renting ... ok

----------------------------------------------------------------------
Ran 1 test in 0.057s
```
