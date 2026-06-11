import pandas as pd

import matplotlib
matplotlib.use('TkAgg')   # or 'QtAgg'


# import matplotlib
# matplotlib.use('Agg')

import os
import matplotlib.pyplot as plt
plt.close('all')
import matplotlib.colors as mcolors



from matplotlib.ticker import ScalarFormatter
from datetime import datetime
import seaborn as sns
import numpy as np
show_all=False

#taken from https://www.investing.com/crypto/bitcoin/btc-usd-historical-data

#https://www.blockchain.com/explorer/charts/transaction-fees
import requests
import json
from datetime import timedelta
#todo add etherium
#todo etherium data from defilamma https://defillama.com/docs/api
#to do spiral presentation
#website to look at: https://charts.bitbo.io/monthly-rsi/

#https://www.bitcoinmagazinepro.com/charts/mvrv-zscore/
#bitcoin reserve balance
#https://cryptoquant.com/asset/btc/chart/exchange-flows/exchange-reserve?exchange=all_exchange&window=DAY&sma=0_14&ema=0&priceScale=log&metricScale=linear&chartStyle=line
#https://www.coinglass.com/Balance


start = '2010-01-01'
end = '2028-05-01'



# Function to calculate the mining reward for a given date
def calculate_mining_reward(date):
    reward = 50.0  # Initial reward of 50 BTC

    for halving_date in bitcoin_halving_dates:
        if date >= halving_date:
            reward /= 2

    return reward

#market-price


import pandas as pd
import requests
import json


bitcoin_halving_dates = [
    datetime(2012, 11, 28),  # 1st Halving
    datetime(2016, 7, 9),   # 2nd Halving
    datetime(2020, 5, 11),  # 3rd Halving
    datetime(2024, 4, 19),  #  4th Halving
    datetime(2028, 3, 31)    # Estimated 5th Halving
]

ordinal_date=datetime(2023, 1, 22)
ETF_date=datetime(2024, 1, 10)
GOX_dist_date=datetime(2024, 7, 20)
Trump_won_date=datetime(2024, 11, 5)
GOX_collapse_date=datetime(2014, 2, 28)
Cyprus_haircut_date=datetime(2013, 3, 17)

china_ban_date=datetime(2021, 5, 15)
x_limit = datetime(2024, 6, 1)


year=365
three_months=90

def fetch_and_process(url, column_name, df_main=None):
    # Fetch data from the API
    response = requests.get(url)
    data = json.loads(response.content)
    data = data.get('values', [])

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Process DataFrame
    df['Date'] = pd.to_datetime(df['x'], unit='s', utc=True)
    df = df.rename(columns={'y': column_name})
    df.set_index('Date', inplace=True)
    df.drop(columns=['x'], inplace=True)

    df = df.resample('D').last()

    df = df.tz_localize(None)  # Remove time zone information, making it naive
    # df_fee = df_fee.tz_convert(df.index.tz)  # Convert to the time zone of df

    # If there's a main DataFrame, merge this data into it
    if df_main is not None:
        df_main = pd.merge(df_main, df, left_index=True, right_index=True, how='left')
        return df_main
    return df



def mark_bitcoin_halvings(ax, halving_dates, color='red', linestyle='-', alpha=0.6):
    """
    Mark Bitcoin halving dates on a given matplotlib Axes.
    Parameters:
    - ax: matplotlib.axes.Axes object
    - halving_dates: list of datetime or numeric values
    - color: line color (default 'red')
    - linestyle: line style (default '--')
    - alpha: transparency of the line (default 0.6)
    """
    for i, date in enumerate(halving_dates, 1):
        ax.axvline(date, color=color, linestyle=linestyle, alpha=alpha, label='Bitcoin Halving')
        ax.text(date, ax.get_ylim()[0], f' Halving {i}', rotation=90, ha='right', va='bottom')
        if i < len(bitcoin_halving_dates): #DRAW THE MID OF THE HALVING
            plt.axvline(date + (bitcoin_halving_dates[i] - date) / 2, color='red', linestyle='--', alpha=0.6)
            ax.text(date + (bitcoin_halving_dates[i] - date) / 2, ax.get_ylim()[0], f' mid', rotation=90, ha='right', va='bottom')




def mark_only_bitcoin_halvings(ax, halving_dates, color='red', linestyle='-', alpha=0.6):
    """
    Mark Bitcoin halving dates on a given matplotlib Axes.
    Parameters:
    - ax: matplotlib.axes.Axes object
    - halving_dates: list of datetime or numeric values
    - color: line color (default 'red')
    - linestyle: line style (default '--')
    - alpha: transparency of the line (default 0.6)
    """
    for i, date in enumerate(halving_dates, 1):
        ax.axvline(date, color=color, linestyle=linestyle, alpha=alpha, label='Bitcoin Halving')
        ax.text(date, ax.get_ylim()[0], f' Halving {i}', rotation=90, ha='right', va='bottom')
        # if i < len(bitcoin_halving_dates): #DRAW THE MID OF THE HALVING
        #     plt.axvline(date + (bitcoin_halving_dates[i] - date) / 2, color='red', linestyle='--', alpha=0.6)
        #     ax.text(date + (bitcoin_halving_dates[i] - date) / 2, ax.get_ylim()[0], f' mid', rotation=90, ha='right', va='bottom')





