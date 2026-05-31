# Lights Out: Analyzing the Severity and Predictability of U.S. Power Outages

**Authors:** Hannah Tran, Romy Luna Caal

---

## Introduction

This project analyzes the **Major Power Outages** dataset, which records 1,534 major power outage events across the continental United States from January 2000 to July 2016. Each row represents one outage event, and the dataset contains 56 columns covering outage timing, cause, impact, and state-level economic and demographic characteristics.

**Central question:** Have power outages become more severe over time? Specifically, do outages after 2010 affect more customers on average than outages before 2011?

Understanding whether outage severity is worsening has real implications for infrastructure investment, emergency preparedness, and grid reliability policy. As climate change intensifies weather events and aging infrastructure struggles to keep pace with demand, knowing whether the problem is getting worse, and by how much, can help direct resources where they matter most.

**Dataset:** 1,534 rows (outage events)

### Relevant Columns

| Column | Description |
|---|---|
| `YEAR` | Year the outage occurred |
| `MONTH` | Month the outage occurred |
| `U.S._STATE` | State where the outage occurred |
| `CLIMATE.REGION` | U.S. climate region (e.g., Northeast, Southeast) |
| `CAUSE.CATEGORY` | High-level cause (e.g., severe weather, intentional attack) |
| `OUTAGE.START` | Date and time the outage began (combined from date + time columns) |
| `OUTAGE.RESTORATION` | Date and time power was restored (combined from date + time columns) |
| `OUTAGE.DURATION` | Duration of the outage in minutes |
| `CUSTOMERS.AFFECTED` | Number of customers affected by the outage |
| `DEMAND.LOSS.MW` | Peak demand loss during the outage (megawatts) |

---

## Data Cleaning and Exploratory Data Analysis

### Data Cleaning

The raw Excel file had 5 header/metadata rows before the actual column names, plus a units row as the first data row; both were stripped on load. The following steps were then applied:

1. **Datetime columns combined:** `OUTAGE.START.DATE` + `OUTAGE.START.TIME` were merged into a single `OUTAGE.START` datetime column, and similarly for `OUTAGE.RESTORATION`. The four raw date/time columns were then dropped. This makes time-based calculations (e.g., duration checks) straightforward and avoids accidental use of incomplete date strings.

2. **Numeric coercion:** Many numeric columns loaded as `object` dtype because the units row introduced string values in row 0. We applied `pd.to_numeric(..., errors='coerce')` to all numeric columns, converting non-numeric strings to `NaN`.

3. **ERA column added:** A derived `ERA` column was created to label each outage as `'Post-2010'` (year > 2010) or `'Pre-2011'` (year ≤ 2010). This binary split roughly divides the dataset in half and directly supports the hypothesis test.

After cleaning, the dataset has **1,534 rows × 55 columns**. Key columns with missing values in the relevant subset: `CUSTOMERS.AFFECTED` (443 missing, ~29%), `OUTAGE.DURATION` (58 missing), `DEMAND.LOSS.MW` (705 missing, ~46%).

### Cleaned DataFrame (first 5 rows, selected columns)

| YEAR | U.S._STATE | CAUSE.CATEGORY | OUTAGE.DURATION | CUSTOMERS.AFFECTED | OUTAGE.START | ERA |
|---|---|---|---|---|---|---|
| 2011 | Minnesota | severe weather | 3060.0 | 70000.0 | 2011-07-01 17:00:00 | Post-2010 |
| 2014 | Minnesota | intentional attack | 1.0 | NaN | 2014-05-11 18:38:00 | Post-2010 |
| 2010 | Minnesota | severe weather | 3000.0 | 70000.0 | 2010-10-26 20:00:00 | Pre-2011 |
| 2012 | Minnesota | severe weather | 2550.0 | 68200.0 | 2012-06-19 04:30:00 | Post-2010 |
| 2015 | Minnesota | severe weather | 1740.0 | 250000.0 | 2015-07-18 02:00:00 | Post-2010 |

### Univariate Analysis

<iframe src="assets/univariate_cause.html" width="800" height="450" frameborder="0"></iframe>

Severe weather is by far the most common cause of major outages, accounting for nearly half of all events. Intentional attacks form the second-largest group, a category that grew substantially after 2010, which motivates our time-based comparison.

<iframe src="assets/univariate_customers.html" width="800" height="450" frameborder="0"></iframe>

The distribution of customers affected per outage is heavily right-skewed: most outages affect tens of thousands of customers, but a small number of extreme events affect hundreds of thousands or even millions. The values shown are clipped at the 99th percentile to make the shape visible.

### Bivariate Analysis

<iframe src="assets/bivariate_mean_by_year.html" width="800" height="450" frameborder="0"></iframe>

