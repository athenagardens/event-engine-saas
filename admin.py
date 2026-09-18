import streamlit as st
import json
import os

st.set_page_config(page_title="Athena SaaS - Admin & Vendor Console", page_icon="🔑")

# Load Configuration & Bookings
with open("vendors.json", "r") as f:
    config_data = json.load(f)

# AUTHENTICATION
st.sidebar.title("🔐 Portal Access")
user_role = st.sidebar.selectbox("Login As:", ["Platform Owner (Athena)", "Sub-Vendor (Supplier)"])
auth_code = st.sidebar.text_input("Access PIN / Password:", type="password")

# --- 1. PLATFORM OWNER DASHBOARD ---
if user_role == "Platform Owner (Athena)":
    if auth_code == "athena2026":  # Secure via st.secrets in production
        st.title("🏛️ Athena Gardens Management Dashboard")
        
        st.subheader("1. Vendor Subscription Status")
        # Managed sub-vendor listing statuses
        vendors_status = [
            {"Vendor": "Savory Bites Catering", "Category": "Catering", "Status": "PAID / ACTIVE", "Fee": "P500/mo"},
            {"Vendor": "Saina Essential", "Category": "Decor", "Status": "PAID / ACTIVE", "Fee": "P500/mo"}
        ]
        st.table(vendors_status)
        
        st.subheader("2. All Saved Client Bookings")
        if os.path.exists("bookings.json"):
            with open("bookings.json", "r") as bf:
                bookings = json.load(bf)
            st.json(bookings)
        else:
            st.info("No client bookings recorded yet.")
            
    elif auth_code:
        st.error("Invalid Admin PIN.")

# --- 2. SUB-VENDOR SELF-SERVICE ---
elif user_role == "Sub-Vendor (Supplier)":
    supplier_key = st.sidebar.selectbox("Select Business:", ["savory_catering", "saina_essential"])
    
    if auth_code == "vendor123":  # Vendor specific password
        supplier_data = config_data["suppliers"][supplier_key]
        st.title(f"🛍️ {supplier_data['business_name']} Catalog Manager")
        
        st.subheader("Update Item Listings")
        for idx, item in enumerate(supplier_data.get("catalog", [])):
            with st.expander(f"Edit: {item['item_name']}"):
                new_price = st.number_input(f"Price (BWP) for {item['item_name']}", value=float(item['price']), key=f"p_{idx}")
                item['price'] = new_price
        
        if st.button("💾 Save Catalog Changes"):
            with open("vendors.json", "w") as f:
                json.dump(config_data, f, indent=2)
            st.success("Catalog updated live on client booking portal!")
    elif auth_code:
        st.error("Invalid Vendor Password.")
