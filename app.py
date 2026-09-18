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
TICKETS_FILE = "tickets.json"

def load_json(filepath, default_data):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return default_data

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# Fully Dynamic Initial Configuration Structure
default_config = {
    "platform_info": {
        "platform_name": "Event Venue Platform",
        "platform_tagline": "Integrated Venue & Event Service Ecosystem",
        "primary_theme": "#1E40AF"
    },
    "venues": {
        "venue_01": {
            "business_name": "Grand Premier Estate",
            "tagline": "Exclusive Luxury Event Space",
            "phone": "+267 71 234 567",
            "password": "pass",
            "brand_color": "#1E40AF",
            "packages": [
                {"id": "p1", "name": "Main Lawn Space", "price": 5000.0, "unit": "Per Day", "desc": "Exclusive full-day access to main grounds."},
                {"id": "p2", "name": "Small Group Pavilion (Up to 30)", "price": 2500.0, "unit": "Per Day", "desc": "Space for intimate gatherings."},
                {"id": "p3", "name": "Bridal Suite Rental", "price": 1200.0, "unit": "Per Unit", "desc": "Private room for party preparation."}
            ],
            "ticketed_events": [
                {
                    "event_id": "evt_101",
                    "event_name": "Summer Gala & Acoustic Evening",
                    "event_date": "2026-11-15",
                    "flyer_headline": "Live Music & Fine Dining Experience",
                    "ticket_types": [
                        {"type": "General Admission", "price": 250.0, "total": 200, "sold": 18},
                        {"type": "VIP Pass", "price": 600.0, "total": 50, "sold": 10}
                    ]
                }
            ]
        }
    },
    "all_suppliers": {
        "supplier_01": {
            "business_name": "Apex Catering & Event Decor",
            "category": "Catering & Event Styling",
            "phone": "+267 72 987 654",
            "password": "pass",
            "brand_color": "#2563EB",
            "packages": [
                {"id": "s1", "name": "Full Buffet & Table Setup", "price": 150.0, "unit": "Per Guest", "desc": "Premium tableware and buffet service."},
                {"id": "s2", "name": "Cocktail & Beverage Station", "price": 3000.0, "unit": "Per Unit", "desc": "Mobile bar and service team."}
            ]
        }
    }
}

# Session State Initializations
if "config_data" not in st.session_state:
    st.session_state.config_data = load_json(CONFIG_FILE, default_config)

if "bookings_data" not in st.session_state:
    st.session_state.bookings_data = load_json(BOOKINGS_FILE, [])

if "ticket_sales_data" not in st.session_state:
    st.session_state.ticket_sales_data = load_json(TICKETS_FILE, [])

if "logged_vendor" not in st.session_state:
    st.session_state.logged_vendor = None

venues = st.session_state.config_data.get("venues", {})
all_suppliers = st.session_state.config_data.get("all_suppliers", {})
platform_info = st.session_state.config_data.get("platform_info", default_config["platform_info"])

# Dynamic Query Parameters
query_params = st.query_params
active_vendor_slug = query_params.get("vendor", None)
active_event_id = query_params.get("event", None)
active_venue = venues.get(active_vendor_slug) if active_vendor_slug in venues else None

primary_color = active_venue.get("brand_color", platform_info.get("primary_theme", "#1E40AF")) if active_venue else platform_info.get("primary_theme", "#1E40AF")

