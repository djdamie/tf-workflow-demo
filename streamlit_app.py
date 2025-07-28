import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import time

# Page config
st.set_page_config(
    page_title="TF Music Workflow Assistant",
    page_icon="🎵",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
if 'project_info' not in st.session_state:
    st.session_state.project_info = {}

# Your LangGraph endpoint
LANGGRAPH_URL = "https://tf-supervisor-workflow-v2-855da41ec83656b3b397ebe6ba569c43.us.langgraph.app"

# Sidebar
with st.sidebar:
    st.header("🎵 TF Music Workflow")
    st.caption("Find, clear, and deliver the perfect music")
    
    st.divider()
    
    # File upload
    st.subheader("📁 Upload Files")
    uploaded_file = st.file_uploader(
        "Upload brief or budget file",
        type=['txt', 'csv', 'pdf', 'docx', 'xlsx'],
        help="Upload project briefs, budget tables, or other documents"
    )
    
    if uploaded_file:
        if uploaded_file.type == 'text/csv' or uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded: {uploaded_file.name}")
            st.dataframe(df, height=200)
            
            if st.button("📊 Process Budget Table"):
                csv_content = df.to_string()
                brief_text = f"Please analyze this budget table:\n\n{csv_content}"
                st.session_state.messages.append({"role": "user", "content": f"📊 Processing budget file: {uploaded_file.name}"})
                # Trigger rerun to process
                st.session_state.pending_message = brief_text
                st.rerun()
        else:
            if st.button("📄 Process Document"):
                try:
                    content = uploaded_file.read().decode('utf-8', errors='ignore')
                    brief_text = f"Please analyze this document ({uploaded_file.name}):\n\n{content[:3000]}..."
                    st.session_state.messages.append({"role": "user", "content": f"📄 Processing: {uploaded_file.name}"})
                    st.session_state.pending_message = brief_text
                    st.rerun()
                except Exception as e:
                    st.error(f"Error reading file: {e}")
    
    st.divider()
    
    # Quick examples
    st.subheader("⚡ Quick Examples")
    
    if st.button("🚗 Car Commercial Brief"):
        sample = """Client: Mercedes-Benz
Project: New EV Campaign
Budget: $75,000

We need an upbeat, modern track that captures innovation and sustainability. 
Think Billie Eilish meets Tame Impala - fresh and forward-thinking.

Deliverables:
- 30 second version
- 60 second version  
- Social cutdowns (15s)

Timeline: Need options by Friday
Territory: Global excluding Japan
Term: 1 year"""
        st.session_state.pending_message = sample
        st.rerun()
    
    if st.button("🏃 Sports Brand Brief"):
        sample = """Client: Nike
Campaign: Just Do It 2024
Budget: $50,000

Looking for high-energy, motivational music for new running shoe launch.
Reference: Imagine Dragons, Kendrick Lamar
Avoid: Nothing too aggressive or dark

Media: TV, Online, Social
Territory: North America
Term: 6 months"""
        st.session_state.pending_message = sample
        st.rerun()
    
    if st.button("💰 Show Margin Calculator"):
        sample = "Show me the margin structure and calculate payouts for budgets of $10k, $50k, $100k, and $200k"
        st.session_state.pending_message = sample
        st.rerun()
    
    st.divider()
    
    # Session info
    st.caption(f"Session: {st.session_state.thread_id[:8]}...")
    if st.button("🔄 New Session"):
        st.session_state.messages = []
        st.session_state.thread_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        st.session_state.project_info = {}
        st.rerun()

# Main area
st.title("🎵 TF Music Workflow Assistant")

# Project metrics (if available)
if st.session_state.project_info:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Project Type", 
            st.session_state.project_info.get('project_type', 'TBD'),
            help="A: >$100k, B: >$25k, C: <$25k"
        )
    with col2:
        budget = st.session_state.project_info.get('budget', 0)
        st.metric("Budget", f"${budget:,}" if budget else "TBD")
    with col3:
        payout = st.session_state.project_info.get('payout', 0)
        st.metric("Payout", f"${payout:,}" if payout else "TBD")
    with col4:
        margin = st.session_state.project_info.get('margin_percentage', 0)
        st.metric("Margin", f"{margin}%" if margin else "TBD")
    st.divider()

# Chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("is_json"):
            st.json(message["content"])
        else:
            st.markdown(message["content"])

