import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# =============================================================================
# SECTION 1 — ATM MASTER TABLE
# New field: tax_service_proximity — 10% of network (~5 ATMs)
# These machines behave like high-volume urban units during tax season peak
# =============================================================================

atm_data = {
    'atm_id': [f'ATM{str(i).zfill(3)}' for i in range(1, 51)],
    'location_name': [
        'Downtown Houston Main','Galleria Mall','IAH Airport Terminal A',
        'IAH Airport Terminal B','Toyota Center Arena','NRG Stadium',
        'Tunica Casino MS','Laughlin Casino NV','Biloxi Casino MS',
        'Shreveport Casino LA','Memorial Hospital','Texas Medical Center',
        'Hobby Airport','Sugar Land Town Square','The Woodlands Mall',
        'Katy Mills Mall','Baybrook Mall','First Colony Mall',
        'Midtown Houston','Montrose District','Heights Boulevard',
        'EaDo District','Greenway Plaza','Westheimer Corridor',
        'Almeda Mall','Deerbrook Mall','Willowbrook Mall',
        'Pearland Town Center','League City Center','Friendswood Market',
        'Conroe Crossroads','Huntsville Walmart','Lufkin Center',
        'Nacogdoches Square','Beaumont Mall','Orange Walmart',
        'Port Arthur Center','Lake Charles Casino LA','Galveston Strand',
        'Texas City Market','Pasadena Town Square','Deer Park Center',
        'La Marque Walmart','Angleton Market','Wharton Center',
        'El Campo Square','Victoria Mall','Bay City Market',
        'Palacios Waterfront','Port Lavaca Center'
    ],
    'city': [
        'Houston','Houston','Houston','Houston','Houston','Houston',
        'Tunica MS','Laughlin NV','Biloxi MS','Shreveport LA',
        'Houston','Houston','Houston','Sugar Land','The Woodlands',
        'Katy','Friendswood','Sugar Land','Houston','Houston',
        'Houston','Houston','Houston','Houston','Houston','Humble',
        'Houston','Pearland','League City','Friendswood',
        'Conroe','Huntsville','Lufkin','Nacogdoches','Beaumont','Orange',
        'Port Arthur','Lake Charles LA','Galveston','Texas City',
        'Pasadena','Deer Park','La Marque','Angleton','Wharton',
        'El Campo','Victoria','Bay City','Palacios','Port Lavaca'
    ],
    'location_type': [
        'Urban','Mall','Airport','Airport','Arena','Stadium',
        'Casino','Casino','Casino','Casino',
        'Hospital','Hospital','Airport','Retail','Mall',
        'Mall','Mall','Mall','Urban','Urban',
        'Urban','Urban','Office','Retail','Mall','Mall',
        'Mall','Retail','Retail','Retail',
        'Retail','Retail','Retail','Retail','Mall','Retail',
        'Retail','Casino','Tourist','Retail',
        'Retail','Retail','Retail','Retail','Retail',
        'Retail','Mall','Retail','Tourist','Retail'
    ],
    'distance_from_branch_miles': [
        2.1,4.5,18.2,18.4,3.1,5.2,
        142.0,156.0,87.0,211.0,
        6.3,7.1,12.4,22.1,31.5,
        35.2,28.7,24.3,3.8,4.1,
        5.2,3.9,6.8,5.5,18.9,22.4,
        28.1,24.6,31.2,29.8,
        45.2,71.3,112.4,128.7,88.3,98.1,
        91.4,135.0,52.3,44.1,
        16.2,18.9,38.4,52.1,68.3,
        82.4,131.2,95.6,143.2,118.7
    ],
    'cash_capacity_dollars': [
        80000,60000,100000,100000,120000,120000,
        150000,150000,120000,150000,
        60000,60000,80000,50000,60000,
        60000,60000,50000,50000,50000,
        50000,50000,60000,60000,50000,60000,
        60000,50000,50000,50000,
        40000,40000,40000,40000,50000,40000,
        40000,120000,60000,40000,
        50000,40000,40000,40000,40000,
        40000,50000,40000,40000,40000
    ],
    'cash_tolerance': [
        'Medium','Medium','Low','Low','Zero','Zero',
        'Zero','Zero','Zero','Zero',
        'Low','Low','Low','Medium','Medium',
        'Medium','Medium','Medium','Medium','Medium',
        'Medium','Medium','Medium','Medium','Medium','Medium',
        'Medium','Medium','Medium','Medium',
        'High','High','High','High','High','High',
        'High','Zero','Medium','High',
        'Medium','High','High','High','High',
        'High','High','High','High','High'
    ],
    # Tax service proximity — 5 ATMs (~10% of network)
    # These are LOW-volume retail/urban units all year
    # that transform during tax season peak
    # Real-world basis: debit card refund transition caught ops teams off guard
    'tax_service_proximity': [
        False,False,False,False,False,False,
        False,False,False,False,
        False,False,False,False,False,
        False,False,False,False,False,
        False,False,False,False,False,False,
        False,False,False,False,
        True,True,False,False,False,True,   # Conroe, Huntsville, Orange Walmart
        False,False,False,True,              # Texas City Market
        False,False,True,False,False,        # La Marque Walmart
        False,False,False,False,False
    ]
}

