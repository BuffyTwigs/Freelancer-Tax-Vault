#this script simulates a freelancer getting paid for a job, calculating tax, savings, and retirement splits, 
#itemized receipts, Schedule C categories, base64 receipt photos, and free Tesseract OCR receipt scanning
#V20 - Free Tesseract OCR Receipt Scanner & Smart Expense Splitter

import streamlit as st
from datetime import date
import pandas as pd
import base64
import re
from PIL import Image
import pytesseract
from tax_logic import load_data, save_data, reset_data
from pdf_generator import generate_pdf_report

# Page Configuration
st.set_page_config(page_title="Freelancer Tax & Wealth Vault", page_icon="🏦", layout="centered")

st.title("🏦 Freelancer Tax Vault & Wealth Dashboard")
st.write("Automated tax sub-accounts, multi-bucket savings splits, itemized receipts, and AI Receipt OCR Scanner.")

# Load saved data into session state
if "data" not in st.session_state:
    st.session_state.data = load_data()

earnings_list = st.session_state.data["earnings"]
expenses_list = st.session_state.data["expenses"]

# Ensure backwards compatibility for older data structures
for item in earnings_list:
    item.setdefault("date", str(date.today()))
    item.setdefault("tax_alloc", item.get("amount", 0.0) * 0.25)
    item.setdefault("savings_alloc", item.get("amount", 0.0) * 0.10)
    item.setdefault("retirement_alloc", item.get("amount", 0.0) * 0.10)
    item.setdefault("spend_alloc", item.get("amount", 0.0) * 0.55)

for item in expenses_list:
    item.setdefault("date", str(date.today()))
    item.setdefault("category", "Other / General Business (Line 27a) - 100%")
    item.setdefault("raw_cost", item.get("cost", 0.0))
    item.setdefault("business_percentage", 100)
    item.setdefault("receipt_img_b64", None)

# Official IRS Schedule C Categories
SCHEDULE_C_CATEGORIES = [
    "Advertising & Marketing (Line 8) - 100%",
    "Car & Truck / Gas & Mileage (Line 9) - 100%",
    "Contract Labor (Line 11) - 100%",
    "Insurance / Business (Line 15) - 100%",
    "Legal & Professional Services (Line 17) - 100%",
    "Office Expenses & Software (Line 18) - 100%",
    "Rent / Equipment & Workspace (Line 20) - 100%",
    "Repairs & Maintenance (Line 21) - 100%",
    "Supplies & Tools (Line 22) - 100%",
    "Travel / Flights & Lodging (Line 24a) - 100%",
    "Business Meals (Line 24b) - 50% IRS Limit",
    "Utilities / Internet & Phone (Line 25) - 100%",
    "Other / General Business (Line 27a) - 100%"
]

def auto_categorize_expense(description):
    """Scans merchant text to auto-suggest a Schedule C category."""
    desc_upper = description.upper()
    if any(k in desc_upper for k in ["META", "GOOGLE ADS", "FACEBOOK", "PRINT", "FLYER"]):
        return 0 
    elif any(k in desc_upper for k in ["SHELL", "CHEVRON", "EXXON", "GAS", "UBER", "AUTOZONE"]):
        return 1 
    elif any(k in desc_upper for k in ["ADOBE", "AWS", "GITHUB", "MICROSOFT", "APPLE", "STAPLES", "ZOOM"]):
        return 5 
    elif any(k in desc_upper for k in ["HOME DEPOT", "LOWES", "HARBOR FREIGHT", "AMAZON"]):
        return 8 
    elif any(k in desc_upper for k in ["AIRLINE", "DELTA", "HOTEL", "AIRBNB"]):
        return 9 
    elif any(k in desc_upper for k in ["STARBUCKS", "MCDONALDS", "CHIPOTLE", "RESTAURANT", "CAFE"]):
        return 10 
    elif any(k in desc_upper for k in ["VERIZON", "AT&T", "COMCAST", "PG&E"]):
        return 11 
    else:
        return 12 