# Process pending message
if hasattr(st.session_state, 'pending_message'):
    prompt = st.session_state.pending_message
    del st.session_state.pending_message
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process through API
    with st.chat_message("assistant"):
        with st.spinner("🎵 TF Agents analyzing your brief..."):
            try:
                # API call
                headers = {
                    "Content-Type": "application/json"
                }
                
                # Add API key if available
                api_key = st.secrets.get("LANGGRAPH_API_KEY", "")
                if api_key:
                    headers["x-api-key"] = api_key
                
                response = requests.post(
                    f"{LANGGRAPH_URL}/runs/invoke",
                    headers=headers,
                    json={
                        "input": {
                            "messages": [],
                            "raw_brief": prompt,
                            "current_task": "analyze_brief",
                            "brief_analysis": None,
                            "project_strategy": None,
                            "next_agent": ""
                        },
                        "config": {
                            "configurable": {
                                "thread_id": st.session_state.thread_id
                            }
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Create a formatted response
                    response_parts = []
                    
                    # Show brief analysis
                    if result.get('brief_analysis'):
                        response_parts.append("### 📋 Brief Analysis")
                        analysis = result['brief_analysis']
                        
                        if isinstance(analysis, dict):
                            # Format each section nicely
                            sections = {
                                'client_info': '**Client Information**',
                                'business_brief': '**Business Requirements**',
                                'creative_brief': '**Creative Direction**',
                                'technical_brief': '**Technical Specifications**',
                                'deliverables': '**Deliverables**'
                            }
                            
                            for key, title in sections.items():
                                if key in analysis and analysis[key]:
                                    response_parts.append(f"\n{title}")
                                    content = analysis[key]
                                    if isinstance(content, dict):
                                        for k, v in content.items():
                                            if v:
                                                response_parts.append(f"- {k.replace('_', ' ').title()}: {v}")
                                    else:
                                        response_parts.append(f"{content}")
                    
                    # Show project strategy
                    if result.get('project_strategy'):
                        response_parts.append("\n### 💡 Project Strategy")
                        strategy = result['project_strategy']
                        
                        if isinstance(strategy, dict):
                            # Update session state
                            st.session_state.project_info = strategy
                            
                            # Display strategy details
                            response_parts.append(f"- **Project Type**: {strategy.get('project_type', 'TBD')}")
                            response_parts.append(f"- **Budget**: ${strategy.get('budget', 0):,}")
                            response_parts.append(f"- **Payout**: ${strategy.get('payout', 0):,}")
                            response_parts.append(f"- **Margin**: {strategy.get('margin_percentage', 0)}%")
                            
                            if strategy.get('approach'):
                                response_parts.append(f"\n**Recommended Approach**: {strategy['approach']}")
                            
                            if strategy.get('key_considerations'):
                                response_parts.append("\n**Key Considerations**:")
                                for consideration in strategy['key_considerations']:
                                    response_parts.append(f"- {consideration}")
                    
                    # Join all parts
                    if response_parts:
                        full_response = "\n".join(response_parts)
                        st.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        
                        # Show success message
                        st.success("✅ Brief analyzed successfully!")
                    else:
                        # Fallback if no structured data
                        st.info("Brief received and processed. The analysis has been completed.")
                        st.session_state.messages.append({"role": "assistant", "content": "Brief processed successfully."})
                    
                    # Force update of metrics
                    st.rerun()
                    
                else:
                    error_msg = f"API Error: {response.status_code}"
                    if response.text:
                        error_msg += f"\n{response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.exceptions.Timeout:
                st.error("Request timed out. The brief might be too complex. Try a shorter version.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Note: Make sure the API key is configured in Streamlit secrets if required.")

# Chat input
if prompt := st.chat_input("Paste your brief or describe your music needs..."):
    st.session_state.pending_message = prompt
    st.rerun()

# Instructions at bottom
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Paste a brief**: Copy and paste your project brief into the chat
    2. **Upload files**: Use the sidebar to upload CSV budget files or brief documents  
    3. **Try examples**: Click the quick example buttons in the sidebar
    4. **View analysis**: The system will analyze your brief and show:
       - Project type (A/B/C based on budget)
       - Budget and calculated payout
       - Recommended approach
       - Key considerations
    
    **Margin Structure**:
    - $0-1,500: 100% margin
    - $1,500-30,000: 50% margin
    - $30,000-100,000: 25% margin
    - $100,000-250,000: 20% margin
    - Above $500,000: 10% margin
    """)
