import streamlit as st
import pandas as pd
import urllib.parse
import datetime
import json
import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. ROUTING & PAGE SETUP
st.set_page_config(page_title="Athena Gardens Venue Portal", page_icon="🏰", layout="wide")

query_params = st.query_params
venue_id = query_params.get("vendor", "athena")

# 2. LOAD CONFIGURATION
if not os.path.exists("vendors.json"):
    st.error("Missing 'vendors.json' configuration file.")
    st.stop()

with open("vendors.json", "r") as f:
    config_data = json.load(f)

venues = config_data.get("venues", {})
suppliers = config_data.get("suppliers", {})

if venue_id not in venues:
    st.error(f"Venue portal '{venue_id}' not found on this platform.")
    st.stop()

venue_cfg = venues[venue_id]

# 3. BRANDING HEADER
if os.path.exists(venue_cfg.get("logo_file", "")):
    st.image(venue_cfg["logo_file"], width=130)
else:
    st.title(f"🏛️ {venue_cfg['business_name']}")

st.caption(f"Powered by EventEngine SaaS | {venue_cfg['tagline']}")
st.markdown("---")

# 4. EVENT DETAILS
st.subheader("1. Event Details & Attendance")
col1, col2 = st.columns(2)
with col1:
    event_type = st.selectbox("Event Type:", ["Wedding Ceremony & Reception", "Corporate Function / Gala", "Private Birthday / Anniversary"])
    guest_count = st.number_input("Estimated Guest Count:", min_value=10, max_value=500, value=80, step=10)