Mean customers affected per outage fluctuates considerably year to year, with some of the highest values occurring in the early 2000s. The trend does not show a clear upward pattern toward the present; if anything, later years appear to have lower mean impact, which motivates the formal hypothesis test.

<iframe src="assets/bivariate_era_box.html" width="800" height="500" frameborder="0"></iframe>

The side-by-side box plots compare the distribution of customers affected in the Pre-2011 vs. Post-2010 eras. The pre-2011 distribution has a noticeably higher median and a longer upper tail, suggesting that earlier outages may have been more impactful on average.

### Interesting Aggregates

The pivot table below shows mean customers affected broken down by era and cause category:

| CAUSE.CATEGORY | Pre-2011 | Post-2010 |
|---|---|---|
| equipment failure | 116,042 | 45,509 |
| fuel supply emergency | 0 | 0 |
| intentional attack | 0 | 1,809 |
| islanding | 5,677 | 6,606 |
| public appeal | 9,505 | 5,544 |
| severe weather | 208,613 | 160,880 |
| system operability disruption | 281,903 | 85,921 |

For nearly every cause category, mean customers affected is *lower* in the Post-2010 era than before 2011. This is particularly striking for severe weather (208K → 161K) and system operability disruptions (282K → 86K). The table suggests that the overall pattern of fewer customers affected per outage in recent years holds across most cause types, not just one category driving the aggregate.

---

## Assessment of Missingness

### NMAR Analysis

`DEMAND.LOSS.MW` records the peak demand lost (in megawatts) during an outage. This column is likely **NMAR** because utilities are only required to report demand loss when it meets a minimum threshold under the DOE's OE-417 reporting rules. For smaller outages (even those with many customers affected), utilities may not record a demand loss figure at all. The missingness is therefore tied to the *value itself* (small demand loss → not reported), not to any other recorded column.

To make this column MAR, we would want additional data such as the utility company's internal reporting threshold or a flag from the OE-417 form indicating whether the entry was below the mandatory reporting cutoff.

### Missingness Dependency

We analyzed the missingness of **`CUSTOMERS.AFFECTED`** (missing in 443 of 1,534 rows, ~29%).

**Null Hypothesis:** The distribution of Cause Category is the same when Customers Affected is missing vs. not missing.

**Alternate Hypothesis:** The distribution of Cause Category is different when Customers Affected is missing vs. not missing.

*Test statistic:* Total Variation Distance (TVD) between the cause category distribution when `CUSTOMERS.AFFECTED` is missing vs. not missing. TVD is appropriate here because `CAUSE.CATEGORY` is a categorical column and we want to measure how different the two distributions look overall.

The observed TVD was **0.5574** with a **p-value ≈ 0.000** (1,000 permutations). We reject the null hypothesis that missingness is independent of cause category.

<iframe src="assets/missingness_test1_null.html" width="800" height="450" frameborder="0"></iframe>

The null distribution of TVD values under random shuffling is tightly clustered near 0, while the observed TVD of 0.557 falls far in the right tail, confirming that the two distributions are very different. Intentional attacks make up a much larger share of rows where `CUSTOMERS.AFFECTED` is missing (~60%) than where it is present (~20%), confirming that missingness is **MAR** on cause category. Utilities reporting intentional attacks consistently omit customer counts, likely for security or reporting reasons.

**Null Hypothesis:** The distribution of Industrial Percentage is the same when Customers Affected is missing vs. not missing.

**Alternate Hypothesis:** The distribution of Industrial Percentage is different when Customers Affected is missing vs. not missing.

*Test statistic:* Absolute difference in mean `IND.PERCEN` (industrial electricity consumption percentage) between rows where `CUSTOMERS.AFFECTED` is missing vs. not missing.

The observed \|diff\| was **0.117** with a **p-value ≈ 0.818** (1,000 permutations). We fail to reject the null hypothesis; missingness does not depend on `IND.PERCEN`.

<iframe src="assets/missingness_test2_null.html" width="800" height="450" frameborder="0"></iframe>

The observed statistic sits well within the bulk of the null distribution, providing no evidence that industrial electricity share influences whether customer counts are reported.

**Summary:** `CUSTOMERS.AFFECTED` is **MAR**: its missingness depends on `CAUSE.CATEGORY` but not on `IND.PERCEN`.

---

## Hypothesis Testing

**Null Hypothesis:** The distribution of outage severity (number of customers affected) has not changed over time. Any observed difference in mean customers affected between outages before 2011 and outages after 2010 is due to random chance.

**Alternative Hypothesis:** Outages have become more severe over time: outages after 2010 affect more customers on average than outages before 2011.

