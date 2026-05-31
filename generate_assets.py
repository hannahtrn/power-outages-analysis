"""Generate all Plotly HTML assets for the GitHub Pages website."""
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px

# ── Load & clean ──────────────────────────────────────────────────────────────
outages = pd.read_excel(
    Path('outage.xlsx.xls'),
    skiprows=5,
    index_col=0,
)
outages = outages.iloc[1:].reset_index(drop=True)

outages['OUTAGE.START'] = pd.to_datetime(
    outages['OUTAGE.START.DATE'].astype(str) + ' ' + outages['OUTAGE.START.TIME'].astype(str),
    errors='coerce'
)
outages['OUTAGE.RESTORATION'] = pd.to_datetime(
    outages['OUTAGE.RESTORATION.DATE'].astype(str) + ' ' + outages['OUTAGE.RESTORATION.TIME'].astype(str),
    errors='coerce'
)
outages = outages.drop(columns=[
    'OUTAGE.START.DATE', 'OUTAGE.START.TIME',
    'OUTAGE.RESTORATION.DATE', 'OUTAGE.RESTORATION.TIME',
])

num_cols = [
    'ANOMALY.LEVEL', 'OUTAGE.DURATION', 'DEMAND.LOSS.MW',
    'RES.PRICE', 'COM.PRICE', 'IND.PRICE', 'TOTAL.PRICE',
    'RES.SALES', 'COM.SALES', 'IND.SALES', 'TOTAL.SALES',
    'RES.PERCEN', 'COM.PERCEN', 'IND.PERCEN',
    'RES.CUST.PCT', 'COM.CUST.PCT', 'IND.CUST.PCT',
    'PC.REALGSP.STATE', 'PC.REALGSP.USA', 'PC.REALGSP.REL', 'PC.REALGSP.CHANGE',
    'UTIL.REALGSP', 'TOTAL.REALGSP', 'UTIL.CONTRI', 'PI.UTIL.OFUSA',
    'POPPCT_URBAN', 'POPPCT_UC',
    'POPDEN_URBAN', 'POPDEN_UC', 'POPDEN_RURAL',
    'AREAPCT_URBAN', 'AREAPCT_UC',
    'PCT_LAND', 'PCT_WATER_TOT', 'PCT_WATER_INLAND',
]
outages[num_cols] = outages[num_cols].apply(pd.to_numeric, errors='coerce')
outages['ERA'] = outages['YEAR'].apply(lambda y: 'Post-2010' if y > 2010 else 'Pre-2011')
outages['CUST_MISSING'] = outages['CUSTOMERS.AFFECTED'].isna()

for col in ['TOTAL.SALES', 'TOTAL.PRICE', 'RES.PRICE', 'COM.PRICE', 'IND.PRICE',
            'TOTAL.CUSTOMERS', 'POPULATION', 'POPPCT_URBAN', 'PC.REALGSP.STATE',
            'UTIL.CONTRI', 'YEAR', 'MONTH']:
    outages[col] = pd.to_numeric(outages[col], errors='coerce')

assets = Path('assets')
assets.mkdir(exist_ok=True)


def save(fig, name):
    fig.write_html(assets / name, include_plotlyjs='cdn', full_html=True)
    print(f'Saved {name}')


# ── Univariate: cause category ────────────────────────────────────────────────
cause_counts = outages['CAUSE.CATEGORY'].value_counts().reset_index()
cause_counts.columns = ['Cause', 'Count']
fig = px.bar(
    cause_counts, x='Cause', y='Count',
    title='Number of Outages by Cause Category',
    labels={'Cause': 'Cause Category', 'Count': 'Number of Outages'},
)
save(fig, 'univariate_cause.html')

# ── Univariate: customers affected ───────────────────────────────────────────
cust_cap = outages['CUSTOMERS.AFFECTED'].quantile(0.99)
fig = px.histogram(
    outages[outages['CUSTOMERS.AFFECTED'] <= cust_cap],
    x='CUSTOMERS.AFFECTED', nbins=50,
    title='Distribution of Customers Affected per Outage (clipped at 99th pct)',
    labels={'CUSTOMERS.AFFECTED': 'Customers Affected'},
)
save(fig, 'univariate_customers.html')

