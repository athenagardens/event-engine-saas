import streamlit as st
import json
import os

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
    return {"venues": [], "supporters": [], "events": [], "bookings": []}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# ---------------------------------------------------------
# 2. APP CONFIGURATION & ENTERPRISE CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Central Venue & Event SaaS Gateway",
    page_icon="🏢",
    layout="wide"
)

def inject_enterprise_styles():
    st.markdown("""
        <style>
            /* Base background & typography */
            .main {
                background-color: #F8FAFC;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            h1, h2, h3, h4, h5 {
                color: #0F172A !important;
                font-weight: 700 !important;
                letter-spacing: -0.02em;
            }
            p, label, span {
                color: #334155;
            }
            
            /* Sidebar Custom Styling */
            [data-testid="stSidebar"] {
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }
            [data-testid="stSidebar"] h1, 
            [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3, 
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p {
                color: #F1F5F9 !important;
            }
            
            /* Custom Cards & Containers */
            .metric-card {
                background: #FFFFFF;
                padding: 1.25rem;
                border-radius: 10px;
                border: 1px solid #E2E8F0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .profile-header-card {
                background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                padding: 1.5rem 2rem;
                border-radius: 12px;
                color: #FFFFFF !important;
                margin-bottom: 1.5rem;
            }
            .profile-header-card h2, .profile-header-card p {
                color: #FFFFFF !important;
            }
            
            /* Buttons */
            .stButton>button {
                background-color: #2563EB;
                color: #FFFFFF;
                border-radius: 8px;
                border: none;
                font-weight: 600;
                padding: 0.5rem 1rem;
                transition: all 0.2s ease;
            }
            .stButton>button:hover {
                background-color: #1D4ED8;
                box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
            }
            
            /* Form inputs styling */
            div[data-baseweb="input"] {
                border-radius: 6px;
            }
        </style>
    """, unsafe_allow_html=True)

inject_enterprise_styles()

# ---------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown("## 🏢 SaaS Platform")
st.sidebar.caption("Central Gateway for Facilities & Service Providers")
st.sidebar.divider()

user_role = st.sidebar.radio(
    "Active Interface Console:",
    [
        "Facility Owner (Venue)",
        "Facility Supporter (Vendor)",
        "Super User (Platform Admin)"
    ]
)

st.sidebar.divider()
with st.sidebar.expander("⚙️ System Utilities"):
    if st.button("Purge & Reset Database", type="primary", use_container_width=True):
        db = {"venues": [], "supporters": [], "events": [], "bookings": []}
        save_data(db)
        st.success("Database purged successfully.")
        st.rerun()

