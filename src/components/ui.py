import streamlit as st
import time
import sys
import os

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Mock imports to run standalone or within Lightning
from src.components.executor import SQLAgent

# Initialize Agent (Cache resource to emulate shared state/hot-swap)
@st.cache_resource
def get_agent(auto_audit=False):
    return SQLAgent(db_url="sqlite:///test_data.db", model_path="llama3:8b", auto_audit=auto_audit)

def main():
    st.set_page_config(page_title="EvoSQL-Lightning", layout="wide")
    st.title("⚡ EvoSQL-Lightning")
    st.caption("Robust NL2SQL with Self-Improvement Loop")

    with st.sidebar:
        st.header("Settings")
        auto_audit = st.toggle("Enable Auto-Auditor (AI Critic)", value=False)
        if auto_audit:
            st.info("AI will auto-judge queries and save 'PASS' results to training data.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Re-get agent if needed (Streamlit cache handles args)
    agent = get_agent(auto_audit=auto_audit)

    # Chat Interface
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sql" in msg:
                st.code(msg["sql"], language="sql")
            if "explanation" in msg:
                st.info(msg["explanation"])
            if "data" in msg:
                 st.dataframe(msg["data"])

    if prompt := st.chat_input("Ask about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = agent.handle_query(prompt)
                
                # Check outcome types
                if isinstance(response, dict):
                    # Successful Execution
                    content = "Here is the result:"
                    st.markdown(content)
                    st.code(response['sql'], language="sql")
                    st.info(response['explanation'])
                    st.dataframe(response['data'])
                    
                    # Store in history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": content,
                        "sql": response['sql'],
                        "explanation": response['explanation'],
                        "data": response['data']
                    })
                    
                    # Refinement 5: Feedback UI
                    col1, col2 = st.columns(2)
                    # We need unique keys for buttons
                    q_idx = len(st.session_state.messages)
                    with col1:
                        if st.button("👍 Good", key=f"good_{q_idx}"):
                            agent.submit_feedback(prompt, response['sql'], 1)
                            st.toast("Positive feedback logged for DPO Loop!")
                    with col2:
                        if st.button("👎 Bad", key=f"bad_{q_idx}"):
                             agent.submit_feedback(prompt, response['sql'], 0)
                             st.toast("Negative feedback logged. Will retrain.")


                else:
                    # String response (Clarification/Error)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