atm_df = pd.DataFrame(atm_data)

def classify_terminal(d):
    return 'Local' if d < 25 else ('Remote' if d < 100 else 'Over The Road')

atm_df['terminal_type'] = atm_df['distance_from_branch_miles'].apply(classify_terminal)
atm_df['emergency_multiplier'] = atm_df['terminal_type'].map({'Local':2.5,'Remote':3.0,'Over The Road':4.0})
atm_df['revenue_impact_per_hour'] = atm_df['location_type'].map({
    'Casino':850,'Airport':420,'Arena':380,'Stadium':380,
    'Hospital':290,'Mall':240,'Urban':210,'Tourist':190,'Office':160,'Retail':120
})

# =============================================================================
# SECTION 2 — FULL YEAR TIME SERIES (365 days)
# Tax service proximity machines get:
#   - 2.0x volume multiplier during Feb 15 – Mar 15
#   - Avg withdrawal bumped to $250–$450 (refund recipients pulling large amounts)
#   - Cash tolerance reclassified to Zero during peak window
# =============================================================================

dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
dow_multipliers = {0:0.82,1:0.78,2:0.85,3:0.91,4:1.15,5:1.42,6:1.28}
base_volume_map = {
    'Casino':280,'Airport':195,'Arena':85,'Stadium':75,
    'Hospital':88,'Mall':142,'Urban':118,'Tourist':95,'Office':72,'Retail':65
}
tax_weight_map = {
    'Retail':1.00,'Urban':1.00,'Mall':0.85,'Casino':0.70,
    'Tourist':0.65,'Airport':0.50,'Hospital':0.50,'Office':0.50,'Arena':0.55,'Stadium':0.55
}

def get_seasonal_multiplier(date):
    m, d = date.month, date.day
    if m == 1: return 1.05
    elif m == 2 and d < 15: return 1.15
    elif (m == 2 and d >= 15) or (m == 3 and d <= 15): return 1.50
    elif (m == 3 and d > 15) or m == 4: return 1.25
    elif m in [11,12]: return 1.18
    else: return 1.00

def is_tax_peak(date):
    return (date.month == 2 and date.day >= 15) or (date.month == 3 and date.day <= 15)

