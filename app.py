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
st.set_page_config(page_title="EventEngine SaaS Engine", page_icon="🏰", layout="wide")

CONFIG_FILE = "vendors.json"
BOOKINGS_FILE = "bookings.json"

# Load or Initialize Configuration Data
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"venues": {}, "suppliers": {}}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

config_data = load_config()
venues = config_data.get("venues", {})
all_suppliers = config_data.get("suppliers", {})

# PRE-CALCULATE ACTIVE/PAID SUPPLIERS (FIXES LINE 344 SCOPE ERROR)
today_str = datetime.date.today().strftime("%Y-%m-%d")
active_suppliers = {}
for s_id, sup in all_suppliers.items():
    sub = sup.get("subscription", {})
    if sub.get("status") == "ACTIVE" and sub.get("paid_until", "") >= today_str:
        active_suppliers[s_id] = sup

# 2. GLOBAL ROUTING (URL Queries & Sidebar Navigation)
query_params = st.query_params
active_venue_id = query_params.get("vendor", "athena")

st.sidebar.title("🌐 SaaS Portal Directory")
route = st.sidebar.radio("Navigation:", ["Client Booking Portal", "Venue & Vendor Registration", "SaaS Master Admin"])

# ---------------------------------------------------------
# ROUTE 1: SELF-SERVICE ONBOARDING (NEW VENUES & VENDORS)
# ---------------------------------------------------------
if route == "Venue & Vendor Registration":
    st.title("🚀 Join the EventEngine SaaS Platform")
    st.write("Register your venue or supplier business to accept client bookings online.")
    
    reg_type = st.radio("I want to register as a:", ["Primary Venue (e.g., Garden, Hall, Estate)", "Value-Add Supplier (e.g., Caterer, Florist, Decor)"])
    
    if reg_type == "Primary Venue (e.g., Garden, Hall, Estate)":
        st.subheader("🏛️ Register Your Venue")
        with st.form("venue_reg_form"):
            v_id = st.text_input("Unique ID (e.g., royaloak):").lower().strip()
            v_name = st.text_input("Business Name:")
            v_tagline = st.text_input("Tagline:")
            v_logo = st.text_input("Direct Logo Image URL:")
            v_phone = st.text_input("WhatsApp Number (with country code):")
            
            p_option = st.selectbox("Select SaaS Subscription Tier:", ["Starter Tier — P1,500/month", "Enterprise Tier — P3,500/month"])
            
            submitted = st.form_submit_button("Register & Proceed to Payment 💳")
            if submitted:
                if v_id and v_name:
                    venues[v_id] = {
                        "business_name": v_name,
                        "tagline": v_tagline,
                        "logo_file": v_logo or "https://raw.githubusercontent.com/athenagardens/event-engine-saas/main/logos/athena_logo.png",
                        "whatsapp": v_phone,
                        "subscription": {"status": "ACTIVE", "paid_until": "2026-12-31"},
                        "venue_catalog": [{"item_id": f"{v_id}_01", "item_name": "Standard Lawn Space", "price": 5000.0, "unit": "Per Day"}],
                        "partner_suppliers": []
                    }
                    config_data["venues"] = venues
                    save_config(config_data)
                    st.success(f"✅ Venue '{v_name}' successfully created!")
                    st.info(f"Your Portal Link: `https://event-engine-saas.streamlit.app/?vendor={v_id}`")
                else:
                    st.error("Please fill in required fields.")

    else:
        st.subheader("🛍️ Register as a Value-Add Supplier")
        with st.form("supplier_reg_form"):
            s_id = st.text_input("Unique Supplier ID (e.g., royal_catering):").lower().strip()
            s_name = st.text_input("Business Name:")
            s_cat = st.selectbox("Category:", ["Catering & Buffets", "Decor & Styling", "Sound & Lighting", "Photography"])
            s_phone = st.text_input("WhatsApp Number:")
            
            item_name = st.text_input("First Package / Item Name:")
            item_price = st.number_input("Item Price (BWP):", min_value=10.0, value=150.0)
            item_unit = st.selectbox("Unit Type:", ["Per Guest", "Per Table", "Per Unit", "Per Day"])
            
            submitted = st.form_submit_button("Register & Pay Monthly Listing Fee (P500/mo) 💳")
            if submitted:
                if s_id and s_name:
                    all_suppliers[s_id] = {
                        "business_name": s_name,
                        "category": s_cat,
                        "whatsapp": s_phone,
                        "subscription": {"status": "ACTIVE", "paid_until": "2026-12-31", "monthly_fee_bwp": 500.0},
                        "catalog": [{"item_id": f"{s_id}_01", "item_name": item_name, "price": item_price, "unit": item_unit}]
                    }
                    config_data["suppliers"] = all_suppliers
                    save_config(config_data)
                    st.success(f"✅ Supplier '{s_name}' registered successfully!")
                else:
                    st.error("Please complete all required fields.")

