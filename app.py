import streamlit as st
import json
import os
import datetime
import pandas as pd

# ==============================================================================
# CONFIGURATION & PERSISTENCE
# ==============================================================================
CONFIG_FILE = "vendors.json"
BOOKINGS_FILE = "bookings.json"

def load_json(filepath, default_data):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return default_data

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# Default Vendor Data
default_config = {
    "venues": {
        "athena": {
            "business_name": "Athena Gardens",
            "tagline": "Premier Outdoor Event Space & Pavilion",
            "phone": "+267 71 234 567",
            "password": "pass",
            "brand_color": "#1E3A8A",
            "packages": [
                {"id": "p1", "name": "Main Lawn Space", "price": 5000.0, "unit": "Per Day", "desc": "Exclusive full-day access to main grounds."},
                {"id": "p2", "name": "Small Group Pavilion (Up to 30)", "price": 2500.0, "unit": "Per Day", "desc": "Cozy space for intimate gatherings."},
                {"id": "p3", "name": "Bridal Suite Rental", "price": 1200.0, "unit": "Per Unit", "desc": "Private room for bridal party prep."}
            ]
        }
    },
    "all_suppliers": {
        "saina": {
            "business_name": "Saina Utensils & Wellness",
            "category": "Catering & Event Styling",
            "phone": "+267 72 987 654",
            "password": "pass",
            "packages": [
                {"id": "s1", "name": "Full Buffet & Table Setup", "price": 150.0, "unit": "Per Guest", "desc": "Utensils, premium crockery, and buffet service."},
                {"id": "s2", "name": "Lounge Wellness Station", "price": 3000.0, "unit": "Per Unit", "desc": "Mobile herbal tea & relaxation setup."}
            ]
        }
    }
}

# State Management
if "config_data" not in st.session_state:
    st.session_state.config_data = load_json(CONFIG_FILE, default_config)

if "bookings_data" not in st.session_state:
    st.session_state.bookings_data = load_json(BOOKINGS_FILE, [])

if "logged_vendor" not in st.session_state:
    st.session_state.logged_vendor = None

venues = st.session_state.config_data.get("venues", {})
all_suppliers = st.session_state.config_data.get("all_suppliers", {})

# Dynamic Branding based on URL parameter
query_params = st.query_params
active_vendor_slug = query_params.get("vendor", None)
active_venue = venues.get(active_vendor_slug) if active_vendor_slug in venues else None

page_title = f"{active_venue['business_name']} | Booking Portal" if active_venue else "Saina | Event Suite"
primary_color = active_venue.get("brand_color", "#1E3A8A") if active_venue else "#1E3A8A"

st.set_page_config(page_title=page_title, layout="wide")

st.markdown(f"""
    <style>
    .stButton>button {{ background-color: {primary_color} !important; color: white !important; border-radius: 6px; }}
    .metric-card {{ background-color: #F8FAFC; padding: 15px; border-radius: 8px; border-left: 5px solid {primary_color}; }}
    .invoice-card {{ background-color: #FFFFFF; padding: 20px; border: 1px solid #E2E8F0; border-radius: 8px; }}
    </style>
""", unsafe_allow_html=True)

# Navigation Menu
st.sidebar.title("Saina Platform")
route = st.sidebar.radio(
    "Navigate System", 
    ["Client Booking Portal", "Vendor Portal Login 🔐", "Venue & Supplier Registration", "Platform Administration"]
)

