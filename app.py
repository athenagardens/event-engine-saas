import streamlit as st
import json
import os
import datetime
import hashlib
import base64

# ---------------------------------------------------------
# 1. DATABASE & STORAGE MANAGEMENT
# ---------------------------------------------------------
DB_FILE = "enterprise_event_platform_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"venues": [], "supporters": [], "events": [], "bookings": [], "tickets": []}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# ---------------------------------------------------------
# 2. APP CONFIGURATION & STYLES
# ---------------------------------------------------------
st.set_page_config(
    page_title="Enterprise Venue & Event Management Gateway",
    page_icon="🏢",
    layout="wide"
)

def inject_enterprise_styles():
    st.markdown("""
        <style>
            .main { background-color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            h1, h2, h3, h4 { color: #0F172A !important; font-weight: 700 !important; letter-spacing: -0.02em; }
            [data-testid="stSidebar"] { background-color: #0F172A !important; }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] p { color: #F1F5F9 !important; }
            
            .invoice-box {
                background: #FFFFFF; padding: 2.2rem; border-radius: 8px;
                border: 1px solid #CBD5E1; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }
            .ticket-card {
                background: #FFFFFF; padding: 1.5rem; border-radius: 8px;
                border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom: 1rem;
            }
            .profile-card {
                padding: 1.8rem; border-radius: 8px; color: #FFFFFF !important; margin-bottom: 1.5rem;
            }
            .badge-verified {
                background-color: #059669; color: #FFFFFF; padding: 0.25rem 0.6rem;
                border-radius: 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
            }
            .logo-img {
                max-height: 60px; max-width: 180px; object-fit: contain;
            }
        </style>
    """, unsafe_allow_html=True)

inject_enterprise_styles()

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

# Free Royalty-Free Unsplash Stock Presets
SPACE_PRESETS = [
    "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=500",
    "https://images.unsplash.com/photo-1511578314322-379afb476865?w=500",
    "https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=500",
    "https://images.unsplash.com/photo-1540575861501-7cf05a4b125a?w=500"
]

DEFAULT_LOGO = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200"

# ---------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown("## 🏢 ENTERPRISE GATEWAY")
st.sidebar.caption("Venue Operations, Ticketing & Service Procurement Platform")
st.sidebar.divider()

user_role = st.sidebar.radio(
    "Active System Console:",
    [
        "Public Portal (Bookings & Ticketing)",
        "Facility Owner Console",
        "Facility Supporter Console (Vendors)",
        "Ticket Scanner & Gate Access",
        "Platform Admin / Master Ledger"
    ]
)

st.sidebar.divider()
with st.sidebar.expander("System Utilities"):
    if st.button("Purge & Reset System Database", type="primary", use_container_width=True):
        db = {"venues": [], "supporters": [], "events": [], "bookings": [], "tickets": []}
        save_data(db)
        st.success("Database purged successfully.")
        st.rerun()

