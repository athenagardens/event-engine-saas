import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, date
from fpdf import FPDF

# ---------------------------------------------------------
# 1. PROFESSIONAL WORKPLACE THEME (CSS)
# ---------------------------------------------------------
def inject_custom_css():
    st.markdown("""
        <style>
            .main {
                background-color: #F8FAFC;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            h1, h2, h3, h4 {
                color: #0F172A !important;
                font-weight: 700 !important;
            }
            [data-testid="stSidebar"] {
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
                color: #94A3B8 !important;
            }
            .stButton>button {
                background-color: #2563EB;
                color: white;
                border-radius: 6px;
                border: none;
                font-weight: 600;
            }
            .stButton>button:hover {
                background-color: #1D4ED8;
            }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DEFAULT TEMPLATES FOR SUPPLIERS
# ---------------------------------------------------------
DEFAULT_FLORIST_CATALOGUE = [
    # Stage Arrangements
    {"item_id": "fl_stg_hi", "category": "Stage Floral Arch", "name": "High-End Grand Orchid & Rose Stage Arch", "price": 8500.0, "unit": "per setup", "tier": "High End (Premium Orchids/Roses)", "image_url": "https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=600"},
    {"item_id": "fl_stg_mid", "category": "Stage Floral Arch", "name": "Mid-Range Mixed Seasonal Floral Arch", "price": 4500.0, "unit": "per setup", "tier": "Mid Range (Seasonal Blooms)", "image_url": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600"},
    {"item_id": "fl_stg_low", "category": "Stage Floral Arch", "name": "Budget Greenery & Carnation Arch", "price": 2200.0, "unit": "per setup", "tier": "Low End / Budget (Greenery Base)", "image_url": "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=600"},
    
    # Bouquets
    {"item_id": "fl_bq_hi", "category": "Bridal / Host Bouquet", "name": "Premium Luxury Cascading Lily Bouquet", "price": 1200.0, "unit": "per bouquet", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1561181286-d3fee7d55364?w=600"},
    {"item_id": "fl_bq_mid", "category": "Bridal / Host Bouquet", "name": "Classic Hand-Tied Rose Bouquet", "price": 650.0, "unit": "per bouquet", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1533616688419-b7a585564566?w=600"},
    {"item_id": "fl_bq_low", "category": "Bridal / Host Bouquet", "name": "Simple Petite Posy Bouquet", "price": 300.0, "unit": "per bouquet", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1508615070457-7baeba4003ab?w=600"},

    # Boutonnieres / Pocket Flowers
    {"item_id": "fl_pkt_hi", "category": "Pocket Flowers / Boutonniere", "name": "Orchid & Gold Leaf Boutonniere", "price": 150.0, "unit": "per piece", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600"},
    {"item_id": "fl_pkt_mid", "category": "Pocket Flowers / Boutonniere", "name": "Classic Single Rose Boutonniere", "price": 85.0, "unit": "per piece", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1508615070457-7baeba4003ab?w=600"},
    {"item_id": "fl_pkt_low", "category": "Pocket Flowers / Boutonniere", "name": "Minimalist Carnation Pin", "price": 45.0, "unit": "per piece", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600"},

    # Table Centerpieces (Large, Medium, Small)
    {"item_id": "fl_cp_lg", "category": "Centerpiece - Large", "name": "Tall Crystal Vase Arrangement (High End)", "price": 850.0, "unit": "per table", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=600"},
    {"item_id": "fl_cp_md", "category": "Centerpiece - Medium", "name": "Medium Gold Bowl Floral Cluster (Mid)", "price": 450.0, "unit": "per table", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600"},
    {"item_id": "fl_cp_sm", "category": "Centerpiece - Small", "name": "Small Bud Vase Trio (Budget)", "price": 180.0, "unit": "per table", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=600"}
]

DEFAULT_CATERING_CATALOGUE = [
    # Tables
    {"item_id": "cat_tb_hi", "category": "Tables", "name": "High-End Mirror Top Executive Banquet Table", "price": 350.0, "unit": "per table", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=600"},
    {"item_id": "cat_tb_mid", "category": "Tables", "name": "Standard Round 10-Seater Banquet Table", "price": 120.0, "unit": "per table", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=600"},
    {"item_id": "cat_tb_low", "category": "Tables", "name": "Trestle Folding Table", "price": 60.0, "unit": "per table", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=600"},

    # Chairs
    {"item_id": "cat_ch_hi", "category": "Chairs", "name": "Gold Chiavari / Ghost Acrylic Chair", "price": 45.0, "unit": "per chair", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1503602642458-232111445657?w=600"},
    {"item_id": "cat_ch_mid", "category": "Chairs", "name": "Cushioned Banquet Chair", "price": 25.0, "unit": "per chair", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1580481072645-022f9a6d83d0?w=600"},
    {"item_id": "cat_ch_low", "category": "Chairs", "name": "Standard Plastic Armless Chair", "price": 10.0, "unit": "per chair", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1503602642458-232111445657?w=600"},

    # Tablecloths
    {"item_id": "cat_tc_hi", "category": "Table Linen", "name": "Velvet / Embroidered Damask Tablecloth", "price": 180.0, "unit": "per cloth", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=600"},
    {"item_id": "cat_tc_mid", "category": "Table Linen", "name": "Premium Satin Floor-Length Linen", "price": 90.0, "unit": "per cloth", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=600"},
    {"item_id": "cat_tc_low", "category": "Table Linen", "name": "Standard Polyester Table Overlay", "price": 40.0, "unit": "per cloth", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=600"},

    # Cutlery / Table Settings
    {"item_id": "cat_ct_hi", "category": "Cutlery & Dinnerware", "name": "Full Gold-Plated 5-Piece Cutlery & Fine Bone China Set", "price": 85.0, "unit": "per seat setting", "tier": "High End", "image_url": "https://images.unsplash.com/photo-1615865417236-d67f572a746f?w=600"},
    {"item_id": "cat_ct_mid", "category": "Cutlery & Dinnerware", "name": "Polished Stainless Steel & Ceramic Setting", "price": 45.0, "unit": "per seat setting", "tier": "Mid Range", "image_url": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=600"},
    {"item_id": "cat_ct_low", "category": "Cutlery & Dinnerware", "name": "Standard Stainless Cutlery & Melamine Plate Set", "price": 20.0, "unit": "per seat setting", "tier": "Low End", "image_url": "https://images.unsplash.com/photo-1615865417236-d67f572a746f?w=600"}
]

# ---------------------------------------------------------
# 3. DATABASE INITIALIZATION & OPERATIONS
# ---------------------------------------------------------
DB_FILE = "enterprise_event_platform_db.json"

def load_data():
    if not os.path.exists(DB_FILE):
        default_data = {
            "venues": [
                {
                    "venue_id": "v_royal_aria",
                    "name": "Royal Aria Convention Center",
                    "address": "Plot 102, Tlokweng Road, Gaborone",
                    "manager_email": "admin@royalaria.bw",
                    "status": "Active",
                    "flyer_image_url": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800",
                    "spaces": [
                        {"space_id": "sp_full", "name": "Full Arena & Grounds", "capacity": 5000, "daily_rate": 30000.0},
                        {"space_id": "sp_hall", "name": "Grand Ballroom", "capacity": 1200, "daily_rate": 15000.0},
                        {"space_id": "sp_lawn", "name": "Executive Garden Lawn", "capacity": 500, "daily_rate": 6000.0}
                    ]
                }
            ],
            "events": [
                {
                    "event_id": "evt_gala_2026",
                    "venue_id": "v_royal_aria",
                    "title": "Botswana Annual Innovation Gala 2026",
                    "date": "2026-11-20",
                    "is_free": False,
                    "ticket_price": 450.0,
                    "tickets_total": 500,
                    "tickets_sold": 42,
                    "flyer_image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
                    "description": "Premier gathering for industry leaders, networking, and live performances."
                }
            ],
            "suppliers": [
                {
                    "supplier_id": "sup_flora",
                    "name": "Kalahari Floral & Decor Studios",
                    "category": "Florists & Decorators",
                    "email": "contact@kalaharidecor.bw",
                    "status": "Active",
                    "catalogue": DEFAULT_FLORIST_CATALOGUE
                },
                {
                    "supplier_id": "sup_cater",
                    "name": "Crown Catering & Tableware Rentals",
                    "category": "Catering & Equipment Rentals",
                    "email": "info@crowncatering.bw",
                    "status": "Active",
                    "catalogue": DEFAULT_CATERING_CATALOGUE
                }
            ],
            "facility_bookings": [],
            "ticket_orders": [],
            "platform_invoices": []
        }
        with open(DB_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    with open(DB_FILE, "r") as f:
        data = json.load(f)
        for v in data.get("venues", []):
            if "status" not in v: v["status"] = "Active"
        for s in data.get("suppliers", []):
            if "status" not in s: s["status"] = "Active"
        return data

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# ---------------------------------------------------------
# 4. DIGITAL PDF GENERATOR
# ---------------------------------------------------------
def generate_pdf(document_title, fields_dict, footer_note=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, document_title.upper(), ln=True, align="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Official Document - Central Venue & Event Platform Gateway", ln=True, align="L")
    pdf.ln(8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    for label, value in fields_dict.items():
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(65, 6, f"{label}:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"{value}", ln=True)
        
    if footer_note:
        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, f"Notice: {footer_note}")
        
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        return pdf_bytes.encode('latin1')
    return bytes(pdf_bytes)

# ---------------------------------------------------------
# 5. INITIALIZATION & ROUTING
# ---------------------------------------------------------
st.set_page_config(page_title="Enterprise Venue Marketplace & Ticketing Portal", layout="wide")
inject_custom_css()

base_domain = st.secrets.get("APP_DOMAIN", "http://localhost:8501")
query_params = st.query_params

param_facility = query_params.get("facility")
param_event = query_params.get("event")

# =========================================================
# ROUTE 1: PUBLIC CUSTOMER GATEWAY (ISOLATED FLYER VIEW)
# =========================================================
if param_facility or param_event:
    target_venue = next((v for v in db["venues"] if v["venue_id"] == param_facility), None) if param_facility else None
    target_event = next((e for e in db["events"] if e["event_id"] == param_event), None) if param_event else None

    # -----------------------------------------------------
    # PUBLIC ROUTE A: EVENT FLYER LINK
    # -----------------------------------------------------
    if target_event:
        v_host = next((v for v in db["venues"] if v["venue_id"] == target_event["venue_id"]), None)
        is_suspended = (v_host and v_host.get("status") == "Suspended")

        st.subheader("Digital Interactive Flyer & Ticket Portal")
        st.caption(f"Hosted at: **{v_host['name'] if v_host else 'Partner Facility'}**")
        st.divider()

        col_f1, col_f2 = st.columns([1, 1], gap="large")
        with col_f1:
            if target_event.get("flyer_image_url"):
                st.image(target_event["flyer_image_url"], caption=target_event["title"], use_container_width=True)
            st.markdown(f"### {target_event['title']}")
            st.write(f"**Scheduled Date:** {target_event['date']}")
            st.write(f"**Facility Location:** {v_host['address'] if v_host else 'Main Grounds'}")
            st.write(f"**Event Details:** {target_event['description']}")

        with col_f2:
            is_free = target_event.get("is_free", False)

            if is_free:
                st.success("🎉 **FREE ENTRY EVENT — NO TICKET PAYMENT REQUIRED**")
                with st.form("free_event_form"):
                    st.markdown("##### Claim Free Pass / Register Attendance")
                    buyer_name = st.text_input("Full Name")
                    buyer_email = st.text_input("Email Address")

                    if st.form_submit_button("Get Free Pass"):
                        if buyer_name and buyer_email:
                            tkt_obj = {
                                "ticket_id": f"tkt_free_{len(db['ticket_orders'])+1001}",
                                "event_id": target_event["event_id"],
                                "event_title": target_event["title"],
                                "venue_id": target_event["venue_id"],
                                "customer_name": buyer_name,
                                "customer_email": buyer_email,
                                "quantity": 1,
                                "total_paid": 0.0,
                                "purchase_date": str(date.today()),
                                "locked_due_to_suspension": is_suspended
                            }
                            db["ticket_orders"].append(tkt_obj)
                            save_data(db)

                            if is_suspended:
                                st.warning("We've Got Your Request! Your booking details are saved. We are just waiting on the facility owner to finalize their portal account details on their end.")
                            else:
                                pdf_tkt = generate_pdf(
                                    document_title="Free Event Access Pass",
                                    fields_dict={
                                        "Pass ID": tkt_obj["ticket_id"],
                                        "Attendee Name": buyer_name,
                                        "Event Title": target_event["title"],
                                        "Facility": v_host['name'] if v_host else 'Venue',
                                        "Date": target_event["date"],
                                        "Entry Type": "Free Open Entry"
                                    },
                                    footer_note="Present pass at gate."
                                )
                                st.success("Free Pass Registered Successfully!")
                                st.download_button("Download Free Pass PDF", pdf_tkt, f"Pass_{tkt_obj['ticket_id']}.pdf", "application/pdf")
                        else:
                            st.error("Name and Email required.")
            else:
                remaining = target_event["tickets_total"] - target_event["tickets_sold"]
                st.metric("Tickets Remaining", remaining)
                st.metric("Price Per Pass", f"BWP {target_event['ticket_price']:,.2f}")

                if remaining > 0:
                    with st.form("buy_ticket_flyer_form"):
                        st.markdown("##### Customer Checkout")
                        buyer_name = st.text_input("Full Name")
                        buyer_email = st.text_input("Email Address")
                        qty = st.number_input("Quantity", min_value=1, max_value=remaining, value=1)

                        if st.form_submit_button("Confirm & Pay Ticket"):
                            if buyer_name and buyer_email:
                                total_cost = qty * target_event["ticket_price"]
                                target_event["tickets_sold"] += qty

                                tkt_obj = {
                                    "ticket_id": f"tkt_{len(db['ticket_orders'])+1001}",
                                    "event_id": target_event["event_id"],
                                    "event_title": target_event["title"],
                                    "venue_id": target_event["venue_id"],
                                    "customer_name": buyer_name,
                                    "customer_email": buyer_email,
                                    "quantity": qty,
                                    "total_paid": total_cost,
                                    "purchase_date": str(date.today()),
                                    "locked_due_to_suspension": is_suspended
                                }
                                db["ticket_orders"].append(tkt_obj)
                                save_data(db)

                                if is_suspended:
                                    st.warning("We've Got Your Request! Your booking details are saved. We are just waiting on the facility owner to finalize their portal account details on their end.")
                                else:
                                    pdf_tkt = generate_pdf(
                                        document_title="Digital Entry Ticket Pass",
                                        fields_dict={
                                            "Ticket ID": tkt_obj["ticket_id"],
                                            "Attendee Name": buyer_name,
                                            "Event Title": target_event["title"],
                                            "Facility": v_host['name'] if v_host else 'Venue',
                                            "Date": target_event["date"],
                                            "Pass Quantity": f"{qty} Pass(es)",
                                            "Total Paid": f"BWP {total_cost:,.2f}"
                                        },
                                        footer_note="Present barcode / digital PDF pass at facility gate for entry verification."
                                    )
                                    st.success("Ticket Issued Successfully!")
                                    st.download_button("Download Digital Ticket PDF", pdf_tkt, f"Ticket_{tkt_obj['ticket_id']}.pdf", "application/pdf")
                            else:
                                st.error("Name and Email required.")
                else:
                    st.error("Event Allocation Fully Sold Out.")

    # -----------------------------------------------------
    # PUBLIC ROUTE B: FACILITY HIRE LINK
    # -----------------------------------------------------
    elif target_venue:
        is_suspended = (target_venue.get("status") == "Suspended")

        st.title(f"Welcome to {target_venue['name']}")
        st.caption(f"Physical Address: {target_venue['address']}")
        st.divider()

        if target_venue.get("flyer_image_url"):
            st.image(target_venue["flyer_image_url"], caption=target_venue["name"], use_container_width=True)

        col_hire, col_quote = st.columns([1, 1], gap="large")

        with col_hire:
            st.markdown("### 1. Select Facility Area / Space to Hire")
            selected_spaces = []
            space_cost = 0.0

            if target_venue.get("spaces"):
                for sp in target_venue["spaces"]:
                    chk = st.checkbox(f"{sp['name']} (Cap: {sp['capacity']} guests) — BWP {sp['daily_rate']:,.2f}/day", key=sp["space_id"])
                    if chk:
                        selected_spaces.append(sp)
                        space_cost += sp["daily_rate"]
            else:
                st.info("No sub-spaces configured for this facility yet.")

            res_date = st.date_input("Select Event Hire Date", min_value=date.today())

        with col_quote:
            st.markdown("### 2. Request Supplier Services (Florists, Catering, Decor)")
            selected_supp_items = []
            supp_cost = 0.0

            active_suppliers = db["suppliers"]
            if active_suppliers:
                for sup in active_suppliers:
                    with st.expander(f"📦 {sup['name']} ({sup['category']})"):
                        for item in sup.get("catalogue", []):
                            ci1, ci2 = st.columns([1, 3])
                            with ci1:
                                if item.get("image_url"):
                                    st.image(item["image_url"], use_container_width=True)
                            with ci2:
                                chk_item = st.checkbox(f"**{item['name']}**\n\nPrice: BWP {item['price']:,.2f} ({item['unit']})", key=f"cust_pub_{item['item_id']}")
                                if chk_item:
                                    selected_supp_items.append({"supplier_name": sup["name"], "item_name": item["name"], "price": item["price"]})
                                    supp_cost += item["price"]

        if selected_spaces:
            st.divider()
            grand_total = space_cost + supp_cost
            st.markdown(f"#### Total Estimated Cost: **BWP {grand_total:,.2f}**")

            with st.form("facility_hire_form"):
                st.markdown("##### Book Facility & Request Quotation")
                c_name = st.text_input("Full Name / Organization Name")
                c_email = st.text_input("Email Address")

                if st.form_submit_button("Submit Hire Booking & Request Quote"):
                    if c_name and c_email:
                        bk_obj = {
                            "booking_id": f"bk_{len(db['facility_bookings'])+1001}",
                            "venue_id": target_venue["venue_id"],
                            "venue_name": target_venue["name"],
                            "customer_name": c_name,
                            "customer_email": c_email,
                            "hire_date": str(res_date),
                            "booked_spaces": [s["name"] for s in selected_spaces],
                            "supplier_items": [i["item_name"] for i in selected_supp_items],
                            "total_amount": grand_total,
                            "status": "Quotation Pending Acceptance",
                            "locked_due_to_suspension": is_suspended
                        }
                        db["facility_bookings"].append(bk_obj)
                        save_data(db)

                        if is_suspended:
                            st.warning("We've Got Your Request! Your booking details are saved. We are just waiting on the facility owner to finalize their portal account details on their end.")
                        else:
                            pdf_quote = generate_pdf(
                                document_title="Facility Hire Official Quotation",
                                fields_dict={
                                    "Quotation Reference": bk_obj["booking_id"],
                                    "Customer": c_name,
                                    "Facility": target_venue["name"],
                                    "Reserved Date": str(res_date),
                                    "Spaces Selected": ", ".join(bk_obj["booked_spaces"]),
                                    "Supplier Add-ons": ", ".join(bk_obj["supplier_items"]) if bk_obj["supplier_items"] else "None",
                                    "Quoted Total": f"BWP {grand_total:,.2f}"
                                },
                                footer_note="This quotation is valid for 7 days."
                            )
                            st.success("Quotation & Hire Request Issued!")
                            st.download_button("Download Official Quotation PDF", pdf_quote, f"Quotation_{bk_obj['booking_id']}.pdf", "application/pdf")
                    else:
                        st.error("Name and Email required.")

# =========================================================
# ROUTE 2: MANAGEMENT CONSOLE & MARKETPLACE
# =========================================================
else:
    st.sidebar.markdown("### Role Portal Switcher")
    user_role = st.sidebar.selectbox(
        "Select Active Interface",
        [
            "Customer Marketplace Search",
            "Facility Owner (Venue)",
            "Facility Supporter (Supplier)",
            "Super User (Platform Owner)"
        ]
    )

    st.title("Central Venue, Event & Supplier Platform")
    st.caption(f"Active Interface Mode: **{user_role}**")
    st.divider()

    # -----------------------------------------------------
    # ROLE A: FACILITY OWNER (SINGLE PROFILE RESTRICTION)
    # -----------------------------------------------------
    if user_role == "Facility Owner (Venue)":
        st.subheader("Facility Owner Management Portal")

        # Single Venue Enforcer
        if not db["venues"]:
            st.info("No facility registered. Please register your venue profile below (Note: Only 1 facility profile permitted per account).")
            with st.form("single_venue_reg_form"):
                fn = st.text_input("Facility Name")
                fa = st.text_input("Physical Address")
                fe = st.text_input("Manager Email")
                ff = st.text_input("Main Venue Image URL", value="https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800")
                if st.form_submit_button("Register Primary Facility"):
                    if fn and fa and fe:
                        new_fac = {"venue_id": f"v_{len(db['venues'])+101}", "name": fn, "address": fa, "manager_email": fe, "status": "Active", "flyer_image_url": ff, "spaces": []}
                        db["venues"].append(new_fac)
                        save_data(db)
                        st.success(f"Facility '{fn}' successfully registered!")
                        st.rerun()
                    else:
                        st.error("All fields required.")
        else:
            cur_v = db["venues"][0]  # Single venue model
            st.success(f"Managing Single Registered Facility: **{cur_v['name']}** ({cur_v['address']})")
            
            is_v_suspended = (cur_v.get("status") == "Suspended")
            locked_bks = [b for b in db["facility_bookings"] if b["venue_id"] == cur_v["venue_id"] and b.get("locked_due_to_suspension", False)]
            locked_tkts = [t for t in db["ticket_orders"] if t.get("venue_id") == cur_v["venue_id"] and t.get("locked_due_to_suspension", False)]
            total_locked = len(locked_bks) + len(locked_tkts)

            if is_v_suspended:
                st.error(f"🔴 ACCOUNT SUSPENDED (UNPAID PLATFORM INVOICE)\n\n"
                         f"You currently have **{total_locked} customer booking(s) / ticket order(s)** locked in the system! "
                         f"Settle your monthly platform payment with the administrator to release customer data.")

            t_config, t_events, t_flyers, t_bookings = st.tabs([
                "Configure Venue & Spaces",
                "Events & Ticket Setup",
                "Flyer & WhatsApp Share",
                "Venue Hire Bookings"
            ])

            with t_config:
                st.markdown(f"##### Add Hire Sub-Spaces to {cur_v['name']}")
                with st.form("add_section_form"):
                    sec_name = st.text_input("Area Name (e.g. VIP Hall, Garden Lawn, Main Stage)")
                    sec_cap = st.number_input("Guest Capacity", min_value=1, value=200)
                    sec_rate = st.number_input("Daily Hire Price (BWP)", min_value=0.0, value=2500.0)
                    if st.form_submit_button("Add Area Section"):
                        cur_v["spaces"].append({"space_id": f"sp_{len(cur_v['spaces'])+101}", "name": sec_name, "capacity": sec_cap, "daily_rate": sec_rate})
                        save_data(db)
                        st.success(f"Section '{sec_name}' added to facility!")
                        st.rerun()

                st.divider()
                st.markdown("##### Configured Facility Sections")
                if cur_v["spaces"]:
                    for idx, sp in enumerate(cur_v["spaces"]):
                        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                        c1.write(f"**{sp['name']}**")
                        c2.write(f"Cap: {sp['capacity']} guests")
                        c3.write(f"BWP {sp['daily_rate']:,.2f}/day")
                        if c4.button("Delete", key=f"del_sp_{sp['space_id']}"):
                            cur_v["spaces"].pop(idx)
                            save_data(db)
                            st.warning(f"Deleted {sp['name']}")
                            st.rerun()
                else:
                    st.caption("No sub-spaces added yet.")

            with t_events:
                with st.form("pub_event_form"):
                    st.markdown(f"##### Create Event at {cur_v['name']}")
                    et = st.text_input("Event Title")
                    ed = st.date_input("Event Date")
                    is_free_evt = st.checkbox("Free Entry (No Tickets / Payment Required)", value=False)
                    
                    ep = 0.0
                    eq = 0
                    if not is_free_evt:
                        ep = st.number_input("Ticket Price (BWP)", min_value=0.0, value=150.0)
                        eq = st.number_input("Total Ticket Quantity", min_value=1, value=100)
                    else:
                        st.info("Event marked as Free Entry. Attendees will receive a zero-cost digital pass.")

                    ef = st.text_input("Event Flyer Image URL", value="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800")
                    edesc = st.text_area("Event Description")

                    if st.form_submit_button("Publish Event"):
                        if et:
                            new_e = {
                                "event_id": f"evt_{len(db['events'])+101}",
                                "venue_id": cur_v["venue_id"],
                                "title": et, "date": str(ed),
                                "is_free": is_free_evt,
                                "ticket_price": ep, "tickets_total": eq, "tickets_sold": 0,
                                "flyer_image_url": ef, "description": edesc
                            }
                            db["events"].append(new_e)
                            save_data(db)
                            st.success(f"Event '{et}' published successfully!")
                            st.rerun()
                        else:
                            st.error("Event title required.")

            with t_flyers:
                col_f1, col_f2 = st.columns(2, gap="large")
                with col_f1:
                    st.markdown("##### 1. Facility Hire Sharing Link")
                    fac_link = f"{base_domain}/?facility={cur_v['venue_id']}"
                    wa_fac_msg = urllib.parse.quote(f"Book spaces or host your private event at {cur_v['name']}:\n{fac_link}")
                    st.text_input("Facility Link", value=fac_link)
                    st.markdown(f'<a href="https://wa.me/?text={wa_fac_msg}" target="_blank"><button style="width:100%; height:40px;">Share Facility on WhatsApp</button></a>', unsafe_allow_html=True)

                with col_f2:
                    st.markdown("##### 2. Event Ticket / Access Link")
                    v_events = [e for e in db["events"] if e["venue_id"] == cur_v["venue_id"]]
                    if v_events:
                        sel_e = st.selectbox("Select Event to Share", [e["title"] for e in v_events])
                        matched_e = next(e for e in v_events if e["title"] == sel_e)
                        evt_link = f"{base_domain}/?event={matched_e['event_id']}"
                        wa_evt_msg = urllib.parse.quote(f"Access tickets/passes for {matched_e['title']}:\n{evt_link}")
                        st.text_input("Event Link", value=evt_link)
                        st.markdown(f'<a href="https://wa.me/?text={wa_evt_msg}" target="_blank"><button style="width:100%; height:40px;">Share Event on WhatsApp</button></a>', unsafe_allow_html=True)

            with t_bookings:
                if is_v_suspended:
                    st.error("🔒 BOOKINGS LOCKED: Pay your platform monthly subscription invoice to unlock customer details and confirm pending bookings.")
                else:
                    st.markdown("##### Active Hire Orders Log")
                    v_bks = [b for b in db["facility_bookings"] if b["venue_id"] == cur_v["venue_id"]]
                    if v_bks:
                        for idx, bk in enumerate(v_bks):
                            cb1, cb2, cb3, cb4 = st.columns([3, 2, 2, 1])
                            cb1.write(f"**{bk['customer_name']}** ({bk['customer_email']})")
                            cb2.write(f"Date: {bk['hire_date']}")
                            cb3.write(f"BWP {bk['total_amount']:,.2f}")
                            if cb4.button("Cancel", key=f"del_bk_{bk['booking_id']}"):
                                db["facility_bookings"] = [b for b in db["facility_bookings"] if b["booking_id"] != bk["booking_id"]]
                                save_data(db)
                                st.warning("Booking removed!")
                                st.rerun()
                    else:
                        st.info("No active facility bookings found.")

    # -----------------------------------------------------
    # ROLE B: FACILITY SUPPORTER (SINGLE PROFILE + TEMPLATES)
    # -----------------------------------------------------
    elif user_role == "Facility Supporter (Supplier)":
        st.subheader("Facility Supporter Portal (Florists, Caterers, Decor)")

        # Single Supplier Enforcer
        if not db["suppliers"]:
            st.info("No supplier profile registered. Create your profile below to auto-load category templates (1 supplier profile allowed).")
            with st.form("single_sup_reg_form"):
                sn = st.text_input("Business / Supporter Name")
                sc = st.selectbox("Category", ["Florists & Decorators", "Catering & Equipment Rentals"])
                se = st.text_input("Contact Email")
                if st.form_submit_button("Register Primary Supporter Profile"):
                    if sn and se:
                        init_cat = DEFAULT_FLORIST_CATALOGUE if sc == "Florists & Decorators" else DEFAULT_CATERING_CATALOGUE
                        new_sup = {
                            "supplier_id": f"sup_{len(db['suppliers'])+101}",
                            "name": sn, "category": sc, "email": se,
                            "status": "Active", "catalogue": init_cat
                        }
                        db["suppliers"].append(new_sup)
                        save_data(db)
                        st.success("Profile Registered with Category Templates loaded!")
                        st.rerun()
                    else:
                        st.error("Name and Email required.")
        else:
            cur_s = db["suppliers"][0] # Single supplier model
            st.success(f"Managing Registered Supporter: **{cur_s['name']}** ({cur_s['category']})")

            if cur_s.get("status") == "Suspended":
                st.error("🔴 ACCOUNT SUSPENDED: Settle outstanding monthly billing invoices with the system admin to unlock supplier requests.")

            t_cat_view, t_add_item = st.tabs(["Manage Comprehensive Catalogue & Images", "Add Custom Item"])

            with t_cat_view:
                st.markdown(f"##### Catalogue for {cur_s['name']} ({cur_s['category']})")
                st.caption("Review tiered pricing ranges (High End, Mid Range, Low End) and image placeholders.")

                for idx, item in enumerate(cur_s.get("catalogue", [])):
                    with st.expander(f"📦 [{item.get('tier', 'Standard')}] {item['name']} - BWP {item['price']:,.2f}"):
                        ci1, ci2 = st.columns([1, 3])
                        with ci1:
                            if item.get("image_url"):
                                st.image(item["image_url"], caption=item["name"], use_container_width=True)
                        with ci2:
                            new_name = st.text_input("Item Name", value=item["name"], key=f"item_n_{idx}")
                            new_price = st.number_input("Price (BWP)", value=float(item["price"]), key=f"item_p_{idx}")
                            new_img = st.text_input("Image URL Placeholder", value=item.get("image_url", ""), key=f"item_img_{idx}")
                            
                            col_b1, col_b2 = st.columns(2)
                            if col_b1.button("Save Changes", key=f"save_itm_{idx}"):
                                item["name"] = new_name
                                item["price"] = new_price
                                item["image_url"] = new_img
                                save_data(db)
                                st.success("Item updated!")
                                st.rerun()
                            if col_b2.button("Remove Item", key=f"del_itm_{idx}"):
                                cur_s["catalogue"].pop(idx)
                                save_data(db)
                                st.warning("Item removed!")
                                st.rerun()

            with t_add_item:
                with st.form("add_cat_item_custom"):
                    st.markdown("##### Add New Service / Product Option")
                    iname = st.text_input("Item Name")
                    itier = st.selectbox("Pricing Tier", ["High End (Premium)", "Mid Range (Standard)", "Low End (Budget)"])
                    iprice = st.number_input("Unit Price (BWP)", min_value=0.0, value=500.0)
                    iunit = st.text_input("Unit Type", value="per item")
                    iimg = st.text_input("Image URL Placeholder", value="https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=600")
                    if st.form_submit_button("Add to Catalogue"):
                        if iname:
                            cur_s["catalogue"].append({
                                "item_id": f"itm_cust_{len(cur_s['catalogue'])+101}",
                                "category": "Custom Option",
                                "name": iname, "price": iprice, "unit": iunit,
                                "tier": itier, "image_url": iimg
                            })
                            save_data(db)
                            st.success("New item added to catalogue!")
                            st.rerun()

    # -----------------------------------------------------
    # ROLE C: SUPER USER (PLATFORM OWNER CONTROL)
    # -----------------------------------------------------
    elif user_role == "Super User (Platform Owner)":
        st.subheader("Platform Administration & Account Control")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Registered Facilities", len(db["venues"]))
        m2.metric("Facility Supporters", len(db["suppliers"]))
        m3.metric("Facility Bookings", len(db["facility_bookings"]))
        m4.metric("Ticket Sales Ledger", len(db["ticket_orders"]))

        tab_susp, tab_inv, tab_logs = st.tabs([
            "Account Suspensions",
            "Monthly Portal Invoicing",
            "System Records & Database"
        ])

        with tab_susp:
            st.markdown("##### Manage Account Status & Automatic Payment Lock Controls")
            st.caption("When suspended, customer bookings accumulate silently, prompting non-paying accounts to settle billing.")

            st.markdown("### 1. Facilities (Venues)")
            for v in db["venues"]:
                col_v1, col_v2, col_v3 = st.columns([3, 2, 2])
                col_v1.write(f"**{v['name']}** ({v['manager_email']})")
                status_color = "🔴 Suspended" if v.get("status") == "Suspended" else "🟢 Active"
                col_v2.write(f"Status: **{status_color}**")
                
                if v.get("status") == "Suspended":
                    if col_v3.button("Reactivate & Release Bookings", key=f"react_v_{v['venue_id']}"):
                        v["status"] = "Active"
                        for b in db["facility_bookings"]:
                            if b["venue_id"] == v["venue_id"]: b["locked_due_to_suspension"] = False
                        for t in db["ticket_orders"]:
                            if t.get("venue_id") == v["venue_id"]: t["locked_due_to_suspension"] = False
                        save_data(db)
                        st.success(f"Reactivated {v['name']}!")
                        st.rerun()
                else:
                    if col_v3.button("Suspend Venue (Non-Payment)", key=f"susp_v_{v['venue_id']}"):
                        v["status"] = "Suspended"
                        save_data(db)
                        st.warning(f"Suspended {v['name']}")
                        st.rerun()

            st.divider()
            st.markdown("### 2. Facility Supporters (Suppliers)")
            for s in db["suppliers"]:
                col_s1, col_s2, col_s3 = st.columns([3, 2, 2])
                col_s1.write(f"**{s['name']}** ({s['email']})")
                status_color = "🔴 Suspended" if s.get("status") == "Suspended" else "🟢 Active"
                col_s2.write(f"Status: **{status_color}**")

                if s.get("status") == "Suspended":
                    if col_s3.button("Reactivate Supporter", key=f"react_s_{s['supplier_id']}"):
                        s["status"] = "Active"
                        save_data(db)
                        st.success(f"Reactivated {s['name']}")
                        st.rerun()
                else:
                    if col_s3.button("Suspend Supporter (Non-Payment)", key=f"susp_s_{s['supplier_id']}"):
                        s["status"] = "Suspended"
                        save_data(db)
                        st.warning(f"Suspended {s['name']}")
                        st.rerun()

        with tab_inv:
            st.markdown("##### Issue Monthly Portal Billing Invoice")
            col_i1, col_i2 = st.columns(2)

            with col_i1:
                target_type = st.radio("Bill Recipient Type", ["Facility Owner", "Facility Supporter"])
                recipient_name = st.selectbox("Select Billed Entity", [v["name"] for v in db["venues"]] if target_type == "Facility Owner" else [s["name"] for s in db["suppliers"]])

            with col_i2:
                sub_fee = st.number_input("Monthly Subscription Fee (BWP)", min_value=0.0, value=1500.0)
                inv_month = st.text_input("Billing Month / Period", value="September 2026")

                if st.button("Generate & Issue Monthly Invoice"):
                    inv_obj = {
                        "invoice_id": f"inv_{len(db['platform_invoices'])+1001}",
                        "recipient": recipient_name,
                        "type": target_type,
                        "period": inv_month,
                        "amount": sub_fee,
                        "date": str(date.today()),
                        "status": "Issued"
                    }
                    db["platform_invoices"].append(inv_obj)
                    save_data(db)

                    pdf_inv = generate_pdf(
                        document_title="Platform Monthly Subscription Invoice",
                        fields_dict={
                            "Invoice Number": inv_obj["invoice_id"],
                            "Billed Entity": recipient_name,
                            "Category": target_type,
                            "Billing Period": inv_month,
                            "Date Issued": str(date.today()),
                            "Total Payable": f"BWP {sub_fee:,.2f}"
                        },
                        footer_note="Payment due within 15 days of invoice date."
                    )
                    st.success(f"Invoice {inv_obj['invoice_id']} issued to {recipient_name}!")
                    st.download_button("Download Subscription Invoice PDF", pdf_inv, f"Invoice_{inv_obj['invoice_id']}.pdf", "application/pdf")

        with tab_logs:
            st.markdown("##### Master System JSON Database")
            st.json(db)

    # -----------------------------------------------------
    # ROLE D: CUSTOMER MARKETPLACE SEARCH (PORTAL CHECKOUT)
    # -----------------------------------------------------
    elif user_role == "Customer Marketplace Search":
        st.subheader("Browse Facilities & Public Events")

        t_search_fac, t_search_evt = st.tabs(["Browse Facilities for Hire", "Browse Public Events"])

        with t_search_fac:
            for v in db["venues"]:
                st.markdown(f"### {v['name']}")
                st.write(f"**Address:** {v['address']}")
                st.markdown(f"🔗 **Direct Facility Booking Link:** `{base_domain}/?facility={v['venue_id']}`")
                
                with st.expander("Book Facility Directly via Portal"):
                    is_suspended = (v.get("status") == "Suspended")
                    
                    st.markdown("#### Select Sub-Spaces to Hire")
                    selected_spaces = []
                    sp_cost = 0.0
                    for sp in v.get("spaces", []):
                        if st.checkbox(f"{sp['name']} (Cap: {sp['capacity']}) - BWP {sp['daily_rate']:,.2f}", key=f"mkt_sp_{sp['space_id']}"):
                            selected_spaces.append(sp)
                            sp_cost += sp["daily_rate"]

                    h_date = st.date_input("Hire Date", min_value=date.today(), key=f"mkt_d_{v['venue_id']}")
                    
                    st.markdown("#### Select Supplier Add-Ons")
                    selected_supps = []
                    sup_cost = 0.0
                    for sup in db["suppliers"]:
                        for item in sup.get("catalogue", []):
                            if st.checkbox(f"{sup['name']} - {item['name']} (BWP {item['price']:,.2f})", key=f"mkt_item_{v['venue_id']}_{item['item_id']}"):
                                selected_supps.append(item)
                                sup_cost += item["price"]

                    total_mkt = sp_cost + sup_cost
                    st.markdown(f"**Grand Total Estimate: BWP {total_mkt:,.2f}**")

                    if selected_spaces:
                        with st.form(f"mkt_hire_form_{v['venue_id']}"):
                            cust_n = st.text_input("Full Name")
                            cust_e = st.text_input("Email Address")
                            if st.form_submit_button("Confirm Booking Request"):
                                if cust_n and cust_e:
                                    bk_obj = {
                                        "booking_id": f"bk_{len(db['facility_bookings'])+1001}",
                                        "venue_id": v["venue_id"],
                                        "venue_name": v["name"],
                                        "customer_name": cust_n,
                                        "customer_email": cust_e,
                                        "hire_date": str(h_date),
                                        "booked_spaces": [s["name"] for s in selected_spaces],
                                        "supplier_items": [i["name"] for i in selected_supps],
                                        "total_amount": total_mkt,
                                        "status": "Quotation Pending Acceptance",
                                        "locked_due_to_suspension": is_suspended
                                    }
                                    db["facility_bookings"].append(bk_obj)
                                    save_data(db)

                                    if is_suspended:
                                        st.warning("We've Got Your Request! Your booking details are saved. We are just waiting on the facility owner to finalize their portal account details on their end.")
                                    else:
                                        pdf_q = generate_pdf("Official Quotation", {"Ref": bk_obj["booking_id"], "Customer": cust_n, "Venue": v["name"], "Total": f"BWP {total_mkt:,.2f}"})
                                        st.success("Booking request logged successfully!")
                                        st.download_button("Download Quotation PDF", pdf_q, f"Quotation_{bk_obj['booking_id']}.pdf")
                                else:
                                    st.error("Fill in name and email.")
                st.divider()

        with t_search_evt:
            for e in db["events"]:
                v_host = next((v for v in db["venues"] if v["venue_id"] == e["venue_id"]), None)
                st.markdown(f"### {e['title']}")
                st.write(f"**Date:** {e['date']} | **Location:** {v_host['name'] if v_host else 'Main Grounds'}")
                st.markdown(f"🔗 **Direct Ticket Link:** `{base_domain}/?event={e['event_id']}`")
                
                with st.expander("Get Tickets / Passes via Portal"):
                    is_suspended = (v_host and v_host.get("status") == "Suspended")
                    is_free = e.get("is_free", False)

                    if is_free:
                        st.info("🎉 Free Entry Event")
                        with st.form(f"mkt_free_form_{e['event_id']}"):
                            fn_c = st.text_input("Name")
                            fe_c = st.text_input("Email")
                            if st.form_submit_button("Claim Free Access Pass"):
                                if fn_c and fe_c:
                                    tkt_obj = {
                                        "ticket_id": f"tkt_free_{len(db['ticket_orders'])+1001}",
                                        "event_id": e["event_id"],
                                        "event_title": e["title"],
                                        "venue_id": e["venue_id"],
                                        "customer_name": fn_c,
                                        "customer_email": fe_c,
                                        "quantity": 1,
                                        "total_paid": 0.0,
                                        "purchase_date": str(date.today()),
                                        "locked_due_to_suspension": is_suspended
                                    }
                                    db["ticket_orders"].append(tkt_obj)
                                    save_data(db)

                                    if is_suspended:
                                        st.warning("We've Got Your Request! Your booking details are saved. We are just waiting on the facility owner to finalize their portal account details on their end.")
                                    else:
                                        pdf_p = generate_pdf("Free Entry Pass", {"Pass ID": tkt_obj["ticket_id"], "Name": fn_c, "Event": e["title"]})
                                        st.success("Pass issued!")
                                        st.download_button("Download Free Pass PDF", pdf_p, f"Pass_{tkt_obj['ticket_id']}.pdf")
                    else:
                        st.write(f"**Price:** BWP {e['ticket_price']:,.2f}")
                        with st.form(f"mkt_tkt_form_{e['event_id']}"):
                            tn_c = st.text_input("Name")
                            te_c = st.text_input("Email")
                            t_qty = st.number_input("Quantity", min_value=1, value=1)
                            if st.form_submit_button("Buy Ticket"):
                                if tn_c and te_c:
                                    tot = t_qty * e["ticket_price"]
                                    e["tickets_sold"] += t_qty
                                    tkt_obj = {
                                        "ticket_id": f"tkt_{len(db['ticket_orders'])+1001}",
                                        "event_id": e["event_id"],
                                        "event_title": e["title"],
                                        "venue_id": e["venue_id"],
                                        "customer_name": tn_c,
                                        "customer_email": te_c,
                                        "quantity": t_qty,
                                        "total_paid": tot,
                                        "purchase_date": str(date.today()),
                                        "locked_due_to_suspension": is_suspended
                                    }
                                    db["ticket_orders"].append(tkt_obj)
                                    save_data(db)

                                    if is_suspended:
                                        st.warning("We've Got Your Request! Your booking details are saved. We are just waiting on the facility owner to finalize their portal account details on their end.")
                                    else:
                                        pdf_t = generate_pdf("Digital Entry Pass", {"Ticket ID": tkt_obj["ticket_id"], "Name": tn_c, "Event": e["title"], "Paid": f"BWP {tot:,.2f}"})
                                        st.success("Ticket Purchased!")
                                        st.download_button("Download Ticket PDF", pdf_t, f"Ticket_{tkt_obj['ticket_id']}.pdf")
                st.divider()
