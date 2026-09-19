import streamlit as st
import sqlite3
import datetime
import hashlib
import base64
import json
import os

# ---------------------------------------------------------
# 1. DATABASE & STORAGE ENGINE (NATIVE SQLITE - $0 COST)
# ---------------------------------------------------------
DB_FILE = "enterprise_platform.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Venues / Facilities Table
    c.execute('''CREATE TABLE IF NOT EXISTS venues (
        venue_id TEXT PRIMARY KEY,
        name TEXT, type TEXT, email TEXT, phone TEXT, whatsapp_no TEXT,
        address TEXT, max_capacity INTEGER, tax_id TEXT, bank_details TEXT,
        brand_color TEXT, brand_secondary TEXT, logo_url TEXT, flyer_image_url TEXT,
        approved_supporter_ids TEXT
    )''')
    
    # Venue Sub-Spaces Table
    c.execute('''CREATE TABLE IF NOT EXISTS spaces (
        space_id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_id TEXT, name TEXT, capacity INTEGER, daily_rate REAL, image_url TEXT,
        FOREIGN KEY(venue_id) REFERENCES venues(venue_id)
    )''')
    
    # Supporters / Vendors Table
    c.execute('''CREATE TABLE IF NOT EXISTS supporters (
        supporter_id TEXT PRIMARY KEY,
        business_name TEXT, category TEXT, contact_person TEXT, email TEXT,
        phone TEXT, bank_details TEXT, brand_color TEXT, logo_url TEXT
    )''')
    
    # Vendor Quotation / Item Templates Table
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supporter_id TEXT, item_name TEXT, description TEXT, unit_type TEXT,
        unit_price REAL, image_url TEXT,
        FOREIGN KEY(supporter_id) REFERENCES supporters(supporter_id)
    )''')
    
    # Venue Bookings Table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        booking_id TEXT PRIMARY KEY, venue_id TEXT, space_name TEXT,
        customer_name TEXT, customer_email TEXT, customer_phone TEXT,
        booking_date TEXT, days INTEGER, venue_cost REAL, payment_method TEXT,
        status TEXT, pop_reference TEXT, created_at TEXT,
        FOREIGN KEY(venue_id) REFERENCES venues(venue_id)
    )''')
    
    # Vendor Invoices Table
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_invoices (
        vendor_invoice_id TEXT PRIMARY KEY, parent_booking_id TEXT, supporter_id TEXT,
        venue_name TEXT, customer_name TEXT, customer_email TEXT, customer_phone TEXT,
        event_date TEXT, items_json TEXT, total_amount REAL, payment_method TEXT,
        status TEXT, pop_reference TEXT, created_at TEXT,
        FOREIGN KEY(supporter_id) REFERENCES supporters(supporter_id)
    )''')
    
    # Event Tickets Table
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY, verification_hash TEXT, event_id TEXT,
        event_title TEXT, venue_id TEXT, venue_name TEXT, venue_logo TEXT,
        buyer TEXT, email TEXT, qty INTEGER, total_paid REAL, payment_method TEXT,
        status TEXT, pop_reference TEXT, scanned_at TEXT
    )''')
    
    # Events Table
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY, venue_id TEXT, venue_name TEXT, space_name TEXT,
        title TEXT, date TEXT, price REAL, description TEXT, flyer_url TEXT
    )''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------
# 2. UTILITY FUNCTIONS
# ---------------------------------------------------------
SPACE_PRESETS = [
    "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=500",
    "https://images.unsplash.com/photo-1511578314322-379afb476865?w=500",
    "https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=500",
    "https://images.unsplash.com/photo-1540575861501-7cf05a4b125a?w=500"
]
DEFAULT_LOGO = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200"

def process_image_upload(uploaded_file, fallback_url):
    if uploaded_file is not None:
        try:
            bytes_data = uploaded_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode()
            mime_type = uploaded_file.type if uploaded_file.type else "image/png"
            return f"data:{mime_type};base64,{b64_str}"
        except Exception:
            return fallback_url
    return fallback_url

def generate_wa_link(phone, msg):
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    encoded = base64.b64encode(msg.encode()).decode() # lightweight safety
    import urllib.parse
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

