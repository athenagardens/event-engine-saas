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
# 1. DATABASE ENGINE (SQLITE CLOUD-READY)
# ---------------------------------------------------------
DB_FILE = "enterprise_platform.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Auth Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, role TEXT, tenant_id TEXT
    )''')

    # Venues / Facilities
    c.execute('''CREATE TABLE IF NOT EXISTS venues (
        venue_id TEXT PRIMARY KEY, name TEXT, type TEXT, email TEXT, phone TEXT, whatsapp_no TEXT,
        address TEXT, max_capacity INTEGER, tax_id TEXT, bank_details TEXT, brand_color TEXT,
        logo_url TEXT, flyer_image_url TEXT, approved_supporter_ids TEXT
    )''')
    
    # Venue Sub-Spaces
    c.execute('''CREATE TABLE IF NOT EXISTS spaces (
        space_id INTEGER PRIMARY KEY AUTOINCREMENT, venue_id TEXT, name TEXT, capacity INTEGER, 
        daily_rate REAL, image_url TEXT, is_active INTEGER DEFAULT 1
    )''')
    
    # Supporters / Vendors
    c.execute('''CREATE TABLE IF NOT EXISTS supporters (
        supporter_id TEXT PRIMARY KEY, business_name TEXT, category TEXT, contact_person TEXT,
        email TEXT, phone TEXT, bank_details TEXT, brand_color TEXT, logo_url TEXT
    )''')
    
    # Vendor Service Templates
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT, supporter_id TEXT, item_name TEXT, description TEXT,
        unit_type TEXT, unit_price REAL, image_url TEXT, is_active INTEGER DEFAULT 1
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
    
    # Event Admission Passes
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY, verification_hash TEXT, event_id TEXT, event_title TEXT, venue_id TEXT,
        venue_name TEXT, venue_logo TEXT, buyer TEXT, email TEXT, qty INTEGER, total_paid REAL,
        payment_method TEXT, status TEXT, pop_reference TEXT, scanned_at TEXT
    )''')
    
    # Public Events
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY, venue_id TEXT, venue_name TEXT, space_name TEXT, title TEXT, date TEXT,
        price REAL, description TEXT, flyer_url TEXT, is_active INTEGER DEFAULT 1
    )''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------
