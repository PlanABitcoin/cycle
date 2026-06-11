import pandas as pd

import matplotlib
matplotlib.use('TkAgg')   # or 'QtAgg'

import matplotlib.pyplot as plt
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors



from matplotlib.ticker import ScalarFormatter
from datetime import datetime
import seaborn as sns
import numpy as np
show_all=False
#show_all=True
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




# URLs
urls_base = [
    (
    'https://api.blockchain.info/charts/market-price?timespan=18years&rollingAverage=24hours&start=2010-01-01&format=json&sampled=false',
    'Price'),
    (
    'https://api.blockchain.info/charts/transaction-fees?timespan=18years&rollingAverage=24hours&start=2010-01-01&format=json&sampled=false',
    'fees'),
    ('https://api.blockchain.info/charts/hash-rate?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'hashrate'),
    ('https://api.blockchain.info/charts/miners-revenue?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'miners_revenue'
     ),
    (
    'https://api.blockchain.info/charts/cost-per-transaction?timespan=18years&start=2010-01-01&format=json&sampled=false',
    'cost_per_transaction'
    ),
    ('https://api.blockchain.info/charts/difficulty?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'Bitcoin_network_difficulty'),

    #('https://api.blockchain.info/charts/trade-volume?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #  'trade_volume'),
    # ('https://api.blockchain.info/charts/blocks-size?timespan=18years&start=2010-01-01&format=json&sampled=false',
    #  'blocks_size'),
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


urls_extra = [
    (
        'https://api.blockchain.info/charts/estimated-transaction-volume-usd?timespan=18years&start=2010-01-01&format=json&sampled=false',
        'transaction_volume'),
    ('https://api.blockchain.info/charts/n-transactions?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'transactions_per_day'),
    ('https://api.blockchain.info/charts/mempool-size?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'mempool_size'),
    ('https://api.blockchain.info/charts/trade-volume?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'trade_volume'),
    ('https://api.blockchain.info/charts/blocks-size?timespan=18years&start=2010-01-01&format=json&sampled=false',
     'blocks_size'),
    ('https://api.blockchain.info/charts/avg-confirmation-time?timespan=18years&start=2010-01-01&format=json&sampled=false',
        'avg_confirmation_time'),
 #   ('https://api.blockchain.info/charts/transaction-rate?timespan=18years&start=2010-01-01&format=json&sampled=false',
 #       'transaction_rate'
 #   )
]



urls = urls_base + urls_extra if show_all else urls_base






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

# Print the maximum value and the date it happens for each halving period
####################################
ax=df['Price'].plot(logy=True)
plt.legend(loc='upper left', labels=['Price'])
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
plt.grid(True)
plt.title('Daily Price')
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
        plt.text(min_date, min_value*0.8,
                 f"{((min_value / max_value) ** (1 / ((min_date - max_date).days / 365.25)) - 1) * 100:.1f}%{'/year' if i == 0 else '/y'}",
                 ha='left', va='bottom')

    dur_down = min_date.date() - max_date.date()

    if i>0 :
        dur_up=max_date.date()-prev_min_date.date()
        plt.annotate('', xy=(max_date, max_value), xytext=(prev_min_date,  prev_min),
                     arrowprops=dict(arrowstyle='->', color='black'))
        plt.text(max_date, max_value, f"{((max_value/prev_min)**(1/((max_date-prev_min_date).days/365.25))-1)*100:.1f}%{'/year' if i==1 else '/y'}", ha='left', va='bottom')
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

#        plt.scatter(max_date_pred, max_value_pred1, c='green', marker='o', label='Max Points')
        plt.scatter(max_date_pred, max_value_pred1, facecolors='none', edgecolor='green', marker='o',
                    label='Max Points')
        plt.text(max_date_pred, max_value_pred1*0.65,
                 f"{((max_value_pred1 / prev_min) ** (1 / ((max_date_pred - prev_min_date).days / 365.25)) - 1) * 100:.0f}%",
                 ha='left', va='bottom')

        plt.scatter(max_date_pred, max_value_pred2, facecolors='none', edgecolor='green', marker='o',
                    label='Max Points')
        plt.text(max_date_pred- timedelta(days=100), max_value_pred2 * 1,
                 f"{((max_value_pred2 / prev_min) ** (1 / ((max_date_pred - prev_min_date).days / 365.25)) - 1) * 100:.0f}%",
                 ha='left', va='bottom')
        plt.scatter(max_date_pred, max_value_pred3, facecolors='none', edgecolor='green', marker='o',
                    label='Max Points')
        plt.text(max_date_pred, max_value_pred3 * 1.20,
                 f"{((max_value_pred3 / prev_min) ** (1 / ((max_date_pred - prev_min_date).days / 365.25)) - 1) * 100:.0f}%",
                 ha='left', va='bottom')
        plt.annotate('', xy=(min_date, min_value), xytext=(max_date_pred, max_value_pred1),
                     arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.annotate('', xy=(min_date, min_value), xytext=(max_date_pred, max_value_pred2),
                     arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.annotate('', xy=(min_date, min_value), xytext=(max_date_pred, max_value_pred3),
                     arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))

        print(f"Prediction {end_date.date()} and {end_date.date()+timedelta(days=4*365)}: W Max Price = {max_value_pred2:>7.1f}  on {max_date_pred.date()} week Min Price = xxxxx up fac=8")


    if i==4:
        min_date_pred=max_date+ + timedelta(days=340) #last three duration were 404,364,378 - I take less than a year: 340
        min_value_pred1=max_value/2
        min_value_pred2=max_value/3
        min_value_pred3=max_value/4

        plt.scatter(min_date_pred, min_value_pred1, facecolors='none', edgecolor='green', marker='o', label='Min Points')
        plt.scatter(min_date_pred, min_value_pred2, facecolors='none', edgecolor='green', marker='o', label='Min Points')
        plt.scatter(min_date_pred, min_value_pred3, facecolors='none', edgecolor='green', marker='o', label='Min Points')
        plt.annotate('', xy=(min_date_pred, min_value_pred1), xytext=(max_date, max_value),
                     arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.text(min_date_pred, min_value_pred1 * 1,
                 f"{((min_value_pred1 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%",
                 ha='left', va='bottom')
        plt.annotate('', xy=(min_date_pred, min_value_pred2), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.text(min_date_pred, min_value_pred2 * .9,
                 f"{((min_value_pred2 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%",
                 ha='left', va='bottom')
        plt.annotate('', xy=(min_date_pred, min_value_pred3), xytext=(max_date, max_value),
                 arrowprops=dict(arrowstyle='-', color='black', linestyle='dotted'))
        plt.text(min_date_pred, min_value_pred3 * .75,
                 f"{((min_value_pred3 / max_value) ** (1 / ((min_date_pred - max_date).days / 365.25)) - 1) * 100:.0f}%",
                 ha='left', va='bottom')

#        print(f"Prediction {end_date.date()} and {end_date.date()+timedelta(days=4*365)}: W Max Price = {max_value_pred2:>7.1f}  on {max_date_pred.date()} week Min Price pred = {min_value_pred2:>7.1f} up fac=8")



    i=i+1
plt.show(block=False)


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
ax2.plot(df.index, df['total_cost'], color='tab:red', label='Mining total cost (fee+reward)')
ax2.tick_params(axis='y', labelcolor='tab:red')
ax2.plot(df.index, df['total_cost_MA_365'], color='tab:green', label='Mining total cost MA 365')
ax2.plot(df.index, df['total_cost_MA_730'], color='tab:orange', label='Mining total cost MA 730')
ax2.plot(df.index, df['total_cost_MA_90'], color='tab:olive', label='Mining total cost MA 90')


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

# Add a title
plt.title('Bitcoin Price and Mining Cost')

mark_bitcoin_halvings(ax1, bitcoin_halving_dates)
plt.grid(True)
# Show the plot
plt.show(block=False)

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
plt.show(block=False)


# Call the function for each dataset
#plot_dual_axis(df, y1_col, y2_col,               y1_label,       y2_label,   title, bitcoin_halving_dates, ordinal_date, china_ban_date, idx2_log_flag=True):
plot_dual_axis(df, 'Price', 'miners_revenue',        'BTC Price ', 'miners_revenue (USD probably per day)', 'Miners revenue:revenue earned by miners on the Bitcoin network block rewards and transaction fees', bitcoin_halving_dates, ordinal_date, china_ban_date)
plot_dual_axis(df, 'Price', 'hashrate', 'BTC Price ', 'hashrate', 'Hashrate', bitcoin_halving_dates, ordinal_date,
               china_ban_date)
plot_dual_axis(df, 'Price', 'Bitcoin_network_difficulty', 'BTC Price ', 'Bitcoin_network_difficulty',
               'Bitcoin_network_difficulty', bitcoin_halving_dates, ordinal_date, china_ban_date)

if show_all:
    plot_dual_axis(df, 'Price', 'transaction_volume', 'BTC Price ', 'Transaction Volume ', 'Transaction Volume ( transactions recorded on the blockchain)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'transactions_per_day', 'BTC Price ', 'Transactions Per Day)', 'Transactions Per Day(number of transactions recorded on the blockchai)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'mempool_size',        'BTC Price ', 'Mempool Size ', 'Mempool Size (waiting area for transactions)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'trade_volume',        'BTC Price ', 'Trade Volume', 'Trade Volume ( trading activity that occurs on exchanges)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'blocks_size',        'BTC Price ', 'Blocks Size', 'Bitcoin Price and Blocks Size', bitcoin_halving_dates, ordinal_date, china_ban_date)
    plot_dual_axis(df, 'Price', 'cost_per_transaction',        'BTC Price ', 'cost_per_transaction ', 'cost_per_transaction (USD)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    # plot_dual_axis(df, 'Price', 'transaction_rate',        'BTC Price ', 'transaction_rate', 'transaction_rate ( number of transactions processed per second TPS)', bitcoin_halving_dates, ordinal_date, china_ban_date, False)
    plot_dual_axis(df, 'Price', 'avg_confirmation_time',        'BTC Price ', 'avg_confirmation_time', 'avg_confirmation_time', bitcoin_halving_dates, ordinal_date, china_ban_date, False)



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

#drawing with respect to block
import matplotlib.pyplot as plt
import numpy as np

# --- Prepare data ---
blocks = df['block_number'].values
prices = df['Price'].values

# --- Determine halvings ---
halving_blocks = np.arange(210_000, blocks[-1] + 210_000, 210_000)
mid_blocks = halving_blocks - 105_000  # middle of each halving cycle

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

# --- Setup Figure with 2 Subplots ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 14))
num_cycles = len(halving_blocks)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for i in range(num_cycles - 1):
    mid_start = halving_blocks[i] - 105_000
    mid_end = halving_blocks[i + 1] - 105_000

    # Masking using your variables
    mask = (blocks >= mid_start) & (blocks < mid_end)
    cycle_blocks = blocks[mask]
    cycle_prices = prices[mask]

    if len(cycle_prices) == 0:
        continue

    # Baseline logic (Start = 100%)
    first_price = cycle_prices[0]
    if first_price == 0:
        non_zero = cycle_prices[cycle_prices > 0]
        first_price = non_zero[0] if len(non_zero) > 0 else 1

    pct_index = (cycle_prices / first_price) * 100
    relative_blocks = cycle_blocks - mid_start

    # --- TOP CHART: Continuous Timeline ---
    ax1.plot(cycle_blocks, pct_index, label=f'Cyc {i + 1}', color=colors[i % len(colors)])

    # --- BOTTOM CHART: Overlap ---
    ax2.plot(relative_blocks, pct_index, color=colors[i % len(colors)], alpha=0.6, linewidth=1.5)

    # --- Find Cycle Maximum ---
    max_idx = pct_index.argmax()
    max_val = pct_index[max_idx]
    max_x = relative_blocks[max_idx]

    # Mark Max with X and vertical line
    ax2.scatter(max_x, max_val, color=colors[i % len(colors)], marker='x', s=100, zorder=5)
    ax2.axvline(x=max_x, color=colors[i % len(colors)], linestyle=':', linewidth=1, alpha=0.6)
    ax2.text(max_x, max_val * 1.05, f'Max {i + 1}', color=colors[i % len(colors)],
             fontsize=9, fontweight='bold', ha='center')

    # --- Find Cycle Minimum ---
    min_idx = pct_index.argmin()
    min_val = pct_index[min_idx]
    min_x = relative_blocks[min_idx]

    # Mark Min with X and vertical line
    ax2.scatter(min_x, min_val, color=colors[i % len(colors)], marker='x', s=100, zorder=5)
    ax2.axvline(x=min_x, color=colors[i % len(colors)], linestyle='--', linewidth=1, alpha=0.4)
    ax2.text(min_x, min_val * 0.90, f'Min {i + 1}', color=colors[i % len(colors)],
             fontsize=9, fontweight='bold', ha='center', va='top')

# --- Formatting: Top Chart ---
ax1.set_yscale('log')
ax1.set_ylim(10, 300000)
ax1.axhline(y=100, color='black', linestyle='-', alpha=0.7)
ax1.set_ylabel('Price Index (Start = 100%)')
ax1.set_title('Bitcoin Mid-Halving Cycles: Continuous Timeline')
ax1.grid(True, which="both", linestyle='--', alpha=0.2)

for b in halving_blocks:
    ax1.axvline(x=b - 105000, color='yellow', linestyle='--', alpha=0.7)

# --- Formatting: Bottom Chart ---
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



# -----------------------------
# Parameters
# -----------------------------
BLOCKS_PER_CYCLE = 210_000
configs = [8, 16]  # Number of columns to generate

# -----------------------------
# Prepare Data
# -----------------------------
df = df.copy().sort_values("block_number")
df["cycle"] = df["block_number"] // BLOCKS_PER_CYCLE
df["block_in_cycle"] = df["block_number"] % BLOCKS_PER_CYCLE
current_block_val = df["block_in_cycle"].iloc[-1]

# Custom Colormap for consistent 0-white centering
custom_rdylgn = mcolors.LinearSegmentedColormap.from_list("", ["#d73027", "white", "#1a9850"])

# -----------------------------
# Loop to generate both Heatmaps
# -----------------------------
for segments in configs:
    blocks_per_seg = BLOCKS_PER_CYCLE // segments

    # 1. Calculate Segments & Returns
    df_temp = df.copy()
    df_temp["segment"] = (df_temp["block_in_cycle"] // blocks_per_seg).clip(upper=segments - 1)

    returns = df_temp.groupby(["cycle", "segment"]).agg(
        first_price=("Price", "first"),
        last_price=("Price", "last")
    )
    returns["yield_pct"] = (returns["last_price"] / returns["first_price"] - 1) * 100

    # 2. Pivot Table
    table = returns["yield_pct"].unstack("segment").fillna(0)
    table.columns = [f"S{i + 1}" for i in range(segments)]

    # 3. Dynamic Labels
    cycle_labels = []
    for cyc in table.index:
        start_b = cyc * BLOCKS_PER_CYCLE
        end_b = df_temp[df_temp["cycle"] == cyc]["block_number"].max() if cyc == df_temp["cycle"].max() else (
                                                                                                                         cyc + 1) * BLOCKS_PER_CYCLE - 1
        cycle_labels.append(f"Cyc {cyc} ({start_b // 1000}K–{end_b // 1000}K)")
    table.index = cycle_labels

    # 4. Plotting
    plt.figure(figsize=(16, 6))
    ax = sns.heatmap(
        table, annot=True, fmt=".1f", cmap=custom_rdylgn, center=0,
        vmin=-100, vmax=100, linewidths=0.7, linecolor="white"
    )

    # 5. Precise Pointer (Arrow + Block Number)
    exact_x_pos = current_block_val / blocks_per_seg
    num_rows = len(table)

    # Mini Arrow pointing at X-axis
    ax.annotate(
        '', xy=(exact_x_pos, num_rows), xytext=(exact_x_pos, num_rows - 0.12),
        arrowprops=dict(arrowstyle="->,head_width=0.2,head_length=0.3", color="black", lw=1.5)
    )

    # Block number text right near arrow
    ax.text(
        exact_x_pos, num_rows - 0.15, f"{current_block_val:,}",
        ha='center', va='bottom', fontsize=8, fontweight='bold',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0.05)
    )

    plt.title(f"Bitcoin Cycle Returns - {segments} Segments\nProgress: Block {current_block_val:,}", fontsize=14,
              fontweight='bold')
    plt.xlabel(f"Segments ({blocks_per_seg:,} blocks each)", fontsize=10)
    plt.ylabel("Cycle Range")
    plt.tight_layout()
    plt.show(block=False)
    plt.show()
















