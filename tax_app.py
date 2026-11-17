#this script simulates a freelancer getting paid for a job, calculating what percentages need to be set aside 
#for self-employment tax and federal income tax, and tracking the total balance in their tax bucket
#V14 - Full file with CSV bank statement bulk importer integrated

#this script simulates a freelancer getting paid for a job, calculating what percentages need to be set aside 
#for self-employment tax, emergency savings, retirement, and tracking the total balances in their financial vaults
#V13 - Multi-bucket allocations (Taxes, Savings, Retirement) & Schedule C Category rules integrated

#this script simulates a freelancer getting paid for a job, calculating tax, savings, and retirement splits, 
#and generating itemized receipts for every individual client payment
#V15 - Itemized Payment Receipts & Multi-Bucket Vault integrated

import streamlit as st
from datetime import date
import pandas as pd
from tax_logic import load_data, save_data, reset_data
from pdf_generator import generate_pdf_report

# Page Configuration
st.set_page_config(page_title="Freelancer Tax & Wealth Vault", page_icon="🏦", layout="centered")

st.title("🏦 Freelancer Tax Vault & Wealth Dashboard")
st.write("Automated tax sub-accounts, multi-bucket savings splits, itemized payment receipts, and PDF tax packet generator.")

# Load saved data into session state
if "data" not in st.session_state:
    st.session_state.data = load_data()

earnings_list = st.session_state.data["earnings"]
expenses_list = st.session_state.data["expenses"]

# Ensure backwards compatibility for older data structures without allocation fields
for item in earnings_list:
    item.setdefault("date", str(date.today()))
    item.setdefault("tax_alloc", item.get("amount", 0.0) * 0.25)
    item.setdefault("savings_alloc", item.get("amount", 0.0) * 0.10)
    item.setdefault("retirement_alloc", item.get("amount", 0.0) * 0.10)
    item.setdefault("spend_alloc", item.get("amount", 0.0) * 0.55)

for item in expenses_list:
    item.setdefault("date", str(date.today()))
    item.setdefault("category", "General Business / 100% Write-off")
    item.setdefault("raw_cost", item.get("cost", 0.0))

# --- SIDEBAR: SETTINGS & ALLOCATIONS ---
st.sidebar.header("⚙️ Multi-Bucket & Tax Settings")
tax_rate_percent = st.sidebar.slider("Tax Withholding Rate (%)", min_value=10, max_value=50, value=25, step=1)
savings_rate_percent = st.sidebar.slider("Emergency Savings Allocation (%)", min_value=0, max_value=25, value=10, step=1)
retirement_rate_percent = st.sidebar.slider("Retirement / Roth IRA Allocation (%)", min_value=0, max_value=25, value=10, step=1)

tax_rate = tax_rate_percent / 100.0
savings_rate = savings_rate_percent / 100.0
retirement_rate = retirement_rate_percent / 100.0

st.sidebar.subheader("🏢 Business Profile (Schedule C)")
business_desc = st.sidebar.text_input("Business Activity", value="Freelance Services / Consulting")
business_code = st.sidebar.text_input("NAICS Principal Business Code", value="541990")

st.sidebar.write("---")
st.sidebar.subheader("Navigation")
action = st.sidebar.radio("Go to:", [
    "Dashboard (Vault View)", 
    "Log Client Payment", 
    "Log Business Expense", 
    "Import Bank CSV", 
    "Quarterly Tax Report & PDF Export"
])

# --- SIDEBAR: DATA MANAGEMENT / RESET ---
st.sidebar.write("---")
st.sidebar.subheader("🗄️ Data Management")
if st.sidebar.button("🔄 Reset Vault & Clear All Data", type="secondary"):
    st.session_state.data = reset_data()
    st.sidebar.success("Vault data cleared successfully!")
    st.rerun()

# --- CALCULATIONS ---
total_earned = sum(item["amount"] for item in earnings_list)
total_exp = sum(item["cost"] for item in expenses_list)

# Total accumulated across vaults from individual stamped receipts
tax_bucket = sum(item.get("tax_alloc", item["amount"] * tax_rate) for item in earnings_list)
savings_bucket = sum(item.get("savings_alloc", item["amount"] * savings_rate) for item in earnings_list)
retirement_bucket = sum(item.get("retirement_alloc", item["amount"] * retirement_rate) for item in earnings_list)
spending_money = sum(item.get("spend_alloc", item["amount"] * (1 - tax_rate - savings_rate - retirement_rate)) for item in earnings_list) - total_exp

taxable_profit = total_earned - total_exp

