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
                                    key="dl_venue_inv"
                                )
                                
                                for v_biz_name, (v_id, v_bytes) in vendor_pdf_dict.items():
                                    st.download_button(
                                        f"📦 Download Ancillary Invoice — {v_biz_name}",
                                        data=v_bytes,
                                        file_name=f"Vendor_Invoice_{v_id}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_v_inv_{v_id}"
                                    )
                            else:
                                st.error("Please complete all required billing details.")
        conn.close()

    with tab_tickets:
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events WHERE is_active = 1").fetchall()
        
        if not events:
            st.info("No active box office public events open for booking.")
        else:
            for ev in events:
                with st.container():
                    st.markdown(f"""
                        <div class="exec-card" style="border-top-color:#D97706;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <h3 style="margin:0; font-family:'Playfair Display', serif;">{ev['title']}</h3>
                                    <p style="margin:0; color:#64748B; font-size:0.85rem;"><b>HOST/LOCATION:</b> {ev['venue_name']} | <b>SPACE:</b> {ev['space_name']}</p>
                                </div>
                                <span style="background:#10B981; color:white; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:0.85rem;">
                                    BWP {ev['price']:,.2f}
                                </span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    ec1, ec2 = st.columns([1, 2])
                    with ec1:
                        if ev['flyer_url']:
                            st.image(ev['flyer_url'], use_container_width=True)
                    with ec2:
                        st.write(ev['description'])
                        st.write(f"🗓️ **Scheduled Event Date:** {ev['date']}")
                        
                        if ev['video_url']:
                            with st.expander("📺 View Promotional Video / Teaser Canvas"):
                                if ev['video_url'].startswith("data:video"):
                                    st.video(ev['video_url'])
                                else:
                                    st.markdown(render_event_promo_video_canvas(
                                        ev['venue_name'], ev['title'], ev['date'], "18:00 - LATE", ev['description'], ev['price'], "#"
                                    ), unsafe_allow_html=True)
                        
                        with st.expander(f"🎟️ Purchase Admission Ticket for {ev['title']}"):
                            with st.form(f"ticket_form_{ev['event_id']}"):
                                t_buyer = st.text_input("Attendee Full Name", key=f"tb_name_{ev['event_id']}")
                                t_email = st.text_input("Attendee Email Address", key=f"tb_email_{ev['event_id']}")
                                t_qty = st.number_input("Number of Admission Tickets", min_value=1, value=1, key=f"tb_qty_{ev['event_id']}")
                                t_pay = st.selectbox("Payment Channel", ["eWallet", "Orange Money", "Pay2Cell", "Credit / Debit Card"], key=f"tb_pay_{ev['event_id']}")
                                
                                total_t_cost = ev['price'] * t_qty
                                st.markdown(f"**Total Amount Payable:** BWP {total_t_cost:,.2f}")
                                
                                if st.form_submit_button("CONFIRM TICKET PURCHASE", use_container_width=True):
                                    if t_buyer and t_email:
                                        t_id = f"TCK-{int(datetime.datetime.now().timestamp())}"
                                        v_hash = hashlib.sha256(f"{t_id}:{ev['event_id']}:{t_email}".encode()).hexdigest()[:16].upper()
                                        
                                        conn.execute("""INSERT INTO tickets 
                                            (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status, created_at)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed / Valid', ?)""",
                                            (t_id, v_hash, ev['event_id'], ev['title'], ev['venue_id'], ev['venue_name'], "", t_buyer, t_email, t_qty, total_t_cost, t_pay, str(datetime.date.today())))
                                        conn.commit()
                                        st.success(f"Ticket Pass #{t_id} Issued Successfully!")
                                        st.info(f"Verification Key: {v_hash}")
                                    else:
                                        st.error("Please specify attendee contact details.")
                st.divider()
        conn.close()

    with tab_my_passes:
        st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>Look Up & Access Digital Entry Passes</h3>", unsafe_allow_html=True)
        search_email = st.text_input("Enter Email Address used for Booking:", key="pass_search_email")
        if search_email:
            conn = get_db_connection()
            user_tickets = conn.execute("SELECT * FROM tickets WHERE email = ?", (search_email,)).fetchall()
            conn.close()
            
            if not user_tickets:
                st.warning("No admission passes registered under this email address.")
            else:
                for tck in user_tickets:
                    qr_b64 = generate_qr_code_base64(f"TICKET_ID:{tck['ticket_id']}|HASH:{tck['verification_hash']}")
                    
                    st.markdown(f"""
                        <div class="ticket-pass">
                            <h2 style="margin:0; font-family:'Playfair Display', serif; color:#0F172A;">{tck['event_title']}</h2>
                            <p style="margin:5px 0; color:#D97706; font-weight:bold;">{tck['venue_name']}</p>
                            <p style="margin:0; font-size:0.85rem; color:#475569;"><b>PASS HOLDER:</b> {tck['buyer']} ({tck['qty']} Person(s))</p>
                            <p style="margin:0; font-size:0.85rem; color:#475569;"><b>TICKET ID:</b> {tck['ticket_id']} | <b>STATUS:</b> <span style="color:green;">{tck['status']}</span></p>
                            <br>
                            <img src="{qr_b64}" width="150" style="border:1px solid #CBD5E1; padding:5px; border-radius:4px;">
                            <p style="font-size:0.75rem; color:#64748B; margin-top:5px;"><b>VERIFICATION HASH:</b> {tck['verification_hash']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. MODULE 2: VENUE OPERATIONS & ANALYTICS CONSOLE
# ---------------------------------------------------------
elif user_role == "Venue Operations & Analytics Console":
    st.markdown("<div class='exec-title'>Venue Operations & Analytics Console</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Commercial Facility Management & Event Hosting Workspace</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "VENUE":
        st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>Venue Operator Workspace Portal Login</h3>", unsafe_allow_html=True)
        
        tab_v_login, tab_v_reg = st.tabs(["🔒 Secure Workspace Login", "🏛️ Register New Venue Facility"])
        
        with tab_v_login:
            with st.form("venue_login_form"):
                v_login_email = st.text_input("Registered Executive Email")
                v_login_pw = st.text_input("Password", type="password")
                if st.form_submit_button("AUTHENTICATE WORKSPACE", use_container_width=True):
                    conn = get_db_connection()
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'VENUE'", (v_login_email,)).fetchone()
                    conn.close()
                    if user and verify_pw(v_login_pw, user['password_hash'], user['salt']):
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = user['email']
                        st.session_state["user_role"] = "VENUE"
                        st.session_state["tenant_id"] = user['tenant_id']
                        st.success("Authenticated successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid operator credentials.")
                        
        with tab_v_reg:
            with st.form("venue_reg_form"):
                v_reg_id = f"VEN-{int(datetime.datetime.now().timestamp())}"
                v_reg_name = st.text_input("Facility Name")
                v_reg_type = st.selectbox("Facility Type", ["Convention Center", "Luxury Hotel & Resort", "Private Event Garden", "Executive Conference Center"])
                v_reg_email = st.text_input("Administrative Contact Email")
                v_reg_pw = st.text_input("Workspace Security Password", type="password")
                v_reg_phone = st.text_input("Phone Number")
                v_reg_wa = st.text_input("WhatsApp Support Line")
                v_reg_addr = st.text_area("Physical Property Address")
                v_reg_cap = st.number_input("Maximum Guest Capacity", min_value=10, value=500)
                v_reg_tax = st.text_input("CIPA / Tax Registration ID")
                v_reg_bank = st.text_area("Official Settlement Bank Details")
                v_reg_color = st.color_picker("Brand Color Palette Accent", "#0F172A")
                
                if st.form_submit_button("REGISTER VENUE FACILITY", use_container_width=True):
                    if v_reg_name and v_reg_email and v_reg_pw:
                        pwd_h, salt = hash_pw(v_reg_pw)
                        conn = get_db_connection()
                        try:
                            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, 'VENUE', ?)", (f"USR-{v_reg_id}", v_reg_email, pwd_h, salt, v_reg_id))
                            conn.execute("""INSERT INTO venues 
                                (venue_id, name, type, email, phone, whatsapp_no, address, max_capacity, tax_id, bank_details, brand_color, logo_url, flyer_image_url, approved_supporter_ids)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '[]')""",
                                (v_reg_id, v_reg_name, v_reg_type, v_reg_email, v_reg_phone, v_reg_wa, v_reg_addr, v_reg_cap, v_reg_tax, v_reg_bank, v_reg_color))
                            conn.commit()
                            st.success("Venue profile registered successfully! Proceed to log in.")
                        except sqlite3.IntegrityError:
                            st.error("Account email already registered on network.")
                        finally:
                            conn.close()
                    else:
                        st.error("Please fill in required fields.")
    else:
        v_id = st.session_state["tenant_id"]
        conn = get_db_connection()
        venue_info = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (v_id,)).fetchall()[0]
        
        tab_v_dash, tab_v_spaces, tab_v_events, tab_v_vendors = st.tabs([
            "📊 Executive Dashboard", "🏛️ Sub-Space Inventory", "🎟️ Host Venue Public Events", "🤝 Approved Vendor Directory"
        ])
        
        with tab_v_dash:
            bookings = conn.execute("SELECT * FROM bookings WHERE venue_id = ?", (v_id,)).fetchall()
            t_rev = sum(b['venue_cost'] for b in bookings if b['status'] == 'Confirmed')
            t_bookings = len(bookings)
            p_bookings = len([b for b in bookings if b['status'] != 'Confirmed'])
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.markdown(f"<div class='metric-card'><small>TOTAL VERIFIED REVENUE</small><h2>BWP {t_rev:,.2f}</h2></div>", unsafe_allow_html=True)
            mc2.markdown(f"<div class='metric-card'><small>TOTAL RESERVATIONS</small><h2>{t_bookings}</h2></div>", unsafe_allow_html=True)
            mc3.markdown(f"<div class='metric-card'><small>PENDING VERIFICATIONS</small><h2>{p_bookings}</h2></div>", unsafe_allow_html=True)
            
            st.divider()
            st.markdown("### Facility Reservation Records")
            if not bookings:
                st.info("No booking records generated yet.")
            else:
                for b in bookings:
                    with st.expander(f"Booking Ref #{b['booking_id']} — {b['customer_name']} ({b['booking_date']})"):
                        st.write(f"**Sub-Space:** {b['space_name']} | **Duration:** {b['days']} Day(s)")
                        st.write(f"**Total Fee:** BWP {b['venue_cost']:,.2f} | **Payment Method:** {b['payment_method']}")
                        st.write(f"**Current Status:** {b['status']}")
                        
                        col_act1, col_act2 = st.columns(2)
                        if b['status'] != 'Confirmed':
                            if col_act1.button("APPROVE & CONFIRM RESERVATION", key=f"app_b_{b['booking_id']}"):
                                conn.execute("UPDATE bookings SET status = 'Confirmed' WHERE booking_id = ?", (b['booking_id'],))
                                conn.commit()
                                st.rerun()
                        if col_act2.button("CANCEL RESERVATION", key=f"cnc_b_{b['booking_id']}"):
                            conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ?", (b['booking_id'],))
                            conn.commit()
                            st.rerun()

        with tab_v_spaces:
            st.markdown("### Manage Facility Sub-Spaces")
            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (v_id,)).fetchall()
            
            with st.form("add_space_form"):
                st.markdown("<div class='form-label'>Add New Sub-Space Asset</div>", unsafe_allow_html=True)
                s_name = st.text_input("Space Name (e.g., Grand Ballroom)")
                s_cap = st.number_input("Space Seating Capacity", min_value=5, value=100)
                s_rate = st.number_input("Daily Rental Tariff (BWP)", min_value=100.0, value=2500.0)
                s_img_file = st.file_uploader("Upload Space Image", type=["jpg", "png", "jpeg"], key="s_img_up")
                
                if st.form_submit_button("ADD SUB-SPACE TO INVENTORY"):
                    if s_name:
                        s_img_url = process_compressed_image_upload(s_img_file, fallback_url=SPACE_PRESETS[0])
                        conn.execute("INSERT INTO spaces (venue_id, name, capacity, daily_rate, image_url) VALUES (?, ?, ?, ?, ?)",
                                     (v_id, s_name, s_cap, s_rate, s_img_url))
                        conn.commit()
                        st.success(f"Space '{s_name}' added to facility catalog!")
                        st.rerun()
            
            st.divider()
            if spaces:
                for sp in spaces:
                    sc_col1, sc_col2 = st.columns([1, 3])
                    if sp['image_url']: sc_col1.image(sp['image_url'], use_container_width=True)
                    sc_col2.markdown(f"**{sp['name']}** — Capacity: {sp['capacity']:,} Guests | Tariff: BWP {sp['daily_rate']:,.2f}/day")

        with tab_v_events:
            st.markdown("### Create & Host Public Venue Events")
            spaces = conn.execute("SELECT * FROM spaces WHERE venue_id = ?", (v_id,)).fetchall()
            
            if not spaces:
                st.warning("Please configure at least one sub-space before creating public events.")
            else:
                with st.form("create_venue_event_form"):
                    e_title = st.text_input("Event Title")
                    e_space = st.selectbox("Venue Space", [s['name'] for s in spaces])
                    e_date = st.date_input("Event Date", min_value=datetime.date.today())
                    e_price = st.number_input("Ticket Admission Price (BWP)", min_value=0.0, value=150.0)
                    e_desc = st.text_area("Event Description & Highlights")
                    e_flyer_file = st.file_uploader("Upload Event Poster / Background Image", type=["jpg", "png", "jpeg"], key="v_ev_flyer")
                    e_vid_file = st.file_uploader("Upload Event Promotional Video (Optional)", type=["mp4", "mov"], key="v_ev_vid")
                    
                    if st.form_submit_button("PUBLISH PUBLIC EVENT TO BOX OFFICE"):
                        if e_title:
                            ev_id = f"EVT-{int(datetime.datetime.now().timestamp())}"
                            flyer_b64 = generate_branded_flyer(venue_info['name'], e_title, str(e_date), e_price, comments=e_desc, uploaded_bg_file=e_flyer_file, brand_color=venue_info['brand_color'])
                            vid_b64 = process_media_file_upload(e_vid_file)
                            
                            conn.execute("""INSERT INTO events 
                                (event_id, host_type, host_id, host_name, venue_id, venue_name, space_name, title, date, price, description, flyer_url, video_url, is_active)
                                VALUES (?, 'VENUE', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                                (ev_id, v_id, venue_info['name'], v_id, venue_info['name'], e_space, e_title, str(e_date), e_price, e_desc, flyer_b64, vid_b64))
                            conn.commit()
                            st.success(f"Event '{e_title}' published to public marketplace!")
                            st.rerun()

        with tab_v_vendors:
            st.markdown("### Approved Ancillary Vendor Network")
            all_vendors = conn.execute("SELECT * FROM supporters").fetchall()
            curr_approved = json.loads(venue_info['approved_supporter_ids'] or "[]")
            
            if not all_vendors:
                st.info("No vendor partners registered on network.")
            else:
                updated_approved = []
                for vnd in all_vendors:
                    is_app = vnd['supporter_id'] in curr_approved
                    chk = st.checkbox(f"{vnd['business_name']} ({vnd['category']})", value=is_app, key=f"chk_v_{vnd['supporter_id']}")
                    if chk:
                        updated_approved.append(vnd['supporter_id'])
                
                if st.button("UPDATE APPROVED VENDOR LIST", use_container_width=True):
                    conn.execute("UPDATE venues SET approved_supporter_ids = ? WHERE venue_id = ?", (json.dumps(updated_approved), v_id))
                    conn.commit()
                    st.success("Approved vendor directory updated successfully!")
                    st.rerun()
        conn.close()

