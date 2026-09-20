with tab_tickets:
        conn = get_db_connection()
        events = conn.execute("SELECT * FROM events WHERE is_active = 1").fetchall()
        if not events:
            st.info("No public ticketed events listed.")
        else:
            for ev in events:
                v = conn.execute("SELECT * FROM venues WHERE venue_id = ?", (ev['venue_id'],)).fetchone()
                col1, col2 = st.columns([1, 2])
                col1.image(ev['flyer_url'] or SPACE_PRESETS[0], use_container_width=True)
                col2.markdown(f"<h3 style='font-family: Playfair Display, serif; margin:0;'>{ev['title']}</h3>", unsafe_allow_html=True)
                col2.write(f"**VENUE:** {ev['venue_name']} | **DATE:** {ev['date']} | **ADMISSION TARIFF:** BWP {ev['price']:,.2f}")
                
                with col2.form(f"tkt_buy_{ev['event_id']}"):
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        st.markdown("<div class='form-label'>Pass Quantity</div>", unsafe_allow_html=True)
                        t_qty = st.number_input("", min_value=1, value=1, label_visibility="collapsed", key=f"tkt_qty_{ev['event_id']}")
                        st.markdown("<div class='form-label'>Attendee Name*</div>", unsafe_allow_html=True)
                        t_buyer = st.text_input("", label_visibility="collapsed", key=f"tkt_buyer_{ev['event_id']}")
                    with tc2:
                        st.markdown("<div class='form-label'>Email Address*</div>", unsafe_allow_html=True)
                        t_email = st.text_input("", label_visibility="collapsed", key=f"tkt_email_{ev['event_id']}")
                        st.markdown("<div class='form-label'>Settlement Method</div>", unsafe_allow_html=True)
                        t_pay = st.selectbox("", ["Direct Bank Wire Transfer", "eWallet", "Orange Money", "Pay2Cell"], label_visibility="collapsed", key=f"tkt_pay_{ev['event_id']}")
                    
                    if st.form_submit_button("SUBMIT TICKET ORDER"):
                        if t_buyer and t_email:
                            tkt_id = f"TKT-{int(datetime.datetime.now().timestamp())}"
                            sec_hash = f"HASH-{hashlib.sha256(f'{tkt_id}-{t_email}'.encode()).hexdigest()[:10].upper()}"
                            
                            # Insert as Pending Verification — NO PASS RELEASED YET
                            conn.execute("""INSERT INTO tickets
                                (ticket_id, verification_hash, event_id, event_title, venue_id, venue_name, venue_logo, buyer, email, qty, total_paid, payment_method, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending WhatsApp POP Verification')""",
                                (tkt_id, sec_hash, ev['event_id'], ev['title'], v['venue_id'] if v else "", ev['venue_name'], v['logo_url'] if v else DEFAULT_LOGO, t_buyer, t_email, t_qty, t_qty*ev['price'], t_pay))
                            conn.commit()
                            
                            st.warning("⏳ Order Placed! Ticket pass is pending payment verification.")
                            
                            # Instructions to send POP via WhatsApp
                            wa_num = v['whatsapp_no'] if v and v['whatsapp_no'] else ""
                            st.info(f"👉 **Next Step:** Send your Proof of Payment (POP) along with Order Ref **`{tkt_id}`** via WhatsApp to **+{wa_num}** for verification before your ticket pass is released.")
                            if wa_num:
                                wa_link = f"https://wa.me/{wa_num}?text=Hello,%20here%20is%20my%20POP%20for%20Ticket%20Ref:%20{tkt_id}"
                                st.markdown(f"[📲 Click Here to Open WhatsApp & Submit POP]({wa_link})")
                        else:
                            st.error("Please enter required attendee details.")
        conn.close()