# ---------------------------------------------------------
# ROUTE 2: MASTER SAAS ADMIN CONSOLE
# ---------------------------------------------------------
# ---------------------------------------------------------
# ROUTE 2: MASTER SAAS ADMIN CONSOLE
# ---------------------------------------------------------
elif route == "SaaS Master Admin":
    st.title("🔑 Master SaaS Platform Admin")
    
    with st.form("admin_login_form"):
        pin = st.text_input("Enter Admin Security PIN:", type="password")
        login_submitted = st.form_submit_button("Access Console 🔓")
    
    if login_submitted or pin == "admin2026":
        if pin == "admin2026":
            st.success("🔓 Access Granted!")
            st.subheader("📊 Platform Financial Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Venues", len(venues))
            col2.metric("Active Suppliers", len(all_suppliers))
            col3.metric("Est. Monthly Revenue", f"P{len(venues)*1500 + len(all_suppliers)*500:,.2f}")
            
            st.markdown("---")
            st.subheader("🏢 Registered Venues")
            st.json(venues)
            
            st.subheader("🛍️ Registered Suppliers")
            st.json(all_suppliers)
            
            st.subheader("📅 Stored Customer Bookings")
            st.json(load_bookings())
        else:
            st.error("❌ Incorrect Admin PIN. Please try again.")
