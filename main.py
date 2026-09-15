# Personal Expense Tracker

import streamlit as st
import pandas as pd
import os
from datetime import date


# Page Config
st.set_page_config(page_title="Personal Expense Tracker", layout="wide")

FILE_NAME = "expenses.csv"

# Load Data and Save Data Functions
def load_data():
    if not os.path.exists(FILE_NAME):
        return pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
    df = pd.read_csv(FILE_NAME)
    df["Date"] = pd.to_datetime(df["Date"])  
    return df

def save_data(df):
    df.to_csv(FILE_NAME, index=False)

# Manage Session State (store data, monthly_budget)
if "data" not in st.session_state:
    st.session_state.data = load_data()

    st.session_state.data["Date"] = pd.to_datetime(
        st.session_state.data["Date"], errors="coerce"
    )

if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 0.0

df = st.session_state.data


# Sidebar - left side menu
st.sidebar.title(" Expense Manager")
menu = st.sidebar.radio(" Navigation", [
    " Add Expense",
    " Update/Delete",
    " Filter Data",
    " Insights",
    " Budget Tracker",
    " Upload / Download"
])

st.title(" Personal Expense Tracker")

# 1. ADD EXPENSE
if menu == " Add Expense":
    st.subheader("Add New Expense")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_input = st.date_input("Date")
            amount = st.number_input("Amount", min_value=0.0)
        with col2:
            category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Health", "Other"])
            description = st.text_input("Description")

        if st.form_submit_button("Add Expense"):
            new_row = pd.DataFrame(
                [[pd.to_datetime(date_input), amount, category, description]],  
                columns=["Date", "Amount", "Category", "Description"]
            )
            st.session_state.data = pd.concat([df, new_row], ignore_index=True)
            save_data(st.session_state.data)
            st.success("Added!")
            st.rerun()

    df_display = df.copy()
    df_display["Date"] = df_display["Date"].dt.date
    st.dataframe(df_display, use_container_width=True)

# 2. UPDATE / DELETE
elif menu == " Update/Delete":
    st.subheader("Manage Expenses")

    if df.empty:
        st.warning("No data available.")
    else:
        if "selected_index" not in st.session_state:
            st.session_state.selected_index = None

        st.write(" Edit Selected Entry")
        st.caption("Select from table")

        if st.session_state.selected_index is not None:
            row = df.loc[st.session_state.selected_index]

            col1, col2 = st.columns(2)
            with col1:
                edit_date = st.date_input("Edit Date", row["Date"].date())
                edit_amount = st.number_input("Edit Amount", value=float(row["Amount"]))
            with col2:
                edit_cat = st.selectbox(
                    "Category",
                    ["Food","Travel","Shopping","Bills","Health","Other"],
                    index=["Food","Travel","Shopping","Bills","Health","Other"].index(row["Category"])
                )
                edit_desc = st.text_input("Description", row["Description"])

            c1, c2 = st.columns(2)

            if c1.button("Update"):
                st.session_state.data.loc[st.session_state.selected_index] = {
                    "Date": pd.to_datetime(edit_date),
                    "Amount": edit_amount,
                    "Category": edit_cat,
                    "Description": edit_desc,
                    "Month": pd.to_datetime(edit_date).strftime("%Y-%m")
                }
                save_data(st.session_state.data)
                st.rerun()

            if c2.button("Delete"):
                st.session_state.data = df.drop(st.session_state.selected_index).reset_index(drop=True)
                save_data(st.session_state.data)
                st.session_state.selected_index = None
                st.rerun()

        else:
            st.info("Select a row from table")

        df_display = df.copy()
        df_display["Date"] = df_display["Date"].dt.date
        df_display.insert(0, "Select", False)

        if st.session_state.selected_index is not None:
            df_display.at[st.session_state.selected_index, "Select"] = True

        def handle_select():
            changes = st.session_state.editor["edited_rows"]
            for idx, val in changes.items():
                if val.get("Select"):
                    st.session_state.selected_index = int(idx)

        st.data_editor(
            df_display,
            key="editor",
            on_change=handle_select,
            disabled=[c for c in df_display.columns if c != "Select"]
        )

