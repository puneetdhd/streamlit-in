import streamlit as st
import requests
import json

# ============================================
# CONFIG
# ============================================
st.set_page_config(
    page_title="Trip Planner API Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_URL = st.sidebar.text_input("API Base URL", value="http://localhost:3000/api/v1")

# Initialize session state for auth
if 'admin_token' not in st.session_state:
    st.session_state['admin_token'] = None
if 'admin_user' not in st.session_state:
    st.session_state['admin_user'] = None

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔐 Admin Authentication")

if st.session_state['admin_token']:
    # Show welcome message and logout
    st.sidebar.success(f"Logged in as: {st.session_state['admin_user'].get('name', 'Admin')}")
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state['admin_token'] = None
        st.session_state['admin_user'] = None
        st.rerun()
else:
    # Render Login Form
    with st.sidebar.form("login_form"):
        email_input = st.text_input("Email/Username")
        password_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        
        if login_btn:
            try:
                resp = requests.post(f"{BASE_URL}/auth/admin/login", json={
                    "emailOrUsername": email_input,
                    "password": password_input
                })
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state['admin_token'] = data['data']['token']
                    st.session_state['admin_user'] = data['data']['user']
                    st.sidebar.success("Login successful!")
                    st.rerun()
                else:
                    st.sidebar.error(f"Login failed: {resp.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.sidebar.error(f"Connection error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Trip Planner API Dashboard")
st.sidebar.markdown("Use this dashboard to test all itinerary generation endpoints.")

# Helper to display responses
def display_response(resp):
    col1, col2 = st.columns([1, 3])
    with col1:
        if resp.status_code < 300:
            st.success(f"Status: {resp.status_code}")
        elif resp.status_code < 500:
            st.warning(f"Status: {resp.status_code}")
        else:
            st.error(f"Status: {resp.status_code}")
    with col2:
        try:
            st.json(resp.json())
        except Exception:
            st.code(resp.text)

# ============================================
# TABS
# ============================================
tabs = st.tabs([
    "🔍 Discover Places",
    "✅ Validate Selection",
    "🚀 Generate Itinerary",
    "📊 Check Status",
    "📖 Get Itinerary",
    "🔗 Shared Itinerary",
    "🔄 Swap Item",
    "↕️ Reorder Items",
    "📍 Re-optimize Day",
    "🗄️ Bulk Data Admin"
])

# ============================================
# TAB 1: Discover Places
# ============================================
with tabs[0]:
    st.header("🔍 Discover Places")
    st.caption("POST /itinerary/discover — Score and rank places for a city based on preferences")

    with st.form("discover_form"):
        col1, col2 = st.columns(2)
        with col1:
            city_id = st.number_input("City ID", min_value=1, value=1, key="disc_city")
            pace = st.selectbox("Pace", ["relaxed", "moderate", "packed"], index=1, key="disc_pace")
        with col2:
            crowd_pref = st.selectbox("Crowd Preference", ["avoid_crowds", "neutral", "love_crowds"], index=1, key="disc_crowd")
            limit = st.number_input("Limit", min_value=1, max_value=100, value=20, key="disc_limit")
        interests = st.text_input("Interests (comma-separated)", value="temple,museum,park", key="disc_interests")
        submitted = st.form_submit_button("Send Request", type="primary")

    if submitted:
        payload = {
            "city_id": city_id,
            "interests": [i.strip() for i in interests.split(",")],
            "pace": pace,
            "crowd_preference": crowd_pref,
            "limit": limit
        }
        with st.spinner("Discovering places..."):
            try:
                resp = requests.post(f"{BASE_URL}/itinerary/discover", json=payload, timeout=10)
                display_response(resp)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ============================================
# TAB 2: Validate Selection
# ============================================
with tabs[1]:
    st.header("✅ Validate Selection")
    st.caption("POST /itinerary/validate-selection — Check if the number of selected places fits the trip duration and pace")

    with st.form("validate_form"):
        col1, col2 = st.columns(2)
        with col1:
            duration_days = st.number_input("Duration (days)", min_value=1, max_value=30, value=3, key="val_dur")
            pace_val = st.selectbox("Pace", ["relaxed", "moderate", "packed"], index=1, key="val_pace")
        with col2:
            place_ids_str = st.text_input("Place IDs (comma-separated)", value="1,2,3,4,5,6,7,8,9,10", key="val_ids")
        submitted = st.form_submit_button("Validate", type="primary")

    if submitted:
        try:
            place_ids = [int(x.strip()) for x in place_ids_str.split(",") if x.strip()]
        except ValueError:
            st.error("Place IDs must be comma-separated integers")
            place_ids = []

        if place_ids:
            payload = {
                "place_ids": place_ids,
                "duration_days": duration_days,
                "pace": pace_val
            }
            with st.spinner("Validating..."):
                try:
                    resp = requests.post(f"{BASE_URL}/itinerary/validate-selection", json=payload, timeout=10)
                    display_response(resp)
                except Exception as e:
                    st.error(f"Request failed: {e}")

# ============================================
# TAB 3: Generate Itinerary
# ============================================
with tabs[2]:
    st.header("🚀 Generate Itinerary")
    st.caption("POST /itinerary/generate — Submit an async itinerary generation job")

    with st.form("generate_form"):
        col1, col2 = st.columns(2)
        with col1:
            gen_city_id = st.number_input("City ID", min_value=1, value=1, key="gen_city")
            gen_duration = st.number_input("Duration (days)", min_value=1, max_value=30, value=3, key="gen_dur")
            gen_pace = st.selectbox("Pace", ["relaxed", "moderate", "packed"], index=1, key="gen_pace")
        with col2:
            gen_crowd = st.selectbox("Crowd Preference", ["avoid_crowds", "neutral", "love_crowds"], index=1, key="gen_crowd")
            gen_lat = st.number_input("User Latitude", value=28.6139, format="%.4f", key="gen_lat")
            gen_lng = st.number_input("User Longitude", value=77.2090, format="%.4f", key="gen_lng")
        gen_place_ids = st.text_input("Place IDs (comma-separated)", value="1,2,3,4,5", key="gen_ids")
        submitted = st.form_submit_button("Generate", type="primary")

    if submitted:
        try:
            pids = [int(x.strip()) for x in gen_place_ids.split(",") if x.strip()]
        except ValueError:
            st.error("Place IDs must be comma-separated integers")
            pids = []

        if pids:
            payload = {
                "city_id": gen_city_id,
                "place_ids": pids,
                "duration_days": gen_duration,
                "pace": gen_pace,
                "crowd_preference": gen_crowd,
                "user_location": {"lat": gen_lat, "lng": gen_lng}
            }
            with st.spinner("Submitting generation job..."):
                try:
                    resp = requests.post(f"{BASE_URL}/itinerary/generate", json=payload, timeout=10)
                    display_response(resp)
                except Exception as e:
                    st.error(f"Request failed: {e}")

# ============================================
# TAB 4: Check Status
# ============================================
with tabs[3]:
    st.header("📊 Check Generation Status")
    st.caption("GET /itinerary/:id/status — Poll the status of a generation job")

    with st.form("status_form"):
        itin_id = st.text_input("Itinerary ID (UUID)", key="status_id")
        submitted = st.form_submit_button("Check Status", type="primary")

    if submitted and itin_id:
        with st.spinner("Checking..."):
            try:
                resp = requests.get(f"{BASE_URL}/itinerary/{itin_id}/status", timeout=10)
                display_response(resp)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ============================================
# TAB 5: Get Full Itinerary
# ============================================
with tabs[4]:
    st.header("📖 Get Full Itinerary")
    st.caption("GET /itinerary/:id — Fetch the complete day-by-day itinerary with place details")

    with st.form("get_form"):
        get_id = st.text_input("Itinerary ID (UUID)", key="get_id")
        submitted = st.form_submit_button("Fetch Itinerary", type="primary")

    if submitted and get_id:
        with st.spinner("Fetching..."):
            try:
                resp = requests.get(f"{BASE_URL}/itinerary/{get_id}", timeout=10)
                display_response(resp)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ============================================
# TAB 6: Shared Itinerary
# ============================================
with tabs[5]:
    st.header("🔗 Get Shared Itinerary")
    st.caption("GET /itinerary/share/:token — Fetch itinerary via public share token (no auth required)")

    with st.form("share_form"):
        share_token = st.text_input("Share Token (UUID)", key="share_token")
        submitted = st.form_submit_button("Fetch Shared", type="primary")

    if submitted and share_token:
        with st.spinner("Fetching..."):
            try:
                resp = requests.get(f"{BASE_URL}/itinerary/share/{share_token}", timeout=10)
                display_response(resp)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ============================================
# TAB 7: Swap Item
# ============================================
with tabs[6]:
    st.header("🔄 Swap an Item")
    st.caption("POST /itinerary/:id/items/:item_id/swap — Replace a place in the itinerary with a different one")

    with st.form("swap_form"):
        col1, col2 = st.columns(2)
        with col1:
            swap_itin_id = st.text_input("Itinerary ID (UUID)", key="swap_itin_id")
            swap_item_id = st.text_input("Item ID (UUID)", key="swap_item_id")
        with col2:
            new_place_id = st.number_input("New Place ID", min_value=1, value=1, key="swap_place_id")
        submitted = st.form_submit_button("Swap", type="primary")

    if submitted and swap_itin_id and swap_item_id:
        payload = {"new_place_id": new_place_id}
        with st.spinner("Swapping..."):
            try:
                resp = requests.post(
                    f"{BASE_URL}/itinerary/{swap_itin_id}/items/{swap_item_id}/swap",
                    json=payload, timeout=10
                )
                display_response(resp)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ============================================
# TAB 8: Reorder Items
# ============================================
with tabs[7]:
    st.header("↕️ Reorder Items")
    st.caption("PATCH /itinerary/:id/items — Bulk update item positions within a day")

    with st.form("reorder_form"):
        reorder_itin_id = st.text_input("Itinerary ID (UUID)", key="reorder_itin_id")
        reorder_json = st.text_area(
            "Items JSON (array of {item_id, position})",
            value='[\n  { "item_id": "uuid-1", "position": 1 },\n  { "item_id": "uuid-2", "position": 2 }\n]',
            height=150,
            key="reorder_json"
        )
        submitted = st.form_submit_button("Reorder", type="primary")

    if submitted and reorder_itin_id:
        try:
            items_payload = json.loads(reorder_json)
        except json.JSONDecodeError:
            st.error("Invalid JSON format")
            items_payload = None

        if items_payload:
            with st.spinner("Reordering..."):
                try:
                    resp = requests.patch(
                        f"{BASE_URL}/itinerary/{reorder_itin_id}/items",
                        json=items_payload, timeout=10
                    )
                    display_response(resp)
                except Exception as e:
                    st.error(f"Request failed: {e}")

# ============================================
# TAB 9: Re-optimize Day
# ============================================
with tabs[8]:
    st.header("📍 Re-optimize Day from Current Location")
    st.caption("POST /itinerary/:id/reoptimize — Re-run TSP from your live GPS for a specific day")

    with st.form("reopt_form"):
        col1, col2 = st.columns(2)
        with col1:
            reopt_itin_id = st.text_input("Itinerary ID (UUID)", key="reopt_itin_id")
            reopt_day = st.number_input("Day Number", min_value=1, max_value=30, value=1, key="reopt_day")
        with col2:
            reopt_lat = st.number_input("Current Latitude", value=28.6139, format="%.4f", key="reopt_lat")
            reopt_lng = st.number_input("Current Longitude", value=77.2090, format="%.4f", key="reopt_lng")
        submitted = st.form_submit_button("Re-optimize", type="primary")

    if submitted and reopt_itin_id:
        payload = {
            "current_lat": reopt_lat,
            "current_lng": reopt_lng,
            "day_number": reopt_day
        }
        with st.spinner("Re-optimizing route..."):
            try:
                resp = requests.post(
                    f"{BASE_URL}/itinerary/{reopt_itin_id}/reoptimize",
                    json=payload, timeout=10
                )
                display_response(resp)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ============================================
# TAB 10: Master Database Admin (Cities, Places, Events)
# ============================================
with tabs[9]:
    st.header("🗄️ Master Database Admin")
    st.caption("Upload CSVs or Live-Edit the Core SQL Tables.")
    
    if not st.session_state.get('admin_token'):
        st.error("🔒 Please login via the sidebar to access the Database Admin panel.")
    else:
        headers = {"Authorization": f"Bearer {st.session_state['admin_token']}"}
        
        # 1. Selection
        target_tb = st.selectbox("Select Target Table", ["Cities", "Places", "Events"])
        
        st.markdown("---")
        st.markdown(f"### 📥 Bulk Insert Data (CSV) -> `{target_tb}`")
        if target_tb == "Cities":
            st.info("CSV Requirements: Headers must include `stateCode` (e.g. 'Odisha') and `name` (e.g. 'Bhubaneswar'). System automatically generates keys like 'OD_BHU'.")
        elif target_tb == "Places":
            st.info("CSV Requirements: Headers must include `state` (or `stateCode`) and `city` (or `cityName`). The system will automatically compute the `city_id` and assign it to the place.")

        
        uploaded_file = st.file_uploader(f"Upload {target_tb} CSV", type="csv", key=f"upload_{target_tb}")
        
        if uploaded_file is not None:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head())
                
                if st.button(f"Inject {target_tb} to SQL DB", type="primary"):
                    success_count = 0
                    error_count = 0
                    endpoint = target_tb.lower()
                    st.info(f"Uploading payloads to /{endpoint}...")
                    
                    # Pre-fetch cities mapping for Places
                    city_mapping = {}
                    if target_tb == "Places":
                        try:
                            cities_resp = requests.get(f"{BASE_URL}/cities?limit=1000", headers=headers)
                            if cities_resp.status_code == 200:
                                cities_data = cities_resp.json().get('data', [])
                                for c in cities_data:
                                    city_mapping[c['name'].lower().strip()] = c['id']
                        except Exception as e:
                            st.warning(f"Could not pre-fetch cities: {e}")

                    progress_bar = st.progress(0)
                    
                    for index, row in df.iterrows():
                        payload = row.to_dict()
                        payload = {k: (v if pd.notna(v) else None) for k, v in payload.items()}
                        
                        try:
                            if target_tb == "Places":
                                # Handle Postgres Arrays
                                for array_field in ['types', 'tags']:
                                    if array_field in payload and payload[array_field]:
                                        payload[array_field] = [x.strip() for x in str(payload[array_field]).split(',') if x.strip()]
                                
                                # Auto-map city_id from active database cities
                                cname = payload.get('city_name') or payload.get('city') or payload.get('City') or payload.get('cityName')
                                if cname and pd.notna(cname):
                                    clean_cname = str(cname).lower().strip()
                                    mapped_id = city_mapping.get(clean_cname)
                                    if mapped_id:
                                        # Force overwrite the old numeric city_id with our new string ID
                                        payload['city_id'] = mapped_id
                                        payload['cityId'] = mapped_id
                                    else:
                                        st.warning(f"Row {index+1}: Could not find a match for city '{cname}' in your Cities table. Please make sure this city is uploaded first!")
                            
                            resp = requests.post(f"{BASE_URL}/{endpoint}", json=payload, headers=headers, timeout=10)
                            
                            if resp.status_code < 300:
                                success_count += 1
                            else:
                                error_count += 1
                                st.error(f"Row {index+1} Failed: {resp.text}")
                        except Exception as e:
                            error_count += 1
                            st.error(f"Row {index+1} Connection Exception: {e}")
                            
                        progress_bar.progress((index + 1) / len(df))
                    st.success(f"Execution Complete: {success_count} inserted, {error_count} failed.")
            except Exception as e:
                st.error(f"Failed to read CSV Pandas DataFrame: {e}")

        # =======================
        # 2. Live Grid View
        # =======================
        st.markdown("---")
        st.markdown(f"### ✏️ Live Interactive Database: `{target_tb}`")
        
        col1, col2 = st.columns([1,4])
        with col1:
            if st.button(f"Load Live {target_tb} Data"):
                try:
                    with st.spinner("Fetching from Postgres backend..."):
                        # Support generalized pagination, defaulting to top 100 rows
                        resp = requests.get(f"{BASE_URL}/{target_tb.lower()}?limit=100")
                        if resp.status_code == 200:
                            data = resp.json().get('data', [])
                            if len(data) > 0:
                                st.session_state[f'live_data_{target_tb}'] = data
                            else:
                                st.warning("No records found in database. Try uploading a CSV first!")
                        else:
                            st.error(f"Failed to fetch data: {resp.status_code}")
                except Exception as e:
                    st.error(f"Backend offline: {e}")

        if f'live_data_{target_tb}' in st.session_state:
            import pandas as pd
            df_live = pd.DataFrame(st.session_state[f'live_data_{target_tb}'])
            
            st.caption("💡 Streamlit Editor: Double-click any cell to type an **Edit**. Or click the checkbox on the far left to designate a row for **Deletion**.")
            
            edited_df = st.data_editor(
                df_live,
                num_rows="dynamic", # Streamlit configuration allowing dynamic deletions
                use_container_width=True,
                key=f"editor_{target_tb}"
            )
            
            st.markdown("##### Apply Modifications")
            
            if st.button("💾 Push Saves + Deletions to Backend", type="primary"):
                # Track diffs placed in Streamlit's implicit session context 
                changes = st.session_state[f"editor_{target_tb}"]
                updates_count = 0
                errors_count = 0
                
                # Run UDPATE streams
                if changes.get("edited_rows"):
                    with st.spinner("Processing Row Updates..."):
                        for row_idx, edits in changes["edited_rows"].items():
                            record_id = df_live.iloc[row_idx]['id']
                            try:
                                resp = requests.put(f"{BASE_URL}/{target_tb.lower()}/{record_id}", json=edits, headers=headers)
                                if resp.status_code < 300: 
                                    updates_count += 1
                                else: 
                                    st.error(f"Update failed for ID {record_id}: {resp.text}")
                                    errors_count += 1
                            except Exception as e:
                                st.error(f"Exception ID {record_id}: {e}")
                                errors_count += 1
                            
                # Run DELETE streams
                if changes.get("deleted_rows"):
                    with st.spinner("Processing Row Deletions..."):
                        for row_idx in changes["deleted_rows"]:
                            record_id = df_live.iloc[row_idx]['id']
                            try:
                                resp = requests.delete(f"{BASE_URL}/{target_tb.lower()}/{record_id}", headers=headers)
                                if resp.status_code < 300: 
                                    updates_count += 1
                                else: 
                                    st.error(f"Delete failed for ID {record_id}: {resp.text}")
                                    errors_count += 1
                            except Exception as e:
                                st.error(f"Exception ID {record_id}: {e}")
                                errors_count += 1
                            
                if updates_count > 0:
                    st.success(f"Committing {updates_count} transactions to database was successful!")
                    del st.session_state[f'live_data_{target_tb}'] # Nuke state to reflect new dataset cleanly
                    st.rerun()

# ============================================
# FOOTER
# ============================================
st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit • Trip Planner API v1")
