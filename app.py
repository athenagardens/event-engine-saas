import streamlit as st
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import urllib.request

# --- CONFIGURATION & DATABASE SETUP ---
DB_FILE = "marketplace_db.json"

def load_data():
    if not os.path.exists(DB_FILE):
        default_data = {
            "events": [
                {
                    "event_id": "evt_101",
                    "title": "Summer Music Festival 2026",
                    "date": "2026-10-15",
                    "location": "Central Park Arena",
                    "tickets_total": 100,
                    "tickets_sold": 15,
                    "price_per_ticket": 45.0,
                    "flyer_image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800"
                }
            ],
            "vendors": [
                {
                    "vendor_id": "v_alice",
                    "name": "Alice Promos",
                    "email": "alice@example.com"
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

# --- HELPER FUNCTION: EMAIL FLYER & LINK ---
def send_flyer_email(recipient_email, event_name, flyer_image_url, checkout_link):
    """
    Sends an email with the direct booking link and the high-res flyer image attached.
    To use automated sending via Gmail SMTP, populate sender credentials in st.secrets.
    """
    sender_email = st.secrets.get("SMTP_EMAIL", "your_platform_email@gmail.com")
    sender_password = st.secrets.get("SMTP_PASSWORD", "")

    if not sender_password:
        return False, "SMTP credentials not configured. Displaying draft below instead!"

    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"📲 Flyer & Booking Link for: {event_name}"
        msg['From'] = sender_email
        msg['To'] = recipient_email

        body = (
            f"Hello!\n\nHere is your official flyer graphic for {event_name}.\n\n"
            f"--- WHATSAPP CAPTION & LINK ---\n"
            f"Get your tickets here before they sell out!\n"
            f"Book now: {checkout_link}\n\n"
            f"Instructions for WhatsApp:\n"
            f"1. Save/Download the attached flyer image to your phone photos.\n"
            f"2. Tap Share -> WhatsApp.\n"
            f"3. Paste the booking link above into your caption box!"
        )
        msg.attach(MIMEText(body, 'plain'))

        # Download and attach image
        if flyer_image_url:
            req = urllib.request.Request(flyer_image_url, headers={'User-Agent': 'Mozilla/5.0'})
            img_data = urllib.request.urlopen(req).read()
            image = MIMEImage(img_data, name="flyer_graphic.jpg")
            msg.attach(image)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

# --- APP LAYOUT & ROUTING ---
st.set_page_config(page_title="Ticket Platform & Vendor Hub", layout="wide")

# Get domain or fall back to local IP/localhost
base_domain = st.secrets.get("APP_DOMAIN", "http://localhost:8501")

# Detect incoming URL parameters (Customer Checkout View)
query_params = st.query_params
param_vendor = query_params.get("vendor")
param_event = query_params.get("event")

# ---------------------------------------------------------
# ROUTE 1: CUSTOMER CHECKOUT PAGE
# ---------------------------------------------------------
if param_vendor and param_event:
    st.title("🎟️ Ticket Checkout")
    
    # Locate Event
    sel_evt = next((e for e in db["events"] if e["event_id"] == param_event), None)
    sel_v = next((v for v in db["vendors"] if v["vendor_id"] == param_vendor), None)
    
    if sel_evt:
        col_img, col_form = st.columns([1, 1])
        
        with col_img:
            if sel_evt.get("flyer_image_url"):
                st.image(sel_evt["flyer_image_url"], use_container_width=True)
            st.caption(f"Promoted by Official Partner: **{sel_v['name'] if sel_v else 'Partner'}**")
            
        with col_form:
            st.subheader(sel_evt["title"])
            st.write(f"📅 **Date:** {sel_evt['date']}")
            st.write(f"📍 **Location:** {sel_evt['location']}")
            st.write(f"💰 **Price:** ${sel_evt['price_per_ticket']:.2f}")
            
            tickets_left = sel_evt["tickets_total"] - sel_evt["tickets_sold"]
            st.metric("Tickets Remaining", tickets_left)
            
            if tickets_left > 0:
                with st.form("checkout_form"):
                    cust_name = st.text_input("Full Name")
                    cust_email = st.text_input("Email Address")
                    qty = st.number_input("Quantity", min_value=1, max_value=tickets_left, value=1)
                    submitted = st.form_submit_button("Complete Purchase")
                    
                    if submitted and cust_name and cust_email:
                        # Process Sale
                        sel_evt["tickets_sold"] += qty
                        save_data(db)
                        st.success(f"🎉 Success! {qty} ticket(s) purchased. Confirmation sent to {cust_email}.")
                        st.balloons()
            else:
                st.error("This event is sold out!")
    else:
        st.error("Event not found.")

# ---------------------------------------------------------
# ROUTE 2: VENDOR DASHBOARD
# ---------------------------------------------------------
else:
    st.title("🎪 Vendor Dashboard & Promotional Hub")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "🎫 Manage Events", 
        "🤝 Partner Vendors", 
        "📧 Email Flyer & Promo Link"
    ])
    
    with tab1:
        st.subheader("Event Performance")
        for evt in db["events"]:
            st.write(f"**{evt['title']}** - Sold: {evt['tickets_sold']}/{evt['tickets_total']}")
            
    with tab2:
        st.subheader("Active Events")
        st.json(db["events"])
        
    with tab3:
        st.subheader("Registered Vendors")
        st.json(db["vendors"])
        
    with tab4:
        st.subheader("📧 Send Flyer & Checkout Link via Email")
        st.write(
            "Select an event and enter an email address. We will email you the full-resolution "
            "flyer image attachment along with your unique referral booking link for WhatsApp promotion."
        )
        
        col_select1, col_select2 = st.columns(2)
        
        with col_select1:
            evt_titles = [e["title"] for e in db["events"]]
            selected_evt_title = st.selectbox("Select Event", evt_titles)
            sel_evt = next(e for e in db["events"] if e["title"] == selected_evt_title)
            
        with col_select2:
            v_names = [v["name"] for v in db["vendors"]]
            selected_v_name = st.selectbox("Select Partner Vendor", v_names)
            sel_v = next(v for v in db["vendors"] if v["name"] == selected_v_name)
            
        # Dynamic Direct Booking Link Construction
        direct_link = f"{base_domain}/?vendor={sel_v['vendor_id']}&event={sel_evt['event_id']}"
        
        st.divider()
        
        # EMAIL SENDER FORM
        st.markdown("#### 1. Dispatch Flyer to Email")
        
        with st.form("send_email_form"):
            target_email = st.text_input("Destination Email Address", value=sel_v.get("email", ""))
            send_btn = st.form_submit_button("📩 Send Flyer & Link To Email")
            
            if send_btn and target_email:
                success, msg = send_flyer_email(
                    recipient_email=target_email,
                    event_name=sel_evt["title"],
                    flyer_image_url=sel_evt.get("flyer_image_url", ""),
                    checkout_link=direct_link
                )
                if success:
                    st.success(msg)
                else:
                    st.info(f"Draft Generated ({msg})")
        
        st.divider()
        
        # PREVIEW & MANUAL DOWNLOAD SECTION
        st.markdown("#### 2. Manual Preview & Download Option")
        col_prev1, col_prev2 = st.columns([1, 1])
        
        with col_prev1:
            if sel_evt.get("flyer_image_url"):
                st.image(sel_evt["flyer_image_url"], caption="Flyer Image Attachment", use_container_width=True)
                
        with col_prev2:
            st.text_area("Copyable WhatsApp Caption Text", value=f"Grab your tickets for {sel_evt['title']} here:\n{direct_link}", height=120)
            
            if sel_evt.get("flyer_image_url"):
                st.markdown(
                    f'<a href="{sel_evt["flyer_image_url"]}" target="_blank" download="flyer.jpg" style="text-decoration:none;">'
                    f'<button style="background-color:#0284C7; color:white; font-weight:700; '
                    f'padding:10px 16px; border-radius:6px; border:none; cursor:pointer; width:100%;">'
                    f'💾 Download Flyer Image File Direct</button></a>',
                    unsafe_allow_html=True
                )