# ---------------------------------------------------------
# ROUTE 3: CLIENT BOOKING WIZARD (DYNAMIC FOR EACH VENUE)
# ---------------------------------------------------------
else:
    venue_cfg = venues.get(active_venue_id, {
        "business_name": "Athena Gardens Venue",
        "tagline": "Luxury Outdoor Event & Wedding Spaces",
        "logo_file": "https://raw.githubusercontent.com/athenagardens/event-engine-saas/main/logos/athena_logo.png",
        "whatsapp": "26774501880",
        "venue_catalog": [{"item_name": "Standard Garden Lawn", "price": 5000.00, "unit": "Per Day"}],
        "partner_suppliers": list(active_suppliers.keys())
    })

    # Session State Setup
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "client_info" not in st.session_state:
        st.session_state.client_info = {}
    if "selected_suppliers" not in st.session_state:
        st.session_state.selected_suppliers = []

    # Venue Branding Header
    logo_path = venue_cfg.get("logo_file", "")
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        if logo_path.startswith("http") or os.path.exists(logo_path):
            st.image(logo_path, width=130)
        else:
            st.write("🏛️")
    with col_title:
        st.title(venue_cfg.get("business_name"))
        st.caption(f"Powered by EventEngine SaaS | {venue_cfg.get('tagline')}")

    st.markdown("---")
    st.progress(st.session_state.step / 5)

    # STEP 1: CLIENT DETAILS & DATE LOCK
    if st.session_state.step == 1:
        st.subheader("Step 1: Event Details & Availability Check")
        with st.form("client_form"):
            c_name = st.text_input("Full Name:")
            c_email = st.text_input("Email Address:")
            c_phone = st.text_input("WhatsApp / Phone Number:")
            e_type = st.selectbox("Event Type:", ["Wedding Ceremony & Reception", "Corporate Function", "Birthday Party"])
            e_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
            e_guests = st.number_input("Estimated Guest Count:", min_value=10, max_value=500, value=80, step=10)
            
            submitted = st.form_submit_button("Check Availability & Continue ➔")
            if submitted:
                if not c_name or not c_phone or not c_email:
                    st.error("Please fill in required fields.")
                else:
                    locked_dates = [b["event_date"] for b in load_bookings() if b.get("status") == "PAID" and b.get("venue_id") == active_venue_id]
                    selected_date_str = e_date.strftime("%Y-%m-%d")
                    
                    if selected_date_str in locked_dates:
                        st.error(f"❌ Sorry! {venue_cfg['business_name']} is fully booked and locked on {selected_date_str}.")
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
        selected_space = st.radio("Choose Area:", options=[f"{v['item_name']} (P{v['price']:,.2f})" for v in venue_catalog])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅ Back"):
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("Next: Select Vendors ➔"):
                chosen_item = next(v for v in venue_catalog if v["item_name"] in selected_space)
                st.session_state.cart = [{
                    "provider": venue_cfg["business_name"],
                    "item_name": chosen_item["item_name"],
                    "qty": 1,
                    "price": chosen_item["price"],
                    "total": chosen_item["price"],
                    "whatsapp": venue_cfg.get("whatsapp", "")
                }]
                st.session_state.step = 3
                st.rerun()

    # STEP 3: SUPPLIER CATEGORIES
    elif st.session_state.step == 3:
        st.subheader("Step 3: Select Required Vendor Categories")
        partner_ids = venue_cfg.get("partner_suppliers", list(active_suppliers.keys()))
        available_suppliers = {active_suppliers[s_id]["category"]: s_id for s_id in partner_ids if s_id in active_suppliers}
        
        if not available_suppliers:
            st.warning("No third-party suppliers are currently registered for this venue.")
            selected_cats = []
        else:
            selected_cats = st.multiselect("Select Categories Needed:", list(available_suppliers.keys()), default=list(available_suppliers.keys()))
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅ Back"):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("Customize Vendors ➔"):
                st.session_state.selected_suppliers = [available_suppliers[cat] for cat in selected_cats]
                st.session_state.step = 4
                st.rerun()

    # STEP 4: CUSTOMIZE SUPPLIER PACKAGES
    elif st.session_state.step == 4:
        st.subheader("Step 4: Customize Vendor Items & Services")
        if not st.session_state.selected_suppliers:
            st.info("No suppliers selected. Proceed to review.")
        else:
            for s_id in st.session_state.selected_suppliers:
                sup = active_suppliers[s_id]
                st.markdown(f"### 🛍️ {sup['category']} — *{sup['business_name']}*")
                
                for idx, item in enumerate(sup.get("catalog", [])):
                    with st.container(border=True):
                        st.write(f"### {item['item_name']}")
                        st.write(f"**Price:** P{item['price']:,.2f} ({item['unit']})")
                        
                        add_item = st.checkbox(f"Include '{item['item_name']}'", key=f"sel_{s_id}_{idx}")
                        if add_item:
                            max_limit = item.get("max_qty", 500)
                            raw_default = st.session_state.client_info["guests"] if "Guest" in item["unit"] else 1
                            qty = st.number_input("Quantity:", min_value=1, max_value=max_limit, value=min(raw_default, max_limit), key=f"q_{s_id}_{idx}")
                            
                            st.session_state.cart = [c for c in st.session_state.cart if c["item_name"] != item["item_name"]]
                            st.session_state.cart.append({
                                "provider": sup["business_name"],
                                "item_name": item["item_name"],
                                "qty": qty,
                                "price": item["price"],
                                "total": item["price"] * qty,
                                "whatsapp": sup.get("whatsapp", "")
                            })

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅ Back"):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("Review Final Quote ➔"):
                st.session_state.step = 5
                st.rerun()

    # STEP 5: REVIEW, PDF & DATE LOCKING
    elif st.session_state.step == 5:
        st.subheader("Step 5: Final Review & Date Lock")
        client = st.session_state.client_info
        st.success(f"**Client:** {client['name']} | **Date:** {client['date']} | **Guests:** {client['guests']}")
        
        df = pd.DataFrame(st.session_state.cart)[["provider", "item_name", "qty", "total"]]
        df.columns = ["Provider", "Item Description", "Qty", "Total (BWP)"]
        st.table(df)
        
        subtotal = sum(i["total"] for i in st.session_state.cart)
        deposit = subtotal * 0.50
        st.markdown(f"### 💰 **50% Deposit to Lock Date: P{deposit:,.2f}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔒 Lock Date & Finalize Reservation"):
                save_booking({
                    "venue_id": active_venue_id,
                    "booking_id": f"EV-{datetime.datetime.now().strftime('%M%S')}",
                    "client_name": client["name"],
                    "client_phone": client["phone"],
                    "event_date": client["date"],
                    "total_amount": subtotal,
                    "status": "PAID",
                    "items": st.session_state.cart
                })
                st.balloons()
                st.success("✅ Booking confirmed! This date is now locked in the venue calendar.")
        with col2:
            if st.button("🔄 Start New Booking"):
                st.session_state.step = 1
                st.session_state.cart = []
                st.rerun()