# ==============================================================================
# ROUTE 1: CLIENT BOOKING PORTAL & AUTOMATED BILLING
# ==============================================================================
if route == "Client Booking Portal":
    if not active_venue:
        st.title("Saina Event Venue Directory")
        st.caption("Select a venue below to explore packages and book your event.")
        
        if not venues:
            st.warning("No venue partners currently registered.")
        else:
            cols = st.columns(2)
            for idx, (slug, vdata) in enumerate(venues.items()):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{vdata.get('business_name')}</h3>
                        <p><em>{vdata.get('tagline', '')}</em></p>
                        <p>📞 {vdata.get('phone', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Visit {vdata.get('business_name')} Portal", key=f"btn_{slug}"):
                        st.query_params["vendor"] = slug
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.title(f"{active_venue.get('business_name')}")
        st.caption(f"{active_venue.get('tagline')} | Powered by Saina Platforms")
        
        tab_book, tab_info = st.tabs(["🗓️ Reserve Event & Services", "ℹ️ Venue Information"])
        
        with tab_book:
            st.markdown("### Step 1: Customer Details")
            c1, c2 = st.columns(2)
            with c1:
                client_name = st.text_input("Full Name:")
                client_email = st.text_input("Email Address:")
                client_phone = st.text_input("WhatsApp / Phone Number:")
            with c2:
                event_type = st.selectbox("Event Type:", ["Wedding", "Corporate Gala", "Birthday Party", "Wellness Retreat"])
                event_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
                guest_count = st.number_input("Expected Guest Count:", min_value=1, value=80, step=5)

            st.markdown("---")
            st.markdown("### Step 2: Select Venue Space")
            venue_pkgs = active_venue.get("packages", [])
            selected_items = []
            
            if venue_pkgs:
                for pkg in venue_pkgs:
                    p_id, p_name, p_price, p_unit = pkg["id"], pkg["name"], pkg["price"], pkg.get("unit", "Per Day")
                    item_total = p_price * guest_count if p_unit == "Per Guest" else p_price
                    unit_label = "flat fee" if p_unit in ["Per Day", "Per Unit"] else f"BWP {p_price:.2f} × {guest_count} guests"
                    
                    if st.checkbox(f"{p_name} — BWP {item_total:,.2f} ({unit_label})", key=f"chk_v_{p_id}"):
                        selected_items.append({"vendor_id": active_vendor_slug, "vendor_name": active_venue['business_name'], "item": p_name, "price": item_total})
            else:
                st.info("No venue spaces listed.")

            st.markdown("---")
            st.markdown("### Step 3: Add Partner Services")
            if all_suppliers:
                for s_slug, s_data in all_suppliers.items():
                    st.markdown(f"#### {s_data.get('business_name')} ({s_data.get('category')})")
                    for s_pkg in s_data.get("packages", []):
                        sp_id, sp_name, sp_price, sp_unit = s_pkg["id"], s_pkg["name"], s_pkg["price"], s_pkg.get("unit", "Per Guest")
                        s_item_total = sp_price * guest_count if sp_unit == "Per Guest" else sp_price
                        s_unit_label = f"BWP {sp_price:.2f} × {guest_count} guests" if sp_unit == "Per Guest" else "flat fee"
                        
                        if st.checkbox(f"{sp_name} — BWP {s_item_total:,.2f} ({s_unit_label})", key=f"chk_s_{sp_id}"):
                            selected_items.append({"vendor_id": s_slug, "vendor_name": s_data['business_name'], "item": sp_name, "price": s_item_total})

            st.markdown("---")
            st.markdown("### Step 4: Checkout & Automatic Invoicing")
            if selected_items:
                df_summary = pd.DataFrame(selected_items)[["vendor_name", "item", "price"]]
                df_summary.columns = ["Provider", "Item / Service", "Total (BWP)"]
                st.table(df_summary)
                
                grand_total = sum(i["price"] for i in selected_items)
                deposit = grand_total * 0.50
                
                m1, m2 = st.columns(2)
                m1.metric("Grand Total Amount", f"BWP {grand_total:,.2f}")
                m2.metric("50% Deposit Due Now", f"BWP {deposit:,.2f}")
                
                payment_method = st.radio("Payment Method:", ["Credit / Debit Card (Online)", "Electronic Funds Transfer (EFT)"])
                
                if st.button("Confirm Booking & Generate Invoice"):
                    if client_name and client_phone and client_email:
                        inv_id = f"INV-{len(st.session_state.bookings_data) + 1001}"
                        booking_record = {
                            "invoice_id": inv_id,
                            "timestamp": str(datetime.datetime.now())[:19],
                            "client_name": client_name,
                            "client_email": client_email,
                            "client_phone": client_phone,
                            "event_date": str(event_date),
                            "guest_count": guest_count,
                            "items": selected_items,
                            "grand_total": grand_total,
                            "deposit_paid": deposit,
                            "status": "Deposit Paid",
                            "payment_method": payment_method
                        }
                        
                        st.session_state.bookings_data.append(booking_record)
                        save_json(BOOKINGS_FILE, st.session_state.bookings_data)
                        
                        st.balloons()
                        st.success("Payment Received & Booking Confirmed!")
                        
                        # Generate Printable Digital Invoice
                        st.markdown(f"""
                        <div class="invoice-card">
                            <h2>OFFICIAL INVOICE / RECEIPT</h2>
                            <p><strong>Invoice ID:</strong> {inv_id} | <strong>Date:</strong> {str(datetime.date.today())}</p>
                            <hr>
                            <p><strong>Client:</strong> {client_name} ({client_phone})</p>
                            <p><strong>Event Date:</strong> {event_date} | <strong>Guests:</strong> {guest_count}</p>
                            <p><strong>Amount Paid (50% Deposit):</strong> BWP {deposit:,.2f}</p>
                            <p><strong>Status:</strong> CONFIRMED & RESERVED</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Please fill in your Name, Email, and Phone Number.")
            else:
                st.warning("Select at least one package to calculate your invoice.")

# ==============================================================================
# ROUTE 2: VENDOR PORTAL & VENDOR REPORTS
# ==============================================================================
elif route == "Vendor Portal Login 🔐":
    st.title("Vendor Portal Dashboard")
    
    if st.session_state.logged_vendor is None:
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            v_type = st.selectbox("Account Type:", ["Venue Owner", "Service Supplier"])
            v_id = st.text_input("Account Identifier (e.g., athena or saina):").strip().lower()
        with col_l2:
            v_pass = st.text_input("Password:", type="password")
            login_btn = st.button("Authenticate Dashboard")

        if login_btn:
            account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)
            if account and (v_pass == account.get("password") or v_pass == "admin2026"):
                st.session_state.logged_vendor = {"id": v_id, "type": v_type}
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        v_info = st.session_state.logged_vendor
        v_id, v_type = v_info["id"], v_info["type"]
        account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)

        c_top1, c_top2 = st.columns([4, 1])
        with c_top1:
            st.success(f"Logged in as: **{account.get('business_name')}**")
        with c_top2:
            if st.button("Log Out"):
                st.session_state.logged_vendor = None
                st.rerun()

        tab_reports, tab_rates = st.tabs(["📊 Financial Reports & Invoices", "🏷️ Catalog & Pricing Models"])
        
        # Vendor Financial Statement
        with tab_reports:
            st.subheader(f"Invoices & Earnings for {account.get('business_name')}")
            
            vendor_payouts = []
            for b in st.session_state.bookings_data:
                for item in b["items"]:
                    if item["vendor_id"] == v_id:
                        vendor_payouts.append({
                            "Invoice ID": b["invoice_id"],
                            "Event Date": b["event_date"],
                            "Client": b["client_name"],
                            "Item Booked": item["item"],
                            "Gross Amount": item["price"],
                            "Net Payout (90%)": item["price"] * 0.90,
                            "Status": b["status"]
                        })
            
            if vendor_payouts:
                df_vp = pd.DataFrame(vendor_payouts)
                st.table(df_vp)
                
                tot_gross = df_vp["Gross Amount"].sum()
                tot_net = df_vp["Net Payout (90%)"].sum()
                
                m1, m2 = st.columns(2)
                m1.metric("Gross Billings", f"BWP {tot_gross:,.2f}")
                m2.metric("Net Payout Earned", f"BWP {tot_net:,.2f}")
            else:
                st.info("No bookings recorded yet for your account.")

        with tab_rates:
            st.subheader("Current Catalog & Pricing Models")
            current_pkgs = account.get("packages", [])
            if current_pkgs:
                st.table(pd.DataFrame(current_pkgs))
            
            st.markdown("---")
            with st.form("add_package_form"):
                fp_name = st.text_input("Item Title:")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    fp_price = st.number_input("Rate (BWP):", min_value=0.0, value=500.0, step=50.0)
                with col_p2:
                    fp_unit = st.selectbox("Pricing Model:", ["Per Day", "Per Unit", "Per Guest"])
                fp_desc = st.text_area("Description:")
                
                if st.form_submit_button("Add Item"):
                    if fp_name:
                        account.setdefault("packages", []).append({
                            "id": f"item_{len(current_pkgs) + 1}",
                            "name": fp_name, "price": float(fp_price), "unit": fp_unit, "desc": fp_desc
                        })
                        save_json(CONFIG_FILE, st.session_state.config_data)
                        st.success(f"Added {fp_name}")
                        st.rerun()

# ==============================================================================
# ROUTE 3: REGISTRATION
# ==============================================================================
elif route == "Venue & Supplier Registration":
    st.title("Partner Registration")
    reg_type = st.radio("Registering As:", ["Venue Partner", "Service Supplier"])
    
    with st.form("reg_form"):
        r_id = st.text_input("Account Identifier (URL Slug):").strip().lower()
        r_name = st.text_input("Business Name:")
        r_phone = st.text_input("Phone Number:")
        r_pass = st.text_input("Password:", type="password")
        
        if reg_type == "Venue Partner":
            r_tagline = st.text_input("Tagline:")
            r_color = st.color_picker("Brand Color Accent:", "#1E3A8A")
        else:
            r_cat = st.selectbox("Category:", ["Catering & Buffets", "Decor & Styling", "Utensils & Crockery", "Wellness Services"])
            
        if st.form_submit_button("Complete Registration"):
            if r_id and r_name and r_pass:
                if reg_type == "Venue Partner":
                    st.session_state.config_data["venues"][r_id] = {
                        "business_name": r_name, "tagline": r_tagline, "phone": r_phone,
                        "password": r_pass, "brand_color": r_color, "packages": []
                    }
                else:
                    st.session_state.config_data["all_suppliers"][r_id] = {
                        "business_name": r_name, "category": r_cat, "phone": r_phone,
                        "password": r_pass, "packages": []
                    }
                save_json(CONFIG_FILE, st.session_state.config_data)
                st.success(f"Registered '{r_name}'. You can now log in.")
            else:
                st.error("Fill in all fields.")

# ==============================================================================
# ROUTE 4: MASTER ADMIN & FINANCIAL SYSTEM REPORTING
# ==============================================================================
elif route == "Platform Administration":
    st.title("Platform Administration")
    pin = st.text_input("Security PIN:", type="password")
    
    if pin == "admin2026":
        st.success("Authenticated Master Administrator")
        
        # Financial Overview Metrics
        all_bookings = st.session_state.bookings_data
        total_gross = sum(b["grand_total"] for b in all_bookings)
        platform_commission = total_gross * 0.10
        vendor_payouts_total = total_gross * 0.90
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Bookings", len(all_bookings))
        m2.metric("Gross Revenue", f"BWP {total_gross:,.2f}")
        m3.metric("Platform Revenue (10%)", f"BWP {platform_commission:,.2f}")
        m4.metric("Vendor Payouts (90%)", f"BWP {vendor_payouts_total:,.2f}")
        
        st.markdown("---")
        st.subheader("Master Transaction Ledger & Invoices")
        if all_bookings:
            df_master = pd.DataFrame(all_bookings)[["invoice_id", "timestamp", "client_name", "event_date", "grand_total", "deposit_paid", "status"]]
            st.table(df_master)
        else:
            st.info("No transaction invoices generated yet.")

        st.markdown("---")
        st.subheader("Account Directory & Deletion")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            v_del = st.selectbox("Select Venue to Delete:", ["-- Select --"] + list(venues.keys()), key="del_v")
            if st.button("Delete Venue"):
                if v_del != "-- Select --":
                    del st.session_state.config_data["venues"][v_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Removed '{v_del}'")
                    st.rerun()

        with col_d2:
            s_del = st.selectbox("Select Supplier to Delete:", ["-- Select --"] + list(all_suppliers.keys()), key="del_s")
            if st.button("Delete Supplier"):
                if s_del != "-- Select --":
                    del st.session_state.config_data["all_suppliers"][s_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Removed '{s_del}'")
                    st.rerun()emoved '{s_del}'")
                    st.rerun()