# ---------------------------------------------------------
# 3. PAGE SETUP & STYLES
# ---------------------------------------------------------
st.set_page_config(page_title="Enterprise Venue & Event Portal", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #F8FAFC; }
        .invoice-box {
            background: #FFFFFF; padding: 2rem; border-radius: 8px;
            border: 1px solid #CBD5E1; margin-bottom: 1.5rem;
        }
        .profile-card { padding: 1.5rem; border-radius: 8px; color: #FFFFFF !important; margin-bottom: 1.5rem; }
        .logo-img { max-height: 60px; max-width: 180px; object-fit: contain; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. SIDEBAR AUTH & NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown("## 🏢 ENTERPRISE GATEWAY")
st.sidebar.caption("Multi-Tenant Venue & Supporter Operations")
st.sidebar.divider()

user_role = st.sidebar.radio(
    "Active Workspace Console:",
    [
        "Public Booking Portal",
        "Facility Owner Console",
        "Facility Supporter Console",
        "Gate Access & Mobile Scanner",
        "Master Platform Control"
    ]
)

st.sidebar.divider()
with st.sidebar.expander("System Maintenance"):
    if st.button("Reset Local SQLite Database", type="primary", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            init_db()
            st.session_state.clear()
            st.success("Database wiped and re-initialized.")
            st.rerun()

# ---------------------------------------------------------
# 5. MODULE 1: PUBLIC BOOKING PORTAL
# ---------------------------------------------------------
if user_role == "Public Booking Portal":
    st.title("Central Venue Booking & Public Ticketing Portal")
    st.caption("Select your venue, customize vendor services, and receive printable invoices.")
    st.divider()

    tab_book, tab_tickets = st.tabs(["Book Venue & Services", "Public Event Tickets"])

    with tab_book:
        conn = get_db_connection()
        venues = conn.execute("SELECT * FROM venues").fetchall()
        
        if not venues:
            st.warning("No facilities currently listed. Register a venue under the Facility Owner Console.")
        else:
            v_names = [v['name'] for v in venues]
            sel_v_name = st.selectbox("1. Choose Venue / Facility:", v_names)
            sel_venue = next(v for v in venues if v['name'] == sel_v_name)

            col1, col2 = st.columns([1, 2])
            col1.image(sel_venue['flyer_image_url'] or SPACE_PRESETS[0], use_container_width=True)
            col2.markdown(f"""
                <div style="background:{sel_venue['brand_color']}; padding:1rem; border-radius:8px; color:white;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2>{sel_venue['name']}</h2>
                        <img src="{sel_venue['logo_url'] or DEFAULT_LOGO}" class="logo-img" style="background:white; padding:2px; border-radius:4px;">
                    </div>
                    <p>📍 {sel_venue['address']} | 👥 Max Capacity: {sel_venue['max_capacity']:,}<br>
                    💬 WhatsApp POP Receiver: {sel_venue['whatsapp_no']}</p>
                </div>
            """, unsafe_allow_html=True)

            # Sub-Spaces
            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (sel_venue['venue_id'],)).fetchall()
            if not spaces:
                st.warning("No sub-spaces configured for this venue yet.")
            else:
                st.divider()
                st.markdown("### 2. Select Space & Event Date")
                sc1, sc2, sc3 = st.columns(3)
                sel_sp_name = sc1.selectbox("Select Space", [s['name'] for s in spaces])
                sel_space = next(s for s in spaces if s['name'] == sel_sp_name)
                booking_date = sc2.date_input("Event Date", min_value=datetime.date.today())
                booking_days = sc3.number_input("Days Required", min_value=1, value=1)

                date_str = str(booking_date)
                space_cost = sel_space['daily_rate'] * booking_days

                # Check double bookings
                existing = conn.execute("SELECT * FROM bookings WHERE venue_id = ? AND space_name = ? AND booking_date = ? AND status != 'Cancelled'", 
                                        (sel_venue['venue_id'], sel_sp_name, date_str)).fetchone()

                if existing:
                    st.error(f"❌ Date Locked: '{sel_sp_name}' is already reserved/pending on {date_str}.")
                else:
                    st.success(f"✅ Date Available: '{sel_sp_name}' is open on {date_str}.")
                    
                    st.divider()
                    st.markdown("### 3. Approved Facility Supporter Packages")
                    
                    # Approved vendors
                    approved_ids = json.loads(sel_venue['approved_supporter_ids'] or "[]")
                    selected_vendor_orders = {}

                    if approved_ids:
                        placeholders = ','.join('?' * len(approved_ids))
                        supporters = conn.execute(f"SELECT * FROM supporters WHERE supporter_id IN ({placeholders})", approved_ids).fetchall()
                        
                        for sup in supporters:
                            templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ?", (sup['supporter_id'],)).fetchall()
                            if templates:
                                with st.expander(f"Add Services: {sup['business_name']} ({sup['category']})"):
                                    sup_items = []
                                    sup_total = 0.0
                                    for t in templates:
                                        tc1, tc2 = st.columns([1, 3])
                                        if t['image_url']: tc1.image(t['image_url'], use_container_width=True)
                                        tc2.markdown(f"**{t['item_name']}** — BWP {t['unit_price']:,.2f} / {t['unit_type']}")
                                        if t['description']: tc2.caption(t['description'])
                                        qty = tc2.number_input("Qty", min_value=0, value=0, key=f"qty_{sup['supporter_id']}_{t['template_id']}")
                                        if qty > 0:
                                            cost = qty * t['unit_price']
                                            sup_total += cost
                                            sup_items.append({"item_name": t['item_name'], "qty": qty, "unit_price": t['unit_price'], "subtotal": cost})
                                    if sup_items:
                                        selected_vendor_orders[sup['supporter_id']] = {"info": sup, "items": sup_items, "total": sup_total}
                    else:
                        st.info("No supplier add-ons currently assigned to this facility.")

                    st.divider()
                    st.markdown("### 4. Direct Invoices & Payment Summary")

                    # Venue Invoice
                    st.markdown(f"""
                    <div class="invoice-box" style="border-top: 5px solid {sel_venue['brand_color']};">
                        <div style="display:flex; justify-content:space-between;">
                            <div>
                                <h3>INVOICE A: VENUE HIRE ({sel_venue['name']})</h3>
                                <p>Space: {sel_sp_name} ({booking_days} day/s)</p>
                            </div>
                            <div style="text-align:right;">
                                <h4>Total: BWP {space_cost:,.2f}</h4>
                                <p style="color:#D97706; font-weight:bold;">Pending Direct POP</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Vendor Invoices
                    for s_id, v_data in selected_vendor_orders.items():
                        s_info = v_data['info']
                        st.markdown(f"""
                        <div class="invoice-box" style="border-top: 5px solid {s_info['brand_color']};">
                            <div style="display:flex; justify-content:space-between;">
                                <div>
                                    <h3>INVOICE: VENDOR SERVICE ({s_info['business_name']})</h3>
                                    <p>Category: {s_info['category']} | WhatsApp: {s_info['phone']}</p>
                                </div>
                                <div style="text-align:right;">
                                    <h4>Total: BWP {v_data['total']:,.2f}</h4>
                                    <p style="color:#D97706; font-weight:bold;">Pending Direct POP</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with st.form("confirm_booking_form"):
                        c_name = st.text_input("Full Name / Business Name*")
                        c_email = st.text_input("Delivery Email*")
                        c_phone = st.text_input("WhatsApp / Phone Number*")
                        c_pay = st.selectbox("Selected Payment Option", ["eWallet", "Orange Money", "Pay2Cell", "Direct Deposit"])

                        if st.form_submit_button("Submit Reservation & Request Invoices", type="primary"):
                            if c_name and c_email and c_phone:
                                b_id = f"BK-{int(datetime.datetime.now().timestamp())}"
                                created_date = str(datetime.date.today())
                                
                                conn.execute("""INSERT INTO bookings 
                                    (booking_id, venue_id, space_name, customer_name, customer_email, customer_phone, booking_date, days, venue_cost, payment_method, status, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP / Verification', ?)""",
                                    (b_id, sel_venue['venue_id'], sel_sp_name, c_name, c_email, c_phone, date_str, booking_days, space_cost, c_pay, created_date))

                                for s_id, v_data in selected_vendor_orders.items():
                                    v_inv_id = f"VINV-{int(datetime.datetime.now().timestamp())}"
                                    conn.execute("""INSERT INTO vendor_invoices
                                        (vendor_invoice_id, parent_booking_id, supporter_id, venue_name, customer_name, customer_email, customer_phone, event_date, items_json, total_amount, payment_method, status, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP', ?)""",
                                        (v_inv_id, b_id, s_id, sel_venue['name'], c_name, c_email, c_phone, date_str, json.dumps(v_data['items']), v_data['total'], c_pay, created_date))

                                conn.commit()
                                st.success(f"Booking #{b_id} Submitted! Send Proof of Payment via WhatsApp to {sel_venue['whatsapp_no']}.")
                                st.rerun()
                            else:
                                st.error("Please fill in required fields.")
        conn.close()

    with tab_tickets:
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events").fetchall()
        if not events:
            st.info("No upcoming event tickets listed.")
        else:
            for ev in events:
                v = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (ev['venue_id'],)).fetchone()
                col1, col2 = st.columns([1, 2])
                col1.image(ev['flyer_url'] or SPACE_PRESETS[0], use_container_width=True)
                col2.markdown(f"### {ev['title']}")
                col2.write(f"Venue: {ev['venue_name']} | Date: {ev['date']} | Price: BWP {ev['price']:,.2f}")
                
                with col2.form(f"tkt_buy_{ev['event_id']}"):
                    t_qty = st.number_input("Qty", min_value=1, value=1)
                    t_buyer = st.text_input("Buyer Full Name*")
                    t_email = st.text_input("Email*")
                    t_pay = st.selectbox("Payment", ["eWallet", "Orange Money", "Pay2Cell", "Direct Deposit"])
                    
                    if st.form_submit_button("Request Admission Ticket"):
                        if t_buyer and t_email:
                            tkt_id = f"TKT-{int(datetime.datetime.now().timestamp())}"
                            sec_hash = f"HASH-{hashlib.sha256(f'{tkt_id}-{t_email}'.encode()).hexdigest()[:10].upper()}"
                            conn.execute("""INSERT INTO tickets
                                (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP / Unverified')""",
                                (tkt_id, sec_hash, ev['event_id'], ev['title'], v['venue_id'] if v else "", ev['venue_name'], v['logo_url'] if v else DEFAULT_LOGO, t_buyer, t_email, t_qty, t_qty*ev['price'], t_pay))
                            conn.commit()
                            
                            wa_msg = f"Hello {ev['venue_name']}, I purchased ticket {tkt_id} for {ev['title']}. Here is my POP."
                            wa_url = generate_wa_link(v['whatsapp_no'] if v else "26770000000", wa_msg)
                            st.warning("Ticket Requested!")
                            st.markdown(f"[💬 Click Here to Send POP via WhatsApp]({wa_url})")
                        else:
                            st.error("Provide buyer name and email.")
        conn.close()

# ---------------------------------------------------------
# 6. MODULE 2: FACILITY OWNER CONSOLE
# ---------------------------------------------------------
elif user_role == "Facility Owner Console":
    st.title("Facility Owner Console & Asset Curation")
    st.caption("Manage facility spaces, set corporate branding, approve vendors, and verify POP payments.")
    st.divider()

    conn = get_db_connection()
    venues = conn.execute("SELECT * FROM venues").fetchall()

    if not venues:
        st.info("No venue profile found. Please complete registration below.")
        with st.form("reg_venue_form"):
            f_name = st.text_input("Venue Name*")
            f_type = st.selectbox("Facility Type", ["Convention Center", "Hotel Ballroom", "Outdoor Arena", "Hall"])
            f_email = st.text_input("Manager Email*")
            f_phone = st.text_input("Phone Number*")
            f_whatsapp = st.text_input("WhatsApp POP Number*", placeholder="26771234567")
            f_address = st.text_input("Physical Address*")
            f_cap = st.number_input("Overall Capacity", value=1000)
            f_tax = st.text_input("Tax / CIPA ID*")
            f_bank = st.text_area("Bank Payout Details*")
            f_logo = st.file_uploader("Company Logo", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("Create Venue Profile"):
                if f_name and f_email and f_whatsapp:
                    v_id = f"v_{int(datetime.datetime.now().timestamp())}"
                    logo_url = process_image_upload(f_logo, DEFAULT_LOGO)
                    conn.execute("""INSERT INTO venues 
                        (venue_id, name, type, email, phone, whatsapp_no, address, max_capacity, tax_id, bank_details, brand_color, brand_secondary, logo_url, flyer_image_url, approved_supporter_ids)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '#0F172A', '#2563EB', ?, ?, '[]')""",
                        (v_id, f_name, f_type, f_email, f_phone, f_whatsapp, f_address, f_cap, f_tax, f_bank, logo_url, SPACE_PRESETS[0]))
                    conn.commit()
                    st.success("Venue Profile Saved!")
                    st.rerun()
    else:
        cur_v = venues[0]
        
        st.markdown(f"""
            <div class="profile-card" style="background:{cur_v['brand_color']};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h2>🏛️ {cur_v['name']}</h2>
                        <p>📍 {cur_v['address']} | 💬 WhatsApp POP: {cur_v['whatsapp_no']}</p>
                    </div>
                    <img src="{cur_v['logo_url'] or DEFAULT_LOGO}" class="logo-img" style="background:white; padding:4px; border-radius:6px;">
                </div>
            </div>
        """, unsafe_allow_html=True)

        v_tab1, v_tab2, v_tab3, v_tab4 = st.tabs(["Manage Sub-Spaces", "🤝 Approved Vendors", "✅ Verify POPs", "📊 Financial Analytics"])

        with v_tab1:
            with st.form("add_space_form"):
                s_name = st.text_input("Sub-Space / Hall Name")
                s_cap = st.number_input("Capacity", value=250)
                s_rate = st.number_input("Daily Rate (BWP)", value=2500.0)
                s_img = st.file_uploader("Space Photo", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("Add Hire Sub-Space"):
                    if s_name:
                        img_url = process_image_upload(s_img, SPACE_PRESETS[0])
                        conn.execute("INSERT INTO spaces (venue_id, name, capacity, daily_rate, image_url) VALUES (?, ?, ?, ?, ?)",
                                     (cur_v['venue_id'], s_name, s_cap, s_rate, img_url))
                        conn.commit()
                        st.success("Sub-Space Added!")
                        st.rerun()

            st.divider()
            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (cur_v['venue_id'],)).fetchall()
            for sp in spaces:
                st.write(f"• **{sp['name']}** — Cap: {sp['capacity']} | Rate: BWP {sp['daily_rate']:,.2f}/day")

        with v_tab2:
            st.markdown("#### Select Global Vendors Approved for Your Venue")
            all_supporters = conn.execute("SELECT * FROM supporters").fetchall()
            cur_approved = set(json.loads(cur_v['approved_supporter_ids'] or "[]"))

            if not all_supporters:
                st.info("No global supporters registered on platform yet.")
            else:
                with st.form("approve_vendors_form"):
                    new_approved = []
                    for sup in all_supporters:
                        chk = st.checkbox(f"**{sup['business_name']}** ({sup['category']})", value=(sup['supporter_id'] in cur_approved))
                        if chk: new_approved.append(sup['supporter_id'])
                    if st.form_submit_button("Save Approved Network"):
                        conn.execute("UPDATE venues SET approved_supporter_ids = ? WHERE venue_id = ?",
                                     (json.dumps(new_approved), cur_v['venue_id']))
                        conn.commit()
                        st.success("Approved vendor list updated!")
                        st.rerun()

        with v_tab3:
            st.markdown("#### Pending Booking Payment Verification")
            pending_bks = conn.execute("SELECT * FROM bookings WHERE venue_id = ? AND status = 'Pending POP / Verification'", (cur_v['venue_id'],)).fetchall()
            if not pending_bks:
                st.success("No pending POPs.")
            else:
                for bk in pending_bks:
                    st.write(f"**Booking #{bk['booking_id']}** — {bk['customer_name']} | BWP {bk['venue_cost']:,.2f}")
                    with st.form(f"verify_bk_{bk['booking_id']}"):
                        txn_ref = st.text_input("Enter WhatsApp Transaction Reference")
                        if st.form_submit_button("✅ Verify & Confirm Booking"):
                            if txn_ref:
                                conn.execute("UPDATE bookings SET status = 'Confirmed / Paid', pop_reference = ? WHERE booking_id = ?", (txn_ref, bk['booking_id']))
                                conn.commit()
                                st.success("Booking verified!")
                                st.rerun()

        with v_tab4:
            st.markdown("#### 📊 Financial Statements & CSV Export")
            bks = conn.execute("SELECT * FROM bookings WHERE venue_id = ?", (cur_v['venue_id'],)).fetchall()
            paid_sum = sum(b['venue_cost'] for b in bks if b['status'] == 'Confirmed / Paid')
            pending_sum = sum(b['venue_cost'] for b in bks if 'Pending' in b['status'])

            m1, m2 = st.columns(2)
            m1.metric("Confirmed Revenue", f"BWP {paid_sum:,.2f}")
            m2.metric("Outstanding Unverified", f"BWP {pending_sum:,.2f}")

            if bks:
                # Printable HTML/CSS Invoice Download Tool
                st.divider()
                st.markdown("##### Printable Invoices & CSV Ledger")
                
                csv_data = "Booking ID,Customer,Space,Date,Cost,Status,POP Ref\n" + "\n".join([f"{b['booking_id']},{b['customer_name']},{b['space_name']},{b['booking_date']},{b['venue_cost']},{b['status']},{b['pop_reference']}" for b in bks])
                st.download_button("📥 Download Financial CSV Export", csv_data, file_name="facility_revenue.csv", mime="text/csv")

    conn.close()

# ---------------------------------------------------------
# 7. MODULE 3: FACILITY SUPPORTER CONSOLE
# ---------------------------------------------------------
elif user_role == "Facility Supporter Console":
    st.title("Facility Supporter Console (Vendors)")
    st.caption("Register supplier profiles, configure service pricing packages, and confirm customer POPs.")
    st.divider()

    conn = get_db_connection()
    supporters = conn.execute("SELECT * FROM supporters").fetchall()

    sup_mode = st.radio("Vendor Options:", ["Select Existing Account", "Create New Vendor Profile"], horizontal=True)

    if sup_mode == "Create New Vendor Profile":
        with st.form("reg_supporter_form"):
            s_name = st.text_input("Trading Business Name*")
            s_cat = st.selectbox("Category", ["Catering & Cutlery", "Stage & Decor", "Sound & AV", "Florist", "Security"])
            s_person = st.text_input("Contact Person*")
            s_email = st.text_input("Email*")
            s_phone = st.text_input("WhatsApp Number for POPs*", placeholder="26771234567")
            s_bank = st.text_area("Bank Details*")
            s_color = st.color_picker("Brand Color", "#1E293B")
            s_logo = st.file_uploader("Logo", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("Register Supporter Account"):
                if s_name and s_phone and s_bank:
                    sup_id = f"sup_{int(datetime.datetime.now().timestamp())}"
                    logo_url = process_image_upload(s_logo, DEFAULT_LOGO)
                    conn.execute("""INSERT INTO supporters 
                        (supporter_id, business_name, category, contact_person, email, phone, bank_details, brand_color, logo_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (sup_id, s_name, s_cat, s_person, s_email, s_phone, s_bank, s_color, logo_url))
                    conn.commit()
                    st.success("Supporter Registered!")
                    st.rerun()
    else:
        if not supporters:
            st.info("No vendor profiles found.")
        else:
            sel_sup_name = st.selectbox("Active Supporter Profile:", [s['business_name'] for s in supporters])
            cur_sup = next(s for s in supporters if s['business_name'] == sel_sup_name)

            st.markdown(f"""
                <div class="profile-card" style="background:{cur_sup['brand_color']};">
                    <h2>🚚 {cur_sup['business_name']}</h2>
                    <p>Category: {cur_sup['category']} | WhatsApp POP: {cur_sup['phone']}</p>
                </div>
            """, unsafe_allow_html=True)

            vtab1, vtab2 = st.tabs(["Service Offerings Catalog", "✅ Verify Invoices"])

            with vtab1:
                with st.form("add_pkg_form"):
                    i_name = st.text_input("Package Item Name*")
                    i_desc = st.text_area("Description / Package Specifications")
                    i_type = st.selectbox("Billing Unit Metric", ["Per Guest", "Per Day", "Flat Rate", "Per Hour"])
                    i_price = st.number_input("Rate Price (BWP)", min_value=1.0, value=150.0)
                    i_photo = st.file_uploader("Service Photo", type=["png", "jpg", "jpeg"])

                    if st.form_submit_button("Add Offering Item"):
                        if i_name:
                            img_url = process_image_upload(i_photo, SPACE_PRESETS[1])
                            conn.execute("""INSERT INTO vendor_templates 
                                (supporter_id, item_name, description, unit_type, unit_price, image_url)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                                (cur_sup['supporter_id'], i_name, i_desc, i_type, i_price, img_url))
                            conn.commit()
                            st.success("Offering Item Added!")
                            st.rerun()

                st.divider()
                templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ?", (cur_sup['supporter_id'],)).fetchall()
                for t in templates:
                    st.write(f"• **{t['item_name']}** — BWP {t['unit_price']:,.2f} / {t['unit_type']}")

            with vtab2:
                v_invs = conn.execute("SELECT * FROM vendor_invoices WHERE supporter_id = ? AND status = 'Pending POP'", (cur_sup['supporter_id'],)).fetchall()
                if not v_invs:
                    st.success("No pending customer POPs.")
                else:
                    for inv in v_invs:
                        st.write(f"**Invoice #{inv['vendor_invoice_id']}** — Client: {inv['customer_name']} | BWP {inv['total_amount']:,.2f}")
                        with st.form(f"verify_vinv_{inv['vendor_invoice_id']}"):
                            ref = st.text_input("Enter WhatsApp Transaction Ref")
                            if st.form_submit_button("✅ Verify Vendor POP"):
                                if ref:
                                    conn.execute("UPDATE vendor_invoices SET status = 'PAID & VERIFIED', pop_reference = ? WHERE vendor_invoice_id = ?", (ref, inv['vendor_invoice_id']))
                                    conn.commit()
                                    st.success("Invoice Paid!")
                                    st.rerun()
    conn.close()

# ---------------------------------------------------------
# 8. MODULE 4: GATE ACCESS & CAMERA SCANNER ($0 COST)
# ---------------------------------------------------------
elif user_role == "Gate Access & Mobile Scanner":
    st.title("Door Gate Access & Camera Verification")
    st.caption("Scan QR ticket passes using smartphone/laptop native browser camera.")
    st.divider()

    conn = get_db_connection()
    
    st.markdown("##### 📷 Native Browser Camera Scanner")
    camera_file = st.camera_input("Point camera at visitor ticket pass")

    scan_input = st.text_input("Or Enter Verification Hash / Ticket ID manually:")

    if st.button("Verify Ticket Admission", type="primary"):
        target_str = scan_input.strip().upper()
        if target_str:
            tkt = conn.execute("SELECT * FROM tickets WHERE verification_hash = ? OR ticket_id = ?", (target_str, target_str)).fetchone()
            if tkt:
                if tkt['status'] == 'VALID':
                    conn.execute("UPDATE tickets SET status = 'USED / SCANNED', scanned_at = ? WHERE ticket_id = ?", (str(datetime.datetime.now()), tkt['ticket_id']))
                    conn.commit()
                    st.success(f"✅ ACCESS GRANTED: {tkt['buyer']} ({tkt['qty']} Person/s) — Event: {tkt['event_title']}")
                elif 'Pending' in tkt['status']:
                    st.warning("⚠️ UNVERIFIED TICKET: Payment POP has not been verified by owner.")
                else:
                    st.error("❌ INVALID: Pass already redeemed/scanned.")
            else:
                st.error("❌ Invalid Pass Verification Hash.")
    conn.close()

# ---------------------------------------------------------
# 9. MODULE 5: MASTER PLATFORM CONTROL
# ---------------------------------------------------------
elif user_role == "Master Platform Control":
    st.title("Master Enterprise Platform Control")
    st.caption("Executive overview and structured data audit tables.")
    st.divider()

    conn = get_db_connection()
    v_count = conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0]
    s_count = conn.execute("SELECT COUNT(*) FROM supporters").fetchone()[0]
    b_count = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    i_count = conn.execute("SELECT COUNT(*) FROM vendor_invoices").fetchone()[0]
    t_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Venues", v_count)
    m2.metric("Supporters", s_count)
    m3.metric("Bookings", b_count)
    m4.metric("Vendor Invoices", i_count)
    m5.metric("Tickets", t_count)

    st.divider()
    adm1, adm2, adm3 = st.tabs(["Facilities Ledger", "Supporters Ledger", "Bookings Ledger"])

    with adm1:
        venues = conn.execute("SELECT venue_id, name, type, email, phone, whatsapp_no, max_capacity FROM venues").fetchall()
        if venues: st.dataframe([dict(v) for v in venues], use_container_width=True)

    with adm2:
        sups = conn.execute("SELECT supporter_id, business_name, category, contact_person, email, phone FROM supporters").fetchall()
        if sups: st.dataframe([dict(s) for s in sups], use_container_width=True)

    with adm3:
        bks = conn.execute("SELECT booking_id, venue_id, space_name, customer_name, booking_date, venue_cost, status FROM bookings").fetchall()
        if bks: st.dataframe([dict(b) for b in bks], use_container_width=True)

    conn.close()