# 2. UTILITIES: IMAGES, PDF, & QR GENERATION
# ---------------------------------------------------------
DEFAULT_LOGO = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150"
SPACE_PRESETS = ["https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=400"]

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def process_compressed_image_upload(uploaded_file, fallback_url, max_dim=600):
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
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), alignment=1)
    story.append(Paragraph(f"{title_text.upper()}", title_style))
    story.append(Spacer(1, 10))

    meta_data = [
        [f"Document Ref: {inv_id}", f"Date: {created_at}"],
        [f"Entity / Issuer: {entity_name}", f"Tax ID / Corporate CIPA: {tax_id}"],
        [f"Client / Billed To: {client_name}", f"Contact Email: {client_email}"]
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

    table_data = [["Line Item Description", "Qty / Duration", "Unit Price (BWP)", "Line Total (BWP)"]]
    for item in items_list:
        table_data.append([
            item.get('item_name', 'Service Description'),
            str(item.get('qty', 1)),
            f"{item.get('unit_price', 0):,.2f}",
            f"{item.get('subtotal', 0):,.2f}"
        ])
    table_data.append(["TOTAL AMOUNT DUE", "", "", f"BWP {total_amount:,.2f}"])

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

    story.append(Paragraph(f"<b>Settlement Terms & Bank Account Details:</b><br/>{bank_details}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------------
# 3. CLASSICAL EXECUTIVE CSS STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="Executive Enterprise Venue & Event Operating Platform", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid #1E293B;
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }

        .exec-title {
            font-family: 'Playfair Display', Georgia, serif;
            color: #0F172A;
            text-align: center;
            font-weight: 700;
            font-size: 2.2rem;
            letter-spacing: -0.02em;
            margin-bottom: 0.2rem;
        }
        .exec-subtitle {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #475569;
            text-align: center;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 1rem;
        }

        .gold-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #D97706, transparent);
            margin: 0.5rem auto 1.5rem auto;
            width: 50%;
        }

        .exec-card {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 4px;
            border: 1px solid #E2E8F0;
            border-top: 3px solid #0F172A;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.25rem;
        }

        .form-label {
            font-weight: 700;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #1E293B;
            margin-bottom: 0.25rem;
        }

        .stButton > button {
            background-color: #0F172A !important;
            color: #FFFFFF !important;
            border-radius: 4px !important;
            border: 1px solid #0F172A !important;
            font-weight: 600 !important;
            letter-spacing: 0.05em !important;
            padding: 0.5rem 1rem !important;
        }
        .stButton > button:hover {
            background-color: #D97706 !important;
            border-color: #D97706 !important;
            color: #FFFFFF !important;
        }

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
st.sidebar.markdown("<h2 style='text-align: center; font-family: Playfair Display, serif;'>🏛️ EXECUTIVE PORTAL</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 0.75rem; letter-spacing: 0.1em; color: #64748B;'><b>ENTERPRISE SAAS INFRASTRUCTURE</b></p>", unsafe_allow_html=True)
st.sidebar.divider()

user_role = st.sidebar.radio(
    "MANAGEMENT CONSOLE:",
    [
        "Enterprise Marketplace & Event Hub",
        "Venue Operations & Asset Management",
        "Vendor Portal & Service Fulfillment",
        "Access Control & Verification Suite",
        "Executive Master Ledger & Audit Suite"
    ],
    key="nav_sidebar_radio"
)

if user_role in ["Enterprise Marketplace & Event Hub", "Access Control & Verification Suite"]:
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None
    st.session_state["tenant_id"] = None

st.sidebar.divider()
if st.session_state["authenticated"]:
    st.sidebar.success(f"AUTHENTICATED: **{st.session_state['user_email']}**")
    if st.sidebar.button("LOG OUT WORKSPACE", use_container_width=True, key="btn_logout"):
        st.session_state["authenticated"] = False
        st.session_state["user_email"] = None
        st.session_state["user_role"] = None
        st.session_state["tenant_id"] = None
        st.rerun()

with st.sidebar.expander("SYSTEM MAINTENANCE"):
    if st.button("RESET DATABASE STATE", type="primary", use_container_width=True, key="btn_reset_db"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            init_db()
            st.session_state.clear()
            st.success("Database state re-initialized.")
            st.rerun()

# ---------------------------------------------------------
# 5. MODULE 1: ENTERPRISE MARKETPLACE & EVENT HUB
# ---------------------------------------------------------
if user_role == "Enterprise Marketplace & Event Hub":
    st.markdown("<div class='exec-title'>Enterprise Marketplace & Event Hub</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Commercial Venue Reservations & Public Event Ticketing</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    tab_book, tab_tickets = st.tabs(["🏛️ Commercial Venue Reservations", "🎟️ Box Office Event Tickets"])

    with tab_book:
        conn = get_db_connection()
        venues = conn.execute("SELECT * FROM venues").fetchall()
        
        if not venues:
            st.warning("No registered commercial properties published on network.")
        else:
            st.markdown("<div class='form-label'>1. Select Destination Venue Facility</div>", unsafe_allow_html=True)
            sel_v_name = st.selectbox("", [v['name'] for v in venues], label_visibility="collapsed", key="mkt_select_venue")
            sel_venue = next(v for v in venues if v['name'] == sel_v_name)

            col1, col2 = st.columns([1, 2])
            col1.image(sel_venue['flyer_image_url'] or SPACE_PRESETS[0], use_container_width=True)
            col2.markdown(f"""
                <div class="exec-card" style="border-top-color:{sel_venue['brand_color']}; margin-bottom:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2 style="margin:0; font-family:'Playfair Display', serif;">{sel_venue['name']}</h2>
                        <img src="{sel_venue['logo_url'] or DEFAULT_LOGO}" class="logo-img" style="background:white; padding:4px; border:1px solid #E2E8F0; border-radius:4px;">
                    </div>
                    <hr style="margin:1rem 0; border:0; border-top:1px solid #E2E8F0;">
                    <p style="margin:0; font-size:0.9rem;">
                        <b>LOCATION:</b> {sel_venue['address']}<br>
                        <b>LICENSED CAPACITY:</b> {sel_venue['max_capacity']:,} Guests<br>
                        <b>WHATSAPP VERIFICATION LINE:</b> {sel_venue['whatsapp_no']}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ? AND is_active = 1", (sel_venue['venue_id'],)).fetchall()
            if not spaces:
                st.warning("No available sub-spaces listed for this facility.")
            else:
                st.divider()
                st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>2. Space Selection & Event Scheduling</h3>", unsafe_allow_html=True)
                
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.markdown("<div class='form-label'>Select Sub-Space Asset</div>", unsafe_allow_html=True)
                    sel_sp_name = st.selectbox("", [s['name'] for s in spaces], label_visibility="collapsed", key="mkt_select_space")
                    sel_space = next(s for s in spaces if s['name'] == sel_sp_name)
                with sc2:
                    st.markdown("<div class='form-label'>Event Date</div>", unsafe_allow_html=True)
                    booking_date = st.date_input("", min_value=datetime.date.today(), label_visibility="collapsed", key="mkt_booking_date")
                with sc3:
                    st.markdown("<div class='form-label'>Reservation Duration (Days)</div>", unsafe_allow_html=True)
                    booking_days = st.number_input("", min_value=1, value=1, label_visibility="collapsed", key="mkt_booking_days")

                date_str = str(booking_date)
                space_cost = sel_space['daily_rate'] * booking_days

                existing = conn.execute("SELECT * FROM bookings WHERE venue_id = ? AND space_name = ? AND booking_date = ? AND status != 'Cancelled'", 
                                        (sel_venue['venue_id'], sel_sp_name, date_str)).fetchone()

                if existing:
                    st.error(f"❌ Date Locked: '{sel_sp_name}' is currently reserved on {date_str}.")
                else:
                    st.success(f"✅ Schedule Confirmed: '{sel_sp_name}' is available on {date_str}.")
                    
                    st.divider()
                    st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>3. Ancillary Vendor Service Bundles</h3>", unsafe_allow_html=True)
                    approved_ids = json.loads(sel_venue['approved_supporter_ids'] or "[]")
                    selected_vendor_orders = {}

                    if approved_ids:
                        placeholders = ','.join('?' * len(approved_ids))
                        supporters = conn.execute(f"SELECT * FROM supporters WHERE supporter_id IN ({placeholders})", approved_ids).fetchall()
                        
                        for sup in supporters:
                            templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ? AND is_active = 1", (sup['supporter_id'],)).fetchall()
                            if templates:
                                with st.expander(f"Add Service Package: {sup['business_name']} ({sup['category']})"):
                                    sup_items = []
                                    sup_total = 0.0
                                    for t in templates:
                                        tc1, tc2 = st.columns([1, 3])
                                        if t['image_url']: tc1.image(t['image_url'], use_container_width=True)
                                        tc2.markdown(f"**{t['item_name'].upper()}**")
                                        tc2.write(f"Tariff: BWP {t['unit_price']:,.2f} per {t['unit_type']}")
                                        if t['description']: tc2.caption(t['description'])
                                        
                                        qty = tc2.number_input(f"Qty ({t['item_name']})", min_value=0, value=0, key=f"mkt_qty_{sup['supporter_id']}_{t['template_id']}")
                                        if qty > 0:
                                            cost = qty * t['unit_price']
                                            sup_total += cost
                                            sup_items.append({"item_name": t['item_name'], "qty": qty, "unit_price": t['unit_price'], "subtotal": cost})
                                    if sup_items:
                                        selected_vendor_orders[sup['supporter_id']] = {"info": sup, "items": sup_items, "total": sup_total}

                    st.divider()
                    st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>4. Settlement & Billing Confirmation</h3>", unsafe_allow_html=True)
                    
                    with st.form("confirm_booking_form"):
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            st.markdown("<div class='form-label'>Client Entity / Full Name*</div>", unsafe_allow_html=True)
                            c_name = st.text_input("", label_visibility="collapsed", key="mkt_c_name")
                            st.markdown("<div class='form-label'>Billing Email Address*</div>", unsafe_allow_html=True)
                            c_email = st.text_input("", label_visibility="collapsed", key="mkt_c_email")
                        with bc2:
                            st.markdown("<div class='form-label'>Contact Phone / WhatsApp Line*</div>", unsafe_allow_html=True)
                            c_phone = st.text_input("", label_visibility="collapsed", key="mkt_c_phone")
                            st.markdown("<div class='form-label'>Preferred Settlement Method</div>", unsafe_allow_html=True)
                            c_pay = st.selectbox("", ["Direct Bank Wire Transfer", "eWallet", "Orange Money", "Pay2Cell"], label_visibility="collapsed", key="mkt_c_pay")

                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.form_submit_button("SUBMIT RESERVATION & GENERATE INVOICES", type="primary", use_container_width=True):
                            if c_name and c_email and c_phone:
                                b_id = f"BK-{int(datetime.datetime.now().timestamp())}"
                                created_date = str(datetime.date.today())
                                
                                conn.execute("""INSERT INTO bookings 
                                    (booking_id, venue_id, space_name, customer_name, customer_email, customer_phone, booking_date, days, venue_cost, payment_method, status, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP / Verification', ?)""",
                                    (b_id, sel_venue['venue_id'], sel_sp_name, c_name, c_email, c_phone, date_str, booking_days, space_cost, c_pay, created_date))

                                vendor_pdf_dict = {}
                                for s_id, v_data in selected_vendor_orders.items():
                                    v_inv_id = f"VINV-{int(datetime.datetime.now().timestamp())}"
                                    conn.execute("""INSERT INTO vendor_invoices
                                        (vendor_invoice_id, parent_booking_id, supporter_id, venue_name, customer_name, customer_email, customer_phone, event_date, items_json, total_amount, payment_method, status, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP', ?)""",
                                        (v_inv_id, b_id, s_id, sel_venue['name'], c_name, c_email, c_phone, date_str, json.dumps(v_data['items']), v_data['total'], c_pay, created_date))

                                    v_info = v_data['info']
                                    v_pdf = generate_in_memory_pdf_bytes(
                                        f"Vendor Invoice — {v_info['business_name']}",
                                        v_inv_id, created_date, v_info['business_name'], "TAX-PENDING",
                                        c_name, c_email, v_data['items'], v_data['total'], v_info['bank_details']
                                    )
                                    vendor_pdf_dict[v_info['business_name']] = (v_inv_id, v_pdf)

                                conn.commit()
                                st.success(f"Reservation Request #{b_id} Generated Successfully!")
                                
                                venue_pdf_bytes = generate_in_memory_pdf_bytes(
                                    f"Official Tax Invoice — {sel_venue['name']}",
                                    b_id, created_date, sel_venue['name'], sel_venue['tax_id'],
                                    c_name, c_email,
                                    [{"item_name": f"Venue Hire ({sel_sp_name})", "qty": booking_days, "unit_price": sel_space['daily_rate'], "subtotal": space_cost}],
                                    space_cost, sel_venue['bank_details']
                                )
                                st.download_button("📄 DOWNLOAD VENUE HIRE PDF INVOICE", venue_pdf_bytes, file_name=f"Venue_Invoice_{b_id}.pdf", mime="application/pdf", key=f"dl_venue_{b_id}")

                                for v_biz, (v_inv_id, v_pdf_data) in vendor_pdf_dict.items():
                                    st.download_button(f"📄 DOWNLOAD VENDOR PDF INVOICE ({v_biz.upper()})", v_pdf_data, file_name=f"Vendor_Invoice_{v_inv_id}.pdf", mime="application/pdf", key=f"dl_vendor_{v_inv_id}")
                            else:
                                st.error("Please complete all required billing contact fields.")
        conn.close()

    with tab_tickets:
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events WHERE is_active = 1").fetchall()
        if not events:
            st.info("No public ticketed events listed.")
        else:
            for ev in events:
                v = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (ev['venue_id'],)).fetchone()
                col1, col2 = st.columns([1, 2])
                col1.image(ev['flyer_url'] or SPACE_PRESETS[0], use_container_width=True)
                col2.markdown(f"<h3 style='font-family: Playfair Display, serif; margin:0;'>{ev['title']}</h3>", unsafe_allow_html=True)
                col2.write(f"**VENUE:** {ev['venue_name']} | **DATE:** {ev['date']} | **ADMISSION TARIFF:** BWP {ev['price']:,.2f}")
                
                with col2.form(f"tkt_buy_{ev['event_id']}"):
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        st.markdown("<div class='form-label'>Pass Quantity</div>", unsafe_allow_html=True)
                        t_qty = st.number_input("", min_value=1, value=1, label_visibility="collapsed", key=f"tkt_qty_{ev['event_id']}")
                        st.markdown("<div class='form-label'>Attendee Name*</div>", unsafe_allow_html=True)
                        t_buyer = st.text_input("", label_visibility="collapsed", key=f"tkt_buyer_{ev['event_id']}")
                    with tc2:
                        st.markdown("<div class='form-label'>Email Address*</div>", unsafe_allow_html=True)
                        t_email = st.text_input("", label_visibility="collapsed", key=f"tkt_email_{ev['event_id']}")
                        st.markdown("<div class='form-label'>Settlement Method</div>", unsafe_allow_html=True)
                        t_pay = st.selectbox("", ["Direct Bank Wire Transfer", "eWallet", "Orange Money", "Pay2Cell"], label_visibility="collapsed", key=f"tkt_pay_{ev['event_id']}")
                    
                    if st.form_submit_button("ISSUE DIGITAL TICKET PASS"):
                        if t_buyer and t_email:
                            tkt_id = f"TKT-{int(datetime.datetime.now().timestamp())}"
                            sec_hash = f"HASH-{hashlib.sha256(f'{tkt_id}-{t_email}'.encode()).hexdigest()[:10].upper()}"
                            conn.execute("""INSERT INTO tickets
                                (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending POP / Unverified')""",
                                (tkt_id, sec_hash, ev['event_id'], ev['title'], v['venue_id'] if v else "", ev['venue_name'], v['logo_url'] if v else DEFAULT_LOGO, t_buyer, t_email, t_qty, t_qty*ev['price'], t_pay))
                            conn.commit()
                            
                            st.warning("Digital Pass Issued! Awaiting Settlement Proof of Payment (POP).")
                            qr_img_str = generate_qr_code_base64(sec_hash)
                            st.image(qr_img_str, caption=f"Unverified QR Access Pass ({sec_hash})", width=160)
                        else:
                            st.error("Please enter required attendee details.")
        conn.close()

# ---------------------------------------------------------
# 6. MODULE 2: VENUE OPERATIONS & ASSET MANAGEMENT
# ---------------------------------------------------------
elif user_role == "Venue Operations & Asset Management":
    st.markdown("<div class='exec-title'>Venue Operations & Asset Management Console</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Corporate Facility & Sub-Space Infrastructure</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    conn = get_db_connection()

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Facility Owner":
        st.info("🔒 Facility Operator Authentication Required")
        
        login_tab, reg_tab = st.tabs(["Operator Workspace Login", "Register New Commercial Property"])
        
        with login_tab:
            with st.form("fac_login_form"):
                st.markdown("<div class='form-label'>Operator Email Address</div>", unsafe_allow_html=True)
                l_email = st.text_input("", label_visibility="collapsed", key="fac_login_email")
                st.markdown("<div class='form-label'>Account Password</div>", unsafe_allow_html=True)
                l_pw = st.text_input("", type="password", label_visibility="collapsed", key="fac_login_pw")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("AUTHENTICATE WORKSPACE", type="primary", use_container_width=True):
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND password_hash = ? AND role = 'Facility Owner'",
                                        (l_email, hash_pw(l_pw))).fetchone()
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = l_email
                        st.session_state["user_role"] = "Facility Owner"
                        st.session_state["tenant_id"] = user['tenant_id']
                        st.success("Authentication successful!")
                        st.rerun()
                    else:
                        st.error("Invalid operator credentials.")

        with reg_tab:
            with st.form("reg_facility_auth_form"):
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown("<div class='form-label'>Venue Facility Name*</div>", unsafe_allow_html=True)
                    f_name = st.text_input("", label_visibility="collapsed", key="reg_fac_name")
                    st.markdown("<div class='form-label'>Facility Designation</div>", unsafe_allow_html=True)
                    f_type = st.selectbox("", ["Convention Center", "Hotel Ballroom", "Outdoor Arena", "Community Hall"], label_visibility="collapsed", key="reg_fac_type")
                    st.markdown("<div class='form-label'>Corporate Email*</div>", unsafe_allow_html=True)
                    f_email = st.text_input("", label_visibility="collapsed", key="reg_fac_email")
                    st.markdown("<div class='form-label'>Account Password*</div>", unsafe_allow_html=True)
                    f_pw = st.text_input("", type="password", label_visibility="collapsed", key="reg_fac_pw")
                    st.markdown("<div class='form-label'>Direct Telephone Line*</div>", unsafe_allow_html=True)
                    f_phone = st.text_input("", label_visibility="collapsed", key="reg_fac_phone")
                with rc2:
                    st.markdown("<div class='form-label'>WhatsApp Audit Verification Line*</div>", unsafe_allow_html=True)
                    f_whatsapp = st.text_input("", placeholder="26771234567", label_visibility="collapsed", key="reg_fac_wa")
                    st.markdown("<div class='form-label'>Physical Location / Street Address*</div>", unsafe_allow_html=True)
                    f_address = st.text_input("", label_visibility="collapsed", key="reg_fac_addr")
                    st.markdown("<div class='form-label'>Tax / CIPA Registration Number*</div>", unsafe_allow_html=True)
                    f_tax = st.text_input("", label_visibility="collapsed", key="reg_fac_tax")
                    st.markdown("<div class='form-label'>Corporate Settlement Instructions*</div>", unsafe_allow_html=True)
                    f_bank = st.text_area("", label_visibility="collapsed", height=68, key="reg_fac_bank")
                    st.markdown("<div class='form-label'>Brand Logo</div>", unsafe_allow_html=True)
                    f_logo = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="reg_fac_logo")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("REGISTER VENUE PROPERTY", type="primary", use_container_width=True):
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
                        st.success("Venue Account Registered! Please log in above.")
                    else:
                        st.error("Please fill in required fields.")
    else:
        cur_v = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (st.session_state["tenant_id"],)).fetchone()
        if cur_v:
            st.markdown(f"""
                <div class="exec-card" style="border-top-color:{cur_v['brand_color']}; text-align:center;">
                    <h2 style="margin:0; font-family:'Playfair Display', serif;">🏛️ {cur_v['name']}</h2>
                    <p style="margin:0.25rem 0 0 0; font-size:0.9rem;">LOCATION: {cur_v['address']} | AUDIT WHATSAPP: {cur_v['whatsapp_no']}</p>
                </div>
            """, unsafe_allow_html=True)

            tab_spaces, tab_vendors, tab_verify_bks, tab_verify_tkts, tab_edit = st.tabs([
                "Sub-Spaces Inventory", "Approved Vendor Network", "Verify Booking POPs", "🎟️ Verify Ticket Passes", "Corporate Profile"
            ])

            with tab_spaces:
                with st.form("add_space_form"):
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        st.markdown("<div class='form-label'>Sub-Space / Hall Identifier</div>", unsafe_allow_html=True)
                        s_name = st.text_input("", label_visibility="collapsed", key="add_sp_name")
                    with sc2:
                        st.markdown("<div class='form-label'>Capacity Rating</div>", unsafe_allow_html=True)
                        s_cap = st.number_input("", value=250, label_visibility="collapsed", key="add_sp_cap")
                    with sc3:
                        st.markdown("<div class='form-label'>Standard Daily Tariff (BWP)</div>", unsafe_allow_html=True)
                        s_rate = st.number_input("", value=2500.0, label_visibility="collapsed", key="add_sp_rate")

                    st.markdown("<div class='form-label'>Asset Media Graphic</div>", unsafe_allow_html=True)
                    s_img = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="add_sp_img")

                    if st.form_submit_button("ADD SUB-SPACE ASSET"):
                        if s_name:
                            img_url = process_compressed_image_upload(s_img, SPACE_PRESETS[0])
                            conn.execute("INSERT INTO spaces (venue_id, name, capacity, daily_rate, image_url, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                                         (cur_v['venue_id'], s_name, s_cap, s_rate, img_url))
                            conn.commit()
                            st.success("Sub-Space Asset Added!")
                            st.rerun()

                st.divider()
                spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ? AND is_active = 1", (cur_v['venue_id'],)).fetchall()
                for sp in spaces:
                    col_sp1, col_sp2 = st.columns([4, 1])
                    col_sp1.write(f"• **{sp['name'].upper()}** — Capacity: {sp['capacity']} Guests | Daily Tariff: BWP {sp['daily_rate']:,.2f}")
                    if col_sp2.button("DEACTIVATE ASSET", key=f"del_sp_{sp['space_id']}"):
                        conn.execute("UPDATE spaces SET is_active = 0 WHERE space_id = ?", (sp['space_id'],))
                        conn.commit()
                        st.rerun()

            with tab_vendors:
                all_supporters = conn.execute("SELECT * FROM supporters").fetchall()
                cur_approved = set(json.loads(cur_v['approved_supporter_ids'] or "[]"))

                if all_supporters:
                    with st.form("approve_vendors_form"):
                        new_approved = []
                        for sup in all_supporters:
                            chk = st.checkbox(f"**{sup['business_name'].upper()}** (`{sup['category']}`)", value=(sup['supporter_id'] in cur_approved), key=f"chk_sup_{sup['supporter_id']}")
                            if chk: new_approved.append(sup['supporter_id'])
                        if st.form_submit_button("SAVE APPROVED SUPPLIER NETWORK"):
                            conn.execute("UPDATE venues SET approved_supporter_ids = ? WHERE venue_id = ?",
                                         (json.dumps(new_approved), cur_v['venue_id']))
                            conn.commit()
                            st.success("Approved Vendor Network Updated!")
                            st.rerun()

            with tab_verify_bks:
                pending_bks = conn.execute("SELECT * FROM bookings WHERE venue_id = ? AND status = 'Pending POP / Verification'", (cur_v['venue_id'],)).fetchall()
                if not pending_bks:
                    st.success("No pending booking settlements.")
                else:
                    for bk in pending_bks:
                        st.write(f"**BOOKING REF #{bk['booking_id']}** — Client: {bk['customer_name']} | Total Tariff: BWP {bk['venue_cost']:,.2f}")
                        with st.form(f"verify_bk_form_{bk['booking_id']}"):
                            st.markdown("<div class='form-label'>WhatsApp Transaction Audit Reference</div>", unsafe_allow_html=True)
                            ref = st.text_input("", label_visibility="collapsed", key=f"bk_ref_{bk['booking_id']}")
                            if st.form_submit_button("CONFIRM & VERIFY SETTLEMENT"):
                                if ref:
                                    conn.execute("UPDATE bookings SET status = 'Confirmed / Paid', pop_reference = ? WHERE booking_id = ?", (ref, bk['booking_id']))
                                    conn.commit()
                                    st.success("Booking Verified!")
                                    st.rerun()

            with tab_verify_tkts:
                pending_tkts = conn.execute("SELECT * FROM tickets WHERE venue_id = ? AND status LIKE 'Pending%'", (cur_v['venue_id'],)).fetchall()
                if not pending_tkts:
                    st.success("No pending ticket pass submissions.")
                else:
                    for tkt in pending_tkts:
                        st.write(f"**TICKET REF #{tkt['ticket_id']}** ({tkt['event_title']}) — Buyer: {tkt['buyer']} | Paid: BWP {tkt['total_paid']:,.2f}")
                        with st.form(f"verify_tkt_form_{tkt['ticket_id']}"):
                            st.markdown("<div class='form-label'>WhatsApp Transaction Audit Reference</div>", unsafe_allow_html=True)
                            ref = st.text_input("", label_visibility="collapsed", key=f"tkt_ref_{tkt['ticket_id']}")
                            if st.form_submit_button("ACTIVATE DIGITAL GATE PASS"):
                                if ref:
                                    conn.execute("UPDATE tickets SET status = 'VALID', pop_reference = ? WHERE ticket_id = ?", (ref, tkt['ticket_id']))
                                    conn.commit()
                                    st.success(f"Ticket #{tkt['ticket_id']} Activated!")
                                    st.rerun()

            with tab_edit:
                with st.form("edit_facility_profile_form"):
                    st.markdown("<div class='form-label'>Corporate Venue Name</div>", unsafe_allow_html=True)
                    u_name = st.text_input("", value=cur_v['name'], label_visibility="collapsed", key="edit_fac_name")
                    st.markdown("<div class='form-label'>Telephone Line</div>", unsafe_allow_html=True)
                    u_phone = st.text_input("", value=cur_v['phone'], label_visibility="collapsed", key="edit_fac_phone")
                    st.markdown("<div class='form-label'>WhatsApp Audit Line</div>", unsafe_allow_html=True)
                    u_wa = st.text_input("", value=cur_v['whatsapp_no'], label_visibility="collapsed", key="edit_fac_wa")
                    st.markdown("<div class='form-label'>Corporate Settlement Instructions</div>", unsafe_allow_html=True)
                    u_bank = st.text_area("", value=cur_v['bank_details'], label_visibility="collapsed", key="edit_fac_bank")
                    st.markdown("<div class='form-label'>Brand Color Theme</div>", unsafe_allow_html=True)
                    u_color = st.color_picker("", value=cur_v['brand_color'], label_visibility="collapsed", key="edit_fac_color")
                    st.markdown("<div class='form-label'>Update Corporate Logo</div>", unsafe_allow_html=True)
                    u_logo = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="edit_fac_logo")

                    if st.form_submit_button("SAVE CORPORATE PROFILE"):
                        logo_url = process_compressed_image_upload(u_logo, cur_v['logo_url'])
                        conn.execute("""UPDATE venues SET name = ?, phone = ?, whatsapp_no = ?, bank_details = ?, brand_color = ?, logo_url = ?
                            WHERE venue_id = ?""", (u_name, u_phone, u_wa, u_bank, u_color, logo_url, cur_v['venue_id']))
                        conn.commit()
                        st.success("Corporate Profile Saved!")
                        st.rerun()

    conn.close()