def scan_receipt_with_ocr(image_file):
    """Uses Tesseract OCR to extract text and find the largest dollar amount on a receipt."""
    try:
        img = Image.open(image_file)
        raw_text = pytesseract.image_to_string(img)
        
        # Search for all dollar-like amounts (e.g., 45.99, 12.00)
        amounts = re.findall(r'\b\d+\.\d{2}\b', raw_text)
        float_amounts = [float(amt) for amt in amounts]
        
        suggested_cost = max(float_amounts) if float_amounts else 0.0
        return raw_text.strip(), suggested_cost
    except Exception as e:
        return "", 0.0

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
    if earnings_list:
        for i, item in enumerate(reversed(earnings_list)):
            with st.expander(f"📁 Payment #{len(earnings_list) - i} | {item['client']} — ${item['amount']:,.2f} ({item['date']})"):
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

    st.write("### 🧾 Business Expense Write-offs & Receipt Photos")
    if expenses_list:
        for i, exp in enumerate(reversed(expenses_list)):
            bus_pct = exp.get("business_percentage", 100)
            status_icon = "🟢 Business" if bus_pct > 0 else "🔴 Personal (Ignored)"
            with st.expander(f"🧾 Expense #{len(expenses_list) - i} | {exp['description']} — ${exp['cost']:,.2f} ({status_icon})"):
                ec1, ec2 = st.columns(2)
                ec1.write(f"**Date:** {exp['date']}")
                ec1.write(f"**Description:** {exp['description']}")
                ec1.write(f"**Category:** {exp['category']}")
                ec1.write(f"**Business Use:** {bus_pct}%")
                ec1.write(f"**Tax-Deductible Amount:** ${exp['cost']:,.2f}")
                
                if ec2.button("Delete Expense", key=f"del_exp_{i}"):
                    expenses_list.remove(exp)
                    save_data(st.session_state.data)
                    st.rerun()

                if exp.get("receipt_img_b64") is not None:
                    st.write("---")
                    st.write("📎 **Attached Receipt Photo & OCR Data:**")
                    img_bytes = base64.b64decode(exp["receipt_img_b64"])
                    st.image(img_bytes, caption=exp['description'], use_container_width=True)
                else:
                    st.write("*(No receipt photo attached)*")
    else:
        st.info("No business expenses logged yet.")

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
                st.balloons()
            else:
                st.warning("Please enter a client name.")

# --- VIEW 3: LOG EXPENSE ---
elif action == "Log Business Expense":
    st.subheader("🧾 AI OCR Receipt Scanner & Expense Splitter")
    
    # Initialize session state for OCR auto-filled values if not present
    if "ocr_scanned_cost" not in st.session_state:
        st.session_state.ocr_scanned_cost = 0.0

    receipt_file = st.file_uploader("Snap or Upload Receipt Photo for OCR Scanner", type=["png", "jpg", "jpeg"])
    
    scanned_text = ""
    detected_amount = 0.0
    
    if receipt_file is not None:
        if st.button("🔍 Run AI OCR Scan on Receipt"):
            with st.spinner("Scanning receipt pixels for text and totals..."):
                scanned_text, detected_amount = scan_receipt_with_ocr(receipt_file)
                st.session_state.ocr_scanned_cost = detected_amount
                st.success(f"OCR Scan Complete! Auto-detected total: ${detected_amount:,.2f}")
                if scanned_text:
                    with st.expander("View Raw OCR Scanned Text"):
                        st.text(scanned_text)

    exp_desc = st.text_input("Merchant / Expense Description (e.g., Staples Printer Ink)")
    
    suggested_index = auto_categorize_expense(exp_desc) if exp_desc else 12
    category = st.selectbox("Schedule C Category (Auto-Suggested)", SCHEDULE_C_CATEGORIES, index=suggested_index)
    
    # Use OCR detected amount as default if available
    exp_cost = st.number_input("Total Receipt Amount Paid ($)", min_value=0.0, value=st.session_state.ocr_scanned_cost, step=10.0, format="%.2f")
    
    business_percentage = st.slider(
        "Business Use Percentage (%) — Move to 0% if personal!", 
        min_value=0, max_value=100, value=100, step=5
    )
    
    exp_date = st.date_input("Expense Date", value=date.today())
    
    if st.button("Save Scanned Expense & Write-off", type="primary"):
        if exp_desc:
            base_deductible = exp_cost * (business_percentage / 100.0)
            if "50%" in category:
                deductible_amount = base_deductible * 0.50
            else:
                deductible_amount = base_deductible
            
            img_b64 = None
            if receipt_file is not None:
                # Reset file pointer and read bytes for base64 storage
                receipt_file.seek(0)
                img_bytes = receipt_file.read()
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            
            st.session_state.data["expenses"].append({
                "date": str(exp_date),
                "description": exp_desc,
                "category": category,
                "cost": deductible_amount,
                "raw_cost": exp_cost,
                "business_percentage": business_percentage,
                "receipt_img_b64": img_b64
            })
            save_data(st.session_state.data)
            st.success(f"Successfully processed receipt! Tax write-off logged: -${deductible_amount:,.2f} ({business_percentage}% business use).")
            st.session_state.ocr_scanned_cost = 0.0
            st.balloons()
        else:
            st.warning("Please enter an expense description or merchant name.")

# --- VIEW 4: IMPORT BANK CSV ---
elif action == "Import Bank CSV":
    st.subheader("📥 Bulk Import Bank Statement (CSV)")
    uploaded_file = st.file_uploader("Upload bank statement (.csv)", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("### 👀 Preview Uploaded Data", df.head())
        
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
                        suggested_idx = auto_categorize_expense(tx_desc)
                        cat_label = SCHEDULE_C_CATEGORIES[suggested_idx]
                        ded_rate = 0.50 if "50%" in cat_label else 1.0
                        
                        st.session_state.data["expenses"].append({
                            "date": tx_date,
                            "description": tx_desc,
                            "category": cat_label,
                            "cost": cost_val * ded_rate,
                            "raw_cost": cost_val,
                            "business_percentage": 100,
                            "receipt_img_b64": None
                        })
                        imported_count += 1
                except Exception:
                    continue
            
            save_data(st.session_state.data)
            st.success(f"Successfully imported {imported_count} transactions with smart categorization!")
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