# ── Bivariate: mean customers affected by year ────────────────────────────────
mean_cust_by_year = (
    outages.groupby('YEAR')['CUSTOMERS.AFFECTED']
    .mean().reset_index()
    .rename(columns={'CUSTOMERS.AFFECTED': 'Mean Customers Affected'})
)
fig = px.line(
    mean_cust_by_year, x='YEAR', y='Mean Customers Affected', markers=True,
    title='Mean Customers Affected per Outage by Year',
    labels={'YEAR': 'Year', 'Mean Customers Affected': 'Mean Customers Affected'},
)
save(fig, 'bivariate_mean_by_year.html')

# ── Bivariate: ERA box plot ───────────────────────────────────────────────────
fig = px.box(
    outages[outages['CUSTOMERS.AFFECTED'] <= cust_cap],
    x='ERA', y='CUSTOMERS.AFFECTED', color='ERA',
    category_orders={'ERA': ['Pre-2011', 'Post-2010']},
    title='Customers Affected: Pre-2011 vs. Post-2010',
    labels={'ERA': 'Era', 'CUSTOMERS.AFFECTED': 'Customers Affected'},
)
save(fig, 'bivariate_era_box.html')

# ── Missingness Test 1: null distribution ────────────────────────────────────
def tvd(a, b):
    cats = set(a.index) | set(b.index)
    a = a.reindex(cats, fill_value=0)
    b = b.reindex(cats, fill_value=0)
    return (a / a.sum() - b / b.sum()).abs().sum() / 2

missing_cause = outages.loc[outages['CUST_MISSING'], 'CAUSE.CATEGORY'].value_counts()
present_cause = outages.loc[~outages['CUST_MISSING'], 'CAUSE.CATEGORY'].value_counts()
obs_tvd_cause = tvd(missing_cause, present_cause)

np.random.seed(42)
n_perms = 1000
null_tvds_cause = []
for _ in range(n_perms):
    shuffled = outages['CUST_MISSING'].sample(frac=1, replace=False).values
    m = outages.loc[shuffled, 'CAUSE.CATEGORY'].value_counts()
    p = outages.loc[~shuffled, 'CAUSE.CATEGORY'].value_counts()
    null_tvds_cause.append(tvd(m, p))

fig = px.histogram(
    x=null_tvds_cause, nbins=40,
    title='Test 1: Null Distribution of TVD (CUSTOMERS.AFFECTED missingness vs. CAUSE.CATEGORY)',
    labels={'x': 'TVD'},
)
fig.add_vline(x=obs_tvd_cause, line_color='red',
              annotation_text=f'Observed TVD = {obs_tvd_cause:.3f}',
              annotation_position='top right')
save(fig, 'missingness_test1_null.html')

# ── Missingness Test 2: null distribution ────────────────────────────────────
obs_diff_ind = abs(
    outages.loc[outages['CUST_MISSING'], 'IND.PERCEN'].mean() -
    outages.loc[~outages['CUST_MISSING'], 'IND.PERCEN'].mean()
)

null_diffs_ind = []
for _ in range(n_perms):
    shuffled = outages['CUST_MISSING'].sample(frac=1, replace=False).values
    d = abs(
        outages.loc[shuffled, 'IND.PERCEN'].mean() -
        outages.loc[~shuffled, 'IND.PERCEN'].mean()
    )
    null_diffs_ind.append(d)

fig = px.histogram(
    x=null_diffs_ind, nbins=40,
    title='Test 2: Null Distribution of |Diff in Mean IND.PERCEN| (CUSTOMERS.AFFECTED missingness vs. IND.PERCEN)',
    labels={'x': '|Difference in Mean IND.PERCEN|'},
)
fig.add_vline(x=obs_diff_ind, line_color='red',
              annotation_text=f'Observed |diff| = {obs_diff_ind:.3f}',
              annotation_position='top right')
save(fig, 'missingness_test2_null.html')

# ── Hypothesis test: null distribution ───────────────────────────────────────
post = outages.loc[outages['ERA'] == 'Post-2010', 'CUSTOMERS.AFFECTED'].dropna()
pre  = outages.loc[outages['ERA'] == 'Pre-2011',  'CUSTOMERS.AFFECTED'].dropna()
obs_diff = post.mean() - pre.mean()