# URLs
urls = [
    (
    'https://api.blockchain.info/charts/market-price?timespan=18years&rollingAverage=24hours&start=2010-01-01&format=json&sampled=false',
    'Price'),
    (
    'https://api.blockchain.info/charts/transaction-fees?timespan=18years&rollingAverage=24hours&start=2010-01-01&format=json&sampled=false',
    'fees'),
    ('https://api.blockchain.info/charts/hash-rate?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'hashrate'),
    (
    'https://api.blockchain.info/charts/estimated-transaction-volume-usd?timespan=18years&start=2010-01-01&format=json&sampled=false',
    'transaction_volume'),
    ('https://api.blockchain.info/charts/n-transactions?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'transactions_per_day'),

    # ('https://api.blockchain.info/charts/mempool-size?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #  'mempool_size'),
    # ('https://api.blockchain.info/charts/trade-volume?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #  'trade_volume'),
    # ('https://api.blockchain.info/charts/blocks-size?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #  'blocks_size'),
    ('https://api.blockchain.info/charts/miners-revenue?timespan=18years&start=2010-01-01&format=json&sampled=false',
        'miners_revenue'
    ),
    ( 'https://api.blockchain.info/charts/cost-per-transaction?timespan=18years&start=2010-01-01&format=json&sampled=false',
        'cost_per_transaction'
    ),
    # (
    #     'https://api.blockchain.info/charts/difficulty?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #     'Bitcoin_network_difficulty'
    # ),
    # (
    #     'https://api.blockchain.info/charts/avg-confirmation-time?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #     'avg_confirmation_time'
    # )


    #
    # ('https://api.blockchain.info/charts/transaction-rate?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #     'transaction_rate'
    # )
]



# Initialize main DataFrame
df = None

# Process each URL
for url, name in urls:
    print(f'downloading {name} from {url}')
    df = fetch_and_process(url, name, df)

# Show the result
print(df)



############################################
df = df.resample('D').last()

max_values_for_halving_periods = []
for i in range(len(bitcoin_halving_dates)):
    if i == 0:
        start_date = df.index[0]
    else:
        start_date = bitcoin_halving_dates[i - 1]
    end_date = bitcoin_halving_dates[i]
    reduced_end_date = end_date - timedelta(days=60) #reducing 60 days since the maximum should be in the cycle not at the end of the cycle


    # Select the data within the date range
    #subset = df[(df.index >= start_date) & (df.index <= reduced_end_date)]
    subset = df[(df.index >= start_date) & (df.index <= reduced_end_date)]

    # Find the maximum value within the date range
    #max_value = subset['Price'].max()
    max_value = subset['Price'].max()


    # Find the date at which the maximum value occurs
    #max_date = subset.loc[subset['Price'].idxmax()].name
    max_date = subset.loc[subset['Price'].idxmax()].name

    max_values_for_halving_periods.append((start_date, end_date, max_date, max_value,  max_date, max_value))


#####################################
# 1. Change logy to False for a linear scale
plt.figure()
plt.rcParams.update({'font.size': 14})
ax = df['Price'].plot(logy=False)

#plt.legend(loc='upper left', labels=['Price'])

# 2. Keep these to ensure the Y-axis shows full numbers (e.g., 100000) instead of scientific notation
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.ticklabel_format(style='plain', axis='y')

#plt.grid(True)
#plt.title('Daily Price')
x_limit = datetime(2026, 8, 1)
plt.xlim(df.index[0], x_limit)
plt.ylabel('USD')
# 3. Show the plot
plt.show(block=False)
plt.savefig('f_bitcoin_price.pdf', bbox_inches='tight')

##########################

#####################################
# 1. Change logy to False for a linear scale
plt.figure()
plt.rcParams.update({'font.size': 14})
ax = df['Price'].plot(logy=True)

#plt.legend(loc='upper left', labels=['Price'])

# 2. Keep these to ensure the Y-axis shows full numbers (e.g., 100000) instead of scientific notation
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
ax.ticklabel_format(style='plain', axis='y')

#plt.grid(True)
#plt.title('Daily Price')
x_limit = datetime(2026, 8, 1)
plt.xlim(df.index[0], x_limit)
plt.ylabel('USD')
# 3. Show the plot
plt.show(block=False)
plt.savefig('f_bitcoin_log_price.pdf', bbox_inches='tight')

##########################


########################





###################
################################PREDICTION####
plt.figure(figsize=(20, 8))
ax=df['Price'].plot(logy=True)
plt.legend(loc='upper left', labels=['Price'])
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
#plt.grid(True)
#plt.title('Daily Price')
x_limit = datetime(2030, 2, 1)
plt.xlim(df.index[0], x_limit)
# Shade future prediction region
today = datetime.today()

plt.axvspan(
    today,
    x_limit,
    color='gray',
    alpha=0.08
)

# Vertical line for today
plt.axvline(
    today,
    color='black',
    linestyle='--',
    linewidth=1,
    alpha=0.7
)

# Today label
plt.text(
    today + pd.DateOffset(days=10),
    0.08,
    'Today',
    rotation=90,
    fontsize=11,
    color='black',
    ha='left',
    va='bottom'
)

# Prediction region label
plt.text(
    today + (x_limit - today) / 2,
    3000,
    'Prediction Region',
    fontsize=18,
    color='gray',
    alpha=0.35,
    ha='center',
    va='center'
)
mark_bitcoin_halvings(ax, bitcoin_halving_dates)

i=0;
for start_date, end_date, max_date, max_value,  max_date, max_value in max_values_for_halving_periods:
    subset = df[(df.index >= max_date) & (df.index <= end_date)]
    min_value = subset['Price'].min()
    min_date = subset.loc[subset['Price'].idxmin()].name
    #daily Maximum Price = {max_value:.1f}
    # Plot maximum points
    plt.scatter(max_date, max_value, c='red', marker='o', label='Max Points')

    if i<4:
        # Plot minimum points
        plt.scatter(min_date, min_value, c='blue', marker='x', label='Min Points')
#        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
#                     arrowprops=dict(arrowstyle='->', color='black'))
        #
        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='->', color='black'))
        #plt.text(min_date, min_value,f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}% / y",
        #        ha='left', va='bottom')
        plt.text(min_date- pd.DateOffset(months=3), min_value*0.60,
                 f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}%{'/year' if i == 0 else '/y'}",
                 ha='left', va='bottom')

    dur_down = min_date.date() - max_date.date()

    if i>0 :
        dur_up=max_date.date()-prev_min_date.date()
        plt.annotate('', xy=(max_date, max_value), xytext=(prev_min_date,  prev_min),
                     arrowprops=dict(arrowstyle='->', color='black'))
        plt.text(max_date- pd.DateOffset(months=4), max_value, f"{((max_value/prev_min)**(1/((max_date-prev_min_date).days/365.25))-1)*100:+.1f}%{'/year' if i==1 else '/y'}", ha='left', va='bottom')
        print(f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:.1f} up fac={max_value/prev_min:>5.1f} dur_down={dur_down.days} dur_up={dur_up.days}")
    else:
        print(
            f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:5.1f} dur_down={dur_down.days}")

    prev_min=min_value
    prev_min_date=min_date


    if i==3:
        max_date_pred=min_date+ + timedelta(days=1000) #last two duration were 1067 and 1059 hence I took 1000
        max_value_pred1=min_value*5
        max_value_pred2=min_value*8
        max_value_pred3=min_value*11



    if i==4:
        min_date_pred=max_date+ + timedelta(days=350) #last three duration were 404,364,378 - I take less than a year: 340
        min_value_pred1=max_value/2.41
        min_value_pred2=max_value/3.17
        min_value_pred3=max_value/4.68

        plt.scatter(min_date_pred, min_value_pred1, facecolors='none', edgecolor='green', marker='o', label='Min Points')
        plt.scatter(min_date_pred, min_value_pred2, facecolors='none', edgecolor='green', marker='o', label='Min Points')
        plt.scatter(min_date_pred, min_value_pred3, facecolors='none', edgecolor='green', marker='o', label='Min Points')
        plt.annotate('', xy=(min_date_pred, min_value_pred1), xytext=(max_date, max_value),
                     arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.text(min_date_pred, min_value_pred1 * 1.1,
                 f"{((min_value_pred1 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%/y",
                 ha='left', va='bottom')
        plt.annotate('', xy=(min_date_pred, min_value_pred2), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.text(min_date_pred, min_value_pred2 * .8,
                 f"{((min_value_pred2 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%/y",
                 ha='left', va='bottom')
        plt.annotate('', xy=(min_date_pred, min_value_pred3), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.text(min_date_pred, min_value_pred3 * .55,
                 f"{((min_value_pred3 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%/y",
                 ha='left', va='bottom')

#        print(f"Prediction {end_date.date()} and {end_date.date()+timedelta(days=4*365)}: W Max Price = {max_value_pred2:>7.1f}  on {max_date_pred.date()} week Min Price pred = {min_value_pred2:>7.1f} up fac=8")

        # -----------------------------
        # Upward prediction after bottom
        # Assume 80% annual return for 1000 days
        # -----------------------------
        up_days = 1000
        up_date_pred = min_date_pred + timedelta(days=up_days)

        annual_growth1 = 2.20  # 80% yearly growth factor
        annual_growth2 = 2.00  # 80% yearly growth factor
        annual_growth3 = 1.80  # 80% yearly growth factor


        up_value_pred1 = min_value_pred2 * (annual_growth1 ** (up_days / 365.25))
        up_value_pred2 = min_value_pred2 * (annual_growth2 ** (up_days / 365.25))
        up_value_pred3 = min_value_pred2 * (annual_growth3 ** (up_days / 365.25))


        # Plot future peak prediction points
        # plt.scatter(min_date_pred, min_value_pred1, facecolors='none', edgecolor='green', marker='o',
        #             label='Min Points')
        plt.scatter(up_date_pred, up_value_pred1, facecolors='none', edgecolor='green', marker='o')
        plt.scatter(up_date_pred, up_value_pred2, facecolors='none', edgecolor='green', marker='o')
        plt.scatter(up_date_pred, up_value_pred3, facecolors='none', edgecolor='green', marker='o')

        # Connect predicted bottoms to predicted tops
        plt.annotate(
            '',
            xy=(up_date_pred, up_value_pred1),
            xytext=(min_date_pred, min_value_pred2),
            arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted')
        )

        plt.annotate(
            '',
            xy=(up_date_pred, up_value_pred2),
            xytext=(min_date_pred, min_value_pred2),
            arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted')
        )

        plt.annotate(
            '',
            xy=(up_date_pred, up_value_pred3),
            xytext=(min_date_pred, min_value_pred2),
            arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted')
        )

        plt.text(up_date_pred + pd.DateOffset(months=1), up_value_pred1*1,
                 f"{((up_value_pred1 / min_value_pred2) ** (1 / ((up_date_pred - min_date_pred).days / 365.25)) - 1) * 100:+.0f}%{'/year' if i == 1 else '/y'}",
                 ha='left', va='bottom')
        plt.text(up_date_pred + pd.DateOffset(months=1), up_value_pred2*0.8,
                 f"{((up_value_pred2 / min_value_pred2) ** (1 / ((up_date_pred - min_date_pred).days / 365.25)) - 1) * 100:+.0f}%{'/year' if i == 1 else '/y'}",
                 ha='left', va='bottom')
        plt.text(up_date_pred + pd.DateOffset(months=1), up_value_pred3*0.6,
                 f"{((up_value_pred3 / min_value_pred2) ** (1 / ((up_date_pred - min_date_pred).days / 365.25)) - 1) * 100:+.0f}%{'/year' if i == 1 else '/y'}",
                 ha='left', va='bottom')

        # plt.text(
        #     up_date_pred+ pd.DateOffset(months=1),
        #     up_value_pred2 * 1.05,
        #     '+95%/y',
        #     color='black',
        #     fontsize=12,
        #     ha='left'
        # )


    i=i+1
plt.ylabel('USD')
plt.show(block=False)
plt.savefig('f_pred.pdf', bbox_inches='tight')


########################################



####################CYCLE ################
plt.figure()
ax=df['Price'].plot(logy=True)
#plt.legend(loc='upper left', labels=['Price'])
plt.ylabel('USD')
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
plt.grid(True)
#plt.title('Daily Price')
x_limit = datetime(2028, 6, 1)
plt.xlim(df.index[0], x_limit)
mark_bitcoin_halvings(ax, bitcoin_halving_dates)

i=0;
for start_date, end_date, max_date, max_value,  max_date, max_value in max_values_for_halving_periods:
    subset = df[(df.index >= max_date) & (df.index <= end_date)]
    min_value = subset['Price'].min()
    min_date = subset.loc[subset['Price'].idxmin()].name
    #daily Maximum Price = {max_value:.1f}
    # Plot maximum points
    plt.scatter(max_date, max_value, c='red', marker='o', label='Max Points')

    if i<4:
        # Plot minimum points
        plt.scatter(min_date, min_value, c='blue', marker='x', label='Min Points')
#        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
#                     arrowprops=dict(arrowstyle='->', color='black'))
        #
        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='->', color='black'))
        #plt.text(min_date, min_value,f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}% / y",
        #        ha='left', va='bottom')
#        plt.text(min_date, min_value*0.8,
#                 f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}%{'/year' if i == 0 else '/y'}",
#                 ha='left', va='bottom')

    dur_down = min_date.date() - max_date.date()

    if i>0 :
        dur_up=max_date.date()-prev_min_date.date()
        plt.annotate('', xy=(max_date, max_value), xytext=(prev_min_date,  prev_min),
                     arrowprops=dict(arrowstyle='->', color='black'))
     #   plt.text(max_date, max_value, f"{((max_value/prev_min)**(1/((max_date-prev_min_date).days/365.25))-1)*100:.1f}%{'/year' if i==1 else '/y'}", ha='left', va='bottom')
        print(f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:.1f} up fac={max_value/prev_min:>5.1f} dur_down={dur_down.days} dur_up={dur_up.days}")
    else:
        print(
            f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:5.1f} dur_down={dur_down.days}")

    prev_min=min_value
    prev_min_date=min_date


    if i==3:
        max_date_pred=min_date+ + timedelta(days=1000) #last two duration were 1067 and 1059 hence I took 1000
        max_value_pred1=min_value*5
        max_value_pred2=min_value*8
        max_value_pred3=min_value*11



    if i==4:
        min_date_pred=max_date+ + timedelta(days=340) #last three duration were 404,364,378 - I take less than a year: 340
        min_value_pred1=max_value/2
        min_value_pred2=max_value/3
        min_value_pred3=max_value/4




    i=i+1
plt.show(block=False)
plt.savefig('f_cycle.pdf', bbox_inches='tight')













################## UP  ##################
plt.figure()
ax=df['Price'].plot(logy=True)
#plt.legend(loc='upper left', labels=['Price'])
plt.ylabel('USD')
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
#plt.grid(True)
#plt.title('Daily Price')
ax.set_xlim(pd.to_datetime(start), pd.to_datetime(end))
mark_only_bitcoin_halvings(ax, bitcoin_halving_dates)

i=0;
for start_date, end_date, max_date, max_value,  max_date, max_value in max_values_for_halving_periods:
    subset = df[(df.index >= max_date) & (df.index <= end_date)]
    min_value = subset['Price'].min()
    min_date = subset.loc[subset['Price'].idxmin()].name
    #daily Maximum Price = {max_value:.1f}
    # Plot maximum points
    if i > 0:
        plt.scatter(max_date, max_value, c='red', marker='o', label='Max Points')

    if i<4:
        # Plot minimum points
        plt.scatter(min_date, min_value, c='blue', marker='x', label='Min Points')
#        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
#                 arrowprops=dict(arrowstyle='->', color='black'))

    dur_down = min_date.date() - max_date.date()

    if i>0 :
        dur_up=max_date.date()-prev_min_date.date()
        plt.annotate('', xy=(max_date, max_value), xytext=(prev_min_date,  prev_min),
                     arrowprops=dict(arrowstyle='->', color='black'))
     #   plt.text(max_date, max_value, f"{((max_value/prev_min)**(1/((max_date-prev_min_date).days/365.25))-1)*100:.1f}%{'/year' if i==1 else '/y'}", ha='left', va='bottom')
        print(f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:.1f} up fac={max_value/prev_min:>5.1f} dur_down={dur_down.days} dur_up={dur_up.days}")
    else:
        print(
            f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:5.1f} dur_down={dur_down.days}")

    prev_min=min_value
    prev_min_date=min_date


    i=i+1
plt.show(block=False)
plt.savefig('f_cycle_only_up.pdf', bbox_inches='tight')











##############  Down  ######################
plt.figure()
ax=df['Price'].plot(logy=True)
#plt.legend(loc='upper left', labels=['Price'])
plt.ylabel('USD')
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
plt.grid(True)
#plt.title('Daily Price')
# x_limit = datetime(2028, 6, 1)
# plt.xlim(df.index[0], x_limit)
ax.set_xlim(pd.to_datetime(start), pd.to_datetime(end))

mark_bitcoin_halvings(ax, bitcoin_halving_dates)

i=0;
for start_date, end_date, max_date, max_value,  max_date, max_value in max_values_for_halving_periods:
    subset = df[(df.index >= max_date) & (df.index <= end_date)]
    min_value = subset['Price'].min()
    min_date = subset.loc[subset['Price'].idxmin()].name
    #daily Maximum Price = {max_value:.1f}
    # Plot maximum points
    plt.scatter(max_date, max_value, c='red', marker='o', label='Max Points')

    if i<4:
        # Plot minimum points
        plt.scatter(min_date, min_value, c='blue', marker='x', label='Min Points')
#        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
#                     arrowprops=dict(arrowstyle='->', color='black'))
        #
        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='->', color='black'))

    dur_down = min_date.date() - max_date.date()

    if i>0 :
        dur_up=max_date.date()-prev_min_date.date()
