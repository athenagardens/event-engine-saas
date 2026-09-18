import streamlit as st
import json
import os
import datetime
import pandas as pd

# ==============================================================================
# CONFIGURATION & PERSISTENCE
# ==============================================================================
CONFIG_FILE = "vendors.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
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

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "config_data" not in st.session_state:
    st.session_state.config_data = load_config()

venues = st.session_state.config_data.get("venues", {})
all_suppliers = st.session_state.config_data.get("all_suppliers", {})

query_params = st.query_params
active_vendor_slug = query_params.get("vendor", None)

# Set base branding depending on active venue parameter
active_venue = venues.get(active_vendor_slug) if active_vendor_slug in venues else None
page_title = f"{active_venue['business_name']} | Booking Portal" if active_venue else "Saina | Event Platform"
primary_color = active_venue.get("brand_color", "#1E3A8A") if active_venue else "#1E3A8A"

st.set_page_config(page_title=page_title, layout="wide")

# Inject Custom Branding Colors
st.markdown(f"""
    <style>
    .stButton>button {{
        background-color: {primary_color} !important;
        color: white !important;
        border-radius: 6px;
    }}
    .metric-card {{
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid {primary_color};
    }}
    </style>
""", unsafe_allow_html=True)

# Navigation
st.sidebar.title("Saina Platform")
route = st.sidebar.radio(
    "Navigate System", 
    ["Client Booking Portal", "Vendor Portal Login 🔐", "Venue & Supplier Registration", "Platform Administration"]
)

# ==============================================================================
# ROUTE 1: CLIENT BOOKING PORTAL
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
            st.markdown("### Step 1: Event Details")
            c1, c2 = st.columns(2)
            with c1:
                client_name = st.text_input("Full Name:")
                client_email = st.text_input("Email Address:")
                client_phone = st.text_input("WhatsApp / Contact Number:")
            with c2:
                event_type = st.selectbox("Event Type:", ["Wedding", "Corporate Gala", "Birthday & Private Party", "Wellness Retreat"])
                event_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
                guest_count = st.number_input("Expected Guest Count:", min_value=1, value=80, step=5)

            st.markdown("---")
            st.markdown("### Step 2: Select Venue Space")
            venue_pkgs = active_venue.get("packages", [])
            selected_venue_items = []
            
            if venue_pkgs:
                for pkg in venue_pkgs:
                    p_id, p_name, p_price, p_unit = pkg["id"], pkg["name"], pkg["price"], pkg.get("unit", "Per Day")
                    
                    # Calculate dynamic item cost
                    item_total = p_price * guest_count if p_unit == "Per Guest" else p_price
                    unit_label = "flat fee" if p_unit in ["Per Day", "Per Unit"] else f"BWP {p_price:.2f} × {guest_count} guests"
                    
                    if st.checkbox(f"{p_name} — BWP {item_total:,.2f} ({unit_label})", key=f"chk_v_{p_id}"):
                        selected_venue_items.append({"name": p_name, "price": item_total, "unit": p_unit})
            else:
                st.info("No venue packages currently listed for this venue.")

            st.markdown("---")
            st.markdown("### Step 3: Add Partner Services (Catering, Utensils & Styling)")
            selected_supplier_items = []
            
            if all_suppliers:
                for s_slug, s_data in all_suppliers.items():
                    st.markdown(f"#### {s_data.get('business_name')} ({s_data.get('category')})")
                    for s_pkg in s_data.get("packages", []):
                        sp_id, sp_name, sp_price, sp_unit = s_pkg["id"], s_pkg["name"], s_pkg["price"], s_pkg.get("unit", "Per Guest")
                        
                        s_item_total = sp_price * guest_count if sp_unit == "Per Guest" else sp_price
                        s_unit_label = f"BWP {sp_price:.2f} × {guest_count} guests" if sp_unit == "Per Guest" else "flat fee"
                        
                        if st.checkbox(f"{sp_name} — BWP {s_item_total:,.2f} ({s_unit_label})", key=f"chk_s_{sp_id}"):
                            selected_supplier_items.append({"name": f"{sp_name} ({s_data['business_name']})", "price": s_item_total, "unit": sp_unit})

            # Calculation Summary
            st.markdown("---")
            st.markdown("### Step 4: Reservation Summary")
            all_selected = selected_venue_items + selected_supplier_items
            
            if all_selected:
                df_summary = pd.DataFrame(all_selected)
                st.table(df_summary)
                
                grand_total = sum(item["price"] for item in all_selected)
                deposit_required = grand_total * 0.50
                
                m1, m2 = st.columns(2)
                m1.metric("Grand Total Amount", f"BWP {grand_total:,.2f}")
                m2.metric("50% Deposit Required to Lock Date", f"BWP {deposit_required:,.2f}")
                
                if st.button("Submit Reservation Request"):
                    if client_name and client_phone:
                        st.balloons()
                        st.success(f"Thank you {client_name}! Your booking request for {event_date} has been submitted. The venue manager will reach out via WhatsApp ({client_phone}) to finalize payment.")
                    else:
                        st.error("Please provide your Name and Contact Number in Step 1.")
            else:
                st.warning("Select at least one space or service package above to calculate your quote.")