#3. filter data
elif menu == " Filter Data":
    st.subheader("Filter Your Expenses")

    if df.empty:
        st.warning("No data available.")
    else:
        df["Date"] = pd.to_datetime(df["Date"])

        c1, c2 = st.columns(2)

        start = pd.to_datetime(
            c1.date_input("Start Date", df["Date"].min().date())
        )

        end = pd.to_datetime(
            c2.date_input("End Date", df["Date"].max().date())
        )

        categories = st.multiselect(
            "Category",
            df["Category"].unique(),
            default=df["Category"].unique()
        )

        filtered = df[
            (df["Date"] >= start) &
            (df["Date"] <= end) &
            (df["Category"].isin(categories))
        ]

        filtered_display = filtered.copy()
        filtered_display["Date"] = filtered_display["Date"].dt.date

        st.dataframe(filtered_display, use_container_width=True)
#4. insight menu
elif menu == " Insights":
    st.subheader("Smart Insights")

    if df.empty:
        st.warning("No data available.")
    else:
        df["Date"] = pd.to_datetime(df["Date"])

        total = df["Amount"].sum()

        cat_spend = df.groupby("Category")["Amount"].sum()
        top_cat = cat_spend.idxmax()
        top_amt = cat_spend.max()

        avg_daily = df.groupby(df["Date"].dt.date)["Amount"].sum().mean()
        today = pd.to_datetime("today").normalize()

        last_7_start = today - pd.Timedelta(days=7)
        last_15_start = today - pd.Timedelta(days=15)

        last_7_total = df[df["Date"] >= last_7_start]["Amount"].sum()
        last_15_total = df[df["Date"] >= last_15_start]["Amount"].sum()

        # Row 1
        c1, c2 = st.columns(2)
        c1.info(f"Top Spending: {top_cat} (₹ {top_amt:,.0f})")
        c2.info(f" Avg Daily Spend: ₹ {avg_daily:,.0f}")

        # Row 2
        c3, c4 = st.columns(2)
        c3.info(f" Last 7 Days: ₹ {last_7_total:,.0f}")
        c4.info(f" Last 15 Days: ₹ {last_15_total:,.0f}")

        # Row 3 (Smart Alerts)
        c5, c6 = st.columns(2)

        with c5:
            if top_amt > total * 0.4:
                st.warning(f" {top_cat} is taking too much of your budget!")
            else:
                st.success(" Category spending is balanced")

        with c6:
            if avg_daily > 1000:
                st.error(" High daily spending detected!")
            else:
                st.success(" Daily spending is under control")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Category Breakdown")
            st.bar_chart(cat_spend)

        with col2:
            st.write("### Monthly Trend")
            df["Month"] = df["Date"].dt.to_period("M")
            monthly = df.groupby("Month")["Amount"].sum()
            st.line_chart(monthly)

# 5. BUDGET
elif menu == "🎯 Budget Tracker":
    st.subheader("Budget")

    budget = st.number_input("Monthly Budget", value=st.session_state.monthly_budget)
    st.session_state.monthly_budget = budget

    today = date.today()

    current = df[
        (df["Date"].apply(lambda x: x.month) == today.month) &
        (df["Date"].apply(lambda x: x.year) == today.year)
    ]

    spent = current["Amount"].sum()

    st.write(f"Spent: ₹{spent}")
    st.write(f"Remaining: ₹{budget - spent}")

# 6. UPLOAD
elif menu == " Upload / Download":
    file = st.file_uploader("Upload CSV")

    if file:
        df = pd.read_csv(file)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        st.session_state.data = df
        save_data(df)
        st.success("Uploaded")

    st.download_button("Download", df.to_csv(index=False), "data.csv")