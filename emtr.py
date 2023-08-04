import numpy as np
import pandas as pd

from taxabate import TaxOrAbateScale

# function determining the number of weeks in a year taking leap years into account
def wks_in_year(year):
    if year % 4 == 0:
        return 366 / 7
    else:
        return 365 / 7


def emtr(
    parameters, partnered=False, wage1_hourly=16.50, children_ages=None, gross_wage2=0, hours2=0, 
    as_accommodation_costs=0, as_accommodation_rent=True, as_area=1, 
    max_wage=1900, steps_per_dollar=1, weeks_in_year=None, 
    mftc_wep_scaling=None, pov_thresholds=0.5, bhc_median=43000, ahc_median=33100):
  
    # Work out length of the year
    model_year = parameters['modelyear']
    
    if weeks_in_year is None:
        weeks_in_year = wks_in_year(model_year)
    if mftc_wep_scaling is None:
        mftc_wep_scaling = 1 / weeks_in_year
    else:
        mftc_wep_scaling = mftc_wep_scaling.value / weeks_in_year
  
    # Pull AS MaxRates together
    as_max_rate_mortgage = np.array([
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area1'],
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area2'],
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area3'],
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area4'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area1'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area2'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area3'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area4'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area1'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area2'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area3'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area4']
        ]).reshape(3, 4)
    
    as_max_rate_rent = np.array([
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area1'],
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area2'],
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area3'],
        parameters['Accommodation_MaxRate_CoupleDeps_Single2_Deps_Area4'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area1'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area2'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area3'],
        parameters['Accommodation_MaxRate_CoupleNoDeps_Single1Dep_Area4'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area1'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area2'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area3'],
        parameters['Accommodation_MaxRate_SingleNoDeps_Area4']
        ]).reshape(3, 4)
    
    # Count and categorise children
    n_kids = len(children_ages)
    bs_abating_kids = np.sum(np.array(children_ages) == 1) * (model_year >= 2020) + \
                      np.sum(np.array(children_ages) == 2) * (model_year >= 2021)
    bs_nonabating_kids = np.sum(np.array(children_ages) == 0) * (model_year >= 2019)
    
    # Convert scales to weekly    
    tax_base_scale_weekly = TaxOrAbateScale(**parameters['Tax_BaseScale']).to_weekly(weeks_in_year)
    benefits_sps_abatement_scale_weekly = TaxOrAbateScale(
       **parameters['Benefits_SPS_AbatementScale']).to_weekly(52.2)
    benefits_jss_abatement_scale_weekly = TaxOrAbateScale(
       **parameters['Benefits_JSS_AbatementScale']).to_weekly(52.2)
    benefits_jss_couple_abatement_scale_weekly = TaxOrAbateScale(
       **parameters['Benefits_JSS_CoupleAbatementScale']).to_weekly(52.2)
    family_assistance_abatement_scale_weekly = TaxOrAbateScale(
       **parameters['FamilyAssistance_Abatement_AbatementScale']).to_weekly(365/7)
    ietc_abatement_scale_weekly = TaxOrAbateScale(
        **parameters['IETC_AbatementScale']).to_weekly(weeks_in_year)
    family_assistance_beststart_abatement_scale_weekly = TaxOrAbateScale(
        **parameters['FamilyAssistance_BestStart_Abatement_AbatementScale']).to_weekly(365/7)
    
    # Convert rates to weekly
    acc_max_weekly = parameters['ACC_MaxLeviableIncome'] / weeks_in_year
    ftc_eldest = parameters['FamilyAssistance_FTC_Rates_FirstChild'] / (365/7)
    ftc_subsequent = parameters['FamilyAssistance_FTC_Rates_SubsequentChild'] / (365/7)
    iwtc_first3 = parameters['FamilyAssistance_IWTC_Rates_UpTo3Children'] / 52
    iwtc_subsequent = parameters['FamilyAssistance_IWTC_Rates_SubsequentChildren'] / 52
    ietc_rate = parameters['IETC_PerYear'] / weeks_in_year
    ietc_minimum_income = parameters['IETC_MinimalIncome'] / weeks_in_year
    bs_rate0 = parameters['FamilyAssistance_BestStart_Rates_Age0'] / (365/7)
    bs_rate1or2 = parameters['FamilyAssistance_BestStart_Rates_Age1or2'] / (365/7)
    we_couple_or_deps_amount = parameters['Benefits_WinterEnergy_Rates_CoupleOrDeps'] * mftc_wep_scaling
    we_single_amount = parameters['Benefits_WinterEnergy_Rates_Single'] * mftc_wep_scaling
    mftc_amount = parameters['FamilyAssistance_MFTC_Rates_MinimumIncome'] / 52
    
    # Calculate inverse thresholds for the tax system (weekly)
    nit = [0]
    for band in range(1, len(tax_base_scale_weekly.thresholds)):
        nit.append(nit[-1] + (tax_base_scale_weekly.thresholds[band] - tax_base_scale_weekly.thresholds[band - 1]) *
                   (1 - tax_base_scale_weekly.rates[band - 1]))
    nit = np.array(nit)

    # Assign benefit rates and abatement schedules
    if partnered:
      # Couple family
      if n_kids == 0:
        # No kids
        benefit1_net_0hrs = parameters['Benefits_JSS_Rate_Couple']
        benefit2_net_0hrs = parameters['Benefits_JSS_Rate_Couple']
        benefit_abatement_scale = benefits_jss_couple_abatement_scale_weekly
      else:
        # At least one kid
        benefit1_net_0hrs = parameters['Benefits_JSS_Rate_CoupleParent']
        benefit2_net_0hrs = parameters['Benefits_JSS_Rate_CoupleParent']
        benefit_abatement_scale = benefits_jss_couple_abatement_scale_weekly
      
    else:
        # Single family
        benefit2_net_0hrs = 0
        if n_kids == 0:
            # No kids
            benefit1_net_0hrs = parameters['Benefits_JSS_Rate_Single']
            benefit_abatement_scale = benefits_jss_abatement_scale_weekly
        else:
            # At least one kid
            if min(children_ages) < parameters['Benefits_Entitlement_Age_SPS_ChildLowerBound']:
                benefit1_net_0hrs = parameters['Benefits_SPS_Rate']
                benefit_abatement_scale = benefits_sps_abatement_scale_weekly
            else:
                # Special case for sole parent whose youngest children is older than
                # Benefits_Entitlement_Age_SPS_ChildLowerBound so the rate is based on JSS,
                # But TaxOrAbateScale is based on SPS
                benefit1_net_0hrs = parameters['Benefits_JSS_Rate_SoleParent']
                benefit_abatement_scale = benefits_sps_abatement_scale_weekly
    
    # Assign AS abatement point, entry threshold, and maximum
    if n_kids > 0 and not partnered:
        as_abate_point = np.ceil(
           weeks_in_year * benefits_jss_abatement_scale_weekly.abatement_vanishing_point(
               parameters['Benefits_JSS_Rate_SoleParent'])) / weeks_in_year
    else:
        as_abate_point = np.ceil(
           weeks_in_year * benefit_abatement_scale.abatement_vanishing_point(benefit1_net_0hrs)) / weeks_in_year
    
    as_entry_threshold = (parameters['Accommodation_BaseRateThreshold_Rent'] if as_accommodation_rent else parameters['Accommodation_BaseRateThreshold_Mortgage']) * \
                        ((benefit1_net_0hrs + benefit2_net_0hrs) + (n_kids > 0) * ftc_eldest)
    
    if as_accommodation_rent:
      as_maximum = as_max_rate_rent[as_area-1, np.maximum(2 - n_kids - 1 * partnered, 0) + 1]
    else:
      as_maximum = as_max_rate_mortgage[as_area-1, np.maximum(2 - n_kids - 1 * partnered, 0) + 1]
    
    # Initiate the output table
    gross_wage1 = np.arange(0, max_wage + 1, 1 / steps_per_dollar)
    hours1 = gross_wage1 / wage1_hourly
    gross_wage1_annual = weeks_in_year * gross_wage1
    
    # Partner wage
    gross_wage2 = gross_wage2
    
    # These are zero by default
    wage2_tax = np.zeros_like(gross_wage1)
    wage2_acc_levy = np.zeros_like(gross_wage1)
    net_wage2 = np.zeros_like(gross_wage1)
    net_benefit2 = np.zeros_like(gross_wage1)
    gross_benefit2 = np.zeros_like(gross_wage1)
    
    ietc_abated1 = np.zeros_like(gross_wage1)
    ietc_abated2 = np.zeros_like(gross_wage1)

    # Abate benefit
    net_benefit1 = benefit_abatement_scale.abate(benefit1_net_0hrs, gross_wage1 + gross_wage2)
    
    if partnered:
        net_benefit2 = benefit_abatement_scale.abate(benefit2_net_0hrs, gross_wage1 + gross_wage2)
    
    # Assign IWTC
    if parameters['FamilyAssistance_IWTC_Eligibility'] == 1:
        # Use income test
        
        # Assign income test based on single/couple
        iwtc_income_threshold = parameters['FamilyAssistance_IWTC_IncomeThreshold_Couple']/52.2 if partnered else parameters['FamilyAssistance_IWTC_IncomeThreshold_Single']/52.2
        
        # Eligible if have children and wage exceeds the threshold
        iwtc_eligible = (n_kids > 0) * ((gross_wage1 + gross_wage2) >= iwtc_income_threshold)
        
        # Calculate unabated IWTC
        iwtc_unabated = iwtc_eligible * (iwtc_first3 + max(0, n_kids - 3) * iwtc_subsequent)
        
        # If IWTC eligible, zero out benefit
        iwtc_mask = iwtc_unabated > 0
        net_benefit1[iwtc_mask] = 0
        net_benefit2[iwtc_mask] = 0
    
    else:
        # Hours test and do not give to beneficiaries
        
        # Hours threshold
        full_time_working_hours = parameters['FamilyAssistance_FullTimeWorkingHours_Couple'] if partnered else parameters['FamilyAssistance_FullTimeWorkingHours_Single']
        
        iwtc_eligible = (n_kids > 0) * ((hours1 + hours2) >= full_time_working_hours)
        
        # Calculate unabated IWTC
        iwtc_unabated = iwtc_eligible * (iwtc_first3 + max(0, n_kids - 3) * iwtc_subsequent)
        
        # If receiving IWTC, zero out benefit
        iwtc_mask = iwtc_unabated > 0
        net_benefit1[iwtc_mask] = 0
        net_benefit2[iwtc_mask] = 0
    
    # Back out Gross benefit
    gross_benefit1 = tax_base_scale_weekly.gross_from_net(net_benefit1, nit)
    
    if partnered:
        gross_benefit2 = tax_base_scale_weekly.gross_from_net(net_benefit2, nit)
    
    # Add wage on to benefit and tax
    gross_benefit_and_wage1 = gross_benefit1 + gross_wage1
    net_benefit_and_wage1 = tax_base_scale_weekly.net_from_gross(gross_benefit_and_wage1)
    wage1_tax = (gross_benefit_and_wage1 - net_benefit_and_wage1) - (gross_benefit1 - net_benefit1)
    
    if partnered:
        gross_benefit_and_wage2 = gross_benefit2 + gross_wage2
        net_benefit_and_wage2 = tax_base_scale_weekly.net_from_gross(gross_benefit_and_wage2)
        wage2_tax = (gross_benefit_and_wage2 - net_benefit_and_wage2) - (gross_benefit2 - net_benefit2)
        
    # Work out ACC levy
    wage1_acc_levy = np.minimum(gross_wage1, acc_max_weekly) * parameters['ACC_LevyRate']
    
    if partnered:
        wage2_acc_levy = np.minimum(gross_wage2, acc_max_weekly) * parameters['ACC_LevyRate']
    
    # Form net wage
    net_wage1 = gross_wage1 - wage1_tax - wage1_acc_levy
    
    if partnered:
        net_wage2 = gross_wage2 - wage2_tax - wage2_acc_levy
    
    # Form unabated FTC
    ftc_unabated = (n_kids > 0) * ftc_eldest + max(n_kids - 1, 0) * ftc_subsequent
    
    # Hours test for MFTC
    # Hours threshold
    full_time_working_hours = parameters['FamilyAssistance_FullTimeWorkingHours_Couple'] if partnered else parameters['FamilyAssistance_FullTimeWorkingHours_Single']
    
    mftc_eligible = (n_kids > 0) & ((hours1 + hours2) >= full_time_working_hours) & ((net_benefit1 + net_benefit2) == 0)
    
    # Work out MFTC amount (if benefit == 0)
    mftc = mftc_eligible * np.maximum(mftc_amount - (gross_wage1 + gross_wage2 - wage1_tax - wage2_tax), 0)
    
    # Abate FTC and IWTC
    abate_amount = family_assistance_abatement_scale_weekly.apply(
       gross_wage1 + gross_wage2 + gross_benefit1 + gross_benefit2)
    
    if 'FamilyAssistance_Abatement_Order' not in parameters:
        parameters['FamilyAssistance_Abatement_Order'] = 0
    
    if parameters['FamilyAssistance_Abatement_Order'] == 0:
        # Abate FTC first then IWTC
        ftc_abated = np.maximum(0, ftc_unabated - abate_amount)
        remaining_abatement = np.maximum(0, abate_amount - ftc_unabated)
        iwtc_abated = np.maximum(0, iwtc_unabated - remaining_abatement)
    else:
        # Abate IWTC first then FTC
        iwtc_abated = np.maximum(0, iwtc_unabated - abate_amount)
        remaining_abatement = np.maximum(0, abate_amount - iwtc_unabated)
        ftc_abated = np.maximum(0, ftc_unabated - remaining_abatement)
    
    # If receiving best start they should not be able to receive IETC
    bs_universal = bs_nonabating_kids * bs_rate0
    bs_abated = family_assistance_beststart_abatement_scale_weekly.abate(
        bs_abating_kids * bs_rate1or2, 
        gross_wage1 + gross_wage2 + gross_benefit1 + gross_benefit2)
    bs_total = bs_universal + bs_abated
    
    # Work out IETC
    ietc_eligible1 = (net_benefit1 == 0) & (ftc_abated == 0) & (iwtc_abated == 0) & \
                    (mftc == 0) & (bs_total == 0) & (gross_wage1 >= ietc_minimum_income)
    
    ietc_abated1 = ietc_eligible1 * ietc_abatement_scale_weekly.abate(ietc_rate, gross_wage1)
    
    ietc_eligible2 = (net_benefit2 == 0) & (ftc_abated == 0) & (iwtc_abated == 0) & \
                    (mftc == 0) & (bs_total == 0) & (gross_wage2 >= ietc_minimum_income)
    
    ietc_abated2 = ietc_eligible2 * ietc_abatement_scale_weekly.abate(ietc_rate, gross_wage2)
    
    if parameters.get('IETC_OnlyFamiliesWithoutChildren', False) and n_kids > 0:
      ietc_abated1[n_kids > 0] = 0
      ietc_abated2[n_kids > 0] = 0
    
    # Winter Energy
    we_couple_or_deps = np.zeros_like(gross_wage1)
    we_single = np.zeros_like(gross_wage1)
    
    we_eligible = (net_benefit1 + net_benefit2) > 0
    
    we_couple_or_deps_eligible = we_eligible & (n_kids > 0 or partnered)
    we_couple_or_deps[we_couple_or_deps_eligible] = we_couple_or_deps_amount
    
    we_single_eligible = we_eligible & (not partnered) & (n_kids == 0)
    we_single[we_single_eligible] = we_single_amount
    
    winter_energy = we_couple_or_deps + we_single
    
    # Accommodation Supplement
    as_amount = np.maximum(
      np.minimum(parameters['Accommodation_PaymentPercentage'] * (as_accommodation_costs - as_entry_threshold), 
                as_maximum) -
      np.maximum(gross_wage1 + gross_wage2 - as_abate_point, 0) *
      parameters['Accommodation_AbatementRate'] * ((net_benefit1 + net_benefit2) == 0), 0
    )
    
    # Net income and EMTR
    net_income = net_benefit1 + net_wage1 + net_benefit2 + net_wage2 + \
                ietc_abated1 + ietc_abated2 + ftc_abated + iwtc_abated + mftc + \
                winter_energy + bs_total + as_amount
    
    emtr = 1 - steps_per_dollar * (np.roll(net_income, -1) - net_income)
    emtr[-1] = emtr[-2]
    
    # Replacement rate
    replacement_rate = net_income[0] / net_income
    
    # Participation Tax Rate
    participation_tax_rate = 1 - (net_income - net_income[0]) / (gross_wage1 + gross_wage2)
    
    # As in TAWA proc the disposable income is calculated as: 
    # P_Income_Total + P_FamilyAssistance_Total + P_TaxCredit_IETC - P_Income_TaxPayable - P_ACC_LevyPayable
    # Same definition as "Net_Income", so use "Net_Income" as disposable income.
    
    # Number of children under 14
    lt_14 = np.sum(np.array(children_ages) < 14)
    
    # Number of children over 14
    gte_14 = np.sum(np.array(children_ages) >= 14) + (1 if not partnered else 2)
    
    # Modified OECD
    moecd_eq_factor = 1 + 0.5 * (gte_14 - 1) + 0.3 * (lt_14)
    
    # Equivalised Income
    equivalised_income = net_income / moecd_eq_factor
    
    # BHC Depth
    bhc_depth = (moecd_eq_factor * 
                (pov_thresholds * bhc_median - np.maximum(0, equivalised_income * weeks_in_year))) / weeks_in_year
    
    # After housing cost disposable income
    ahc_net_income = net_income - as_accommodation_costs
    
    # Equivalised Income
    ahc_equivalised_income = ahc_net_income / moecd_eq_factor
    
    # AHC Depth
    ahc_depth = (moecd_eq_factor * 
                (pov_thresholds * ahc_median - np.maximum(0, ahc_equivalised_income * weeks_in_year))) / weeks_in_year
    
    # Unequivalised median
    bhc_unequiv_poverty_line = pov_thresholds * moecd_eq_factor * bhc_median
    ahc_unequiv_poverty_line = pov_thresholds * moecd_eq_factor * ahc_median
    eq_factor = moecd_eq_factor
    
    return pd.DataFrame(
        {'gross_wage1': gross_wage1, 'hours1': hours1, 'gross_wage1_annual': gross_wage1_annual,
        'gross_wage2': gross_wage2, 'wage2_tax': wage2_tax, 'wage2_acc_levy': wage2_acc_levy,
        'net_wage2': net_wage2, 'net_benefit2': net_benefit2, 'gross_benefit2': gross_benefit2,
        'ietc_abated1': ietc_abated1, 'ietc_abated2': ietc_abated2, 'net_benefit1': net_benefit1,
        'gross_benefit1': gross_benefit1, 'wage1_tax': wage1_tax, 'wage1_acc_levy': wage1_acc_levy,
        'net_wage1': net_wage1, 'ftc_unabated': ftc_unabated, 'mftc': mftc,
        'abate_amount': abate_amount, 'winter_energy': winter_energy, 'as_amount': as_amount,
        'net_income': net_income, 'emtr': emtr, 'replacement_rate': replacement_rate,
        'participation_tax_rate': participation_tax_rate, 'bhc_depth': bhc_depth,
        'ahc_net_income': ahc_net_income, 'ahc_depth': ahc_depth, 'eq_factor': eq_factor,
        'bhc_unequiv_poverty_line': bhc_unequiv_poverty_line, 'ahc_unequiv_poverty_line': ahc_unequiv_poverty_line,
        'ftc_abated': ftc_abated, 'iwtc_abated': iwtc_abated, 'bs_total': bs_total})