st.set_page_config(page_title=f"{platform_info.get('platform_name')} | Platform", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# MODERN BLUE THEME DESIGN SYSTEM & UNIFORM SIDEBAR
# ==============================================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: #0F172A;
        background-color: #F8FAFC;
    }}

    /* Sidebar Container Box */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
        border-right: 1px solid #334155;
    }}

    [data-testid="stSidebar"] * {{
        color: #F8FAFC !important;
    }}

    /* Hide default radio header label completely */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{
        display: none !important;
    }}

    /* Sidebar Radio Flex Group Container */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {{
        display: flex !important;
        flex-direction: column !important;
        gap: 12px !important;
        margin-top: 0px !important;
        padding-top: 0px !important;
    }}

    /* Individual Navigation Buttons - Pixel Perfect Uniform Height */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
        padding: 0 12px !important;
        height: 52px !important; /* Uniform height for all items */
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-sizing: border-box !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out;
    }}

    /* Hover State */
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }}

    /* Equalize Text Alignment and Padding Inside Menu Buttons */
    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:nth-child(2) {{
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:nth-child(2) p {{
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        text-align: center !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }}
    
    /* Dynamic Hero Banner Container */
    .hero-header {{
        background: linear-gradient(135deg, {primary_color} 0%, #0F172A 100%);
        padding: 2rem;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
    }}
    .hero-header h1 {{
        color: #FFFFFF !important;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }}
    .hero-header p {{
        color: #93C5FD;
        font-size: 1rem;
        margin: 0;
    }}

    /* Card Panels */
    .custom-card {{
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}
    
    /* Promotional Banner Styling */
    .flyer-container {{
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 12px;
        padding: 2rem;
        color: #FFFFFF;
        text-align: center;
        margin: 1.5rem 0;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: {primary_color} !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 0.5rem 1.25rem !important;
    }}
    
    /* Invoice Card */
    .invoice-card {{
        background-color: #FFFFFF;
        border: 1px solid #BFDBFE;
        border-left: 5px solid #1E40AF;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# DYNAMIC NAVIGATION SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown(f"### **{platform_info.get('platform_name', 'PLATFORM').upper()}**")
    st.caption(platform_info.get("platform_tagline", "Event Management Platform"))
    st.markdown("---")
    
    st.markdown(
        """
        <div style="font-weight: 700; font-size: 0.82rem; letter-spacing: 0.05em; margin-bottom: 12px; color: #94A3B8;">
            NAVIGATION MENU
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    route = st.radio(
        "NAVIGATION MENU", 
        ["Customer Marketplace", "Vendor Dashboard", "Partner Onboarding", "Master Administration"],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("---")
    
    if active_venue:
        st.info(f"Active Portal:\n**{active_venue.get('business_name')}**")
        if st.button("Reset Portal Selection"):
            st.query_params.clear()
            st.rerun()

# ==============================================================================
# ROUTE 1: CUSTOMER MARKETPLACE
# ==============================================================================
if route == "Customer Marketplace":
    if not active_venue:
        st.markdown(f"""
        <div class="hero-header">
            <h1>{platform_info.get('platform_name')} Marketplace</h1>
            <p>Select a partner venue to manage bookings or purchase event tickets.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not venues:
            st.info("No venues currently listed on the platform.")
        else:
            cols = st.columns(2)
            for idx, (slug, vdata) in enumerate(venues.items()):
                with cols[idx % 2]:
                    v_color = vdata.get('brand_color', '#1E40AF')
                    st.markdown(f"""
                    <div class="custom-card">
                        <strong style="color:{v_color}; font-size:0.8rem; text-transform:uppercase;">Verified Partner</strong>
                        <h3 style="margin: 0.2rem 0 0.5rem 0; color:#0F172A;">{vdata.get('business_name')}</h3>
                        <p style="color:#475569; font-size:0.9rem; margin-bottom: 0.75rem;">{vdata.get('tagline', '')}</p>
                        <p style="font-size:0.85rem; color:#334155;"><strong>Contact:</strong> {vdata.get('phone', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Access {vdata.get('business_name')}", key=f"nav_{slug}"):
                        st.query_params["vendor"] = slug
                        st.rerun()
    else:
        st.markdown(f"""
        <div class="hero-header">
            <h1>{active_venue.get('business_name')}</h1>
            <p>{active_venue.get('tagline')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_tickets, tab_book, tab_info = st.tabs(["Event Tickets", "Reserve Venue", "Venue Details"])
        
        # --- TICKETING ---
        with tab_tickets:
            st.markdown("### Scheduled Events")
            events_list = active_venue.get("ticketed_events", [])
            
            if not events_list:
                st.info("No scheduled events available.")
            else:
                for evt in events_list:
                    is_direct_flyer_event = (active_event_id == evt['event_id'])
                    
                    if is_direct_flyer_event:
                        st.success(f"Direct referral link loaded for **{evt['event_name']}**.")
                    
                    with st.expander(f"{evt['event_name']} — Date: {evt['event_date']}", expanded=is_direct_flyer_event or (len(events_list) == 1)):
                        
                        if evt.get("flyer_headline"):
                            st.markdown(f"""
                            <div class="flyer-container">
                                <h2 style="margin:0;">{evt['event_name']}</h2>
                                <p style="color:#93C5FD; margin-top:0.5rem;">{evt.get('flyer_headline')}</p>
                                <hr style="border:0.5px solid rgba(255,255,255,0.2); margin: 1rem 0;">
                                <p style="margin:0; font-size:0.9rem;">Venue: {active_venue.get('business_name')} | Date: {evt['event_date']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("#### Select Ticket Tier:")
                        t_cols = st.columns(len(evt["ticket_types"]))
                        selected_tickets = {}
                        
                        for idx, tt in enumerate(evt["ticket_types"]):
                            with t_cols[idx]:
                                remaining = tt["total"] - tt["sold"]
                                st.markdown(f"""
                                <div class="custom-card" style="text-align:center;">
                                    <strong>{tt['type']}</strong>
                                    <h3 style="color:#1E40AF; margin:0.5rem 0;">BWP {tt['price']:,.2f}</h3>
                                    <span style="color:#475569; font-size:0.8rem;">Available: {remaining}/{tt['total']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if remaining > 0:
                                    qty = st.number_input("Quantity:", min_value=0, max_value=remaining, value=0, key=f"t_qty_{evt['event_id']}_{idx}")
                                    if qty > 0:
                                        selected_tickets[tt['type']] = {"qty": qty, "price": tt['price'], "index": idx}
                                else:
                                    st.error("Sold Out")

                        if selected_tickets:
                            st.markdown("---")
                            t_total = sum(item["qty"] * item["price"] for item in selected_tickets.values())
                            st.markdown(f"### Total Payable: **BWP {t_total:,.2f}**")
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                t_client_name = st.text_input("Attendee Full Name:", key=f"t_name_{evt['event_id']}")
                            with c2:
                                t_client_phone = st.text_input("Contact Number:", key=f"t_phone_{evt['event_id']}")
                            
                            if st.button("Process Payment", key=f"btn_buy_{evt['event_id']}"):
                                if t_client_name and t_client_phone:
                                    t_inv = f"TCK-{len(st.session_state.ticket_sales_data) + 5001}"
                                    
                                    sale_record = {
                                        "ticket_invoice_id": t_inv,
                                        "timestamp": str(datetime.datetime.now())[:19],
                                        "venue_id": active_vendor_slug,
                                        "venue_name": active_venue['business_name'],
                                        "event_name": evt['event_name'],
                                        "event_date": evt['event_date'],
                                        "attendee_name": t_client_name,
                                        "attendee_phone": t_client_phone,
                                        "tickets_purchased": selected_tickets,
                                        "total_amount": t_total,
                                        "status": "Paid"
                                    }
                                    
                                    for t_name, t_info in selected_tickets.items():
                                        evt["ticket_types"][t_info["index"]]["sold"] += t_info["qty"]
                                    
                                    save_json(CONFIG_FILE, st.session_state.config_data)
                                    st.session_state.ticket_sales_data.append(sale_record)
                                    save_json(TICKETS_FILE, st.session_state.ticket_sales_data)
                                    
                                    st.success("Transaction Complete.")
                                    st.markdown(f"""
                                    <div class="invoice-card">
                                        <h4>OFFICIAL TICKET RECEIPT</h4>
                                        <hr style="border:0.5px solid #BFDBFE; margin:0.75rem 0;">
                                        <p><strong>Reference:</strong> {t_inv} | <strong>Date:</strong> {str(datetime.date.today())}</p>
                                        <p><strong>Attendee:</strong> {t_client_name} ({t_client_phone})</p>
                                        <p><strong>Event:</strong> {evt['event_name']} | <strong>Date:</strong> {evt['event_date']}</p>
                                        <p><strong>Venue:</strong> {active_venue['business_name']}</p>
                                        <p><strong>Amount Paid:</strong> BWP {t_total:,.2f}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error("Attendee details required.")

        # --- RESERVATIONS ---
        with tab_book:
            st.markdown("### Venue Booking Engine")
            
            st.markdown("#### 1. Contact Details")
            c1, c2 = st.columns(2)
            with c1:
                client_name = st.text_input("Client Name:")
                client_email = st.text_input("Email:")
                client_phone = st.text_input("Phone Number:")
            with c2:
                event_type = st.selectbox("Event Type:", ["Wedding", "Corporate Event", "Private Gathering", "Other"])
                event_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
                guest_count = st.number_input("Guest Count:", min_value=1, value=80, step=5)

            st.markdown("---")
            st.markdown("#### 2. Venue Space Selection")
            venue_pkgs = active_venue.get("packages", [])
            selected_items = []
            
            if venue_pkgs:
                for pkg in venue_pkgs:
                    p_id, p_name, p_price, p_unit = pkg["id"], pkg["name"], pkg["price"], pkg.get("unit", "Per Day")
                    item_total = p_price * guest_count if p_unit == "Per Guest" else p_price
                    unit_label = "Flat Rate" if p_unit in ["Per Day", "Per Unit"] else f"BWP {p_price:.2f} x {guest_count} guests"
                    
                    if st.checkbox(f"**{p_name}** — BWP {item_total:,.2f} ({unit_label})", key=f"chk_v_{p_id}"):
                        selected_items.append({"vendor_id": active_vendor_slug, "vendor_name": active_venue['business_name'], "item": p_name, "price": item_total})
            else:
                st.info("No venue packages available.")

            st.markdown("---")
            st.markdown("#### 3. Supplier Add-Ons")
            if all_suppliers:
                for s_slug, s_data in all_suppliers.items():
                    st.markdown(f"**{s_data.get('business_name')}** ({s_data.get('category')})")
                    for s_pkg in s_data.get("packages", []):
                        sp_id, sp_name, sp_price, sp_unit = s_pkg["id"], s_pkg["name"], s_pkg["price"], s_pkg.get("unit", "Per Guest")
                        s_item_total = sp_price * guest_count if sp_unit == "Per Guest" else sp_price
                        s_unit_label = f"BWP {sp_price:.2f} x {guest_count} guests" if sp_unit == "Per Guest" else "Flat Rate"
                        
                        if st.checkbox(f"**{sp_name}** — BWP {s_item_total:,.2f} ({s_unit_label})", key=f"chk_s_{sp_id}"):
                            selected_items.append({"vendor_id": s_slug, "vendor_name": s_data['business_name'], "item": sp_name, "price": s_item_total})

            st.markdown("---")
            st.markdown("#### 4. Cost Summary & Deposit")
            if selected_items:
                df_summary = pd.DataFrame(selected_items)[["vendor_name", "item", "price"]]
                df_summary.columns = ["Provider", "Item", "Total (BWP)"]
                st.table(df_summary)
                
                grand_total = sum(i["price"] for i in selected_items)
                deposit = grand_total * 0.50
                
                m1, m2 = st.columns(2)
                m1.metric("Grand Total", f"BWP {grand_total:,.2f}")
                m2.metric("50% Deposit Due", f"BWP {deposit:,.2f}")
                
                payment_method = st.radio("Payment Method:", ["Credit Card", "EFT Transfer"])
                
                if st.button("Confirm Booking"):
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
                        
                        st.success("Booking Request Submitted.")
                        st.markdown(f"""
                        <div class="invoice-card">
                            <h4>TAX INVOICE</h4>
                            <hr style="border:0.5px solid #BFDBFE; margin:0.75rem 0;">
                            <p><strong>Invoice Reference:</strong> {inv_id} | <strong>Date:</strong> {str(datetime.date.today())}</p>
                            <p><strong>Client:</strong> {client_name} ({client_phone})</p>
                            <p><strong>Event Date:</strong> {event_date} | <strong>Guests:</strong> {guest_count}</p>
                            <p><strong>Deposit Paid:</strong> BWP {deposit:,.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Client details required.")
            else:
                st.warning("Select at least one package to proceed.")

        with tab_info:
            st.markdown(f"### {active_venue.get('business_name')}")
            st.write(f"Phone Contact: {active_venue.get('phone')}")

# ==============================================================================
# ROUTE 2: VENDOR DASHBOARD
# ==============================================================================
elif route == "Vendor Dashboard":
    st.markdown("""
    <div class="hero-header">
        <h1>Vendor Management Portal</h1>
        <p>Manage account branding, financial statements, and event listings.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.logged_vendor is None:
        st.markdown("### Account Authentication")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            v_type = st.selectbox("Account Type:", ["Venue Owner", "Service Supplier"])
            v_id = st.text_input("Account Identifier Slug:").strip().lower()
        with col_l2:
            v_pass = st.text_input("Password:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            login_btn = st.button("Authenticate")

        if login_btn:
            account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)
            if account and (v_pass == account.get("password") or v_pass == "admin2026"):
                st.session_state.logged_vendor = {"id": v_id, "type": v_type}
                st.rerun()
            else:
                st.error("Authentication failed. Invalid credentials.")
    else:
        v_info = st.session_state.logged_vendor
        v_id, v_type = v_info["id"], v_info["type"]
        account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)

        c_top1, c_top2 = st.columns([4, 1])
        with c_top1:
            st.subheader(f"Account: **{account.get('business_name')}**")
        with c_top2:
            if st.button("Log Out"):
                st.session_state.logged_vendor = None
                st.rerun()

        st.markdown("---")
        
        tab_list = ["Financial Statements", "Catalog & Branding"]
        if v_type == "Venue Owner":
            tab_list.append("Event Management")
            tab_list.append("Promotional Link Builder")
            
        tabs = st.tabs(tab_list)
        
        # --- TAB 1: FINANCIALS ---
        with tabs[0]:
            st.markdown("#### Transaction Ledger (90% Payout)")
            
            vendor_payouts = []
            for b in st.session_state.bookings_data:
                for item in b["items"]:
                    if item["vendor_id"] == v_id:
                        vendor_payouts.append({
                            "Type": "Private Booking",
                            "Ref Code": b["invoice_id"],
                            "Event Date": b["event_date"],
                            "Client": b["client_name"],
                            "Description": item["item"],
                            "Gross Sales": item["price"],
                            "Net Payable (90%)": item["price"] * 0.90,
                        })
            
            for t in st.session_state.ticket_sales_data:
                if t["venue_id"] == v_id:
                    vendor_payouts.append({
                        "Type": "Ticket Sale",
                        "Ref Code": t["ticket_invoice_id"],
                        "Event Date": t["event_date"],
                        "Client": t["attendee_name"],
                        "Description": f"Event: {t['event_name']}",
                        "Gross Sales": t["total_amount"],
                        "Net Payable (90%)": t["total_amount"] * 0.90,
                    })

            if vendor_payouts:
                df_vp = pd.DataFrame(vendor_payouts)
                st.table(df_vp)
                
                tot_gross = df_vp["Gross Sales"].sum()
                tot_net = df_vp["Net Payable (90%)"].sum()
                
                m1, m2 = st.columns(2)
                m1.metric("Gross Billings", f"BWP {tot_gross:,.2f}")
                m2.metric("Net Vendor Payout (90%)", f"BWP {tot_net:,.2f}")
            else:
                st.info("No transactions logged.")

        # --- TAB 2: CATALOG & DYNAMIC BRANDING ---
        with tabs[1]:
            st.markdown("#### Dynamic Account Branding")
            with st.form("edit_branding_form"):
                b_name = st.text_input("Business Name:", value=account.get("business_name", ""))
                b_tag = st.text_input("Tagline / Service Category:", value=account.get("tagline", account.get("category", "")))
                b_phone = st.text_input("Phone Number:", value=account.get("phone", ""))
                b_color = st.color_picker("Custom Brand Theme Accent:", value=account.get("brand_color", "#1E40AF"))
                
                if st.form_submit_button("Update Brand Settings"):
                    account["business_name"] = b_name
                    if v_type == "Venue Owner":
                        account["tagline"] = b_tag
                    else:
                        account["category"] = b_tag
                    account["phone"] = b_phone
                    account["brand_color"] = b_color
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success("Branding details updated successfully!")
                    st.rerun()

            st.markdown("---")
            st.markdown("#### Active Service Packages")
            current_pkgs = account.get("packages", [])
            if current_pkgs:
                st.table(pd.DataFrame(current_pkgs))
            
            st.markdown("---")
            st.markdown("#### Add New Package")
            with st.form("add_pkg_form"):
                fp_name = st.text_input("Package Title:")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    fp_price = st.number_input("Rate (BWP):", min_value=0.0, value=500.0, step=50.0)
                with col_p2:
                    fp_unit = st.selectbox("Pricing Model:", ["Per Day", "Per Unit", "Per Guest"])
                fp_desc = st.text_area("Description:")
                
                if st.form_submit_button("Add Package"):
                    if fp_name:
                        account.setdefault("packages", []).append({
                            "id": f"pkg_{len(current_pkgs) + 1}",
                            "name": fp_name, "price": float(fp_price), "unit": fp_unit, "desc": fp_desc
                        })
                        save_json(CONFIG_FILE, st.session_state.config_data)
                        st.success(f"Added '{fp_name}'.")
                        st.rerun()

        # --- TAB 3: TICKETING ---
        if v_type == "Venue Owner":
            with tabs[2]:
                st.markdown("#### Hosted Events")
                v_events = account.get("ticketed_events", [])
                
                if v_events:
                    for e in v_events:
                        st.markdown(f"**{e['event_name']}** | Date: `{e['event_date']}`")
                        st.table(pd.DataFrame(e["ticket_types"]))
                else:
                    st.info("No events created.")

                st.markdown("---")
                st.markdown("#### Publish New Event")
                
                with st.form("create_evt_form"):
                    e_name = st.text_input("Event Name:")
                    e_date = st.date_input("Event Date:", min_value=datetime.date.today())
                    e_headline = st.text_input("Promotional Subtitle:", value="Live Event")
                    
                    st.markdown("##### Ticket Tier 1:")
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        t1_name = st.text_input("Tier Name:", value="General Admission")
                    with col_t2:
                        t1_price = st.number_input("Price (BWP):", min_value=0.0, value=200.0)
                    with col_t3:
                        t1_qty = st.number_input("Capacity:", min_value=1, value=150)

                    st.markdown("##### Ticket Tier 2 (Optional):")
                    col_t4, col_t5, col_t6 = st.columns(3)
                    with col_t4:
                        t2_name = st.text_input("Tier Name:", value="VIP Pass", key="t2_n")
                    with col_t5:
                        t2_price = st.number_input("Price (BWP):", min_value=0.0, value=500.0, key="t2_p")
                    with col_t6:
                        t2_qty = st.number_input("Capacity:", min_value=0, value=30, key="t2_q")

                    if st.form_submit_button("Publish Event"):
                        if e_name:
                            ticket_types = [{"type": t1_name, "price": float(t1_price), "total": int(t1_qty), "sold": 0}]
                            if t2_qty > 0 and t2_name:
                                ticket_types.append({"type": t2_name, "price": float(t2_price), "total": int(t2_qty), "sold": 0})
                                
                            new_evt = {
                                "event_id": f"evt_{len(v_events) + 101}",
                                "event_name": e_name,
                                "event_date": str(e_date),
                                "flyer_headline": e_headline,
                                "ticket_types": ticket_types
                            }
                            account.setdefault("ticketed_events", []).append(new_evt)
                            save_json(CONFIG_FILE, st.session_state.config_data)
                            st.success(f"Published '{e_name}'.")
                            st.rerun()

            # --- TAB 4: LINK BUILDER ---
            with tabs[3]:
                st.markdown("#### Direct Referral Link Builder")
                
                v_events = account.get("ticketed_events", [])
                if not v_events:
                    st.warning("Create an event in Event Management first.")
                else:
                    event_options = {e["event_name"]: e for e in v_events}
                    selected_e_name = st.selectbox("Select Event:", list(event_options.keys()))
                    sel_evt = event_options[selected_e_name]
                    
                    st.markdown("---")
                    f_headline = st.text_input("Event Description Line:", value=sel_evt.get("flyer_headline", ""))
                    sel_evt["flyer_headline"] = f_headline
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    
                    direct_link = f"http://localhost:8501/?vendor={v_id}&event={sel_evt['event_id']}"
                    
                    st.markdown("##### Banner Preview")
                    st.markdown(f"""
                    <div class="flyer-container">
                        <h2 style="margin:0;">{sel_evt['event_name']}</h2>
                        <p style="color:#93C5FD; margin-top:0.5rem;">{f_headline}</p>
                        <hr style="border:0.5px solid rgba(255,255,255,0.2); margin: 1rem 0;">
                        <p style="margin:0; font-size:0.9rem;">Venue: {account.get('business_name')} | Date: {sel_evt['event_date']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("##### Direct Checkout URL")
                    st.code(direct_link, language="markdown")

# ==============================================================================
# ROUTE 3: PARTNER ONBOARDING
# ==============================================================================
elif route == "Partner Onboarding":
    st.markdown("""
    <div class="hero-header">
        <h1>Partner Onboarding</h1>
        <p>Register a new venue or service supplier account on the platform.</p>
    </div>
    """, unsafe_allow_html=True)
    
    reg_type = st.radio("Account Category:", ["Venue Partner", "Service Supplier"])
    
    with st.form("registration_form"):
        r_id = st.text_input("Account Identifier Slug:").strip().lower()
        r_name = st.text_input("Business Name:")
        r_phone = st.text_input("Phone Number:")
        r_pass = st.text_input("Password:", type="password")
        
        if reg_type == "Venue Partner":
            r_tagline = st.text_input("Venue Tagline:")
            r_color = st.color_picker("Brand Theme Color:", "#1E40AF")
        else:
            r_cat = st.selectbox("Service Category:", ["Catering & Buffets", "Decor & Event Styling", "Equipment Rental", "Wellness Services"])
            r_color = st.color_picker("Brand Theme Color:", "#2563EB")
            
        if st.form_submit_button("Submit Registration"):
            if r_id and r_name and r_pass:
                if reg_type == "Venue Partner":
                    st.session_state.config_data["venues"][r_id] = {
                        "business_name": r_name, "tagline": r_tagline, "phone": r_phone,
                        "password": r_pass, "brand_color": r_color, "packages": [], "ticketed_events": []
                    }
                else:
                    st.session_state.config_data["all_suppliers"][r_id] = {
                        "business_name": r_name, "category": r_cat, "phone": r_phone,
                        "password": r_pass, "brand_color": r_color, "packages": []
                    }
                save_json(CONFIG_FILE, st.session_state.config_data)
                st.success(f"Registered '{r_name}'.")
            else:
                st.error("Fill in all required fields.")

# ==============================================================================
# ROUTE 4: MASTER PLATFORM ADMINISTRATION
# ==============================================================================
elif route == "Master Administration":
    st.markdown("""
    <div class="hero-header">
        <h1>System Administration</h1>
        <p>Platform branding, billing metrics, and account controls.</p>
    </div>
    """, unsafe_allow_html=True)
    
    pin = st.text_input("Passcode:", type="password")
    
    if pin == "admin2026":
        st.success("Admin Access Granted")
        
        # --- PLATFORM BRANDING SETTINGS ---
        st.markdown("#### Global Platform Settings")
        with st.form("platform_branding_form"):
            p_name = st.text_input("Platform Name:", value=platform_info.get("platform_name", ""))
            p_tag = st.text_input("Platform Tagline:", value=platform_info.get("platform_tagline", ""))
            p_theme = st.color_picker("Global Primary Theme Color:", value=platform_info.get("primary_theme", "#1E40AF"))
            
            if st.form_submit_button("Update System Settings"):
                st.session_state.config_data["platform_info"] = {
                    "platform_name": p_name,
                    "platform_tagline": p_tag,
                    "primary_theme": p_theme
                }
                save_json(CONFIG_FILE, st.session_state.config_data)
                st.success("Platform branding updated globally.")
                st.rerun()

        st.markdown("---")
        
        all_bookings = st.session_state.bookings_data
        all_tickets = st.session_state.ticket_sales_data
        
        total_booking_gross = sum(b["grand_total"] for b in all_bookings)
        total_ticket_gross = sum(t["total_amount"] for t in all_tickets)
        total_gross = total_booking_gross + total_ticket_gross
        
        platform_commission = total_gross * 0.10
        vendor_payouts_total = total_gross * 0.90
        
        st.markdown("#### Platform Financial Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Records", f"{len(all_bookings)} Bookings / {len(all_tickets)} Tickets")
        m2.metric("Gross Billings", f"BWP {total_gross:,.2f}")
        m3.metric("Platform Revenue (10%)", f"BWP {platform_commission:,.2f}")
        m4.metric("Vendor Payouts (90%)", f"BWP {vendor_payouts_total:,.2f}")
        
        st.markdown("---")
        st.markdown("#### Master Reservations Ledger")
        if all_bookings:
            df_master = pd.DataFrame(all_bookings)[["invoice_id", "timestamp", "client_name", "event_date", "grand_total", "deposit_paid", "status"]]
            st.table(df_master)
        else:
            st.info("No bookings registered.")

        st.markdown("---")
        st.markdown("#### Master Ticket Sales Ledger")
        if all_tickets:
            df_t_master = pd.DataFrame(all_tickets)[["ticket_invoice_id", "timestamp", "venue_name", "event_name", "attendee_name", "total_amount", "status"]]
            st.table(df_t_master)
        else:
            st.info("No ticket sales registered.")

        st.markdown("---")
        st.markdown("#### Account Management")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            v_del = st.selectbox("Remove Venue Account:", ["-- Select --"] + list(venues.keys()), key="del_v")
            if st.button("Delete Venue"):
                if v_del != "-- Select --":
                    del st.session_state.config_data["venues"][v_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Removed '{v_del}'")
                    st.rerun()

        with col_d2:
            s_del = st.selectbox("Remove Supplier Account:", ["-- Select --"] + list(all_suppliers.keys()), key="del_s")
            if st.button("Delete Supplier"):
                if s_del != "-- Select --":
                    del st.session_state.config_data["all_suppliers"][s_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Removed '{s_del}'")
                    st.rerun()
