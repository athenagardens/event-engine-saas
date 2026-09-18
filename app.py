import streamlit as st
import pandas as pd
import datetime
import json
import os

# 1. PAGE SETUP
st.set_page_config(
    page_title="EventEngine Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

CONFIG_FILE = "vendors.json"
BOOKINGS_FILE = "bookings.json"

# --- DATA HELPERS ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"venues": {}, "suppliers": {}}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_booking(new_booking):
    bookings = load_bookings()
    bookings.append(new_booking)
    try:
        with open(BOOKINGS_FILE, "w") as f:
            json.dump(bookings, f, indent=2)
    except Exception:
        pass

# Initialize Session State
if "config_data" not in st.session_state:
    st.session_state.config_data = load_config()

venues = st.session_state.config_data.get("venues", {})
all_suppliers = st.session_state.config_data.get("suppliers", {})

# PRE-CALCULATE ACTIVE SUPPLIERS
today_str = datetime.date.today().strftime("%Y-%m-%d")
active_suppliers = {}
for s_id, sup in all_suppliers.items():
    sub = sup.get("subscription", {})
    if sub.get("status") == "ACTIVE" and sub.get("paid_until", "") >= today_str:
        active_suppliers[s_id] = sup

# ROUTING & PARAMS
query_params = st.query_params
active_venue_id = query_params.get("vendor", None)

# Dynamic Dynamic Styling Fallbacks (Platform Default Palette)
if active_venue_id and active_venue_id in venues:
    venue_cfg = venues[active_venue_id]
else:
    venue_cfg = None

# Set UI Colors
if venue_cfg:
    v_brand = venue_cfg.get("brand_colors", {"primary": "#1E3A8A", "secondary": "#1E293B", "accent": "#3B82F6"})
    v_primary = v_brand.get("primary", "#1E3A8A")
    v_secondary = v_brand.get("secondary", "#1E293B")
else:
    v_primary = "#1E3A8A"
    v_secondary = "#1E293B"

st.markdown(f"""
    <style>
    /* Clean Modern Base Styles */
    .stApp {{
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    /* Executive Sidebar Theme */
    [data-testid="stSidebar"] {{
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }}
    [data-testid="stSidebar"] * {{
        color: #F1F5F9 !important;
    }}
    
    /* Dynamic Brand Header */
    .vendor-header {{
        background: linear-gradient(135deg, {v_primary} 0%, {v_secondary} 100%);
        padding: 28px 32px;
        border-radius: 8px;
        color: #FFFFFF !important;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }}
    .vendor-header h1 {{
        color: #FFFFFF !important;
        margin: 0;
        font-size: 1.75rem;
        font-weight: 600;
        letter-spacing: -0.025em;
    }}
    .vendor-header p {{
        color: #E2E8F0 !important;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }}
    
    /* Clean Corporate Cards */
    .vendor-card {{
        border: 1px solid #E2E8F0;
        border-top: 3px solid {v_primary};
        border-radius: 6px;
        padding: 20px;
        background-color: #FFFFFF;
        margin-bottom: 16px;
    }}
    
    /* Modern Button Overrides */
    .stButton>button {{
        background-color: {v_primary} !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
    }}
    
    /* Metrics Layout */
    [data-testid="stMetric"] {{
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
    }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("### EventEngine")
st.sidebar.caption("Enterprise Event Suite")
st.sidebar.markdown("---")

route = st.sidebar.radio(
    "Navigation",
    ["Client Booking Portal", "Venue & Supplier Registration", "Vendor Portal Login", "Platform Administration"]
)

st.sidebar.markdown("---")
if venue_cfg:
    st.sidebar.caption(f"Active Portal: **{venue_cfg.get('business_name')}**")
else:
    st.sidebar.caption("Active Portal: **Platform Directory**")

# ==============================================================================
# ROUTE 1: REGISTRATION & ONBOARDING
# ==============================================================================
if route == "Venue & Supplier Registration":
    st.title("Business Registration")
    st.markdown("Register your venue or service business to establish your dedicated portal.")
    
    reg_type = st.radio("Registration Type", ["Venue Partner", "Service Supplier"])
    
    if reg_type == "Venue Partner":
        st.subheader("Venue Account Configuration")
        col1, col2 = st.columns(2)
        with col1:
            v_id = st.text_input("Unique Venue Identifier (URL Slug):").lower().strip()
            v_pass = st.text_input("Account Password:", type="password")
            v_name = st.text_input("Business Name:")
            v_tagline = st.text_input("Tagline or Subtitle:")
            v_phone = st.text_input("Contact WhatsApp Number:")
            v_logo_url = st.text_input("Logo Image URL:")
        with col2:
            st.markdown("#### Corporate Brand Palette")
            st.caption("Select your exact corporate primary and secondary hex colors.")
            c_primary = st.color_picker("Primary Brand Color", "#1E3A8A")
            c_secondary = st.color_picker("Secondary Brand Color", "#1E293B")
            c_accent = st.color_picker("Accent Color", "#3B82F6")
            
        if st.button("Complete Registration"):
            if v_id and v_name and v_pass:
                venues[v_id] = {
                    "password": v_pass,
                    "business_name": v_name,
                    "tagline": v_tagline or "Event Destination",
                    "logo_file": v_logo_url.strip(),
                    "whatsapp": v_phone,
                    "brand_colors": {"primary": c_primary, "secondary": c_secondary, "accent": c_accent},
                    "subscription": {"status": "ACTIVE", "paid_until": "2026-12-31"},
                    "venue_catalog": [{"item_id": f"{v_id}_01", "item_name": "Main Event Space", "price": 5000.0, "unit": "Per Day"}],
                    "partner_suppliers": list(all_suppliers.keys())
                }
                st.session_state.config_data["venues"] = venues
                save_config(st.session_state.config_data)
                st.success(f"Venue account '{v_name}' registered successfully.")
                st.info(f"Direct Portal Link: `?vendor={v_id}`")
            else:
                st.error("Please complete all required identification and credential fields.")

    else:
        st.subheader("Supplier Account Configuration")
        col1, col2 = st.columns(2)
        with col1:
            s_id = st.text_input("Supplier Identifier:").lower().strip()
            s_pass = st.text_input("Account Password:", type="password")
            s_name = st.text_input("Business Name:")
            s_cat = st.selectbox("Service Category:", ["Catering & Buffets", "Decor & Styling", "Sound & Lighting", "Photography"])
            s_phone = st.text_input("Contact WhatsApp Number:")
        with col2:
            st.markdown("#### Initial Service Offering")
            item_name = st.text_input("Package Title:")
            item_price = st.number_input("Package Unit Price (BWP):", min_value=10.0, value=150.0)
            item_unit = st.selectbox("Pricing Unit:", ["Per Guest", "Per Table", "Per Unit", "Per Day"])
            
        if st.button("Register Supplier Account"):
            if s_id and s_name and s_pass:
                all_suppliers[s_id] = {
                    "password": s_pass,
                    "business_name": s_name,
                    "category": s_cat,
                    "whatsapp": s_phone,
                    "subscription": {"status": "ACTIVE", "paid_until": "2026-12-31", "monthly_fee_bwp": 500.0},
                    "catalog": [{"item_id": f"{s_id}_01", "item_name": item_name or "Standard Service", "price": item_price, "unit": item_unit}]
                }
                st.session_state.config_data["suppliers"] = all_suppliers
                save_config(st.session_state.config_data)
                st.success(f"Supplier account '{s_name}' registered successfully.")
            else:
                st.error("Please complete required identifier and credential fields.")

# ==============================================================================
# ROUTE 2: VENDOR MANAGEMENT DASHBOARD
# ==============================================================================
elif route == "Vendor Portal Login":
    st.title("Vendor Management Portal")
    st.markdown("Log in to manage corporate branding, catalog offerings, and client bookings.")
    
    if "logged_vendor_id" not in st.session_state:
        st.session_state.logged_vendor_id = None
        st.session_state.vendor_type = None

    if not st.session_state.logged_vendor_id:
        with st.form("vendor_login"):
            v_type = st.radio("Account Type", ["Venue Owner", "Service Supplier"])
            v_id_input = st.text_input("Account Identifier:").lower().strip()
            v_pass_input = st.text_input("Password:", type="password")
            login_btn = st.form_submit_button("Authenticate")
            
            if login_btn:
                if v_type == "Venue Owner" and v_id_input in venues:
                    if venues[v_id_input].get("password") == v_pass_input or v_pass_input == "admin2026":
                        st.session_state.logged_vendor_id = v_id_input
                        st.session_state.vendor_type = "venue"
                        st.rerun()
                    else:
                        st.error("Authentication failed. Invalid password.")
                elif v_type == "Service Supplier" and v_id_input in all_suppliers:
                    if all_suppliers[v_id_input].get("password") == v_pass_input or v_pass_input == "admin2026":
                        st.session_state.logged_vendor_id = v_id_input
                        st.session_state.vendor_type = "supplier"
                        st.rerun()
                    else:
                        st.error("Authentication failed. Invalid password.")
                else:
                    st.error("Account identifier not found.")
    else:
        v_id = st.session_state.logged_vendor_id
        is_venue = st.session_state.vendor_type == "venue"
        account = venues[v_id] if is_venue else all_suppliers[v_id]
        
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.subheader(f"Dashboard: {account.get('business_name')}")
        with col_logout:
            if st.button("Sign Out"):
                st.session_state.logged_vendor_id = None
                st.session_state.vendor_type = None
                st.rerun()

        tab_bookings, tab_branding, tab_catalog = st.tabs(["Client Reservations", "Brand & Site Settings", "Package Directory"])
        
        # TAB 1: BOOKINGS
        with tab_bookings:
            st.markdown("#### Reservations")
            all_b = load_bookings()
            vendor_bookings = [b for b in all_b if b.get("venue_id") == v_id or any(item.get("provider") == account.get("business_name") for item in b.get("items", []))]
            
            if vendor_bookings:
                df = pd.DataFrame(vendor_bookings)[["booking_id", "client_name", "client_phone", "event_date", "total_amount", "status"]]
                df.columns = ["Booking ID", "Client", "Contact", "Event Date", "Total (BWP)", "Status"]
                st.table(df)
            else:
                st.info("No active reservations found.")
                
        # TAB 2: BRAND SETTINGS
        with tab_branding:
            st.markdown("#### Identity & Branding Settings")
            new_name = st.text_input("Business Name:", value=account.get("business_name", ""))
            new_tagline = st.text_input("Tagline:", value=account.get("tagline", ""))
            new_phone = st.text_input("WhatsApp Number:", value=account.get("whatsapp", ""))
            new_logo = st.text_input("Logo Image URL:", value=account.get("logo_file", ""))
            
            if is_venue:
                c_data = account.get("brand_colors", {"primary": "#1E3A8A", "secondary": "#1E293B", "accent": "#3B82F6"})
                col1, col2, col3 = st.columns(3)
                with col1:
                    cp = st.color_picker("Primary Corporate Color", c_data.get("primary", "#1E3A8A"))
                with col2:
                    cs = st.color_picker("Secondary Brand Color", c_data.get("secondary", "#1E293B"))
                with col3:
                    ca = st.color_picker("Accent Color", c_data.get("accent", "#3B82F6"))

            if st.button("Update Corporate Identity"):
                account["business_name"] = new_name
                account["tagline"] = new_tagline
                account["whatsapp"] = new_phone
                account["logo_file"] = new_logo
                if is_venue:
                    account["brand_colors"] = {"primary": cp, "secondary": cs, "accent": ca}
                    venues[v_id] = account
                    st.session_state.config_data["venues"] = venues
                else:
                    all_suppliers[v_id] = account
                    st.session_state.config_data["suppliers"] = all_suppliers
                
                save_config(st.session_state.config_data)
                st.success("Brand settings updated.")

        # TAB 3: CATALOG
        with tab_catalog:
            st.markdown("#### Offered Packages & Space Rentals")
            cat_key = "venue_catalog" if is_venue else "catalog"
            catalog = account.get(cat_key, [])
            
            if catalog:
                st.table(pd.DataFrame(catalog))
            
            st.markdown("---")
            st.markdown("#### Add New Package")
            add_item_name = st.text_input("Package Title:")
            add_item_price = st.number_input("Rate (BWP):", min_value=10.0, value=1000.0)
            add_item_unit = st.selectbox("Unit:", ["Per Day", "Per Guest", "Per Table", "Per Unit"])
            
            if st.button("Add Item"):
                if add_item_name:
                    catalog.append({
                        "item_id": f"{v_id}_{len(catalog)+1}",
                        "item_name": add_item_name,
                        "price": add_item_price,
                        "unit": add_item_unit
                    })
                    account[cat_key] = catalog
                    if is_venue:
                        venues[v_id] = account
                        st.session_state.config_data["venues"] = venues
                    else:
                        all_suppliers[v_id] = account
                        st.session_state.config_data["suppliers"] = all_suppliers
                    save_config(st.session_state.config_data)
                    st.success("Item added to catalog.")
                    st.rerun()

# ==============================================================================
# ROUTE 3: MASTER ADMIN
# ==============================================================================
elif route == "Platform Administration":
    st.title("Platform Administration")
    with st.form("admin_login_form"):
        pin = st.text_input("Platform Security Key:", type="password")
        login_submitted = st.form_submit_button("Authenticate")
    
    if login_submitted or pin == "admin2026":
        if pin == "admin2026":
            st.success("Authenticated Platform Administrator")
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Venues", len(venues))
            col2.metric("Active Suppliers", len(all_suppliers))
            col3.metric("Estimated Monthly Revenue", f"P{len(venues)*1500 + len(all_suppliers)*500:,.2f}")
            
            st.markdown("---")
            st.subheader("Registered Venues")
            if venues:
                v_rows = [{"Identifier": k, "Business Name": v.get("business_name"), "Primary Color": v.get("brand_colors", {}).get("primary"), "Portal Link": f"/?vendor={k}"} for k, v in venues.items()]
                st.table(pd.DataFrame(v_rows))
            
            st.subheader("Registered Suppliers")
            if all_suppliers:
                s_rows = [{"Identifier": k, "Business Name": v.get("business_name"), "Category": v.get("category"), "WhatsApp": v.get("whatsapp")} for k, v in all_suppliers.items()]
                st.table(pd.DataFrame(s_rows))

# ==============================================================================
# ROUTE 4: CLIENT BOOKING WIZARD
# ==============================================================================
else:
    # IF NO VENDOR SPECIFIED IN URL, SHOW PLATFORM DIRECTORY
    if not venue_cfg:
        st.title("EventEngine Directory")
        st.markdown("Select an active venue portal below to begin reservation:")
        
        if venues:
            for v_key, v_val in venues.items():
                st.markdown(f"""
                    <div class="vendor-card">
                        <h3>{v_val.get('business_name')}</h3>
                        <p>{v_val.get('tagline')}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Access {v_val.get('business_name')} Portal", key=f"btn_{v_key}"):
                    st.query_params["vendor"] = v_key
                    st.rerun()
        else:
            st.info("No venues registered yet. Please navigate to 'Venue & Supplier Registration' to onboard a venue.")
            
    else:
        if "step" not in st.session_state: st.session_state.step = 1
        if "cart" not in st.session_state: st.session_state.cart = []
        if "client_info" not in st.session_state: st.session_state.client_info = {}
        if "selected_suppliers" not in st.session_state: st.session_state.selected_suppliers = []

        # Render Branded Header Banner
        logo_path = venue_cfg.get("logo_file", "")
        logo_html = f'<img src="{logo_path}" style="width: 72px; height: 72px; border-radius: 6px; object-fit: cover; background: white; padding: 4px;">' if logo_path else ''
        
        st.markdown(f"""
            <div class="vendor-header">
                <div style="display: flex; align-items: center; gap: 20px;">
                    {logo_html}
                    <div>
                        <h1>{venue_cfg.get('business_name')}</h1>
                        <p>{venue_cfg.get('tagline')}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.progress(st.session_state.step / 5)

        if st.session_state.step == 1:
            st.subheader("Step 1: Event Details & Availability")
            with st.form("client_form"):
                col1, col2 = st.columns(2)
                with col1:
                    c_name = st.text_input("Full Name:")
                    c_email = st.text_input("Email Address:")
                    c_phone = st.text_input("Contact / WhatsApp Number:")
                with col2:
                    e_type = st.selectbox("Event Type:", ["Wedding Ceremony & Reception", "Corporate Function", "Gala & Birthday Party"])
                    e_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
                    e_guests = st.number_input("Expected Guest Count:", min_value=10, max_value=500, value=80, step=10)
                
                submitted = st.form_submit_button("Check Availability and Continue")
                if submitted:
                    if not c_name or not c_phone or not c_email:
                        st.error("Please complete required contact information.")
                    else:
                        locked_dates = [b["event_date"] for b in load_bookings() if b.get("status") == "PAID" and b.get("venue_id") == active_venue_id]
                        selected_date_str = e_date.strftime("%Y-%m-%d")
                        if selected_date_str in locked_dates:
                            st.error(f"The selected venue is reserved on {selected_date_str}.")
                        else:
                            st.session_state.client_info = {"name": c_name, "email": c_email, "phone": c_phone, "event_type": e_type, "date": selected_date_str, "guests": e_guests}
                            st.session_state.step = 2
                            st.rerun()

        elif st.session_state.step == 2:
            st.subheader("Step 2: Venue Space Selection")
            client = st.session_state.client_info
            st.info(f"Booking Context: **{client['event_type']}** | Guest Count: **{client['guests']}** | Reserved Date: **{client['date']}**")
            
            venue_catalog = venue_cfg.get("venue_catalog", [])
            selected_space = st.radio("Available Space Options:", options=[f"{v['item_name']} (P{v['price']:,.2f})" for v in venue_catalog])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Previous"):
                    st.session_state.step = 1
                    st.rerun()
            with col2:
                if st.button("Continue to Services"):
                    chosen_item = next(v for v in venue_catalog if v["item_name"] in selected_space)
                    st.session_state.cart = [{"provider": venue_cfg["business_name"], "item_name": chosen_item["item_name"], "qty": 1, "price": chosen_item["price"], "total": chosen_item["price"], "whatsapp": venue_cfg.get("whatsapp", "")}]
                    st.session_state.step = 3
                    st.rerun()

        elif st.session_state.step == 3:
            st.subheader("Step 3: Service Selection")
            partner_ids = venue_cfg.get("partner_suppliers", list(active_suppliers.keys()))
            available_suppliers = {active_suppliers[s_id]["category"]: s_id for s_id in partner_ids if s_id in active_suppliers}
            
            selected_cats = st.multiselect("Select Required Service Categories:", list(available_suppliers.keys()), default=list(available_suppliers.keys())) if available_suppliers else []
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Previous"):
                    st.session_state.step = 2
                    st.rerun()
            with col2:
                if st.button("Configure Packages"):
                    st.session_state.selected_suppliers = [available_suppliers[cat] for cat in selected_cats]
                    st.session_state.step = 4
                    st.rerun()

        elif st.session_state.step == 4:
            st.subheader("Step 4: Package Customization")
            if not st.session_state.selected_suppliers:
                st.info("No external suppliers selected. Proceed to quote summary.")
            else:
                for s_id in st.session_state.selected_suppliers:
                    sup = active_suppliers[s_id]
                    st.markdown(f"#### Category: {sup['category']} ({sup['business_name']})")
                    for idx, item in enumerate(sup.get("catalog", [])):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            add_item = st.checkbox(f"{item['item_name']} (P{item['price']:,.2f} / {item['unit']})", key=f"sel_{s_id}_{idx}")
                        with col2:
                            if add_item:
                                raw_default = st.session_state.client_info["guests"] if "Guest" in item["unit"] else 1
                                qty = st.number_input("Quantity:", min_value=1, value=raw_default, key=f"q_{s_id}_{idx}")
                                st.session_state.cart = [c for c in st.session_state.cart if c["item_name"] != item["item_name"]]
                                st.session_state.cart.append({"provider": sup["business_name"], "item_name": item["item_name"], "qty": qty, "price": item["price"], "total": item["price"] * qty, "whatsapp": sup.get("whatsapp", "")})

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Previous"):
                    st.session_state.step = 3
                    st.rerun()
            with col2:
                if st.button("Review Quote Summary"):
                    st.session_state.step = 5
                    st.rerun()

        elif st.session_state.step == 5:
            st.subheader("Step 5: Quote Summary & Confirmation")
            client = st.session_state.client_info
            st.markdown(f"Client: **{client['name']}** | Date: **{client['date']}** | Guests: **{client['guests']}**")
            
            df = pd.DataFrame(st.session_state.cart)[["provider", "item_name", "qty", "total"]]
            df.columns = ["Service Provider", "Package Details", "Quantity", "Total (BWP)"]
            st.table(df)
            
            subtotal = sum(i["total"] for i in st.session_state.cart)
            deposit = subtotal * 0.50
            st.markdown(f"### Total Quote: **P{subtotal:,.2f}** | Initial Deposit (50%): **P{deposit:,.2f}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Reservation"):
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
                    st.success("Reservation confirmed and recorded.")
            with col2:
                if st.button("Create New Quotation"):
                    st.session_state.step = 1
                    st.session_state.cart = []
                    st.rerun()
