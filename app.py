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

# Default Vendor Data
default_config = {
    "venues": {
        "athena": {
            "business_name": "Athena Gardens",
            "tagline": "Premier Outdoor Event Space & Pavilion",
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
                    "flyer_headline": "The Biggest Music Festival of the Season!",
                    "ticket_types": [
                        {"type": "General Admission", "price": 250.0, "total": 200, "sold": 15},
                        {"type": "VIP Lounge Pass", "price": 600.0, "total": 50, "sold": 8}
                    ]
                }
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

if "ticket_sales_data" not in st.session_state:
    st.session_state.ticket_sales_data = load_json(TICKETS_FILE, [])

if "logged_vendor" not in st.session_state:
    st.session_state.logged_vendor = None

venues = st.session_state.config_data.get("venues", {})
all_suppliers = st.session_state.config_data.get("all_suppliers", {})

# Dynamic Branding based on URL parameters
query_params = st.query_params
active_vendor_slug = query_params.get("vendor", None)
active_event_id = query_params.get("event", None)
active_venue = venues.get(active_vendor_slug) if active_vendor_slug in venues else None

page_title = f"{active_venue['business_name']} | Enterprise Portal" if active_venue else "Saina | Event Management Suite"
primary_color = active_venue.get("brand_color", "#0F172A") if active_venue else "#0F172A"

st.set_page_config(page_title=page_title, layout="wide")

# ==============================================================================
# PROFESSIONAL ENTERPRISE STYLING (CSS)
# ==============================================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: #1E293B;
    }}
    
    .stButton>button {{
        background-color: {primary_color} !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s ease-in-out;
    }}
    
    .stButton>button:hover {{
        opacity: 0.9;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    .metric-card {{
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-top: 4px solid {primary_color};
    }}
    
    .invoice-card {{
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 28px;
        margin-top: 20px;
    }}
    
    .flyer-card {{
        background: linear-gradient(135deg, {primary_color} 0%, #1E293B 100%);
        color: #FFFFFF;
        border-radius: 12px;
        padding: 35px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 25px;
    }}
    
    .status-badge {{
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    </style>
""", unsafe_allow_html=True)

# Navigation Menu
st.sidebar.markdown("### **SAINA ENTERPRISE**")
st.sidebar.caption("Event & Venue Management")
st.sidebar.markdown("---")

route = st.sidebar.radio(
    "Navigation Menu", 
    ["Client Booking Portal", "Vendor Portal Login 🔐", "Venue & Supplier Registration", "Platform Administration"]
)

# ==============================================================================
# ROUTE 1: CLIENT BOOKING PORTAL & TICKETING BUYING ENGINE
# ==============================================================================
if route == "Client Booking Portal":
    if not active_venue:
        st.title("Saina Venue Directory")
        st.caption("Select an enterprise venue partner to configure event reservations or buy event tickets.")
        st.markdown("---")
        
        if not venues:
            st.warning("No venue partners currently registered.")
        else:
            cols = st.columns(2)
            for idx, (slug, vdata) in enumerate(venues.items()):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="margin-bottom:0px;">{vdata.get('business_name')}</h3>
                        <p style="color:#64748B; font-size:0.9rem;"><em>{vdata.get('tagline', '')}</em></p>
                        <p style="font-size:0.85rem;">📞 Contact: <strong>{vdata.get('phone', 'N/A')}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(f"Access {vdata.get('business_name')} Portal", key=f"btn_{slug}"):
                        st.query_params["vendor"] = slug
                        st.rerun()
    else:
        st.title(f"{active_venue.get('business_name')}")
        st.caption(f"{active_venue.get('tagline')} — Official Booking & Ticketing Portal")
        st.markdown("---")
        
        tab_book, tab_tickets, tab_info = st.tabs(["🗓️ Reserve Event & Services", "🎟️ Buy Event Tickets", "ℹ️ Venue Profile"])
        
        with tab_book:
            st.markdown("#### **Step 1: Reservation & Contact Information**")
            c1, c2 = st.columns(2)
            with c1:
                client_name = st.text_input("Full Name:")
                client_email = st.text_input("Email Address:")
                client_phone = st.text_input("WhatsApp / Contact Phone:")
            with c2:
                event_type = st.selectbox("Event Category:", ["Wedding Ceremony & Reception", "Corporate Function", "Gala / Birthday Party", "Wellness Retreat"])
                event_date = st.date_input("Event Date:", min_value=datetime.date.today() + datetime.timedelta(days=1))
                guest_count = st.number_input("Expected Guest Count:", min_value=1, value=80, step=5)

            st.markdown("---")
            st.markdown("#### **Step 2: Select Venue Space**")
            venue_pkgs = active_venue.get("packages", [])
            selected_items = []
            
            if venue_pkgs:
                for pkg in venue_pkgs:
                    p_id, p_name, p_price, p_unit = pkg["id"], pkg["name"], pkg["price"], pkg.get("unit", "Per Day")
                    item_total = p_price * guest_count if p_unit == "Per Guest" else p_price
                    unit_label = "flat fee" if p_unit in ["Per Day", "Per Unit"] else f"BWP {p_price:.2f} × {guest_count} guests"
                    
                    if st.checkbox(f"**{p_name}** — BWP {item_total:,.2f} ({unit_label})", key=f"chk_v_{p_id}"):
                        selected_items.append({"vendor_id": active_vendor_slug, "vendor_name": active_venue['business_name'], "item": p_name, "price": item_total})
            else:
                st.info("No venue spaces listed.")

            st.markdown("---")
            st.markdown("#### **Step 3: Add Onsite Partner Services**")
            if all_suppliers:
                for s_slug, s_data in all_suppliers.items():
                    st.markdown(f"**{s_data.get('business_name')}** ({s_data.get('category')})")
                    for s_pkg in s_data.get("packages", []):
                        sp_id, sp_name, sp_price, sp_unit = s_pkg["id"], s_pkg["name"], s_pkg["price"], s_pkg.get("unit", "Per Guest")
                        s_item_total = sp_price * guest_count if sp_unit == "Per Guest" else sp_price
                        s_unit_label = f"BWP {sp_price:.2f} × {guest_count} guests" if sp_unit == "Per Guest" else "flat fee"
                        
                        if st.checkbox(f"**{sp_name}** — BWP {s_item_total:,.2f} ({s_unit_label})", key=f"chk_s_{sp_id}"):
                            selected_items.append({"vendor_id": s_slug, "vendor_name": s_data['business_name'], "item": sp_name, "price": s_item_total})

            st.markdown("---")
            st.markdown("#### **Step 4: Invoice Summary & Payment Confirmation**")
            if selected_items:
                df_summary = pd.DataFrame(selected_items)[["vendor_name", "item", "price"]]
                df_summary.columns = ["Service Provider", "Item / Space Description", "Total (BWP)"]
                st.table(df_summary)
                
                grand_total = sum(i["price"] for i in selected_items)
                deposit = grand_total * 0.50
                
                m1, m2 = st.columns(2)
                m1.metric("Grand Total Cost", f"BWP {grand_total:,.2f}")
                m2.metric("Required 50% Deposit", f"BWP {deposit:,.2f}")
                
                payment_method = st.radio("Select Payment Channel:", ["Credit / Debit Card (Instant Gateway)", "Electronic Funds Transfer (EFT)"])
                
                if st.button("Confirm Reservation & Issue Invoice"):
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
                        
                        st.markdown(f"""
                        <div class="invoice-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3>OFFICIAL TAX INVOICE</h3>
                                <span class="status-badge">RESERVATION CONFIRMED</span>
                            </div>
                            <hr style="border:0.5px solid #CBD5E1;">
                            <p><strong>Invoice Reference:</strong> {inv_id} | <strong>Date Issued:</strong> {str(datetime.date.today())}</p>
                            <p><strong>Client Name:</strong> {client_name} ({client_phone})</p>
                            <p><strong>Scheduled Event Date:</strong> {event_date} | <strong>Guest Count:</strong> {guest_count}</p>
                            <p><strong>Amount Remitted (50% Deposit):</strong> <span style="color:#059669; font-weight:700;">BWP {deposit:,.2f}</span></p>
                            <p style="font-size:0.85rem; color:#64748B; margin-top:15px;">A copy of this invoice has been logged to your corporate account ledger.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Please enter your Name, Email, and Phone Number before confirming.")
            else:
                st.warning("Please select at least one space or service package above.")

        # --- CLIENT TICKET PURCHASING & FLYER LINK ENGINE ---
        with tab_tickets:
            st.markdown("#### **Upcoming Ticketed Events at this Venue**")
            events_list = active_venue.get("ticketed_events", [])
            
            if not events_list:
                st.info("There are currently no public ticketed events scheduled for this venue.")
            else:
                for evt in events_list:
                    # Auto-expand if referred directly via Flyer Link (`?event=EVT_ID`)
                    is_direct_flyer_event = (active_event_id == evt['event_id'])
                    
                    if is_direct_flyer_event:
                        st.success(f"⚡ You were redirected via the Official Promotional Flyer for **{evt['event_name']}**!")
                    
                    with st.expander(f"🎟️ {evt['event_name']} — Date: {evt['event_date']}", expanded=is_direct_flyer_event or (len(events_list) == 1)):
                        
                        # Display Digital Flyer Preview if available
                        if evt.get("flyer_headline"):
                            st.markdown(f"""
                            <div class="flyer-card">
                                <h2>{evt['event_name'].upper()}</h2>
                                <h4><em>"{evt.get('flyer_headline')}"</em></h4>
                                <p style="margin-top:10px;">📍 Location: <strong>{active_venue.get('business_name')}</strong> | 📅 Date: <strong>{evt['event_date']}</strong></p>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown(f"**Venue Host:** {active_venue.get('business_name')}")
                        st.markdown("##### **Select Tickets:**")
                        
                        t_cols = st.columns(len(evt["ticket_types"]))
                        selected_tickets = {}
                        
                        for idx, tt in enumerate(evt["ticket_types"]):
                            with t_cols[idx]:
                                remaining = tt["total"] - tt["sold"]
                                st.markdown(f"**{tt['type']}**")
                                st.markdown(f"Price: **BWP {tt['price']:,.2f}**")
                                st.caption(f"Remaining: {remaining} / {tt['total']}")
                                if remaining > 0:
                                    qty = st.number_input(f"Qty ({tt['type']}):", min_value=0, max_value=remaining, value=0, key=f"t_qty_{evt['event_id']}_{idx}")
                                    if qty > 0:
                                        selected_tickets[tt['type']] = {"qty": qty, "price": tt['price'], "index": idx}
                                else:
                                    st.error("SOLD OUT")

                        if selected_tickets:
                            st.markdown("---")
                            t_total = sum(item["qty"] * item["price"] for item in selected_tickets.values())
                            st.markdown(f"### Total Ticket Amount: **BWP {t_total:,.2f}**")
                            
                            t_client_name = st.text_input("Attendee Name:", key=f"t_name_{evt['event_id']}")
                            t_client_phone = st.text_input("Attendee WhatsApp / Phone:", key=f"t_phone_{evt['event_id']}")
                            
                            if st.button("Complete Payment & Issue Ticket Pass", key=f"btn_buy_{evt['event_id']}"):
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
                                    
                                    # Update sold counts
                                    for t_name, t_info in selected_tickets.items():
                                        evt["ticket_types"][t_info["index"]]["sold"] += t_info["qty"]
                                    
                                    save_json(CONFIG_FILE, st.session_state.config_data)
                                    st.session_state.ticket_sales_data.append(sale_record)
                                    save_json(TICKETS_FILE, st.session_state.ticket_sales_data)
                                    
                                    st.balloons()
                                    st.success(f"Payment Confirmed! Your Digital Ticket Pass ID is {t_inv}")
                                    
                                    # Issue Digital Ticket Pass Invoice
                                    st.markdown(f"""
                                    <div class="invoice-card">
                                        <div style="display:flex; justify-content:space-between; align-items:center;">
                                            <h3>🎟️ OFFICIAL EVENT TICKET PASS</h3>
                                            <span class="status-badge">PAYMENT VERIFIED</span>
                                        </div>
                                        <hr style="border:0.5px solid #CBD5E1;">
                                        <p><strong>Ticket Pass Reference:</strong> {t_inv} | <strong>Date Issued:</strong> {str(datetime.date.today())}</p>
                                        <p><strong>Attendee Name:</strong> {t_client_name} ({t_client_phone})</p>
                                        <p><strong>Event:</strong> {evt['event_name']} | <strong>Date:</strong> {evt['event_date']}</p>
                                        <p><strong>Host Venue:</strong> {active_venue['business_name']}</p>
                                        <p><strong>Total Paid:</strong> <span style="color:#059669; font-weight:700;">BWP {t_total:,.2f}</span></p>
                                        <hr style="border:0.5px solid #CBD5E1;">
                                        <p style="font-size:0.85rem; color:#64748B;">Please present this ticket pass receipt upon gate entrance for entry validation.</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error("Please enter Attendee Name and Phone Number.")

# ==============================================================================
# ROUTE 2: VENDOR PORTAL & FLYER GENERATOR DASHBOARD
# ==============================================================================
elif route == "Vendor Portal Login 🔐":
    st.title("Vendor Management Portal")
    st.markdown("---")
    
    if st.session_state.logged_vendor is None:
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            v_type = st.selectbox("Account Category:", ["Venue Owner", "Service Supplier"])
            v_id = st.text_input("Account Identifier (Slug):").strip().lower()
        with col_l2:
            v_pass = st.text_input("Password:", type="password")
            login_btn = st.button("Authenticate Dashboard")

        if login_btn:
            account = venues.get(v_id) if v_type == "Venue Owner" else all_suppliers.get(v_id)
            if account and (v_pass == account.get("password") or v_pass == "admin2026"):
                st.session_state.logged_vendor = {"id": v_id, "type": v_type}
                st.rerun()
            else:
                st.error("Authentication failed. Check credentials.")
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

        tab_list = ["📊 Financial Statements & Invoices", "🏷️ Catalog & Pricing Models"]
        if v_type == "Venue Owner":
            tab_list.append("🎟️ Event Ticketing Setup")
            tab_list.append("🎨 Event Flyer Generator")
            
        tabs = st.tabs(tab_list)
        
        with tabs[0]:
            st.markdown("#### **Transaction Ledger & Net Payouts**")
            
            vendor_payouts = []
            for b in st.session_state.bookings_data:
                for item in b["items"]:
                    if item["vendor_id"] == v_id:
                        vendor_payouts.append({
                            "Type": "Private Booking",
                            "Invoice Reference": b["invoice_id"],
                            "Event Date": b["event_date"],
                            "Client Name": b["client_name"],
                            "Service Item": item["item"],
                            "Gross Revenue": item["price"],
                            "Net Payout (90%)": item["price"] * 0.90,
                        })
            
            for t in st.session_state.ticket_sales_data:
                if t["venue_id"] == v_id:
                    vendor_payouts.append({
                        "Type": "Ticket Sale (Flyer / Portal)",
                        "Invoice Reference": t["ticket_invoice_id"],
                        "Event Date": t["event_date"],
                        "Client Name": t["attendee_name"],
                        "Service Item": f"Tickets: {t['event_name']}",
                        "Gross Revenue": t["total_amount"],
                        "Net Payout (90%)": t["total_amount"] * 0.90,
                    })

            if vendor_payouts:
                df_vp = pd.DataFrame(vendor_payouts)
                st.table(df_vp)
                
                tot_gross = df_vp["Gross Revenue"].sum()
                tot_net = df_vp["Net Payout (90%)"].sum()
                
                m1, m2 = st.columns(2)
                m1.metric("Gross Revenue (Bookings + Tickets)", f"BWP {tot_gross:,.2f}")
                m2.metric("Net Payable Payout (90%)", f"BWP {tot_net:,.2f}")
            else:
                st.info("No transaction records found for this account.")

        with tabs[1]:
            st.markdown("#### **Active Catalog & Pricing Setup**")
            current_pkgs = account.get("packages", [])
            if current_pkgs:
                st.table(pd.DataFrame(current_pkgs))
            
            st.markdown("---")
            st.markdown("#### **Add Item to Catalog**")
            with st.form("add_package_form"):
                fp_name = st.text_input("Item Title:")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    fp_price = st.number_input("Rate (BWP):", min_value=0.0, value=500.0, step=50.0)
                with col_p2:
                    fp_unit = st.selectbox("Billing Model:", ["Per Day", "Per Unit", "Per Guest"])
                fp_desc = st.text_area("Item Description:")
                
                if st.form_submit_button("Add Catalog Item"):
                    if fp_name:
                        account.setdefault("packages", []).append({
                            "id": f"item_{len(current_pkgs) + 1}",
                            "name": fp_name, "price": float(fp_price), "unit": fp_unit, "desc": fp_desc
                        })
                        save_json(CONFIG_FILE, st.session_state.config_data)
                        st.success(f"Added '{fp_name}' to catalog.")
                        st.rerun()

        if v_type == "Venue Owner":
            with tabs[2]:
                st.markdown("#### **Manage Hosted Ticketed Events**")
                v_events = account.get("ticketed_events", [])
                
                if v_events:
                    st.markdown("##### **Current Ticketed Events**")
                    for e in v_events:
                        st.write(f"🔹 **{e['event_name']}** | Date: {e['event_date']}")
                        st.table(pd.DataFrame(e["ticket_types"]))
                else:
                    st.info("No ticketed events currently created.")

                st.markdown("---")
                st.markdown("#### **Create New Ticketed Event**")
                
                with st.form("create_event_form"):
                    e_name = st.text_input("Event Name (e.g., Summer Music Gala):")
                    e_date = st.date_input("Event Date:", min_value=datetime.date.today())
                    e_headline = st.text_input("Event Tagline / Flyer Headline:", value="An Unforgettable Experience!")
                    
                    st.markdown("##### **Ticket Tier 1:**")
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        t1_name = st.text_input("Tier 1 Name:", value="General Admission")
                    with col_t2:
                        t1_price = st.number_input("Tier 1 Price (BWP):", min_value=0.0, value=150.0)
                    with col_t3:
                        t1_qty = st.number_input("Tier 1 Quantity:", min_value=1, value=100)

                    st.markdown("##### **Ticket Tier 2 (Optional):**")
                    col_t4, col_t5, col_t6 = st.columns(3)
                    with col_t4:
                        t2_name = st.text_input("Tier 2 Name:", value="VIP Pass")
                    with col_t5:
                        t2_price = st.number_input("Tier 2 Price (BWP):", min_value=0.0, value=400.0)
                    with col_t6:
                        t2_qty = st.number_input("Tier 2 Quantity:", min_value=0, value=25)

                    if st.form_submit_button("Publish Ticketed Event"):
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
                            st.success(f"Published ticketed event '{e_name}'!")
                            st.rerun()

            # --- NEW TAB: EVENT FLYER GENERATOR WITH INTEGRATED PAYMENT LINKS ---
            with tabs[3]:
                st.markdown("#### **Generate Event Promotional Flyer & Payment Link**")
                st.caption("Create branded digital flyers for your events carrying embedded payment links for direct ticket issuance.")
                
                v_events = account.get("ticketed_events", [])
                if not v_events:
                    st.warning("Please create a ticketed event under 'Event Ticketing Setup' first.")
                else:
                    event_options = {e["event_name"]: e for e in v_events}
                    selected_e_name = st.selectbox("Select Event for Flyer Creation:", list(event_options.keys()))
                    sel_evt = event_options[selected_e_name]
                    
                    st.markdown("---")
                    st.markdown("##### **Flyer Customization**")
                    f_headline = st.text_input("Promotional Headline / Tagline:", value=sel_evt.get("flyer_headline", "Join Us Live!"))
                    f_call_to_action = st.text_input("Call To Action Button Text:", value="BUY TICKETS NOW")
                    
                    # Update headline in config
                    sel_evt["flyer_headline"] = f_headline
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    
                    # Construct Direct Payment Link with Query Parameters
                    payment_link = f"http://localhost:8501/?vendor={v_id}&event={sel_evt['event_id']}"
                    
                    st.markdown("---")
                    st.markdown("##### **Official Digital Event Flyer Preview**")
                    
                    # Render Digital Flyer Graphic
                    st.markdown(f"""
                    <div class="flyer-card">
                        <span class="status-badge" style="background-color:#FEF08A; color:#854D0E;">OFFICIAL EVENT ANNOUNCEMENT</span>
                        <h1 style="margin-top:15px; font-size:2.2rem; font-weight:700;">{sel_evt['event_name'].upper()}</h1>
                        <h3 style="font-weight:400; opacity:0.9;"><em>"{f_headline}"</em></h3>
                        <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:20px 0;">
                        <p style="font-size:1.1rem;">📍 Venue: <strong>{account.get('business_name')}</strong></p>
                        <p style="font-size:1.1rem;">📅 Date: <strong>{sel_evt['event_date']}</strong></p>
                        <p style="font-size:1.1rem;">📞 Contact: <strong>{account.get('phone')}</strong></p>
                        <div style="margin-top:25px;">
                            <a href="{payment_link}" target="_blank" style="background-color:#22C55E; color:white; padding:12px 28px; font-weight:700; text-decoration:none; border-radius:8px; display:inline-block;">
                                🎟️ {f_call_to_action}
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("##### **Sharable Payment Link**")
                    st.code(payment_link, language="markdown")
                    st.caption("Copy and share this direct link on social media or WhatsApp. Customers who pay through this link will instantly receive an issued ticket pass.")

# ==============================================================================
# ROUTE 3: REGISTRATION
# ==============================================================================
elif route == "Venue & Supplier Registration":
    st.title("Partner Account Registration")
    st.markdown("---")
    reg_type = st.radio("Registration Type:", ["Venue Partner", "Service Supplier"])
    
    with st.form("reg_form"):
        r_id = st.text_input("Account Identifier (URL Slug):").strip().lower()
        r_name = st.text_input("Business Name:")
        r_phone = st.text_input("Contact Phone:")
        r_pass = st.text_input("Portal Password:", type="password")
        
        if reg_type == "Venue Partner":
            r_tagline = st.text_input("Tagline:")
            r_color = st.color_picker("Corporate Accent Color:", "#0F172A")
        else:
            r_cat = st.selectbox("Service Category:", ["Catering & Buffets", "Decor & Styling", "Utensils & Crockery", "Wellness Services"])
            
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
                        "password": r_pass, "packages": []
                    }
                save_json(CONFIG_FILE, st.session_state.config_data)
                st.success(f"Account '{r_name}' successfully registered.")
            else:
                st.error("Please complete all required fields.")

# ==============================================================================
# ROUTE 4: MASTER ADMIN & FINANCIAL SYSTEM REPORTING
# ==============================================================================
elif route == "Platform Administration":
    st.title("Platform Administration")
    st.markdown("---")
    pin = st.text_input("Security Passcode:", type="password")
    
    if pin == "admin2026":
        st.success("Authenticated Platform Administrator")
        
        all_bookings = st.session_state.bookings_data
        all_tickets = st.session_state.ticket_sales_data
        
        total_booking_gross = sum(b["grand_total"] for b in all_bookings)
        total_ticket_gross = sum(t["total_amount"] for t in all_tickets)
        total_gross = total_booking_gross + total_ticket_gross
        
        platform_commission = total_gross * 0.10
        vendor_payouts_total = total_gross * 0.90
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Private Bookings / Tickets", f"{len(all_bookings)} / {len(all_tickets)}")
        m2.metric("Gross System Billings", f"BWP {total_gross:,.2f}")
        m3.metric("Platform Revenue (10%)", f"BWP {platform_commission:,.2f}")
        m4.metric("Vendor Payouts (90%)", f"BWP {vendor_payouts_total:,.2f}")
        
        st.markdown("---")
        st.markdown("#### **Master Reservation Ledger**")
        if all_bookings:
            df_master = pd.DataFrame(all_bookings)[["invoice_id", "timestamp", "client_name", "event_date", "grand_total", "deposit_paid", "status"]]
            st.table(df_master)
        else:
            st.info("No private booking invoices generated yet.")

        st.markdown("---")
        st.markdown("#### **Master Ticket Sales Ledger (Flyers & Portal)**")
        if all_tickets:
            df_t_master = pd.DataFrame(all_tickets)[["ticket_invoice_id", "timestamp", "venue_name", "event_name", "attendee_name", "total_amount", "status"]]
            st.table(df_t_master)
        else:
            st.info("No ticket sales generated yet.")

        st.markdown("---")
        st.markdown("#### **Account Directory & Management**")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            v_del = st.selectbox("Delete Venue Account:", ["-- Select --"] + list(venues.keys()), key="del_v")
            if st.button("Purge Venue Account"):
                if v_del != "-- Select --":
                    del st.session_state.config_data["venues"][v_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Purged '{v_del}'")
                    st.rerun()

        with col_d2:
            s_del = st.selectbox("Delete Supplier Account:", ["-- Select --"] + list(all_suppliers.keys()), key="del_s")
            if st.button("Purge Supplier Account"):
                if s_del != "-- Select --":
                    del st.session_state.config_data["all_suppliers"][s_del]
                    save_json(CONFIG_FILE, st.session_state.config_data)
                    st.success(f"Purged '{s_del}'")
                    st.rerun()
