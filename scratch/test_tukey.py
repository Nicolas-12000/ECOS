import numpy as np
from scipy.stats import tukey_hsd

# Generate sample data
group1 = np.random.normal(10, 2, 50)
group2 = np.random.normal(12, 2, 50)
group3 = np.random.normal(15, 2, 50)

res = tukey_hsd(group1, group2, group3)
print("Tukey HSD Results:")
print("Statistic matrix:")
print(res.statistic)
print("p-value matrix:")
print(res.pvalue)

ci = res.confidence_interval(confidence_level=0.95)
print("CI low:")
print(ci.low)
print("CI high:")
print(ci.high)
