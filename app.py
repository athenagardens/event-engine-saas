import streamlit as st
import json
import os
import datetime

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
# 2. APP CONFIGURATION & ENTERPRISE STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Central Event, Venue & Booking SaaS Platform",
    page_icon="🎪",
    layout="wide"
)

def inject_enterprise_styles():
    st.markdown("""
        <style>
            .main { background-color: #F8FAFC; font-family: -apple-system, sans-serif; }
            h1, h2, h3, h4 { color: #0F172A !important; font-weight: 700 !important; }
            [data-testid="stSidebar"] { background-color: #0F172A !important; }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] p { color: #F1F5F9 !important; }
            
            .invoice-box {
                background: #FFFFFF; padding: 2rem; border-radius: 12px;
                border: 1px solid #CBD5E1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }
            .profile-card {
                background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
                padding: 1.5rem; border-radius: 10px; color: #FFF !important; margin-bottom: 1.5rem;
            }
            .profile-card h3, .profile-card p { color: #FFF !important; }
        </style>
    """, unsafe_allow_html=True)

inject_enterprise_styles()

# ---------------------------------------------------------
# 3. SIDEBAR NAVIGATION & UTILITIES
# ---------------------------------------------------------
st.sidebar.markdown("## 🎪 Event Engine SaaS")
st.sidebar.caption("Self-Service Venue, Supplier & Event Portal")
st.sidebar.divider()

user_role = st.sidebar.radio(
    "Select Console Portal:",
    [
        "Public Portal (Book Venues & Buy Tickets)",
        "Facility Owner Portal",
        "Facility Supporter Portal (Vendors)",
        "Platform Admin / Master Ledger"
    ]
)

st.sidebar.divider()
with st.sidebar.expander("⚙️ System Utilities"):
    if st.button("Purge & Reset System Database", type="primary", use_container_width=True):
        db = {"venues": [], "supporters": [], "events": [], "bookings": [], "tickets": []}
        save_data(db)
        st.success("Database purged successfully.")
        st.rerun()

