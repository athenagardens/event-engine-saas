import streamlit as st
import json
import os

# --- CONFIGURACIÓN DE BASE DE DATOS ---
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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Enterprise Event Platform", layout="wide", page_icon="🎪")
st.title("🎪 Enterprise Event & Venue Management Platform")

# --- NAVEGACIÓN LATERAL ---
st.sidebar.header("Navigation & Role Portal")
user_role = st.sidebar.selectbox(
    "Select Your Role / Portal:",
    [
        "Facility Owner (Venue)",
        "Facility Supporter (Vendor/Supplier)",
        "Platform Admin / Overview"
    ]
)

st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Developer Tools"):
    if st.button("Reset Entire Database", type="primary"):
        db = {"venues": [], "supporters": [], "events": [], "bookings": []}
        save_data(db)
        st.success("Database cleared!")
        st.rerun()


# =========================================================
# ROLE 1: FACILITY OWNER PORTAL
# =========================================================
if user_role == "Facility Owner (Venue)":
    st.subheader("🏢 Facility Owner Management Portal")

    if not db.get("venues"):
        st.info("👋 Welcome! Register your primary facility profile below to begin managing spaces and hosting events.")
        
        with st.form("facility_registration_form"):
            st.markdown("### 🏛️ Facility Onboarding (Industry Standard Profile)")
            
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Facility / Venue Name*", placeholder="e.g. Royal Aria Convention Center")
                f_type = st.selectbox(
                    "Facility Type / Category*",
                    ["Convention Center", "Hotel Ballroom", "Outdoor Arena / Park", "Community Hall", "Stadium", "Nightclub / Lounge", "Private Estate"]
                )
                f_email = st.text_input("Official Contact Email*", placeholder="manager@venue.com")
                f_phone = st.text_input("Phone / WhatsApp Number*", placeholder="+267 71 234 567")
            
            with col2:
                f_address = st.text_input("Physical Location / Address*", placeholder="Plot 102, Tlokweng Road, Gaborone")
                f_max_cap = st.number_input("Overall Facility Max Capacity (Guests)*", min_value=10, value=1000, step=50)
                f_tax_id = st.text_input("Tax / Business Reg Number (VAT/CIPA)", placeholder="e.g. CIPA-2023-8901")
                f_bank = st.text_input("Payout Bank & Account Details", placeholder="Bank Name, Branch Code, Account Number")

            f_image = st.text_input(
                "Main Facility Cover Photo URL",
                value="https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800"
            )
            
            submit_fac = st.form_submit_button("Submit & Register Facility Profile")

            if submit_fac:
                if f_name and f_address and f_email and f_phone and f_tax_id:
                    new_venue = {
                        "venue_id": f"v_{len(db['venues']) + 101}",
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
                    db["venues"].append(new_venue)
                    save_data(db)
                    st.success(f"🎉 '{f_name}' has been successfully registered!")
                    st.rerun()
                else:
                    st.error("Please fill in all mandatory fields marked with (*).")

    else:
        # Lectura segura de los campos del establecimiento activo
        cur_v = db["venues"][0]
        v_name = cur_v.get("name", "Unnamed Facility")
        v_type = cur_v.get("type", "General Venue")
        v_address = cur_v.get("address", "N/A")
        v_phone = cur_v.get("phone", "N/A")
        v_email = cur_v.get("manager_email", "N/A")
        v_tax = cur_v.get("tax_id", "N/A")
        
        st.success(f"📌 **Active Facility:** {v_name} ({v_type}) | 📍 {v_address}")
        st.caption(f"Contact: {v_phone} | Email: {v_email} | Tax ID: {v_tax}")

        with st.expander("⚙️ Manage Facility Profile"):
            if st.button("Unlink Facility & Clear Profile"):
                db["venues"] = []
                save_data(db)
                st.rerun()

        t_spaces, t_events, t_vendors = st.tabs([
            "Configured Sub-Spaces", 
            "Facility Events", 
            "Approved Facility Supporters"
        ])

        with t_spaces:
            st.markdown(f"#### Add Hire Spaces / Areas within {v_name}")
            with st.form("add_space_form"):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    s_name = st.text_input("Area / Room Name", placeholder="e.g. VIP Ballroom")
                with col_b:
                    s_cap = st.number_input("Area Max Capacity", min_value=1, value=250)
                with col_c:
                    s_rate = st.number_input("Daily Hire Price (BWP)", min_value=0.0, value=5000.0)
                
                if st.form_submit_button("Add Area"):
                    if s_name:
                        cur_v.setdefault("spaces", []).append({
                            "space_id": f"sp_{len(cur_v.get('spaces', []))+101}",
                            "name": s_name,
                            "capacity": s_cap,
                            "daily_rate": s_rate
                        })
                        save_data(db)
                        st.success(f"Added area '{s_name}'!")
                        st.rerun()

            st.markdown("##### Existing Areas")
            spaces = cur_v.get("spaces", [])
            if spaces:
                for sp in spaces:
                    st.write(f"• **{sp.get('name')}** — Capacity: {sp.get('capacity')} guests | Rate: **BWP {sp.get('daily_rate', 0):,.2f}/day**")
            else:
                st.info("No individual sub-spaces added yet.")

        with t_vendors:
            st.markdown("#### Registered Facility Supporters / Service Network")
            if db.get("supporters"):
                for sup in db["supporters"]:
                    st.markdown(f"""
                    * **{sup.get('business_name')}** (`{sup.get('category')}`)
                      * **Contact:** {sup.get('contact_person')} ({sup.get('phone')} | {sup.get('email')})
                      * **Coverage:** {sup.get('service_area')} | **Compliance:** {'✅ Insurance Verified' if sup.get('has_insurance') else '⚠️ No Insurance Recorded'}
                    """)
            else:
                st.info("No facility supporters have registered on the platform yet.")


# =========================================================
# ROLE 2: FACILITY SUPPORTER (VENDOR / SUPPLIER) PORTAL
# =========================================================
elif user_role == "Facility Supporter (Vendor/Supplier)":
    st.subheader("🛠️ Facility Supporter & Vendor Registration Portal")
    st.caption("Register your business to partner with facilities and event organizers on the platform.")

    with st.form("supporter_registration_form"):
        st.markdown("### 🤝 Supporter Business Onboarding")
        
        col1, col2 = st.columns(2)
        with col1:
            s_biz_name = st.text_input("Business / Trading Name*", placeholder="e.g. Apex Security & VIP Protection")
            s_category = st.selectbox(
                "Primary Service Category*",
                [
                    "Catering & Mobile Bar",
                    "Security, Bouncers & Access Control",
                    "Sound, Stage & Lighting (AV)",
                    "Decor, Floral & Stage Design",
                    "Cleaning & Sanitation",
                    "Photography & Videography",
                    "Medical & First Aid Standby",
                    "Equipment & Tent Hire"
                ]
            )
            s_person = st.text_input("Primary Contact Person*", placeholder="John Doe")
            s_email = st.text_input("Contact Email Address*", placeholder="info@apexsecurity.co.bw")

        with col2:
            s_phone = st.text_input("Direct Phone / WhatsApp*", placeholder="+267 72 000 111")
            s_area = st.text_input("Service Coverage Region*", placeholder="e.g. Gaborone & Greater South-East")
            s_pricing = st.selectbox("Pricing Model", ["Fixed Package Rates", "Hourly Rate", "Custom Quote Request Only"])
            s_portfolio = st.text_input("Portfolio / Website / Social Link", placeholder="https://instagram.com/yourbusiness")

        st.markdown("#### 📋 Compliance & Operational Readiness")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            s_insurance = st.checkbox("Holds Public Liability Insurance Policy")
        with col_c2:
            s_safety = st.checkbox("Holds Valid Health & Safety / Food Safety Compliance Certificates")

        submit_sup = st.form_submit_button("Register as Approved Supporter")

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
                st.success(f"🎉 Supporter '{s_biz_name}' successfully registered!")
                st.rerun()
            else:
                st.error("Please complete all mandatory fields marked with (*).")


# =========================================================
# ROLE 3: PLATFORM ADMIN OVERVIEW
# =========================================================
elif user_role == "Platform Admin / Overview":
    st.subheader("📊 Platform Master Overview")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Facilities Registered", len(db.get("venues", [])))
    with col_m2:
        st.metric("Total Supporters Registered", len(db.get("supporters", [])))

    st.markdown("---")
    st.markdown("### 🏢 Facilities Summary")
    st.json(db.get("venues", []))

    st.markdown("### 🛠️ Supporters Summary")
    st.json(db.get("supporters", []))
