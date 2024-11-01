import pandas as pd
import glob
import os
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# get the lates trader tagging file
downloads_folder = os.path.join(os.environ['USERPROFILE'], 'Downloads')
list_of_files = glob.glob(os.path.join(downloads_folder, 'trader_tagging*.csv'))
latest_file = max(list_of_files, key=os.path.getmtime)

# load and process data
df = pd.read_csv(latest_file)
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M')
df = df[(df['Date'].dt.time >= pd.to_datetime('07:00').time()) & (df['Date'].dt.time <= pd.to_datetime('22:29').time())]
df = df.dropna(subset=['Event'])
df = df[df['Scheduled for in-play'] != 'No']
df = df.sort_values(by=['Scheduled for in-play'], ascending=False).drop_duplicates(subset='Event', keep='first')
df['Trader'] = df['Assign a trader'].str.replace(r'\d+', '', regex=True).str.replace(r'\(.*\)', '', regex=True).str.strip()
df.drop(['Assign a trader'], axis=1, inplace=True)
df['Trader'] = df['Trader'].replace('-', 'Unassigned')
df['Hour'] = df['Date'].dt.hour

# define bins and format time for table
start_hour = 7
end_hour = 23
bins = list(range(start_hour, end_hour+1))
labels = [f"{i}am-{i+1}am" if i < 12 else f"{i-12}pm-{i-11}pm" if i > 12 else "12pm-1pm" for i in range(start_hour, end_hour)]
df['Time'] = pd.cut(df['Hour'], bins=bins, labels=labels, right=False)

# pivot table for heat map
pivot_table = df.pivot_table(index='Time', columns='Trader', aggfunc='size', fill_value=0, observed=False)

# Streamlit app layout
st.title("Trader Heatmap")

# Plot the heatmap
plt.figure(figsize=(8, 8))  # Adjust the figure size to make it more square
ax = sns.heatmap(pivot_table, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5, cbar=False,
                 annot_kws={"size": 10, "weight": "bold"}, square=False)
plt.xticks(rotation=45, ha='right', fontsize=12)  # Make trader names larger and rotate
plt.yticks(fontsize=10)  # Adjust font size for y-axis (time slots)
plt.xlabel("")
plt.ylabel("")
for i in range(len(pivot_table) + 1):  # Add lines for each row in the heatmap
    ax.hlines(i, *ax.get_xlim(), color='gray', linewidth=0.5)
plt.tight_layout()
st.pyplot(plt)