import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import json
from datetime import datetime
import time

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
        return response.json() if response.text else {"status": "success"}
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request Failed: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Serverless Platform", layout="wide")
    st.title("Serverless Function Platform")

    page = st.sidebar.selectbox("Navigate", ["Deploy Function", "Manage Functions", "Execute Function", "Metrics Dashboard"])

    if page == "Deploy Function":
        st.header("Deploy a New Function")
        with st.form("deploy_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Function Name", placeholder="e.g., my_function")
                language = st.selectbox("Language", ["python", "javascript"])
            with col2:
                timeout = st.number_input("Timeout (seconds)", min_value=1, value=30)
                runtime = st.selectbox("Runtime", ["runc", "runsc"])
                st.caption("""
                ℹ️ **Runtime Options**:
                - `runc`: Default Docker runtime (fast, less isolated)
                - `runsc`: gVisor sandboxed runtime (more secure, slightly slower)
                """)
                route_suffix = st.text_input("Route Suffix (optional)", placeholder="echo", help="Will be /fn/{unique_id}/{suffix}, leave blank for 'default'")
            code = st.text_area("Code", height=200, placeholder="Enter your code here")
            submit = st.form_submit_button("Deploy")
            if submit:
                if not name or not code:
                    st.error("Function Name and Code are required!")
                else:
                    func = {"name": name, "language": language, "code": code, "timeout": timeout, "runtime": runtime}
                    if route_suffix:
                        func["route"] = route_suffix
                    result = api_call("POST", "/functions/", func)
                    if result:
                        st.success(f"Function {result['id']} deployed successfully! Route: {result['route']}")

    elif page == "Manage Functions":
        st.header("Manage Functions")
        funcs = api_call("GET", "/functions/")
        if funcs:
            df = pd.DataFrame(funcs)
            display_columns = ["id", "name", "language", "code", "timeout", "route"]
            st.dataframe(df[display_columns], use_container_width=True)

            if "selected_func_id" not in st.session_state:
                st.session_state.selected_func_id = None

            func_id_input = st.number_input("Function ID to Edit/Delete", min_value=1, step=1, key="func_id_input")
            if st.button("Load Function"):
                st.session_state.selected_func_id = func_id_input

            if st.session_state.selected_func_id:
                func = api_call("GET", f"/functions/{st.session_state.selected_func_id}")
                if func:
                    with st.form("edit_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Function Name", value=func["name"])
                            language = st.selectbox("Language", ["python", "javascript"], index=["python", "javascript"].index(func["language"]))
                        with col2:
                            timeout = st.number_input("Timeout (seconds)", min_value=1, value=func["timeout"])
                            route_suffix = st.text_input("Route Suffix", value=func["route"].split("/")[-1])
                        code = st.text_area("Code", value=func["code"], height=200)
                        
                        col3, col4 = st.columns(2)
                        update = col3.form_submit_button("Update")
                        delete = col4.form_submit_button("Delete")

                        if update:
                            updated_func = {
                                "id": st.session_state.selected_func_id,
                                "name": name,
                                "language": language,
                                "code": code,
                                "timeout": timeout,
                                "route": route_suffix
                            }
                            result = api_call("PUT", f"/functions/{st.session_state.selected_func_id}", updated_func)
                            if result:
                                st.success(f"Function {st.session_state.selected_func_id} updated successfully!")
                                st.session_state.selected_func_id = None
                                time.sleep(1)
                                st.rerun()

                        if delete:
                            result = api_call("DELETE", f"/functions/{st.session_state.selected_func_id}")
                            if result:
                                st.success(f"Function {st.session_state.selected_func_id} deleted successfully!")
                                st.session_state.selected_func_id = None
                                time.sleep(1)
                                st.rerun()
                else:
                    st.warning(f"Function {st.session_state.selected_func_id} not found.")
        else:
            st.info("No functions available.")

    elif page == "Execute Function":
        st.header("Execute a Function")
        execution_method = st.radio("Execute by:", ["Function ID", "Route"], horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if execution_method == "Function ID":
                func_id = st.number_input("Function ID", min_value=1, step=1, key="func_id")
            else:
                route = st.text_input("Route", placeholder="/fn/abc12345/echo", key="route")
        with col2:
            payload = st.text_area("Payload (JSON)", "{}", height=100)
        
        if st.button("Execute"):
            try:
                payload_dict = json.loads(payload)
                if execution_method == "Function ID":
                    result = api_call("POST", f"/execute/{func_id}", payload_dict)
                else:
                    result = api_call("POST", route, payload_dict)
                if result:
                    st.subheader("Execution Result")
                    st.code(result["result"], language="text")
            except json.JSONDecodeError:
                st.error("Invalid JSON payload!")
            except NameError:
                st.error("Please provide a valid Function ID or Route.")

    elif page == "Metrics Dashboard":
        st.header("Metrics Dashboard")
        route_filter = st.text_input("Filter by Route (optional, leave blank for all)", placeholder="/fn/abc12345/echo")
        metrics = api_call("GET", "/metrics/" if not route_filter else f"/metrics/?route={route_filter}")
        if metrics:
            # Handle single dict or list of dicts
            if isinstance(metrics, dict):
                metrics = [metrics]  # Wrap single dict in list
            df = pd.DataFrame(metrics)
            if not df.empty:
                # Ensure required columns exist
                if "timestamp" not in df.columns:
                    df["timestamp"] = pd.to_datetime(datetime.now())
                else:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                if "errors" not in df.columns:
                    df["errors"] = None
                if "route" not in df.columns:
                    df["route"] = route_filter or "unknown"
                if "resources" in df.columns:
                    # Flatten resources dict if needed
                    df["cpu_usage"] = df["resources"].apply(lambda x: x.get("cpu", "N/A") if isinstance(x, dict) else "N/A")
                    df["memory_usage"] = df["resources"].apply(lambda x: x.get("memory", "N/A") if isinstance(x, dict) else "N/A")
                st.write("Metrics Data:", df[["route", "timestamp", "response_time", "cpu_usage", "memory_usage", "errors"]])
                fig = px.line(df, x="timestamp", y="response_time", color="route", 
                              title="Response Time Over Time", labels={"response_time": "Response Time (s)"})
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("Statistics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Response Time", f"{df['response_time'].mean():.2f} s" if 'response_time' in df else "N/A")
                col2.metric("Execution Count", len(df))
                col3.metric("Error Rate", f"{(df['errors'].notnull().sum() / len(df) * 100):.1f}%")
            else:
                st.info("No metrics available for this filter.")
        else:
            st.info("No metrics available.")

if __name__ == "__main__":
    main()