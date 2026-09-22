import streamlit as st
import sqlite3
import datetime
import hashlib
import secrets
import base64
import json
import os
import io

# ReportLab Engine (In-Memory PDF Generation with Image Support)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
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
    
    # Auth Users
    c.execute('''CREATE TABLE IF NOT EXISTS users(
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
# 2. UTILITIES: SECURITY, IMAGES, PDF & QR CODES
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

def process_compressed_image_upload(uploaded_file, fallback_url, max_dim=800):
    """Resizes and compresses images to a lightweight format."""
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail((max_dim, max_dim))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception:
            return fallback_url
    return fallback_url

def generate_branded_flyer(venue_name, event_title, event_date, price, start_time="18:00", end_time="23:00", comments="", uploaded_bg_file=None, brand_color="#D97706"):
    """Generates a light-colored standard digital flyer (500x700 px) with large readable text."""
    width, height = 500, 700

    if uploaded_bg_file is not None:
        try:
            bg_img = Image.open(uploaded_bg_file).convert("RGB")
            bg_img = bg_img.resize((width, height))
            
            # Semi-transparent light overlay so dark text is easily readable
            overlay = Image.new("RGBA", (width, height), (255, 255, 255, 210))
            img = Image.alpha_composite(bg_img.convert("RGBA"), overlay).convert("RGB")
        except Exception:
            img = Image.new("RGB", (width, height), color="#F8FAFC")
    else:
        img = Image.new("RGB", (width, height), color="#F8FAFC")

    draw = ImageDraw.Draw(img)
    
    # Outer Border & Light Header Band
    draw.rectangle([(0, 0), (width, 80)], fill="#0F172A")
    draw.rectangle([(10, 10), (width-10, height-10)], outline=brand_color, width=3)
    
    try:
        font_header = ImageFont.truetype("arialbd.ttf", 22)
        font_title = ImageFont.truetype("arialbd.ttf", 28)
        font_sub = ImageFont.truetype("arialbd.ttf", 18)
        font_body = ImageFont.truetype("arial.ttf", 15)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        font_header = font_title = font_sub = font_body = font_small = ImageFont.load_default()
        
    # Venue Name (Top Banner)
    draw.text((width//2, 40), venue_name.upper(), fill="#FFFFFF", font=font_header, anchor="mm")
    
    # Event Title
    draw.text((width//2, 130), event_title, fill="#0F172A", font=font_title, anchor="mm")
    draw.line([(50, 160), (width-50, 160)], fill=brand_color, width=2)
    
    # Date & Time Section
    draw.text((width//2, 200), f"DATE: {event_date}", fill="#1E293B", font=font_sub, anchor="mm")
    draw.text((width//2, 235), f"TIME: {start_time} - {end_time}", fill="#0284C7", font=font_sub, anchor="mm")
    
    # Price Tag Badge
    draw.rectangle([(80, 275), (width-80, 335)], fill="#0F172A", outline=brand_color, width=2)
    draw.text((width//2, 305), f"ADMISSION: BWP {price:,.2f}", fill="#F59E0B", font=font_sub, anchor="mm")
    
    # Event Comments / Details Box
    if comments:
        draw.rectangle([(30, 360), (width-30, 620)], fill="#FFFFFF", outline="#CBD5E1", width=2)
        draw.text((width//2, 390), "— EVENT DETAILS —", fill=brand_color, font=font_sub, anchor="mm")
        
        words = comments.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 32:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        y_offset = 430
        for line in lines[:7]:
            draw.text((width//2, y_offset), line, fill="#334155", font=font_body, anchor="mm")
            y_offset += 25

    draw.text((width//2, 660), "OFFICIAL ADMISSION PASS — EXECUTIVE EVENT HUB", fill="#64748B", font=font_small, anchor="mm")
    
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    b64_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64_str}"

def generate_qr_code_base64(data_string):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def generate_in_memory_pdf_bytes(title_text, inv_id, created_at, entity_name, tax_id, client_name, client_email, items_list, total_amount, bank_details, logo_b64=None):
    """Generates official lightweight PDF invoices embedded with entity branding logos."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), alignment=0)
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#1E293B'))
    header_cell_style = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName='Helvetica-Bold')

    # Brand Logo Header Section
    logo_flowable = None
    if logo_b64 and "base64," in logo_b64:
        try:
            base64_data = logo_b64.split("base64,")[1]
            img_data = base64.b64decode(base64_data)
            img_buffer = io.BytesIO(img_data)
            logo_flowable = RLImage(img_buffer, width=60, height=60)
        except Exception:
            logo_flowable = None

    header_table_data = [
        [logo_flowable if logo_flowable else "", Paragraph(f"<b>{title_text.upper()}</b><br/><font size=8 color='#64748B'>{entity_name}</font>", title_style)]
    ]
    t_header = Table(header_table_data, colWidths=[70, 470])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_header)
    story.append(Spacer(1, 15))

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
            padding: 1.25rem;
            border-radius: 6px;
            border: 1px solid #E2E8F0;
            border-top: 3px solid #0F172A;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }

        .ticket-pass {
            background: #FFFFFF;
            border: 2px dashed #0F172A;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }

        .form-label {
            font-weight: 700;
            font-size: 0.85rem;
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
        "Venue Operations & Analytics Console",
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

    tab_book, tab_tickets, tab_my_passes = st.tabs(["🏛️ Commercial Venue Reservations", "🎟️ Box Office Event Tickets", "🎫 View My Issued Ticket Passes"])

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
                <div class="exec-card" style="border-top-color:{sel_venue['brand_color'] or '#D97706'}; margin-bottom:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2 style="margin:0; font-family:'Playfair Display', serif;">{sel_venue['name']}</h2>
                        <img src="{sel_venue['logo_url'] or DEFAULT_LOGO}" style="background:white; padding:4px; border:1px solid #E2E8F0; border-radius:4px; height: 50px;">
                    </div>
                    <hr style="margin:1rem 0; border:0; border-top:1px solid #E2E8F0;">
                    <p style="margin:0; font-size:0.95rem; color:#334155;">
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
                                        c_name, c_email, v_data['items'], v_data['total'], v_info['bank_details'],
                                        logo_b64=v_info['logo_url']
                                    )
                                    vendor_pdf_dict[v_info['business_name']] = (v_inv_id, v_pdf)

                                conn.commit()
                                st.success(f"Reservation Request #{b_id} Generated Successfully!")
                                
                                venue_pdf_bytes = generate_in_memory_pdf_bytes(
                                    f"Official Tax Invoice — {sel_venue['name']}",
                                    b_id, created_date, sel_venue['name'], sel_venue['tax_id'],
                                    c_name, c_email,
                                    [{"item_name": f"Venue Hire ({sel_sp_name})", "qty": booking_days, "unit_price": sel_space['daily_rate'], "subtotal": space_cost}],
                                    space_cost, sel_venue['bank_details'],
                                    logo_b64=sel_venue['logo_url']
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
                
                # Dynamic flyer visual generation with Light Theme & Background Image Support
                flyer_b64 = generate_branded_flyer(
                    venue_name=ev['venue_name'],
                    event_title=ev['title'],
                    event_date=ev['date'],
                    price=ev['price'],
                    comments=ev['description'],
                    uploaded_bg_file=ev['flyer_url'] if ev['flyer_url'] and os.path.exists(ev['flyer_url']) else None
                )
                col1.image(flyer_b64, use_container_width=True)
                
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
                        st.markdown("<div class='form-label'>Payment Channel</div>", unsafe_allow_html=True)
                        t_pay = st.selectbox("", ["Orange Money", "eWallet", "Card Payment", "Pay2Cell"], label_visibility="collapsed", key=f"tkt_pay_{ev['event_id']}")

                    if st.form_submit_button("PURCHASE TICKET PASSES", type="primary", use_container_width=True):
                        if t_buyer and t_email:
                            t_id = f"TKT-{int(datetime.datetime.now().timestamp())}"
                            v_hash = hashlib.sha256(f"{t_id}{ev['event_id']}{t_email}".encode()).hexdigest()[:16]
                            total_paid = ev['price'] * t_qty
                            
                            conn.execute("""INSERT INTO tickets 
                                (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE / VALID')""",
                                (t_id, v_hash, ev['event_id'], ev['title'], ev['venue_id'], ev['venue_name'], v['logo_url'] if v else "", t_buyer, t_email, t_qty, total_paid, t_pay))
                            conn.commit()
                            st.success(f"🎟️ Ticket Pass Issued Successfully! Ref ID: {t_id}")
                        else:
                            st.error("Please fill in attendee name and email address.")
                st.divider()
        conn.close()

    with tab_my_passes:
        st.markdown("<h3 style='font-family: Playfair Display, serif;'>Lookup & Display My Ticket Passes</h3>", unsafe_allow_html=True)
        search_email = st.text_input("Enter Email Address Used During Purchase:", key="lookup_email_pass")
        if search_email:
            conn = get_db_connection()
            my_tkts = conn.execute("SELECT * FROM tickets WHERE email = ?", (search_email,)).fetchall()
            if not my_tkts:
                st.info("No active admission passes located for this email.")
            else:
                for tkt in my_tkts:
                    qr_b64 = generate_qr_code_base64(f"TICKET_ID:{tkt['ticket_id']}|HASH:{tkt['verification_hash']}")
                    ev = conn.execute("SELECT * FROM events WHERE event_id = ?", (tkt['event_id'],)).fetchone()
                    
                    # Light aesthetic layout ticket card design with background uploaded flyer support
                    bg_style = f"background-image: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)), url('{ev['flyer_url']}'); background-size: cover;" if (ev and ev['flyer_url']) else "background: #FFFFFF;"
                    
                    st.markdown(f"""
                        <div class="ticket-pass" style="{bg_style} border-color: #D97706; margin-bottom: 20px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3 style="margin:0; font-family:'Playfair Display', serif; color:#0F172A; font-size: 1.6rem;">{tkt['event_title']}</h3>
                                <span style="background:#10B981; color:white; padding:4px 12px; border-radius:12px; font-weight:bold; font-size:0.8rem;">{tkt['status']}</span>
                            </div>
                            <hr style="margin: 0.8rem 0; border-top: 1px dashed #CBD5E1;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div style="text-align:left; color:#1E293B;">
                                    <p style="margin:2px 0; font-size:1.05rem;"><b>ATTENDEE:</b> {tkt['buyer']}</p>
                                    <p style="margin:2px 0; font-size:1.05rem;"><b>VENUE:</b> {tkt['venue_name']}</p>
                                    <p style="margin:2px 0; font-size:1.05rem;"><b>PASS QUANTITY:</b> {tkt['qty']} Person(s)</p>
                                    <p style="margin:2px 0; font-size:1.05rem;"><b>TICKET ID:</b> <code style="font-size:1.1rem; color:#D97706;">{tkt['ticket_id']}</code></p>
                                </div>
                                <div>
                                    <img src="{qr_b64}" style="width:130px; border:2px solid #0F172A; border-radius:6px; padding:4px; background:white;">
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            conn.close()
