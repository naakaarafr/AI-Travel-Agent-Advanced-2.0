#!/usr/bin/env python3
"""
AI Travel Planner - Streamlit Interface
Beautiful UI for the multi-agent travel planning system
"""

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from crew.py - keeping all backend logic intact
from crew import (
    TravelRequest,
    TravelPlannerAgents,
    check_system_requirements,
    REPORTS_DIR
)

# Page configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling with dark mode support
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
    }
    
    /* Enhanced button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        color: white !important;
        padding: 0.875rem 2rem;
        font-size: 1.125rem;
        font-weight: 600;
        border: none;
        border-radius: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #ec4899 100%);
    }
    
    .stButton>button:active {
        transform: translateY(-1px);
    }
    
    /* Header styling with gradient */
    .header-container {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .header-container h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    .header-container p {
        font-size: 1.25rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    /* Info boxes with better contrast */
    .info-box {
        background: rgba(99, 102, 241, 0.1);
        border: 2px solid #6366f1;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        color: inherit;
    }
    
    .info-box h4 {
        color: #6366f1;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    
    .success-box {
        background: rgba(34, 197, 94, 0.1);
        border: 2px solid #22c55e;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        color: inherit;
    }
    
    .success-box h4 {
        color: #22c55e;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    
    .warning-box {
        background: rgba(234, 179, 8, 0.1);
        border: 2px solid #eab308;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        color: inherit;
    }
    
    .warning-box h3, .warning-box h4 {
        color: #eab308;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    
    .error-box {
        background: rgba(239, 68, 68, 0.1);
        border: 2px solid #ef4444;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        color: inherit;
    }
    
    .error-box h4 {
        color: #ef4444;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    
    /* Card styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Feature cards */
    .feature-card {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.2);
        padding: 1.25rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateX(5px);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: rgba(0, 0, 0, 0.02);
    }
    
    /* Input field enhancements */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select,
    .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 2px solid rgba(99, 102, 241, 0.3);
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>select:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.5rem 0;
    }
    
    .status-ready {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid #22c55e;
    }
    
    .status-not-ready {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
        border: 1px solid #eab308;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem;
        border-top: 2px solid rgba(99, 102, 241, 0.2);
    }
    
    .footer-emoji {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Progress bar customization */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #d946ef);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(99, 102, 241, 0.05);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Download button special styling */
    .download-section {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid rgba(99, 102, 241, 0.3);
        margin: 1.5rem 0;
    }
    
    /* Emoji styling */
    .big-emoji {
        font-size: 2.5rem;
        display: inline-block;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    /* Dark mode specific fixes */
    [data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.02);
    }
    
    /* Better text contrast */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: inherit;
    }
    
    /* Improved card backgrounds for dark mode */
    [data-testid="stVerticalBlock"] > div {
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'planner' not in st.session_state:
    st.session_state.planner = None
if 'planning_result' not in st.session_state:
    st.session_state.planning_result = None
if 'system_ready' not in st.session_state:
    st.session_state.system_ready = False

def initialize_system():
    """Check system requirements and initialize planner"""
    with st.spinner("🔍 Checking system requirements..."):
        issues = check_system_requirements()
        
        if issues:
            st.error("❌ System Requirements Not Met")
            for issue in issues:
                st.markdown(f'<div class="error-box"><h4>⚠️ Issue Detected</h4><p>{issue}</p></div>', unsafe_allow_html=True)
            return False
        
        st.success("✅ All system requirements met!")
        
        try:
            with st.spinner("🤖 Initializing AI Travel Planner..."):
                st.session_state.planner = TravelPlannerAgents()
                st.session_state.system_ready = True
                st.markdown(f'<div class="success-box"><h4>✅ System Ready</h4><p>Using Ollama model: <strong>{st.session_state.planner.ollama_manager.current_model}</strong></p></div>', unsafe_allow_html=True)
                return True
        except Exception as e:
            st.error(f"❌ Failed to initialize planner: {e}")
            return False

def save_plan_to_file(result: str, request: TravelRequest) -> Path:
    """Save the travel plan to a markdown file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"travel_plan_{timestamp}.md"
    filepath = REPORTS_DIR / filename
    
    content = f"""# Travel Plan
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**AI Model:** {st.session_state.planner.ollama_manager.current_model}

## Trip Summary
- **Origin:** {request.origin}
- **Destination Options:** {', '.join(request.destinations)}
- **Travel Dates:** {request.start_date} to {request.end_date}
- **Duration:** {request.duration} days
- **Group Size:** {request.group_size} travelers
- **Budget Range:** {request.budget_range}
- **Travel Style:** {request.travel_style}
- **Interests:** {', '.join(request.interests)}

---

## Travel Plan

{result}

---

*Generated by AI Travel Planner powered by Ollama*
*All recommendations are AI-generated. Please verify details before booking.*
"""
    
    filepath.write_text(content, encoding='utf-8')
    return filepath

def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="big-emoji">✈️</div>
        <h1>AI Travel Planner</h1>
        <p>Powered by Ollama - Your Personal Multi-Agent Travel Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Control Panel")
        
        if st.button("🚀 Initialize System", use_container_width=True):
            initialize_system()
        
        st.markdown("---")
        
        # System Status with enhanced styling
        st.markdown("### 📊 System Status")
        if st.session_state.system_ready:
            st.markdown('<div class="status-badge status-ready">✅ System Ready</div>', unsafe_allow_html=True)
            if st.session_state.planner:
                st.markdown(f"""
                <div class="feature-card">
                    <strong>🤖 AI Model</strong><br>
                    {st.session_state.planner.ollama_manager.current_model}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge status-not-ready">⚠️ Not Initialized</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Features section
        st.markdown("### ✨ Features")
        st.markdown("""
        <div class="feature-card">
            <strong>🎯 Destination Analysis</strong><br>
            Multi-factor comparison
        </div>
        <div class="feature-card">
            <strong>🗺️ Local Insights</strong><br>
            Hidden gems & secrets
        </div>
        <div class="feature-card">
            <strong>📅 Full Itinerary</strong><br>
            Day-by-day planning
        </div>
        <div class="feature-card">
            <strong>💰 Budget Planning</strong><br>
            Detailed cost breakdown
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Tech stack
        st.markdown("### 🔧 Tech Stack")
        st.markdown("""
        - 🤖 **Ollama** - Local AI
        - 🔍 **SerperDev** - Web Search
        - 👥 **CrewAI** - Multi-Agent
        - 🎨 **Streamlit** - Interface
        """)
        

    
    # Main content
    if not st.session_state.system_ready:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("""
            <div class="warning-box">
                <h3>⚠️ System Not Initialized</h3>
                <p style="margin: 1rem 0;">Please click the <strong>"Initialize System"</strong> button in the sidebar to get started.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<h2 class='section-header'>📋 Prerequisites Checklist</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4>1️⃣ Install Ollama</h4>
                <p><strong>Linux/Mac:</strong></p>
                <code>ollama serve</code>
                <p style="margin-top: 1rem;"><strong>Windows:</strong></p>
                <p>Auto-starts on installation</p>
                <p style="margin-top: 1rem;">📥 <a href="https://ollama.ai/download" target="_blank">Download Ollama</a></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>3️⃣ Optional: Search API</h4>
                <p>For enhanced web search capabilities</p>
                <code>SERPER_API_KEY=your_key</code>
                <p style="margin-top: 1rem;">🔑 <a href="https://serper.dev" target="_blank">Get API Key</a></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4>2️⃣ Pull AI Model</h4>
                <p>Download an AI model to use:</p>
                <code>ollama pull llama3.2</code>
                <p style="margin-top: 1rem;"><strong>Recommended models:</strong></p>
                <ul style="margin-left: 1rem;">
                    <li>llama3.2 (Fastest)</li>
                    <li>mistral (Balanced)</li>
                    <li>llama3.1 (Advanced)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>4️⃣ Environment Setup</h4>
                <p>Create a <code>.env</code> file:</p>
                <code>SERPER_API_KEY=your_key_here</code>
                <p style="margin-top: 1rem;">Place it in your project root directory</p>
            </div>
            """, unsafe_allow_html=True)
        
        return
    
    # Travel Planning Form
    st.markdown("<h2 class='section-header'>🎯 Plan Your Perfect Trip</h2>", unsafe_allow_html=True)
    
    # Create tabs for better organization
    tab1, tab2 = st.tabs(["📍 Trip Details", "🎨 Preferences"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏠 Departure & Destinations")
            
            origin = st.text_input(
                "Where are you traveling from?",
                placeholder="e.g., New York, London, Tokyo",
                help="Enter your departure city",
                key="origin"
            )
            
            destinations_input = st.text_input(
                "Destinations to compare (comma-separated)",
                placeholder="e.g., Paris, Rome, Barcelona",
                help="Enter multiple destinations for AI to analyze",
                key="destinations"
            )
        
        with col2:
            st.markdown("#### 📅 Travel Dates")
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() + timedelta(days=30),
                    min_value=datetime.now(),
                    help="When does your trip begin?"
                )
            
            with col_date2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now() + timedelta(days=37),
                    min_value=start_date,
                    help="When does your trip end?"
                )
            
            duration = max((end_date - start_date).days, 1)
            st.info(f"📊 Trip Duration: **{duration} days**")
        
        st.markdown("#### 👥 Group Information")
        group_size = st.number_input(
            "Number of Travelers",
            min_value=1,
            max_value=20,
            value=1,
            help="How many people are traveling?"
        )
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Budget & Style")
            
            budget_range = st.selectbox(
                "Budget Range",
                options=["budget", "mid-range", "luxury"],
                index=1,
                help="Select your budget preference"
            )
            
            travel_style = st.selectbox(
                "Travel Style",
                options=["relaxed", "adventure", "cultural", "romantic", "family"],
                help="Choose your preferred travel style"
            )
        
        with col2:
            st.markdown("#### 🎨 Interests")
            
            interests_input = st.text_area(
                "Your Interests (comma-separated)",
                placeholder="e.g., food, history, nature, art, photography, beaches",
                help="What are you passionate about?",
                height=100
            )
        
        st.markdown("#### 📝 Special Requirements (Optional)")
        special_requirements = st.text_area(
            "Any special needs or preferences?",
            placeholder="e.g., vegetarian food, wheelchair accessible, pet-friendly, gluten-free",
            help="Let us know about any special requirements",
            height=80
        )
    
    # Plan Trip Button with enhanced styling
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        plan_button = st.button("🚀 Generate My Travel Plan", use_container_width=True, type="primary")
    
    if plan_button:
        # Validation
        if not origin or not destinations_input or not interests_input:
            st.markdown("""
            <div class="error-box">
                <h4>❌ Missing Required Information</h4>
                <p>Please fill in:</p>
                <ul>
                    <li>✈️ Origin city</li>
                    <li>🎯 At least one destination</li>
                    <li>🎨 Your interests</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Parse inputs
        destinations = [d.strip() for d in destinations_input.split(',') if d.strip()]
        interests = [i.strip() for i in interests_input.split(',') if i.strip()]
        special_reqs = [s.strip() for s in special_requirements.split(',') if s.strip()] if special_requirements else []
        
        if not destinations:
            st.error("❌ Please provide at least one destination")
            return
        
        if not interests:
            st.error("❌ Please provide at least one interest")
            return
        
        # Create request
        request = TravelRequest(
            origin=origin,
            destinations=destinations,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            duration=duration,
            budget_range=budget_range,
            travel_style=travel_style,
            interests=interests,
            group_size=group_size,
            special_requirements=special_reqs
        )
        
        # Display planning info with beautiful card
        st.markdown(f"""
        <div class="info-box">
            <h4>🔄 AI Agents Working on Your Trip...</h4>
            <p><strong>📊 Analyzing:</strong> {len(destinations)} destination(s)</p>
            <p><strong>📅 Duration:</strong> {duration} days</p>
            <p><strong>🤖 AI Model:</strong> {st.session_state.planner.ollama_manager.current_model}</p>
            <p><strong>⏳ Estimated Time:</strong> 5-10 minutes</p>
            <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">Our AI agents are analyzing weather, costs, attractions, and creating your perfect itinerary...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Start planning
            status_text.markdown("🔍 **Phase 1/3:** Analyzing destinations and comparing options...")
            progress_bar.progress(15)
            
            status_text.markdown("🗺️ **Phase 2/3:** Gathering local insights and hidden gems...")
            progress_bar.progress(35)
            
            result = st.session_state.planner.plan_trip(request)
            
            progress_bar.progress(85)
            status_text.markdown("📋 **Phase 3/3:** Finalizing itinerary and budget...")
            
            progress_bar.progress(100)
            status_text.markdown("✅ **Complete!** Your personalized travel plan is ready!")
            
            st.session_state.planning_result = result
            
            # Success message
            st.balloons()
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<h2 class='section-header'>🎉 Your Personalized Travel Plan</h2>", unsafe_allow_html=True)
            
            # Save to file
            filepath = save_plan_to_file(result, request)
            
            # Download section with beautiful styling
            st.markdown("""
            <div class="download-section">
                <h3 style="text-align: center; margin-bottom: 1rem;">📥 Download Your Travel Plan</h3>
                <p style="text-align: center; opacity: 0.8;">Save your itinerary for offline access</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Download button
            with open(filepath, 'r', encoding='utf-8') as f:
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    st.download_button(
                        label="📥 Download Complete Itinerary (Markdown)",
                        data=f.read(),
                        file_name=filepath.name,
                        mime="text/markdown",
                        use_container_width=True
                    )
            
            st.markdown(f'<div class="success-box"><h4>💾 Auto-Saved</h4><p>Your plan has been saved to: <code>{filepath}</code></p></div>', unsafe_allow_html=True)
            
            # Display result in expandable section with proper formatting
            with st.expander("📋 View Complete Travel Plan", expanded=True):
                # Add custom CSS for better markdown rendering
                st.markdown("""
                <style>
                    .travel-plan-content {
                        line-height: 1.8;
                    }
                    .travel-plan-content h1 {
                        color: #6366f1;
                        font-size: 2.5rem;
                        margin-top: 2rem;
                        margin-bottom: 1rem;
                        padding-bottom: 0.5rem;
                        border-bottom: 3px solid #6366f1;
                    }
                    .travel-plan-content h2 {
                        color: #8b5cf6;
                        font-size: 2rem;
                        margin-top: 1.5rem;
                        margin-bottom: 0.75rem;
                        padding-left: 0.5rem;
                        border-left: 4px solid #8b5cf6;
                    }
                    .travel-plan-content h3 {
                        color: #d946ef;
                        font-size: 1.5rem;
                        margin-top: 1.25rem;
                        margin-bottom: 0.5rem;
                    }
                    .travel-plan-content h4 {
                        color: #ec4899;
                        font-size: 1.25rem;
                        margin-top: 1rem;
                        margin-bottom: 0.5rem;
                    }
                    .travel-plan-content ul, .travel-plan-content ol {
                        margin-left: 1.5rem;
                        margin-bottom: 1rem;
                    }
                    .travel-plan-content li {
                        margin-bottom: 0.5rem;
                        line-height: 1.6;
                    }
                    .travel-plan-content p {
                        margin-bottom: 1rem;
                        line-height: 1.7;
                    }
                    .travel-plan-content strong {
                        color: #6366f1;
                        font-weight: 600;
                    }
                    .travel-plan-content code {
                        background: rgba(99, 102, 241, 0.1);
                        padding: 0.2rem 0.4rem;
                        border-radius: 4px;
                        font-family: 'Courier New', monospace;
                    }
                    .travel-plan-content blockquote {
                        border-left: 4px solid #6366f1;
                        padding-left: 1rem;
                        margin: 1rem 0;
                        background: rgba(99, 102, 241, 0.05);
                        padding: 1rem;
                        border-radius: 4px;
                    }
                    .travel-plan-content table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 1rem 0;
                    }
                    .travel-plan-content th {
                        background: rgba(99, 102, 241, 0.1);
                        padding: 0.75rem;
                        text-align: left;
                        font-weight: 600;
                        border-bottom: 2px solid #6366f1;
                    }
                    .travel-plan-content td {
                        padding: 0.75rem;
                        border-bottom: 1px solid rgba(99, 102, 241, 0.2);
                    }
                    .travel-plan-content hr {
                        border: none;
                        border-top: 2px solid rgba(99, 102, 241, 0.2);
                        margin: 2rem 0;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Render the markdown with proper formatting
                st.markdown(f'<div class="travel-plan-content">{result}</div>', unsafe_allow_html=True)
            
            # Footer with trip summary
            st.markdown("""
            <div class="footer">
                <div class="footer-emoji">🌍✈️🎒</div>
                <h3>Have an Amazing Trip!</h3>
                <p style="font-size: 0.95rem; opacity: 0.7; margin-top: 1rem;">
                    All recommendations are AI-generated. Please verify details and prices before booking.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <h4>❌ Planning Failed</h4>
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔧 Troubleshooting Guide"):
                st.markdown("""
                ### Common Solutions:
                
                1. **Check Ollama Status**
                   ```bash
                   ollama serve
                   ```
                
                2. **Verify Model Installation**
                   ```bash
                   ollama list
                   ollama pull llama3.2
                   ```
                
                3. **Restart the System**
                   - Click "Initialize System" in sidebar
                   - Wait for confirmation
                   - Try planning again
                
                4. **Check Logs**
                   - Look at terminal output for detailed errors
                   - Ensure no firewall blocking Ollama
                
                If issues persist, please check the Ollama documentation.
                """)

if __name__ == "__main__":
    main()  