# ---------------------------------------------------------
# 7. MODULE 3: VENDOR PORTAL & SERVICE FULFILLMENT
# ---------------------------------------------------------
elif user_role == "Vendor Portal & Service Fulfillment":
    st.markdown("<div class='exec-title'>Vendor Portal & Service Fulfillment</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Ancillary Service Bundles & Vendor Event Hosting Workspace</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    if not st.session_state["authenticated"] or st.session_state["user_role"] != "VENDOR":
        st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>Vendor Workspace Portal Login</h3>", unsafe_allow_html=True)
        tab_v_login, tab_v_reg = st.tabs(["🔒 Secure Workspace Login", "📦 Register Vendor Partner"])
        
        with tab_v_login:
            with st.form("vendor_login_form"):
                vnd_login_email = st.text_input("Registered Partner Email")
                vnd_login_pw = st.text_input("Password", type="password")
                if st.form_submit_button("AUTHENTICATE VENDOR WORKSPACE", use_container_width=True):
                    conn = get_db_connection()
                    user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'VENDOR'", (vnd_login_email,)).fetchone()
                    conn.close()
                    if user and verify_pw(vnd_login_pw, user['password_hash'], user['salt']):
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = user['email']
                        st.session_state["user_role"] = "VENDOR"
                        st.session_state["tenant_id"] = user['tenant_id']
                        st.success("Authenticated successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid vendor credentials.")
                        
        with tab_v_reg:
            with st.form("vendor_reg_form"):
                vnd_reg_id = f"SUP-{int(datetime.datetime.now().timestamp())}"
                vnd_reg_biz = st.text_input("Business / Trade Name")
                vnd_reg_cat = st.selectbox("Service Category", ["Catering & Culinary Services", "Sound, Stage & Lighting", "Decor & Event Styling", "Security & VIP Protocol", "Photography & Videography"])
                vnd_reg_contact = st.text_input("Primary Contact Person")
                vnd_reg_email = st.text_input("Business Email Address")
                vnd_reg_pw = st.text_input("Workspace Security Password", type="password")
                vnd_reg_phone = st.text_input("Contact Phone Number")
                vnd_reg_bank = st.text_area("Settlement Bank Details")
                
                if st.form_submit_button("REGISTER VENDOR BUSINESS", use_container_width=True):
                    if vnd_reg_biz and vnd_reg_email and vnd_reg_pw:
                        pwd_h, salt = hash_pw(vnd_reg_pw)
                        conn = get_db_connection()
                        try:
                            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, 'VENDOR', ?)", (f"USR-{vnd_reg_id}", vnd_reg_email, pwd_h, salt, vnd_reg_id))
                            conn.execute("""INSERT INTO supporters 
                                (supporter_id, business_name, category, contact_person, email, phone, bank_details, brand_color, logo_url)
                                VALUES (?, ?, ?, ?, ?, ?, ?, '#0F172A', '')""",
                                (vnd_reg_id, vnd_reg_biz, vnd_reg_cat, vnd_reg_contact, vnd_reg_email, vnd_reg_phone, vnd_reg_bank))
                            conn.commit()
                            st.success("Vendor partner registered successfully! Log in to continue.")
                        except sqlite3.IntegrityError:
                            st.error("Account email already exists.")
                        finally:
                            conn.close()
                    else:
                        st.error("Please complete all required registration fields.")
    else:
        s_id = st.session_state["tenant_id"]
        conn = get_db_connection()
        vendor_info = conn.execute("SELECT * FROM supporters WHERE supporter_id = ?", (s_id,)).fetchall()[0]
        
        tab_vnd_dash, tab_vnd_pkgs, tab_vnd_events = st.tabs([
            "📊 Vendor Ledger & Orders", "📦 Service Package Catalog", "🎉 Host Vendor Public Event"
        ])
        
        with tab_vnd_dash:
            v_invoices = conn.execute("SELECT * FROM vendor_invoices WHERE supporter_id = ?", (s_id,)).fetchall()
            v_rev = sum(i['total_amount'] for i in v_invoices if i['status'] == 'Confirmed')
            
            st.markdown(f"### Welcome, {vendor_info['business_name']}")
            vm1, vm2 = st.columns(2)
            vm1.markdown(f"<div class='metric-card'><small>TOTAL VERIFIED VENDOR REVENUE</small><h2>BWP {v_rev:,.2f}</h2></div>", unsafe_allow_html=True)
            vm2.markdown(f"<div class='metric-card'><small>TOTAL INVOICE ORDERS</small><h2>{len(v_invoices)}</h2></div>", unsafe_allow_html=True)
            
            st.divider()
            st.markdown("### Client Ancillary Service Orders")
            if not v_invoices:
                st.info("No service orders received yet.")
            else:
                for vi in v_invoices:
                    with st.expander(f"Invoice #{vi['vendor_invoice_id']} — {vi['customer_name']} (BWP {vi['total_amount']:,.2f})"):
                        st.write(f"**Venue Location:** {vi['venue_name']} | **Event Date:** {vi['event_date']}")
                        st.write(f"**Client Email:** {vi['customer_email']} | **Phone:** {vi['customer_phone']}")
                        st.write(f"**Status:** {vi['status']}")
                        
                        items = json.loads(vi['items_json'] or "[]")
                        st.table(items)
                        
                        if vi['status'] != 'Confirmed':
                            if st.button("MARK INVOICE AS SETTLED & CONFIRMED", key=f"settle_vi_{vi['vendor_invoice_id']}"):
                                conn.execute("UPDATE vendor_invoices SET status = 'Confirmed' WHERE vendor_invoice_id = ?", (vi['vendor_invoice_id'],))
                                conn.commit()
                                st.rerun()

        with tab_vnd_pkgs:
            st.markdown("### Manage Service Packages & Pricing")
            templates = conn.execute("SELECT * FROM vendor_templates WHERE supporter_id = ?", (s_id,)).fetchall()
            
            with st.form("add_vendor_template_form"):
                st.markdown("<div class='form-label'>Add New Service Offering</div>", unsafe_allow_html=True)
                t_name = st.text_input("Package / Item Name")
                t_desc = st.text_area("Service Description")
                t_unit = st.selectbox("Pricing Unit", ["Per Day", "Per Event", "Per Guest / Person", "Per Hour", "Fixed Package"])
                t_price = st.number_input("Unit Tariff (BWP)", min_value=10.0, value=500.0)
                t_img_file = st.file_uploader("Upload Package Banner Image", type=["jpg", "png", "jpeg"], key="vnd_pkg_img")
                
                if st.form_submit_button("SAVE SERVICE PACKAGE"):
                    if t_name:
                        t_img_url = process_compressed_image_upload(t_img_file, fallback_url="")
                        conn.execute("""INSERT INTO vendor_templates 
                            (supporter_id, item_name, description, unit_type, unit_price, image_url, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, 1)""",
                            (s_id, t_name, t_desc, t_unit, t_price, t_img_url))
                        conn.commit()
                        st.success("Service package catalog updated!")
                        st.rerun()

            st.divider()
            if templates:
                for tp in templates:
                    st.write(f"• **{tp['item_name']}** — BWP {tp['unit_price']:,.2f} / {tp['unit_type']}")

        # ---------------------------------------------------------
        # NEW VENDOR COMPONENT: VENDOR EVENT HOSTING
        # ---------------------------------------------------------
        with tab_vnd_events:
            st.markdown("### Host Public Event as Vendor Partner")
            venues = conn.execute("SELECT * FROM venues").fetchall()
            
            if not venues:
                st.warning("No commercial venue facilities currently registered on network to host events.")
            else:
                with st.form("vendor_create_event_form"):
                    ve_title = st.text_input("Vendor Event Title (e.g., Annual Culinary Expo)")
                    ve_venue_name = st.selectbox("Select Partner Venue Facility", [v['name'] for v in venues])
                    selected_partner_venue = next(v for v in venues if v['name'] == ve_venue_name)
                    
                    ve_space = st.text_input("Venue Area / Space (e.g., Main Exhibition Lawn)", value="Main Event Space")
                    ve_date = st.date_input("Event Date", min_value=datetime.date.today(), key="vnd_ev_date")
                    ve_price = st.number_input("Ticket Price per Attendee (BWP)", min_value=0.0, value=200.0, key="vnd_ev_price")
                    ve_desc = st.text_area("Event Description & Key Highlights", key="vnd_ev_desc")
                    
                    ve_flyer_file = st.file_uploader("Upload Event Poster / Canvas Image", type=["jpg", "png", "jpeg"], key="vnd_ev_flyer")
                    ve_vid_file = st.file_uploader("Upload Promotional Video (Optional)", type=["mp4", "mov"], key="vnd_ev_vid")
                    
                    if st.form_submit_button("PUBLISH VENDOR EVENT TO BOX OFFICE", type="primary", use_container_width=True):
                        if ve_title:
                            ve_id = f"EVT-VND-{int(datetime.datetime.now().timestamp())}"
                            flyer_b64 = generate_branded_flyer(
                                f"{vendor_info['business_name']} @ {selected_partner_venue['name']}",
                                ve_title, str(ve_date), ve_price, comments=ve_desc, uploaded_bg_file=ve_flyer_file, brand_color="#D97706"
                            )
                            vid_b64 = process_media_file_upload(ve_vid_file)
                            
                            conn.execute("""INSERT INTO events 
                                (event_id, host_type, host_id, host_name, venue_id, venue_name, space_name, title, date, price, description, flyer_url, video_url, is_active)
                                VALUES (?, 'VENDOR', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                                (ve_id, s_id, vendor_info['business_name'], selected_partner_venue['venue_id'], selected_partner_venue['name'], ve_space, ve_title, str(ve_date), ve_price, ve_desc, flyer_b64, vid_b64))
                            conn.commit()
                            st.success(f"Vendor Event '{ve_title}' hosted successfully and published to public Box Office!")
                            st.rerun()
                        else:
                            st.error("Event title is required.")
        conn.close()

# ---------------------------------------------------------
# 8. MODULE 4: ACCESS CONTROL & VERIFICATION SUITE
# ---------------------------------------------------------
elif user_role == "Access Control & Verification Suite":
    st.markdown("<div class='exec-title'>Access Control & Verification Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Gatekeeper Real-Time Ticket Validation</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    with st.form("verify_ticket_form"):
        st.markdown("<h3 style='text-align: center; font-family: Playfair Display, serif;'>Scan or Key-In Ticket Credentials</h3>", unsafe_allow_html=True)
        raw_input = st.text_input("Enter Ticket Pass ID or Verification Hash:")
        
        if st.form_submit_button("VERIFY TICKET PASS", type="primary", use_container_width=True):
            if raw_input:
                conn = get_db_connection()
                tck = conn.execute("SELECT * FROM tickets WHERE ticket_id = ? OR verification_hash = ?", (raw_input.strip(), raw_input.strip())).fetchone()
                
                if not tck:
                    st.error("❌ INVALID ADMISSION TICKET: No matching pass found in system ledger.")
                else:
                    if tck['scanned_at']:
                        st.error(f"🚨 ALREADY USED TICKET: Pass was previously validated on {tck['scanned_at']}.")
                    else:
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn.execute("UPDATE tickets SET status = 'VALIDATED / ENTRY GRANTED', scanned_at = ? WHERE ticket_id = ?", (now_str, tck['ticket_id']))
                        conn.commit()
                        st.balloons()
                        st.success(f"✅ ENTRY GRANTED! Valid Pass #{tck['ticket_id']} for {tck['buyer']} ({tck['qty']} Person(s)).")
                conn.close()

# ---------------------------------------------------------
# 9. MODULE 5: EXECUTIVE MASTER LEDGER & AUDIT SUITE
# ---------------------------------------------------------
elif user_role == "Executive Master Ledger & Audit Suite":
    st.markdown("<div class='exec-title'>Executive Master Ledger & Audit Suite</div>", unsafe_allow_html=True)
    st.markdown("<div class='exec-subtitle'>Enterprise Cross-Facility Operational Audit</div>", unsafe_allow_html=True)
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

    conn = get_db_connection()
    venues = conn.execute("SELECT * FROM venues").fetchall()
    supporters = conn.execute("SELECT * FROM supporters").fetchall()
    bookings = conn.execute("SELECT * FROM bookings").fetchall()
    v_invoices = conn.execute("SELECT * FROM vendor_invoices").fetchall()
    tickets = conn.execute("SELECT * FROM tickets").fetchall()
    conn.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"<div class='metric-card'><small>REGISTERED VENUES</small><h2>{len(venues)}</h2></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card'><small>VENDOR PARTNERS</small><h2>{len(supporters)}</h2></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card'><small>TOTAL BOOKINGS</small><h2>{len(bookings)}</h2></div>", unsafe_allow_html=True)
    m4.markdown(f"<div class='metric-card'><small>TICKETS ISSUED</small><h2>{len(tickets)}</h2></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Master Venue Booking Register")
    if bookings:
        st.dataframe([dict(b) for b in bookings], use_container_width=True)

    st.markdown("### Master Vendor Invoice Register")
    if v_invoices:
        st.dataframe([dict(v) for v in v_invoices], use_container_width=True)

    st.markdown("### Master Event Pass Ticket Register")
    if tickets:
        st.dataframe([dict(t) for t in tickets], use_container_width=True)
