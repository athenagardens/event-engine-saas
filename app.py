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

# Default Vendor & Event Data
default_config = {
    "venues": {
        "athena": {
            "business_name": "Athena Gardens & Pavilion",
            "tagline": "Premier Luxury Outdoor Event Space & Estate",
            "phone": "+267 71 234 567",
            "password": "pass",
            "brand_color": "#0F172A",
            "packages": [
                {"id": "p1", "name": "Main Lawn Space", "price": 5000.0, "unit": "Per Day", "desc": "Exclusive full-day access to main grounds."},
                {"id": "p2", "name": "Small Group Pavilion (Up to 30)", "price": 2500.0, "unit": "Per Day", "desc": "Cozy space for intimate gatherings."},
                {"id": "p3", "name": "Bridal Suite Rental", "price": 1200.0, "unit": "Per Unit", "desc": "Private room for bridal party prep."}
            ],
            "ticketed_events": [
                {
                    "event_id": "evt_101",
                    "event_name": "Summer Garden Music Festival",
                    "event_date": "2026-11-15",
                    "flyer_headline": "The Biggest Live Acoustic & Food Festival of the Season!",
                    "ticket_types": [
                        {"type": "General Admission", "price": 250.0, "total": 200, "sold": 18},
                        {"type": "VIP Lounge Pass", "price": 600.0, "total": 50, "sold": 10}
                    ]
                }
            ]
        }
    },
    "all_suppliers": {
        "saina": {
            "business_name": "Saina Utensils & Event Wellness",
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

# Dynamic Query Parameters Parsing
query_params = st.query_params
active_vendor_slug = query_params.get("vendor", None)
active_event_id = query_params.get("event", None)
active_venue = venues.get(active_vendor_slug) if active_vendor_slug in venues else None

primary_color = active_venue.get("brand_color", "#0F172A") if active_venue else "#0F172A"

st.set_page_config(page_title="Saina Enterprise | Luxury Venue Management", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# LUXURY ENTERPRISE CSS STYLING
# ==============================================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #0F172A;
        background-color: #F8FAFC;
    }}
    
    /* Main Header Container */
    .hero-header {{
        background: linear-gradient(135deg, {primary_color} 0%, #1E293B 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1);
    }}
    .hero-header h1 {{
        color: #FFFFFF !important;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }}
    .hero-header p {{
        color: #94A3B8;
        font-size: 1.05rem;
        margin: 0;
    }}

    /* Card Panels */
    .custom-card {{
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .custom-card:hover {{
        box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.08);
    }}
    
    /* Promotional Flyer Styling */
    .flyer-container {{
        background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
        border: 2px solid #6366F1;
        border-radius: 16px;
        padding: 2.5rem;
        color: #FFFFFF;
        text-align: center;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        margin: 1.5rem 0;
    }}
    .flyer-badge {{
        background: #4F46E5;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.35rem 1rem;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 1rem;
    }}

    /* Modern Buttons */
    .stButton>button {{
        background-color: {primary_color} !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .stButton>button:hover {{
        opacity: 0.92;
        transform: translateY(-1px);
    }}
    
    /* Invoice Box */
    .invoice-card {{
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 6px solid #22C55E;
        border-radius: 10px;
        padding: 1.75rem;
        margin-top: 1.5rem;
    }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# NAVIGATION SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("### 👑 **SAINA ENTERPRISE**")
    st.caption("Venue & Hospitality Management Platform")
    st.markdown("---")
    
    route = st.radio(
        "NAVIGATION MENU", 
        ["🏢 Customer Marketplace", "🔐 Vendor Dashboard", "📝 Partner Onboarding", "🛡️ Master Administration"],
        index=0
    )
    st.markdown("---")
    
    if active_venue:
        st.success(f"📍 Active Portal: **{active_venue['business_name']}**")
        if st.button("Reset Portal Selection"):
            st.query_params.clear()
            st.rerun()

# ==============================================================================
# ROUTE 1: CUSTOMER MARKETPLACE (BOOKINGS & FLYER TICKET PAYMENTS)
# ==============================================================================
if route == "🏢 Customer Marketplace":
    if not active_venue:
        st.markdown("""
        <div class="hero-header">
            <h1>Discover & Reserve Premier Venues</h1>
            <p>Book luxury spaces and purchase direct event tickets across Botswana.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not venues:
            st.info("No venues currently listed on the platform.")
        else:
            cols = st.columns(2)
            for idx, (slug, vdata) in enumerate(venues.items()):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class="custom-card">
                        <span style="color:#6366F1; font-weight:700; font-size:0.8rem; text-transform:uppercase;">Verified Venue Partner</span>
                        <h3 style="margin: 0.2rem 0 0.5rem 0; color:#0F172A;">{vdata.get('business_name')}</h3>
                        <p style="color:#64748B; font-size:0.9rem; margin-bottom: 1rem;"><em>"{vdata.get('tagline', '')}"</em></p>
                        <p style="font-size:0.85rem; color:#334155;">📞 <strong>Contact:</strong> {vdata.get('phone', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Enter {vdata.get('business_name')} Portal", key=f"nav_{slug}"):
                        st.query_params["vendor"] = slug
                        st.rerun()
    else:
        st.markdown(f"""
        <div class="hero-header">
            <h1>{active_venue.get('business_name')}</h1>
            <p>{active_venue.get('tagline')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_tickets, tab_book, tab_info = st.tabs(["🎟️ Buy Event Tickets", "🗓️ Reserve Venue Spaces", "ℹ️ Venue Profile"])
        
        # --- TICKETING & FLYER GATEWAY ---
        with tab_tickets:
            st.markdown("### **Upcoming Ticketed Events**")
            events_list = active_venue.get("ticketed_events", [])
            
            if not events_list:
                st.info("There are currently no scheduled ticketed events at this venue.")
            else:
                for evt in events_list:
                    is_direct_flyer_event = (active_event_id == evt['event_id'])
                    
                    if is_direct_flyer_event:
                        st.success(f"⚡ **Direct Link Activated:** You are viewing tickets via the promotional flyer for **{evt['event_name']}**!")
                    
                    with st.expander(f"🎟️ {evt['event_name']} — Date: {evt['event_date']}", expanded=is_direct_flyer_event or (len(events_list) == 1)):
                        
                        # Render Digital Promotional Flyer Graphic
                        if evt.get("flyer_headline"):
                            st.markdown(f"""
                            <div class="flyer-container">
                                <span class="flyer-badge">Official Event Pass</span>
                                <h1 style="font-size:2.2rem; font-weight:800; margin-bottom:0.5rem;">{evt['event_name'].upper()}</h1>
                                <p style="font-size:1.1rem; color:#C7D2FE; font-style:italic;">"{evt.get('flyer_headline')}"</p>
                                <hr style="border:0.5px solid rgba(255,255,255,0.15); margin: 1.5rem 0;">
                                <div style="display:flex; justify-content:center; gap:20px; font-size:0.95rem;">
                                    <span>📍 <strong>Venue:</strong> {active_venue.get('business_name')}</span>
                                    <span>📅 <strong>Date:</strong> {evt['event_date']}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("#### **Select Your Tickets:**")
                        t_cols = st.columns(len(evt["ticket_types"]))
                        selected_tickets = {}
                        
                        for idx, tt in enumerate(evt["ticket_types"]):
                            with t_cols[idx]:
                                remaining = tt["total"] - tt["sold"]
                                st.markdown(f"""
                                <div class="custom-card" style="text-align:center;">
                                    <h4 style="margin:0;">{tt['type']}</h4>
                                    <h2 style="color:#4F46E5; margin:0.5rem 0;">BWP {tt['price']:,.2f}</h2>
                                    <p style="color:#64748B; font-size:0.8rem;">Available: {remaining} / {tt['total']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if remaining > 0:
                                    qty = st.number_input(f"Quantity:", min_value=0, max_value=remaining, value=0, key=f"t_qty_{evt['event_id']}_{idx}")
                                    if qty > 0:
                                        selected_tickets[tt['type']] = {"qty": qty, "price": tt['price'], "index": idx}
                                else:
                                    st.error("Sold Out")

                        if selected_tickets:
                            st.markdown("---")
                            t_total = sum(item["qty"] * item["price"] for item in selected_tickets.values())
                            st.markdown(f"### Checkout Total: <span style='color:#4F46E5;'>BWP {t_total:,.2f}</span>", unsafe_allow_html=True)
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                t_client_name = st.text_input("Attendee Full Name:", key=f"t_name_{evt['event_id']}")
                            with c2:
                                t_client_phone = st.text_input("WhatsApp / Phone Number:", key=f"t_phone_{evt['event_id']}")
                            
                            if st.button("Complete Payment & Download Ticket Pass", key=f"btn_buy_{evt['event_id']}"):
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
                                    
                                    # Deduct Inventory
                                    for t_name, t_info in selected_tickets.items():
                                        evt["ticket_types"][t_info["index"]]["sold"] += t_info["qty"]
                                    
                                    save_json(CONFIG_FILE, st.session_state.config_data)
                                    st.session_state.ticket_sales_data.append(sale_record)
                                    save_json(TICKETS_FILE, st.session_state.ticket_sales_data)
                                    
                                    st.balloons()
                                    st.success("Payment Processed Successfully!")
                                    
                                    # Render Issued Pass Invoice
                                    st.markdown(f"""
                                    <div class="invoice-card">
                                        <div style="display:flex; justify-content:space-between; align-items:center;">
                                            <h3 style="margin:0; color:#0F172A;">🎟️ OFFICIAL DIGITAL TICKET PASS</h3>
                                            <span style="background:#DCFCE7; color:#15803D; font-weight:700; padding:4px 12px; border-radius:20px; font-size:0.8rem;">PAYMENT VERIFIED</span>
                                        </div>
                                        <hr style="border:0.5px solid #E2E8F0; margin:1rem 0;">
                                        <p><strong>Pass Reference ID:</strong> {t_inv} | <strong>Issue Date:</strong> {str(datetime.date.today())}</p>
                                        <p><strong>Attendee Name:</strong> {t_client_name} ({t_client_phone})</p>
                                        <p><strong>Event:</strong> {evt['event_name']} | <strong>Date:</strong> {evt['event_date']}</p>
                                        <p><strong>Venue Location:</strong> {active_venue['business_name']}</p>
                                        <p style="font-size:1.2rem; margin-top:1rem;"><strong>Amount Paid:</strong> <span style="color:#15803D; font-weight:700;">BWP {t_total:,.2f}</span></p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error("Please enter Attendee Name and Contact Number.")

        # --- MULTI-STEP VENUE RESERVATION ENGINE ---
        with tab_book:
            st.markdown("### **Reserve Venue & Onsite Services**")
            
            st.markdown("#### **Step 1: Reservation & Contact Details**")
            c1, c2 = st.columns(2)
            with c1:
                client_name = st.text_input("Client Full Name:")
                client_email = st.text_input("Email Address:")
                client_phone = st.text_input("Contact / WhatsApp Number:")
            with c2:
                event_type = st.selectbox("Event Category:", ["Wedding & Reception", "Corporate Event / Gala", "Birthday / Private Celebration", "Wellness Retreat"])
                event_date = st.date_input("Scheduled Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
                guest_count = st.number_input("Expected Guest Count:", min_value=1, value=80, step=5)

            st.markdown("---")
            st.markdown("#### **Step 2: Select Venue Package & Spaces**")
            venue_pkgs = active_venue.get("packages", [])
            selected_items = []
            
            if venue_pkgs:
                for pkg in venue_pkgs:
                    p_id, p_name, p_price, p_unit = pkg["id"], pkg["name"], pkg["price"], pkg.get("unit", "Per Day")
                    item_total = p_price * guest_count if p_unit == "Per Guest" else p_price
                    unit_label = "flat rate" if p_unit in ["Per Day", "Per Unit"] else f"BWP {p_price:.2f} × {guest_count} guests"
                    
                    if st.checkbox(f"**{p_name}** — BWP {item_total:,.2f} ({unit_label})", key=f"chk_v_{p_id}"):
                        selected_items.append({"vendor_id": active_vendor_slug, "vendor_name": active_venue['business_name'], "item": p_name, "price": item_total})
            else:
                st.info("No venue packages listed.")

            st.markdown("---")
            st.markdown("#### **Step 3: Onsite Supplier Add-Ons**")
            if all_suppliers:
                for s_slug, s_data in all_suppliers.items():
                    st.markdown(f"**{s_data.get('business_name')}** ({s_data.get('category')})")
                    for s_pkg in s_data.get("packages", []):
                        sp_id, sp_name, sp_price, sp_unit = s_pkg["id"], s_pkg["name"], s_pkg["price"], s_pkg.get("unit", "Per Guest")
                        s_item_total = sp_price * guest_count if sp_unit == "Per Guest" else sp_price
                        s_unit_label = f"BWP {sp_price:.2f} × {guest_count} guests" if sp_unit == "Per Guest" else "flat rate"
                        
                        if st.checkbox(f"**{sp_name}** — BWP {s_item_total:,.2f} ({s_unit_label})", key=f"chk_s_{sp_id}"):
                            selected_items.append({"vendor_id": s_slug, "vendor_name": s_data['business_name'], "item": sp_name, "price": s_item_total})

            st.markdown("---")
            st.markdown("#### **Step 4: Invoice Summary & Payment Gateway**")
            if selected_items:
                df_summary = pd.DataFrame(selected_items)[["vendor_name", "item", "price"]]
                df_summary.columns = ["Service Provider", "Item / Space Description", "Total (BWP)"]
                st.table(df_summary)
                
                grand_total = sum(i["price"] for i in selected_items)
                deposit = grand_total * 0.50
                
                m1, m2 = st.columns(2)
                m1.metric("Grand Total Cost", f"BWP {grand_total:,.2f}")
                m2.metric("Required 50% Deposit", f"BWP {deposit:,.2f}")
                
                payment_method = st.radio("Select Payment Channel:", ["Debit / Credit Card (Instant Confirmation)", "EFT Payment Transfer"])
                
                if st.button("Confirm Reservation & Issue Deposit Invoice"):
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
                        st.success("Booking Request & Payment Confirmed!")
                        
                        st.markdown(f"""
                        <div class="invoice-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3 style="margin:0;">OFFICIAL TAX INVOICE</h3>
                                <span style="background:#DCFCE7; color:#15803D; font-weight:700; padding:4px 12px; border-radius:20px; font-size:0.8rem;">CONFIRMED</span>
                            </div>
                            <hr style="border:0.5px solid #E2E8F0; margin:1rem 0;">
                            <p><strong>Invoice Reference:</strong> {inv_id} | <strong>Date Issued:</strong> {str(datetime.date.today())}</p>
                            <p><strong>Client Name:</strong> {client_name} ({client_phone})</p>
                            <p><strong>Event Date:</strong> {event_date} | <strong>Guests:</strong> {guest_count}</p>
                            <p><strong>Deposit Paid (50%):</strong> <span style="color:#15803D; font-weight:700;">BWP {deposit:,.2f}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Please fill out your contact details before confirming.")
            else:
                st.warning("Please select at least one package or service above.")

        with tab_info:
            st.markdown(f"### About {active_venue.get('business_name')}")
            st.write(f"📞 **Phone Contact:** {active_venue.get('phone')}")
            st.write(f"🎨 **Brand Theme Code:** `{active_venue.get('brand_color')}`")

# ==============================================================================
# ROUTE 2: VENDOR DASHBOARD & FLYER BUILDER ENGINE
# ==============================================================================
elif route == "🔐 Vendor Dashboard":
    st.markdown("""
    <div class="hero-header">
        <h1>Vendor Portal & Management Control</h1>
        <p>Manage revenue payouts, catalog listings, event ticketing, and direct marketing flyers.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.logged_vendor is None:
        st.markdown("### **Authentication Login**")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            v_type = st.selectbox("Account Category:", ["Venue Owner", "Service Supplier"])
            v_id = st.text_input("Account Identifier Slug (e.g., athena or saina):").strip().lower()
        with col_l2:
            v_pass = st.text_input("Portal Password:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            login_btn = st.button("Authenticate & Enter Portal")

        if login_btn:
            account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)
            if account and (v_pass == account.get("password") or v_pass == "admin2026"):
                st.session_state.logged_vendor = {"id": v_id, "type": v_type}
                st.rerun()
            else:
                st.error("Authentication failed. Check your identifier and password.")
    else:
        v_info = st.session_state.logged_vendor
        v_id, v_type = v_info["id"], v_info["type"]
        account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)

        c_top1, c_top2 = st.columns([4, 1])
        with c_top1:
            st.subheader(f"Welcome Back, **{account.get('business_name')}**")
        with c_top2:
            if st.button("Log Out Dashboard"):
                st.session_state.logged_vendor = None
                st.rerun()

        st.markdown("---")
        
        tab_list = ["📊 Financial Ledger & Net Payouts", "🏷️ Catalog & Package Pricing"]
        if v_type == "Venue Owner":
            tab_list.append("🎟️ Ticketed Events Setup")
            tab_list.append("🎨 Promotional Flyer Builder")
            
        tabs = st.tabs(tab_list)
        
        # --- TAB 1: LEDGER & PAYOUTS ---
        with tabs[0]:
            st.markdown("#### **Transaction Ledger & Net Payout Statements**")
            
            vendor_payouts = []
            for b in st.session_state.bookings_data:
                for item in b["items"]:
                    if item["vendor_id"] == v_id:
                        vendor_payouts.append({
                            "Type": "Private Reservation",
                            "Ref Code": b["invoice_id"],
                            "Event Date": b["event_date"],
                            "Client Name": b["client_name"],
                            "Service Description": item["item"],
                            "Gross Sales": item["price"],
                            "Net Payable Payout (90%)": item["price"] * 0.90,
                        })
            
            for t in st.session_state.ticket_sales_data:
                if t["venue_id"] == v_id:
                    vendor_payouts.append({
                        "Type": "Direct Ticket Pass (Flyer / Portal)",
                        "Ref Code": t["ticket_invoice_id"],
                        "Event Date": t["event_date"],
                        "Client Name": t["attendee_name"],
                        "Service Description": f"Tickets: {t['event_name']}",
                        "Gross Sales": t["total_amount"],
                        "Net Payable Payout (90%)": t["total_amount"] * 0.90,
                    })

            if vendor_payouts:
                df_vp = pd.DataFrame(vendor_payouts)
                st.table(df_vp)
                
                tot_gross = df_vp["Gross Sales"].sum()
                tot_net = df_vp["Net Payable Payout (90%)"].sum()
                
                m1, m2 = st.columns(2)
                m1.metric("Gross Platform Billings", f"BWP {tot_gross:,.2f}")
                m2.metric("Net Vendor Payout (90%)", f"BWP {tot_net:,.2f}")
            else:
                st.info("No recorded transactions currently logged for this vendor account.")

        # --- TAB 2: CATALOG MANAGEMENT ---
        with tabs[1]:
            st.markdown("#### **Active Service Listings**")
            current_pkgs = account.get("packages", [])
            if current_pkgs:
                st.table(pd.DataFrame(current_pkgs))
            
            st.markdown("---")
            st.markdown("#### **Add New Item or Package**")
            with st.form("add_pkg_form"):
                fp_name = st.text_input("Package Title:")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    fp_price = st.number_input("Rate (BWP):", min_value=0.0, value=500.0, step=50.0)
                with col_p2:
                    fp_unit = st.selectbox("Pricing Model:", ["Per Day", "Per Unit", "Per Guest"])
                fp_desc = st.text_area("Package Overview:")
                
                if st.form_submit_button("Add Package Listing"):
                    if fp_name:
                        account.setdefault("packages", []).append({
                            "id": f"pkg_{len(current_pkgs) + 1}",
                            "name": fp_name, "price": float(fp_price), "unit": fp_unit, "desc": fp_desc
                        })
                        save_json(CONFIG_FILE, st.session_state.config_data)
                        st.success(f"Successfully added '{fp_name}' to catalog.")
                        st.rerun()

        # --- TAB 3: TICKETING SETUP ---
        if v_type == "Venue Owner":
            with tabs[2]:
                st.markdown("#### **Hosted Ticketed Events**")
                v_events = account.get("ticketed_events", [])
                
                if v_events:
                    for e in v_events:
                        st.markdown(f"🔹 **{e['event_name']}** | Scheduled: `{e['event_date']}`")
                        st.table(pd.DataFrame(e["ticket_types"]))
                else:
                    st.info("No ticketed events created yet.")

                st.markdown("---")
                st.markdown("#### **Publish New Event**")
                
                with st.form("create_evt_form"):
                    e_name = st.text_input("Event Name:")
                    e_date = st.date_input("Event Date:", min_value=datetime.date.today())
                    e_headline = st.text_input("Flyer Promotional Headline:", value="An Exclusive Live Event Experience!")
                    
                    st.markdown("##### **Ticket Tier 1:**")
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        t1_name = st.text_input("Tier Name:", value="General Admission")
                    with col_t2:
                        t1_price = st.number_input("Price (BWP):", min_value=0.0, value=200.0)
                    with col_t3:
                        t1_qty = st.number_input("Total Seats/Passes:", min_value=1, value=150)

                    st.markdown("##### **Ticket Tier 2 (Optional):**")
                    col_t4, col_t5, col_t6 = st.columns(3)
                    with col_t4:
                        t2_name = st.text_input("Tier Name:", value="VIP Pass", key="t2_n")
                    with col_t5:
                        t2_price = st.number_input("Price (BWP):", min_value=0.0, value=500.0, key="t2_p")
                    with col_t6:
                        t2_qty = st.number_input("Total Seats/Passes:", min_value=0, value=30, key="t2_q")

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
                            st.success(f"Published '{e_name}' successfully!")
                            st.rerun()

            # --- TAB 4: FLYER GENERATOR ENGINE WITH INTEGRATED PAYMENT LINKS ---
            with tabs[3]:
                st.markdown("#### **Digital Event Flyer Builder & Payment Link Suite**")
                st.caption("Generate dynamic promotional flyers that embed direct ticket payment links for WhatsApp and social media campaigns.")
                
                v_events = account.get("ticketed_events", [])
                if not v_events:
                    st.warning("Create a ticketed event under 'Ticketed Events Setup' first.")
                else:
                    event_options = {e["event_name"]: e for e in v_events}
                    selected_e_name = st.selectbox("Select Target Event:", list(event_options.keys()))
                    sel_evt = event_options[selected_e_name]
                    
                    st.markdown("---")
                    st.markdown("##### **1. Customize Promotional Copy**")
                    f_headline = st.text_input("Headline Subtitle:", value=sel_evt.get("flyer_headline", "Join us for an unforgettable evening!"))
                    f_cta = st.text_input("Button Action Text:", value="PURCHASE TICKET PASS")
                    
                    # Update active event headline
                    sel_evt["flyer_headline"] = f_headline
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    
                    # Construct URL Direct Link with query params
                    direct_link = f"http://localhost:8501/?vendor={v_id}&event={sel_evt['event_id']}"
                    
                    st.markdown("---")
                    st.markdown("##### **2. Live Digital Flyer Graphic Preview**")
                    
                    st.markdown(f"""
                    <div class="flyer-container">
                        <span class="flyer-badge">OFFICIAL INVITATION PASS</span>
                        <h1 style="font-size:2.5rem; font-weight:800; margin:0.5rem 0;">{sel_evt['event_name'].upper()}</h1>
                        <p style="font-size:1.15rem; color:#C7D2FE; font-style:italic;">"{f_headline}"</p>
                        <hr style="border:0.5px solid rgba(255,255,255,0.15); margin: 1.5rem 0;">
                        <div style="margin-bottom:1.5rem;">
                            <p style="margin:0.25rem 0;">📍 Location: <strong>{account.get('business_name')}</strong></p>
                            <p style="margin:0.25rem 0;">📅 Scheduled Date: <strong>{sel_evt['event_date']}</strong></p>
                            <p style="margin:0.25rem 0;">📞 Enquiries: <strong>{account.get('phone')}</strong></p>
                        </div>
                        <a href="{direct_link}" target="_blank" style="background:#22C55E; color:#FFFFFF; text-decoration:none; padding:12px 30px; font-weight:700; border-radius:30px; display:inline-block;">
                            🎟️ {f_cta}
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("##### **3. Embedded Marketing Link**")
                    st.code(direct_link, language="markdown")
                    st.caption("Copy this URL into your promotional broadcasts. When clicked, clients are routed directly to checkout with this event pre-selected.")

# ==============================================================================
# ROUTE 3: PARTNER ONBOARDING
# ==============================================================================
elif route == "📝 Partner Onboarding":
    st.markdown("""
    <div class="hero-header">
        <h1>Partner Registration Portal</h1>
        <p>Register your venue or service business to join the Saina network.</p>
    </div>
    """, unsafe_allow_html=True)
    
    reg_type = st.radio("Account Category:", ["Venue Partner", "Service Supplier"])
    
    with st.form("registration_form"):
        r_id = st.text_input("Account Handle Slug (e.g., grandpalace):").strip().lower()
        r_name = st.text_input("Registered Business Name:")
        r_phone = st.text_input("Business Phone Number:")
        r_pass = st.text_input("Dashboard Password:", type="password")
        
        if reg_type == "Venue Partner":
            r_tagline = st.text_input("Venue Tagline / Motto:")
            r_color = st.color_picker("Brand Accent Color:", "#0F172A")
        else:
            r_cat = st.selectbox("Service Specialty:", ["Catering & Buffets", "Decor & Event Styling", "Utensils & Equipment Rental", "Wellness Services"])
            
        if st.form_submit_button("Complete Registration"):
            if r_id and r_name and r_pass:
                if reg_type == "Venue Partner":
                    st.session_state.config_data["venues"][r_id] = {
                        "business_name": r_name, "tagline": r_tagline, "phone": r_phone,
                        "password": r_pass, "brand_color": r_color, "packages": [], "ticketed_events": []
                    }
                else:
                    st.session_state.config_data["all_suppliers"][r_id] = {
                        "business_name": r_name, "category": r_cat, "phone": r_phone,
                        "password": r_pass, "packages": []
                    }
                save_json(CONFIG_FILE, st.session_state.config_data)
                st.success(f"Partner Account '{r_name}' successfully onboarded!")
            else:
                st.error("Please fill in all required registration fields.")

# ==============================================================================
# ROUTE 4: MASTER PLATFORM ADMINISTRATION
# ==============================================================================
elif route == "🛡️ Master Administration":
    st.markdown("""
    <div class="hero-header">
        <h1>Platform Administration & Financial Control</h1>
        <p>Audit system revenue, view all reservation ledgers, and manage active accounts.</p>
    </div>
    """, unsafe_allow_html=True)
    
    pin = st.text_input("Enter Master Passcode:", type="password")
    
    if pin == "admin2026":
        st.success("Platform Authenticated")
        
        all_bookings = st.session_state.bookings_data
        all_tickets = st.session_state.ticket_sales_data
        
        total_booking_gross = sum(b["grand_total"] for b in all_bookings)
        total_ticket_gross = sum(t["total_amount"] for t in all_tickets)
        total_gross = total_booking_gross + total_ticket_gross
        
        platform_commission = total_gross * 0.10
        vendor_payouts_total = total_gross * 0.90
        
        st.markdown("#### **Platform Revenue Overview**")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total System Orders", f"{len(all_bookings)} Bookings / {len(all_tickets)} Tickets")
        m2.metric("Gross Billings", f"BWP {total_gross:,.2f}")
        m3.metric("Saina Revenue (10%)", f"BWP {platform_commission:,.2f}")
        m4.metric("Vendor Disbursements (90%)", f"BWP {vendor_payouts_total:,.2f}")
        
        st.markdown("---")
        st.markdown("#### **Master Private Reservations Ledger**")
        if all_bookings:
            df_master = pd.DataFrame(all_bookings)[["invoice_id", "timestamp", "client_name", "event_date", "grand_total", "deposit_paid", "status"]]
            st.table(df_master)
        else:
            st.info("No private reservation invoices generated yet.")

        st.markdown("---")
        st.markdown("#### **Master Ticket Sales Ledger (Flyers & Portal)**")
        if all_tickets:
            df_t_master = pd.DataFrame(all_tickets)[["ticket_invoice_id", "timestamp", "venue_name", "event_name", "attendee_name", "total_amount", "status"]]
            st.table(df_t_master)
        else:
            st.info("No ticket sales recorded yet.")

        st.markdown("---")
        st.markdown("#### **Platform Directory Management**")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            v_del = st.selectbox("Purge Venue Account:", ["-- Select --"] + list(venues.keys()), key="del_v")
            if st.button("Delete Venue"):
                if v_del != "-- Select --":
                    del st.session_state.config_data["venues"][v_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Purged '{v_del}'")
                    st.rerun()

        with col_d2:
            s_del = st.selectbox("Purge Supplier Account:", ["-- Select --"] + list(all_suppliers.keys()), key="del_s")
            if st.button("Delete Supplier"):
                if s_del != "-- Select --":
                    del st.session_state.config_data["all_suppliers"][s_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Purged '{s_del}'")
                    st.rerun()