records = []
for _, atm in atm_df.iterrows():
    base_vol = base_volume_map[atm['location_type']]
    tax_weight = tax_weight_map[atm['location_type']]
    tax_proximity = atm['tax_service_proximity']
    current_cash = atm['cash_capacity_dollars'] * np.random.uniform(0.55, 0.95)

    for date in dates:
        dow = date.dayofweek
        peak = is_tax_peak(date)
        raw_seasonal = get_seasonal_multiplier(date)

        # Standard seasonal blending
        seasonal_mult = 1.0 + (raw_seasonal - 1.0) * tax_weight if raw_seasonal > 1.0 else raw_seasonal

        # Casino/Tourist weekend boost
        if atm['location_type'] in ['Casino','Tourist'] and dow in [4,5,6]:
            seasonal_mult *= 1.25

        # TAX SERVICE PROXIMITY BOOST
        # Machine doubles in volume during peak — large withdrawal amounts
        # This is the "Penn Station" effect — caught ops teams off guard
        if tax_proximity and peak:
            seasonal_mult *= 2.0
            avg_withdrawal = np.random.uniform(400, 500)  # Refund recipients hitting max withdrawal limit ($500)
            effective_tolerance = 'Zero'                   # Reclassified during peak
        else:
            avg_withdrawal = np.random.uniform(85, 165)
            effective_tolerance = atm['cash_tolerance']

        daily_txn = int(base_vol * dow_multipliers[dow] * seasonal_mult * np.random.uniform(0.82, 1.18))
        daily_cash_out = daily_txn * avg_withdrawal
        current_cash = max(0, current_cash - daily_cash_out)

        replenishment_threshold = atm['cash_capacity_dollars'] * 0.20
        if current_cash <= replenishment_threshold:
            current_cash = atm['cash_capacity_dollars'] * np.random.uniform(0.75, 1.0)

        season_label = (
            'Tax Season Peak'  if (date.month==2 and date.day>=15) or (date.month==3 and date.day<=15)
            else 'Tax Season'  if date.month in [1,4] or (date.month==2 and date.day<15) or (date.month==3 and date.day>15)
            else 'Holiday'     if date.month in [11,12]
            else 'Baseline'
        )

        records.append({
            'atm_id': atm['atm_id'],
            'transaction_date': date.strftime('%Y-%m-%d'),
            'year': date.year,
            'month': date.month,
            'month_name': date.strftime('%B'),
            'day_of_week': date.strftime('%A'),
            'day_num': dow,
            'season': season_label,
            'tax_service_proximity': tax_proximity,
            'tax_peak_active': tax_proximity and peak,
            'effective_cash_tolerance': effective_tolerance,
            'seasonal_multiplier': round(seasonal_mult, 3),
            'daily_transactions': daily_txn,
            'avg_withdrawal_amount': round(avg_withdrawal, 2),
            'daily_cash_dispensed': round(daily_cash_out, 2),
            'cash_balance_eod': round(current_cash, 2)
        })

txn_df = pd.DataFrame(records)

# =============================================================================
# SECTION 3 — 72-HOUR PREDICTIVE DEMAND MODEL
# Tax service proximity machines evaluated with peak-adjusted risk scoring
# =============================================================================

cutoff = pd.Timestamp('2024-12-29')
last_30 = txn_df[pd.to_datetime(txn_df['transaction_date']) >= cutoff - pd.Timedelta(days=30)]
dow_burn = last_30.groupby(['atm_id','day_num'])['daily_cash_dispensed'].mean().reset_index()
dow_burn.columns = ['atm_id','day_num','avg_daily_burn']
current_balance = txn_df[txn_df['transaction_date']=='2024-12-29'][['atm_id','cash_balance_eod']]

# Also generate a TAX PEAK forecast (Feb 15 scenario) for comparison
tax_peak_date = pd.Timestamp('2024-02-15')
last_30_tax = txn_df[
    (pd.to_datetime(txn_df['transaction_date']) >= tax_peak_date - pd.Timedelta(days=30)) &
    (pd.to_datetime(txn_df['transaction_date']) <= tax_peak_date)
]
dow_burn_tax = last_30_tax.groupby(['atm_id','day_num'])['daily_cash_dispensed'].mean().reset_index()
dow_burn_tax.columns = ['atm_id','day_num','avg_daily_burn_tax']
current_balance_tax = txn_df[txn_df['transaction_date']=='2024-02-15'][['atm_id','cash_balance_eod']]

