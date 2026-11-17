#V6 - Added transaction dates to the supporting ledger table

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(total_earned, total_exp, taxable_profit, tax_rate_percent, business_code, business_desc, earnings_list, expenses_list):
    """
    Generates a professional IRS Schedule C, Schedule SE, Form 1040-ES breakdown 
    packet complete with official IRS payment method instructions and transaction dates.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#6B7280'), spaceAfter=10)
    heading_style = ParagraphStyle('Head', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1F2937'), spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#374151'), spaceAfter=4)
    disclaimer_style = ParagraphStyle('Disc', parent=styles['Normal'], fontSize=7.5, textColor=colors.HexColor('#9CA3AF'), spaceBefore=8)
    
    # Header Banner & Title
    story.append(Paragraph("<b>FREELANCER TAX VAULT — PROFESSIONAL TAX & PAYMENT PACKET</b>", title_style))
    story.append(Paragraph(f"Includes Schedule C, Schedule SE, 1040-ES Schedule, & IRS Payment Instructions | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceAfter=10))
    
    # --- TAX CALCULATIONS ---
    net_profit = taxable_profit
    se_tax = (net_profit * 0.9235) * 0.153 if net_profit > 400 else 0.0
    half_se_tax = se_tax / 2.0
    adjusted_income_for_tax = max(0.0, net_profit - half_se_tax)
    income_tax = adjusted_income_for_tax * (tax_rate_percent / 100.0)
    total_annual_tax = se_tax + income_tax
    estimated_quarterly = total_annual_tax / 4.0 if total_annual_tax > 0 else 0.0
    
    # 1. Schedule C & Industry Classification
    story.append(Paragraph("<b>1. Business Identification & Schedule C (Profit or Loss)</b>", heading_style))
    sched_c_data = [
        ["Business Classification / Description", "NAICS Code", "Amount ($)"],
        [business_desc, business_code, "Code Ref Active"],
        ["Gross receipts or sales (Line 1)", "Schedule C, Line 1", f"${total_earned:,.2f}"],
        ["Total business expenses (Line 28)", "Schedule C, Line 28", f"${total_exp:,.2f}"],
        ["Net profit / (loss) (Line 31)", "Schedule C, Line 31", f"${net_profit:,.2f}"]
    ]
    t1 = Table(sched_c_data, colWidths=[240, 130, 170])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
    ]))
    story.append(t1)
    story.append(Spacer(1, 8))
    
    # 2. Combined Tax Breakdown
    story.append(Paragraph("<b>2. Total Tax Burden Breakdown (Schedule SE & Income Tax)</b>", heading_style))
    tax_breakdown_data = [
        ["Tax Component", "Basis / Rate", "Estimated Amount"],
        ["Self-Employment Tax (Schedule SE)", "15.3% on 92.35% of Net Profit", f"${se_tax:,.2f}"],
        ["Deductible Part of SE Tax", "50% Form 1040 Adjustment", f"-${half_se_tax:,.2f}"],
        ["Estimated Income Tax", f"{tax_rate_percent}% Effective Bracket", f"${income_tax:,.2f}"],
        ["Total Annual Tax Obligation", "Combined SE + Income Tax", f"${total_annual_tax:,.2f}"]
    ]
    t2 = Table(tax_breakdown_data, colWidths=[200, 180, 160])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4B5563')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8))
    
    # 3. Form 1040-ES Quarterly Schedule & Payment Instructions
    story.append(Paragraph("<b>3. Form 1040-ES Quarterly Schedule & IRS Payment Guide</b>", heading_style))
    q_data = [
        ["Quarter", "Due Date", "Suggested Quarterly Payment"],
        ["Q1", "April 15", f"${estimated_quarterly:,.2f}"],
        ["Q2", "June 15", f"${estimated_quarterly:,.2f}"],
        ["Q3", "September 15", f"${estimated_quarterly:,.2f}"],
        ["Q4", "January 15 (Next Year)", f"${estimated_quarterly:,.2f}"]
    ]
    t3 = Table(q_data, colWidths=[100, 180, 260])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
    ]))
    story.append(t3)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>How to Pay IRS Estimated Taxes:</b>", body_style))
    story.append(Paragraph("• <b>Online (Recommended):</b> Use <b>IRS Direct Pay</b> (irs.gov/payments) to transfer funds directly from your checking/savings account for free using reason code 'Estimated Tax'.", body_style))
    story.append(Paragraph("• <b>By Mail:</b> Print Form 1040-ES voucher for the respective quarter, write your SSN and '20XX Form 1040-ES' on a check, and mail to the IRS address listed in the form instructions.", body_style))
    story.append(Spacer(1, 8))
    
    # 4. Itemized Ledger
    story.append(Paragraph("<b>4. Supporting Transaction Ledger</b>", heading_style))
    ledger_data = [["Date", "Type", "Description / Client", "Amount"]]
    for item in earnings_list:
        ledger_date = item.get("date", "N/A")
        ledger_data.append([ledger_date, "Income", item['client'], f"+${item['amount']:,.2f}"])
    for item in expenses_list:
        ledger_date = item.get("date", "N/A")
        ledger_data.append([ledger_date, "Expense", item['description'], f"-${item['cost']:,.2f}"])
        
    t4 = Table(ledger_data, colWidths=[80, 70, 230, 120])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    story.append(t4)
    story.append(Spacer(1, 10))
    
    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#D1D5DB'), spaceAfter=4))
    story.append(Paragraph("<b>DISCLAIMER:</b> Estimates include calculated Schedule SE and Income tax provisions for organizational planning only. Always consult a certified CPA before filing or submitting payments.", disclaimer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()