# ---------------------------------------------------------
# 4. MODULE 1: PUBLIC PORTAL (AUTOMATED BOOKING & TICKETING)
# ---------------------------------------------------------
if user_role == "Public Portal (Book Venues & Buy Tickets)":
    st.title("🎟️ Central Venue Booking & Public Ticketing Portal")
    st.caption("Browse events, reserve facility spaces, customize vendor packages, and generate instant paid bookings.")
    st.divider()

    public_tab1, public_tab2 = st.tabs(["🏛️ Book a Venue & Request Instant Quote", "🎫 Buy Event Tickets"])

    # -----------------------------------------------------
    # TAB A: INSTANT VENUE & SUPPLIER QUOTATION ENGINE
    # -----------------------------------------------------
    with public_tab1:
        st.markdown("### 📅 Automated Venue & Services Booking System")
        st.info("No phone calls required! Select your date, space, and optional services to calculate a complete quotation, lock dates, and complete payment.")

        venues_list = db.get("venues", [])
        if not venues_list:
            st.warning("No facilities have been registered on the platform yet.")
        else:
            venue_names = [v.get("name", "Unnamed Facility") for v in venues_list]
            sel_v_name = st.selectbox("1. Select Preferred Facility / Venue:", venue_names)
            sel_venue = next(v for v in venues_list if v.get("name") == sel_v_name)

            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                st.image(sel_venue.get("flyer_image_url", "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800"), use_container_width=True)
            with col_v2:
                st.markdown(f"#### **{sel_venue.get('name')}**")
                st.write(f"📍 **Address:** {sel_venue.get('address')}")
                st.write(f"🏢 **Category:** {sel_venue.get('type')}")
                st.write(f"👥 **Max Venue Capacity:** {sel_venue.get('max_capacity'):,} Guests")

            spaces = sel_venue.get("spaces", [])
            if not spaces:
                st.warning("This venue has not listed any hire sub-spaces yet.")
            else:
                st.divider()
                st.markdown("### 2. Select Space & Reserve Dates")
                
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

                # Check for Date Locking Conflicts
                existing_bookings = db.get("bookings", [])
                date_str = str(booking_date)
                is_locked = any(
                    b.get("venue_id") == sel_venue.get("venue_id") and 
                    b.get("space_name") == sel_sp_name and 
                    b.get("booking_date") == date_str and 
                    b.get("status") == "Confirmed / Paid"
                    for b in existing_bookings
                )

                if is_locked:
                    st.error(f"❌ '{sel_sp_name}' is ALREADY LOCKED and booked on {date_str}. Please choose another date or space.")
                else:
                    st.success(f"✅ '{sel_sp_name}' is AVAILABLE on {date_str}!")

                    st.divider()
                    st.markdown("### 3. Customize Add-On Services (Supporters / Vendors)")
                    st.caption("Select items from pre-configured supplier templates to automatically compute your final bill.")

                    selected_addons = []
                    addons_total = 0.0

                    supporters = db.get("supporters", [])
                    if supporters:
                        for sup in supporters:
                            templates = sup.get("quotation_templates", [])
                            if templates:
                                with st.expander(f"🤝 Add Services from {sup.get('business_name')} ({sup.get('category')})"):
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
                                                "item": t.get("item_name"),
                                                "qty": qty,
                                                "unit_price": t.get("unit_price"),
                                                "total": cost
                                            })
                    else:
                        st.info("No supplier add-ons currently selected.")

                    # --- LIVE TOTAL & CHECKOUT INVOICE ---
                    st.divider()
                    grand_total = space_total + addons_total

                    st.markdown(f"### 4. Instant Itemized Quotation Total")
                    
                    st.markdown(f"""
                    <div class="invoice-box">
                        <h3>🧾 Instant Automated Quote</h3>
                        <hr>
                        <p><b>Facility:</b> {sel_venue.get('name')} | <b>Space:</b> {sel_sp_name}</p>
                        <p><b>Event Date:</b> {date_str} ({booking_days} day/s)</p>
                        <p><b>Base Venue Hire:</b> BWP {space_total:,.2f}</p>
                        <p><b>Supplier Add-ons Total:</b> BWP {addons_total:,.2f}</p>
                        <hr>
                        <h2 style="color: #2563EB !important;">Grand Total Due: BWP {grand_total:,.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("#### Customer Details & Instant Lock Payment")
                    with st.form("public_booking_form"):
                        c_name = st.text_input("Full Name / Company Name*")
                        c_email = st.text_input("Email Address (for Invoice & Receipt)*")
                        c_phone = st.text_input("Phone / WhatsApp Number*")
                        c_pay_method = st.selectbox("Payment Gateway", ["Card Payment (Visa/Mastercard)", "EFT Bank Transfer", "Mobile Money / Orange Money"])

                        pay_btn = st.form_submit_button("Pay Now & Lock Dates Immediately", use_container_width=True)

                        if pay_btn:
                            if c_name and c_email and c_phone:
                                new_booking = {
                                    "booking_id": f"bk_{len(existing_bookings)+101}",
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
                                st.balloons()
                                st.success("🎉 Payment Successful! Dates are officially LOCKED. Digital tax invoice generated below.")
                                st.rerun()
                            else:
                                st.error("Please fill in customer contact details.")

    # -----------------------------------------------------
    # TAB B: EVENT TICKETING SHOP
    # -----------------------------------------------------
    with public_tab2:
        st.markdown("### 🎫 Buy Public Event Tickets")
        events = db.get("events", [])
        if not events:
            st.info("No upcoming public ticketed events hosted at this time.")
        else:
            for ev in events:
                with st.container():
                    col_e1, col_e2 = st.columns([1, 2])
                    with col_e1:
                        st.image(ev.get("flyer_url", "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800"), use_container_width=True)
                    with col_e2:
                        st.markdown(f"### {ev.get('title')}")
                        st.write(f"📍 **Venue:** {ev.get('venue_name')} | 📅 **Date:** {ev.get('date')}")
                        st.write(f"📝 {ev.get('description')}")
                        st.markdown(f"🎟️ **Ticket Price:** BWP {ev.get('price', 0):,.2f}")

                        with st.form(f"ticket_form_{ev.get('event_id')}"):
                            t_qty = st.number_input("Quantity", min_value=1, value=1)
                            t_buyer = st.text_input("Your Full Name")
                            t_email = st.text_input("Your Email (Ticket Delivery)")
                            
                            buy_t_btn = st.form_submit_button("Buy Ticket Now")
                            if buy_t_btn:
                                if t_buyer and t_email:
                                    tot_t = t_qty * ev.get('price', 0)
                                    db.setdefault("tickets", []).append({
                                        "ticket_id": f"tkt_{len(db.get('tickets', []))+1001}",
                                        "event_id": ev.get('event_id'),
                                        "event_title": ev.get('title'),
                                        "buyer": t_buyer,
                                        "email": t_email,
                                        "qty": t_qty,
                                        "total_paid": tot_t,
                                        "status": "Paid / Issued"
                                    })
                                    save_data(db)
                                    st.success(f"🎟️ {t_qty} Ticket(s) issued! Sent to {t_email}")
                                else:
                                    st.error("Please provide buyer name and email.")
                    st.divider()

# ---------------------------------------------------------
# 5. MODULE 2: FACILITY OWNER PORTAL (FLYER BUILDER & MANAGEMENT)
# ---------------------------------------------------------
elif user_role == "Facility Owner Portal":
    st.title("🏢 Facility Owner Management Console")
    st.caption("Manage facility sub-spaces, publish ticketed events with flyer templates, and view locked date bookings.")
    st.divider()

    venues = db.get("venues", [])
    if not venues:
        st.info("👋 Welcome! Please register your facility profile to start.")
        with st.form("fac_reg_main"):
            st.markdown("### 🏛️ Primary Facility Onboarding")
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

            f_img = st.text_input("Cover Image URL", value="https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800")
            
            if st.form_submit_button("Register Facility"):
                if f_name and f_email and f_phone and f_address and f_tax:
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
                        "flyer_image_url": f_img,
                        "spaces": []
                    })
                    save_data(db)
                    st.success("Facility Registered!")
                    st.rerun()
    else:
        cur_v = venues[0]
        st.markdown(f"""
            <div class="profile-card">
                <h3>🏛️ {cur_v.get('name')}</h3>
                <p>📍 {cur_v.get('address')} | 👥 Capacity: {cur_v.get('max_capacity'):,} | Tax ID: {cur_v.get('tax_id')}</p>
            </div>
        """, unsafe_allow_html=True)

        t_spaces, t_flyers, t_bookings = st.tabs([
            "Configured Sub-Spaces", 
            "🎨 Event Publisher & Flyer Builder", 
            "📋 Locked Date Bookings & Invoices"
        ])

        with t_spaces:
            st.markdown("#### Add Hire Spaces")
            with st.form("add_sp"):
                c1, c2, c3 = st.columns(3)
                s_name = c1.text_input("Space Name (e.g. Hall A)")
                s_cap = c2.number_input("Capacity", value=200)
                s_rate = c3.number_input("Daily Hire Price (BWP)", value=2500.0)
                if st.form_submit_button("Add Space"):
                    cur_v.setdefault("spaces", []).append({"name": s_name, "capacity": s_cap, "daily_rate": s_rate})
                    save_data(db)
                    st.success("Space added!")
                    st.rerun()

            st.divider()
            for sp in cur_v.get("spaces", []):
                st.write(f"• **{sp.get('name')}** | Cap: {sp.get('capacity')} | BWP {sp.get('daily_rate'):,.2f}/day")

        # EVENT PUBLISHER & FLYER BUILDER
        with t_flyers:
            st.markdown("#### 🎨 Create Ticketed Event & Build Flyer")
            with st.form("flyer_builder_form"):
                e_title = st.text_input("Event Title", placeholder="Annual Music Festival & Expo")
                e_date = st.date_input("Event Date")
                e_price = st.number_input("Ticket Price (BWP)", value=150.0)
                e_desc = st.text_area("Event Description / Highlights")

                st.markdown("##### Choose Flyer Poster Background Template:")
                flyer_template = st.radio(
                    "Select Visual Template",
                    [
                        "Concert / Festival Poster",
                        "Corporate Conference Poster",
                        "Gala / VIP Night Poster"
                    ]
                )

                # Pre-defined professional images corresponding to templates
                img_map = {
                    "Concert / Festival Poster": "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800",
                    "Corporate Conference Poster": "https://images.unsplash.com/photo-1511578314322-379afb476865?w=800",
                    "Gala / VIP Night Poster": "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=800"
                }

                if st.form_submit_button("Publish Event & Generate Tickets"):
                    if e_title:
                        db.setdefault("events", []).append({
                            "event_id": f"ev_{len(db.get('events', []))+101}",
                            "venue_id": cur_v.get("venue_id"),
                            "venue_name": cur_v.get("name"),
                            "title": e_title,
                            "date": str(e_date),
                            "price": e_price,
                            "description": e_desc,
                            "flyer_url": img_map[flyer_template]
                        })
                        save_data(db)
                        st.success(f"🎉 Event '{e_title}' published to Public Ticketing Portal!")
                        st.rerun()

        with t_bookings:
            st.markdown("#### Locked Customer Bookings & Generated Invoices")
            bks = [b for b in db.get("bookings", []) if b.get("venue_id") == cur_v.get("venue_id")]
            if not bks:
                st.info("No booked/locked dates yet.")
            else:
                for b in bks:
                    with st.expander(f"📌 Booking #{b.get('booking_id')} — {b.get('customer_name')} ({b.get('booking_date')})"):
                        st.write(f"**Space:** {b.get('space_name')} | **Status:** {b.get('status')}")
                        st.write(f"**Customer Email:** {b.get('customer_email')} | **Phone:** {b.get('customer_phone')}")
                        st.write(f"**Venue Fee:** BWP {b.get('venue_cost'):,.2f} | **Addons Fee:** BWP {b.get('addons_cost'):,.2f}")
                        st.write(f"**Total Paid:** **BWP {b.get('grand_total'):,.2f}**")

# ---------------------------------------------------------
# 6. MODULE 3: FACILITY SUPPORTER PORTAL (VENDOR TEMPLATES)
# ---------------------------------------------------------
elif user_role == "Facility Supporter Portal (Vendors)":
    st.title("🛠️ Facility Supporter & Vendor Console")
    st.caption("Configure industry-standard quotation templates so clients can instantly order cutlery, decor, audio-visual, and security online.")
    st.divider()

    supporters = db.get("supporters", [])

    st.markdown("### 1. Vendor Profile Onboarding")
    with st.form("supporter_reg_form"):
        col1, col2 = st.columns(2)
        s_name = col1.text_input("Business / Trading Name*", placeholder="Kalahari Decor & Catering")
        s_cat = col1.selectbox("Category*", [
            "Catering & Cutlery Hire", 
            "Stage & Decor Design", 
            "Florist & Botanical Styling", 
            "Sound, Lighting & AV", 
            "Security & VIP Protection"
        ])
        s_person = col1.text_input("Contact Person*")
        s_email = col2.text_input("Contact Email*")
        s_phone = col2.text_input("Phone / WhatsApp*")
        s_area = col2.text_input("Coverage Area*", placeholder="Gaborone & Greater Region")

        if st.form_submit_button("Save / Update Supporter Profile"):
            if s_name and s_email and s_phone:
                existing = next((s for s in supporters if s.get("business_name") == s_name), None)
                if not existing:
                    new_sup = {
                        "supporter_id": f"sup_{len(supporters)+101}",
                        "business_name": s_name,
                        "category": s_cat,
                        "contact_person": s_person,
                        "email": s_email,
                        "phone": s_phone,
                        "service_area": s_area,
                        "quotation_templates": []
                    }
                    db.setdefault("supporters", []).append(new_sup)
                save_data(db)
                st.success("Supporter Profile Saved!")
                st.rerun()

    if supporters:
        st.divider()
        st.markdown("### 2. Configure Industry Standard Quotation Item Templates")
        st.caption("Benchmark templates (e.g. Cutlery per head, Floral stage centerpieces, Security officers per shift).")

        sel_sup_name = st.selectbox("Select Your Supporter Account:", [s.get("business_name") for s in supporters])
        cur_sup = next(s for s in supporters if s.get("business_name") == sel_sup_name)

        with st.form("add_template_item_form"):
            st.markdown(f"#### Add Template Price Item to `{cur_sup.get('business_name')}`")
            t_col1, t_col2, t_col3 = st.columns(3)
            i_name = t_col1.text_input("Item Name", placeholder="e.g. Premium VIP Cutlery & Dinner Set")
            i_type = t_col2.selectbox("Unit Unit Type", ["Per Head / Guest", "Per Day", "Per Item / Set", "Flat Rate"])
            i_price = t_col3.number_input("Unit Price (BWP)", min_value=1.0, value=45.0)

            if st.form_submit_button("Add Template Item"):
                if i_name:
                    cur_sup.setdefault("quotation_templates", []).append({
                        "item_name": i_name,
                        "unit_type": i_type,
                        "unit_price": i_price
                    })
                    save_data(db)
                    st.success(f"Added '{i_name}' to quotation template library!")
                    st.rerun()

        st.markdown("##### Current Quotation Template Items")
        items = cur_sup.get("quotation_templates", [])
        if items:
            for it in items:
                st.write(f"• **{it.get('item_name')}** — BWP {it.get('unit_price'):,.2f} ({it.get('unit_type')})")
        else:
            st.info("No template pricing items added yet.")

# ---------------------------------------------------------
# 7. MODULE 4: PLATFORM MASTER LEDGER & AUDIT
# ---------------------------------------------------------
elif user_role == "Platform Admin / Master Ledger":
    st.title("📊 Master Executive Control Panel")
    st.divider()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Registered Facilities", len(db.get("venues", [])))
    m2.metric("Registered Vendors", len(db.get("supporters", [])))
    m3.metric("Confirmed Bookings", len(db.get("bookings", [])))
    m4.metric("Issued Tickets", len(db.get("tickets", [])))

    st.markdown("---")
    st.markdown("### 📑 System Wide Master Records")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Venue Bookings Ledger", "Ticket Sales Ledger", "Raw Database"])

    with admin_tab1:
        st.json(db.get("bookings", []))

    with admin_tab2:
        st.json(db.get("tickets", []))

    with admin_tab3:
        st.json(db)
