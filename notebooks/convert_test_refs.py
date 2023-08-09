import pandas as pd

r_path = '../../IncomeExplorer_devops/IncomeExplorer/tests/testthat/ref/emtr_output_6.csv'
new_path = '../test/ref/emtr_output_6.csv'


REQUIRED_OUTPUTS = [
    'gross_wage1', 'hours1', 'gross_wage1_annual', 'gross_wage2', 'wage2_tax', 
    'wage2_acc_levy', 'net_wage2', 'net_benefit2', 'gross_benefit2', 'ietc_abated1',
    'ietc_abated2', 'net_benefit1', 'gross_benefit1', 'wage1_tax', 'wage1_acc_levy',
    'net_wage1', 'ftc_unabated', 'mftc', 'abate_amount', 'winter_energy', 'as_amount',
    'net_income', 'emtr', 'replacement_rate', 
    'participation_tax_rate', 'ftc_abated', 'iwtc_abated', 'bs_total']


ref_data = pd.read_csv(r_path)
ref_data.columns = [c.lower() for c in ref_data.columns]
ref_data.rename(columns = {'abateamount': 'abate_amount', 'beststart_total': 'bs_total', 'winterenergy': 'winter_energy'}, inplace=True)
extra_cols = set(ref_data.columns) - set(REQUIRED_OUTPUTS)
ref_data.drop(columns=extra_cols, inplace=True)
assert(set(ref_data.columns) == set(REQUIRED_OUTPUTS))
ref_data.to_csv(new_path, index=False)