#        plt.annotate('', xy=(max_date, max_value), xytext=(prev_min_date,  prev_min),
#                     arrowprops=dict(arrowstyle='->', color='black'))
     #   plt.text(max_date, max_value, f"{((max_value/prev_min)**(1/((max_date-prev_min_date).days/365.25))-1)*100:.1f}%{'/year' if i==1 else '/y'}", ha='left', va='bottom')
        print(f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:.1f} up fac={max_value/prev_min:>5.1f} dur_down={dur_down.days} dur_up={dur_up.days}")
    else:
        print(
            f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:5.1f} dur_down={dur_down.days}")

    prev_min=min_value
    prev_min_date=min_date


    if i==3:
        max_date_pred=min_date+ + timedelta(days=1000) #last two duration were 1067 and 1059 hence I took 1000
        max_value_pred1=min_value*5
        max_value_pred2=min_value*8
        max_value_pred3=min_value*11



    if i==4:
        min_date_pred=max_date+ + timedelta(days=340) #last three duration were 404,364,378 - I take less than a year: 340
        min_value_pred1=max_value/2
        min_value_pred2=max_value/3
        min_value_pred3=max_value/4




    i=i+1
plt.show(block=False)
plt.savefig('f_down.pdf', bbox_inches='tight')











#####mining reward/cost
#do the energy cost
#add a columd of bitcoin award,
#calculate the number of bitcoin per week
#multiply and show

df['Reward'] = df.index.map(calculate_mining_reward)
df['Mining cost']=df['Price']*(df['Reward']*6*24*365/1_000_000_000) #6 per hours since its 10 min

# ax = df[['Price', 'Mining cost']].plot(secondary_y='Mining cost', logy=True)
df['fees'] = df['fees'].fillna(0)  #replace Nan with Zeros
df['fees cost']=(df['fees']*df['Price']*365)/1_000_000_000 #annual
df['total_cost']=df['Mining cost']+df['fees cost']
df['percentage_fees']=(df['fees cost']/df['total_cost'])*100
df['total_cost_MA_365'] = df['total_cost'].rolling(window=365).mean()
df['total_cost_MA_730'] = df['total_cost'].rolling(window=730).mean()
df['total_cost_MA_90'] = df['total_cost'].rolling(window=90).mean()

fig, ax1 = plt.subplots()

# Plot the "Price" column on a semilog y-axis
ax1.set_yscale('log')
ax1.set_ylabel('Price (log scale)', color='tab:blue')
ax1.plot(df.index, df['Price'], color='tab:blue', label='Price')
ax1.tick_params(axis='y', labelcolor='tab:blue')

# Create a second y-axis for "Mining cost"
ax2 = ax1.twinx()

# Plot the "Mining cost" column on a linear y-axis
ax2.set_yscale('linear')
ax2.set_ylabel('total_cost (fee+reward)', color='tab:red')
ax2.plot(df.index, df['total_cost'], color='tab:red', label='Mining cost (fee+reward)')
ax2.tick_params(axis='y', labelcolor='tab:red')
#ax2.plot(df.index, df['total_cost_MA_365'], color='tab:green', label='Mining total cost MA 365')
#ax2.plot(df.index, df['total_cost_MA_730'], color='tab:orange', label='Mining total cost MA 730')
ax2.plot(df.index, df['total_cost_MA_90'], color='tab:olive', label='Mining cost averaged 90 days')


