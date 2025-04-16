import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import json
from datetime import datetime

# ---------- Custom CSS ----------
st.markdown("""
    <style>
        .main {
            background-color: #f5f7fa;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.5em 1em;
        }
        .stTextInput, .stTextArea, .stSelectbox, .stNumberInput {
            border-radius: 10px !important;
        }
        .stDataFrame {
            border-radius: 10px;
        }
        .metric-label > div {
            font-size: 14px !important;
            color: #6c757d;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000"

def api_call(method, endpoint, data=None):
    url = f"{API_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"🚨 API Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"🚨 Request Failed: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="⚡ Serverless Platform", layout="wide")
    st.markdown("<h1 style='color:#2c3e50;'>⚡ Serverless Function Execution Platform</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        page = st.selectbox("Choose a page", ["🚀 Deploy Function", "🛠 Manage Functions", "⚙️ Execute Function", "📊 Metrics Dashboard"])

    if page == "🚀 Deploy Function":
        st.markdown("## 🚀 Deploy a New Function")
        with st.container():
            with st.form("deploy_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Function Name", placeholder="e.g., my_function")
                    language = st.selectbox("Language", ["python", "javascript"])
                with col2:
                    timeout = st.slider("Timeout (seconds)", min_value=1, max_value=300, value=30)
                code = st.text_area("Function Code", height=250, placeholder="Paste your function code here...")
                submit = st.form_submit_button("🚀 Deploy Function")
                if submit:
                    if not name or not code:
                        st.warning("⚠️ Please enter both name and code.")
                    else:
                        func = {"name": name, "language": language, "code": code, "timeout": timeout}
                        result = api_call("POST", "/functions/", func)
                        if result:
                            st.success(f"✅ Function `{result['id']}` deployed successfully!")

    elif page == "🛠 Manage Functions":
        st.markdown("## 🛠 Manage Functions")
        funcs = api_call("GET", "/functions/")
        if funcs:
            df = pd.DataFrame(funcs)
            st.dataframe(df, use_container_width=True)

            st.subheader("✏️ Edit or ❌ Delete a Function")
            func_id = st.number_input("Enter Function ID", min_value=1, step=1)
            if st.button("🔍 Load"):
                func = api_call("GET", f"/functions/{func_id}")
                if func:
                    with st.form("edit_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Function Name", value=func["name"])
                            language = st.selectbox("Language", ["python", "javascript"], index=["python", "javascript"].index(func["language"]))
                        with col2:
                            timeout = st.slider("Timeout (seconds)", min_value=1, max_value=300, value=func["timeout"])
                        code = st.text_area("Code", value=func["code"], height=250)
                        col3, col4 = st.columns(2)
                        with col3:
                            update = st.form_submit_button("✅ Update")
                        with col4:
                            delete = st.form_submit_button("🗑 Delete")

                        if update:
                            updated_func = {"name": name, "language": language, "code": code, "timeout": timeout}
                            result = api_call("PUT", f"/functions/{func_id}", updated_func)
                            if result:
                                st.success(f"✅ Function `{func_id}` updated!")
                        if delete:
                            result = api_call("DELETE", f"/functions/{func_id}")
                            if result:
                                st.success(f"🗑 Function `{func_id}` deleted!")
        else:
            st.info("ℹ️ No functions available. Try deploying one.")

    elif page == "⚙️ Execute Function":
        st.markdown("## ⚙️ Execute a Function")
        col1, col2 = st.columns(2)
        with col1:
            func_id = st.number_input("Function ID", min_value=1, step=1)
        with col2:
            payload = st.text_area("Payload (JSON)", "{}", height=100)
        if st.button("▶️ Execute"):
            try:
                payload_dict = json.loads(payload)
                result = api_call("POST", f"/execute/{func_id}", payload_dict)
                if result:
                    st.markdown("### ✅ Result")
                    st.code(result["result"], language="text")
            except json.JSONDecodeError:
                st.error("🚫 Invalid JSON format!")

    elif page == "📊 Metrics Dashboard":
        st.markdown("## 📊 Metrics Dashboard")
        func_id_filter = st.number_input("Filter by Function ID (0 = all)", min_value=0, step=1, value=0)
        metrics = api_call("GET", "/metrics/" if func_id_filter == 0 else f"/metrics/?func_id={func_id_filter}")
        if metrics:
            df = pd.DataFrame(metrics)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                fig = px.line(df, x="timestamp", y="response_time", color="func_id", 
                              title="Response Time Over Time", labels={"response_time": "Response Time (s)"})
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### 📈 Statistics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Avg Response Time", f"{df['response_time'].mean():.2f} s")
                col2.metric("Total Executions", len(df))
                error_rate = (df['errors'].notnull().sum() / len(df) * 100)
                col3.metric("Error Rate", f"{error_rate:.1f}%")
            else:
                st.info("ℹ️ No metrics data available.")
        else:
            st.warning("⚠️ Failed to fetch metrics.")

if __name__ == "__main__":
    main()
