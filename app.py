import streamlit as st
import sqlite3
import datetime
import hashlib
import base64
import json
import os
import io

# ReportLab Engine (In-Memory PDF Generation)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# QR Code Engine
import qrcode
from PIL import Image

# ---------------------------------------------------------
# 1. DATABASE & STORAGE ENGINE (CLOUD-READY SQL)
# ---------------------------------------------------------
DB_FILE = "enterprise_platform.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Auth Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, role TEXT, tenant_id TEXT
    )''')

    # Venues
    c.execute('''CREATE TABLE IF NOT EXISTS venues (
        venue_id TEXT PRIMARY KEY, name TEXT, type TEXT, email TEXT, phone TEXT, whatsapp_no TEXT,
        address TEXT, max_capacity INTEGER, tax_id TEXT, bank_details TEXT, brand_color TEXT,
        logo_url TEXT, flyer_image_url TEXT, approved_supporter_ids TEXT
    )''')
    
    # Sub-Spaces
    c.execute('''CREATE TABLE IF NOT EXISTS spaces (
        space_id INTEGER PRIMARY KEY AUTOINCREMENT, venue_id TEXT, name TEXT, capacity INTEGER, daily_rate REAL, image_url TEXT
    )''')
    
    # Supporters / Vendors
    c.execute('''CREATE TABLE IF NOT EXISTS supporters (
        supporter_id TEXT PRIMARY KEY, business_name TEXT, category TEXT, contact_person TEXT,
        email TEXT, phone TEXT, bank_details TEXT, brand_color TEXT, logo_url TEXT
    )''')
    
    # Vendor Package Templates
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT, supporter_id TEXT, item_name TEXT, description TEXT,
        unit_type TEXT, unit_price REAL, image_url TEXT
    )''')
    
    # Venue Bookings
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        booking_id TEXT PRIMARY KEY, venue_id TEXT, space_name TEXT, customer_name TEXT,
        customer_email TEXT, customer_phone TEXT, booking_date TEXT, days INTEGER, venue_cost REAL,
        payment_method TEXT, status TEXT, pop_reference TEXT, created_at TEXT
    )''')
    
    # Vendor Invoices
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_invoices (
        vendor_invoice_id TEXT PRIMARY KEY, parent_booking_id TEXT, supporter_id TEXT, venue_name TEXT,
        customer_name TEXT, customer_email TEXT, customer_phone TEXT, event_date TEXT, items_json TEXT,
        total_amount REAL, payment_method TEXT, status TEXT, pop_reference TEXT, created_at TEXT
    )''')
    
    # Tickets
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY, verification_hash TEXT, event_id TEXT, event_title TEXT, venue_id TEXT,
        venue_name TEXT, venue_logo TEXT, buyer TEXT, email TEXT, qty INTEGER, total_paid REAL,
        payment_method TEXT, status TEXT, pop_reference TEXT, scanned_at TEXT
    )''')
    
    # Events
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY, venue_id TEXT, venue_name TEXT, space_name TEXT, title TEXT, date TEXT,
        price REAL, description TEXT, flyer_url TEXT
    )''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    # Replace DB_FILE string with Supabase/PostgreSQL URI when deploying to production
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------
# 2. LIGHTWEIGHT IMAGE & IN-MEMORY PDF ENGINE
# ---------------------------------------------------------
DEFAULT_LOGO = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150"
SPACE_PRESETS = ["https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=400"]

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def process_compressed_image_upload(uploaded_file, fallback_url, max_dim=600):
    """Compresses uploaded images to JPEG max 600px width/height before base64 encoding to minimize DB size."""
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail((max_dim, max_dim))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=65, optimize=True)
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception:
            return fallback_url
    return fallback_url

def generate_qr_code_base64(data_string):
    qr = qrcode.QRCode(version=1, box_size=6, border=1)
    qr.add_data(data_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def generate_in_memory_pdf_bytes(title_text, inv_id, created_at, entity_name, tax_id, client_name, client_email, items_list, total_amount, bank_details):
    """Generates PDF directly in RAM using BytesIO. No file saved to server disk."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'))
    story.append(Paragraph(f"{title_text.upper()}", title_style))
    story.append(Spacer(1, 10))

    meta_data = [
        [f"Invoice Ref: {inv_id}", f"Date: {created_at}"],
        [f"Issuer: {entity_name}", f"Tax ID / CIPA: {tax_id}"],
        [f"Billed To: {client_name}", f"Email: {client_email}"]
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    table_data = [["Description / Item", "Qty", "Rate (BWP)", "Subtotal (BWP)"]]
    for item in items_list:
        table_data.append([
            item.get('item_name', 'Service Item'),
            str(item.get('qty', 1)),
            f"{item.get('unit_price', 0):,.2f}",
            f"{item.get('subtotal', 0):,.2f}"
        ])
    table_data.append(["TOTAL DUE", "", "", f"BWP {total_amount:,.2f}"])

    t_items = Table(table_data, colWidths=[240, 90, 105, 105])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')
    ]))
    story.append(t_items)
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Payment Instructions & Bank Account:</b><br/>{bank_details}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------------
# 3. PAGE SETUP & STYLES
# ---------------------------------------------------------
st.set_page_config(page_title="Enterprise Venue Gateway", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #F8FAFC; }
        .invoice-box { background: #FFFFFF; padding: 1.5rem; border-radius: 8px; border: 1px solid #CBD5E1; margin-bottom: 1.5rem; }
        .profile-card { padding: 1.2rem; border-radius: 8px; color: #FFFFFF !important; margin-bottom: 1rem; }
        .logo-img { max-height: 50px; max-width: 150px; object-fit: contain; }
        @media print {
            [data-testid="stSidebar"], button, header { display: none !important; }
        }
    </style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None
    st.session_state["tenant_id"] = None

# ---------------------------------------------------------
# 4. SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown("## 🏢 ENTERPRISE GATEWAY")
st.sidebar.caption("Zero-Storage Cloud Architecture")
st.sidebar.divider()

user_role = st.sidebar.radio(
    "Active Console:",
    [
        "Public Booking Portal",
        "Facility Owner Console",
        "Facility Supporter Console",
        "Gate Access & Mobile Scanner",
        "Master Platform Control"
    ]
)

st.sidebar.divider()
if st.session_state["authenticated"]:
    st.sidebar.success(f"Logged in: {st.session_state['user_email']}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = None
        st.session_state["user_role"] = None
        st.session_state["tenant_id"] = None
        st.rerun()

with st.sidebar.expander("System Utilities"):
    if st.button("Reset System Database", type="primary", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            init_db()
            st.session_state.clear()
            st.success("Database re-initialized.")
            st.rerun()

# ---------------------------------------------------------
# 5. MODULE 1: PUBLIC BOOKING PORTAL
# ---------------------------------------------------------
if user_role == "Public Booking Portal":
    st.title("Central Venue Booking & Public Ticketing Portal")
    st.caption("Reserve enterprise facilities, customize vendor packages, and receive instant invoices.")
    st.divider()

    tab_book, tab_tickets = st.tabs(["Book Venue & Services", "Public Event Ticket Shop"])

    with tab_book:
        conn = get_db_connection()
        venues = conn.execute("SELECT * FROM venues").fetchall()
        
        if not venues:
            st.warning("No facility profiles listed.")
        else:
            sel_v_name = st.selectbox("1. Select Venue / Facility:", [v['name'] for v in venues])
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
                    💬 WhatsApp POP Line: {sel_venue['whatsapp_no']}</p>
                </div>
            """, unsafe_allow_html=True)

            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (sel_venue['venue_id'],)).fetchall()
            if not spaces:
                st.warning("No sub-spaces listed.")
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

                existing = conn.execute("SELECT * FROM bookings WHERE venue_id = ? AND space_name = ? AND booking_date = ? AND status != 'Cancelled'", 
                                        (sel_venue['venue_id'], sel_sp_name, date_str)).fetchone()

                if existing:
                    st.error(f"❌ Date Reserved: '{sel_sp_name}' is locked on {date_str}.")
                else:
                    st.success(f"✅ Date Available: '{sel_sp_name}' is open on {date_str}.")
                    
                    st.divider()
                    st.markdown("### 3. Approved Service Provider Packages")
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

                    st.divider()
                    st.markdown("### 4. Confirm Reservation")
                    with st.form("confirm_booking_form"):
                        c_name = st.text_input("Full Name / Business Name*")
                        c_email = st.text_input("Delivery Email*")
                        c_phone = st.text_input("WhatsApp / Phone Number*")
                        c_pay = st.selectbox("Payment Option", ["eWallet", "Orange Money", "Pay2Cell", "Direct Bank Deposit"])

                        if st.form_submit_button("Submit Reservation & Issue Invoices", type="primary"):
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
                                st.success(f"Reservation Request #{b_id} Created Successfully!")
                                
                                # Dynamic In-Memory PDF Download Button (Generated on-the-fly in RAM)
                                pdf_bytes = generate_in_memory_pdf_bytes(
                                    f"Venue Tax Invoice — {sel_venue['name']}",
                                    b_id, created_date, sel_venue['name'], sel_venue['tax_id'],
                                    c_name, c_email,
                                    [{"item_name": f"Venue Hire ({sel_sp_name})", "qty": booking_days, "unit_price": sel_space['daily_rate'], "subtotal": space_cost}],
                                    space_cost, sel_venue['bank_details']
                                )
                                st.download_button("📄 Download PDF Invoice (0 KB Disk Space)", pdf_bytes, file_name=f"Invoice_{b_id}.pdf", mime="application/pdf")
                            else:
                                st.error("Please fill in required fields.")
        conn.close()

    with tab_tickets:
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events").fetchall()
        if not events:
            st.info("No upcoming ticketed events available.")
        else:
            for ev in events:
                v = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (ev['venue_id'],)).fetchone()
                col1, col2 = st.columns([1, 2])
                col1.image(ev['flyer_url'] or SPACE_PRESETS[0], use_container_width=True)
                col2.markdown(f"### {ev['title']}")
                col2.write(f"Venue: {ev['venue_name']} | Date: {ev['date']} | Price: BWP {ev['price']:,.2f}")
                
                with col2.form(f"tkt_buy_{ev['event_id']}"):
                    t_qty = st.number_input("Quantity", min_value=1, value=1)
                    t_buyer = st.text_input("Buyer Name*")
                    t_email = st.text_input("Email*")
                    t_pay = st.selectbox("Payment", ["eWallet", "Orange Money", "Pay2Cell", "Direct Deposit"])
                    
                    if st.form_submit_button("Request Ticket Pass"):
                        if t_buyer and t_email:
                            tkt_id = f"TKT-{int(datetime.datetime.now().timestamp())}"
                            sec_hash = f"HASH-{hashlib.sha256(f'{tkt_id}-{t_email}'.encode()).hexdigest()[:10].upper()}"
                            conn.execute("""INSERT INTO tickets
                                (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP / Unverified')""",
                                (tkt_id, sec_hash, ev['event_id'], ev['title'], v['venue_id'] if v else "", ev['venue_name'], v['logo_url'] if v else DEFAULT_LOGO, t_buyer, t_email, t_qty, t_qty*ev['price'], t_pay))
                            conn.commit()
                            
                            st.warning("Ticket Reserved!")
                            qr_img_str = generate_qr_code_base64(sec_hash)
                            st.image(qr_img_str, caption=f"Ticket QR Pass ({sec_hash})", width=160)
                        else:
                            st.error("Provide buyer details.")
        conn.close()

# ---------------------------------------------------------
# 6. MODULE 2: FACILITY OWNER CONSOLE
# ---------------------------------------------------------
elif user_role == "Facility Owner Console":
    st.title("Facility Owner Workspace")
    conn = get_db_connection()

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Facility Owner":
        st.info("🔒 Facility Authentication Required")
        
        login_tab, reg_tab = st.tabs(["Login", "Register Facility"])
        
        with login_tab:
            with st.form("fac_login"):
                l_email = st.text_input("Email")
                l_pw = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND password_hash = ? AND role = 'Facility Owner'",
                                        (l_email, hash_pw(l_pw))).fetchone()
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = l_email
                        st.session_state["user_role"] = "Facility Owner"
                        st.session_state["tenant_id"] = user['tenant_id']
                        st.success("Authenticated!")
                        st.rerun()
                    else:
                        st.error("Invalid Credentials.")

        with reg_tab:
            with st.form("reg_facility_auth"):
                f_name = st.text_input("Facility Name*")
                f_type = st.selectbox("Type", ["Convention Center", "Hotel Ballroom", "Outdoor Arena", "Community Hall"])
                f_email = st.text_input("Email*")
                f_pw = st.text_input("Password*", type="password")
                f_phone = st.text_input("Phone*")
                f_whatsapp = st.text_input("WhatsApp POP Line*", placeholder="26771234567")
                f_address = st.text_input("Address*")
                f_tax = st.text_input("Tax / CIPA ID*")
                f_bank = st.text_area("Bank Details*")
                f_logo = st.file_uploader("Logo", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("Register Facility Profile"):
                    if f_name and f_email and f_pw and f_whatsapp:
                        v_id = f"v_{int(datetime.datetime.now().timestamp())}"
                        logo_url = process_compressed_image_upload(f_logo, DEFAULT_LOGO)
                        
                        conn.execute("""INSERT INTO venues 
                            (venue_id, name, type, email, phone, whatsapp_no, address, max_capacity, tax_id, bank_details, brand_color, logo_url, flyer_image_url, approved_supporter_ids)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1000, ?, ?, '#0F172A', ?, ?, '[]')""",
                            (v_id, f_name, f_type, f_email, f_phone, f_whatsapp, f_address, f_tax, f_bank, logo_url, SPACE_PRESETS[0]))
                        
                        conn.execute("INSERT INTO users (user_id, email, password_hash, role, tenant_id) VALUES (?, ?, ?, 'Facility Owner', ?)",
                                     (f"usr_{int(datetime.datetime.now().timestamp())}", f_email, hash_pw(f_pw), v_id))
                        conn.commit()
                        st.success("Account created! Log in above.")
                    else:
                        st.error("Fill in required fields.")
    else:
        cur_v = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (st.session_state["tenant_id"],)).fetchone()
        if cur_v:
            st.markdown(f"""
                <div class="profile-card" style="background:{cur_v['brand_color']};">
                    <h2>🏛️ {cur_v['name']}</h2>
                    <p>📍 {cur_v['address']} | 💬 WhatsApp POP: {cur_v['whatsapp_no']}</p>
                </div>
            """, unsafe_allow_html=True)

            tab_spaces, tab_vendors, tab_verify, tab_edit = st.tabs(["Sub-Spaces", "Approved Vendors", "Verify POPs", "Edit Profile"])

            with tab_spaces:
                with st.form("add_space_form"):
                    s_name = st.text_input("Sub-Space Name")
                    s_cap = st.number_input("Capacity", value=250)
                    s_rate = st.number_input("Daily Rate (BWP)", value=2500.0)
                    s_img = st.file_uploader("Photo", type=["png", "jpg", "jpeg"])

                    if st.form_submit_button("Add Space"):
                        if s_name:
                            img_url = process_compressed_image_upload(s_img, SPACE_PRESETS[0])
                            conn.execute("INSERT INTO spaces (venue_id, name, capacity, daily_rate, image_url) VALUES (?, ?, ?, ?, ?)",
                                         (cur_v['venue_id'], s_name, s_cap, s_rate, img_url))
                            conn.commit()
                            st.success("Sub-Space Saved!")
                            st.rerun()

                st.divider()
                spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (cur_v['venue_id'],)).fetchall()
                for sp in spaces:
                    col_sp1, col_sp2 = st.columns([4, 1])
                    col_sp1.write(f"• **{sp['name']}** — Cap: {sp['capacity']} | BWP {sp['daily_rate']:,.2f}/day")
                    if col_sp2.button("🗑️ Delete", key=f"del_sp_{sp['space_id']}"):
                        conn.execute("DELETE FROM spaces WHERE space_id = ?", (sp['space_id'],))
                        conn.commit()
                        st.rerun()

            with tab_vendors:
                all_supporters = conn.execute("SELECT * FROM supporters").fetchall()
                cur_approved = set(json.loads(cur_v['approved_supporter_ids'] or "[]"))

                if all_supporters:
                    with st.form("approve_vendors_form"):
                        new_approved = []
                        for sup in all_supporters:
                            chk = st.checkbox(f"**{sup['business_name']}** (`{sup['category']}`)", value=(sup['supporter_id'] in cur_approved))
                            if chk: new_approved.append(sup['supporter_id'])
                        if st.form_submit_button("Save Network"):
                            conn.execute("UPDATE venues SET approved_supporter_ids = ? WHERE venue_id = ?",
                                         (json.dumps(new_approved), cur_v['venue_id']))
                            conn.commit()
                            st.success("Approved Network Updated!")
                            st.rerun()

            with tab_verify:
                pending_bks = conn.execute("SELECT * FROM bookings WHERE venue_id = ? AND status = 'Pending POP / Verification'", (cur_v['venue_id'],)).fetchall()
                if not pending_bks:
                    st.success("No pending POPs.")
                else:
                    for bk in pending_bks:
                        st.write(f"**Booking #{bk['booking_id']}** — Client: {bk['customer_name']} | BWP {bk['venue_cost']:,.2f}")
                        with st.form(f"verify_bk_{bk['booking_id']}"):
                            ref = st.text_input("Enter WhatsApp Ref")
                            if st.form_submit_button("✅ Verify"):
                                if ref:
                                    conn.execute("UPDATE bookings SET status = 'Confirmed / Paid', pop_reference = ? WHERE booking_id = ?", (ref, bk['booking_id']))
                                    conn.commit()
                                    st.success("Booking Verified!")
                                    st.rerun()

            with tab_edit:
                with st.form("edit_facility_profile"):
                    u_name = st.text_input("Facility Name", value=cur_v['name'])
                    u_phone = st.text_input("Phone", value=cur_v['phone'])
                    u_wa = st.text_input("WhatsApp Line", value=cur_v['whatsapp_no'])
                    u_bank = st.text_area("Bank Details", value=cur_v['bank_details'])
                    u_color = st.color_picker("Brand Color", value=cur_v['brand_color'])
                    u_logo = st.file_uploader("Update Logo", type=["png", "jpg", "jpeg"])

                    if st.form_submit_button("Save Profile"):
                        logo_url = process_compressed_image_upload(u_logo, cur_v['logo_url'])
                        conn.execute("""UPDATE venues SET name = ?, phone = ?, whatsapp_no = ?, bank_details = ?, brand_color = ?, logo_url = ?
                            WHERE venue_id = ?""", (u_name, u_phone, u_wa, u_bank, u_color, logo_url, cur_v['venue_id']))
                        conn.commit()
                        st.success("Profile Saved!")
                        st.rerun()

    conn.close()

# ---------------------------------------------------------
# 7. MODULE 3: FACILITY SUPPORTER CONSOLE
# ---------------------------------------------------------
elif user_role == "Facility Supporter Console":
    st.title("Facility Supporter Console (Vendors)")
    conn = get_db_connection()

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Facility Supporter":
        st.info("🔒 Vendor Authentication Required")
        
        login_tab, reg_tab = st.tabs(["Login", "Register Vendor"])
        
        with login_tab:
            with st.form("sup_login"):
                l_email = st.text_input("Email")
                l_pw = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND password_hash = ? AND role = 'Facility Supporter'",
                                        (l_email, hash_pw(l_pw))).fetchone()
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = l_email
                        st.session_state["user_role"] = "Facility Supporter"
                        st.session_state["tenant_id"] = user['tenant_id']
                        st.success("Authenticated!")
                        st.rerun()
                    else:
                        st.error("Invalid Credentials.")

        with reg_tab:
            with st.form("reg_supporter_auth"):
                s_name = st.text_input("Business Name*")
                s_cat = st.selectbox("Category", ["Catering & Cutlery", "Stage & Decor", "Sound & AV", "Florist", "Security"])
                s_person = st.text_input("Contact Person*")
                s_email = st.text_input("Email*")
                s_pw = st.text_input("Password*", type="password")
                s_phone = st.text_input("WhatsApp Line*", placeholder="26771234567")
                s_bank = st.text_area("Bank Details*")
                s_color = st.color_picker("Brand Color", "#1E293B")
                s_logo = st.file_uploader("Logo", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("Register Vendor Account"):
                    if s_name and s_email and s_pw and s_phone:
                        sup_id = f"sup_{int(datetime.datetime.now().timestamp())}"
                        logo_url = process_compressed_image_upload(s_logo, DEFAULT_LOGO)
                        
                        conn.execute("""INSERT INTO supporters 
                            (supporter_id, business_name, category, contact_person, email, phone, bank_details, brand_color, logo_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (sup_id, s_name, s_cat, s_person, s_email, s_phone, s_bank, s_color, logo_url))
                        
                        conn.execute("INSERT INTO users (user_id, email, password_hash, role, tenant_id) VALUES (?, ?, ?, 'Facility Supporter', ?)",
                                     (f"usr_{int(datetime.datetime.now().timestamp())}", s_email, hash_pw(s_pw), sup_id))
                        conn.commit()
                        st.success("Profile Created! Log in above.")
                    else:
                        st.error("Fill in required fields.")
    else:
        cur_sup = conn.execute("SELECT * FROM supporters WHERE supporter_id = ?", (st.session_state["tenant_id"],)).fetchone()
        if cur_sup:
            st.markdown(f"""
                <div class="profile-card" style="background:{cur_sup['brand_color']};">
                    <h2>🚚 {cur_sup['business_name']}</h2>
                    <p>Category: {cur_sup['category']} | WhatsApp POP: {cur_sup['phone']}</p>
                </div>
            """, unsafe_allow_html=True)

            vtab1, vtab2, vtab3 = st.tabs(["Service Catalog", "Verify Invoices", "Edit Profile"])

            with vtab1:
                with st.form("add_pkg_form"):
                    i_name = st.text_input("Package Item Name*")
                    i_desc = st.text_area("Specifications")
                    i_type = st.selectbox("Unit Metric", ["Per Guest", "Per Day", "Flat Rate", "Per Hour"])
                    i_price = st.number_input("Rate (BWP)", min_value=1.0, value=150.0)
                    i_photo = st.file_uploader("Item Image", type=["png", "jpg", "jpeg"])

                    if st.form_submit_button("Add Offering Item"):
                        if i_name:
                            img_url = process_compressed_image_upload(i_photo, SPACE_PRESETS[0])
                            conn.execute("""INSERT INTO vendor_templates 
                                (supporter_id, item_name, description, unit_type, unit_price, image_url)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                                (cur_sup['supporter_id'], i_name, i_desc, i_type, i_price, img_url))
                            conn.commit()
                            st.success("Offering Added!")
                            st.rerun()

                st.divider()
                templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ?", (cur_sup['supporter_id'],)).fetchall()
                for t in templates:
                    col_t1, col_t2 = st.columns([4, 1])
                    col_t1.write(f"• **{t['item_name']}** — BWP {t['unit_price']:,.2f} / {t['unit_type']}")
                    if col_t2.button("🗑️ Delete", key=f"del_item_{t['template_id']}"):
                        conn.execute("DELETE FROM vendor_templates WHERE template_id = ?", (t['template_id'],))
                        conn.commit()
                        st.rerun()

            with vtab2:
                v_invs = conn.execute("SELECT * FROM vendor_invoices WHERE supporter_id = ? AND status = 'Pending POP'", (cur_sup['supporter_id'],)).fetchall()
                if not v_invs:
                    st.success("No pending invoices.")
                else:
                    for inv in v_invs:
                        st.write(f"**Invoice #{inv['vendor_invoice_id']}** — Client: {inv['customer_name']} | BWP {inv['total_amount']:,.2f}")
                        with st.form(f"verify_vinv_{inv['vendor_invoice_id']}"):
                            ref = st.text_input("Enter WhatsApp Ref")
                            if st.form_submit_button("✅ Verify POP"):
                                if ref:
                                    conn.execute("UPDATE vendor_invoices SET status = 'PAID & VERIFIED', pop_reference = ? WHERE vendor_invoice_id = ?", (ref, inv['vendor_invoice_id']))
                                    conn.commit()
                                    st.success("Invoice Paid!")
                                    st.rerun()

            with vtab3:
                with st.form("edit_vendor_profile"):
                    u_phone = st.text_input("WhatsApp Line", value=cur_sup['phone'])
                    u_bank = st.text_area("Bank Details", value=cur_sup['bank_details'])
                    u_color = st.color_picker("Brand Color", value=cur_sup['brand_color'])
                    u_logo = st.file_uploader("Update Logo", type=["png", "jpg", "jpeg"])

                    if st.form_submit_button("Save Setup"):
                        logo_url = process_compressed_image_upload(u_logo, cur_sup['logo_url'])
                        conn.execute("""UPDATE supporters SET phone = ?, bank_details = ?, brand_color = ?, logo_url = ?
                            WHERE supporter_id = ?""", (u_phone, u_bank, u_color, logo_url, cur_sup['supporter_id']))
                        conn.commit()
                        st.success("Profile Updated!")
                        st.rerun()

    conn.close()

# ---------------------------------------------------------
# 8. MODULE 4: GATE ACCESS & CAMERA QR SCANNER
# ---------------------------------------------------------
elif user_role == "Gate Access & Mobile Scanner":
    st.title("Door Gate Access & Mobile QR Scanner")
    st.caption("Point camera at guest QR passes or type verification hashes.")
    st.divider()

    conn = get_db_connection()
    camera_file = st.camera_input("Point camera at guest QR pass")
    scan_input = st.text_input("Or Enter Verification Hash manually:")

    if st.button("Validate Admission Pass", type="primary"):
        target_str = scan_input.strip().upper()
        if target_str:
            tkt = conn.execute("SELECT * FROM tickets WHERE verification_hash = ? OR ticket_id = ?", (target_str, target_str)).fetchone()
            if tkt:
                if tkt['status'] == 'VALID':
                    conn.execute("UPDATE tickets SET status = 'USED / SCANNED', scanned_at = ? WHERE ticket_id = ?", (str(datetime.datetime.now()), tkt['ticket_id']))
                    conn.commit()
                    st.success(f"✅ ACCESS GRANTED: {tkt['buyer']} ({tkt['qty']} Person/s) — Event: {tkt['event_title']}")
                elif 'Pending' in tkt['status']:
                    st.warning("⚠️ UNVERIFIED TICKET: Payment POP has not been confirmed.")
                else:
                    st.error("❌ INVALID: Pass already redeemed.")
            else:
                st.error("❌ Invalid Ticket Pass.")
    conn.close()

# ---------------------------------------------------------
# 9. MODULE 5: MASTER PLATFORM CONTROL
# ---------------------------------------------------------
elif user_role == "Master Platform Control":
    st.title("Master Enterprise Platform Control")
    st.caption("Executive overview and data audit tables.")
    st.divider()

    conn = get_db_connection()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Venues", conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0])
    m2.metric("Vendors", conn.execute("SELECT COUNT(*) FROM supporters").fetchone()[0])
    m3.metric("Bookings", conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0])
    m4.metric("Vendor Invoices", conn.execute("SELECT COUNT(*) FROM vendor_invoices").fetchone()[0])
    m5.metric("Tickets", conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0])

    st.divider()
    adm1, adm2, adm3 = st.tabs(["Facilities Ledger", "Supporters Ledger", "Bookings Ledger"])

    with adm1:
        venues = conn.execute("SELECT venue_id, name, type, email, phone, whatsapp_no FROM venues").fetchall()
        if venues: st.dataframe([dict(v) for v in venues], use_container_width=True)

    with adm2:
        sups = conn.execute("SELECT supporter_id, business_name, category, contact_person, email, phone FROM supporters").fetchall()
        if sups: st.dataframe([dict(s) for s in sups], use_container_width=True)

    with adm3:
        bks = conn.execute("SELECT booking_id, venue_id, space_name, customer_name, booking_date, venue_cost, status FROM bookings").fetchall()
        if bks: st.dataframe([dict(b) for b in bks], use_container_width=True)

    conn.close()
