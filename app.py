import streamlit as st
import json
import os
import urllib.parse
import io
import pandas as pd
from fpdf import FPDF

# ---------------------------------------------------------
# 1. ENTERPRISE CSS INJECTION
# ---------------------------------------------------------
def inject_custom_css():
    st.markdown("""
        <style>
            .main {
                background-color: #FAFAFA;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            h1, h2, h3, h4 {
                color: #0F172A !important;
                font-weight: 600 !important;
            }
            [data-testid="stSidebar"] {
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
                color: #94A3B8 !important;
            }
            button[data-baseweb="tab"] {
                font-weight: 500 !important;
                color: #475569 !important;
            }
            button[aria-selected="true"] {
                color: #2563EB !important;
                border-bottom: 2px solid #2563EB !important;
            }
            .stAlert {
                border-radius: 6px !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
                font-weight: 700 !important;
                color: #0F172A !important;
            }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DATABASE READ/WRITE OPERATIONS
# ---------------------------------------------------------
DB_FILE = "marketplace_db.json"

def load_data():
    if not os.path.exists(DB_FILE):
        default_data = {
            "venues": [
                {
                    "venue_id": "v_central_park",
                    "name": "Gaborone International Convention Centre",
                    "address": "Plot 54367, Western Bypass, Gaborone",
                    "capacity": 5000,
                    "manager_email": "venue_admin@example.bw"
                }
            ],
            "events": [
                {
                    "event_id": "evt_101",
                    "title": "Botswana Music & Cultural Festival 2026",
                    "date": "2026-10-15",
                    "location": "Gaborone International Convention Centre",
                    "venue_id": "v_central_park",
                    "tickets_total": 100,
                    "tickets_sold": 15,
                    "price_per_ticket": 350.0,
                    "flyer_image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
                    "description": "Annual live musical performance and cultural event."
                }
            ],
            "vendors": [
                {
                    "vendor_id": "v_alice",
                    "name": "Kalahari Promos & VIP Booking",
                    "email": "alice@example.bw",
                    "bio": "Official affiliate promotion partner."
                }
            ],
            "services": [
                {
                    "service_id": "srv_cat_01",
                    "title": "Gourmet Catering & Bar Services",
                    "category": "Catering & Refreshments",
                    "provider_name": "Apex Hospitality Botswana",
                    "status": "Confirmed"
                }
            ]
        }
        with open(DB_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# ---------------------------------------------------------
# 3. PDF RECEIPT GENERATOR
# ---------------------------------------------------------
def generate_pdf_receipt(cust_name, cust_email, event_title, qty, price_per_ticket, vendor_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "OFFICIAL PAYMENT RECEIPT", ln=True, align="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Issued by Event Engine Platform Operations (Botswana)", ln=True, align="L")
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Customer Name: {cust_name}", ln=True)
    pdf.cell(0, 6, f"Email Address: {cust_email}", ln=True)
    pdf.cell(0, 6, f"Affiliate Vendor: {vendor_name}", ln=True)
    pdf.ln(4)
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Event Designation: {event_title}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Quantity Issued: {qty}", ln=True)
    pdf.cell(0, 6, f"Unit Ticket Price: BWP {price_per_ticket:.2f}", ln=True)
    
    total = qty * price_per_ticket
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Total Transaction Amount: BWP {total:.2f}", ln=True)
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Notice: Please present this document along with government-issued photo identification at the facility entrance for validation.")
    
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin1')
    return bytes(pdf_output)

# ---------------------------------------------------------
# 4. PAGE INITIALIZATION
# ---------------------------------------------------------
st.set_page_config(page_title="Event Booking Engine & Venue Management System", layout="wide")
inject_custom_css()

base_domain = st.secrets.get("APP_DOMAIN", "http://localhost:8501")

query_params = st.query_params
param_vendor = query_params.get("vendor")
param_event = query_params.get("event")

# ---------------------------------------------------------
# 5. CUSTOMER CHECKOUT VIEW (IF URL HAS PARAMS)
# ---------------------------------------------------------
if param_vendor and param_event:
    st.title("Ticket Order Checkout")
    st.caption("Complete your ticket reservation securely through the central booking gateway.")
    st.divider()
    
    sel_evt = next((e for e in db["events"] if e["event_id"] == param_event), None)
    sel_v = next((v for v in db["vendors"] if v["vendor_id"] == param_vendor), None)
    
    if sel_evt:
        col_flyer, col_booking = st.columns([1, 1], gap="large")
        
        with col_flyer:
            st.subheader("Event Promotional Asset")
            if sel_evt.get("flyer_image_url"):
                st.image(sel_evt["flyer_image_url"], use_container_width=True)
            st.caption(f"Authorized Affiliate Partner: **{sel_v['name'] if sel_v else 'Direct Venue Distribution'}**")
            
        with col_booking:
            st.subheader(sel_evt["title"])
            st.write(f"**Description:** {sel_evt.get('description', 'Standard entry pass.')}")
            st.write(f"**Scheduled Date:** {sel_evt['date']}")
            st.write(f"**Facility Location:** {sel_evt['location']}")
            st.write(f"**Unit Price:** BWP {sel_evt['price_per_ticket']:.2f}")
            
            tickets_left = sel_evt["tickets_total"] - sel_evt["tickets_sold"]
            st.metric("Remaining Inventory", tickets_left)
            
            if tickets_left > 0:
                with st.form("customer_purchase_form"):
                    st.markdown("##### Buyer Information")
                    cust_name = st.text_input("Full Legal Name")
                    cust_email = st.text_input("Email Address")
                    qty = st.number_input("Ticket Quantity", min_value=1, max_value=tickets_left, value=1)
                    submitted = st.form_submit_button("Confirm Order")
                    
                    if submitted and cust_name and cust_email:
                        sel_evt["tickets_sold"] += qty
                        save_data(db)
                        
                        v_name = sel_v['name'] if sel_v else 'Direct Distribution'
                        pdf_bytes = generate_pdf_receipt(
                            cust_name=cust_name,
                            cust_email=cust_email,
                            event_title=sel_evt['title'],
                            qty=qty,
                            price_per_ticket=sel_evt['price_per_ticket'],
                            vendor_name=v_name
                        )
                        
                        st.success(f"Order processed successfully for {cust_name}.")
                        st.download_button(
                            label="Download PDF Invoice & Pass",
                            data=pdf_bytes,
                            file_name=f"Invoice_{cust_name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("Ticket allocation exhausted for this event.")
    else:
        st.error("Requested event configuration not found.")

# ---------------------------------------------------------
# 6. MANAGEMENT CONSOLE (RBAC ROLE VIEWS)
# ---------------------------------------------------------
else:
    st.sidebar.markdown("### Access Delegation")
    user_role = st.sidebar.selectbox(
        "Active Role Profile",
        ["Super Admin", "Venue Manager", "Vendor / Promoter"]
    )
    
    st.title("Event Booking Engine & Venue Management System")
    st.caption(f"Currently viewing console as: **{user_role}**")
    st.divider()

    # --- ROLE A: SUPER ADMIN ---
    if user_role == "Super Admin":
        st.info("**Scope: Global Platform Controls.** Unrestricted access across all system entities, financial records, and logs.")
        
        tab_overview, tab_events, tab_venue_mgmt, tab_billing = st.tabs([
            "Dashboard Overview", "All Events Inventory", "Facility Management", "Platform Financials"
        ])
        
        with tab_overview:
            m_col1, m_col2, m_col3 = st.columns(3)
            total_gross = sum(e["tickets_sold"] * e["price_per_ticket"] for e in db["events"])
            total_sold = sum(e["tickets_sold"] for e in db["events"])
            total_capacity = sum(e["tickets_total"] for e in db["events"])
            
            m_col1.metric("Gross Revenue", f"BWP {total_gross:,.2f}")
            m_col2.metric("Tickets Sold", total_sold)
            m_col3.metric("Fulfillment Rate", f"{(total_sold/total_capacity*100) if total_capacity else 0:.1f}%")
            
            st.divider()
            st.markdown("##### System Breakdown")
            for evt in db["events"]:
                rev = evt["tickets_sold"] * evt["price_per_ticket"]
                st.write(f"**{evt['title']}** | Sold: `{evt['tickets_sold']}/{evt['tickets_total']}` | Total Revenue: `BWP {rev:,.2f}`")

        with tab_events:
            df_events = pd.DataFrame(db["events"])
            if not df_events.empty:
                df_events["Total Revenue (BWP)"] = df_events["tickets_sold"] * df_events["price_per_ticket"]
                st.dataframe(df_events, use_container_width=True, hide_index=True)

        with tab_venue_mgmt:
            col_v1, col_v2 = st.columns(2, gap="large")
            with col_v1:
                st.markdown("##### Facility Profiles")
                st.dataframe(pd.DataFrame(db["venues"]), use_container_width=True, hide_index=True)
            with col_v2:
                st.markdown("##### Associated Subcontractors")
                st.dataframe(pd.DataFrame(db["services"]), use_container_width=True, hide_index=True)

        with tab_billing:
            col_b1, col_b2, col_b3 = st.columns(3)
            total_rev = sum(e["tickets_sold"] * e["price_per_ticket"] for e in db["events"])
            platform_fee = total_rev * 0.05
            net_payout = total_rev - platform_fee
            
            col_b1.metric("Gross Platform Revenue", f"BWP {total_rev:,.2f}")
            col_b2.metric("Platform Retention (5.0%)", f"BWP {platform_fee:,.2f}")
            col_b3.metric("Net Facility Payout", f"BWP {net_payout:,.2f}")

    # --- ROLE B: VENUE MANAGER ---
    elif user_role == "Venue Manager":
        st.warning("**Scope: Venue Operations.** Data view filtered strictly to assigned facility spaces and events.")
        
        tab_events, tab_venue_mgmt, tab_billing = st.tabs([
            "Manage In-House Events", "Facility Settings & Services", "Venue Settlement Statement"
        ])
        
        with tab_events:
            with st.expander("➕ Publish New Event"):
                with st.form("new_event_form"):
                    new_title = st.text_input("Event Designation")
                    new_date = st.date_input("Scheduled Date")
                    venue_names = [v["name"] for v in db["venues"]]
                    new_loc = st.selectbox("Venue Facility Location", venue_names)
                    new_total = st.number_input("Maximum Capacity Allocation", min_value=1, value=100)
                    new_price = st.number_input("Unit Price (BWP)", min_value=0.0, value=250.0)
                    new_flyer = st.text_input("Flyer Image URL", value="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800")
                    new_desc = st.text_area("Description Summary", value="Official scheduled event.")
                    
                    if st.form_submit_button("Publish Event Entry"):
                        matched_v = next((v for v in db["venues"] if v["name"] == new_loc), db["venues"][0])
                        new_evt_obj = {
                            "event_id": f"evt_{len(db['events']) + 101}",
                            "title": new_title,
                            "date": str(new_date),
                            "location": new_loc,
                            "venue_id": matched_v["venue_id"],
                            "tickets_total": new_total,
                            "tickets_sold": 0,
                            "price_per_ticket": new_price,
                            "flyer_image_url": new_flyer,
                            "description": new_desc
                        }
                        db["events"].append(new_evt_obj)
                        save_data(db)
                        st.success(f"Record '{new_title}' published!")
                        st.rerun()

            df_events = pd.DataFrame(db["events"])
            if not df_events.empty:
                st.dataframe(df_events, use_container_width=True, hide_index=True)

        with tab_venue_mgmt:
            col_v_add, col_s_add = st.columns(2, gap="large")
            
            with col_v_add:
                with st.expander("➕ Register New Venue / Facility", expanded=True):
                    with st.form("add_venue_form"):
                        v_name = st.text_input("Venue Name", placeholder="e.g. Royal Aria Stadium")
                        v_address = st.text_input("Physical Address", placeholder="e.g. Plot 101, Tlokweng")
                        v_capacity = st.number_input("Maximum Guest Capacity", min_value=10, value=1000)
                        v_email = st.text_input("Manager Contact Email", placeholder="e.g. admin@venue.bw")
                        
                        if st.form_submit_button("Save Venue Profile"):
                            if v_name and v_address:
                                new_venue = {
                                    "venue_id": f"v_{len(db['venues']) + 101}",
                                    "name": v_name,
                                    "address": v_address,
                                    "capacity": v_capacity,
                                    "manager_email": v_email
                                }
                                db["venues"].append(new_venue)
                                save_data(db)
                                st.success(f"Venue '{v_name}' successfully added!")
                                st.rerun()

            with col_s_add:
                with st.expander("➕ Add Venue Service / Vendor", expanded=True):
                    with st.form("add_service_form"):
                        s_title = st.text_input("Service Description", placeholder="e.g. Stage Lighting")
                        s_cat = st.selectbox("Category", ["Catering & Refreshments", "Audio & Visual", "Security & Crowd Control", "Decoration"])
                        s_provider = st.text_input("Provider / Company Name", placeholder="e.g. Kalahari Sound")
                        
                        if st.form_submit_button("Register Service"):
                            if s_title and s_provider:
                                new_service = {
                                    "service_id": f"srv_{len(db['services']) + 101}",
                                    "title": s_title,
                                    "category": s_cat,
                                    "provider_name": s_provider,
                                    "status": "Active"
                                }
                                db["services"].append(new_service)
                                save_data(db)
                                st.success(f"Service '{s_title}' successfully registered!")
                                st.rerun()

            st.divider()
            col_tbl1, col_tbl2 = st.columns(2, gap="large")
            with col_tbl1:
                st.markdown("##### Registered Facilities")
                st.dataframe(pd.DataFrame(db["venues"]), use_container_width=True, hide_index=True)
            with col_tbl2:
                st.markdown("##### Associated Facility Services")
                st.dataframe(pd.DataFrame(db["services"]), use_container_width=True, hide_index=True)

        with tab_billing:
            st.subheader("Venue Settlement Statement")
            st.info("Settlements are processed on a rolling 7-day cycle net of platform service processing fees.")
            st.write("**Processed Ticket Sales:** BWP 5,250.00")
            st.write("**Platform Overhead Fee (5.0%):** -BWP 262.50")
            st.write("**Net Funds Disbursed:** BWP 4,987.50")

    # --- ROLE C: VENDOR / PROMOTER ---
    elif user_role == "Vendor / Promoter":
        st.success("**Scope: Affiliate Promotion.** Access restricted to promotional toolsets and assigned referral metrics.")
        
        tab_flyer_builder, tab_commissions = st.tabs(["Flyer & Link Distribution", "Affiliate Earnings"])
        
        with tab_flyer_builder:
            col_f1, col_f2 = st.columns(2, gap="large")
            with col_f1:
                evt_titles = [e["title"] for e in db["events"]]
                sel_title = st.selectbox("Target Event", evt_titles)
                sel_evt = next(e for e in db["events"] if e["title"] == sel_title)
                sel_v = db["vendors"][0]
                
                st.text_input("Active Promoter Profile", value=sel_v["name"], disabled=True)
                custom_flyer_url = st.text_input("Flyer Image Endpoint URL", value=sel_evt.get("flyer_image_url", ""))
                if custom_flyer_url != sel_evt.get("flyer_image_url"):
                    sel_evt["flyer_image_url"] = custom_flyer_url
                    save_data(db)

            with col_f2:
                interactive_booking_link = f"{base_domain}/?vendor={sel_v['vendor_id']}&event={sel_evt['event_id']}"
                whatsapp_caption = f"Tickets for {sel_evt['title']} are available at:\n{interactive_booking_link}"
                encoded_wa = urllib.parse.quote(whatsapp_caption)
                wa_share_url = f"https://wa.me/?text={encoded_wa}"
                
                if sel_evt.get("flyer_image_url"):
                    st.image(sel_evt["flyer_image_url"], caption=f"Asset Preview: {sel_evt['title']}", use_container_width=True)
                    
                st.text_input("Trackable Booking URL", value=interactive_booking_link)
                st.markdown(
                    f'<a href="{wa_share_url}" target="_blank"><button style="background-color:#0F172A; color:white; padding:10px 16px; border-radius:4px; border:none; width:100%;">Dispatch to WhatsApp</button></a>',
                    unsafe_allow_html=True
                )

        with tab_commissions:
            st.subheader("Affiliate Commission Statement")
            st.write("**Total Commission Accrued:** BWP 525.00")
            st.write("**Payout Status:** Settled")
