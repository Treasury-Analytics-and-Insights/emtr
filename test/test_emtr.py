import sys
import unittest

import pandas as pd
import yaml

sys.path.append('..')
from emtr import *

PARAMETERS_FILE = 'test/input/TY2022.yaml'

REQUIRED_OUTPUTS = [
    'gross_wage1', 'hours1', 'gross_wage1_annual', 'gross_wage2', 'wage2_tax', 
    'wage2_acc_levy', 'net_wage2', 'net_benefit2', 'gross_benefit2', 'ietc_abated1',
    'ietc_abated2', 'net_benefit1', 'gross_benefit1', 'wage1_tax', 'wage1_acc_levy',
    'net_wage1', 'ftc_unabated', 'mftc', 'abate_amount', 'winter_energy', 'as_amount',
    'net_income', 'emtr', 'replacement_rate', 
    'participation_tax_rate', 'ftc_abated', 'iwtc_abated', 'bs_total']


class EMTRTest(unittest.TestCase):
    def compare_with_ref_file(self, output, ref_file):
        """Test that output matches reference file"""
        # load reference csv file into pandas dataframe
        ref = pd.read_csv(ref_file)
        # check that all required outputs are present and equal to the reference
        for output_name in REQUIRED_OUTPUTS:
            self.assertTrue(output_name in output)
            if not np.allclose(output[output_name], ref[output_name], equal_nan=True):
                print('Output does not match reference')
                print('First 10 differences:')
                close_index = np.isclose(output[output_name], ref[output_name], equal_nan=True)
                print('test output: ')
                print(output[output_name][~close_index].head(10))
                print('reference: ')
                print(ref[output_name][~close_index].head(10))
                self.assertTrue(False)
            


class TestEmtr(EMTRTest):
    def test_emtr1(self):
        """Single parent, children aged 0, 1, 10, AS area 1, renting"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = False, wage1_hourly = 18.50,
            children_ages = [0, 1, 10], wage2_hourly = 0, hours2 = 0,
            as_accommodation_costs = 600, as_accommodation_rent = True, as_area = 1)
        output.to_csv('test/output/emtr_output_1.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_1.csv')
        
    def test_emtr2(self):
        """Couple parent, children aged 2, 15, partner not working, AS area 2, mortgage"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = True, wage1_hourly = 18.50,
            children_ages = [2, 15], wage2_hourly = 0, hours2 = 0,
            as_accommodation_costs = 800, as_accommodation_rent = False, as_area = 2)
        output.to_csv('test/output/emtr_output_2.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_2.csv')

    def test_emtr3(self):
        """Couple parent, child aged 9, partner working 10 hours, AS area 4, mortgage"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = True, wage1_hourly = 18.50,
            children_ages = [9], wage2_hourly = 18.5, hours2=10,
            as_accommodation_costs = 600, as_accommodation_rent = True, 
            as_area = 3)
        output.to_csv('test/output/emtr_output_3.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_3.csv')

    def test_emtr4(self):
        """Couple, both working, partner working 20 hours, AS area 4, mortgage"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = True, wage1_hourly = 18.50,
            children_ages = [], wage2_hourly = 18.50, hours2=20,
            as_accommodation_costs = 500, as_accommodation_rent = False, 
            as_area = 4)
        output.to_csv('test/output/emtr_output_4.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_4.csv')

    def test_emtr5(self):
        """Couple, one working, AS area 1, mortgage"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = True, wage1_hourly = 18.50,
            children_ages = [], wage2_hourly=0, hours2=0,
            as_accommodation_costs = 800, as_accommodation_rent = False, 
            as_area = 1)
        output.to_csv('test/output/emtr_output_5.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_5.csv')

    def test_emtr6(self):
        """Single, AS area 2, renting"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = False, wage1_hourly = 18.50,
            children_ages = [], wage2_hourly=0, hours2=0,
            as_accommodation_costs = 0, as_accommodation_rent = True, 
            as_area = 2)
        output.to_csv('test/output/emtr_output_6.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_6.csv')



if __name__ == '__main__':
    unittest.main()