#from bradLwhat is electrical energy cost of the 10  biggest countries for whole year in 2022? Give me the result in a table
#Country        Estimated Consumption (TWh)     Assumed Price ($/kWh) \$        Estimated Cost ( Billion
#Italy  310     0.17    52.7
#California     255     0.15    38.25
#Brazil 309     0.1     30.9
#Egypt  192     0.1     19.2
#New York State 124     0.19    23.56
#Florida        181     0.14    25.34
#North Carolina 118     0.15    17.70
#Israel  66 0.15  9.9
#Nevada 58 0.14 8.12
#Jordan  17     0.13  2.21
#whole world  25000 0.12 3000 Billion
# Add a legend
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="upper left")

# Set the y-axis limits for "Mining cost" between 1 and 30
ax2.set_ylim(0, 45)



ax1.set_xlim(pd.to_datetime(start), pd.to_datetime(end))

# Add a title
plt.title('Bitcoin Price and Mining Cost')

mark_bitcoin_halvings(ax1, bitcoin_halving_dates)
plt.grid(True)
# Show the plot
plt.show(block=False)
plt.savefig('f_cost.pdf', bbox_inches='tight')




















###Printing cycles with dates###########
#################### CYCLE ################
plt.figure(figsize=(12, 7))

ax = df['Price'].plot(logy=True)

plt.ylabel('USD')
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
plt.grid(True)

x_limit = datetime(2028, 6, 1)
plt.xlim(df.index[0], x_limit)

# Draw halving lines
mark_bitcoin_halvings(ax, bitcoin_halving_dates)

# Add arrows and exact date labels for halvings
for idx, halving_date in enumerate(bitcoin_halving_dates):

    # Put first halving label on the right
    if idx == 0:
        x_offset = 40
    else:
        x_offset = -40 if idx % 2 == 0 else 40

    y_arrow_target = 2
    y_text_offset = 25

    # Add "Predicted" above the 5th halving
    label_text = halving_date.strftime('%Y-%m-%d')
    if idx == 4:
        label_text = f"Predicted\n{halving_date.strftime('%Y-%m-%d')}"

    plt.annotate(
        label_text,
        xy=(halving_date, y_arrow_target),
        xytext=(x_offset, y_text_offset),
        textcoords='offset points',
        ha='center',
        va='bottom',
        fontsize=10,
        color='darkred',
        bbox=dict(
            boxstyle='round,pad=0.2',
            fc='white',
            ec='darkred',
            alpha=0.8
        ),
        arrowprops=dict(
            arrowstyle='->',
            color='darkred',
            lw=0.8
        )
    )

i = 0

for start_date, end_date, max_date, max_value, max_date, max_value in max_values_for_halving_periods:

    subset = df[(df.index >= max_date) & (df.index <= end_date)]
    min_value = subset['Price'].min()
    min_date = subset.loc[subset['Price'].idxmin()].name

    # Plot maximum point
    plt.scatter(max_date, max_value, c='red', marker='o', s=50)

    # Skip date labels for the first cycle
    if i > 0:
        plt.annotate(
            max_date.strftime('%Y-%m-%d'),
            xy=(max_date, max_value),
            xytext=(0, 15),
            textcoords='offset points',
            ha='center',
            va='bottom',
            fontsize=12,
            color='red',
            arrowprops=dict(
                arrowstyle='->',
                color='red',
                lw=0.8
            )
        )

    if i < 4:
        # Plot minimum point
        plt.scatter(min_date, min_value, c='blue', marker='x', s=60)

        # Skip date labels for the first cycle minimum
        if i > 0:
            plt.annotate(
                min_date.strftime('%Y-%m-%d'),
                xy=(min_date, min_value),
                xytext=(0, -25),
                textcoords='offset points',
                ha='center',
                va='top',
                fontsize=12,
                color='blue',
                arrowprops=dict(
                    arrowstyle='->',
                    color='blue',
                    lw=0.8
                )
            )

        # Arrow from max to min
        plt.annotate(
            '',
            xy=(min_date, min_value),
            xytext=(max_date, max_value),
            arrowprops=dict(
                arrowstyle='->',
                color='black',
                lw=1
            )
        )

    dur_down = min_date.date() - max_date.date()

    if i > 0:
        dur_up = max_date.date() - prev_min_date.date()

        # Arrow from previous minimum to current maximum
        plt.annotate(
            '',
            xy=(max_date, max_value),
            xytext=(prev_min_date, prev_min),
            arrowprops=dict(
                arrowstyle='->',
                color='black',
                lw=1
            )
        )

        print(
            f"Between {start_date.date()} and {end_date.date()}: "
            f"Max Price = {max_value:>7.1f} on {max_date.date()} "
            f"Min Price = {min_value:>7.1f} on {min_date.date()} "
            f"down fac={max_value/min_value:.1f} "
            f"up fac={max_value/prev_min:>5.1f} "
            f"dur_down={dur_down.days} dur_up={dur_up.days}"
        )
    else:
        print(
            f"Between {start_date.date()} and {end_date.date()}: "
            f"Max Price = {max_value:>7.1f} on {max_date.date()} "
            f"Min Price = {min_value:>7.1f} on {min_date.date()} "
            f"down fac={max_value/min_value:5.1f} "
            f"dur_down={dur_down.days}"
        )

    prev_min = min_value
    prev_min_date = min_date

    if i == 3:
        max_date_pred = min_date + timedelta(days=1000)
        max_value_pred1 = min_value * 5
        max_value_pred2 = min_value * 8
        max_value_pred3 = min_value * 11

    if i == 4:
        min_date_pred = max_date + timedelta(days=340)
        min_value_pred1 = max_value / 2
        min_value_pred2 = max_value / 3
        min_value_pred3 = max_value / 4

    i += 1

plt.tight_layout()
plt.show(block=False)
plt.savefig('f_cycle_dates.pdf', bbox_inches='tight')






###############adding blocks number###############

# --- 1. Load your main df (already in your code) ---
# df is assumed to exist already with a DatetimeIndex


# --- 2. Load daily block numbers from CSV ---
csv_file = 'daily_block_heights.csv'

if not os.path.exists(csv_file):
    raise FileNotFoundError(f"{csv_file} not found.")

df_blocks = pd.read_csv(csv_file, parse_dates=['date'])
df_blocks.set_index('date', inplace=True)

# Detect which column is the block number
block_cols = [c for c in df_blocks.columns if 'block' in c.lower() or 'height' in c.lower()]
if not block_cols:
    raise ValueError("No column found in CSV that looks like block number.")
block_col = block_cols[0]
df_blocks['block_number'] = df_blocks[block_col].astype(int)

# --- 3. Reindex to cover all dates in df ---
full_index = pd.date_range(df.index.min(), df.index.max(), freq='D')
df_blocks = df_blocks.reindex(full_index)

# 1. Start by copying the original block column
df_blocks['block_number'] = df_blocks['block']

# 2. Identify where the NaNs start (at the end)
missing_mask = df_blocks['block'].isna()

if missing_mask.any():
    # 3. Find the last real block value and its position
    last_valid_idx = df_blocks['block'].last_valid_index()
    last_known_value = df_blocks.loc[last_valid_idx, 'block']

    # 4. Count how many missing rows there are at the end
    num_missing = missing_mask.sum()

    # 5. Create the increments: [144, 288, 432, ...]
    increments = [144 * i for i in range(1, num_missing + 1)]

    # 6. Apply them only to the missing rows
    df_blocks.loc[missing_mask, 'block_number'] = last_known_value + increments

# Ensure integer
df_blocks['block_number'] = df_blocks['block_number'].astype(int)

# --- 5. Merge into your main df ---
df = df.merge(df_blocks[['block_number']], left_index=True, right_index=True, how='left')

print(df.head())
print(df.tail())




blocks = df['block_number'].values
prices = df['Price'].values

# --- Determine halvings ---
halving_blocks = np.arange(210_000, blocks[-1] + 210_000, 210_000)
mid_blocks = halving_blocks - 105_000  # middle of each halving cycle

###################### diminishing return #######################
num_cycles = len(halving_blocks)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

# --------------------------------------------------
# FIGURE 1: Continuous Timeline
# --------------------------------------------------
fig1, ax1 = plt.subplots(figsize=(14, 7))

for i in range(num_cycles - 1):
    mid_start = halving_blocks[i] - 105_000
    mid_end = halving_blocks[i + 1] - 105_000

    mask = (blocks >= mid_start) & (blocks < mid_end)
    cycle_blocks = blocks[mask]
    cycle_prices = prices[mask]

    if len(cycle_prices) == 0:
        continue

    first_price = cycle_prices[0]
    if first_price == 0:
        non_zero = cycle_prices[cycle_prices > 0]
        first_price = non_zero[0] if len(non_zero) > 0 else 1

    pct_index = (cycle_prices / first_price) * 100

    ax1.plot(
        cycle_blocks,
        pct_index,
        label=f'Cyc {i + 1}',
        color=colors[i % len(colors)]
    )

