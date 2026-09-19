import streamlit as st
import json
import os
import urllib.parse
import io
from fpdf import FPDF

# --- CONFIGURATION & DATABASE SETUP ---
DB_FILE = "marketplace_db.json"

def load_data():
    if not os.path.exists(DB_FILE):
        default_data = {
            "venues": [
                {
                    "venue_id": "v_central_park",
                    "name": "Central Park Arena",
                    "address": "123 Park Ave, New York, NY",
                    "capacity": 5000,
                    "manager_email": "venue_admin@example.com"
                }
            ],
            "events": [
                {
                    "event_id": "evt_101",
                    "title": "Summer Music Festival 2026",
                    "date": "2026-10-15",
                    "location": "Central Park Arena",
                    "venue_id": "v_central_park",
                    "tickets_total": 100,
                    "tickets_sold": 15,
                    "price_per_ticket": 45.0,
                    "flyer_image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
                    "description": "Join us for an unforgettable live music experience in the park!"
                }
            ],
            "vendors": [
                {
                    "vendor_id": "v_alice",
                    "name": "Alice Promos & VIP Booking",
                    "email": "alice@example.com",
                    "bio": "Official VIP ticket partner and promoter."
                }
            ],
            "services": [
                {
                    "service_id": "srv_cat_01",
                    "title": "Gourmet Catering & Bar Services",
                    "category": "Catering & Refreshments",
                    "provider_name": "Apex Hospitality",
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

# --- PDF GENERATOR UTILITY (INVOICES & RECEIPTS) ---
def generate_pdf_receipt(cust_name, cust_email, event_title, qty, price_per_ticket, vendor_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "PLATFORM PAYMENT RECEIPT & TICKET", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "Issued by Platform Global Booking Engine LLC", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Customer Name: {cust_name}", ln=True)
    pdf.cell(0, 8, f"Customer Email: {cust_email}", ln=True)
    pdf.cell(0, 8, f"Promotional Partner: {vendor_name}", ln=True)
    pdf.ln(5)
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Event: {event_title}", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Quantity Purchased: {qty}", ln=True)
    pdf.cell(0, 8, f"Price Per Ticket: ${price_per_ticket:.2f}", ln=True)
    
    total = qty * price_per_ticket
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Total Amount Paid: ${total:.2f}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, "Thank you for your purchase! Present this receipt along with a valid ID at the venue gate for admission.")
    
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin1')
    return bytes(pdf_output)

# --- APP LAYOUT SETUP ---
st.set_page_config(page_title="Event Booking Engine & Venue Manager", layout="wide")
base_domain = st.secrets.get("APP_DOMAIN", "http://localhost:8501")

# Detect query parameters for Customer Checkout Route
query_params = st.query_params
param_vendor = query_params.get("vendor")
param_event = query_params.get("event")

# ---------------------------------------------------------
# ROUTE 1: CUSTOMER CHECKOUT & INTERACTIVE FLYER VIEW
# ---------------------------------------------------------
if param_vendor and param_event:
    st.title("🎟️ Official Interactive Ticket Booking Page")
    
    sel_evt = next((e for e in db["events"] if e["event_id"] == param_event), None)
    sel_v = next((v for v in db["vendors"] if v["vendor_id"] == param_vendor), None)
    
    if sel_evt:
        col_flyer, col_booking = st.columns([1, 1])
        
        with col_flyer:
            st.markdown("### 📢 Event Flyer")
            if sel_evt.get("flyer_image_url"):
                st.image(sel_evt["flyer_image_url"], use_container_width=True)
            st.info(f"🤝 **Promoted By Partner:** {sel_v['name'] if sel_v else 'Official Ticket Hub'}")
            
        with col_booking:
            st.markdown(f"## {sel_evt['title']}")
            st.write(f"📝 **Description:** {sel_evt.get('description', 'Official event tickets.')}")
            st.write(f"📅 **Date:** {sel_evt['date']}")
            st.write(f"📍 **Venue:** {sel_evt['location']}")
            st.write(f"💰 **Ticket Price:** ${sel_evt['price_per_ticket']:.2f}")
            
            tickets_left = sel_evt["tickets_total"] - sel_evt["tickets_sold"]
            st.metric("Tickets Remaining Available", tickets_left)
            
            if tickets_left > 0:
                with st.form("customer_purchase_form"):
                    st.markdown("#### Enter Ticket & Contact Details")
                    cust_name = st.text_input("Full Name", help="Enter your legal full name for gate entry verification.")
                    cust_email = st.text_input("Email Address", help="Your payment receipt and entry pass will be generated for this email.")
                    qty = st.number_input("Number of Tickets", min_value=1, max_value=tickets_left, value=1)
                    submitted = st.form_submit_button("💳 Reserve & Purchase Tickets Now")
                    
                    if submitted and cust_name and cust_email:
                        sel_evt["tickets_sold"] += qty
                        save_data(db)
                        
                        v_name = sel_v['name'] if sel_v else 'Official Ticket Hub'
                        pdf_bytes = generate_pdf_receipt(
                            cust_name=cust_name,
                            cust_email=cust_email,
                            event_title=sel_evt['title'],
                            qty=qty,
                            price_per_ticket=sel_evt['price_per_ticket'],
                            vendor_name=v_name
                        )
                        
                        st.success(f"🎉 Success! {qty} ticket(s) reserved for {cust_name}. Receipt generated!")
                        st.balloons()
                        
                        st.download_button(
                            label="📄 Download Official PDF Receipt & Ticket",
                            data=pdf_bytes,
                            file_name=f"Receipt_{cust_name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("This event is completely sold out!")
    else:
        st.error("Event not found or link has expired.")

# ---------------------------------------------------------
# ROUTE 2: MANAGEMENT HUB & FLYER CREATOR CONSOLE
# ---------------------------------------------------------
else:
    # AUTHENTICATION & ROLE SWITCHER
    st.sidebar.title("🔐 Control Console Access")
    user_role = st.sidebar.selectbox(
        "Select User Role",
        ["Super Admin", "Venue Manager", "Vendor / Promoter"],
        help="Super Admins manage the platform globally. Venue Managers oversee facility events. Vendors generate promotional flyers and booking links."
    )
    
    st.title("🎪 Event Booking Engine & Venue Management Platform")
    
    if user_role == "Super Admin":
        st.info("🌐 **Super Admin Console:** Viewing system-wide venue performance, vendors, billing receipts, and ticket analytics.")
    elif user_role == "Venue Manager":
        st.warning("🏟️ **Venue Management Suite:** Managing in-house events, capacity limits, and service providers.")
    else:
        st.success("🎨 **Vendor & Promoter Hub:** Create interactive flyers, manage promotional events, and generate shareable booking links.")

    # TABS FOR MANAGING EVENTS, FLYERS, AND VENUES
    tab_overview, tab_flyer_builder, tab_events, tab_venue_mgmt, tab_billing = st.tabs([
        "📊 Dashboard Overview", 
        "🎨 Flyer Builder & Link Generator", 
        "🎫 Manage Events & Tickets", 
        "🏟️ Venue & Facility Settings",
        "🧾 Platform Invoicing & Fees"
    ])
    
    # --- TAB 1: OVERVIEW METRICS ---
    with tab_overview:
        st.subheader("Real-Time Sales & Event Performance")
        st.caption("Review gross sales, ticket velocity, and revenue distribution.")
        for evt in db["events"]:
            rev = evt["tickets_sold"] * evt["price_per_ticket"]
            st.write(f"**{evt['title']}** | Sold: `{evt['tickets_sold']}/{evt['tickets_total']}` | Revenue: `${rev:,.2f}`")

    # --- TAB 2: INTERACTIVE FLYER BUILDER & LINK GENERATOR ---
    with tab_flyer_builder:
        st.subheader("🎨 Create & Share Interactive Event Flyers")
        st.write("Generate custom promotional flyers and unique booking links to distribute to your target audience on WhatsApp, social media, or email.")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.markdown("#### 1. Select Event & Vendor Profile")
            evt_titles = [e["title"] for e in db["events"]]
            sel_title = st.selectbox("Select Target Event", evt_titles, help="Choose the event you want to advertise.")
            sel_evt = next(e for e in db["events"] if e["title"] == sel_title)
            
            v_names = [v["name"] for v in db["vendors"]]
            sel_v_name = st.selectbox("Select Promoting Vendor / Profile", v_names, help="Attributes ticket sales directly to your vendor profile.")
            sel_v = next(v for v in db["vendors"] if v["name"] == sel_v_name)
            
            st.markdown("#### 2. Optional Flyer Customization")
            custom_flyer_url = st.text_input("Flyer Image URL", value=sel_evt.get("flyer_image_url", ""), help="Paste an image URL for your promotional event poster.")
            if custom_flyer_url != sel_evt.get("flyer_image_url"):
                sel_evt["flyer_image_url"] = custom_flyer_url
                save_data(db)

        with col_f2:
            # Construct Dynamic Referral Booking Link
            interactive_booking_link = f"{base_domain}/?vendor={sel_v['vendor_id']}&event={sel_evt['event_id']}"
            whatsapp_caption = f"🎟️ Get your tickets for {sel_evt['title']} here:\n{interactive_booking_link}"
            encoded_wa = urllib.parse.quote(whatsapp_caption)
            wa_share_url = f"https://wa.me/?text={encoded_wa}"
            
            st.markdown("#### 3. Interactive Flyer Preview & Share")
            if sel_evt.get("flyer_image_url"):
                st.image(sel_evt["flyer_image_url"], caption=f"Flyer Preview for {sel_evt['title']}", use_container_width=True)
                
            st.text_input("Direct Interactive Booking Link", value=interactive_booking_link, help="Share this link with your audience so they can buy tickets directly.")
            st.text_area("WhatsApp Promo Caption Text", value=whatsapp_caption, height=90)
            
            st.markdown(
                f'<a href="{wa_share_url}" target="_blank" style="text-decoration:none;">'
                f'<button style="background-color:#25D366; color:white; font-weight:700; '
                f'padding:12px 20px; border-radius:8px; border:none; cursor:pointer; width:100%; font-size:16px;">'
                f'📲 Share Flyer & Booking Link Direct to WhatsApp</button></a>',
                unsafe_allow_html=True
            )

    # --- TAB 3: MANAGE EVENTS ---
    with tab_events:
        st.subheader("🎫 Event Management")
        st.write("Create new in-house events, update ticket pricing, or adjust total available inventory.")
        
        with st.expander("➕ Create New Event or In-House Booking"):
            with st.form("new_event_form"):
                new_title = st.text_input("Event Title", help="Name of the event as displayed on customer flyers.")
                new_date = st.date_input("Event Date")
                new_loc = st.text_input("Venue Location", value="Central Park Arena")
                new_total = st.number_input("Total Ticket Capacity", min_value=1, value=100)
                new_price = st.number_input("Price Per Ticket ($)", min_value=0.0, value=25.0)
                new_flyer = st.text_input("Flyer Image URL", value="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800")
                new_desc = st.text_area("Event Description & Details", value="Join us for this exciting event!")
                
                if st.form_submit_button("Publish Event & Enable Booking Link"):
                    new_evt_obj = {
                        "event_id": f"evt_{len(db['events']) + 101}",
                        "title": new_title,
                        "date": str(new_date),
                        "location": new_loc,
                        "venue_id": "v_central_park",
                        "tickets_total": new_total,
                        "tickets_sold": 0,
                        "price_per_ticket": new_price,
                        "flyer_image_url": new_flyer,
                        "description": new_desc
                    }
                    db["events"].append(new_evt_obj)
                    save_data(db)
                    st.success(f"Event '{new_title}' successfully published! You can now build flyers for it in Tab 2.")
                    st.rerun()

        st.json(db["events"])

    # --- TAB 4: VENUE & FACILITY MANAGEMENT ---
    with tab_venue_mgmt:
        st.subheader("🏟️ Venue Infrastructure & Facility Settings")
        st.write("Configure physical venue profiles, maximum capacity limits, and assigned third-party service providers.")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("#### Venue Information")
            st.json(db["venues"])
            
        with col_v2:
            st.markdown("#### Assigned Service Providers & Vendors")
            st.json(db["services"])

    # --- TAB 5: INVOICING & PLATFORM REVENUE ---
    with tab_billing:
        st.subheader("🧾 Platform Invoicing & Fee Structure")
        st.caption("Manage platform service fees, vendor commission splits, and automated invoicing.")
        
        if user_role == "Super Admin":
            st.markdown("#### Platform Global Financial Summary")
            col_b1, col_b2, col_b3 = st.columns(3)
            
            total_rev = sum(e["tickets_sold"] * e["price_per_ticket"] for e in db["events"])
            platform_fee = total_rev * 0.05  # 5% platform cut
            net_payout = total_rev - platform_fee
            
            col_b1.metric("Gross Platform Revenue", f"${total_rev:,.2f}")
            col_b2.metric("Platform Service Fee (5%)", f"${platform_fee:,.2f}")
            col_b3.metric("Net Venue Remittance", f"${net_payout:,.2f}")
            
            st.divider()
            st.markdown("#### Generate Venue Monthly Tax Invoice")
            st.text_input("Billing Entity", value="Central Park Arena LLC")
            st.text_input("Platform Service Fee Rate (%)", value="5.0%")
            st.button("📄 Generate & Dispatch Official Platform Tax Invoice")
            
        elif user_role == "Venue Manager":
            st.markdown("#### Venue Payout Statements & Invoices")
            st.info("Your net sales revenue is automatically remitted to your bank account weekly minus the 5% platform processing fee.")
            st.write("• **Total Ticket Revenue Processed:** $675.00")
            st.write("• **Platform Fees Deducted (5%):** -$33.75")
            st.write("• **Net Remitted Proceeds:** $641.25")
            
        else:
            st.markdown("#### Promotional Affiliate Earnings & Invoices")
            st.info("Promoters receive commission payouts for sales generated using their referral booking links.")
            st.write("• **Total Commission Earned:** $67.50")
            st.write("• **Status:** Remitted")
