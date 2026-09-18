import streamlit as st
import pandas as pd
import urllib.parse
import datetime
import json
import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. PAGE SETUP
st.set_page_config(page_title="Athena Gardens Booking Portal", page_icon="🏰", layout="wide")

BOOKINGS_FILE = "bookings.json"

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "r") as f:
            return json.load(f)
    return []

def save_booking(new_booking):
    bookings = load_bookings()
    bookings.append(new_booking)
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=2)

if not os.path.exists("vendors.json"):
    st.error("Missing 'vendors.json' configuration file.")
    st.stop()

with open("vendors.json", "r") as f:
    config_data = json.load(f)

venues = config_data.get("venues", {})
all_suppliers = config_data.get("suppliers", {})
venue_cfg = venues.get("athena", {})

# FILTER ACTIVE & PAID VENDORS
today_str = datetime.date.today().strftime("%Y-%m-%d")
suppliers = {}
for s_id, sup in all_suppliers.items():
    sub = sup.get("subscription", {})
    if sub.get("status") == "ACTIVE" and sub.get("paid_until", "") >= today_str:
        suppliers[s_id] = sup

# SIDEBAR ROUTING (Client Wizard vs Sub-Vendor Subscription Portal)
st.sidebar.title("📌 Portal Navigation")
view_mode = st.sidebar.radio("Go to:", ["Client Booking Wizard", "Sub-Vendor Payment Portal"])

if view_mode == "Sub-Vendor Payment Portal":
    st.title("💳 Sub-Vendor Subscription Portal")
    st.write("Manage your listing status and pay monthly platform fees.")
    
    vendor_id = st.selectbox("Select Your Business:", list(all_suppliers.keys()))
    vendor = all_suppliers[vendor_id]
    sub = vendor.get("subscription", {})
    
    st.info(f"**Business Name:** {vendor['business_name']}")
    st.write(f"**Current Status:** `{sub.get('status', 'INACTIVE')}`")
    st.write(f"**Paid Until:** `{sub.get('paid_until', 'N/A')}`")
    st.write(f"**Monthly Listing Fee:** P{sub.get('monthly_fee_bwp', 500):,.2f}")
    
    if st.button("💳 Pay Listing Fee Online"):
        pay_url = f"https://checkout.paystack.com/pay/{vendor_id}"
        st.markdown(f"👉 [Click here to complete payment on Paystack]({pay_url})")
        st.caption("Once payment is completed, your catalog items will instantly activate on the client booking wizard.")