# Formatting Figure 1
ax1.set_yscale('log')
ax1.set_ylim(10, 300000)
ax1.axhline(y=100, color='black', linestyle='-', alpha=0.7)
ax1.set_xlabel('Block Index')
ax1.set_ylabel('Price Index (Start = 100%)')
ax1.grid(True, which="both", linestyle='--', alpha=0.2)

# Mid-halving lines and labels
for idx, b in enumerate(halving_blocks):
    mid_halving_block = b - 105000

    ax1.axvline(
        x=mid_halving_block,
        color='yellow',
        linestyle='--',
        alpha=0.7,
        linewidth=1.5
    )

    ax1.annotate(
        f'Mid-Halving\n{mid_halving_block:,}',
        xy=(mid_halving_block, 150000),
        xytext=(0, 10),
        textcoords='offset points',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold',
        color='darkgoldenrod',
        bbox=dict(
            boxstyle='round,pad=0.2',
            facecolor='white',
            alpha=0.8,
            edgecolor='goldenrod'
        )
    )

plt.tight_layout()
plt.show(block=False)
fig1.savefig('f_dem1.pdf', bbox_inches='tight')
# --------------------------------------------------
# FIGURE 2: Overlap with Max / Min Timing
# --------------------------------------------------
fig2, ax2 = plt.subplots(figsize=(14, 7))

for i in range(num_cycles - 1):
    mid_start = halving_blocks[i] - 105_000
    mid_end = halving_blocks[i + 1] - 105_000

    mask = (blocks >= mid_start) & (blocks < mid_end)
    cycle_blocks = blocks[mask]
    cycle_prices = prices[mask]

    if len(cycle_prices) == 0:
        continue

    first_price = cycle_prices[0]
    if first_price == 0:
        non_zero = cycle_prices[cycle_prices > 0]
        first_price = non_zero[0] if len(non_zero) > 0 else 1

    pct_index = (cycle_prices / first_price) * 100
    relative_blocks = cycle_blocks - mid_start

    # Plot cycle
    ax2.plot(
        relative_blocks,
        pct_index,
        color=colors[i % len(colors)],
        alpha=0.6,
        linewidth=1.5
    )

    # --- Find Cycle Maximum ---
    max_idx = pct_index.argmax()
    max_val = pct_index[max_idx]
    max_x = relative_blocks[max_idx]

    ax2.scatter(max_x, max_val, color=colors[i % len(colors)], marker='x', s=100, zorder=5)
    ax2.axvline(x=max_x, color=colors[i % len(colors)], linestyle=':', linewidth=1, alpha=0.6)

    ax2.text(
        max_x,
        max_val * 1.05,
        f'Max {i + 1}',
        color=colors[i % len(colors)],
        fontsize=11,
        fontweight='bold',
        ha='center'
    )

    # --- Find Cycle Minimum ---
    min_idx = pct_index.argmin()
    min_val = pct_index[min_idx]
    min_x = relative_blocks[min_idx]

    ax2.scatter(min_x, min_val, color=colors[i % len(colors)], marker='x', s=100, zorder=5)
    ax2.axvline(x=min_x, color=colors[i % len(colors)], linestyle='--', linewidth=1, alpha=0.4)

    # Do not show Min 1
    if i > 0:
        if i == 2:
            ax2.annotate(
                f'Min {i + 1}',
                xy=(min_x, min_val),
                xytext=(min_x - 12000, min_val * 0.72),
                color=colors[i % len(colors)],
                fontsize=11,
                fontweight='bold',
                arrowprops=dict(
                    arrowstyle='->',
                    color=colors[i % len(colors)],
                    lw=1.2
                )
            )
        elif i == 3:
            ax2.annotate(
                f'Min {i + 1}',
                xy=(min_x, min_val),
                xytext=(min_x + 8000, min_val * 0.82),
                color=colors[i % len(colors)],
                fontsize=11,
                fontweight='bold',
                arrowprops=dict(
                    arrowstyle='->',
                    color=colors[i % len(colors)],
                    lw=1.2
                )
            )
        else:
            ax2.text(
                min_x,
                min_val * 0.90,
                f'Min {i + 1}',
                color=colors[i % len(colors)],
                fontsize=11,
                fontweight='bold',
                ha='center',
                va='top'
            )

# Formatting Figure 2
ax2.set_yscale('log')
ax2.set_xlim(0, 210000)
ax2.axhline(y=100, color='black', linestyle='-', alpha=0.7)
ax2.axvline(x=105000, color='grey', linestyle='-', alpha=0.8, label='Halving Event')
ax2.set_xlabel('Blocks Since Mid-Halving Start')
ax2.set_ylabel('Price Index (Start = 100%)')
ax2.set_title('Cycle Overlap: Timing of Max/Min (Vertical Lines)')
ax2.grid(True, which="both", linestyle='--', alpha=0.2)

plt.tight_layout()
plt.show(block=False)
fig2.savefig('f_dem2.pdf', bbox_inches='tight')
###############Hotmap - cycle evidence #######################################


# -----------------------------
# Parameters
# -----------------------------
BLOCKS_PER_CYCLE = 210_000
configs = [8]  # Number of columns to generate

# -----------------------------
# Prepare Data
# -----------------------------
df = df.copy().sort_values("block_number")
df["cycle"] = df["block_number"] // BLOCKS_PER_CYCLE
df["block_in_cycle"] = df["block_number"] % BLOCKS_PER_CYCLE
current_block_val = df["block_in_cycle"].iloc[-1]

# Remove cycle 0
df = df[df["cycle"] > 0].copy()

# Custom Colormap with a wider pure-white zone around 0
custom_rdylgn = mcolors.LinearSegmentedColormap.from_list(
    "",
    [
        (0.00, "#d73027"),   # strong red
        (0.49, "#f4cccc"),   # light red
        (0.498, "#fff5f5"),  # very pale red
        (0.498, "#ffffff"),  # start white zone
        (0.502, "#ffffff"),  # end white zone
        (0.502, "#f2fff2"),  # very pale green
        (0.51, "#d9ead3"),   # light green
        (1.00, "#1a9850")    # strong green
    ]
)

# -----------------------------
# Loop to generate both Heatmaps
# -----------------------------
for segments in configs:
    blocks_per_seg = BLOCKS_PER_CYCLE // segments

    # 1. Calculate Segments & Returns
    df_temp = df.copy()
    df_temp["segment"] = (
        df_temp["block_in_cycle"] // blocks_per_seg
    ).clip(upper=segments - 1)

    returns = df_temp.groupby(["cycle", "segment"]).agg(
        first_price=("Price", "first"),
        last_price=("Price", "last")
    )
    returns["yield_pct"] = (
        (returns["last_price"] / returns["first_price"] - 1) * 100
    )

    # 2. Pivot Table
    table = returns["yield_pct"].unstack("segment").fillna(0)
    table.columns = [f"S{i + 1}" for i in range(segments)]

    # 3. Dynamic Labels
    cycle_labels = []
    for cyc in table.index:
        start_b = cyc * BLOCKS_PER_CYCLE

        if cyc == df_temp["cycle"].max():
            end_b = df_temp[df_temp["cycle"] == cyc]["block_number"].max()
        else:
            end_b = (cyc + 1) * BLOCKS_PER_CYCLE - 1

        cycle_labels.append(
            f"Cycle {cyc} ({start_b // 1000}K–{end_b // 1000}K)"
        )

    table.index = cycle_labels

    # Create annotation labels with + sign for positive values
    func = lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}"

    if hasattr(table, "map"):  # new pandas
        annot_labels = table.copy().map(func)
    else:  # old pandas
        annot_labels = table.copy().applymap(func)

    # 4. Plotting
    plt.figure(figsize=(16, 6))
    ax = sns.heatmap(
        table,
        annot=annot_labels,
        fmt="",
        cmap=custom_rdylgn,
        center=0,
        vmin=-100,
        vmax=100,
        linewidths=0.7,
        linecolor="white"
    )

    # 5. Precise Pointer (Arrow + Block Number)
    exact_x_pos = current_block_val / blocks_per_seg
    num_rows = len(table)

    # Mini Arrow pointing at X-axis
    ax.annotate(
        '',
        xy=(exact_x_pos, num_rows),
        xytext=(exact_x_pos, num_rows - 0.12),
        arrowprops=dict(
            arrowstyle="->,head_width=0.2,head_length=0.3",
            color="black",
            lw=1.5
        )
    )

    # Block number text right near arrow
    ax.text(
        exact_x_pos,
        num_rows - 0.15,
        f"{current_block_val:,}",
        ha='center',
        va='bottom',
        fontsize=8,
        fontweight='bold',
        bbox=dict(
            facecolor='white',
            alpha=0.7,
            edgecolor='none',
            pad=0.05
        )
    )

    # plt.title(
    #     f"Bitcoin Cycle Returns - {segments} Segments\n"
    #     f"Progress: Block {current_block_val:,}",
    #     fontsize=14,
    #     fontweight='bold'
    # )
    plt.xlabel(f"Segments ({blocks_per_seg:,} blocks each)", fontsize=10)
    plt.ylabel("Cycle Range")
    plt.tight_layout()
    plt.show(block=False)