forecast_records = []
for atm_id in atm_df['atm_id']:
    # Standard forecast
    bal_row = current_balance[current_balance['atm_id']==atm_id]['cash_balance_eod'].values
    if len(bal_row) == 0: continue
    bal = bal_row[0]
    total_burn = 0
    for day_num in [0,1,2]:
        db = dow_burn[(dow_burn['atm_id']==atm_id)&(dow_burn['day_num']==day_num)]['avg_daily_burn']
        burn = db.values[0] if len(db) > 0 else last_30[last_30['atm_id']==atm_id]['daily_cash_dispensed'].mean()
        total_burn += burn
    projected_bal = max(0, bal - total_burn)

    # Tax peak forecast
    bal_tax_row = current_balance_tax[current_balance_tax['atm_id']==atm_id]['cash_balance_eod'].values
    bal_tax = bal_tax_row[0] if len(bal_tax_row) > 0 else bal
    total_burn_tax = 0
    for day_num in [0,1,2]:
        db = dow_burn_tax[(dow_burn_tax['atm_id']==atm_id)&(dow_burn_tax['day_num']==day_num)]['avg_daily_burn_tax']
        burn = db.values[0] if len(db) > 0 else last_30_tax[last_30_tax['atm_id']==atm_id]['daily_cash_dispensed'].mean()
        total_burn_tax += burn
    projected_bal_tax = max(0, bal_tax - total_burn_tax)

    atm_row = atm_df[atm_df['atm_id']==atm_id].iloc[0]
    capacity = atm_row['cash_capacity_dollars']
    tax_proximity = atm_row['tax_service_proximity']

    pct_remaining = (projected_bal / capacity) * 100
    pct_remaining_tax = (projected_bal_tax / capacity) * 100
    days_remaining = projected_bal / (total_burn / 3) if total_burn > 0 else 99

    # Standard tolerance
    threshold_map = {'Zero':30,'Low':25,'Medium':20,'High':15}
    cash_tol = atm_row['cash_tolerance']
    critical_pct = threshold_map[cash_tol]
    is_critical = pct_remaining <= critical_pct

    # Tax peak tolerance — proximity machines reclassified to Zero
    tax_peak_tol = 'Zero' if tax_proximity else cash_tol
    tax_peak_threshold = 30
    is_critical_tax_peak = pct_remaining_tax <= tax_peak_threshold

    def risk_score(pct, terminal, tolerance, revenue, tax_prox=False, tax_peak=False):
        s = max(0, (30 - pct) * 2)
        s += {'Over The Road':40,'Remote':20,'Local':5}[terminal]
        s += {'Zero':35,'Low':20,'Medium':10,'High':0}[tolerance]
        s += revenue / 20
        if tax_prox and tax_peak:
            s += 25  # Tax service proximity premium during peak season
        return round(s, 1)

    score = risk_score(pct_remaining, atm_row['terminal_type'], cash_tol, atm_row['revenue_impact_per_hour'])
    score_tax = risk_score(pct_remaining_tax, atm_row['terminal_type'], tax_peak_tol,
                           atm_row['revenue_impact_per_hour'], tax_proximity, True)

    forecast_records.append({
        'atm_id': atm_id,
        'location_name': atm_row['location_name'],
        'city': atm_row['city'],
        'location_type': atm_row['location_type'],
        'terminal_type': atm_row['terminal_type'],
        'cash_tolerance': cash_tol,
        'tax_service_proximity': tax_proximity,
        'distance_from_branch_miles': atm_row['distance_from_branch_miles'],
        'cash_capacity_dollars': capacity,
        'current_balance': round(bal, 2),
        'projected_72hr_balance': round(projected_bal, 2),
        'projected_pct_remaining': round(pct_remaining, 1),
        'projected_pct_remaining_tax_peak': round(pct_remaining_tax, 1),
        'days_until_empty': round(days_remaining, 1),
        'total_72hr_burn': round(total_burn, 2),
        'total_72hr_burn_tax_peak': round(total_burn_tax, 2),
        'emergency_multiplier': atm_row['emergency_multiplier'],
        'revenue_impact_per_hour': atm_row['revenue_impact_per_hour'],
        'revenue_at_risk_72hr': round(atm_row['revenue_impact_per_hour'] * 72, 2),
        'is_critical_72hr': is_critical,
        'is_critical_tax_peak': is_critical_tax_peak,
        'critical_threshold_pct': critical_pct,
        'composite_risk_score': score,
        'composite_risk_score_tax_peak': score_tax,
        'status': 'CRITICAL' if is_critical else 'ELEVATED',
        'status_tax_peak': 'CRITICAL' if is_critical_tax_peak else 'ELEVATED'
    })

forecast_df = pd.DataFrame(forecast_records).sort_values('composite_risk_score', ascending=False).reset_index(drop=True)
forecast_df['priority_rank'] = forecast_df.index + 1
forecast_df_tax = forecast_df.sort_values('composite_risk_score_tax_peak', ascending=False).reset_index(drop=True)
forecast_df_tax['priority_rank_tax_peak'] = forecast_df_tax.index + 1

# =============================================================================
# SECTION 4 — CONSOLE OUTPUT
# =============================================================================

total_atms = len(forecast_df)
critical_count = forecast_df['is_critical_72hr'].sum()
otr_critical = len(forecast_df[(forecast_df['terminal_type']=='Over The Road') & forecast_df['is_critical_72hr']])
total_revenue_at_risk = (forecast_df[forecast_df['is_critical_72hr']]['revenue_impact_per_hour'] * 72).sum()
avg_network_cash = forecast_df['projected_pct_remaining'].mean()
tax_machines = atm_df['tax_service_proximity'].sum()