# ---------------------------------------------------------
# 4. MODULE 1: PUBLIC PORTAL (BOOKINGS, TICKETS & INVOICES)
# ---------------------------------------------------------
if user_role == "Public Portal (Bookings & Ticketing)":
    st.title("Central Venue Booking & Public Ticketing Console")
    st.caption("Reserve enterprise facilities, customize vendor packages, and purchase verified event admission tickets.")
    st.divider()

    public_tab1, public_tab2 = st.tabs(["Book Venue & Instant Quotation", "Public Event Ticket Shop"])

    # --- TAB A: VENUE BOOKING & BRANDED INVOICE ---
    with public_tab1:
        st.markdown("### Automated Venue & Services Reservation")
        st.info("Direct digital booking console. Select your date, hall, and supplier packages to generate an instant quotation and locked date invoice.")

        venues_list = db.get("venues", [])
        if not venues_list:
            st.warning("No facility profiles are currently published on the gateway.")
        else:
            venue_names = [v.get("name", "Unnamed Facility") for v in venues_list]
            
            query_params = st.query_params
            default_index = 0
            if "venue_id" in query_params:
                matched_v = next((i for i, v in enumerate(venues_list) if v.get("venue_id") == query_params["venue_id"]), 0)
                default_index = matched_v

            sel_v_name = st.selectbox("1. Select Facility / Venue:", venue_names, index=default_index)
            sel_venue = next(v for v in venues_list if v.get("name") == sel_v_name)

            v_brand_color = sel_venue.get("brand_color", "#0F172A")
            v_secondary_color = sel_venue.get("brand_secondary", "#2563EB")
            v_logo = sel_venue.get("logo_url", DEFAULT_LOGO)

            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                st.image(sel_venue.get("flyer_image_url", SPACE_PRESETS[0]), use_container_width=True)
            with col_v2:
                st.markdown(f"""
                    <div style="background-color: {v_brand_color}; padding: 1.2rem; border-radius: 8px; color: #FFFFFF;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="color: #FFFFFF !important; margin: 0;">{sel_venue.get('name')}</h3>
                            <img src="{v_logo}" class="logo-img" style="border-radius: 4px; background: white; padding: 2px;">
                        </div>
                        <p style="color: #F1F5F9 !important; margin-top: 10px; font-size: 0.9rem;">
                            <b>Location:</b> {sel_venue.get('address')} | <b>Category:</b> {sel_venue.get('type')}<br>
                            <b>Max Guest Occupancy:</b> {sel_venue.get('max_capacity'):,} Guests
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            spaces = sel_venue.get("spaces", [])
            if not spaces:
                st.warning("This venue has not listed sub-spaces for hire.")
            else:
                st.divider()
                st.markdown("### 2. Select Space & Reserve Date")
                
                # Show Sub-Space Thumbnails
                st.markdown("##### Available Venue Sections / Spaces:")
                sp_cols = st.columns(min(len(spaces), 4))
                for idx, sp in enumerate(spaces):
                    with sp_cols[idx % 4]:
                        sp_img = sp.get("image_url", SPACE_PRESETS[0])
                        st.image(sp_img, use_container_width=True)
                        st.caption(f"**{sp.get('name')}**\n\nCap: {sp.get('capacity')} | BWP {sp.get('daily_rate'):,.2f}/day")

                sp_col1, sp_col2, sp_col3 = st.columns(3)
                with sp_col1:
                    space_opts = [s.get("name") for s in spaces]
                    sel_sp_name = st.selectbox("Select Space / Hall", space_opts)
                    sel_space = next(s for s in spaces if s.get("name") == sel_sp_name)
                with sp_col2:
                    booking_date = st.date_input("Event Date", min_value=datetime.date.today())
                with sp_col3:
                    booking_days = st.number_input("Duration (Days)", min_value=1, value=1)

                space_total = sel_space.get("daily_rate", 0) * booking_days

                existing_bookings = db.get("bookings", [])
                existing_events = db.get("events", [])
                date_str = str(booking_date)
                
                is_customer_locked = any(
                    b.get("venue_id") == sel_venue.get("venue_id") and 
                    b.get("space_name") == sel_sp_name and 
                    b.get("booking_date") == date_str and 
                    b.get("status") == "Confirmed / Paid"
                    for b in existing_bookings
                )

                is_facility_event_locked = any(
                    e.get("venue_id") == sel_venue.get("venue_id") and
                    (e.get("space_name") == sel_sp_name or e.get("space_name") == "All Spaces / Full Venue") and
                    e.get("date") == date_str
                    for e in existing_events
                )

                if is_customer_locked or is_facility_event_locked:
                    st.error(f"❌ DATE LOCKED: '{sel_sp_name}' is ALREADY RESERVED on {date_str}. Please choose another date or space.")
                else:
                    st.success(f"✅ DATE AVAILABLE: '{sel_sp_name}' is open for booking on {date_str}.")

                    st.divider()
                    st.markdown("### 3. Add Service Provider Packages (Supporters)")

                    selected_addons = []
                    addons_total = 0.0

                    supporters = db.get("supporters", [])
                    if supporters:
                        for sup in supporters:
                            templates = sup.get("quotation_templates", [])
                            sup_color = sup.get("brand_color", "#1E293B")
                            sup_logo = sup.get("logo_url", DEFAULT_LOGO)
                            if templates:
                                with st.expander(f"Add Services: {sup.get('business_name')} ({sup.get('category')})"):
                                    st.image(sup_logo, width=120)
                                    for t in templates:
                                        item_key = f"{sup.get('supporter_id')}_{t.get('item_name')}"
                                        qty = st.number_input(
                                            f"{t.get('item_name')} — BWP {t.get('unit_price'):,.2f} / {t.get('unit_type')}",
                                            min_value=0, value=0, key=item_key
                                        )
                                        if qty > 0:
                                            cost = qty * t.get("unit_price")
                                            addons_total += cost
                                            selected_addons.append({
                                                "vendor": sup.get("business_name"),
                                                "vendor_color": sup_color,
                                                "item": t.get("item_name"),
                                                "qty": qty,
                                                "unit_price": t.get("unit_price"),
                                                "total": cost
                                            })
                    else:
                        st.info("No supplier add-ons currently available.")

                    st.divider()
                    grand_total = space_total + addons_total

                    # --- BRANDED OFFICIAL INVOICE WITH LOGO & COMPANY DETAILS ---
                    st.markdown("### 4. Itemized Quotation & Digital Receipt")
                    
                    st.markdown(f"""
                    <div class="invoice-box" style="border-top: 6px solid {v_brand_color};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <img src="{v_logo}" class="logo-img" style="margin-bottom: 10px;">
                                <h2 style="color: {v_brand_color} !important; margin: 0;">OFFICIAL INVOICE / QUOTATION</h2>
                                <p style="font-size: 0.85rem; color: #64748B; margin-top: 4px;">
                                    <b>Issuer:</b> {sel_venue.get('name')}<br>
                                    <b>Address:</b> {sel_venue.get('address')}<br>
                                    <b>Tax / Reg ID:</b> {sel_venue.get('tax_id')} | <b>Email:</b> {sel_venue.get('email')}
                                </p>
                            </div>
                            <div style="text-align: right;">
                                <p style="font-size: 0.85rem; margin: 0;"><b>Invoice Date:</b> {datetime.date.today()}</p>
                                <p style="font-size: 0.85rem; margin: 0;"><b>Payment Status:</b> Pending Settlement</p>
                            </div>
                        </div>
                        <hr>
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 1rem;">
                            <thead>
                                <tr style="background-color: #F1F5F9; text-align: left;">
                                    <th style="padding: 8px;">Item Description</th>
                                    <th style="padding: 8px;">Qty / Days</th>
                                    <th style="padding: 8px;">Unit Rate</th>
                                    <th style="padding: 8px; text-align: right;">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="padding: 8px;">Venue Hire: {sel_sp_name} ({sel_venue.get('name')})</td>
                                    <td style="padding: 8px;">{booking_days} day(s)</td>
                                    <td style="padding: 8px;">BWP {sel_space.get('daily_rate'):,.2f}</td>
                                    <td style="padding: 8px; text-align: right;">BWP {space_total:,.2f}</td>
                                </tr>
                                {"".join([f"<tr><td style='padding:8px;'>[{addon['vendor']}] {addon['item']}</td><td style='padding:8px;'>{addon['qty']}</td><td style='padding:8px;'>BWP {addon['unit_price']:,.2f}</td><td style='padding:8px; text-align:right;'>BWP {addon['total']:,.2f}</td></tr>" for addon in selected_addons])}
                            </tbody>
                        </table>
                        <hr>
                        <div style="text-align: right;">
                            <h2 style="color: {v_secondary_color} !important; margin: 0;">Grand Total: BWP {grand_total:,.2f}</h2>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("#### Customer Details & Instant Lock Payment")
                    with st.form("public_booking_form"):
                        c_name = st.text_input("Full Name / Company Name*")
                        c_email = st.text_input("Email Address (for Digital Tax Invoice & Receipt)*")
                        c_phone = st.text_input("Phone / WhatsApp Number*")
                        c_pay_method = st.selectbox("Payment Gateway", ["Credit/Debit Card (Visa/Mastercard)", "EFT Electronic Settlement", "Corporate Account Invoice"])

                        pay_btn = st.form_submit_button("Pay Now & Lock Event Dates", use_container_width=True)

                        if pay_btn:
                            if c_name and c_email and c_phone:
                                new_booking = {
                                    "booking_id": f"BK-{len(existing_bookings)+1001}",
                                    "venue_id": sel_venue.get("venue_id"),
                                    "venue_name": sel_venue.get("name"),
                                    "space_name": sel_sp_name,
                                    "customer_name": c_name,
                                    "customer_email": c_email,
                                    "customer_phone": c_phone,
                                    "booking_date": date_str,
                                    "days": booking_days,
                                    "venue_cost": space_total,
                                    "addons_cost": addons_total,
                                    "grand_total": grand_total,
                                    "addons_breakdown": selected_addons,
                                    "payment_method": c_pay_method,
                                    "status": "Confirmed / Paid",
                                    "created_at": str(datetime.datetime.now())
                                }
                                db.setdefault("bookings", []).append(new_booking)
                                save_data(db)
                                st.success("Payment Processed Successfully. Dates are officially locked.")
                                st.rerun()
                            else:
                                st.error("Please complete mandatory customer details.")

    # --- TAB B: BRANDED TICKET SHOP & TICKETS WITH LOGOS ---
    with public_tab2:
        st.markdown("### Public Event Ticket Shop")
        events = db.get("events", [])
        if not events:
            st.info("No upcoming public ticketed events hosted at this time.")
        else:
            for ev in events:
                # Find matching venue for branding
                matching_venue = next((v for v in db.get("venues", []) if v.get("venue_id") == ev.get("venue_id")), {})
                v_logo = matching_venue.get("logo_url", DEFAULT_LOGO)
                v_primary = matching_venue.get("brand_color", "#0F172A")
                v_sec = matching_venue.get("brand_secondary", "#2563EB")

                with st.container():
                    col_e1, col_e2 = st.columns([1, 2])
                    with col_e1:
                        st.image(ev.get("flyer_url", SPACE_PRESETS[0]), use_container_width=True)
                    with col_e2:
                        st.markdown(f"### {ev.get('title')}")
                        st.write(f"<b>Venue:</b> {ev.get('venue_name')} | <b>Space:</b> {ev.get('space_name', 'Full Venue')} | <b>Date:</b> {ev.get('date')}", unsafe_allow_html=True)
                        st.write(f"{ev.get('description')}")
                        st.markdown(f"<b>Admission Price:</b> BWP {ev.get('price', 0):,.2f}", unsafe_allow_html=True)

                        with st.form(f"ticket_form_{ev.get('event_id')}"):
                            t_qty = st.number_input("Quantity", min_value=1, value=1)
                            t_buyer = st.text_input("Buyer Full Name*")
                            t_email = st.text_input("Delivery Email*")
                            
                            buy_t_btn = st.form_submit_button("Purchase Admission Ticket")
                            if buy_t_btn:
                                if t_buyer and t_email:
                                    tot_t = t_qty * ev.get('price', 0)
                                    ticket_id = f"TKT-{len(db.get('tickets', []))+10001}"
                                    raw_hash = f"{ticket_id}-{ev.get('event_id')}-{t_email}-{datetime.datetime.now()}"
                                    sec_hash = hashlib.sha256(raw_hash.encode()).hexdigest()[:12].upper()

                                    new_ticket = {
                                        "ticket_id": ticket_id,
                                        "verification_hash": f"HASH-{sec_hash}",
                                        "event_id": ev.get('event_id'),
                                        "event_title": ev.get('title'),
                                        "venue_name": ev.get('venue_name'),
                                        "venue_logo": v_logo,
                                        "brand_color": v_primary,
                                        "brand_secondary": v_sec,
                                        "buyer": t_buyer,
                                        "email": t_email,
                                        "qty": t_qty,
                                        "total_paid": tot_t,
                                        "status": "VALID",
                                        "scanned_at": None
                                    }
                                    db.setdefault("tickets", []).append(new_ticket)
                                    save_data(db)

                                    st.success("Ticket Purchased Successfully!")
                                    st.markdown(f"""
                                    <div class="ticket-card" style="border-left: 8px solid {v_primary};">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <div>
                                                <span class="badge-verified">OFFICIAL PASS</span>
                                                <span style="font-family: monospace; font-weight: bold; margin-left: 10px;">{new_ticket['verification_hash']}</span>
                                            </div>
                                            <img src="{v_logo}" class="logo-img">
                                        </div>
                                        <h3 style="margin-top: 10px; color: {v_primary} !important;">{ev.get('title')}</h3>
                                        <p><b>Holder:</b> {t_buyer} | <b>Qty:</b> {t_qty} Guest(s)<br>
                                        <b>Venue:</b> {ev.get('venue_name')} | <b>Ticket ID:</b> {ticket_id}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error("Please provide buyer name and email.")
                    st.divider()

# ---------------------------------------------------------
# 5. MODULE 2: FACILITY OWNER CONSOLE
# ---------------------------------------------------------
elif user_role == "Facility Owner Console":
    st.title("Facility Owner Console")
    st.caption("Configure facility details, upload logos, manage sub-spaces with thumbnails, and publish flyers.")
    st.divider()

    venues = db.get("venues", [])
    if not venues:
        st.info("👋 Welcome! Please complete initial facility registration.")
        with st.form("fac_reg_main"):
            st.markdown("### Primary Facility Onboarding Profile")
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Facility Name*", placeholder="Royal Aria Convention Center")
                f_type = st.selectbox("Facility Type", ["Convention Center", "Hotel Ballroom", "Outdoor Arena", "Community Hall"])
                f_email = st.text_input("Manager Email*")
                f_phone = st.text_input("Manager WhatsApp/Phone*")
            with col2:
                f_address = st.text_input("Physical Address*")
                f_cap = st.number_input("Max Overall Capacity*", value=1000)
                f_tax = st.text_input("Tax / CIPA Registration ID*")
                f_bank = st.text_input("Bank Payout Account Details")

            st.markdown("##### Logo & Corporate Branding")
            f_logo_file = st.file_uploader("Upload Official Company Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
            
            bc1, bc2 = st.columns(2)
            f_brand_color = bc1.color_picker("Primary Brand Color", "#0F172A")
            f_brand_sec = bc2.color_picker("Accent / Secondary Color", "#2563EB")

            f_img = st.text_input("Cover Image URL", value=SPACE_PRESETS[0])
            
            if st.form_submit_button("Register Facility Profile"):
                if f_name and f_email and f_phone and f_address and f_tax:
                    logo_url = process_image_upload(f_logo_file, DEFAULT_LOGO)
                    db.setdefault("venues", []).append({
                        "venue_id": f"v_{len(venues)+101}",
                        "name": f_name,
                        "type": f_type,
                        "email": f_email,
                        "phone": f_phone,
                        "address": f_address,
                        "max_capacity": f_cap,
                        "tax_id": f_tax,
                        "bank_details": f_bank,
                        "brand_color": f_brand_color,
                        "brand_secondary": f_brand_sec,
                        "logo_url": logo_url,
                        "flyer_image_url": f_img,
                        "spaces": []
                    })
                    save_data(db)
                    st.success("Facility Registered Successfully!")
                    st.rerun()
    else:
        cur_v = venues[0]
        v_color = cur_v.get("brand_color", "#0F172A")
        v_sec = cur_v.get("brand_secondary", "#2563EB")
        v_logo = cur_v.get("logo_url", DEFAULT_LOGO)

        st.markdown(f"""
            <div class="profile-card" style="background: linear-gradient(135deg, {v_color} 0%, {v_sec} 100%);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #FFFFFF !important; margin: 0;">🏛️ {cur_v.get('name')}</h2>
                        <p style="color: #F1F5F9 !important; margin-top: 5px;">
                            📍 {cur_v.get('address')} | 👥 Max Capacity: {cur_v.get('max_capacity'):,} | Tax ID: {cur_v.get('tax_id')}
                        </p>
                    </div>
                    <img src="{v_logo}" class="logo-img" style="background: white; padding: 4px; border-radius: 6px;">
                </div>
            </div>
        """, unsafe_allow_html=True)

        t_spaces, t_brand, t_flyers, t_bookings = st.tabs([
            "Configured Sub-Spaces (Photos & Thumbnails)", 
            "Logo & Corporate Brand Colors",
            "Flyer Builder & Scheduled Events", 
            "Locked Date Bookings & Invoices"
        ])

        # SUB-SPACES WITH PHOTO PRESETS & UPLOADS
        with t_spaces:
            st.markdown("#### Add / Manage Sub-Spaces with Photos")
            with st.form("add_sp"):
                c1, c2, c3 = st.columns(3)
                s_name = c1.text_input("Space Name (e.g. Executive Ballroom)")
                s_cap = c2.number_input("Capacity", value=250)
                s_rate = c3.number_input("Daily Hire Rate (BWP)", value=3500.0)

                st.markdown("##### Sub-Space Photo:")
                sp_img_file = st.file_uploader("Upload Sub-Space Photo", type=["png", "jpg", "jpeg"], key="sp_upload")
                preset_choice = st.selectbox("Or Choose Preset Photo Thumbnail", SPACE_PRESETS)

                if st.form_submit_button("Add Hire Space"):
                    if s_name:
                        final_sp_img = process_image_upload(sp_img_file, preset_choice)
                        cur_v.setdefault("spaces", []).append({
                            "name": s_name, 
                            "capacity": s_cap, 
                            "daily_rate": s_rate,
                            "image_url": final_sp_img
                        })
                        save_data(db)
                        st.success("Sub-space added!")
                        st.rerun()

            st.divider()
            st.markdown("##### Existing Sub-Spaces")
            spaces_list = cur_v.get("spaces", [])
            if not spaces_list:
                st.info("No sub-spaces configured.")
            else:
                for idx, sp in enumerate(spaces_list):
                    with st.expander(f"📍 {sp.get('name')} — BWP {sp.get('daily_rate'):,.2f}/day"):
                        sc1, sc2 = st.columns([1, 2])
                        with sc1:
                            st.image(sp.get("image_url", SPACE_PRESETS[0]), use_container_width=True)
                        with sc2:
                            with st.form(f"edit_sp_form_{idx}"):
                                es_name = st.text_input("Space Name", value=sp.get('name'))
                                es_cap = st.number_input("Capacity", value=int(sp.get('capacity', 0)))
                                es_rate = st.number_input("Daily Rate (BWP)", value=float(sp.get('daily_rate', 0.0)))
                                new_sp_file = st.file_uploader("Change Image", type=["png", "jpg", "jpeg"], key=f"sp_edit_{idx}")
                                
                                col_btn1, col_btn2 = st.columns(2)
                                save_edit = col_btn1.form_submit_button("💾 Save Changes")
                                delete_sp = col_btn2.form_submit_button("🗑️ Delete Space")

                                if save_edit:
                                    img_final = process_image_upload(new_sp_file, sp.get("image_url"))
                                    spaces_list[idx] = {"name": es_name, "capacity": es_cap, "daily_rate": es_rate, "image_url": img_final}
                                    save_data(db)
                                    st.success("Sub-space updated!")
                                    st.rerun()
                                if delete_sp:
                                    spaces_list.pop(idx)
                                    save_data(db)
                                    st.warning("Sub-space deleted!")
                                    st.rerun()

        # LOGO & BRANDING UPDATE
        with t_brand:
            st.markdown("#### Upload Company Logo & Set Corporate Colors")
            with st.form("update_brand_form"):
                new_logo_file = st.file_uploader("Upload New Company Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
                col_b1, col_b2 = st.columns(2)
                new_p = col_b1.color_picker("Primary Corporate Color", value=cur_v.get("brand_color", "#0F172A"))
                new_s = col_b2.color_picker("Secondary / Accent Color", value=cur_v.get("brand_secondary", "#2563EB"))
                
                if st.form_submit_button("Save Corporate Branding"):
                    cur_v["brand_color"] = new_p
                    cur_v["brand_secondary"] = new_s
                    if new_logo_file is not None:
                        cur_v["logo_url"] = process_image_upload(new_logo_file, cur_v.get("logo_url"))
                    save_data(db)
                    st.success("Brand logo and colors updated across all invoices, flyers & tickets!")
                    st.rerun()

        # FLYER BUILDER WITH LOGOS
        with t_flyers:
            st.markdown("#### 🎨 Custom Flyer Builder (Includes Brand Logo)")
            
            with st.form("flyer_builder_form"):
                e_title = st.text_input("Event Title*", placeholder="Annual Executive Business Expo")
                v_spaces_names = ["All Spaces / Full Venue"] + [s.get("name") for s in cur_v.get("spaces", [])]
                e_space = st.selectbox("Reserve/Lock Venue Space*", v_spaces_names)
                e_date = st.date_input("Scheduled Event Date*")
                e_price = st.number_input("Ticket Admission Price (BWP)", value=250.0)
                e_desc = st.text_area("Event Description")

                st.markdown("##### Poster Image Selection:")
                uploaded_flyer_file = st.file_uploader("Upload Poster Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
                preset_flyer = st.selectbox("Or Choose Stock Poster Image", SPACE_PRESETS)

                if st.form_submit_button("Publish Event & Generate Flyer"):
                    if e_title:
                        final_flyer = process_image_upload(uploaded_flyer_file, preset_flyer)
                        ev_id = f"EV-{len(db.get('events', []))+101}"
                        db.setdefault("events", []).append({
                            "event_id": ev_id,
                            "venue_id": cur_v.get("venue_id"),
                            "venue_name": cur_v.get("name"),
                            "space_name": e_space,
                            "title": e_title,
                            "date": str(e_date),
                            "price": e_price,
                            "description": e_desc,
                            "flyer_url": final_flyer
                        })
                        save_data(db)
                        st.success(f"Event '{e_title}' published!")
                        st.rerun()

            st.divider()
            pub_events = [e for e in db.get("events", []) if e.get("venue_id") == cur_v.get("venue_id")]
            if pub_events:
                for idx, ev in enumerate(pub_events):
                    with st.expander(f"📢 {ev.get('title')} ({ev.get('date')})"):
                        fc1, fc2 = st.columns([1, 2])
                        with fc1:
                            st.image(ev.get("flyer_url"), use_container_width=True)
                        with fc2:
                            st.write(f"<b>Venue:</b> {ev.get('venue_name')} | <b>Price:</b> BWP {ev.get('price'):,.2f}", unsafe_allow_html=True)
                            if st.button("Delete Event", key=f"del_ev_{idx}"):
                                db["events"].remove(ev)
                                save_data(db)
                                st.rerun()

        with t_bookings:
            st.markdown("#### Confirmed Date Bookings & Payment Records")
            bks = [b for b in db.get("bookings", []) if b.get("venue_id") == cur_v.get("venue_id")]
            if not bks:
                st.info("No confirmed date bookings recorded yet.")
            else:
                for b in bks:
                    with st.expander(f"Booking #{b.get('booking_id')} — {b.get('customer_name')} ({b.get('booking_date')})"):
                        st.write(f"**Space:** {b.get('space_name')} | **Status:** {b.get('status')}")
                        st.write(f"**Grand Total Paid:** **BWP {b.get('grand_total'):,.2f}**")

# ---------------------------------------------------------
# 6. MODULE 3: FACILITY SUPPORTER CONSOLE (VENDORS)
# ---------------------------------------------------------
elif user_role == "Facility Supporter Console (Vendors)":
    st.title("Facility Supporter Console")
    st.caption("Manage vendor profile, upload corporate logos, and configure item pricing.")
    st.divider()

    supporters = db.get("supporters", [])

    st.markdown("### 1. Vendor Profile, Logo & Branding")
    with st.form("supporter_reg_form"):
        col1, col2 = st.columns(2)
        s_name = col1.text_input("Business Trading Name*", placeholder="Kalahari Decor & Catering")
        s_cat = col1.selectbox("Service Category*", [
            "Catering & Cutlery Hire", 
            "Stage & Decor Design", 
            "Florist & Botanical Styling", 
            "Sound, Lighting & AV", 
            "Security & VIP Protection"
        ])
        s_person = col1.text_input("Contact Person*")
        s_email = col2.text_input("Contact Email*")
        s_phone = col2.text_input("Phone / WhatsApp*")
        s_color = col2.color_picker("Corporate Brand Color", "#1E293B")

        s_logo_file = st.file_uploader("Upload Vendor Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("Save Supporter Profile"):
            if s_name and s_email and s_phone:
                logo_url = process_image_upload(s_logo_file, DEFAULT_LOGO)
                existing = next((s for s in supporters if s.get("business_name") == s_name), None)
                if not existing:
                    new_sup = {
                        "supporter_id": f"sup_{len(supporters)+101}",
                        "business_name": s_name,
                        "category": s_cat,
                        "contact_person": s_person,
                        "email": s_email,
                        "phone": s_phone,
                        "brand_color": s_color,
                        "logo_url": logo_url,
                        "quotation_templates": []
                    }
                    db.setdefault("supporters", []).append(new_sup)
                else:
                    existing["brand_color"] = s_color
                    if s_logo_file is not None:
                        existing["logo_url"] = logo_url
                save_data(db)
                st.success("Supporter Profile & Logo Saved!")
                st.rerun()

    if supporters:
        st.divider()
        st.markdown("### 2. Configure Quotation Item Templates")
        sel_sup_name = st.selectbox("Select Active Supporter Account:", [s.get("business_name") for s in supporters])
        cur_sup = next(s for s in supporters if s.get("business_name") == sel_sup_name)

        with st.form("add_template_item_form"):
            t_col1, t_col2, t_col3 = st.columns(3)
            i_name = t_col1.text_input("Template Item Name")
            i_type = t_col2.selectbox("Unit Metric Type", ["Per Head / Guest", "Per Day", "Per Item / Set", "Flat Rate Shift"])
            i_price = t_col3.number_input("Unit Rate Price (BWP)", min_value=1.0, value=45.0)

            if st.form_submit_button("Add Item Template"):
                if i_name:
                    cur_sup.setdefault("quotation_templates", []).append({
                        "item_name": i_name,
                        "unit_type": i_type,
                        "unit_price": i_price
                    })
                    save_data(db)
                    st.success(f"Added '{i_name}'!")
                    st.rerun()

        st.divider()
        items = cur_sup.get("quotation_templates", [])
        for idx, it in enumerate(items):
            st.write(f"• **{it.get('item_name')}** — BWP {it.get('unit_price'):,.2f} ({it.get('unit_type')})")

# ---------------------------------------------------------
# 7. MODULE 4: TICKET SCANNER & GATE ACCESS
# ---------------------------------------------------------
elif user_role == "Ticket Scanner & Gate Access":
    st.title("Door Gate Ticket Access & Verification Console")
    st.caption("Scan or enter ticket hashes at event entrances to verify validity.")
    st.divider()

    tickets = db.get("tickets", [])
    verify_input = st.text_input("Enter Ticket Verification Hash or ID (e.g. HASH-XXXXXX or TKT-10001):")

    if st.button("Scan & Verify Ticket", type="primary"):
        if verify_input:
            search_str = verify_input.strip().upper()
            matched_tkt = next((t for t in tickets if t.get("verification_hash") == search_str or t.get("ticket_id") == search_str), None)

            if matched_tkt:
                if matched_tkt.get("status") == "VALID":
                    matched_tkt["status"] = "USED / SCANNED"
                    matched_tkt["scanned_at"] = str(datetime.datetime.now())
                    save_data(db)

                    v_logo = matched_tkt.get("venue_logo", DEFAULT_LOGO)
                    v_color = matched_tkt.get("brand_color", "#059669")

                    st.markdown(f"""
                    <div style="background-color: #D1FAE5; border: 2px solid #059669; padding: 1.5rem; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h2 style="color: #065F46 !important; margin: 0;">✅ ACCESS GRANTED — VALID TICKET</h2>
                            <img src="{v_logo}" class="logo-img">
                        </div>
                        <hr style="border-color: #A7F3D0;">
                        <p style="color: #064E3B !important;">
                            <b>Event:</b> {matched_tkt.get('event_title')}<br>
                            <b>Guest Holder:</b> {matched_tkt.get('buyer')}<br>
                            <b>Admit Quantity:</b> {matched_tkt.get('qty')} Person(s)<br>
                            <b>Hash:</b> {matched_tkt.get('verification_hash')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ INVALID / ALREADY REDEEMED: Ticket has already been scanned.")
            else:
                st.error("❌ INVALID TICKET: Verification hash not found.")

# ---------------------------------------------------------
# 8. MODULE 5: PLATFORM ADMIN
# ---------------------------------------------------------
elif user_role == "Platform Admin / Master Ledger":
    st.title("Master Executive Control Panel")
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Facilities", len(db.get("venues", [])))
    m2.metric("Vendors", len(db.get("supporters", [])))
    m3.metric("Bookings", len(db.get("bookings", [])))
    m4.metric("Tickets", len(db.get("tickets", [])))
    st.json(db)