plt.savefig('f_seg.pdf', bbox_inches='tight')


print("\nAll figures generated.")
print("Press SPACE in any figure window to close all figures.")

# def close_all(event):
#     if event.key == ' ':
#         plt.close('all')
#
# for num in plt.get_fignums():
#     fig = plt.figure(num)
#     fig.canvas.mpl_connect('key_press_event', close_all)

# KEEP PYTHON ALIVE until space closes all figures
# while plt.get_fignums():
#     plt.pause(0.1)

#######################PREDICTION########################################

# ####################CYCLE ################
# plt.figure()
# ax=df['Price'].plot(logy=True)
# #plt.legend(loc='upper left', labels=['Price'])
# plt.ylabel('USD')
# ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
# plt.grid(True)
# #plt.title('Daily Price')
# x_limit = datetime(2028, 6, 1)
# plt.xlim(df.index[0], x_limit)
# mark_bitcoin_halvings(ax, bitcoin_halving_dates)
#
#
# i = 0
#
# for start_date, end_date, max_date, max_value, max_date, max_value in max_values_for_halving_periods:
#
#     subset = df[(df.index >= max_date) & (df.index <= end_date)]
#
#     # Skip empty subsets
#     if subset.empty or subset['Price'].dropna().empty:
#         print(f"Skipping empty subset between {max_date} and {end_date}")
#         i += 1
#         continue
#
#     min_value = subset['Price'].min()
#     min_date = subset['Price'].idxmin()
#
#     # Plot maximum points
#     plt.scatter(max_date, max_value, c='red', marker='o', label='Max Points')
#
#     if i < 4:
#         # Plot minimum points
#         plt.scatter(min_date, min_value, c='blue', marker='x', label='Min Points')
#
#         plt.annotate(
#             '',
#             xy=(min_date, min_value),
#             xytext=(max_date, max_value),
#             arrowprops=dict(arrowstyle='->', color='black')
#         )
#
#     dur_down = min_date.date() - max_date.date()
#
#     if i > 0:
#         dur_up = max_date.date() - prev_min_date.date()
#
#         plt.annotate(
#             '',
#             xy=(max_date, max_value),
#             xytext=(prev_min_date, prev_min),
#             arrowprops=dict(arrowstyle='->', color='black')
#         )
#
#         print(
#             f"Between {start_date.date()} and {end_date.date()}: "
#             f"W Max Price = {max_value:>7.1f} on {max_date.date()} "
#             f"week Min Price = {min_value:>7.1f} on {min_date.date()} "
#             f"down fac={max_value/min_value:.1f} "
#             f"up fac={max_value/prev_min:>5.1f} "
#             f"dur_down={dur_down.days} dur_up={dur_up.days}"
#         )
#     else:
#         print(
#             f"Between {start_date.date()} and {end_date.date()}: "
#             f"W Max Price = {max_value:>7.1f} on {max_date.date()} "
#             f"week Min Price = {min_value:>7.1f} on {min_date.date()} "
#             f"down fac={max_value/min_value:5.1f} "
#             f"dur_down={dur_down.days}"
#         )
#
#     prev_min = min_value
#     prev_min_date = min_date
#
#     if i == 3:
#         max_date_pred = min_date + timedelta(days=1000)  # last two duration were 1067 and 1059
#         max_value_pred1 = min_value * 5
#         max_value_pred2 = min_value * 8
#         max_value_pred3 = min_value * 11
#
#     if i == 4:
#         min_date_pred = max_date + timedelta(days=340)  # last three duration were 404,364,378
#         min_value_pred1 = max_value / 2
#         min_value_pred2 = max_value / 3
#         min_value_pred3 = max_value / 4
#
#     i += 1
#
#
# plt.show(block=False)
# plt.savefig('f_cycle.pdf', bbox_inches='tight')
#
#




#
#
# ###########################Prediction%%%
# ####################################
# ax=df['Price'].plot(logy=True)
# plt.legend(loc='upper left', labels=['Price'])
# ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
# plt.grid(True)
# plt.title('Daily Price')
# x_limit = datetime(2028, 6, 1)
# plt.xlim(df.index[0], x_limit)
# mark_bitcoin_halvings(ax, bitcoin_halving_dates)
#
# i=0;
# for start_date, end_date, max_date, max_value,  max_date, max_value in max_values_for_halving_periods:
#     subset = df[(df.index >= max_date) & (df.index <= end_date)]
#     min_value = subset['Price'].min()
#     min_date = subset.loc[subset['Price'].idxmin()].name
#     #daily Maximum Price = {max_value:.1f}
#     # Plot maximum points
#     plt.scatter(max_date, max_value, c='red', marker='o', label='Max Points')
#
#     if i<4:
#         # Plot minimum points
#         plt.scatter(min_date, min_value, c='blue', marker='x', label='Min Points')
# #        plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
# #                     arrowprops=dict(arrowstyle='->', color='black'))
#         #
#         plt.annotate('', xy=(min_date, min_value), xytext=(max_date, max_value),
#                  arrowprops=dict(arrowstyle='->', color='black'))
#         #plt.text(min_date, min_value,f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}% / y",
#         #        ha='left', va='bottom')
#         plt.text(min_date, min_value*0.8,
#                  f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}%{'/year' if i == 0 else '/y'}",
#                  ha='left', va='bottom')
#
#     dur_down = min_date.date() - max_date.date()
#
#     if i>0 :
#         dur_up=max_date.date()-prev_min_date.date()
#         plt.annotate('', xy=(max_date, max_value), xytext=(prev_min_date,  prev_min),
#                      arrowprops=dict(arrowstyle='->', color='black'))
#         plt.text(max_date, max_value, f"{((max_value/prev_min)**(1/((max_date-prev_min_date).days/365.25))-1)*100:.1f}%{'/year' if i==1 else '/y'}", ha='left', va='bottom')
#         print(f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:.1f} up fac={max_value/prev_min:>5.1f} dur_down={dur_down.days} dur_up={dur_up.days}")
#     else:
#         print(
#             f"Between {start_date.date()} and {end_date.date()}: W Max Price = {max_value:>7.1f}  on {max_date.date()} week Min Price = {min_value:>7.1f} on {min_date.date()} down fac={max_value/min_value:5.1f} dur_down={dur_down.days}")
#
#     prev_min=min_value
#     prev_min_date=min_date
#
#
#     if i==3:
#         max_date_pred=min_date+ + timedelta(days=1000) #last two duration were 1067 and 1059 hence I took 1000
#         max_value_pred1=min_value*5
#         max_value_pred2=min_value*8
#         max_value_pred3=min_value*11
#
# #        plt.scatter(max_date_pred, max_value_pred1, c='green', marker='o', label='Max Points')
#         plt.scatter(max_date_pred, max_value_pred1, facecolors='none', edgecolor='green', marker='o',
#                     label='Max Points')
#         plt.text(max_date_pred, max_value_pred1*0.65,
#                  f"{((max_value_pred1 / prev_min) ** (1 / ((max_date_pred - prev_min_date).days / 365.25)) - 1) * 100:.0f}%",
#                  ha='left', va='bottom')
#
#         plt.scatter(max_date_pred, max_value_pred2, facecolors='none', edgecolor='green', marker='o',
#                     label='Max Points')
#         plt.text(max_date_pred- timedelta(days=100), max_value_pred2 * 1,
#                  f"{((max_value_pred2 / prev_min) ** (1 / ((max_date_pred - prev_min_date).days / 365.25)) - 1) * 100:.0f}%",
#                  ha='left', va='bottom')
#         plt.scatter(max_date_pred, max_value_pred3, facecolors='none', edgecolor='green', marker='o',
#                     label='Max Points')
#         plt.text(max_date_pred, max_value_pred3 * 1.20,
#                  f"{((max_value_pred3 / prev_min) ** (1 / ((max_date_pred - prev_min_date).days / 365.25)) - 1) * 100:.0f}%",
#                  ha='left', va='bottom')
#         plt.annotate('', xy=(min_date, min_value), xytext=(max_date_pred, max_value_pred1),
#                      arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
#         plt.annotate('', xy=(min_date, min_value), xytext=(max_date_pred, max_value_pred2),
#                      arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
#         plt.annotate('', xy=(min_date, min_value), xytext=(max_date_pred, max_value_pred3),
#                      arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
#
#         print(f"Prediction {end_date.date()} and {end_date.date()+timedelta(days=4*365)}: W Max Price = {max_value_pred2:>7.1f}  on {max_date_pred.date()} week Min Price = xxxxx up fac=8")
#
#
#     if i==4:
#         min_date_pred=max_date+ + timedelta(days=340) #last three duration were 404,364,378 - I take less than a year: 340
#         min_value_pred1=max_value/2
#         min_value_pred2=max_value/3
#         min_value_pred3=max_value/4
#
#         plt.scatter(min_date_pred, min_value_pred1, facecolors='none', edgecolor='green', marker='o', label='Min Points')
#         plt.scatter(min_date_pred, min_value_pred2, facecolors='none', edgecolor='green', marker='o', label='Min Points')
#         plt.scatter(min_date_pred, min_value_pred3, facecolors='none', edgecolor='green', marker='o', label='Min Points')
#         plt.annotate('', xy=(min_date_pred, min_value_pred1), xytext=(max_date, max_value),
#                      arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
#         plt.text(min_date_pred, min_value_pred1 * 1,
#                  f"{((min_value_pred1 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%",
#                  ha='left', va='bottom')
#         plt.annotate('', xy=(min_date_pred, min_value_pred2), xytext=(max_date, max_value),
#                  arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
#         plt.text(min_date_pred, min_value_pred2 * .9,
#                  f"{((min_value_pred2 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%",
#                  ha='left', va='bottom')
#         plt.annotate('', xy=(min_date_pred, min_value_pred3), xytext=(max_date, max_value),
#                  arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
#         plt.text(min_date_pred, min_value_pred3 * .75,
#                  f"{((min_value_pred3 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%",
#                  ha='left', va='bottom')
#
# #        print(f"Prediction {end_date.date()} and {end_date.date()+timedelta(days=4*365)}: W Max Price = {max_value_pred2:>7.1f}  on {max_date_pred.date()} week Min Price pred = {min_value_pred2:>7.1f} up fac=8")
#
#
#
#     i=i+1
# plt.show(block=False)
#
#
#


