else:
    # CLIENT BOOKING WIZARD FLOW
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "client_info" not in st.session_state:
        st.session_state.client_info = {}
    if "selected_suppliers" not in st.session_state:
        st.session_state.selected_suppliers = []

    # BRANDING HEADER
    logo_path = venue_cfg.get("logo_file", "")
    if logo_path.startswith("http") or os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.title(f"🏛️ {venue_cfg['business_name']}")

    st.caption(f"Powered by EventEngine SaaS | {venue_cfg['tagline']}")
    st.progress(st.session_state.step / 5)

    # STEP 1: CLIENT DETAILS & DATE CHECK
    if st.session_state.step == 1:
        st.subheader("Step 1: Client Information & Event Date")
        
        with st.form("client_form"):
            c_name = st.text_input("Full Name:")
            c_email = st.text_input("Email Address:")
            c_phone = st.text_input("WhatsApp / Phone Number:")
            e_type = st.selectbox("Event Type:", ["Wedding Ceremony & Reception", "Corporate Function", "Birthday / Anniversary"])
            e_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
            e_guests = st.number_input("Estimated Guest Count:", min_value=10, max_value=500, value=80, step=10)
            
            submitted = st.form_submit_button("Check Date Availability & Continue ➔")
            
            if submitted:
                if not c_name or not c_phone or not c_email:
                    st.error("Please fill in all contact details.")
                else:
                    existing_bookings = load_bookings()
                    locked_dates = [b["event_date"] for b in existing_bookings if b.get("status") == "PAID"]
                    
                    selected_date_str = e_date.strftime("%Y-%m-%d")
                    if selected_date_str in locked_dates:
                        st.error(f"❌ Sorry! Athena Gardens is fully booked and locked on {selected_date_str}. Please choose another date.")
                    else:
                        st.session_state.client_info = {
                            "name": c_name, "email": c_email, "phone": c_phone,
                            "event_type": e_type, "date": selected_date_str, "guests": e_guests
                        }
                        st.session_state.step = 2
                        st.rerun()

    # STEP 2: VENUE SELECTION
    elif st.session_state.step == 2:
        st.subheader("Step 2: Select Venue Space")
        client = st.session_state.client_info
        st.info(f"Booking for **{client['guests']} Guests** on **{client['date']}**")
        
        venue_catalog = venue_cfg.get("venue_catalog", [])
        selected_space = st.radio("Choose Venue Area:", options=[f"{v['item_name']} (P{v['price']:,.2f})" for v in venue_catalog])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅ Back"):
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("Next: Choose Vendors ➔"):
                chosen_item = next(v for v in venue_catalog if v["item_name"] in selected_space)
                st.session_state.cart = [{
                    "provider": venue_cfg["business_name"],
                    "item_name": chosen_item["item_name"],
                    "qty": 1,
                    "price": chosen_item["price"],
                    "total": chosen_item["price"],
                    "whatsapp": venue_cfg["whatsapp"]
                }]
                st.session_state.step = 3
                st.rerun()

    # STEP 3: VENDOR CATEGORY SELECTION
    elif st.session_state.step == 3:
        st.subheader("Step 3: Select Required Vendor Categories")
        
        partner_ids = venue_cfg.get("partner_suppliers", [])
        available_suppliers = {suppliers[s_id]["category"]: s_id for s_id in partner_ids if s_id in suppliers}
        
        if not available_suppliers:
            st.warning("No active third-party suppliers are currently available.")
            selected_cats = []
        else:
            selected_cats = st.multiselect("Select Categories Needed:", list(available_suppliers.keys()), default=list(available_suppliers.keys()))
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅ Back"):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("Configure Selected Vendors ➔"):
                st.session_state.selected_suppliers = [available_suppliers[cat] for cat in selected_cats]
                st.session_state.step = 4
                st.rerun()

    # STEP 4: ITEM SELECTION & INCLUSIONS
    elif st.session_state.step == 4:
        st.subheader("Step 4: Customize Vendor Items & Menus")
        
        if not st.session_state.selected_suppliers:
            st.info("No additional vendor categories selected. Proceed to review.")
        else:
            for s_id in st.session_state.selected_suppliers:
                sup = suppliers[s_id]
                st.markdown(f"### 🛍️ {sup['category']} — *{sup['business_name']}*")
                
                for idx, item in enumerate(sup.get("catalog", [])):
                    with st.container(border=True):
                        col_img, col_det = st.columns([1, 2])
                        with col_img:
                            if item.get("image_url"):
                                st.image(item["image_url"], width="stretch")
                        with col_det:
                            st.write(f"### {item['item_name']}")
                            st.write(f"**Price:** P{item['price']:,.2f} ({item['unit']})")
                            
                            if "inclusions" in item:
                                st.write("**Package Inclusions:**")
                                for inc in item["inclusions"]:
                                    st.write(f"• {inc}")
                            
                            add_item = st.checkbox(f"Include '{item['item_name']}'", key=f"sel_{s_id}_{idx}")
                            if add_item:
                                max_limit = item.get("max_qty", 500)
                                raw_default = st.session_state.client_info["guests"] if "Guest" in item["unit"] else 1
                                safe_default = min(raw_default, max_limit)
                                
                                qty = st.number_input(f"Quantity:", min_value=1, max_value=max_limit, value=safe_default, key=f"q_{s_id}_{idx}")
                                item_total = item["price"] * qty
                                
                                # Add or Update Cart Item
                                st.session_state.cart = [c for c in st.session_state.cart if c["item_name"] != item["item_name"]]
                                st.session_state.cart.append({
                                    "provider": sup["business_name"],
                                    "item_name": item["item_name"],
                                    "qty": qty,
                                    "price": item["price"],
                                    "total": item_total,
                                    "whatsapp": sup["whatsapp"]
                                })

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅ Back"):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("Review Full Quote ➔"):
                st.session_state.step = 5
                st.rerun()

    # STEP 5: QUOTE SUMMARY, PDF & LOCKING
    elif st.session_state.step == 5:
        st.subheader("Step 5: Final Review & Booking Confirmation")
        
        client = st.session_state.client_info
        st.success(f"**Client:** {client['name']} | **Phone:** {client['phone']} | **Date:** {client['date']} | **Guests:** {client['guests']}")
        
        df = pd.DataFrame(st.session_state.cart)[["provider", "item_name", "qty", "total"]]
        df.columns = ["Provider", "Item Description", "Qty", "Total (BWP)"]
        st.table(df)
        
        subtotal = sum(i["total"] for i in st.session_state.cart)
        deposit = subtotal * 0.50
        
        st.write(f"**Subtotal Services:** P{subtotal:,.2f}")
        st.markdown(f"### 💰 **50% Deposit to Lock Date: P{deposit:,.2f}**")
        
        # GENERATE PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []
        
        forest_green = colors.HexColor("#1B4D3E")
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=forest_green)
        
        story.append(Paragraph(f"{venue_cfg['business_name'].upper()} — UNIFIED QUOTE", title_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Client:</b> {client['name']} | <b>Date:</b> {client['date']} | <b>Guests:</b> {client['guests']}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        pdf_table_data = [["Provider", "Item Description", "Qty", "Amount (BWP)"]]
        for item in st.session_state.cart:
            pdf_table_data.append([item["provider"], item["item_name"], str(item["qty"]), f"P{item['total']:,.2f}"])
        pdf_table_data.append(["TOTAL", "GRAND TOTAL ESTIMATE", "-", f"P{subtotal:,.2f}"])
        pdf_table_data.append(["DEPOSIT DUE", "50% RESERVATION DEPOSIT", "-", f"P{deposit:,.2f}"])
        
        t = Table(pdf_table_data, colWidths=[120, 220, 40, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), forest_green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor("#E8F5E9")),
        ]))
        story.append(t)
        doc.build(story)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download Official PDF Quote",
                data=buffer.getvalue(),
                file_name=f"Athena_Gardens_Quote_{client['name'].replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        with col2:
            if st.button("🔒 Lock Date & Save Reservation"):
                booking_record = {
                    "booking_id": f"AG-{datetime.datetime.now().strftime('%M%S')}",
                    "client_name": client["name"],
                    "client_phone": client["phone"],
                    "client_email": client["email"],
                    "event_date": client["date"],
                    "guests": client["guests"],
                    "total_amount": subtotal,
                    "status": "PAID",
                    "items": st.session_state.cart
                }
                save_booking(booking_record)
                st.balloons()
                st.success("✅ Booking confirmed! This date is now locked in the calendar.")