# --- VIEW 1: DASHBOARD ---
if action == "Dashboard (Vault View)":
    st.subheader("📊 Your Financial Wealth & Vault Snapshot")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gross Revenue", f"${total_earned:,.2f}")
    col2.metric("🔒 Tax Vault", f"${tax_bucket:,.2f}", delta="Auto-locked")
    col3.metric("💵 Spendable Cash", f"${spending_money:,.2f}")

    st.write("---")
    col4, col5 = st.columns(2)
    col4.metric("💰 Emergency Savings", f"${savings_bucket:,.2f}")
    col5.metric("🌱 Retirement / Roth IRA", f"${retirement_bucket:,.2f}")

    st.write("---")
    col6, col7 = st.columns(2)
    col6.metric("Business Write-offs", f"${total_exp:,.2f}")
    col7.metric("Estimated Net Profit", f"${taxable_profit:,.2f}")

    st.write("### 🧾 Itemized Client Payment Receipts")
    st.write("Click on any payment receipt below to inspect its exact multi-bucket breakdown.")
    
    if earnings_list:
        for i, item in enumerate(reversed(earnings_list)):
            with st.expander(f"📁 Receipt #{len(earnings_list) - i} | {item['client']} — ${item['amount']:,.2f} ({item['date']})"):
                rc1, rc2 = st.columns(2)
                rc1.write(f"**Date Received:** {item['date']}")
                rc1.write(f"**Client Name:** {item['client']}")
                rc1.metric("Gross Payment", f"${item['amount']:,.2f}")
                
                rc2.write("**Vault Allocations Stamped on Receipt:**")
                rc2.write(f"🔒 Tax Allocation: **${item.get('tax_alloc', 0.0):,.2f}**")
                rc2.write(f"💰 Savings Allocation: **${item.get('savings_alloc', 0.0):,.2f}**")
                rc2.write(f"🌱 Retirement Allocation: **${item.get('retirement_alloc', 0.0):,.2f}**")
                rc2.write(f"💵 Spendable Portion: **${item.get('spend_alloc', 0.0):,.2f}**")
    else:
        st.info("No client payment receipts logged yet.")

    st.write("### 🧾 Business Expense Write-offs")
    if expenses_list:
        st.dataframe(expenses_list, use_container_width=True)
    else:
        st.info("No expenses logged yet.")

# --- VIEW 2: LOG CLIENT PAYMENT ---
elif action == "Log Client Payment":
    st.subheader("💰 Log Incoming Client Payment")
    with st.form("payment_form"):
        client_name = st.text_input("Client Name (e.g., Acme Corp)")
        payment_amount = st.number_input("Payment Amount ($)", min_value=0.0, step=50.0, format="%.2f")
        payment_date = st.date_input("Date Received", value=date.today())
        submitted = st.form_submit_button("Deposit & Generate Receipt")
        
        if submitted:
            if client_name:
                locked_tax = payment_amount * tax_rate
                locked_savings = payment_amount * savings_rate
                locked_retirement = payment_amount * retirement_rate
                spend = payment_amount - (locked_tax + locked_savings + locked_retirement)
                
                st.session_state.data["earnings"].append({
                    "date": str(payment_date),
                    "client": client_name,
                    "amount": payment_amount,
                    "tax_alloc": locked_tax,
                    "savings_alloc": locked_savings,
                    "retirement_alloc": locked_retirement,
                    "spend_alloc": spend
                })
                save_data(st.session_state.data)
                
                st.success(f"Generated Itemized Receipt for ${payment_amount:,.2f} from {client_name}!")
                st.info(
                    f"🔒 **Tax Vault:** ${locked_tax:,.2f} | "
                    f"💰 **Savings:** ${locked_savings:,.2f} | "
                    f"🌱 **Retirement:** ${locked_retirement:,.2f} | "
                    f"💵 **Spendable:** ${spend:,.2f}"
                )
                st.balloons()
            else:
                st.warning("Please enter a client name.")

# --- VIEW 3: LOG EXPENSE ---
elif action == "Log Business Expense":
    st.subheader("🧾 Log Business Expense (Schedule C Write-off)")
    with st.form("expense_form"):
        exp_desc = st.text_input("Expense Description (e.g., Adobe Subscription, Client Lunch)")
        exp_cost = st.number_input("Total Cost Paid ($)", min_value=0.0, step=10.0, format="%.2f")
        
        category = st.selectbox("Schedule C Expense Category", [
            "General Business / 100% Write-off (Software, Tools, Supplies, Advertising)",
            "Business Meals / 50% IRS Deductible Limit"
        ])
        
        exp_date = st.date_input("Expense Date", value=date.today())
        exp_submitted = st.form_submit_button("Save Expense")
        
        if exp_submitted:
            if exp_desc:
                if "50%" in category:
                    deductible_amount = exp_cost * 0.50
                    cat_label = "Business Meals (50% Rule)"
                else:
                    deductible_amount = exp_cost
                    cat_label = "General Business (100%)"
                
                st.session_state.data["expenses"].append({
                    "date": str(exp_date),
                    "description": exp_desc,
                    "category": cat_label,
                    "cost": deductible_amount,
                    "raw_cost": exp_cost
                })
                save_data(st.session_state.data)
                st.success(f"Successfully logged: {exp_desc} (-${deductible_amount:,.2f} tax deduction applied)!")
            else:
                st.warning("Please enter an expense description.")