# ---------------------------------------------------------
# 7. MODULE 3: VENDOR PORTAL & SERVICE FULFILLMENT
# ---------------------------------------------------------
elif user_role == "Vendor Portal & Service Fulfillment":
    st.markdown("<div class='exec-title'>Vendor Portal & Service Fulfillment Console</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Ancillary Supplier Account & Service Catalog</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    conn = get_db_connection()

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Facility Supporter":
        st.info("🔒 Vendor Operator Authentication Required")
        
        login_tab, reg_tab = st.tabs(["Vendor Operator Login", "Register Supplier Account"])
        
        with login_tab:
            with st.form("sup_login_form"):
                st.markdown("<div class='form-label'>Corporate Email Address</div>", unsafe_allow_html=True)
                l_email = st.text_input("", label_visibility="collapsed", key="sup_login_email")
                st.markdown("<div class='form-label'>Account Password</div>", unsafe_allow_html=True)
                l_pw = st.text_input("", type="password", label_visibility="collapsed", key="sup_login_pw")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("AUTHENTICATE VENDOR WORKSPACE", type="primary", use_container_width=True):
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
                        st.error("Invalid vendor credentials.")

        with reg_tab:
            with st.form("reg_supporter_auth_form"):
                st.markdown("<div class='form-label'>Trading Entity Name*</div>", unsafe_allow_html=True)
                s_name = st.text_input("", label_visibility="collapsed", key="reg_sup_name")
                st.markdown("<div class='form-label'>Industry Classification</div>", unsafe_allow_html=True)
                s_cat = st.selectbox("", ["Catering & Cutlery", "Stage & Decor", "Sound & AV", "Florist", "Security Services"], label_visibility="collapsed", key="reg_sup_cat")
                st.markdown("<div class='form-label'>Account Manager / Representative*</div>", unsafe_allow_html=True)
                s_person = st.text_input("", label_visibility="collapsed", key="reg_sup_person")
                st.markdown("<div class='form-label'>Corporate Email*</div>", unsafe_allow_html=True)
                s_email = st.text_input("", label_visibility="collapsed", key="reg_sup_email")
                st.markdown("<div class='form-label'>Account Password*</div>", unsafe_allow_html=True)
                s_pw = st.text_input("", type="password", label_visibility="collapsed", key="reg_sup_pw")
                st.markdown("<div class='form-label'>WhatsApp POP Verification Number*</div>", unsafe_allow_html=True)
                s_phone = st.text_input("", placeholder="26771234567", label_visibility="collapsed", key="reg_sup_phone")
                st.markdown("<div class='form-label'>Settlement Details*</div>", unsafe_allow_html=True)
                s_bank = st.text_area("", label_visibility="collapsed", key="reg_sup_bank")
                st.markdown("<div class='form-label'>Brand Color Theme</div>", unsafe_allow_html=True)
                s_color = st.color_picker("", "#1E293B", label_visibility="collapsed", key="reg_sup_color")
                st.markdown("<div class='form-label'>Corporate Logo</div>", unsafe_allow_html=True)
                s_logo = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="reg_sup_logo")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("REGISTER SUPPLIER ACCOUNT", type="primary", use_container_width=True):
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
                        st.success("Supplier Account Created! Please log in above.")
                    else:
                        st.error("Please fill in required fields.")
    else:
        cur_sup = conn.execute("SELECT * FROM supporters WHERE supporter_id = ?", (st.session_state["tenant_id"],)).fetchone()
        if cur_sup:
            st.markdown(f"""
                <div class="exec-card" style="border-top-color:{cur_sup['brand_color']}; text-align:center;">
                    <h2 style="margin:0; font-family:'Playfair Display', serif;">🚚 {cur_sup['business_name']}</h2>
                    <p style="margin:0.25rem 0 0 0; font-size:0.9rem;">INDUSTRY: {cur_sup['category']} | AUDIT WHATSAPP: {cur_sup['phone']}</p>
                </div>
            """, unsafe_allow_html=True)

            vtab1, vtab2, vtab3 = st.tabs(["Service Catalog Management", "Verify Vendor Invoices", "Corporate Profile"])

            with vtab1:
                with st.form("add_pkg_form"):
                    st.markdown("<div class='form-label'>Service Offering Title*</div>", unsafe_allow_html=True)
                    i_name = st.text_input("", label_visibility="collapsed", key="add_pkg_name")
                    st.markdown("<div class='form-label'>Service Specifications</div>", unsafe_allow_html=True)
                    i_desc = st.text_area("", label_visibility="collapsed", key="add_pkg_desc")
                    st.markdown("<div class='form-label'>Unit Metric Tariff</div>", unsafe_allow_html=True)
                    i_type = st.selectbox("", ["Per Guest", "Per Day", "Flat Rate", "Per Hour"], label_visibility="collapsed", key="add_pkg_type")
                    st.markdown("<div class='form-label'>Unit Tariff Price (BWP)</div>", unsafe_allow_html=True)
                    i_price = st.number_input("", min_value=1.0, value=150.0, label_visibility="collapsed", key="add_pkg_price")
                    st.markdown("<div class='form-label'>Service Media Graphic</div>", unsafe_allow_html=True)
                    i_photo = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="add_pkg_photo")

                    if st.form_submit_button("PUBLISH SERVICE OFFERING"):
                        if i_name:
                            img_url = process_compressed_image_upload(i_photo, SPACE_PRESETS[0])
                            conn.execute("""INSERT INTO vendor_templates 
                                (supporter_id, item_name, description, unit_type, unit_price, image_url, is_active)
                                VALUES (?, ?, ?, ?, ?, ?, 1)""",
                                (cur_sup['supporter_id'], i_name, i_desc, i_type, i_price, img_url))
                            conn.commit()
                            st.success("Offering Published!")
                            st.rerun()

                st.divider()
                templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ? AND is_active = 1", (cur_sup['supporter_id'],)).fetchall()
                for t in templates:
                    col_t1, col_t2 = st.columns([4, 1])
                    col_t1.write(f"• **{t['item_name'].upper()}** — Tariff: BWP {t['unit_price']:,.2f} / {t['unit_type']}")
                    if col_t2.button("DEACTIVATE OFFERING", key=f"del_item_{t['template_id']}"):
                        conn.execute("UPDATE vendor_templates SET is_active = 0 WHERE template_id = ?", (t['template_id'],))
                        conn.commit()
                        st.rerun()

            with vtab2:
                v_invs = conn.execute("SELECT * FROM vendor_invoices WHERE supporter_id = ? AND status = 'Pending POP'", (cur_sup['supporter_id'],)).fetchall()
                if not v_invs:
                    st.success("No pending invoice settlements.")
                else:
                    for inv in v_invs:
                        st.write(f"**INVOICE REF #{inv['vendor_invoice_id']}** — Client: {inv['customer_name']} | Amount Due: BWP {inv['total_amount']:,.2f}")
                        with st.form(f"verify_vinv_form_{inv['vendor_invoice_id']}"):
                            st.markdown("<div class='form-label'>WhatsApp Audit Reference</div>", unsafe_allow_html=True)
                            ref = st.text_input("", label_visibility="collapsed", key=f"vinv_ref_{inv['vendor_invoice_id']}")
                            if st.form_submit_button("CONFIRM SETTLEMENT"):
                                if ref:
                                    conn.execute("UPDATE vendor_invoices SET status = 'PAID & VERIFIED', pop_reference = ? WHERE vendor_invoice_id = ?", (ref, inv['vendor_invoice_id']))
                                    conn.commit()
                                    st.success("Invoice Paid!")
                                    st.rerun()

            with vtab3:
                with st.form("edit_vendor_profile_form"):
                    st.markdown("<div class='form-label'>WhatsApp Audit Line</div>", unsafe_allow_html=True)
                    u_phone = st.text_input("", value=cur_sup['phone'], label_visibility="collapsed", key="edit_sup_phone")
                    st.markdown("<div class='form-label'>Settlement Details</div>", unsafe_allow_html=True)
                    u_bank = st.text_area("", value=cur_sup['bank_details'], label_visibility="collapsed", key="edit_sup_bank")
                    st.markdown("<div class='form-label'>Brand Color Theme</div>", unsafe_allow_html=True)
                    u_color = st.color_picker("", value=cur_sup['brand_color'], label_visibility="collapsed", key="edit_sup_color")
                    st.markdown("<div class='form-label'>Update Corporate Logo</div>", unsafe_allow_html=True)
                    u_logo = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="edit_sup_logo")

                    if st.form_submit_button("SAVE VENDOR PROFILE"):
                        logo_url = process_compressed_image_upload(u_logo, cur_sup['logo_url'])
                        conn.execute("""UPDATE supporters SET phone = ?, bank_details = ?, brand_color = ?, logo_url = ?
                            WHERE supporter_id = ?""", (u_phone, u_bank, u_color, logo_url, cur_sup['supporter_id']))
                        conn.commit()
                        st.success("Vendor Profile Saved!")
                        st.rerun()

    conn.close()

