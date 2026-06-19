import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Superstore Dashboard",page_icon='📊',layout='wide',initial_sidebar_state='expanded')

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv("data/superstore_clean.csv")

    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"] = pd.to_datetime(df["Ship Date"])

    return df


st.title('📊Superstore Sales Dashboard')

with st.sidebar:
    st.header('🔍Filters')
    regions=st.multiselect('Region',
        options=df['Region'].unique(),
        default=df['Region'].unique())
    Year=st.multiselect('Year',
        options=df['Order Year'].unique(),
        default=df['Order Year'].unique())
    with st.form('date_filter'):
        st.write('🗓️Date Range')
        start=st.date_input('Start date',value=df['Order Date'].min().date())
        end=st.date_input('End date',value=df['Order Date'].max().date())
        submitted=st.form_submit_button('Apply')

    if st.sidebar.button("🔄️Refresh Data"):
        st.cache_data.clear()
        st.rerun()


filtered=df[df['Region'].isin(regions)&df['Order Year'].isin(Year)]
if submitted:
        filtered=filtered[filtered['Order Date'].dt.date.between(start,end)]
st.sidebar.divider()
csv_bytes=filtered.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    "📥Download filtered data",
    data=csv_bytes, 
    file_name="superstore_filtered.csv", 
    mime="text/csv")

Dis_arr=filtered['Discount'].values
sales_arr=filtered['Sales'].values
high_disc_pct=np.percentile(Dis_arr,75) if len(Dis_arr) else 0
high_disc_n=int(np.sum(Dis_arr>high_disc_pct)) if len(Dis_arr) else 0
z_score=((sales_arr-np.mean(sales_arr))/np.std(sales_arr)) if len(sales_arr) else 0
outlier_n=int(np.sum(np.abs(z_score)>3)) if len(z_score) else 0
mean_margin=filtered['Profit Margin%'].mean() if len(filtered) else 0

c1,c2,c3=st.columns(3)

c1.metric("Total Sales", f"${filtered['Sales'].sum():,.0f}")
c2.metric("Total Profit", f"${filtered['Profit'].sum():,.0f}")
c3.metric("Avg Discount", f"{filtered['Discount'].mean()*100:,.1f}%")


tab1,tab2,tab3,tab4=st.tabs(['📋 Overview','📦By Category','🗺️By Region','🚨Quality Alerts'])
with tab1:
    st.subheader('Filtered Data - First 20 rows')
    st.dataframe(filtered.head(20),hide_index=True,use_container_width=True)
    st.subheader('📈Monthly Sales by Year')
    monthly_yr = (filtered.groupby([filtered['Order Date'].dt.to_period("M").astype(str),"Order Year"])["Sales"].sum().reset_index().rename(columns={"Order Date": "Month"}))
    fig = px.line(monthly_yr, x="Month", y="Sales",
    color="Order Year", title="Monthly Sales by Year")
    st.plotly_chart(fig, use_container_width=True)
with tab2:
    st.subheader("📦Top 10 Sub-Categories by Sales")
    top10=filtered.groupby("Sub_Category")["Sales"].sum().nlargest(10).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(top10.index, top10.values, color="#F63B79")
    ax.bar_label(bars, fmt="$%.0f", padding=4, fontsize=8)
    ax.set_xlabel("Total Sales")
    ax.set_title("Top 10 Sub-Categories by Sales")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.subheader("🗒️Sub-Category Breakdown")
    summary=filtered.groupby('Sub_Category').agg(
    sales=('Sales','sum'),profit=('Profit','sum')).sort_values("sales",ascending=False)
    st.dataframe(summary.style.format("${:,.0f}"),use_container_width=True)
    st.subheader(" 🎯Sales Vs Profit")
    fig = px.scatter(filtered, x="Sales", y="Profit",
    color="Category", size="Quantity",
    hover_data=["Sub_Category"],
    title="Sales vs Profit by Category")
    st.plotly_chart(fig, use_container_width=True)
with tab3:
    st.subheader("🗺️Profit Share by Region")
    reg=filtered.groupby('Region')['Profit'].sum().reset_index()
    fig=px.pie(reg,names='Region',values='Profit',
           hole=0.4,title='Profit Share by Region')
    st.plotly_chart(fig, use_container_width=True)
with tab4:
    st.subheader("🚨Quality Alerts")
    if mean_margin<10:
     st.error(f'🔴Critical messaging :{mean_margin:.1f}%-investigate discount and product mix.')
    elif mean_margin< 20:
      st.warning(f'🟡Moderate message:{mean_margin:.1f}%-room to improve.')
    else:
      st.success(f'🟢Healthy message:{mean_margin:.1f}% pricing strategy is working well.')
    st.info(f' {high_disc_n} orders have discount above the 75th percentile ({high_disc_pct*100:.0f}%).')
    if outlier_n>0:
        st.warning(f' {outlier_n} sales outliers detected (|z-score|>3).')
    else:
        st.success('No sales outliers detected.')
    with st.expander("view outlier rows"):
        outlier_mask = np.abs(z_score)>3 if len(z_score) else 0
        outliers=filtered[outlier_mask] if len(outlier_mask) else 0
        st.dataframe(outliers[[ 'Order ID','Sales','Profit','Region','Order Date']],use_container_width=True)

st.markdown("---")

min_year = filtered['Order Date'].min()
max_year = filtered['Order Date'].max()
st.caption(f'Showing {len(filtered):,} rows. {min_year}-{max_year}. Built by Fathima Farhana')
