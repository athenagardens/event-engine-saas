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
    
    # Public Events (Supports both Venue & Vendor/Supporter Hosted Events)
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY, host_type TEXT DEFAULT 'VENUE', host_id TEXT, host_name TEXT,
        venue_id TEXT, venue_name TEXT, space_name TEXT, title TEXT, date TEXT,
        price REAL, description TEXT, flyer_url TEXT, video_url TEXT, is_active INTEGER DEFAULT 1
    )''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------
# 2. UTILITIES: SECURITY, IMAGES, MEDIA & PDF
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

def process_compressed_image_upload(uploaded_file, fallback_url="", max_dim=400):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail((max_dim, max_dim))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75, optimize=True)
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception:
            return fallback_url
    return fallback_url

def process_media_file_upload(uploaded_file):
    if uploaded_file is not None:
        try:
            bytes_data = uploaded_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode()
            mime_type = uploaded_file.type
            return f"data:{mime_type};base64,{b64_str}"
        except Exception:
            return ""
    return ""

def generate_branded_flyer(venue_name, event_title, event_date, price, start_time="18:00", end_time="23:00", comments="", uploaded_bg_file=None, brand_color="#0F172A"):
    width, height = 400, 500

    if uploaded_bg_file is not None:
        try:
            bg_img = Image.open(uploaded_bg_file).convert("RGB")
            bg_img.thumbnail((width, height))
            
            overlay = Image.new("RGBA", (width, height), (15, 23, 42, 215))
            img = bg_img.convert("RGBA").resize((width, height))
            img = Image.alpha_composite(img, overlay).convert("RGB")
        except Exception:
            img = Image.new("RGB", (width, height), color="#0F172A")
    else:
        img = Image.new("RGB", (width, height), color="#0F172A")

    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(0, 0), (width, 60)], fill=brand_color)
    draw.rectangle([(8, 8), (width-8, height-8)], outline="#D97706", width=2)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 18)
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        font_sub = ImageFont.truetype("arialbd.ttf", 13)
        font_body = ImageFont.truetype("arial.ttf", 11)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except IOError:
        font_header = font_title = font_sub = font_body = font_small = ImageFont.load_default()
        
    draw.text((width//2, 30), venue_name.upper(), fill="#FFFFFF", font=font_header, anchor="mm")
    draw.text((width//2, 90), event_title, fill="#F59E0B", font=font_title, anchor="mm")
    draw.line([(40, 115), (width-40, 115)], fill="#CBD5E1", width=1)
    
    draw.text((width//2, 140), f"DATE: {event_date}", fill="#FFFFFF", font=font_sub, anchor="mm")
    draw.text((width//2, 165), f"TIME: {start_time} - {end_time}", fill="#38BDF8", font=font_sub, anchor="mm")
    draw.text((width//2, 210), f"ADMISSION: BWP {price:,.2f}", fill="#10B981", font=font_title, anchor="mm")
    
    if comments:
        draw.rectangle([(30, 240), (width-30, 430)], fill=(0, 0, 0, 150), outline="#D97706", width=1)
        draw.text((width//2, 260), "— EVENT HIGHLIGHTS —", fill="#D97706", font=font_sub, anchor="mm")
        
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
            
        y_offset = 290
        for line in lines[:5]:
            draw.text((width//2, y_offset), line, fill="#F8FAFC", font=font_body, anchor="mm")
            y_offset += 20

    draw.text((width//2, 475), "OFFICIAL ADMISSION PASS — EXECUTIVE EVENT HUB", fill="#94A3B8", font=font_small, anchor="mm")
    
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    b64_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64_str}"

def render_event_promo_video_canvas(venue_name, event_title, event_date, time_range, highlights, price, booking_url):
    html_code = f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border: 3px solid #D97706; border-radius: 12px; padding: 25px; text-align: center; color: white; font-family: sans-serif; max-width: 450px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        <div style="font-size: 0.8rem; letter-spacing: 0.15em; color: #94A3B8; text-transform: uppercase; margin-bottom: 5px;">📍 LOCATION / HOST</div>
        <div style="font-size: 1.4rem; font-weight: bold; color: #FFFFFF; text-transform: uppercase;">{venue_name}</div>
        <hr style="border: 0; border-top: 1px solid #334155; margin: 15px 0;">
        <div style="background: rgba(217, 119, 6, 0.15); border-radius: 8px; padding: 10px; margin-bottom: 15px;">
            <div style="font-size: 1.6rem; font-weight: bold; color: #F59E0B;">{event_title}</div>
            <div style="font-size: 0.95rem; color: #38BDF8; font-weight: 600; margin-top: 5px;">🗓️ {event_date} | ⏰ {time_range}</div>
        </div>
        <div style="text-align: left; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 6px; font-size: 0.85rem; line-height: 1.5; color: #CBD5E1; margin-bottom: 15px;">
            <b style="color: #D97706;">✨ EVENT HIGHLIGHTS:</b><br>{highlights}
        </div>
        <div style="font-size: 1.2rem; font-weight: bold; color: #10B981; margin-bottom: 15px;">ADMISSION: BWP {price:,.2f}</div>
        <a href="{booking_url}" target="_blank" style="display: block; background: #D97706; color: white; text-decoration: none; padding: 12px; font-weight: bold; border-radius: 6px; letter-spacing: 0.05em; box-shadow: 0 4px 10px rgba(217,119,6,0.4);">👉 CLICK HERE TO BOOK TICKETS ONLINE</a>
    </div>
    """
    return html_code

def generate_qr_code_base64(data_string):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def generate_in_memory_pdf_bytes(title_text, inv_id, created_at, entity_name, tax_id, client_name, client_email, items_list, total_amount, bank_details, logo_b64=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), alignment=0)
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#1E293B'))
    header_cell_style = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, fontName='Helvetica-Bold')

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
            border-radius: 4px;
            border: 1px solid #E2E8F0;
            border-top: 3px solid #0F172A;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }

        .metric-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #D97706;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }

        .ticket-pass {
            background: #FFFFFF;
            border: 2px dashed #0F172A;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
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
                <div class="exec-card" style="border-top-color:{sel_venue['brand_color']}; margin-bottom:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2 style="margin:0; font-family:'Playfair Display', serif;">{sel_venue['name']}</h2>
                        <img src="{sel_venue['logo_url'] or DEFAULT_LOGO}" style="background:white; padding:4px; border:1px solid #E2E8F0; border-radius:4px; height: 50px;">
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
                                    space_cost, sel_venue['bank_details'], logo_b64=sel_venue['logo_url']
                                )
                                
                                st.download_button(
                                    f"📄 Download Venue Tax Invoice (BWP {space_cost:,.2f})",
                                    data=venue_pdf_bytes,
                                    file_name=f"Invoice_{b_id}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )

                                for v_name, (v_inv_id, v_pdf_b) in vendor_pdf_dict.items():
                                    st.download_button(
                                        f"📦 Download Ancillary Vendor Invoice — {v_name}",
                                        data=v_pdf_b,
                                        file_name=f"VendorInvoice_{v_inv_id}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                            else:
                                st.error("Please fill out all mandatory customer detail fields.")
        conn.close()

    with tab_tickets:
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events WHERE is_active = 1").fetchall()
        
        if not events:
            st.info("No public events currently published on the network.")
        else:
            for ev in events:
                with st.container():
                    st.markdown(f"<div class='exec-card'>", unsafe_allow_html=True)
                    ec1, ec2 = st.columns([1, 2])
                    if ev['flyer_url']:
                        ec1.image(ev['flyer_url'], use_container_width=True)
                    ec2.markdown(f"### {ev['title']}")
                    ec2.markdown(f"**Host / Venue:** {ev['venue_name']} ({ev['space_name'] or 'Main Arena'})")
                    ec2.markdown(f"**Date:** {ev['date']} | **Price:** BWP {ev['price']:,.2f}")
                    if ev['description']: ec2.caption(ev['description'])

                    with ec2.form(f"buy_ticket_form_{ev['event_id']}"):
                        tb1, tb2, tb3 = st.columns(3)
                        b_buyer = tb1.text_input("Full Name", key=f"tb_buyer_{ev['event_id']}")
                        b_email = tb2.text_input("Email", key=f"tb_email_{ev['event_id']}")
                        b_qty = tb3.number_input("Pass Quantity", min_value=1, value=1, key=f"tb_qty_{ev['event_id']}")
                        
                        if st.form_submit_button("PURCHASE TICKET PASSES", use_container_width=True):
                            if b_buyer and b_email:
                                t_id = f"TCK-{int(datetime.datetime.now().timestamp())}"
                                v_hash = hashlib.sha256(f"{t_id}:{b_email}:{ev['event_id']}".encode()).hexdigest()[:16].upper()
                                total_paid = b_qty * ev['price']

                                conn.execute("""INSERT INTO tickets 
                                    (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Online Checkout', 'Active / Valid')""",
                                    (t_id, v_hash, ev['event_id'], ev['title'], ev['venue_id'], ev['venue_name'], "", b_buyer, b_email, b_qty, total_paid))
                                conn.commit()

                                st.success(f"Passes Issued! Ticket Reference ID: {t_id}")
                                qr_b64 = generate_qr_code_base64(f"TICKET:{t_id}:{v_hash}")
                                st.image(qr_b64, caption=f"Verification Hash: {v_hash}", width=180)
                            else:
                                st.error("Please enter buyer details.")
                    st.markdown("</div>", unsafe_allow_html=True)
        conn.close()

    with tab_my_passes:
        st.markdown("<h3 style='font-family: Playfair Display, serif;'>Retrieve Admission Passes</h3>", unsafe_allow_html=True)
        lookup_email = st.text_input("Enter Email Address linked to Ticket Purchase")
        if lookup_email:
            conn = get_db_connection()
            user_tickets = conn.execute("SELECT * FROM tickets WHERE email = ?", (lookup_email,)).fetchall()
            if not user_tickets:
                st.warning("No admission passes found for this email address.")
            else:
                for t in user_tickets:
                    qr_b64 = generate_qr_code_base64(f"TICKET:{t['ticket_id']}:{t['verification_hash']}")
                    st.markdown(f"""
                    <div class='ticket-pass'>
                        <h3 style='margin:0; color:#0F172A;'>{t['event_title']}</h3>
                        <p style='margin:5px 0; font-size:0.85rem;'><b>VENUE:</b> {t['venue_name']} | <b>PASS HOLDER:</b> {t['buyer']} ({t['qty']} Person(s))</p>
                        <p style='margin:5px 0; font-size:0.8rem; color:#D97706;'>STATUS: <b>{t['status']}</b></p>
                        <img src="{qr_b64}" style="width:140px; margin:10px auto;">
                        <p style='font-size:0.75rem; color:#64748B;'>REF: {t['ticket_id']} | HASH: {t['verification_hash']}</p>
                    </div>
                    <br>
                    """, unsafe_allow_html=True)
            conn.close()

# ---------------------------------------------------------
# 6. MODULE 2: VENUE OPERATIONS & ANALYTICS CONSOLE
# ---------------------------------------------------------
elif user_role == "Venue Operations & Analytics Console":
    st.markdown("<div class='exec-title'>Venue Operations & Analytics Console</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Sub-Space Control, Vendor Approvals & Event Publishing</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "VENUE":
        st.subheader("Venue Workspace Authentication")
        conn = get_db_connection()
        venues = conn.execute("SELECT * FROM venues").fetchall()
        conn.close()

        v_options = {v['name']: v['venue_id'] for v in venues} if venues else {}
        auth_col1, auth_col2 = st.columns(2)
        
        with auth_col1:
            st.markdown("#### Login to Existing Workspace")
            l_email = st.text_input("Workspace Email", key="v_login_email")
            l_pass = st.text_input("Password", type="password", key="v_login_pass")
            if st.button("AUTHENTICATE WORKSPACE", use_container_width=True):
                conn = get_db_connection()
                usr = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'VENUE'", (l_email,)).fetchone()
                conn.close()
                if usr and verify_pw(l_pass, usr['password_hash'], usr['salt']):
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = usr['email']
                    st.session_state["user_role"] = "VENUE"
                    st.session_state["tenant_id"] = usr['tenant_id']
                    st.success("Authenticated.")
                    st.rerun()
                else:
                    st.error("Invalid credentials or unauthorized role.")

        with auth_col2:
            st.markdown("#### Register New Venue Property")
            r_name = st.text_input("Venue Facility Name")
            r_email = st.text_input("Admin Email")
            r_pass = st.text_input("Set Password", type="password")
            r_phone = st.text_input("Phone Number")
            r_whatsapp = st.text_input("WhatsApp Line")
            r_address = st.text_input("Physical Address")
            r_cap = st.number_input("Max Licensed Capacity", min_value=10, value=500)
            
            if st.button("REGISTER VENUE FACILITY", use_container_width=True):
                if r_name and r_email and r_pass:
                    v_id = f"VEN-{int(datetime.datetime.now().timestamp())}"
                    p_hash, salt = hash_pw(r_pass)
                    conn = get_db_connection()
                    try:
                        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, 'VENUE', ?)", (f"U-{v_id}", r_email, p_hash, salt, v_id))
                        conn.execute("INSERT INTO venues (venue_id, name, type, email, phone, whatsapp_no, address, max_capacity, brand_color) VALUES (?, ?, 'Commercial Venue', ?, ?, ?, ?, ?, '#0F172A')",
                                     (v_id, r_name, r_email, r_phone, r_whatsapp, r_address, r_cap))
                        conn.commit()
                        st.success("Venue Workspace Registered successfully. Please log in.")
                    except sqlite3.IntegrityError:
                        st.error("User email already exists.")
                    finally:
                        conn.close()
    else:
        v_id = st.session_state["tenant_id"]
        conn = get_db_connection()
        venue = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (v_id,)).fetchone()

        v_tab1, v_tab2, v_tab3, v_tab4, v_tab5 = st.tabs(["📊 KPI Dashboard", "🚪 Sub-Space Mgmt", "🤝 Vendor Approvals", "📢 Event Publishing", "📋 Booking Ledger"])

        with v_tab1:
            st.markdown(f"### Management Dashboard — {venue['name']}")
            bookings = conn.execute("SELECT * FROM bookings WHERE venue_id = ?", (v_id,)).fetchall()
            total_rev = sum(b['venue_cost'] for b in bookings)
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"<div class='metric-card'><h4>TOTAL VENUE REVENUE</h4><h2>BWP {total_rev:,.2f}</h2></div>", unsafe_allow_html=True)
            m2.markdown(f"<div class='metric-card'><h4>RESERVATIONS</h4><h2>{len(bookings)}</h2></div>", unsafe_allow_html=True)
            m3.markdown(f"<div class='metric-card'><h4>MAX CAPACITY</h4><h2>{venue['max_capacity']:,}</h2></div>", unsafe_allow_html=True)

        with v_tab2:
            st.markdown("### Manage Facility Sub-Spaces")
            with st.form("add_space_form"):
                s_name = st.text_input("Sub-Space Name (e.g. Main Hall, Garden Suite)")
                s_cap = st.number_input("Space Capacity", min_value=1, value=100)
                s_rate = st.number_input("Daily Tariff (BWP)", min_value=0.0, value=1500.0)
                s_img = st.file_uploader("Upload Sub-Space Photo", type=["jpg", "png", "jpeg"])
                
                if st.form_submit_button("ADD SUB-SPACE ASSET"):
                    img_url = process_compressed_image_upload(s_img, fallback_url=SPACE_PRESETS[0])
                    conn.execute("INSERT INTO spaces (venue_id, name, capacity, daily_rate, image_url) VALUES (?, ?, ?, ?, ?)",
                                 (v_id, s_name, s_cap, s_rate, img_url))
                    conn.commit()
                    st.success("Sub-Space added.")
                    st.rerun()

            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (v_id,)).fetchall()
            for sp in spaces:
                st.write(f"• **{sp['name']}** — Cap: {sp['capacity']} | Daily: BWP {sp['daily_rate']:,.2f}")

        with v_tab3:
            st.markdown("### Approved Ancillary Supporters / Vendors")
            supporters = conn.execute("SELECT * FROM supporters").fetchall()
            curr_approved = json.loads(venue['approved_supporter_ids'] or "[]")

            new_approved = []
            for sup in supporters:
                checked = st.checkbox(f"{sup['business_name']} ({sup['category']})", value=(sup['supporter_id'] in curr_approved))
                if checked:
                    new_approved.append(sup['supporter_id'])
            
            if st.button("SAVE APPROVED VENDORS"):
                conn.execute("UPDATE venues SET approved_supporter_ids = ? WHERE venue_id = ?", (json.dumps(new_approved), v_id))
                conn.commit()
                st.success("Approved vendor list updated.")

        with v_tab4:
            st.markdown("### Publish & Promote Public Events")
            with st.form("pub_event_form"):
                e_title = st.text_input("Event Title")
                e_date = st.date_input("Event Date")
                e_price = st.number_input("Admission Price (BWP)", min_value=0.0, value=100.0)
                e_desc = st.text_area("Event Highlights / Description")
                e_bg = st.file_uploader("Flyer Background Image", type=["jpg", "png"])
                
                if st.form_submit_button("PUBLISH EVENT TO MARKETPLACE"):
                    e_id = f"EVT-{int(datetime.datetime.now().timestamp())}"
                    flyer_url = generate_branded_flyer(venue['name'], e_title, str(e_date), e_price, comments=e_desc, uploaded_bg_file=e_bg)
                    
                    conn.execute("""INSERT INTO events 
                        (event_id, host_type, host_id, host_name, venue_id, venue_name, space_name, title, date, price, description, flyer_url)
                        VALUES (?, 'VENUE', ?, ?, ?, ?, 'Main Area', ?, ?, ?, ?, ?)""",
                        (e_id, v_id, venue['name'], v_id, venue['name'], e_title, str(e_date), e_price, e_desc, flyer_url))
                    conn.commit()
                    st.success("Event Published Successfully!")

        with v_tab5:
            st.markdown("### Reservation & Booking Ledger")
            b_list = conn.execute("SELECT * FROM bookings WHERE venue_id = ?", (v_id,)).fetchall()
            for b in b_list:
                st.write(f"Ref: **{b['booking_id']}** | Client: {b['customer_name']} | Date: {b['booking_date']} | Status: {b['status']} | Total: BWP {b['venue_cost']:,.2f}")

        conn.close()

# ---------------------------------------------------------
# 7. MODULE 3: VENDOR PORTAL & SERVICE FULFILLMENT
# ---------------------------------------------------------
elif user_role == "Vendor Portal & Service Fulfillment":
    st.markdown("<div class='exec-title'>Vendor Portal & Service Fulfillment</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Service Catalog Templates & Order Processing</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "VENDOR":
        st.subheader("Vendor Workspace Authentication")
        v_col1, v_col2 = st.columns(2)
        
        with v_col1:
            st.markdown("#### Login to Vendor Portal")
            vl_email = st.text_input("Vendor Email")
            vl_pass = st.text_input("Password", type="password")
            if st.button("AUTHENTICATE VENDOR", use_container_width=True):
                conn = get_db_connection()
                usr = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'VENDOR'", (vl_email,)).fetchone()
                conn.close()
                if usr and verify_pw(vl_pass, usr['password_hash'], usr['salt']):
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = usr['email']
                    st.session_state["user_role"] = "VENDOR"
                    st.session_state["tenant_id"] = usr['tenant_id']
                    st.success("Authenticated.")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with v_col2:
            st.markdown("#### Register Vendor Service Provider")
            vr_name = st.text_input("Business Name")
            vr_cat = st.selectbox("Category", ["Catering & Bar", "Sound & Lighting", "Decor & Design", "Security", "Photography/Media"])
            vr_email = st.text_input("Business Email")
            vr_pass = st.text_input("Password", type="password")
            vr_phone = st.text_input("Phone")
            vr_bank = st.text_area("Bank Details")

            if st.button("REGISTER VENDOR BUSINESS", use_container_width=True):
                if vr_name and vr_email and vr_pass:
                    s_id = f"SUP-{int(datetime.datetime.now().timestamp())}"
                    p_hash, salt = hash_pw(vr_pass)
                    conn = get_db_connection()
                    try:
                        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, 'VENDOR', ?)", (f"U-{s_id}", vr_email, p_hash, salt, s_id))
                        conn.execute("INSERT INTO supporters (supporter_id, business_name, category, contact_person, email, phone, bank_details) VALUES (?, ?, ?, 'Manager', ?, ?, ?)",
                                     (s_id, vr_name, vr_cat, vr_email, vr_phone, vr_bank))
                        conn.commit()
                        st.success("Vendor Business Registered successfully. Please log in.")
                    except sqlite3.IntegrityError:
                        st.error("Email already exists.")
                    finally:
                        conn.close()
    else:
        s_id = st.session_state["tenant_id"]
        conn = get_db_connection()
        vendor = conn.execute("SELECT * FROM supporters WHERE supporter_id = ?", (s_id,)).fetchone()

        st.markdown(f"### Vendor Dashboard — {vendor['business_name']}")
        vp_tab1, vp_tab2 = st.tabs(["📦 Service Catalog Templates", "📄 Received Orders & Invoices"])

        with vp_tab1:
            st.markdown("#### Add Service Package Template")
            with st.form("add_template_form"):
                t_name = st.text_input("Item / Service Name")
                t_unit = st.selectbox("Billing Unit", ["Person / Head", "Hour", "Day", "Fixed Package"])
                t_price = st.number_input("Unit Price (BWP)", min_value=0.0, value=250.0)
                t_desc = st.text_area("Package Scope & Details")
                t_img = st.file_uploader("Upload Image", type=["jpg", "png"])

                if st.form_submit_button("SAVE SERVICE TEMPLATE"):
                    img_url = process_compressed_image_upload(t_img)
                    conn.execute("INSERT INTO vendor_templates (supporter_id, item_name, description, unit_type, unit_price, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                                 (s_id, t_name, t_desc, t_unit, t_price, img_url))
                    conn.commit()
                    st.success("Template Saved.")
                    st.rerun()

            templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ?", (s_id,)).fetchall()
            for t in templates:
                st.write(f"• **{t['item_name']}** — BWP {t['unit_price']:,.2f} / {t['unit_type']}")

        with vp_tab2:
            st.markdown("#### Vendor Invoices & Orders")
            invoices = conn.execute("SELECT * FROM vendor_invoices WHERE supporter_id = ?", (s_id,)).fetchall()
            for inv in invoices:
                st.write(f"Invoice Ref: **{inv['vendor_invoice_id']}** | Venue: {inv['venue_name']} | Client: {inv['customer_name']} | Total: BWP {inv['total_amount']:,.2f} | Status: {inv['status']}")

        conn.close()

# ---------------------------------------------------------
# 8. MODULE 4: ACCESS CONTROL & VERIFICATION SUITE
# ---------------------------------------------------------
elif user_role == "Access Control & Verification Suite":
    st.markdown("<div class='exec-title'>Access Control & Verification Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Real-Time QR Ticket Scanner & Entry Gate Validation</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    scan_input = st.text_input("Scan QR Code Payload or Enter Ticket Verification Hash")
    if scan_input:
        conn = get_db_connection()
        ticket = None
        if scan_input.startswith("TICKET:"):
            parts = scan_input.split(":")
            if len(parts) >= 3:
                t_id, v_hash = parts[1], parts[2]
                ticket = conn.execute("SELECT * FROM tickets WHERE ticket_id = ? AND verification_hash = ?", (t_id, v_hash)).fetchone()
        else:
            ticket = conn.execute("SELECT * FROM tickets WHERE ticket_id = ? OR verification_hash = ?", (scan_input, scan_input)).fetchone()

        if not ticket:
            st.error("❌ INVALID TICKET PASS — NOT FOUND IN ENTERPRISE LEDGER")
        else:
            if ticket['status'] == 'USED / ADMITTED':
                st.warning(f"⚠️ ALREADY USED — Admitted at {ticket['scanned_at']}")
            elif ticket['status'] != 'Active / Valid':
                st.error(f"❌ INVALID STATUS — {ticket['status']}")
            else:
                st.success(f"✅ VALID TICKET PASS — ADMIT {ticket['qty']} GUEST(S)")
                st.markdown(f"""
                * **EVENT:** {ticket['event_title']}
                * **BUYER:** {ticket['buyer']} ({ticket['email']})
                * **VENUE:** {ticket['venue_name']}
                * **QUANTITY:** {ticket['qty']} Person(s)
                """)
                if st.button("CONFIRM GATE ENTRY / ADMIT GUESTS", type="primary"):
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn.execute("UPDATE tickets SET status = 'USED / ADMITTED', scanned_at = ? WHERE ticket_id = ?", (now_str, ticket['ticket_id']))
                    conn.commit()
                    st.success("Pass Status Updated to USED / ADMITTED.")
                    st.rerun()
        conn.close()

# ---------------------------------------------------------
# 9. MODULE 5: EXECUTIVE MASTER LEDGER & AUDIT SUITE
# ---------------------------------------------------------
elif user_role == "Executive Master Ledger & Audit Suite":
    st.markdown("<div class='exec-title'>Executive Master Ledger & Audit Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>System-Wide Consolidated Financial & Operational Audit Log</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    conn = get_db_connection()
    all_bookings = conn.execute("SELECT * FROM bookings").fetchall()
    all_v_inv = conn.execute("SELECT * FROM vendor_invoices").fetchall()
    all_tickets = conn.execute("SELECT * FROM tickets").fetchall()
    conn.close()

    total_venue_rev = sum(b['venue_cost'] for b in all_bookings)
    total_vendor_rev = sum(vi['total_amount'] for vi in all_v_inv)
    total_ticket_rev = sum(t['total_paid'] for t in all_tickets)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h4>TOTAL VENUE BOOKINGS</h4><h2>BWP {total_venue_rev:,.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h4>TOTAL VENDOR SERVICES</h4><h2>BWP {total_vendor_rev:,.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h4>TOTAL TICKET SALES</h4><h2>BWP {total_ticket_rev:,.2f}</h2></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Consolidated System Activity Log")
    st.dataframe([dict(b) for b in all_bookings], use_container_width=True)
