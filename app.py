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
    return {"venues": [], "supporters": [], "events": [], "bookings": [], "tickets": [], "vendor_invoices": []}

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
                background: #FFFFFF; padding: 2rem; border-radius: 8px;
                border: 1px solid #CBD5E1; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin-bottom: 1.5rem;
            }
            .profile-card {
                padding: 1.8rem; border-radius: 8px; color: #FFFFFF !important; margin-bottom: 1.5rem;
            }
            .logo-img {
                max-height: 60px; max-width: 180px; object-fit: contain;
            }
            .item-card {
                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;
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
st.sidebar.caption("Venue Operations, Split Ticketing & Vendor Invoicing")
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
        db = {"venues": [], "supporters": [], "events": [], "bookings": [], "tickets": [], "vendor_invoices": []}
        save_data(db)
        st.session_state.clear()
        st.success("Database purged successfully.")
        st.rerun()

# ---------------------------------------------------------
# 4. MODULE 1: PUBLIC PORTAL (SPLIT INVOICING)
# ---------------------------------------------------------
if user_role == "Public Portal (Bookings & Ticketing)":
    st.title("Central Venue Booking & Public Ticketing Console")
    st.caption("Reserve enterprise facilities and customize approved vendor packages with separate billing.")
    st.divider()

    public_tab1, public_tab2 = st.tabs(["Book Venue & Vendor Packages", "Public Event Ticket Shop"])

    # --- TAB A: VENUE & VENDOR BOOKING WITH SEPARATE INVOICES ---
    with public_tab1:
        st.markdown("### Automated Venue & Service Reservation")

        venues_list = db.get("venues", [])
        if not venues_list:
            st.warning("No facility profiles are currently published on the gateway.")
        else:
            venue_names = [v.get("name", "Unnamed Facility") for v in venues_list]
            sel_v_name = st.selectbox("1. Select Facility / Venue:", venue_names)
            sel_venue = next(v for v in venues_list if v.get("name") == sel_v_name)

            v_brand_color = sel_venue.get("brand_color", "#0F172A")
            v_logo = sel_venue.get("logo_url", DEFAULT_LOGO)
            v_whatsapp = sel_venue.get("whatsapp_no", "Not Specified")

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
                            <b>Max Guest Occupancy:</b> {sel_venue.get('max_capacity'):,} Guests<br>
                            <b>Venue POP WhatsApp Line:</b> {v_whatsapp}
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            spaces = sel_venue.get("spaces", [])
            if not spaces:
                st.warning("This venue has not listed sub-spaces for hire.")
            else:
                st.divider()
                st.markdown("### 2. Select Space & Reserve Date")

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
                date_str = str(booking_date)

                is_locked = any(
                    b.get("venue_id") == sel_venue.get("venue_id") and 
                    b.get("space_name") == sel_sp_name and 
                    b.get("booking_date") == date_str and 
                    b.get("status") in ["Confirmed / Paid", "Pending POP / Verification"]
                    for b in db.get("bookings", [])
                )

                if is_locked:
                    st.error(f"❌ DATE UNAVAILABLE: '{sel_sp_name}' is already reserved/pending on {date_str}.")
                else:
                    st.success(f"✅ DATE AVAILABLE: '{sel_sp_name}' is open on {date_str}.")

                    st.divider()
                    st.markdown("### 3. Add Approved Service Provider Packages")
                    st.info(f"💡 Showing vendors approved specifically by {sel_venue.get('name')}. Services are billed directly by each provider.")

                    selected_vendor_orders = {}
                    
                    # FILTER VENDORS APPROVED BY THIS SPECIFIC FACILITY OWNER
                    approved_ids = sel_venue.get("approved_supporter_ids", [])
                    all_supporters = db.get("supporters", [])
                    supporters = [s for s in all_supporters if s.get("supporter_id") in approved_ids]

                    if supporters:
                        for sup in supporters:
                            templates = sup.get("quotation_templates", [])
                            if templates:
                                with st.expander(f"Add Services: {sup.get('business_name')} ({sup.get('category')})"):
                                    st.image(sup.get("logo_url", DEFAULT_LOGO), width=100)
                                    sup_items = []
                                    sup_total = 0.0

                                    for t in templates:
                                        t_col1, t_col2 = st.columns([1, 3])
                                        with t_col1:
                                            if t.get("image_url"):
                                                st.image(t.get("image_url"), use_container_width=True)
                                        with t_col2:
                                            st.markdown(f"**{t.get('item_name')}** — BWP {t.get('unit_price'):,.2f} / {t.get('unit_type')}")
                                            if t.get("description"):
                                                st.caption(t.get("description"))
                                            
                                            item_key = f"{sup.get('supporter_id')}_{t.get('item_name')}"
                                            qty = st.number_input(
                                                "Select Quantity", min_value=0, value=0, key=item_key
                                            )
                                            if qty > 0:
                                                cost = qty * t.get("unit_price")
                                                sup_total += cost
                                                sup_items.append({
                                                    "item_name": t.get("item_name"),
                                                    "unit_type": t.get("unit_type"),
                                                    "qty": qty,
                                                    "unit_price": t.get("unit_price"),
                                                    "subtotal": cost
                                                })
                                        st.divider()

                                    if sup_items:
                                        selected_vendor_orders[sup.get("supporter_id")] = {
                                            "supporter": sup,
                                            "items": sup_items,
                                            "total": sup_total
                                        }
                    else:
                        st.info(f"No approved vendor packages currently assigned to {sel_venue.get('name')}.")

                    st.divider()
                    st.markdown("### 4. Separate Itemized Invoices / Quotations")

                    # INVOICE 1: VENUE OWNER
                    st.markdown(f"""
                    <div class="invoice-box" style="border-top: 5px solid {v_brand_color};">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <img src="{v_logo}" class="logo-img">
                                <h3>INVOICE A: VENUE HIRE ({sel_venue.get('name')})</h3>
                            </div>
                            <div style="text-align: right;">
                                <h4>Total: BWP {space_total:,.2f}</h4>
                                <p style="color: #D97706; font-weight: bold;">Status: Pending POP Submission</p>
                            </div>
                        </div>
                        <p><b>Hire Space:</b> {sel_sp_name} ({booking_days} day/s) @ BWP {sel_space.get('daily_rate'):,.2f}/day</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # INVOICES 2+: INDIVIDUAL VENDORS
                    for sup_id, v_data in selected_vendor_orders.items():
                        sup_info = v_data["supporter"]
                        s_color = sup_info.get("brand_color", "#1E293B")
                        s_logo = sup_info.get("logo_url", DEFAULT_LOGO)

                        st.markdown(f"""
                        <div class="invoice-box" style="border-top: 5px solid {s_color};">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <img src="{s_logo}" class="logo-img">
                                    <h3>INVOICE: VENDOR SERVICE ({sup_info.get('business_name')})</h3>
                                    <p style="font-size: 0.85rem; color: #64748B;">Category: {sup_info.get('category')} | WhatsApp: {sup_info.get('phone')}</p>
                                </div>
                                <div style="text-align: right;">
                                    <h4 style="color: {s_color};">Total: BWP {v_data['total']:,.2f}</h4>
                                    <p style="color: #D97706; font-weight: bold;">Status: Pending Direct POP</p>
                                </div>
                            </div>
                            <table style="width:100%; border-collapse: collapse; font-size: 0.85rem;">
                                <tr style="background-color: #F8FAFC;">
                                    <th style="padding: 6px; text-align: left;">Service Item</th>
                                    <th style="padding: 6px;">Qty</th>
                                    <th style="padding: 6px;">Rate</th>
                                    <th style="padding: 6px; text-align: right;">Subtotal</th>
                                </tr>
                                {"".join([f"<tr><td style='padding:6px;'>{i['item_name']}</td><td style='padding:6px; text-align:center;'>{i['qty']}</td><td style='padding:6px;'>BWP {i['unit_price']:,.2f}</td><td style='padding:6px; text-align:right;'>BWP {i['subtotal']:,.2f}</td></tr>" for i in v_data['items']])}
                            </table>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("#### Confirm Booking & Generate Separate POP Requests")
                    with st.form("split_booking_form"):
                        c_name = st.text_input("Full Name / Company Name*")
                        c_email = st.text_input("Email Address*")
                        c_phone = st.text_input("Phone / WhatsApp Number*")
                        c_pay_method = st.selectbox("Preferred Payment Method", [
                            "eWallet / First National Bank",
                            "Orange Money",
                            "Pay2Cell / Absa",
                            "Direct Bank Deposit / Transfer"
                        ])

                        if st.form_submit_button("Submit Reservation & Issue Invoices", use_container_width=True):
                            if c_name and c_email and c_phone:
                                b_id = f"BK-{len(db.get('bookings', []))+1001}"
                                
                                # Save Master Venue Booking
                                new_booking = {
                                    "booking_id": b_id,
                                    "venue_id": sel_venue.get("venue_id"),
                                    "venue_name": sel_venue.get("name"),
                                    "space_name": sel_sp_name,
                                    "customer_name": c_name,
                                    "customer_email": c_email,
                                    "customer_phone": c_phone,
                                    "booking_date": date_str,
                                    "days": booking_days,
                                    "venue_cost": space_total,
                                    "payment_method": c_pay_method,
                                    "status": "Pending POP / Verification",
                                    "pop_reference": None,
                                    "created_at": str(datetime.date.today())
                                }
                                db.setdefault("bookings", []).append(new_booking)

                                # Save Individual Vendor Invoices
                                for sup_id, v_data in selected_vendor_orders.items():
                                    v_inv_id = f"VINV-{len(db.get('vendor_invoices', []))+5001}"
                                    sup_info = v_data["supporter"]
                                    db.setdefault("vendor_invoices", []).append({
                                        "vendor_invoice_id": v_inv_id,
                                        "parent_booking_id": b_id,
                                        "supporter_id": sup_id,
                                        "supporter_name": sup_info.get("business_name"),
                                        "venue_name": sel_venue.get("name"),
                                        "customer_name": c_name,
                                        "customer_email": c_email,
                                        "customer_phone": c_phone,
                                        "event_date": date_str,
                                        "items": v_data["items"],
                                        "total_amount": v_data["total"],
                                        "payment_method": c_pay_method,
                                        "status": "Pending POP",
                                        "pop_reference": None,
                                        "created_at": str(datetime.date.today())
                                    })

                                save_data(db)
                                st.success(f"Reservation Request #{b_id} Created! Please submit POPs directly to the venue and vendor WhatsApp lines.")
                                st.rerun()
                            else:
                                st.error("Please complete all required customer fields.")

    # --- TAB B: EVENT TICKET SHOP ---
    with public_tab2:
        st.markdown("### Public Event Ticket Shop")
        events = db.get("events", [])
        if not events:
            st.info("No upcoming public ticketed events hosted at this time.")
        else:
            for ev in events:
                matching_venue = next((v for v in db.get("venues", []) if v.get("venue_id") == ev.get("venue_id")), {})
                v_logo = matching_venue.get("logo_url", DEFAULT_LOGO)
                v_whatsapp = matching_venue.get("whatsapp_no", "Not Specified")

                with st.container():
                    col_e1, col_e2 = st.columns([1, 2])
                    with col_e1:
                        st.image(ev.get("flyer_url", SPACE_PRESETS[0]), use_container_width=True)
                    with col_e2:
                        st.markdown(f"### {ev.get('title')}")
                        st.write(f"<b>Venue:</b> {ev.get('venue_name')} | <b>Date:</b> {ev.get('date')} | <b>Price:</b> BWP {ev.get('price', 0):,.2f}", unsafe_allow_html=True)
                        st.write(f"<b>WhatsApp POP Submission:</b> {v_whatsapp}", unsafe_allow_html=True)

                        with st.form(f"ticket_form_{ev.get('event_id')}"):
                            t_qty = st.number_input("Quantity", min_value=1, value=1)
                            t_buyer = st.text_input("Buyer Full Name*")
                            t_email = st.text_input("Delivery Email*")
                            t_pay_method = st.selectbox("Payment Method", ["eWallet", "Orange Money", "Pay2Cell", "Direct Bank Deposit"])
                            
                            if st.form_submit_button("Request Ticket (Pending POP)"):
                                if t_buyer and t_email:
                                    t_id = f"TKT-{len(db.get('tickets', []))+10001}"
                                    sec_hash = hashlib.sha256(f"{t_id}-{t_email}-{datetime.datetime.now()}".encode()).hexdigest()[:12].upper()
                                    db.setdefault("tickets", []).append({
                                        "ticket_id": t_id,
                                        "verification_hash": f"HASH-{sec_hash}",
                                        "event_id": ev.get('event_id'),
                                        "event_title": ev.get('title'),
                                        "venue_name": ev.get('venue_name'),
                                        "venue_id": ev.get('venue_id'),
                                        "venue_logo": v_logo,
                                        "buyer": t_buyer,
                                        "email": t_email,
                                        "qty": t_qty,
                                        "total_paid": t_qty * ev.get('price', 0),
                                        "payment_method": t_pay_method,
                                        "status": "Pending POP / Unverified",
                                        "pop_reference": None
                                    })
                                    save_data(db)
                                    st.warning(f"Ticket Reserved! Send Proof of Payment to WhatsApp {v_whatsapp} referencing Ticket ID {t_id}.")
                                else:
                                    st.error("Please complete buyer details.")
                    st.divider()

# ---------------------------------------------------------
# 5. MODULE 2: FACILITY OWNER CONSOLE & REPORTING
# ---------------------------------------------------------
elif user_role == "Facility Owner Console":
    st.title("Facility Owner Console & Curation")
    st.caption("Manage spaces, select approved facility supporters, confirm bookings, and view earnings reports.")
    st.divider()

    venues = db.get("venues", [])
    if not venues:
        st.info("👋 Welcome! Please complete initial facility registration.")
        with st.form("fac_reg_main"):
            st.markdown("### Primary Facility Profile Setup")
            f_name = st.text_input("Facility Name*")
            f_type = st.selectbox("Type", ["Convention Center", "Hotel Ballroom", "Outdoor Arena", "Community Hall"])
            f_email = st.text_input("Manager Email*")
            f_phone = st.text_input("Manager Phone*")
            f_whatsapp = st.text_input("WhatsApp Number for POP Reception*")
            f_address = st.text_input("Physical Address*")
            f_cap = st.number_input("Max Capacity", value=1000)
            f_tax = st.text_input("Tax / CIPA Registration ID*")
            f_bank = st.text_area("Bank Details & Payment Instructions*")
            f_logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("Register Facility Profile"):
                if f_name and f_email and f_phone and f_whatsapp:
                    logo_url = process_image_upload(f_logo_file, DEFAULT_LOGO)
                    db.setdefault("venues", []).append({
                        "venue_id": f"v_{len(venues)+101}",
                        "name": f_name,
                        "type": f_type,
                        "email": f_email,
                        "phone": f_phone,
                        "whatsapp_no": f_whatsapp,
                        "address": f_address,
                        "max_capacity": f_cap,
                        "tax_id": f_tax,
                        "bank_details": f_bank,
                        "brand_color": "#0F172A",
                        "brand_secondary": "#2563EB",
                        "logo_url": logo_url,
                        "flyer_image_url": SPACE_PRESETS[0],
                        "spaces": [],
                        "approved_supporter_ids": []
                    })
                    save_data(db)
                    st.success("Facility Registered Successfully!")
                    st.rerun()
    else:
        cur_v = venues[0]
        v_logo = cur_v.get("logo_url", DEFAULT_LOGO)

        st.markdown(f"""
            <div class="profile-card" style="background: #0F172A;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #FFFFFF !important; margin: 0;">🏛️ {cur_v.get('name')}</h2>
                        <p style="color: #CBD5E1 !important; margin-top: 4px;">
                            📍 {cur_v.get('address')} | 💬 WhatsApp POP: {cur_v.get('whatsapp_no')}
                        </p>
                    </div>
                    <img src="{v_logo}" class="logo-img" style="background: white; padding: 4px; border-radius: 6px;">
                </div>
            </div>
        """, unsafe_allow_html=True)

        t_spaces, t_vendors, t_brand, t_verify, t_reports = st.tabs([
            "Configured Sub-Spaces", 
            "🤝 Approved Vendor Network",
            "Profile & WhatsApp Setup",
            "✅ Verify POPs & Confirm Bookings",
            "📊 Facility Financial Reports"
        ])

        # SUB-SPACES
        with t_spaces:
            with st.form("add_sp"):
                s_name = st.text_input("Sub-Space Name")
                s_cap = st.number_input("Capacity", value=200)
                s_rate = st.number_input("Daily Rate (BWP)", value=3000.0)
                sp_img_file = st.file_uploader("Space Photo", type=["png", "jpg", "jpeg"])

                if st.form_submit_button("Add Hire Space"):
                    if s_name:
                        img_final = process_image_upload(sp_img_file, SPACE_PRESETS[0])
                        cur_v.setdefault("spaces", []).append({"name": s_name, "capacity": s_cap, "daily_rate": s_rate, "image_url": img_final})
                        save_data(db)
                        st.success("Sub-space saved!")
                        st.rerun()

            st.divider()
            for sp in cur_v.get("spaces", []):
                st.write(f"• **{sp.get('name')}** — Capacity: {sp.get('capacity')} | BWP {sp.get('daily_rate'):,.2f}/day")

        # APPROVED VENDOR SELECTION
        with t_vendors:
            st.markdown("#### Select & Approve Global Vendors for Your Facility")
            st.caption("Check the vendors you wish to allow to offer catering, decor, AV, or security packages to clients booking your venue.")

            all_global_supporters = db.get("supporters", [])
            current_approved_ids = set(cur_v.get("approved_supporter_ids", []))

            if not all_global_supporters:
                st.info("No global vendors have registered on the platform yet.")
            else:
                with st.form("vendor_curation_form"):
                    updated_approved_ids = []
                    for sup in all_global_supporters:
                        is_checked = sup.get("supporter_id") in current_approved_ids
                        col_s1, col_s2 = st.columns([1, 4])
                        with col_s1:
                            st.image(sup.get("logo_url", DEFAULT_LOGO), width=80)
                        with col_s2:
                            chk = st.checkbox(
                                f"**{sup.get('business_name')}** (`{sup.get('category')}`)",
                                value=is_checked,
                                key=f"vendor_chk_{sup.get('supporter_id')}"
                            )
                            st.caption(f"Contact: {sup.get('contact_person')} ({sup.get('phone')})")
                            if chk:
                                updated_approved_ids.append(sup.get("supporter_id"))
                        st.divider()

                    if st.form_submit_button("Save Approved Vendor Network", type="primary"):
                        cur_v["approved_supporter_ids"] = updated_approved_ids
                        save_data(db)
                        st.success("Approved Vendor Network updated successfully!")
                        st.rerun()

        with t_brand:
            with st.form("update_v_brand"):
                u_whatsapp = st.text_input("WhatsApp POP Number", value=cur_v.get("whatsapp_no", ""))
                u_bank = st.text_area("Bank Details", value=cur_v.get("bank_details", ""))
                u_logo_file = st.file_uploader("Upload New Logo", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("Save Changes"):
                    cur_v["whatsapp_no"] = u_whatsapp
                    cur_v["bank_details"] = u_bank
                    if u_logo_file is not None:
                        cur_v["logo_url"] = process_image_upload(u_logo_file, cur_v.get("logo_url"))
                    save_data(db)
                    st.success("Facility details updated!")
                    st.rerun()

        with t_verify:
            st.markdown("#### Verify WhatsApp Proofs of Payment")
            pending_bks = [b for b in db.get("bookings", []) if b.get("venue_id") == cur_v.get("venue_id") and b.get("status") == "Pending POP / Verification"]
            
            if not pending_bks:
                st.success("No pending venue booking POPs.")
            else:
                for bk in pending_bks:
                    st.write(f"**Booking {bk.get('booking_id')}** — {bk.get('customer_name')} | Space: {bk.get('space_name')} | BWP {bk.get('venue_cost'):,.2f}")
                    with st.form(f"v_verify_{bk.get('booking_id')}"):
                        ref = st.text_input("Enter POP Transaction Reference")
                        if st.form_submit_button("Confirm Booking"):
                            if ref:
                                bk["status"] = "Confirmed / Paid"
                                bk["pop_reference"] = ref
                                save_data(db)
                                st.success(f"Booking {bk.get('booking_id')} confirmed!")
                                st.rerun()
                    st.divider()

        with t_reports:
            st.markdown("#### 📊 Facility Financial Statements & Date Filter")
            
            f_col1, f_col2 = st.columns(2)
            start_date = f_col1.date_input("Report Start Date", datetime.date(2026, 1, 1))
            end_date = f_col2.date_input("Report End Date", datetime.date.today())

            v_bookings = [b for b in db.get("bookings", []) if b.get("venue_id") == cur_v.get("venue_id")]
            
            filtered_bks = [
                b for b in v_bookings 
                if start_date <= datetime.datetime.strptime(b.get("created_at", str(datetime.date.today())), "%Y-%m-%d").date() <= end_date
            ]

            paid_revenue = sum(b.get("venue_cost", 0) for b in filtered_bks if b.get("status") == "Confirmed / Paid")
            pending_revenue = sum(b.get("venue_cost", 0) for b in filtered_bks if b.get("status") == "Pending POP / Verification")

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Bookings Requested", len(filtered_bks))
            m2.metric("Confirmed Revenue (Paid)", f"BWP {paid_revenue:,.2f}")
            m3.metric("Pending Invoices", f"BWP {pending_revenue:,.2f}")

            st.divider()
            st.markdown("##### Detailed Invoices Breakdown")
            if filtered_bks:
                report_data = []
                for b in filtered_bks:
                    report_data.append({
                        "Invoice / Booking ID": b.get("booking_id"),
                        "Date Created": b.get("created_at"),
                        "Customer": b.get("customer_name"),
                        "Reserved Space": b.get("space_name"),
                        "Event Date": b.get("booking_date"),
                        "Amount (BWP)": f"{b.get('venue_cost'):,.2f}",
                        "Payment Method": b.get("payment_method"),
                        "Status": b.get("status"),
                        "POP Ref": b.get("pop_reference", "N/A")
                    })
                st.dataframe(report_data, use_container_width=True)
            else:
                st.info("No booking records found for the selected date range.")

# ---------------------------------------------------------
# 6. MODULE 3: FACILITY SUPPORTER CONSOLE (VENDORS) & REPORTS
# ---------------------------------------------------------
elif user_role == "Facility Supporter Console (Vendors)":
    st.title("Facility Supporter Console & Service Offerings")
    st.caption("Manage vendor profiles, list offering packages with pictures & pricing, verify customer POPs, and view earnings.")
    st.divider()

    supporters = db.get("supporters", [])

    sup_action = st.radio("Vendor Account Options:", ["Select Existing Account", "Create New Vendor Account"], horizontal=True)

    if sup_action == "Create New Vendor Account":
        with st.form("supporter_reg_form"):
            st.markdown("### 📝 Register New Supporter / Vendor Account")
            s_name = st.text_input("Business Name*", placeholder="Kalahari Decor & Catering")
            s_cat = st.selectbox("Category*", ["Catering & Cutlery", "Stage & Decor Design", "Sound & AV", "Florist", "Security"])
            s_person = st.text_input("Contact Person*")
            s_email = st.text_input("Contact Email*")
            s_phone = st.text_input("Phone / WhatsApp Line for POP Reception*")
            s_bank = st.text_area("Company Bank Account & Payment Instructions*")
            s_color = st.color_picker("Corporate Brand Color", "#1E293B")
            s_logo_file = st.file_uploader("Upload Company Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("Create Vendor Account", type="primary"):
                if s_name and s_email and s_phone and s_bank:
                    new_sup_id = f"sup_{len(supporters)+101}"
                    logo_url = process_image_upload(s_logo_file, DEFAULT_LOGO)
                    new_sup = {
                        "supporter_id": new_sup_id,
                        "business_name": s_name,
                        "category": s_cat,
                        "contact_person": s_person,
                        "email": s_email,
                        "phone": s_phone,
                        "bank_details": s_bank,
                        "brand_color": s_color,
                        "logo_url": logo_url,
                        "quotation_templates": []
                    }
                    db.setdefault("supporters", []).append(new_sup)
                    save_data(db)
                    st.session_state["active_supporter_id"] = new_sup_id
                    st.success(f"Vendor Profile '{s_name}' Created Successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all mandatory fields (*).")

    else:
        if not supporters:
            st.info("No vendor accounts found. Please choose 'Create New Vendor Account' above.")
        else:
            sup_options = {s.get("business_name"): s.get("supporter_id") for s in supporters}
            
            default_index = 0
            if "active_supporter_id" in st.session_state:
                matched = [i for i, (k, v) in enumerate(sup_options.items()) if v == st.session_state["active_supporter_id"]]
                if matched:
                    default_index = matched[0]

            sel_sup_name = st.selectbox("Select Active Vendor Profile:", list(sup_options.keys()), index=default_index)
            cur_sup = next(s for s in supporters if s.get("business_name") == sel_sup_name)

            s_logo = cur_sup.get("logo_url", DEFAULT_LOGO)
            s_color = cur_sup.get("brand_color", "#1E293B")

            st.markdown(f"""
                <div class="profile-card" style="background: {s_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style="color: #FFFFFF !important; margin: 0;">🚚 {cur_sup.get('business_name')}</h2>
                            <p style="color: #F1F5F9 !important; margin-top: 4px;">
                                <b>Category:</b> {cur_sup.get('category')} | <b>WhatsApp POP:</b> {cur_sup.get('phone')}
                            </p>
                        </div>
                        <img src="{s_logo}" class="logo-img" style="background: white; padding: 4px; border-radius: 6px;">
                    </div>
                </div>
            """, unsafe_allow_html=True)

            v_tab1, v_tab2, v_tab3, v_tab4 = st.tabs([
                "Service Packages & Quotation Templates", 
                "Branding & Payment Details",
                "✅ Verify Customer POPs", 
                "📊 Vendor Financial Statements & Reports"
            ])

            # SERVICE OFFERINGS & QUOTATION TEMPLATES
            with v_tab1:
                st.markdown("#### Add & Manage What You Provide (Service Packages, Pricing & Photos)")
                
                with st.expander("➕ Create New Service Package / Item Template", expanded=True):
                    with st.form("add_template_item_form"):
                        i_name = st.text_input("Service Item / Package Name*", placeholder="3-Course Buffet Catering")
                        i_desc = st.text_area("Service Description / Specs", placeholder="Includes starters, 2 meats, salads, desserts & cutlery setup.")
                        
                        i_col1, i_col2 = st.columns(2)
                        with i_col1:
                            i_type = st.selectbox("Unit / Charge Type*", ["Per Guest", "Per Day", "Flat Rate", "Per Item Set", "Per Hour"])
                        with i_col2:
                            i_price = st.number_input("Unit Price Rate (BWP)*", min_value=1.0, value=150.0)
                        
                        i_photo = st.file_uploader("Upload Item Photo / Showcase Image", type=["png", "jpg", "jpeg"])

                        if st.form_submit_button("Add Package Offering to Catalog", type="primary"):
                            if i_name:
                                photo_url = process_image_upload(i_photo, SPACE_PRESETS[1])
                                cur_sup.setdefault("quotation_templates", []).append({
                                    "item_name": i_name,
                                    "description": i_desc,
                                    "unit_type": i_type,
                                    "unit_price": i_price,
                                    "image_url": photo_url
                                })
                                save_data(db)
                                st.success(f"Added service package: '{i_name}'")
                                st.rerun()
                            else:
                                st.error("Please enter a service item name.")

                st.divider()
                st.markdown("#### Current Service Offering Catalog")
                templates = cur_sup.get("quotation_templates", [])
                
                if not templates:
                    st.info("No service packages or item rates configured yet. Use the form above to add what you provide.")
                else:
                    for idx, it in enumerate(templates):
                        with st.container():
                            col_t1, col_t2, col_t3 = st.columns([1, 3, 1])
                            with col_t1:
                                if it.get("image_url"):
                                    st.image(it.get("image_url"), use_container_width=True)
                            with col_t2:
                                st.markdown(f"### {it.get('item_name')}")
                                st.markdown(f"**Rate:** BWP {it.get('unit_price'):,.2f} ({it.get('unit_type')})")
                                if it.get("description"):
                                    st.write(it.get("description"))
                            with col_t3:
                                if st.button("Delete Item", key=f"del_t_{idx}"):
                                    templates.pop(idx)
                                    save_data(db)
                                    st.success("Item removed.")
                                    st.rerun()
                            st.divider()

            # BRANDING & PAYMENTS
            with v_tab2:
                st.markdown("#### Update Profile & Payment Details")
                with st.form("edit_vendor_profile"):
                    u_phone = st.text_input("WhatsApp Number for POPs", value=cur_sup.get("phone", ""))
                    u_bank = st.text_area("Bank Details & Instructions", value=cur_sup.get("bank_details", ""))
                    u_color = st.color_picker("Corporate Color", value=cur_sup.get("brand_color", "#1E293B"))
                    u_logo = st.file_uploader("Upload New Logo", type=["png", "jpg", "jpeg"])

                    if st.form_submit_button("Save Profile Setup"):
                        cur_sup["phone"] = u_phone
                        cur_sup["bank_details"] = u_bank
                        cur_sup["brand_color"] = u_color
                        if u_logo is not None:
                            cur_sup["logo_url"] = process_image_upload(u_logo, cur_sup.get("logo_url"))
                        save_data(db)
                        st.success("Vendor profile updated!")
                        st.rerun()

            # VERIFY CUSTOMER POPS
            with v_tab3:
                st.markdown("#### Verify Direct Vendor Invoices & Proofs of Payment")
                my_invoices = [i for i in db.get("vendor_invoices", []) if i.get("supporter_id") == cur_sup.get("supporter_id") and i.get("status") == "Pending POP"]

                if not my_invoices:
                    st.success("No pending supplier POPs awaiting verification.")
                else:
                    for inv in my_invoices:
                        st.write(f"**Vendor Invoice #{inv.get('vendor_invoice_id')}** — Client: {inv.get('customer_name')}")
                        st.write(f"**Venue:** {inv.get('venue_name')} | **Event Date:** {inv.get('event_date')} | **Total:** BWP {inv.get('total_amount'):,.2f}")
                        st.write(f"**Client Contact:** {inv.get('customer_phone')} ({inv.get('customer_email')})")

                        with st.form(f"verify_vendor_inv_{inv.get('vendor_invoice_id')}"):
                            pop_txn = st.text_input("Enter WhatsApp Transaction / POP Reference*")
                            if st.form_submit_button("✅ Verify Vendor POP & Approve Order"):
                                if pop_txn:
                                    inv["status"] = "PAID & VERIFIED"
                                    inv["pop_reference"] = pop_txn
                                    save_data(db)
                                    st.success(f"Invoice {inv.get('vendor_invoice_id')} marked as PAID!")
                                    st.rerun()
                                else:
                                    st.error("Please enter the POP reference number.")
                        st.divider()

            # VENDOR FINANCIAL REPORTING
            with v_tab4:
                st.markdown("#### 📊 Vendor Earnings Statements & Period Filtering")

                v_c1, v_c2 = st.columns(2)
                v_start = v_c1.date_input("Start Date", datetime.date(2026, 1, 1), key="v_start")
                v_end = v_c2.date_input("End Date", datetime.date.today(), key="v_end")

                all_v_invs = [i for i in db.get("vendor_invoices", []) if i.get("supporter_id") == cur_sup.get("supporter_id")]

                filtered_v_invs = [
                    i for i in all_v_invs
                    if v_start <= datetime.datetime.strptime(i.get("created_at", str(datetime.date.today())), "%Y-%m-%d").date() <= v_end
                ]

                paid_tot = sum(i.get("total_amount", 0) for i in filtered_v_invs if i.get("status") == "PAID & VERIFIED")
                pending_tot = sum(i.get("total_amount", 0) for i in filtered_v_invs if i.get("status") == "Pending POP")

                vm1, vm2, vm3 = st.columns(3)
                vm1.metric("Total Quotations Issued", len(filtered_v_invs))
                vm2.metric("Confirmed Payments", f"BWP {paid_tot:,.2f}")
                vm3.metric("Outstanding Invoices", f"BWP {pending_tot:,.2f}")

                st.divider()
                st.markdown("##### Vendor Invoices Breakdown")
                if filtered_v_invs:
                    v_report = []
                    for i in filtered_v_invs:
                        v_report.append({
                            "Vendor Inv ID": i.get("vendor_invoice_id"),
                            "Master Booking ID": i.get("parent_booking_id"),
                            "Date Created": i.get("created_at"),
                            "Client": i.get("customer_name"),
                            "Venue Location": i.get("venue_name"),
                            "Event Date": i.get("event_date"),
                            "Total (BWP)": f"{i.get('total_amount'):,.2f}",
                            "Status": i.get("status"),
                            "POP Ref": i.get("pop_reference", "N/A")
                        })
                    st.dataframe(v_report, use_container_width=True)
                else:
                    st.info("No vendor invoice activity recorded in this date range.")

# ---------------------------------------------------------
# 7. MODULE 4: TICKET SCANNER & GATE ACCESS
# ---------------------------------------------------------
elif user_role == "Ticket Scanner & Gate Access":
    st.title("Door Gate Ticket Access Console")
    st.caption("Verify and scan tickets at event entry doors.")
    st.divider()

    tickets = db.get("tickets", [])
    verify_input = st.text_input("Enter Ticket Hash or Ticket ID:")

    if st.button("Scan & Verify Ticket", type="primary"):
        if verify_input:
            search_str = verify_input.strip().upper()
            matched_tkt = next((t for t in tickets if t.get("verification_hash") == search_str or t.get("ticket_id") == search_str), None)

            if matched_tkt:
                if matched_tkt.get("status") == "VALID":
                    matched_tkt["status"] = "USED / SCANNED"
                    save_data(db)
                    st.success(f"✅ ACCESS GRANTED: Valid Ticket for {matched_tkt.get('buyer')} ({matched_tkt.get('qty')} person/s).")
                elif matched_tkt.get("status") == "Pending POP / Unverified":
                    st.warning("⚠️ UNVERIFIED TICKET: The POP has not been confirmed by the facility manager yet.")
                else:
                    st.error("❌ INVALID: Ticket has already been used.")
            else:
                st.error("❌ Ticket Hash / ID Not Found.")

# ---------------------------------------------------------
# 8. MODULE 5: PLATFORM ADMIN
# ---------------------------------------------------------
elif user_role == "Platform Admin / Master Ledger":
    st.title("Master Enterprise Platform Control")
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Facilities", len(db.get("venues", [])))
    m2.metric("Vendors", len(db.get("supporters", [])))
    m3.metric("Bookings", len(db.get("bookings", [])))
    m4.metric("Vendor Invoices", len(db.get("vendor_invoices", [])))
    m5.metric("Tickets", len(db.get("tickets", [])))
    st.json(db)
