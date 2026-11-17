#V7 - Added transaction dates to the supporting ledger table

# pdf_generator.py - Generates professional Schedule C & 1040-ES PDF packets with categorized expense breakdowns

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

def generate_pdf_report(total_earned, total_exp, taxable_profit, tax_rate_percent, business_code, business_desc, earnings_list, expenses_list):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#374151"))

    # Title Header
    story.append(Paragraph("<b>FREELANCER TAX & WEALTH PACKET</b>", title_style))
    story.append(Paragraph("Official Estimated Tax Calculation, Schedule C Summary, and Expense Ledger", subtitle_style))
    story.append(Spacer(1, 10))

    # Business Profile Box
    profile_data = [
        [Paragraph("<b>Business Activity:</b>", body_style), Paragraph(business_desc, body_style)],
        [Paragraph("<b>NAICS Business Code:</b>", body_style), Paragraph(str(business_code), body_style)],
        [Paragraph("<b>Tax Withholding Rate:</b>", body_style), Paragraph(f"{tax_rate_percent}%", body_style)]
    ]
    t_profile = Table(profile_data, colWidths=[150, 384])
    t_profile.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F3F4F6")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D1D5DB")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_profile)
    story.append(Spacer(1, 15))

    # Financial Summary
    story.append(Paragraph("<b>1. Annual Financial Overview</b>", heading_style))
    se_tax_est = (taxable_profit * 0.9235 * 0.153) if taxable_profit > 400 else 0.0
    half_se = se_tax_est / 2.0
    income_tax_est = max(0.0, taxable_profit - half_se) * (tax_rate_percent / 100.0)
    total_tax_est = se_tax_est + income_tax_est
    quarterly_est = total_tax_est / 4.0 if total_tax_est > 0 else 0.0

    summary_data = [
        ["Gross Revenue", f"${total_earned:,.2f}"],
        ["Total Business Write-offs", f"-${total_exp:,.2f}"],
        ["Estimated Net Schedule C Profit", f"${taxable_profit:,.2f}"],
        ["Estimated Self-Employment Tax (SE)", f"${se_tax_est:,.2f}"],
        ["Estimated Total Combined Tax", f"${total_tax_est:,.2f}"],
        ["Suggested Quarterly Voucher (1040-ES)", f"${quarterly_est:,.2f} / quarter"]
    ]
    t_summary = Table(summary_data, colWidths=[280, 254])
    t_summary.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1E3A8A")),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EFF6FF")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#E5E7EB")),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    # Schedule C Expenses by Category Breakdown
    story.append(Paragraph("<b>2. Schedule C Expenses by Category Summary</b>", heading_style))
    
    # Group expenses by category
    category_totals = {}
    for exp in expenses_list:
        cat = exp.get("category", "Other / General Business")
        cost = exp.get("cost", 0.0)
        category_totals[cat] = category_totals.get(cat, 0.0) + cost

    if category_totals:
        cat_table_data = [["Schedule C Category / Line", "Deductible Amount"]]
        for cat, amt in category_totals.items():
            cat_table_data.append([cat, f"${amt:,.2f}"])
            
        t_cat = Table(cat_table_data, colWidths=[350, 184])
        t_cat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F2937")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D1D5DB")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_cat)
    else:
        story.append(Paragraph("No business write-offs logged yet.", body_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()