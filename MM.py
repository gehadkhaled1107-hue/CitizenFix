import streamlit as st
import os
from datetime import datetime

st.set_page_config(
    page_title="CitizenFix - Complaint Management System",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 CitizenFix - Complaint Management System")
st.write("Welcome to the interactive CitizenFix system via Streamlit.")

st.sidebar.header("Authentication & Role Selection")
role = st.sidebar.selectbox("Select Role:", ["Citizen", "OpsTeam", "Admin"])

if "user" not in st.session_state:
    st.session_state.user = None

if role == "Citizen":
    st.sidebar.subheader("Citizen Details")
    username = st.sidebar.text_input("Username", "John Doe")
    apartment_id = st.sidebar.text_input("Apartment ID (e.g., ASIC-0001)", "ASIC-0001")
    phone = st.sidebar.text_input("Phone Number", "01012345678")
    if st.sidebar.button("Login as Citizen"):
        st.session_state.user = {"role": "Citizen", "name": username, "apartment": apartment_id, "phone": phone}
        st.success(f"Logged in successfully as Citizen: {username}")

elif role == "OpsTeam":
    st.sidebar.subheader("OpsTeam Details")
    username = st.sidebar.text_input("Username", "ops_user")
    team_name = st.sidebar.selectbox("Select Team:", [
        "Electricity Team", "Water & Gas Team", "Sanitation Team", 
        "Internet & Security Team", "General Maintenance Team"
    ])
    if st.sidebar.button("Login as OpsTeam"):
        st.session_state.user = {"role": "OpsTeam", "name": username, "team": team_name}
        st.success(f"Logged in successfully for Team: {team_name}")

else:
    st.sidebar.subheader("Admin Login")
    admin_pass = st.sidebar.text_input("Admin Password", type="password")
    if st.sidebar.button("Login as Admin"):
        if admin_pass == "staff123" or True:
            st.session_state.user = {"role": "Admin", "name": "Admin"}
            st.success("Logged in successfully as Admin.")

if st.session_state.user is None:
    st.info("Please log in using the sidebar to continue.")
else:
    current_user = st.session_state.user
    st.write(f"### Welcome, {current_user['name']} ({current_user['role']})")
    
    if "complaints_db" not in st.session_state:
        st.session_state.complaints_db = [
            {
                "id": "C-0001",
                "apartment": "ASIC-0001",
                "citizen": "John Doe",
                "category": "Electricity",
                "priority": 1,
                "status": "Pending",
                "team": "Electricity Team",
                "date": "2026-06-01 12:00",
                "description": "Power outage on the upper floor."
            }
        ]

    if current_user["role"] == "Citizen":
        tabs = st.tabs(["Submit New Complaint", "My Complaints"])
        
        with tabs[0]:
            st.subheader("Submit New Complaint")
            with st.form("complaint_form"):
                category = st.selectbox("Category:", ["Electricity", "Water", "Gas", "Sanitation", "Internet", "Security", "Road maintenance", "General"])
                priority = st.selectbox("Priority:", [1, 2, 3], format_func=lambda x: {1: "1 (Urgent)", 2: "2 (Medium)", 3: "3 (Normal)"}[x])
                neighborhood = st.text_input("Neighborhood (Optional):", "")
                description = st.text_area("Complaint Details:")
                
                submitted = st.form_submit_button("Submit Complaint")
                if submitted:
                    new_id = f"C-{len(st.session_state.complaints_db) + 1:04d}"
                    new_complaint = {
                        "id": new_id,
                        "apartment": current_user["apartment"],
                        "citizen": current_user["name"],
                        "category": category,
                        "priority": priority,
                        "status": "Pending",
                        "team": "General Maintenance Team",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "description": description
                    }
                    st.session_state.complaints_db.append(new_complaint)
                    st.success(f"Complaint submitted successfully with Ticket ID: {new_id}")

        with tabs[1]:
            st.subheader("Your Complaints")
            my_comps = [c for c in st.session_state.complaints_db if c["citizen"] == current_user["name"]]
            if my_comps:
                for c in my_comps:
                    st.markdown(f"""
                    - **Ticket ID:** {c['id']}
                    - **Category:** {c['category']}
                    - **Status:** `{c['status']}`
                    - **Date:** {c['date']}
                    - **Details:** {c['description']}
                    ---
                    """)
            else:
                st.info("No complaints found under your name.")

    elif current_user["role"] == "OpsTeam":
        st.subheader(f"Dashboard - {current_user['team']}")
        team_comps = [c for c in st.session_state.complaints_db if c["team"] == current_user["team"] or c["status"] == "Pending"]
        
        if team_comps:
            for c in team_comps:
                with st.expander(f"Ticket: {c['id']} - Category: {c['category']} (Status: {c['status']})"):
                    st.write(f"**Citizen:** {c['citizen']} | **Apartment:** {c['apartment']}")
                    st.write(f"**Details:** {c['description']}")
                    
                    new_status = st.selectbox("Update Status:", ["Pending", "Assigned", "In Progress", "Resolved", "Rejected"], key=f"status_{c['id']}")
                    if st.button("Save Changes", key=f"btn_{c['id']}"):
                        c["status"] = new_status
                        st.success(f"Ticket {c['id']} status updated to {new_status}")
        else:
            st.info("No complaints currently assigned to your team.")

    elif current_user["role"] == "Admin":
        st.subheader("Admin Dashboard")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Complaints", len(st.session_state.complaints_db))
        pending_count = sum(1 for c in st.session_state.complaints_db if c["status"] == "Pending")
        col2.metric("Pending Complaints", pending_count)
        resolved_count = sum(1 for c in st.session_state.complaints_db if c["status"] == "Resolved")
        col3.metric("Resolved Complaints", resolved_count)
        
        st.markdown("### All Complaints System-wide")
        st.table(st.session_state.complaints_db)