import sys
import unittest

import pandas as pd
import yaml

sys.path.append('..')
from emtr import *

PARAMETERS_FILE = 'test/input/TY2022.yaml'

REQUIRED_OUTPUTS = [
  'gross_wage1_annual', 'gross_benefit1', 'gross_benefit2',
  'net_benefit1_and_LAP', 'net_benefit2', 'net_wage1', 'net_wage2',
  'gross_benefit1_and_LAP', 'gross_wage1', 'gross_wage2', 'wage1_tax',
  'wage2_tax', 'wage1_ACC_levy', 'wage2_ACC_levy', 'IETC_abated1',
  'IETC_abated2', 'FTC_abated', 'MFTC', 'IWTC_abated',
  'AS_Amount', 'WinterEnergy', 'BestStart_Total', 'Net_Income', 'hours1',
  'EMTR' ,'Equivalised_Income', 'AHC_Equivalised_Income', 'BHC_Depth',
  'AHC_Depth', "BHC_Unequiv_Poverty_Line", "AHC_Unequiv_Poverty_Line", "Eq_Factor",
  'AHC_Net_Income']

class EMTRTest(unittest.TestCase):
    def compare_with_ref_file(self, output, ref_file):
        """Test that output matches reference file"""
        # load reference csv file into pandas dataframe
        ref = pd.read_csv(ref_file)
        # check that all required outputs are present and equal to the reference
        for output_name in REQUIRED_OUTPUTS:
            self.assertTrue(output_name in output)
            # compare the column and check that all values are equal - display the first 10 that are not
            # preferably using unittest capabilities      
            if not np.allclose(output[output_name], ref[output_name]):
                print('Output does not match reference')
                print('First 10 differences:')
                print(output[output_name][output[output_name] != ref[output_name]].head(10))
                self.assertTrue(False)
            


class TestEmtr(EMTRTest):
    def test_emtr(self):
        """1.	Single parent, children aged 0, 1, 10, AS area 1, renting"""
        with open(PARAMETERS_FILE, 'r', encoding='utf-8') as f:
            parameters = yaml.safe_load(f)
        output = emtr(
            parameters, partnered = False, wage1_hourly = 18.50,
            children_ages = [0, 1, 10], gross_wage2 = 0, hours2 = 0,
            as_accommodation_costs = 600, as_accommodation_rent = True, as_area = 1)
        output.to_csv('test/output/emtr_output_1.csv', index=False)
        self.compare_with_ref_file(output, 'test/ref/emtr_output_1.csv')
        


if __name__ == '__main__':
    unittest.main()