###################### POWER LAW MODEL #######################

#from matplotlib.ticker import ScalarFormatter
#from sklearn.linear_model import LinearRegression
# -----------------------------
# Prepare Data
# -----------------------------
df_power = df.copy()

# Remove zero prices
df_power = df_power[df_power["Price"] > 0].copy()

# Days since Bitcoin genesis block (2009-01-03)
genesis_date = pd.Timestamp("2009-01-03")
df_power["days_since_genesis"] = (df_power.index - genesis_date).days

# Remove very early days to avoid log(0)
df_power = df_power[df_power["days_since_genesis"] > 0].copy()

# Use only data from mid 2012 onward
plot_start = pd.Timestamp("2012-06-01")
plot_end = pd.Timestamp("2032-12-31")

df_power = df_power[df_power.index >= plot_start].copy()

# Log transform
X = np.log10(df_power["days_since_genesis"].values)
y = np.log10(df_power["Price"].values)

# -----------------------------
# Fit Power Law (NO SKLEARN)
# -----------------------------
slope, intercept = np.polyfit(X, y, 1)

# -----------------------------
# Create Future Timeline to 2032
# -----------------------------
future_dates = pd.date_range(start=plot_start, end=plot_end, freq="D")

future_days = (future_dates - genesis_date).days.values
future_days_log = np.log10(future_days)

future_powerlaw = 10 ** (slope * future_days_log + intercept)

# Bands
upper_band = future_powerlaw * 2
lower_band = future_powerlaw / 2

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(13, 8))

# Actual Bitcoin price
plt.plot(
    df_power.index,
    df_power["Price"],
    label="Bitcoin Price",
    linewidth=2
)

# Power law model
plt.plot(
    future_dates,
    future_powerlaw,
    linestyle="--",
    linewidth=2,
    label="Power Law Fit"
)

# Bands
plt.plot(
    future_dates,
    upper_band,
    linestyle=":",
    linewidth=1.5,
    alpha=0.8,
    label="Upper Band"
)

plt.plot(
    future_dates,
    lower_band,
    linestyle=":",
    linewidth=1.5,
    alpha=0.8,
    label="Lower Band"
)

plt.yscale("log")
plt.xlim(plot_start, plot_end)
plt.ylim(1, 1_000_000)

plt.ylabel("Bitcoin Price (USD)")
plt.xlabel("Date")
# plt.title("Bitcoin Power Law Model")
plt.grid(True, which="both", linestyle="--", alpha=0.3)
plt.legend()

# Show fitted equation
plt.text(
    0.02,
    0.05,
    f"log10(Price) = {slope:.2f} log10(Days) + {intercept:.2f}",
    transform=plt.gca().transAxes,
    fontsize=10,
    bbox=dict(facecolor='white', alpha=0.8)
)

plt.tight_layout()

# Save BEFORE show
plt.savefig('f_powerlaw.pdf', bbox_inches='tight')

plt.show(block=False)
###################### PLANB STOCK-TO-FLOW HORIZONTAL LEVELS #######################

# -----------------------------
# Prepare Data
# -----------------------------
df_s2f = df.copy()
df_s2f = df_s2f[df_s2f["Price"] > 0].copy()

plot_start = pd.Timestamp("2011-06-01")
plot_end = pd.Timestamp("2028-12-31")

df_s2f = df_s2f[df_s2f.index >= plot_start].copy()

# -----------------------------
# Use Existing Halving Dates
# -----------------------------
halving_dates = [datetime(2009, 1, 3)] + bitcoin_halving_dates

# -----------------------------
# Approximate PlanB S2F Levels
# -----------------------------
s2f_levels = [
    6,          # pre 2012
    100,        # 2012-2016
    6000,       # 2016-2020
    55000,      # 2020-2024
    480000,     # 2024-2028
    4000000     # after 2028
]

# -----------------------------
# Build Staircase Series
# -----------------------------
s2f_dates = []
s2f_values = []

for i in range(len(halving_dates) - 1):
    s2f_dates.extend([
        halving_dates[i],
        halving_dates[i + 1]
    ])
    s2f_values.extend([
        s2f_levels[i],
        s2f_levels[i]
    ])

# Extend final level to end of plot
s2f_dates.extend([
    halving_dates[-1],
    plot_end
])

s2f_values.extend([
    s2f_levels[-1],
    s2f_levels[-1]
])

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(13, 8))

# Bitcoin price
plt.plot(
    df_s2f.index,
    df_s2f["Price"],
    linewidth=2,
    color='blue',
    label="BTC Price"
)

# PlanB S2F staircase
plt.plot(
    s2f_dates,
    s2f_values,
    color='orange',
    linestyle='--',
    linewidth=3,
    label="S2F Model"
)

# Vertical lines at halvings
for i, h in enumerate(halving_dates[1:-1]):
    plt.axvline(
        h,
        color='gray',
        linestyle=':',
        alpha=0.4,
        label='Halving Date' if i == 0 else None
    )

plt.yscale("log")
plt.xlim(plot_start, plot_end)
plt.ylim(1, 10_000_000)

plt.ylabel("Bitcoin Price (USD)")
plt.xlabel("Date")
plt.title("PlanB Stock-to-Flow (S2F)")
plt.grid(True, which="both", linestyle="--", alpha=0.3)

plt.legend(loc='upper left')

plt.tight_layout()

plt.savefig('f_s2f.pdf', bbox_inches='tight')

plt.show(block=False)




#exit()






















#draw precentage of fees from the total cost


print(df)
df['MA_per'] = df['percentage_fees'].rolling(window=365).mean()


fig, ax1 = plt.subplots()

# Plot the "Price" column on a semilog y-axis
ax1.set_yscale('log')
ax1.set_ylabel('Price (log scale)', color='tab:blue')
ax1.plot(df.index, df['Price'], color='tab:blue', label='Price')
ax1.tick_params(axis='y', labelcolor='tab:blue')

# Create a second y-axis for "Mining cost"
ax2 = ax1.twinx()

# Plot the "Mining cost" column on a linear y-axis
ax2.set_yscale('linear')
ax2.set_ylabel('percentage_fees', color='tab:red')
ax2.plot(df.index, df['percentage_fees'], color='tab:red', label='percentage cost of fees')
ax2.tick_params(axis='y', labelcolor='tab:red')
ax2.plot(df.index, df['MA_per'], color='green', label='MA per 365 days')

# Add a legend
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="upper left")
# Set the y-axis limits for "Mining cost" between 1 and 30
ax2.set_ylim(0, 70)

# Add a title
plt.title('Bitcoin Price and percentage cost of fees')

mark_bitcoin_halvings(ax1, bitcoin_halving_dates)
plt.grid(True)




# Show the plot
plt.show(block=False)


