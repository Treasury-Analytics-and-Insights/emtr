import numpy as np

class TaxOrAbateScale(object):
    def __init__(self, thresholds, rates):
        self.thresholds = np.array(thresholds)
        self.rates = np.array(rates)

    def to_weekly(self, weeks_in_year):
        return TaxOrAbateScale(self.thresholds / weeks_in_year, self.rates)
    
    def abate(self, amount, income):
        thresholds, rates = self.thresholds, self.rates
        num_bands = len(thresholds)
        for band in range(1, num_bands):
            amount = amount - np.maximum(
                0, np.minimum(thresholds[band], income) - thresholds[band - 1]) * rates[band - 1]
        amount = amount - np.maximum(0, income - thresholds[num_bands - 1]) * rates[num_bands - 1]
        return np.maximum(0, amount)
    
    def abatement_vanishing_point(self, amount):
        thresholds, rates = self.thresholds, self.rates
        num_bands = len(thresholds)
        for band in range(0, num_bands - 1):
            if rates[band] == 0:
                continue
            if thresholds[band] + amount / rates[band] > thresholds[band]:
                amount -= rates[band] * (thresholds[band] - thresholds[band])
            else:
                return thresholds[band] + amount / rates[band]
        return thresholds[band -1] + amount / rates[band -1]
    
    def apply(self, amount):
        tax = 0
        thresholds, rates = self.thresholds, self.rates
        num_bands = len(thresholds)
        for band in range(0, num_bands - 1):
            tax += (np.minimum(np.maximum(amount, thresholds[band]), 
                    thresholds[band + 1]) - thresholds[band]) * rates[band]
        return tax + np.maximum(0, amount - thresholds[num_bands - 1]) * rates[num_bands - 1]
    
    def gross_from_net(self, amount, net_thresholds):
        levels = len(net_thresholds)
        old = 0
        gross = np.zeros_like(amount)
        for level in range(1, levels):
            gross += (np.logical_and(amount < net_thresholds[level], amount >= net_thresholds[level - 1])) * \
                (self.thresholds[level - 1] + (amount - old) / (1 - self.rates[level - 1]))
            old = net_thresholds[level]
        return gross + (amount > net_thresholds[levels - 1]) * \
            (self.thresholds[levels - 1] + (amount - old) / (1 - self.rates[levels - 1]))
    
    def net_from_gross(self, amount):
        return amount - self.apply(amount)
    