with col2:
    event_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
    tables_count = max(1, (guest_count // 8))

formatted_date = event_date.strftime("%B %d, %Y")
quote_num = f"AG-{datetime.datetime.now().strftime('%M%S')}"

st.markdown("---")
st.subheader("2. Select Venue Spaces & Visual Vendor Packages")

cart_items = []
grand_total = 0.0

# A. VENUE SPACE CATALOG
st.markdown(f"#### 🏰 **Venue Spaces ({venue_cfg['business_name']})**")
for idx, item in enumerate(venue_cfg.get("venue_catalog", [])):
    p_name = item["item_name"]
    p_price = float(item["price"])
    p_unit = item["unit"]
    
    label = f"{p_name} — P{p_price:,.2f} ({p_unit})"
    if st.checkbox(label, key=f"v_{idx}"):
        cart_items.append({
            "vendor_type": "Venue",
            "provider": venue_cfg["business_name"],
            "item_name": p_name,
            "unit_price": p_price,
            "qty": 1,
            "total": p_price,
            "whatsapp": venue_cfg["whatsapp"]
        })
        grand_total += p_price

# B. PARTNER SUPPLIER VISUAL CATALOG CARDS
partner_ids = venue_cfg.get("partner_suppliers", [])
for s_id in partner_ids:
    if s_id in suppliers:
        sup = suppliers[s_id]
        st.markdown(f"#### {sup['category']} — *{sup['business_name']}*")
        
        catalog = sup.get("catalog", [])
        cols = st.columns(2)
        
        for idx, item in enumerate(catalog):
            col_target = cols[idx % 2]
            with col_target:
                with st.container(border=True):
                    if item.get("image_url"):
                        # Updated to new Streamlit width parameter syntax
                        st.image(item["image_url"], width="stretch")
                    st.write(f"**{item['item_name']}**")
                    st.write(f"Price: P{item['price']:,.2f} ({item['unit']})")
                    
                    max_limit = item.get("max_qty", 500)
                    raw_default = guest_count if "Guest" in item["unit"] else (tables_count if "Table" in item["unit"] else 1)
                    
                    # FIX: Cap default_qty so it never exceeds max_qty
                    safe_default_qty = min(raw_default, max_limit)
                    
                    qty_selected = st.number_input(
                        f"Quantity ({item['item_name']}):",
                        min_value=1,
                        max_value=max_limit,
                        value=safe_default_qty,
                        key=f"qty_{s_id}_{idx}"
                    )
                    
                    item_total = item["price"] * qty_selected
                    
                    if st.checkbox("☑ Add to Event Cart", key=f"chk_{s_id}_{idx}"):
                        cart_items.append({
                            "vendor_type": sup["category"],
                            "provider": sup["business_name"],
                            "item_name": item["item_name"],
                            "unit_price": item["price"],
                            "qty": qty_selected,
                            "total": item_total,
                            "whatsapp": sup["whatsapp"]
                        })
                        grand_total += item_total
# 5. CART SUMMARY & CHECKOUT
if cart_items:
    st.markdown("---")
    st.subheader("3. Comprehensive Quote Summary")
    
    breakage_deposit = 1500.00
    final_total = grand_total + breakage_deposit
    deposit_due = final_total * 0.50
    
    summary_df = pd.DataFrame(cart_items)[["provider", "item_name", "qty", "total"]]
    summary_df.columns = ["Provider", "Selected Service / Catalog Item", "Qty", "Total (BWP)"]
    st.table(summary_df)
    
    st.write(f"**Subtotal Services:** P{grand_total:,.2f}")
    st.write(f"**Refundable Security & Breakage Deposit:** P{breakage_deposit:,.2f}")
    st.markdown(f"### 💰 **GRAND TOTAL ESTIMATE: P{final_total:,.2f}**")
    st.markdown(f"🔒 **50% COMBINED DEPOSIT TO LOCK DATE: P{deposit_due:,.2f}**")
    
    # 6. GENERATE ALL-IN-ONE PDF QUOTE
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    forest_green = colors.HexColor("#1B4D3E")
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=forest_green)
    
    story.append(Paragraph(f"{venue_cfg['business_name'].upper()} — UNIFIED EVENT QUOTE", title_style))
    story.append(Spacer(1, 8))
    
    meta_text = f"<b>Quote #:</b> {quote_num} | <b>Event Date:</b> {formatted_date} | <b>Guests:</b> {guest_count}"
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    pdf_table_data = [["Provider", "Item Description", "Qty", "Amount (BWP)"]]
    for item in cart_items:
        pdf_table_data.append([item["provider"], item["item_name"], str(item["qty"]), f"P{item['total']:,.2f}"])
    
    pdf_table_data.append(["Venue Deposit", "Refundable Security Deposit", "1", f"P{breakage_deposit:,.2f}"])
    pdf_table_data.append(["TOTAL", "GRAND TOTAL ESTIMATE", "-", f"P{final_total:,.2f}"])
    pdf_table_data.append(["DEPOSIT DUE", "50% RESERVATION DEPOSIT", "-", f"P{deposit_due:,.2f}"])
    
    t = Table(pdf_table_data, colWidths=[120, 220, 40, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), forest_green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor("#E8F5E9")),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t)
    doc.build(story)
    
    st.download_button(
        label="📄 Download Official Unified PDF Quote",
        data=buffer.getvalue(),
        file_name=f"Athena_Gardens_Quote_{quote_num}.pdf",
        mime="application/pdf"
    )
    
    # 7. MULTI-VENDOR WHATSAPP DISPATCH
    st.markdown("---")
    st.subheader("4. Dispatch Order Alerts to Vendors")
    st.info("Click below to send automated booking alerts directly to each selected supplier:")
    
    providers_map = {}
    for item in cart_items:
        p_name = item["provider"]
        if p_name not in providers_map:
            providers_map[p_name] = {"phone": item["whatsapp"], "items": []}
        providers_map[p_name]["items"].append(item)
        
    for p_name, p_data in providers_map.items():
        msg = f"Hello {p_name}! A new booking quote (#{quote_num}) has been created on the Venue Portal:\n\n"
        msg += f"📅 Event Date: {formatted_date}\n"
        msg += f"👥 Guest Count: {guest_count}\n\n"
        msg += "Selected Items from your Catalog:\n"
        
        for i in p_data["items"]:
            msg += f"• {i['item_name']} (Qty: {i['qty']}) — P{i['total']:,.2f}\n"
            
        msg += f"\nPlease confirm date availability for Quote #{quote_num}."
        
        encoded_url = f"https://wa.me/{p_data['phone']}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{encoded_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 18px; border-radius:4px; font-weight:bold; margin-bottom:8px; cursor:pointer;">📲 Dispatch Order to {p_name} via WhatsApp</button></a>', unsafe_allow_html=True)

else:
    st.warning("👈 Select items from the venue or vendor catalogs above to build your event quote.")