# ---------------------------------------------------------
# 8. MODULE 4: ACCESS CONTROL & VERIFICATION SUITE
# ---------------------------------------------------------
elif user_role == "Access Control & Verification Suite":
    st.markdown("<div class='exec-title'>Access Control & Optical Verification Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Smartphone & Optical QR Pass Scanner</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    conn = get_db_connection()
    
    st.markdown("<div class='form-label'>Align Digital Pass Barcode within Frame</div>", unsafe_allow_html=True)
    camera_file = st.camera_input("", key="access_camera_input")
    
    st.markdown("<div class='form-label'>Or Enter Verification Hash Manually</div>", unsafe_allow_html=True)
    scan_input = st.text_input("", label_visibility="collapsed", key="access_hash_input")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("AUTHENTICATE ADMISSION PASS", type="primary", use_container_width=True, key="btn_auth_pass"):
        target_str = scan_input.strip().upper()
        if target_str:
            tkt = conn.execute("SELECT * FROM tickets WHERE verification_hash = ? OR ticket_id = ?", (target_str, target_str)).fetchone()
            if tkt:
                if tkt['status'] == 'VALID':
                    conn.execute("UPDATE tickets SET status = 'USED / SCANNED', scanned_at = ? WHERE ticket_id = ?", (str(datetime.datetime.now()), tkt['ticket_id']))
                    conn.commit()
                    st.success(f"✅ ACCESS GRANTED: {tkt['buyer']} ({tkt['qty']} Person/s) — Event: {tkt['event_title']}")
                elif 'Pending' in tkt['status']:
                    st.warning("⚠️ UNVERIFIED PASS: Payment Proof of Payment (POP) pending operator verification.")
                else:
                    st.error("❌ INVALID ENTRY: Pass already redeemed.")
            else:
                st.error("❌ Invalid Ticket Verification Hash.")
    conn.close()

# ---------------------------------------------------------
# 9. MODULE 5: EXECUTIVE MASTER LEDGER & AUDIT SUITE (LOCKED)
# ---------------------------------------------------------
elif user_role == "Executive Master Ledger & Audit Suite":
    st.markdown("<div class='exec-title'>Executive Master Ledger & Audit Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Platform-Wide System Ledgers & Analytics</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    # SECURE MASTER ADMIN AUTHENTICATION GATE
    MASTER_ADMIN_PASSWORD_HASH = hash_pw("AdminSecureKey2026!")

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Platform Admin":
        st.info("🔒 Platform Master Administrator Access Required")
        
        with st.form("master_admin_login_form"):
            st.markdown("<div class='form-label'>Master Administrator Email</div>", unsafe_allow_html=True)
            a_email = st.text_input("", label_visibility="collapsed", key="admin_email")
            st.markdown("<div class='form-label'>Executive Master Password</div>", unsafe_allow_html=True)
            a_pw = st.text_input("", type="password", label_visibility="collapsed", key="admin_pw")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("AUTHENTICATE EXECUTIVE ACCESS", type="primary", use_container_width=True):
                if hash_pw(a_pw) == MASTER_ADMIN_PASSWORD_HASH:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = a_email
                    st.session_state["user_role"] = "Platform Admin"
                    st.success("Executive Master Access Granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Master Administrator Credentials.")
    else:
        conn = get_db_connection()
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("VENUES", conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0])
        m2.metric("VENDORS", conn.execute("SELECT COUNT(*) FROM supporters").fetchone()[0])
        m3.metric("BOOKINGS", conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0])
        m4.metric("INVOICES", conn.execute("SELECT COUNT(*) FROM vendor_invoices").fetchone()[0])
        m5.metric("TICKETS", conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0])

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
