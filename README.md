# Income Explorer prototype

This is a prototype tool that looks at the the components of income for specified families and how their effective marginal tax rate (EMTR) changes as they work more hours, taking into account New Zealand's tax and transfer system and modifications thereof.

This is based on an earlier R-shiny implementation, but migrated to Python to allow for easier user access with pyscript (http://pyscript.net).

The latest version is published on github pages here: https://treasury-analytics-and-insights.github.io/emtr/


# Running the unit tests

There are several tests in the `test/` folder.  These confirm that all of the
binaries/scripts are working.  To run all of these:

```
PS C:\Users\DavisC\sandpit\emtr> python -m unittest discover -s test -v
test_emtr1 (test_emtr.TestEmtr.test_emtr1)
Single parent, children aged 0, 1, 10, AS area 1, renting ... ok
test_emtr2 (test_emtr.TestEmtr.test_emtr2)
Couple parent, children aged 2, 15, partner not working, AS area 2, mortgage ... ok
test_emtr3 (test_emtr.TestEmtr.test_emtr3)
Couple parent, child aged 9, partner working 10 hours, AS area 4, mortgage ... ok
test_emtr4 (test_emtr.TestEmtr.test_emtr4)
Couple, both working, partner working 20 hours, AS area 4, mortgage ... ok
test_emtr5 (test_emtr.TestEmtr.test_emtr5)
Couple, one working, AS area 1, mortgage ... ok
test_emtr6 (test_emtr.TestEmtr.test_emtr6)
Single, AS area 2, renting ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.336s

OK
```