####Adding MA 200 and mulitlies of it

df['price_MA_200'] = df['Price'].rolling(window=200*7).mean()
fig, ax1 = plt.subplots()

# Plot the "Price" column on a semilog y-axis
ax1.set_yscale('log')
ax1.set_ylabel('Price (log scale)', color='tab:blue')
ax1.plot(df.index, df['Price'], color='tab:blue', label='Price')
ax1.plot(df.index, df['price_MA_200'], color='yellow', alpha=1, label='MA_200')
ax1.plot(df.index, 2*df['price_MA_200'], color='yellow', alpha=0.6, label='2* MA_200 weeks')
ax1.plot(df.index, 3*df['price_MA_200'], color='yellow', alpha=0.6, label='3* MA_200')
ax1.plot(df.index, 4*df['price_MA_200'], color='yellow', alpha=0.6, label='4* MA_200')
ax1.plot(df.index, 5*df['price_MA_200'], color='yellow', alpha=0.8, label='5* MA_200')
ax1.plot(df.index, 7*df['price_MA_200'], color='yellow', alpha=1, label='7* MA_200')
ax1.legend()
mark_bitcoin_halvings(ax1, bitcoin_halving_dates)
plt.grid(True)

#--------------------------------------
# Add horizontal lines from max values - 1300 days to the right
for i, (start_date, end_date, max_date, max_value, max_date_daily, max_value_daily) in enumerate(
        max_values_for_halving_periods):
    # Calculate end date (1300 days after max_date)
    line_end_date = max_date + pd.Timedelta(days=1460) #4 years

    # Draw horizontal line
    ax1.hlines(y=max_value,
               xmin=max_date,
               xmax=line_end_date,
               colors='green',
               linestyles='dotted',
               alpha=0.7,
               linewidth=2)
#--------------------------------------
plt.show(block=False)





def plot_dual_axis(df, y1_col, y2_col, y1_label, y2_label, title, bitcoin_halving_dates, ordinal_date, china_ban_date, idx2_log_flag=True):
    fig, ax1 = plt.subplots()

    # Plot the first column on a semilog y-axis
    ax1.set_yscale('log')
    ax1.set_ylabel(y1_label, color='tab:blue')
    ax1.plot(df.index, df[y1_col], color='tab:blue', label=y1_label)
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Create a second y-axis for the second column
    ax2 = ax1.twinx()

    # Plot the second column on a linear y-axis
    if idx2_log_flag:
        ax2.set_yscale('log')
    else:
        ax2.set_yscale('linear')

    ax2.set_ylabel(y2_label, color='tab:red')
    ax2.plot(df.index, df[y2_col], color='tab:red', label=y2_label)
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Add legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    # Add title
    plt.title(title)

    # Add vertical lines for bitcoin halving dates
    mark_bitcoin_halvings(ax1, bitcoin_halving_dates)
    # Add vertical lines for other important dates
    plt.axvline(ordinal_date, color='blue', linestyle='--', alpha=0.6, label='Ordinal')
    plt.axvline(ETF_date, color='blue', linestyle='--', alpha=0.6, label='ETF')
    plt.text(ETF_date, ax2.get_ylim()[0], f' ETF', rotation=90, ha='right', va='bottom')
    plt.axvline(GOX_dist_date, color='blue', linestyle='--', alpha=0.6, label='GOX_dist')
    plt.text(GOX_dist_date, ax2.get_ylim()[0], f' GOX_dist', rotation=90, ha='right', va='bottom')
    plt.axvline(Trump_won_date, color='blue', linestyle='--', alpha=0.6, label='Trump')
    plt.text(Trump_won_date, ax2.get_ylim()[0], f' Trump', rotation=90, ha='right', va='bottom')

    plt.axvline(GOX_collapse_date, color='blue', linestyle='--', alpha=0.6, label='GOX_collapse')
    plt.text(GOX_collapse_date, ax2.get_ylim()[0], f' GOX_collapse', rotation=90, ha='right', va='bottom')
    plt.axvline(Cyprus_haircut_date, color='blue', linestyle='--', alpha=0.6, label='Cyprus_haircut')
    plt.text(Cyprus_haircut_date, ax2.get_ylim()[0], f' Cyprus_haircut', rotation=90, ha='right', va='bottom')

    plt.axvline(china_ban_date, color='red', linestyle='-.', alpha=0.6, label='China Ban')
    plt.text(ordinal_date, ax2.get_ylim()[0], f' Ordinal', rotation=90, ha='right', va='bottom')
    plt.text(china_ban_date, ax2.get_ylim()[0], f' china ban', rotation=90, ha='right', va='bottom')

    # Show the plot
    plt.grid(True)
    plt.show()


# Call the function for each dataset
#plot_dual_axis(df, y1_col, y2_col,               y1_label,       y2_label,   title, bitcoin_halving_dates, ordinal_date, china_ban_date, idx2_log_flag=True):
plot_dual_axis(df, 'Price', 'miners_revenue',        'BTC Price ', 'miners_revenue (USD probably per day)', 'Miners revenue:revenue earned by miners on the Bitcoin network block rewards and transaction fees', bitcoin_halving_dates, ordinal_date, china_ban_date)
if show_all:
    plot_dual_axis(df, 'Price', 'hashrate',           'BTC Price ', 'hashrate', 'Hashrate', bitcoin_halving_dates, ordinal_date, china_ban_date)
    plot_dual_axis(df, 'Price', 'transaction_volume', 'BTC Price ', 'Transaction Volume ', 'Transaction Volume ( transactions recorded on the blockchain)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'transactions_per_day', 'BTC Price ', 'Transactions Per Day)', 'Transactions Per Day(number of transactions recorded on the blockchai)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'mempool_size',        'BTC Price ', 'Mempool Size ', 'Mempool Size (waiting area for transactions)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'trade_volume',        'BTC Price ', 'Trade Volume', 'Trade Volume ( trading activity that occurs on exchanges)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'blocks_size',        'BTC Price ', 'Blocks Size', 'Bitcoin Price and Blocks Size', bitcoin_halving_dates, ordinal_date, china_ban_date)
    plot_dual_axis(df, 'Price', 'cost_per_transaction',        'BTC Price ', 'cost_per_transaction ', 'cost_per_transaction (USD)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    # plot_dual_axis(df, 'Price', 'transaction_rate',        'BTC Price ', 'transaction_rate', 'transaction_rate ( number of transactions processed per second TPS)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'Bitcoin_network_difficulty',        'BTC Price ', 'Bitcoin_network_difficulty', 'Bitcoin_network_difficulty', bitcoin_halving_dates, ordinal_date, china_ban_date)
    plot_dual_axis(df, 'Price', 'avg_confirmation_time',        'BTC Price ', 'avg_confirmation_time', 'avg_confirmation_time', bitcoin_halving_dates, ordinal_date, china_ban_date, False)




#drawing with respect to block
#import matplotlib.pyplot as plt
#import numpy as np

# --- Prepare data ---

# --- Plot ---
plt.figure(figsize=(14,7))
plt.plot(blocks, prices, label='Price', color='blue')
plt.yscale('log')
plt.xlabel('Block Number')
plt.ylabel('Price (USD)')
plt.title('Bitcoin Price vs Block Number (Log Scale)')

# --- Draw vertical lines ---
for hb in halving_blocks:
    plt.axvline(x=hb, color='red', linestyle='--')

for mb in mid_blocks:
    plt.axvline(x=mb, color='yellow', linestyle='--')

# --- Set x-axis ticks only at yellow lines and last block ---
x_ticks = list(mid_blocks) + [blocks[-1]]
plt.xticks(x_ticks, [f"{int(x):,}" for x in x_ticks], rotation=45)

plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show(block=False)
# ########the cycles overlap
# # --- New figure: percentage change from first block of each halving cycle ---
# # --- New figure: percentage change from first block of each halving cycle (log scale) ---
# plt.figure(figsize=(14, 7))
#
# num_cycles = len(halving_blocks)
# for i in range(1, num_cycles):
#     start_block = halving_blocks[i - 1]
#     end_block = halving_blocks[i] if i < num_cycles else blocks[-1]
#
#     # Mask the blocks for this cycle
#     mask = (blocks >= start_block) & (blocks < end_block)
#     cycle_blocks = blocks[mask]
#     cycle_prices = prices[mask]
#
#     # Percentage change from the first point of this cycle
#     pct_change = (cycle_prices - cycle_prices[0]) / cycle_prices[0] * 100
#
#     plt.plot(cycle_blocks, pct_change, label=f'Cyc {i + 1}')
#
# plt.xlabel('Block Number')
# plt.ylabel('Percentage Change from First Block of Cycle')
# plt.title('Bitcoin Halving Cycles Percentage Change (Log Scale)')
# plt.yscale('symlog', linthresh=1)  # Handles negative and small values
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend()
# plt.tight_layout()
# plt.show()