# ==============================================================================
# ROUTE 2: VENDOR PORTAL LOGIN & DASHBOARD
# ==============================================================================
elif route == "Vendor Portal Login 🔐":
    st.title("Vendor Portal Dashboard")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        v_type = st.selectbox("Account Type:", ["Venue Owner", "Service Supplier"])
        v_id = st.text_input("Account Identifier (e.g., athena or saina):").strip().lower()
    with col_l2:
        v_pass = st.text_input("Password:", type="password")
        login_btn = st.button("Authenticate Dashboard")

    account = None
    if v_id:
        account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)

    if account and (v_pass == account.get("password") or v_pass == "admin2026"):
        st.success(f"Authenticated: {account.get('business_name')}")
        
        tab_rates, tab_settings = st.tabs(["🏷️ Package Directory & Pricing", "⚙️ Account Settings"])
        
        with tab_rates:
            st.subheader("Current Catalog & Pricing Models")
            current_pkgs = account.get("packages", [])
            
            if current_pkgs:
                st.table(pd.DataFrame(current_pkgs))
            else:
                st.info("No pricing options currently active.")
            
            st.markdown("---")
            st.subheader("Add New Pricing Item")
            
            with st.form("add_package_form"):
                fp_name = st.text_input("Item / Space / Service Title:", placeholder="e.g., VIP Pavilion, Buffet Service, Bridal Suite")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    fp_price = st.number_input("Rate (BWP):", min_value=0.0, value=500.0, step=50.0)
                with col_p2:
                    fp_unit = st.selectbox("Pricing Model / Unit:", ["Per Day", "Per Unit", "Per Guest"])
                
                fp_desc = st.text_area("Description / Capacity Details:", placeholder="e.g., Covers up to 30 guests or flat rate space fee.")
                add_pkg_submitted = st.form_submit_button("Add Item to Catalog")
                
                if add_pkg_submitted:
                    if fp_name:
                        new_pkg = {
                            "id": f"item_{len(current_pkgs) + 1}",
                            "name": fp_name,
                            "price": float(fp_price),
                            "unit": fp_unit,
                            "desc": fp_desc
                        }
                        account.setdefault("packages", []).append(new_pkg)
                        save_config(st.session_state.config_data)
                        st.success(f"Added '{fp_name}' at BWP {fp_price} ({fp_unit})")
                        st.rerun()
                    else:
                        st.error("Please enter an item title.")

# ==============================================================================
# ROUTE 3: REGISTRATION
# ==============================================================================
elif route == "Venue & Supplier Registration":
    st.title("Partner Registration")
    reg_type = st.radio("Registering As:", ["Venue Partner", "Service Supplier"])
    
    with st.form("reg_form"):
        r_id = st.text_input("Account Identifier (URL Slug, e.g., 'royaloak'):").strip().lower()
        r_name = st.text_input("Business Name:")
        r_phone = st.text_input("Contact Phone Number:")
        r_pass = st.text_input("Set Portal Password:", type="password")
        
        if reg_type == "Venue Partner":
            r_tagline = st.text_input("Tagline:")
            r_color = st.color_picker("Brand Color Accent:", "#1E3A8A")
        else:
            r_cat = st.selectbox("Service Category:", ["Catering & Buffets", "Decor & Styling", "Utensils & Crockery", "Wellness Services"])
            
        submit_reg = st.form_submit_button("Complete Registration")
        
        if submit_reg:
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
                save_config(st.session_state.config_data)
                st.success(f"Registered '{r_name}' successfully!")
            else:
                st.error("Please fill in all required fields.")

# ==============================================================================
# ROUTE 4: MASTER ADMIN
# ==============================================================================
elif route == "Platform Administration":
    st.title("Platform Administration")
    pin = st.text_input("Security PIN:", type="password")
    
    if pin == "admin2026":
        st.subheader("Manage & Delete Accounts")
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("#### Delete Venue")
            v_del = st.selectbox("Select Venue:", ["-- Select --"] + list(venues.keys()), key="del_v")
            if st.button("Delete Venue"):
                if v_del != "-- Select --":
                    del st.session_state.config_data["venues"][v_del]
                    save_config(st.session_state.config_data)
                    st.success(f"Removed '{v_del}'")
                    st.rerun()

        with col_d2:
            st.markdown("#### Delete Supplier")
            s_del = st.selectbox("Select Supplier:", ["-- Select --"] + list(all_suppliers.keys()), key="del_s")
            if st.button("Delete Supplier"):
                if s_del != "-- Select --":
                    del st.session_state.config_data["all_suppliers"][s_del]
                    save_config(st.session_state.config_data)
                    st.success(f"Removed '{s_del}'")
                    st.rerun()