print("=" * 70)
print("ATM PREDICTIVE DEMAND MODEL v3 — ANALYSIS COMPLETE")
print("Full Year | Tax Season | Tax Service Proximity | Terminal Tier")
print("=" * 70)
print(f"\n NETWORK SUMMARY (72-Hour Standard Forecast)")
print(f"  Total ATMs Monitored:           {total_atms}")
print(f"  Tax Service Proximity Machines: {tax_machines} ({(tax_machines/total_atms)*100:.0f}% of network)")
print(f"  Critical in 72 Hours:           {critical_count} ({(critical_count/total_atms)*100:.0f}% of network)")
print(f"  Over The Road Critical:         {otr_critical}")
print(f"  Avg Network Cash Remaining:     {avg_network_cash:.1f}%")
print(f"  Revenue at Risk (72hr):         ${total_revenue_at_risk:,.0f}")

print(f"\n TAX SERVICE PROXIMITY — THE PENN STATION EFFECT")
print(f"  Standard reporting classification vs Tax Peak reclassification:")
print("-" * 70)
tax_machines_df = forecast_df[forecast_df['tax_service_proximity']]
for _, row in tax_machines_df.iterrows():
    standard_burn = row['total_72hr_burn']
    peak_burn = row['total_72hr_burn_tax_peak']
    if standard_burn > 0:
        multiplier = peak_burn / standard_burn
    else:
        multiplier = 0
    print(f"  {row['atm_id']} | {row['location_name']:<28} | "
          f"Standard: {row['cash_tolerance']:<6} | "
          f"Tax Peak: Zero | Burn multiplier: {multiplier:.1f}x")

print(f"\n TAX SEASON IMPACT — Avg Daily Cash Dispensed")
print("-" * 70)
merged = txn_df.merge(atm_df[['atm_id','location_type','terminal_type']], on='atm_id')
for ltype in ['Retail','Urban','Casino','Mall']:
    baseline = merged[(merged['location_type']==ltype)&(merged['season']=='Baseline')]['daily_cash_dispensed'].mean()
    peak = merged[(merged['location_type']==ltype)&(merged['season']=='Tax Season Peak')]['daily_cash_dispensed'].mean()
    if baseline > 0:
        lift = ((peak - baseline) / baseline) * 100
        print(f"  {ltype:<10} | Baseline: ${baseline:>8,.0f}/day | Tax Peak: ${peak:>8,.0f}/day | Lift: +{lift:.0f}%")

tax_prox_baseline = merged[(merged['tax_service_proximity']==True)&(merged['season']=='Baseline')]['daily_cash_dispensed'].mean()
tax_prox_peak = merged[(merged['tax_service_proximity']==True)&(merged['season']=='Tax Season Peak')]['daily_cash_dispensed'].mean()
lift_prox = ((tax_prox_peak - tax_prox_baseline) / tax_prox_baseline) * 100
print(f"  {'Tax Svc Prox':<10} | Baseline: ${tax_prox_baseline:>8,.0f}/day | Tax Peak: ${tax_prox_peak:>8,.0f}/day | Lift: +{lift_prox:.0f}%")

print(f"\n TOP 10 PRIORITY ATMs (Standard Forecast)")
print("-" * 70)
for _, row in forecast_df.head(10).iterrows():
    prox = " ⚑ TAX SVC" if row['tax_service_proximity'] else ""
    print(f"  #{int(row['priority_rank'])} {row['atm_id']} | {row['location_name'][:26]:<26} | "
          f"{row['terminal_type']:<14} | {row['projected_pct_remaining']:>5.1f}% | "
          f"Risk: {row['composite_risk_score']:>5.1f} | {row['status']}{prox}")

print("\n" + "=" * 70)

# =============================================================================
# SECTION 5 — SAVE ALL OUTPUTS
# =============================================================================
atm_df.to_csv('/home/claude/ATM-Predictive-Demand-Model/atm_master.csv', index=False)
txn_df.to_csv('/home/claude/ATM-Predictive-Demand-Model/atm_transactions.csv', index=False)
forecast_df.to_csv('/home/claude/ATM-Predictive-Demand-Model/atm_forecast.csv', index=False)
print("CSVs saved successfully")
print(f"  atm_master.csv        — {len(atm_df)} rows")
print(f"  atm_transactions.csv  — {len(txn_df):,} rows")
print(f"  atm_forecast.csv      — {len(forecast_df)} rows")