**Test Statistic:** Difference in mean customers affected (post-2010 minus pre-2011). A one-sided test statistic is appropriate because our alternative hypothesis has a specific direction (post-2010 should be *larger*).

**Significance Level:** 0.05

**Justification:** We use a permutation test because we make no distributional assumptions about `CUSTOMERS.AFFECTED` (it is heavily right-skewed). The difference in means directly measures the magnitude of the shift we care about. The 2010 cutoff splits the dataset roughly in half and aligns with well-documented increases in intentional attacks and shifting severe weather patterns recorded in this dataset.

**Results:**

| Group | Mean Customers Affected | n |
|---|---|---|
| Post-2010 | 91,531 | 566 |
| Pre-2011 | 199,437 | 525 |
| Observed difference (post − pre) | −107,906 | |

**p-value: 1.000**

<iframe src="assets/hypothesis_test_null.html" width="800" height="450" frameborder="0"></iframe>

The observed difference (−107,906 customers) falls at the extreme *left* tail of the null distribution, the opposite direction from our alternative hypothesis. The p-value of 1.000 means that under random shuffling, every simulated difference is larger (more positive) than the observed one. We **fail to reject the null hypothesis** at α = 0.05.

**Conclusion:** The data do not support the claim that outages after 2010 are more severe. In fact, the evidence points in the opposite direction: outages before 2011 had substantially higher mean customer impact. This may reflect improvements in grid resilience, changes in reporting practices, or a shift in outage composition (e.g., more intentional attacks post-2010, which tend to affect far fewer customers than severe weather). Since this is an observational study, we cannot draw causal conclusions, and confounding factors such as population growth or changes in reporting thresholds may contribute to the pattern.

---

## Framing a Prediction Problem

We predict **`TOTAL.SALES`** (MWh), the total electricity consumed in a U.S. state during the year of the outage event. This is a **regression** problem.

**Why this target?** `TOTAL.SALES` directly measures the electricity consumption of an area, capturing its energy demand profile. Understanding consumption is valuable for grid capacity planning, infrastructure investment, and identifying areas that may be vulnerable to large-scale outages due to high demand.

**What is known at the time of prediction?** Each row corresponds to an outage event, but `TOTAL.SALES` is a state-level annual figure that reflects the state's consumption for that year and is known before any particular outage occurs. The features we use (electricity prices, customer counts, population, economic output, climate region) are all state-level annual statistics available to a grid planner before an outage event.

**Columns excluded to avoid leakage:**
- `RES.SALES`, `COM.SALES`, `IND.SALES` (sub-components that directly sum to `TOTAL.SALES`)
- `RES.PERCEN`, `COM.PERCEN`, `IND.PERCEN` (percentage breakdowns of `TOTAL.SALES`)
- Outage-specific columns (`OUTAGE.DURATION`, `CUSTOMERS.AFFECTED`, `DEMAND.LOSS.MW`), which are consequences of an outage, not pre-existing state characteristics

**Evaluation metric: RMSE (Root Mean Squared Error).** `TOTAL.SALES` spans a wide range (~400,000 to ~42,000,000 MWh). RMSE is interpretable in the same units and penalizes large errors more than MAE, which matters here because underestimating consumption for a high-demand state by millions of MWh is far more consequential than a small error. R² is reported as a secondary metric.

---

## Baseline Model

The baseline model predicts `TOTAL.SALES` using two features:

| Feature | Type | Encoding |
|---|---|---|
| `CLIMATE.REGION` | Nominal | One-hot encoding (8 U.S. climate regions) |
| `TOTAL.PRICE` | Quantitative | Median imputation; passed as-is to linear regression |

**1 quantitative feature** (`TOTAL.PRICE`) and **1 nominal feature** (`CLIMATE.REGION`, one-hot encoded into 7 dummy columns). All steps are implemented in a single `sklearn Pipeline`.

**Why these features?** Climate region captures systematic demand differences (e.g., the South uses far more electricity for cooling than the Northwest). `TOTAL.PRICE` is the average electricity price in a state, a key economic driver of consumption known at the state-year level before any outage.

**Performance:**

| Split | RMSE | R² |
|---|---|---|
| Train | 5,956,419 MWh | 0.532 |
| Test | 5,894,112 MWh | 0.464 |
| Mean-only baseline | 8,057,843 MWh | |

The model explains roughly 46% of the variance in state electricity consumption on the test set, which is better than predicting the mean, but it misses major drivers like population and economic scale. This motivates the final model.

---

## Final Model

### New Features Added

