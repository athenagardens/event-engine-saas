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

# 1. PAGE SETUP & CONFIG
st.set_page_config(page_title="Athena Gardens — Event Booking Portal", page_icon="🏰", layout="wide")

# Persistent Storage for Bookings & Reports
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
suppliers = config_data.get("suppliers", {})
venue_cfg = venues.get("athena", {})

# Session State Initializer for Step-by-Step Flow
if "step" not in st.session_state:
    st.session_state.step = 1
if "cart" not in st.session_state:
    st.session_state.cart = []
if "client_info" not in st.session_state:
    st.session_state.client_info = {}
if "selected_suppliers" not in st.session_state:
    st.session_state.selected_suppliers = []

# Header Branding
st.title("🏛️ Athena Gardens Event Booking")
st.caption("Custom Event & Multi-Vendor Package Creator")
st.markdown("---")

# Navigation Progress Bar
st.progress(st.session_state.step / 5)

# ---------------------------------------------------------
# STEP 1: CLIENT DETAILS & DATE LOCK CHECK
# ---------------------------------------------------------
if st.session_state.step == 1:
    st.subheader("Step 1: Your Details & Event Date")
    
    with st.form("client_form"):
        c_name = st.text_input("Full Name:")
        c_email = st.text_input("Email Address:")
        c_phone = st.text_input("WhatsApp / Phone Number:")
        e_type = st.selectbox("Event Type:", ["Wedding", "Corporate Gala", "Birthday Party", "Anniversary"])
        e_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
        e_guests = st.number_input("Number of Guests:", min_value=10, max_value=500, value=80, step=10)
        
        submitted = st.form_submit_button("Check Availability & Continue ➔")
        
        if submitted:
            if not c_name or not c_phone or not c_email:
                st.error("Please fill in all contact details.")
            else:
                # Check for locked/paid dates
                existing_bookings = load_bookings()
                locked_dates = [b["event_date"] for b in existing_bookings if b.get("status") == "PAID"]
                
                selected_date_str = e_date.strftime("%Y-%m-%d")
                if selected_date_str in locked_dates:
                    st.error(f"❌ Sorry! Athena Gardens is fully booked and locked for {selected_date_str}. Please choose another date.")
                else:
                    st.session_state.client_info = {
                        "name": c_name, "email": c_email, "phone": c_phone,
                        "event_type": e_type, "date": selected_date_str, "guests": e_guests
                    }
                    st.session_state.step = 2
                    st.rerun()

# ---------------------------------------------------------
# STEP 2: VENUE SPACE SELECTION
# ---------------------------------------------------------
elif st.session_state.step == 2:
    st.subheader("Step 2: Select Your Venue Space")
    st.info(f"Booking for **{st.session_state.client_info['guests']} Guests** on **{st.session_state.client_info['date']}**")
    
    venue_catalog = venue_cfg.get("venue_catalog", [])
    selected_space = st.radio("Choose Venue Area:", options=[v["item_name"] + f" (P{v['price']:,.2f})" for v in venue_catalog])
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅ Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Next: Choose Vendors ➔"):
            # Add chosen venue space to cart
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

# ---------------------------------------------------------
# STEP 3: CHOOSE VENDOR CATEGORIES
# ---------------------------------------------------------
elif st.session_state.step == 3:
    st.subheader("Step 3: Which Services Do You Need?")
    st.write("Select the supplier types you want to include in your booking:")
    
    available_suppliers = venue_cfg.get("partner_suppliers", [])
    supplier_options = {suppliers[s_id]["category"]: s_id for s_id in available_suppliers if s_id in suppliers}
    
    selected_cats = st.multiselect("Select Categories:", list(supplier_options.keys()), default=list(supplier_options.keys()))
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅ Back"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Configure Selected Vendors ➔"):
            st.session_state.selected_suppliers = [supplier_options[cat] for cat in selected_cats]
            st.session_state.step = 4
            st.rerun()

# ---------------------------------------------------------
# STEP 4: VENDOR-BY-VENDOR CUSTOMIZATION
# ---------------------------------------------------------
elif st.session_state.step == 4:
    st.subheader("Step 4: Select Menu & Vendor Items")
    
    if not st.session_state.selected_suppliers:
        st.write("No additional suppliers selected.")
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
                        
                        # Inclusions List (Cutlery, Glassware, Menu Details)
                        if "inclusions" in item:
                            st.write("**What's Included:**")
                            for inc in item["inclusions"]:
                                st.write(f"• {inc}")
                        
                        add_item = st.checkbox(f"Add '{item['item_name']}' to quote", key=f"select_{s_id}_{idx}")
                        if add_item:
                            qty = st.number_input(f"Quantity:", min_value=1, value=st.session_state.client_info["guests"] if "Guest" in item["unit"] else 1, key=f"q_{s_id}_{idx}")
                            
                            # Update Cart
                            item_total = item["price"] * qty
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
        if st.button("Review Full Quote & Reserve ➔"):
            st.session_state.step = 5
            st.rerun()

# ---------------------------------------------------------
# STEP 5: SUMMARY, PDF QUOTE & LOCK RESERVATION
# ---------------------------------------------------------
elif st.session_state.step == 5:
    st.subheader("Step 5: Final Review & Confirmation")
    
    client = st.session_state.client_info
    st.success(f"**Client:** {client['name']} | **Phone:** {client['phone']} | **Date:** {client['date']} | **Guests:** {client['guests']}")
    
    # Cart Summary Table
    df = pd.DataFrame(st.session_state.cart)[["provider", "item_name", "qty", "total"]]
    df.columns = ["Provider", "Item Description", "Qty", "Total (BWP)"]
    st.table(df)
    
    subtotal = sum(i["total"] for i in st.session_state.cart)
    deposit = subtotal * 0.50
    
    st.write(f"**Subtotal:** P{subtotal:,.2f}")
    st.markdown(f"### 💰 **50% Deposit to Lock Date: P{deposit:,.2f}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔒 Lock Date & Save Reservation"):
            booking_record = {
                "booking_id": f"AG-{datetime.datetime.now().strftime('%M%S')}",
                "client_name": client["name"],
                "client_phone": client["phone"],
                "client_email": client["email"],
                "event_date": client["date"],
                "guests": client["guests"],
                "total_amount": subtotal,
                "status": "PAID",  # Locks the calendar date
                "items": st.session_state.cart
            }
            save_booking(booking_record)
            st.balloons()
            st.success("✅ Date is officially booked and locked in the calendar!")
            
    with col2:
        if st.button("🔄 Start New Booking"):
            st.session_state.step = 1
            st.session_state.cart = []
            st.rerun()