# --- VIEW 4: IMPORT BANK CSV ---
elif action == "Import Bank CSV":
    st.subheader("📥 Bulk Import Bank Statement (CSV)")
    st.write("Export your transactions as a CSV from your online banking portal and upload them here to process multiple items at once.")
    
    uploaded_file = st.file_uploader("Upload bank statement (.csv)", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("### 👀 Preview Uploaded Data", df.head())
        
        st.write("### ⚙️ Map Your Columns")
        col1, col2, col3 = st.columns(3)
        with col1:
            date_col = st.selectbox("Date Column", df.columns)
        with col2:
            desc_col = st.selectbox("Description / Client Column", df.columns)
        with col3:
            amount_col = st.selectbox("Amount Column ($)", df.columns)
            
        import_type = st.radio("Are these mostly Income or Expenses?", ["Income (Client Payments)", "Expenses (Write-offs)"])
        
        if st.button("Process & Save to Vault"):
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    raw_amt = str(row[amount_col]).replace("$", "").replace(",", "").strip()
                    amt = float(raw_amt)
                    if amt == 0:
                        continue
                    tx_date = str(row[date_col])
                    tx_desc = str(row[desc_col])
                    
                    if import_type == "Income (Client Payments)" and amt > 0:
                        t_alloc = amt * tax_rate
                        s_alloc = amt * savings_rate
                        r_alloc = amt * retirement_rate
                        sp_alloc = amt - (t_alloc + s_alloc + r_alloc)
                        
                        st.session_state.data["earnings"].append({
                            "date": tx_date,
                            "client": tx_desc,
                            "amount": amt,
                            "tax_alloc": t_alloc,
                            "savings_alloc": s_alloc,
                            "retirement_alloc": r_alloc,
                            "spend_alloc": sp_alloc
                        })
                        imported_count += 1
                    elif import_type == "Expenses (Write-offs)":
                        cost_val = abs(amt)
                        st.session_state.data["expenses"].append({
                            "date": tx_date,
                            "description": tx_desc,
                            "category": "Imported CSV Expense",
                            "cost": cost_val,
                            "raw_cost": cost_val
                        })
                        imported_count += 1
                except Exception:
                    continue
            
            save_data(st.session_state.data)
            st.success(f"Successfully imported {imported_count} transactions and generated receipts!")
            st.balloons()

# --- VIEW 5: QUARTERLY TAX REPORT & PDF EXPORT ---
elif action == "Quarterly Tax Report & PDF Export":
    st.subheader("📑 Schedule SE, Schedule C, & 1040-ES PDF Report Generator")
    
    st.warning(
        "⚠️ **DISCLAIMER:** This software calculates estimated Self-Employment (Schedule SE) and Income taxes "
        "for organizational purposes only. Always consult a certified CPA before filing."
    )
    
    se_tax_est = (taxable_profit * 0.9235 * 0.153) if taxable_profit > 400 else 0.0
    half_se = se_tax_est / 2.0
    income_tax_est = max(0.0, taxable_profit - half_se) * tax_rate
    total_tax_est = se_tax_est + income_tax_est
    quarterly_est = total_tax_est / 4.0 if total_tax_est > 0 else 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Est. Self-Employment Tax (SE)", f"${se_tax_est:,.2f}")
    col2.metric("Est. Total Combined Tax", f"${total_tax_est:,.2f}")
    
    st.info(f"**Suggested Quarterly Payment (Form 1040-ES):** ${quarterly_est:,.2f} per quarter")
    
    st.write("---")
    st.subheader("📥 Download Professional Tax Packet")
    st.write("Click below to generate your complete tax filing breakdown PDF including IRS payment instructions and NAICS business profile.")
    
    pdf_bytes = generate_pdf_report(
        total_earned, total_exp, taxable_profit, tax_rate_percent, 
        business_code, business_desc, earnings_list, expenses_list
    )
    
    st.download_button(
        label="📥 Download Professional Tax Packet (.pdf)",
        data=pdf_bytes,
        file_name="Freelancer_Complete_Tax_Packet.pdf",
        type="primary",
        mime="application/pdf",
        key="download_pdf_report"
    )