# ---------------------------------------------------------
# 4. MODULE 1: FACILITY OWNER PORTAL
# ---------------------------------------------------------
if user_role == "Facility Owner (Venue)":
    st.title("🏢 Facility Owner Management Console")
    st.caption("Manage your primary facility, configure event spaces, and review service partners.")
    st.divider()

    venues_list = db.get("venues", [])

    if not venues_list:
        st.info("👋 Welcome! Please complete your primary facility onboarding form below.")
        
        with st.form("facility_registration_form"):
            st.markdown("### 🏛️ Facility Onboarding Profile")
            st.caption("Provide accurate operational information to publish your facility onto the platform.")
            
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Facility / Venue Name*", placeholder="e.g. Royal Aria Convention Center")
                f_type = st.selectbox(
                    "Facility Type / Category*",
                    ["Convention Center", "Hotel Ballroom", "Outdoor Arena / Park", "Community Hall", "Stadium", "Nightclub / Lounge", "Private Estate"]
                )
                f_email = st.text_input("Manager Contact Email*", placeholder="manager@venue.com")
                f_phone = st.text_input("Phone / WhatsApp Contact*", placeholder="+267 71 234 567")
            
            with col2:
                f_address = st.text_input("Physical Address / Location*", placeholder="Plot 102, Tlokweng Road, Gaborone")
                f_max_cap = st.number_input("Maximum Guest Capacity*", min_value=10, value=1000, step=50)
                f_tax_id = st.text_input("Tax / Business Registration Number*", placeholder="e.g. CIPA-2023-8901")
                f_bank = st.text_input("Payout Account Details", placeholder="Bank Name, Branch Code, Account Number")

            f_image = st.text_input(
                "Main Facility Cover Image URL",
                value="https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800"
            )
            
            submit_fac = st.form_submit_button("Complete Facility Registration", use_container_width=True)

            if submit_fac:
                if f_name and f_address and f_email and f_phone and f_tax_id:
                    new_venue = {
                        "venue_id": f"v_{len(venues_list) + 101}",
                        "name": f_name,
                        "type": f_type,
                        "address": f_address,
                        "manager_email": f_email,
                        "phone": f_phone,
                        "max_capacity": f_max_cap,
                        "tax_id": f_tax_id,
                        "bank_details": f_bank,
                        "status": "Active",
                        "flyer_image_url": f_image,
                        "spaces": []
                    }
                    db.setdefault("venues", []).append(new_venue)
                    save_data(db)
                    st.success(f"🎉 Facility '{f_name}' successfully onboarded!")
                    st.rerun()
                else:
                    st.error("Please fill in all mandatory fields marked with (*).")

    else:
        cur_v = venues_list[0]
        v_name = cur_v.get("name", "Unnamed Facility")
        v_type = cur_v.get("type", "General Facility")
        v_address = cur_v.get("address", "N/A")
        v_phone = cur_v.get("phone", "N/A")
        v_email = cur_v.get("manager_email", "N/A")
        v_tax = cur_v.get("tax_id", "N/A")
        v_cap = cur_v.get("max_capacity", 0)

        # Header Profile Card
        st.markdown(f"""
            <div class="profile-header-card">
                <h2>🏛️ {v_name}</h2>
                <p><b>Type:</b> {v_type} &nbsp;|&nbsp; <b>Location:</b> {v_address} &nbsp;|&nbsp; <b>Max Overall Occupancy:</b> {v_cap:,} Guests</p>
                <p style="font-size: 0.85rem; opacity: 0.8; margin-top: 5px;">
                    Contact: {v_phone} &nbsp;|&nbsp; Email: {v_email} &nbsp;|&nbsp; Tax/Registration ID: {v_tax}
                </p>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("⚙️ Account Settings / Unlink Profile"):
            st.warning("Unlinking this profile will remove the facility from your active workspace.")
            if st.button("Unlink & Clear This Facility Profile"):
                db["venues"] = []
                save_data(db)
                st.rerun()

        t_spaces, t_events, t_vendors = st.tabs([
            "Configured Sub-Spaces", 
            "Facility Events", 
            "Approved Service Network"
        ])

        with t_spaces:
            st.markdown("#### Manage Facility Hire Spaces & Halls")
            with st.form("add_space_form"):
                col_a, col_b, col_c = st.columns([3, 2, 2])
                with col_a:
                    s_name = st.text_input("Space Name", placeholder="e.g. Grand Ballroom")
                with col_b:
                    s_cap = st.number_input("Space Capacity", min_value=1, value=250)
                with col_c:
                    s_rate = st.number_input("Daily Hire Rate (BWP)", min_value=0.0, value=3500.0)
                
                if st.form_submit_button("Add Area / Hall"):
                    if s_name:
                        cur_v.setdefault("spaces", []).append({
                            "space_id": f"sp_{len(cur_v.get('spaces', []))+101}",
                            "name": s_name,
                            "capacity": s_cap,
                            "daily_rate": s_rate
                        })
                        save_data(db)
                        st.success(f"Added space '{s_name}'!")
                        st.rerun()

            st.divider()
            st.markdown("##### Configured Areas")
            spaces = cur_v.get("spaces", [])
            if spaces:
                for sp in spaces:
                    st.write(f"• **{sp.get('name')}** — Capacity: {sp.get('capacity'):,} guests | Daily Rate: **BWP {sp.get('daily_rate', 0):,.2f}**")
            else:
                st.info("No sub-spaces configured yet.")

        with t_events:
            st.markdown("#### Published Facility Events")
            st.info("Configure events hosted at your venue from this section.")

        with t_vendors:
            st.markdown("#### Registered Supporter Network")
            supporters = db.get("supporters", [])
            if supporters:
                for sup in supporters:
                    with st.container():
                        st.markdown(f"""
                        **{sup.get('business_name')}** (`{sup.get('category')}`)  
                        * **Contact:** {sup.get('contact_person')} ({sup.get('phone')} | {sup.get('email')})  
                        * **Service Area:** {sup.get('service_area')} | **Compliance:** {'✅ Public Liability Insured' if sup.get('has_insurance') else '⚠️ Unverified Insurance'}
                        """)
                        st.divider()
            else:
                st.info("No facility supporters have joined the platform network yet.")

# ---------------------------------------------------------
# 5. MODULE 2: FACILITY SUPPORTER PORTAL
# ---------------------------------------------------------
elif user_role == "Facility Supporter (Vendor)":
    st.title("🛠️ Facility Supporter Onboarding Portal")
    st.caption("Register your business to supply catering, AV, decor, or equipment to venue events.")
    st.divider()

    with st.form("supporter_registration_form"):
        st.markdown("### 🤝 Supporter Profile Onboarding")
        
        col1, col2 = st.columns(2)
        with col1:
            s_biz_name = st.text_input("Business Trading Name*", placeholder="e.g. Kalahari Floral & Stage Decor")
            s_category = st.selectbox(
                "Primary Service Category*",
                [
                    "Catering & Mobile Bar",
                    "Security, Bouncers & Access Control",
                    "Sound, Stage & Lighting (AV)",
                    "Decor, Floral & Stage Design",
                    "Cleaning & Sanitation Services",
                    "Photography & Videography",
                    "Medical & First Aid Standby",
                    "Equipment & Tent Rental"
                ]
            )
            s_person = st.text_input("Primary Contact Person*", placeholder="Jane Smith")
            s_email = st.text_input("Official Email Address*", placeholder="contact@kalaharidecor.bw")

        with col2:
            s_phone = st.text_input("Direct Phone / WhatsApp*", placeholder="+267 72 100 200")
            s_area = st.text_input("Service Coverage Area*", placeholder="e.g. Gaborone & Greater South-East")
            s_pricing = st.selectbox("Pricing Structure", ["Fixed Package Rates", "Hourly Service Rate", "Custom Quote Request Only"])
            s_portfolio = st.text_input("Portfolio / Website / Instagram Link", placeholder="https://instagram.com/yourbusiness")

        st.markdown("#### 📋 Operational Compliance & Verification")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            s_insurance = st.checkbox("Holds Active Public Liability Insurance")
        with col_c2:
            s_safety = st.checkbox("Holds Valid Health & Safety / Food Safety Certificates")

        submit_sup = st.form_submit_button("Register Supporter Account", use_container_width=True)

        if submit_sup:
            if s_biz_name and s_person and s_email and s_phone and s_area:
                new_supporter = {
                    "supporter_id": f"sup_{len(db.get('supporters', []))+101}",
                    "business_name": s_biz_name,
                    "category": s_category,
                    "contact_person": s_person,
                    "email": s_email,
                    "phone": s_phone,
                    "service_area": s_area,
                    "pricing_model": s_pricing,
                    "portfolio": s_portfolio,
                    "has_insurance": s_insurance,
                    "has_safety_cert": s_safety,
                    "status": "Verified"
                }
                db.setdefault("supporters", []).append(new_supporter)
                save_data(db)
                st.success(f"🎉 Supporter profile '{s_biz_name}' successfully registered!")
                st.rerun()
            else:
                st.error("Please complete all mandatory fields marked with (*).")

# ---------------------------------------------------------
# 6. MODULE 3: SUPER USER PLATFORM ADMIN
# ---------------------------------------------------------
elif user_role == "Super User (Platform Admin)":
    st.title("📊 Master Executive Control Panel")
    st.caption("Platform-wide analytics and account audit logs.")
    st.divider()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Facilities", len(db.get("venues", [])))
    with m2:
        st.metric("Total Supporters / Vendors", len(db.get("supporters", [])))
    with m3:
        st.metric("Total System Events", len(db.get("events", [])))

    st.markdown("---")
    t_v, t_s = st.tabs(["Registered Facilities Ledger", "Registered Supporters Ledger"])

    with t_v:
        st.json(db.get("venues", []))

    with t_s:
        st.json(db.get("supporters", []))
