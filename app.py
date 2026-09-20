import streamlit as st
import sqlite3
import datetime
import hashlib
import secrets
import base64
import json
import os
import io

# ReportLab Engine (In-Memory PDF Generation)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Image & QR Code Engine
import qrcode
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------
# 1. DATABASE ENGINE (SQLITE CLOUD-READY)
# ---------------------------------------------------------
DB_FILE = "enterprise_platform.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Auth Users (Salted Hashes)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, salt TEXT, role TEXT, tenant_id TEXT
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
# 2. UTILITIES: SECURITY, IMAGES, PDF, QR & FLYER GENERATION
# ---------------------------------------------------------
DEFAULT_LOGO = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150"
SPACE_PRESETS = ["https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=400"]

def hash_pw(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    salted_password = f"{salt}{password}".encode('utf-8')
    pwd_hash = hashlib.sha256(salted_password).hexdigest()
    return pwd_hash, salt

def verify_pw(password, pwd_hash, salt):
    test_hash, _ = hash_pw(password, salt)
    return test_hash == pwd_hash

def process_compressed_image_upload(uploaded_file, fallback_url, max_dim=500):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail((max_dim, max_dim))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=60, optimize=True)
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception:
            return fallback_url
    return fallback_url

def generate_branded_flyer(venue_name, event_title, event_date, price, start_time="18:00", end_time="23:00", comments="", uploaded_bg_file=None, brand_color="#0F172A"):
    """Generates a compact, custom-branded event flyer (400x500) with dynamic backdrop, timing & custom comments."""
    width, height = 400, 500

    # Handle Backdrop Image
    if uploaded_bg_file is not None:
        try:
            bg_img = Image.open(uploaded_bg_file).convert("RGB")
            # Resize and center crop
            bg_ratio = bg_img.width / bg_img.height
            target_ratio = width / height
            if bg_ratio > target_ratio:
                new_width = int(height * bg_ratio)
                bg_img = bg_img.resize((new_width, height), Image.Resampling.LANCZOS)
                left = (new_width - width) // 2
                bg_img = bg_img.crop((left, 0, left + width, height))
            else:
                new_height = int(width / bg_ratio)
                bg_img = bg_img.resize((width, new_height), Image.Resampling.LANCZOS)
                top = (new_height - height) // 2
                bg_img = bg_img.crop((0, top, width, top + height))
            
            # Apply dark overlay for text readability
            overlay = Image.new("RGBA", (width, height), (15, 23, 42, 200))
            img = bg_img.convert("RGBA")
            img = Image.alpha_composite(img, overlay).convert("RGB")
        except Exception:
            img = Image.new("RGB", (width, height), color="#0F172A")
    else:
        img = Image.new("RGB", (width, height), color="#0F172A")

    draw = ImageDraw.Draw(img)
    
    # Header Banner
    draw.rectangle([(0, 0), (width, 60)], fill=brand_color)
    draw.rectangle([(10, 10), (width-10, height-10)], outline="#D97706", width=2)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_sub = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 11)
        font_bold = ImageFont.truetype("arialbd.ttf", 13)
    except IOError:
        font_title = font_sub = font_small = font_bold = ImageFont.load_default()
        
    draw.text((width//2, 30), venue_name.upper(), fill="#FFFFFF", font=font_sub, anchor="mm")
    draw.text((width//2, 90), event_title, fill="#F59E0B", font=font_title, anchor="mm")
    
    draw.line([(40, 120), (width-40, 120)], fill="#CBD5E1", width=1)
    
    # Time and Date Block
    time_str = f"TIME: {start_time} - {end_time}"
    draw.text((width//2, 145), f"DATE: {event_date}", fill="#F8FAFC", font=font_bold, anchor="mm")
    draw.text((width//2, 170), time_str, fill="#38BDF8", font=font_bold, anchor="mm")
    draw.text((width//2, 210), f"ADMISSION: BWP {price:,.2f}", fill="#10B981", font=font_title, anchor="mm")
    
    # Custom Comments Box Section
    if comments:
        draw.rectangle([(30, 250), (width-30, 390)], fill=(0, 0, 0, 120), outline="#64748B", width=1)
        draw.text((width//2, 270), "— EVENT DETAILS / NOTES —", fill="#D97706", font=font_small, anchor="mm")
        
        # Word Wrap Comments
        words = comments.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 35:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        y_offset = 295
        for line in lines[:4]:  # Max 4 lines display
            draw.text((width//2, y_offset), line, fill="#E2E8F0", font=font_small, anchor="mm")
            y_offset += 20

    draw.text((width//2, 465), "OFFICIAL ADMISSION PASS — EXECUTIVE EVENT HUB", fill="#94A3B8", font=font_small, anchor="mm")
    
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    b64_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64_str}"

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
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#1E293B'))
    header_cell_style = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName='Helvetica-Bold')

    story.append(Paragraph(f"{title_text.upper()}", title_style))
    story.append(Spacer(1, 10))

    meta_data = [
        [Paragraph(f"<b>Document Ref:</b> {inv_id}", body_style), Paragraph(f"<b>Date:</b> {created_at}", body_style)],
        [Paragraph(f"<b>Entity / Issuer:</b> {entity_name}", body_style), Paragraph(f"<b>Tax ID / CIPA:</b> {tax_id}", body_style)],
        [Paragraph(f"<b>Client / Billed To:</b> {client_name}", body_style), Paragraph(f"<b>Contact Email:</b> {client_email}", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    table_data = [[
        Paragraph("Line Item Description", header_cell_style),
        Paragraph("Qty / Duration", header_cell_style),
        Paragraph("Unit Price (BWP)", header_cell_style),
        Paragraph("Line Total (BWP)", header_cell_style)
    ]]
    for item in items_list:
        table_data.append([
            Paragraph(item.get('item_name', 'Service Description'), body_style),
            Paragraph(str(item.get('qty', 1)), body_style),
            Paragraph(f"{item.get('unit_price', 0):,.2f}", body_style),
            Paragraph(f"{item.get('subtotal', 0):,.2f}", body_style)
        ])
    
    total_cell_style = ParagraphStyle('TotalCell', parent=styles['Normal'], fontSize=10, leading=13, textColor=colors.HexColor('#0F172A'), fontName='Helvetica-Bold')
    table_data.append([
        Paragraph("TOTAL AMOUNT DUE", total_cell_style),
        Paragraph("", body_style),
        Paragraph("", body_style),
        Paragraph(f"BWP {total_amount:,.2f}", total_cell_style)
    ])

    t_items = Table(table_data, colWidths=[240, 90, 105, 105])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('SPAN', (0, -1), (2, -1))
    ]))
    story.append(t_items)
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Settlement Terms & Bank Account Details:</b><br/>{bank_details}", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------------
# 3. EXECUTIVE CSS STYLING
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
                        <img src="{sel_venue['logo_url'] or DEFAULT_LOGO}" class="logo-img" style="background:white; padding:4px; border:1px solid #E2E8F0; border-radius:4px; height: 50px;">
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
                col1.image(ev['flyer_url'] or SPACE_PRESETS[0], width=350)
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
                    
                    if st.form_submit_button("SUBMIT TICKET ORDER"):
                        if t_buyer and t_email:
                            tkt_id = f"TKT-{int(datetime.datetime.now().timestamp())}"
                            sec_hash = f"HASH-{hashlib.sha256(f'{tkt_id}-{t_email}'.encode()).hexdigest()[:10].upper()}"
                            
                            # Insert as Pending Verification — NO PASS RELEASED YET
                            conn.execute("""INSERT INTO tickets
                                (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending WhatsApp POP Verification')""",
                                (tkt_id, sec_hash, ev['event_id'], ev['title'], v['venue_id'] if v else "", ev['venue_name'], v['logo_url'] if v else DEFAULT_LOGO, t_buyer, t_email, t_qty, t_qty*ev['price'], t_pay))
                            conn.commit()
                            
                            st.warning("⏳ Order Placed! Ticket pass is pending payment verification.")
                            
                            wa_num = v['whatsapp_no'] if v and v['whatsapp_no'] else ""
                            st.info(f"👉 **Next Step:** Send your Proof of Payment (POP) along with Order Ref **`{tkt_id}`** via WhatsApp to **+{wa_num}** for verification before your ticket pass is released.")
                            if wa_num:
                                wa_link = f"https://wa.me/{wa_num}?text=Hello,%20here%20is%20my%20POP%20for%20Ticket%20Ref:%20{tkt_id}"
                                st.markdown(f"[📲 Click Here to Open WhatsApp & Submit POP]({wa_link})")
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
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'Facility Owner'", (l_email,)).fetchone()
                    if user and verify_pw(l_pw, user['password_hash'], user['salt']):
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
                    st.markdown("<div class='form-label'>Max Guest Capacity</div>", unsafe_allow_html=True)
                    f_cap = st.number_input("", min_value=10, value=500, label_visibility="collapsed", key="reg_fac_cap")
                    st.markdown("<div class='form-label'>Primary Settlement Bank Details*</div>", unsafe_allow_html=True)
                    f_bank = st.text_area("", placeholder="Bank Name, Branch, Account No.", label_visibility="collapsed", key="reg_fac_bank")

                st.markdown("<div class='form-label'>Corporate Logo Image</div>", unsafe_allow_html=True)
                logo_file = st.file_uploader("", type=["png", "jpg", "jpeg"], key="reg_fac_logo")
                
                if st.form_submit_button("REGISTER FACILITY & PUBLISH WORKSPACE", type="primary", use_container_width=True):
                    if f_name and f_email and f_pw and f_tax:
                        v_id = f"VEN-{int(datetime.datetime.now().timestamp())}"
                        pw_hash, salt = hash_pw(f_pw)
                        
                        logo_str = process_compressed_image_upload(logo_file, DEFAULT_LOGO)

                        try:
                            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, 'Facility Owner', ?)",
                                         (f"USR-{v_id}", f_email, pw_hash, salt, v_id))
                            conn.execute("""INSERT INTO venues 
                                (venue_id, name, type, email, phone, whatsapp_no, address, max_capacity, tax_id, bank_details, brand_color, logo_url, flyer_image_url, approved_supporter_ids)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '#0F172A', ?, ?, '[]')""",
                                (v_id, f_name, f_type, f_email, f_phone, f_whatsapp, f_address, f_cap, f_tax, f_bank, logo_str, SPACE_PRESETS[0]))
                            conn.commit()
                            st.success("Commercial Property successfully registered. Please log in.")
                        except sqlite3.IntegrityError:
                            st.error("Email is already registered.")
                    else:
                        st.error("Please fill in all mandatory fields.")
    else:
        v_id = st.session_state["tenant_id"]
        venue = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (v_id,)).fetchone()
        
        st.subheader(f"Workspace: {venue['name']}")
        tab_subspaces, tab_supp, tab_events = st.tabs(["🏛️ Sub-Space Inventory", "🤝 Vendor Approvals", "🎟️ Public Events Management"])
        
        with tab_subspaces:
            with st.form("add_space_form"):
                st.markdown("##### Add New Sub-Space Asset")
                sc1, sc2, sc3 = st.columns(3)
                sp_name = sc1.text_input("Sub-Space Name (e.g. Hall A)")
                sp_cap = sc2.number_input("Max Capacity", min_value=1, value=100)
                sp_rate = sc3.number_input("Daily Hire Tariff (BWP)", min_value=0.0, value=1500.0)
                sp_img = st.file_uploader("Space Image", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("ADD SUB-SPACE TO INVENTORY"):
                    if sp_name:
                        img_str = process_compressed_image_upload(sp_img, SPACE_PRESETS[0])
                        conn.execute("INSERT INTO spaces (venue_id, name, capacity, daily_rate, image_url) VALUES (?, ?, ?, ?, ?)",
                                     (v_id, sp_name, sp_cap, sp_rate, img_str))
                        conn.commit()
                        st.success(f"Added {sp_name} to inventory.")
                        st.rerun()

            st.divider()
            st.markdown("##### Current Sub-Spaces")
            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (v_id,)).fetchall()
            for s in spaces:
                col1, col2 = st.columns([1, 4])
                col1.image(s['image_url'] or SPACE_PRESETS[0], use_container_width=True)
                col2.write(f"**{s['name']}** | Capacity: {s['capacity']} | Daily Rate: BWP {s['daily_rate']:,.2f}")

        with tab_supp:
            st.markdown("##### Approved Vendor Network")
            all_vendors = conn.execute("SELECT * FROM supporters").fetchall()
            current_approved = json.loads(venue['approved_supporter_ids'] or "[]")
            
            updated_approved = []
            for v in all_vendors:
                is_app = v['supporter_id'] in current_approved
                if st.checkbox(f"Approve {v['business_name']} ({v['category']})", value=is_app, key=f"chk_v_{v['supporter_id']}"):
                    updated_approved.append(v['supporter_id'])
            
            if st.button("UPDATE VENDOR NETWORK APPROVALS"):
                conn.execute("UPDATE venues SET approved_supporter_ids = ? WHERE venue_id = ?", (json.dumps(updated_approved), v_id))
                conn.commit()
                st.success("Vendor network updated successfully.")

        with tab_events:
            st.markdown("##### Create & Manage Public Ticketed Events")
            
            ev_title = st.text_input("Event Title*", key="ev_p_title")
            col_e1, col_e2 = st.columns(2)
            ev_date = col_e1.date_input("Event Date*", min_value=datetime.date.today(), key="ev_p_date")
            ev_price = col_e2.number_input("Ticket Tariff (BWP)*", min_value=0.0, value=100.0, step=10.0, key="ev_p_price")
            
            # Start and End Times
            t_col1, t_col2 = st.columns(2)
            ev_start_time = t_col1.time_input("Event Start Time*", value=datetime.time(18, 0), key="ev_p_start")
            ev_end_time = t_col2.time_input("Event End Time*", value=datetime.time(23, 0), key="ev_p_end")

            # Comments box for flyer details
            ev_comments = st.text_area("Additional Notes / Comments for Flyer (e.g. VIP Dress Code, Special Guests)", key="ev_p_comments")

            # Flyer Backdrop File Uploader
            ev_flyer_bg = st.file_uploader("Upload Custom Flyer Background Image", type=["png", "jpg", "jpeg"], key="ev_p_flyer_bg")
            
            st.divider()
            st.markdown("##### 👁️ Live Compact Flyer Preview (Backdrop + Timings + Comments)")
            
            start_str = ev_start_time.strftime("%H:%M")
            end_str = ev_end_time.strftime("%H:%M")

            if ev_title:
                preview_flyer = generate_branded_flyer(
                    venue_name=venue['name'],
                    event_title=ev_title,
                    event_date=str(ev_date),
                    price=ev_price,
                    start_time=start_str,
                    end_time=end_str,
                    comments=ev_comments,
                    uploaded_bg_file=ev_flyer_bg,
                    brand_color=venue['brand_color'] or "#0F172A"
                )
                st.image(preview_flyer, caption="Live Preview of Custom Compact Flyer / Ticket Pass", width=350)
            else:
                st.caption("Type an event title above to view the live generated flyer preview.")

            st.divider()
            if st.button("PUBLISH EVENT TO BOX OFFICE", type="primary", use_container_width=True):
                if ev_title:
                    ev_id = f"EV-{int(datetime.datetime.now().timestamp())}"
                    
                    flyer_str = generate_branded_flyer(
                        venue_name=venue['name'],
                        event_title=ev_title,
                        event_date=str(ev_date),
                        price=ev_price,
                        start_time=start_str,
                        end_time=end_str,
                        comments=ev_comments,
                        uploaded_bg_file=ev_flyer_bg,
                        brand_color=venue['brand_color'] or "#0F172A"
                    )
                    
                    conn.execute("""INSERT INTO events 
                        (event_id, venue_id, venue_name, space_name, title, date, price, description, flyer_url, is_active)
                        VALUES (?, ?, ?, 'Main Facility', ?, ?, ?, ?, ?, 1)""",
                        (ev_id, v_id, venue['name'], ev_title, str(ev_date), ev_price, ev_comments, flyer_str))
                    conn.commit()
                    st.success(f"🎉 Event '{ev_title}' has been published with dynamic flyer backdrop!")
                    st.rerun()
                else:
                    st.error("Please enter a title for the event before publishing.")

            st.divider()
            st.markdown("##### Published Events")
            
            my_events = conn.execute("SELECT * FROM events WHERE venue_id = ? ORDER BY date DESC", (v_id,)).fetchall()
            if not my_events:
                st.info("No public events published yet.")
            else:
                for ev in my_events:
                    with st.expander(f"{'🟢 Active' if ev['is_active'] else '🔴 Inactive'} — {ev['title']} ({ev['date']})"):
                        ec1, ec2 = st.columns([1, 3])
                        if ev['flyer_url']:
                            ec1.image(ev['flyer_url'], width=220)
                        ec2.write(f"**Ticket Tariff:** BWP {ev['price']:,.2f}")
                        ec2.write(f"**Notes / Inclusions:** {ev['description'] or 'N/A'}")
                        
                        btn_label = "Deactivate Event" if ev['is_active'] else "Activate Event"
                        if ec2.button(btn_label, key=f"toggle_ev_{ev['event_id']}"):
                            new_status = 0 if ev['is_active'] else 1
                            conn.execute("UPDATE events SET is_active = ? WHERE event_id = ?", (new_status, ev['event_id']))
                            conn.commit()
                            st.rerun()

    conn.close()

# ---------------------------------------------------------
# 7. MODULE 3: VENDOR PORTAL & SERVICE FULFILLMENT
# ---------------------------------------------------------
elif user_role == "Vendor Portal & Service Fulfillment":
    st.markdown("<div class='exec-title'>Vendor Portal & Service Fulfillment</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Ancillary Service Provider Management Console</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    conn = get_db_connection()

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Supporter":
        st.info("🔒 Service Provider Authentication Required")
        v_login_tab, v_reg_tab = st.tabs(["Vendor Account Login", "Register Service Entity"])
        
        with v_login_tab:
            with st.form("vendor_login_form"):
                st.markdown("<div class='form-label'>Corporate Email Address</div>", unsafe_allow_html=True)
                vl_email = st.text_input("", label_visibility="collapsed", key="v_login_email")
                st.markdown("<div class='form-label'>Account Password</div>", unsafe_allow_html=True)
                vl_pw = st.text_input("", type="password", label_visibility="collapsed", key="v_login_pw")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("AUTHENTICATE VENDOR WORKSPACE", type="primary", use_container_width=True):
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'Supporter'", (vl_email,)).fetchone()
                    if user and verify_pw(vl_pw, user['password_hash'], user['salt']):
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = vl_email
                        st.session_state["user_role"] = "Supporter"
                        st.session_state["tenant_id"] = user['tenant_id']
                        st.success("Authentication successful!")
                        st.rerun()
                    else:
                        st.error("Invalid vendor credentials.")

        with v_reg_tab:
            with st.form("reg_vendor_form"):
                vc1, vc2 = st.columns(2)
                with vc1:
                    v_biz = st.text_input("Business Name*")
                    v_cat = st.selectbox("Service Category", ["Catering", "Audio Visual", "Security", "Decor", "Photography"])
                    v_email = st.text_input("Corporate Email*")
                    v_pw = st.text_input("Account Password*", type="password")
                with vc2:
                    v_contact = st.text_input("Contact Person Name*")
                    v_phone = st.text_input("Direct Telephone Line*")
                    v_bank = st.text_area("Settlement Bank Details*")
                
                if st.form_submit_button("REGISTER VENDOR ENTITY", type="primary", use_container_width=True):
                    if v_biz and v_email and v_pw:
                        s_id = f"SUP-{int(datetime.datetime.now().timestamp())}"
                        pw_hash, salt = hash_pw(v_pw)
                        try:
                            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, 'Supporter', ?)", (f"USR-{s_id}", v_email, pw_hash, salt, s_id))
                            conn.execute("""INSERT INTO supporters (supporter_id, business_name, category, contact_person, email, phone, bank_details, brand_color, logo_url)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, '#0F172A', ?)""",
                                         (s_id, v_biz, v_cat, v_contact, v_email, v_phone, v_bank, DEFAULT_LOGO))
                            conn.commit()
                            st.success("Vendor profile registered successfully!")
                        except sqlite3.IntegrityError:
                            st.error("Email is already registered.")
    else:
        sup_id = st.session_state["tenant_id"]
        supporter = conn.execute("SELECT * FROM supporters WHERE supporter_id = ?", (sup_id,)).fetchone()
        
        st.subheader(f"Vendor Workspace: {supporter['business_name']}")
        
        v_tab_catalog, v_tab_orders = st.tabs(["📦 Service Tariff Catalog", "📋 Active Service Orders"])
        
        with v_tab_catalog:
            with st.form("add_template_form"):
                st.markdown("##### Add New Service Package")
                tc1, tc2 = st.columns(2)
                item_name = tc1.text_input("Service Item Name (e.g. Executive Buffet)")
                unit_type = tc2.selectbox("Unit Basis", ["Per Person", "Per Day", "Flat Fee", "Per Hour"])
                unit_price = tc1.number_input("Unit Price (BWP)", min_value=0.0, value=250.0)
                item_desc = tc2.text_area("Service Specs / Inclusions")
                item_img = st.file_uploader("Catalog Photo", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("PUBLISH SERVICE TARIFF"):
                    if item_name:
                        img_str = process_compressed_image_upload(item_img, "")
                        conn.execute("""INSERT INTO vendor_templates (supporter_id, item_name, description, unit_type, unit_price, image_url)
                                        VALUES (?, ?, ?, ?, ?, ?)""", (sup_id, item_name, item_desc, unit_type, unit_price, img_str))
                        conn.commit()
                        st.success("Service package added successfully!")
                        st.rerun()

            st.divider()
            st.markdown("##### Current Service Catalog")
            templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ?", (sup_id,)).fetchall()
            for t in templates:
                st.write(f"**{t['item_name']}** — BWP {t['unit_price']:,.2f} / {t['unit_type']}")

        with v_tab_orders:
            st.markdown("##### Service Invoices & Orders")
            vinvs = conn.execute("SELECT * FROM vendor_invoices WHERE supporter_id = ?", (sup_id,)).fetchall()
            if not vinvs:
                st.info("No active service orders found.")
            else:
                for vi in vinvs:
                    st.write(f"**Invoice #{vi['vendor_invoice_id']}** | Event Date: {vi['event_date']} | Status: {vi['status']} | Total: BWP {vi['total_amount']:,.2f}")
    
    conn.close()

# ---------------------------------------------------------
# 8. MODULE 4: ACCESS CONTROL & VERIFICATION SUITE
# ---------------------------------------------------------
elif user_role == "Access Control & Verification Suite":
    st.markdown("<div class='exec-title'>Access Control & Gate Scanner Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Real-Time QR Admission Pass Verification</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    
    scan_hash = st.text_input("Enter Pass Security Hash / Scan String:", placeholder="HASH-XXXXXXXXXX")
    
    if st.button("VERIFY & PROCESS ADMISSION PASS", type="primary"):
        if scan_hash:
            ticket = conn.execute("SELECT * FROM tickets WHERE verification_hash = ?", (scan_hash,)).fetchone()
            if not ticket:
                st.error("❌ INVALID TICKET PASS: Hash reference not found in master ledger.")
            elif ticket['status'] == 'Admitted / Claimed':
                st.error(f"❌ REJECTED - PASS ALREADY USED: Claimed at {ticket['scanned_at']}")
            elif 'Pending' in ticket['status']:
                st.warning(f"⚠️ ADMISSION DENIED: Settlement Status is '{ticket['status']}'. Payment verification required.")
            elif ticket['status'] == 'Verified / Active':
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("UPDATE tickets SET status = 'Admitted / Claimed', scanned_at = ? WHERE ticket_id = ?", (now_str, ticket['ticket_id']))
                conn.commit()
                st.balloons()
                st.success(f"✅ ACCESS GRANTED: Welcome {ticket['buyer']}! Pass validated ({ticket['qty']} Person Admission).")
        else:
            st.warning("Please enter a valid ticket security hash.")
            
    conn.close()

# ---------------------------------------------------------
# 9. MODULE 5: EXECUTIVE MASTER LEDGER & AUDIT SUITE
# ---------------------------------------------------------
elif user_role == "Executive Master Ledger & Audit Suite":
    st.markdown("<div class='exec-title'>Executive Master Ledger & Settlement Audit</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Financial Oversight, Proof-of-Payment Verification & Reconciliation</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    
    if not st.session_state["authenticated"] or st.session_state["user_role"] != "Auditor":
        st.info("🔒 Auditor / Executive Clearance Required")
        with st.form("audit_login_form"):
            a_email = st.text_input("Auditor Email Address")
            a_pw = st.text_input("Master Password", type="password")
            if st.form_submit_button("AUTHENTICATE AUDIT CONSOLE", type="primary", use_container_width=True):
                if a_email == "admin@executive.co.bw" and a_pw == "AdminPass123!":
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = a_email
                    st.session_state["user_role"] = "Auditor"
                    st.success("Master Clearance Granted.")
                    st.rerun()
                else:
                    st.error("Invalid audit credentials.")
    else:
        st.subheader("Global Settlement Audit Console")
        
        tab_v_settle, tab_tkt_settle = st.tabs(["🏛️ Venue & Vendor Bookings Settlement", "🎟️ Ticket Sales Settlement"])
        
        with tab_v_settle:
            st.markdown("##### Venue Hire & Vendor Invoices Reconciliation")
            bookings = conn.execute("SELECT * FROM bookings").fetchall()
            for b in bookings:
                with st.expander(f"Booking #{b['booking_id']} — {b['customer_name']} (BWP {b['venue_cost']:,.2f}) — Status: {b['status']}"):
                    st.write(f"**Venue Asset:** {b['space_name']} | **Event Date:** {b['booking_date']}")
                    st.write(f"**Contact Email:** {b['customer_email']} | **Phone:** {b['customer_phone']}")
                    st.write(f"**Payment Method:** {b['payment_method']} | **POP Reference:** {b['pop_reference'] or 'None Provided'}")
                    
                    pop_ref = st.text_input(f"Proof of Payment Ref for {b['booking_id']}", value=b['pop_reference'] or "", key=f"pop_b_{b['booking_id']}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("APPROVE PAYMENT & CONFIRM RESERVATION", key=f"app_b_{b['booking_id']}"):
                        conn.execute("UPDATE bookings SET status = 'Settled & Confirmed', pop_reference = ? WHERE booking_id = ?", (pop_ref, b['booking_id']))
                        conn.commit()
                        st.success("Booking status updated to Settled & Confirmed.")
                        st.rerun()
                    if c2.button("CANCEL RESERVATION", key=f"can_b_{b['booking_id']}"):
                        conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ?", (b['booking_id'],))
                        conn.commit()
                        st.warning("Booking marked as Cancelled.")
                        st.rerun()

        with tab_tkt_settle:
            st.markdown("##### Box Office Ticket Pass Reconciliations")
            tkts = conn.execute("SELECT * FROM tickets").fetchall()
            for t in tkts:
                with st.expander(f"Pass #{t['ticket_id']} — {t['buyer']} ({t['event_title']}) — Status: {t['status']}"):
                    st.write(f"**Qty:** {t['qty']} | **Total Paid:** BWP {t['total_paid']:,.2f} | **Method:** {t['payment_method']}")
                    st.write(f"**Security Hash:** `{t['verification_hash']}`")
                    
                    tkt_pop = st.text_input(f"POP Reference for {t['ticket_id']}", value=t['pop_reference'] or "", key=f"pop_t_{t['ticket_id']}")
                    if st.button("VERIFY WhatsApp POP & RELEASE ACTIVE TICKET PASS", key=f"app_t_{t['ticket_id']}"):
                        conn.execute("UPDATE tickets SET status = 'Verified / Active', pop_reference = ? WHERE ticket_id = ?", (tkt_pop, t['ticket_id']))
                        conn.commit()
                        st.success("Ticket pass activated and released!")
                        st.rerun()

    conn.close()
