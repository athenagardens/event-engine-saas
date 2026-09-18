# ==============================================================================
# ROUTE 4: MASTER ADMIN
# ==============================================================================
elif route == "Platform Administration":
    st.title("Platform Administration")
    pin = st.text_input("Security PIN:", type="password")
    
    if pin == "admin2026":
        st.success("Authenticated as Platform Administrator")
        
        # Financial Overview Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Venues Registered", len(venues))
        m2.metric("Total Suppliers Registered", len(all_suppliers))
        m3.metric("Platform Fee Rate", "10%")
        
        st.markdown("---")
        
        # Manage & Delete Accounts Section
        st.subheader("Manage & Delete Accounts")
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("#### Venues")
            v_del = st.selectbox("Select Venue to Delete:", ["-- Select --"] + list(venues.keys()), key="del_v")
            if st.button("Delete Venue"):
                if v_del != "-- Select --":
                    del st.session_state.config_data["venues"][v_del]
                    save_config(st.session_state.config_data)
                    st.success(f"Removed venue '{v_del}'")
                    st.rerun()

        with col_d2:
            st.markdown("#### Suppliers")
            s_del = st.selectbox("Select Supplier to Delete:", ["-- Select --"] + list(all_suppliers.keys()), key="del_s")
            if st.button("Delete Supplier"):
                if s_del != "-- Select --":
                    del st.session_state.config_data["all_suppliers"][s_del]
                    save_config(st.session_state.config_data)
                    st.success(f"Removed supplier '{s_del}'")
                    st.rerun()

        st.markdown("---")
        
        # System Tables
        st.subheader("Registered Venues Directory")
        if venues:
            v_rows = [{"Identifier (Slug)": k, "Business Name": v.get("business_name"), "Portal Link": f"/?vendor={k}"} for k, v in venues.items()]
            st.table(pd.DataFrame(v_rows))
            
        st.subheader("Registered Suppliers Directory")
        if all_suppliers:
            s_rows = [{"Identifier (Slug)": k, "Business Name": v.get("business_name"), "Category": v.get("category")} for k, v in all_suppliers.items()]
            st.table(pd.DataFrame(s_rows))
