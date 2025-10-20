import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

st.title("Trader Heatmap")

uploaded_file = st.file_uploader("Choose a trader tagging CSV file", type="csv")

def build_time_labels(start_hour=7, end_hour=23):
    bins = list(range(start_hour, end_hour + 1))
    labels = [
        (f"{i}am-{i+1}am") if i < 12
        else ("12pm-1pm" if i == 12 else f"{i-12}pm-{i-11}pm")
        for i in range(start_hour, end_hour)
    ]
    return bins, labels

def make_pivot(df):
    # Pivot counts by time x trader
    return df.pivot_table(
        index='Time', columns='Trader', aggfunc='size', fill_value=0, observed=False
    )

def plot_heatmap(pivot_table):
    fig, ax = plt.subplots(figsize=(8, 8))
    sns.heatmap(
        pivot_table,
        annot=True, fmt="d", cmap="YlOrRd",
        linewidths=0.5, cbar=False,
        annot_kws={"size": 10, "weight": "bold"},
        square=False, ax=ax
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis='x', rotation=45, labelsize=12)
    ax.tick_params(axis='y', labelsize=10)
    # Row divider lines
    for i in range(len(pivot_table) + 1):
        ax.hlines(i, *ax.get_xlim(), color='gray', linewidth=0.5)
    fig.tight_layout()
    return fig

if uploaded_file is not None:
    # ---- Load & base clean (shared by both views) ----
    df_base = pd.read_csv(uploaded_file)
    df_base['Date'] = pd.to_datetime(df_base['Date'], format='%d/%m/%Y %H:%M')

    # keep within 07:00–22:29
    df_base = df_base[
        (df_base['Date'].dt.time >= pd.to_datetime('07:00').time()) &
        (df_base['Date'].dt.time <= pd.to_datetime('22:29').time())
    ]

    df_base = df_base.dropna(subset=['Event'])

    # Prefer in-play rows when deduplicating events (for both views)
    df_base = df_base.sort_values(
        by=['Scheduled for in-play'], ascending=False
    ).drop_duplicates(subset='Event', keep='first')

    # Clean trader
    df_base['Trader'] = (
        df_base['Assign a trader']
        .str.replace(r'\d+', '', regex=True)
        .str.replace(r'\(.*\)', '', regex=True)
        .str.strip()
        .replace('-', 'Unassigned')
    )
    df_base = df_base.drop(columns=['Assign a trader'])

    # Time binning
    df_base['Hour'] = df_base['Date'].dt.hour
    bins, labels = build_time_labels(7, 23)
    df_base['Time'] = pd.cut(df_base['Hour'], bins=bins, labels=labels, right=False)

    # ---- View 1: Scheduled for In-Play (filtered) ----
    df_inplay = df_base[df_base['Scheduled for in-play'] != 'No'].copy()
    pivot_inplay = make_pivot(df_inplay)
    st.subheader("Scheduled for In-Play")
    if len(df_inplay) == 0:
        st.info("No rows where ‘Scheduled for in-play’ is not ‘No’.")
    else:
        fig1 = plot_heatmap(pivot_inplay)
        st.pyplot(fig1)

    # ---- View 2: Total (no in-play filter) ----
    pivot_total = make_pivot(df_base)
    st.subheader("Total")
    fig2 = plot_heatmap(pivot_total)
    st.pyplot(fig2)

else:
    st.warning("Please upload a trader tagging CSV file to generate the heatmaps.")