np.random.seed(42)
combined = outages['CUSTOMERS.AFFECTED'].dropna()
combined_era = outages.loc[outages['CUSTOMERS.AFFECTED'].notna(), 'ERA']
n_post = (combined_era == 'Post-2010').sum()

null_diffs = []
for _ in range(10000):
    shuffled = combined.sample(frac=1, replace=False).values
    null_diffs.append(shuffled[:n_post].mean() - shuffled[n_post:].mean())

fig = px.histogram(
    x=null_diffs, nbins=50,
    title='Permutation Test: Null Distribution of Difference in Mean Customers Affected (Post-2010 minus Pre-2011)',
    labels={'x': 'Difference in Mean Customers Affected'},
)
fig.add_vline(x=obs_diff, line_color='red',
              annotation_text=f'Observed diff = {obs_diff:,.0f}',
              annotation_position='top right')
save(fig, 'hypothesis_test_null.html')

# ── Final model + fairness ────────────────────────────────────────────────────
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

target = 'TOTAL.SALES'
final_features = ['CLIMATE.REGION', 'CLIMATE.CATEGORY', 'TOTAL.PRICE',
                  'TOTAL.CUSTOMERS', 'POPULATION', 'POPPCT_URBAN',
                  'PC.REALGSP.STATE', 'UTIL.CONTRI']

df_final = outages[final_features + [target]].dropna(subset=[target])
X_f = df_final[final_features]
y_f = df_final[target]

X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(
    X_f, y_f, test_size=0.2, random_state=42
)

cat_f = ['CLIMATE.REGION', 'CLIMATE.CATEGORY']
num_f = ['TOTAL.PRICE', 'TOTAL.CUSTOMERS', 'POPULATION',
         'POPPCT_URBAN', 'PC.REALGSP.STATE', 'UTIL.CONTRI']

pre_f = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), cat_f),
    ('num', SimpleImputer(strategy='median'), num_f),
])

best_model = Pipeline([
    ('preprocessor', pre_f),
    ('regressor', RandomForestRegressor(
        n_estimators=300, max_depth=20, min_samples_leaf=1,
        random_state=42, n_jobs=-1
    )),
])
best_model.fit(X_train_f, y_train_f)

# Residual plot
preds_f = best_model.predict(X_test_f)
fig = px.scatter(
    x=preds_f,
    y=y_test_f.values - preds_f,
    labels={'x': 'Predicted TOTAL.SALES (MWh)', 'y': 'Residual (actual − predicted)'},
    title='Final Model: Residuals vs. Predicted Values (Test Set)',
    opacity=0.5,
)
fig.add_hline(y=0, line_dash='dash', line_color='red')
save(fig, 'final_model_residuals.html')

# Fairness permutation test
train_median = y_train_f.median()
test_df_fair = X_test_f.copy()
test_df_fair['actual'] = y_test_f.values
test_df_fair['pred']   = preds_f
test_df_fair['high_consumption'] = y_test_f.values > train_median

hi_mask = test_df_fair['high_consumption']
lo_mask = ~test_df_fair['high_consumption']

def group_rmse(df, mask):
    g = df[mask]
    return mean_squared_error(g['actual'], g['pred']) ** 0.5

rmse_hi  = group_rmse(test_df_fair, hi_mask)
rmse_lo  = group_rmse(test_df_fair, lo_mask)
obs_diff_fair = rmse_hi - rmse_lo

np.random.seed(42)
null_diffs_fair = []
labels = test_df_fair['high_consumption'].values.copy()
for _ in range(1000):
    shuffled = np.random.permutation(labels)
    r_hi = mean_squared_error(test_df_fair['actual'][ shuffled], test_df_fair['pred'][ shuffled]) ** 0.5
    r_lo = mean_squared_error(test_df_fair['actual'][~shuffled], test_df_fair['pred'][~shuffled]) ** 0.5
    null_diffs_fair.append(r_hi - r_lo)

fig = px.histogram(
    x=null_diffs_fair, nbins=40,
    title='Fairness Permutation Test: Null Distribution of RMSE Difference (High − Low Consumption)',
    labels={'x': 'RMSE Difference (MWh)'},
)
fig.add_vline(x=obs_diff_fair, line_color='red',
              annotation_text=f'Observed diff = {obs_diff_fair:,.0f} MWh',
              annotation_position='top left')
save(fig, 'fairness_permutation.html')

print('\nAll assets generated.')