| Feature | Type | Transformation | Rationale |
|---|---|---|---|
| `TOTAL.CUSTOMERS` | Quantitative | Median imputation | The number of electricity customers is the single strongest proxy for total consumption; more customers means more aggregate demand, directly tied to the data generating process |
| `POPULATION` | Quantitative | Median imputation | Population drives residential demand; two states with the same customer count but different populations may consume very differently due to urban/rural mix |
| `POPPCT_URBAN` | Quantitative | Median imputation | Urban areas have higher per-capita electricity use due to density, commercial activity, and HVAC usage; captures the urban/rural composition of state demand |
| `PC.REALGSP.STATE` | Quantitative | Median imputation | Per-capita real GDP proxies industrial and commercial activity intensity; wealthier, more industrialized states consume more electricity per customer |
| `UTIL.CONTRI` | Quantitative | Median imputation | Utility sector's share of state GDP reflects the relative size of the electricity sector; states with large utility sectors tend to have higher total consumption |
| `CLIMATE.CATEGORY` | Nominal | One-hot encoding | Warm/cold/normal year classification captures inter-annual climate variation that shifts heating and cooling demand independently of the fixed region label |

**Why `RandomForestRegressor`?** The relationship between consumption and its drivers is nonlinear (e.g., the effect of `TOTAL.CUSTOMERS` differs by `CLIMATE.REGION` since Southern customers consume more per head for cooling). A random forest captures these interactions through tree splits without requiring explicit interaction terms.

**Hyperparameter selection:** `GridSearchCV` with 5-fold cross-validation on the training set, scored by negative RMSE.

| Hyperparameter | Grid Searched | Best Value | Rationale |
|---|---|---|---|
| `n_estimators` | [100, 300] | 300 | More trees reduce variance; 300 gave better CV RMSE than 100 |
| `max_depth` | [10, 20, None] | 20 | Deep enough to capture complex interactions without fully memorizing training data |
| `min_samples_leaf` | [1, 3, 5] | 1 | With clean numeric features and a moderate dataset, single-sample leaves are stable |

**Best CV RMSE: 1,244,311 MWh**

### Performance Comparison

| Model | Test RMSE | Test R² |
|---|---|---|
| Baseline (Linear Regression, 2 features) | 5,894,112 MWh | 0.464 |
| **Final (Random Forest, 8 features)** | **1,438,933 MWh** | **0.968** |

The final model reduces test RMSE by ~76% and raises R² from 0.46 to 0.97, a dramatic improvement driven primarily by the addition of `TOTAL.CUSTOMERS`, which directly connects to the data generating process (more customers → more aggregate electricity sales).

<iframe src="assets/final_model_residuals.html" width="800" height="500" frameborder="0"></iframe>

The residual plot shows predictions clustered tightly around zero for most of the range, with larger absolute residuals at higher predicted values, consistent with the fairness analysis finding discussed next.

---

## Fairness Analysis

**Group X (High-consumption states):** states where `TOTAL.SALES` is above the training-set median (~8,926,587 MWh), including large, high-demand states such as Texas, California, and Florida.

**Group Y (Low-consumption states):** states where `TOTAL.SALES` is at or below the training-set median, i.e., smaller or lower-demand states.

**Evaluation metric:** RMSE (same as overall evaluation).

**Null Hypothesis:** The model is fair. Its RMSE for high-consumption states and low-consumption states are roughly the same; any observed difference is due to random chance.

**Alternative Hypothesis:** The model is unfair. Its RMSE for high-consumption states is *higher* than for low-consumption states (i.e., the model performs worse on the large states where prediction errors are most consequential).

**Test Statistic:** Difference in RMSE (high-consumption RMSE − low-consumption RMSE). Positive values indicate the model does worse on high-consumption states.

**Significance Level:** 0.05

**Results:**

| Group | n | RMSE |
|---|---|---|
| High-consumption states | 160 | 1,852,961 MWh |
| Low-consumption states | 143 | 738,624 MWh |
| Observed difference | | 1,114,338 MWh |

**p-value: 0.000**

<iframe src="assets/fairness_permutation.html" width="800" height="450" frameborder="0"></iframe>

The observed RMSE gap of ~1.1 million MWh lies far outside the null distribution. We **reject the null hypothesis** at α = 0.05: the model is significantly less accurate for high-consumption states than for low-consumption states.

**Why this occurs:** High-consumption states (Texas, California, Florida) have `TOTAL.SALES` values in the tens of millions of MWh. Even a small *relative* prediction error translates into a very large *absolute* RMSE. The random forest learned strong patterns for typical mid-range states, but the extreme values at the high end are harder to pin down precisely.

**Practical implication:** Grid planners using this model for capacity decisions in large, high-demand states should be aware that predictions carry roughly 2.5× more absolute uncertainty than for smaller states. Supplementing the model with state-specific historical data could reduce this disparity.
