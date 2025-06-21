"""
iAI Solutions Theme CSS Styling for Streamlit
Based on the color palette from https://www.iaisolution.com/
"""

def get_iai_theme_css():
    """Return CSS for iAI Solutions inspired theme."""
    return """
    <style>
    /* Import Google Fonts for better typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for iAI color palette */
    :root {
        --iai-primary: #8B5CF6;
        --iai-primary-dark: #7C3AED;
        --iai-background: #1E1B2E;
        --iai-background-light: #2D2A3F;
        --iai-background-lighter: #3D3A4F;
        --iai-text: #FFFFFF;
        --iai-text-secondary: #D1D5DB;
        --iai-accent: #A78BFA;
        --iai-success: #10B981;
        --iai-warning: #F59E0B;
        --iai-error: #EF4444;
        --iai-gradient: linear-gradient(135deg, #1E1B2E 0%, #2D2A3F 100%);
    }
    
    /* Main app styling */
    .stApp {
        background: var(--iai-gradient);
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .stApp > header {
        background: rgba(30, 27, 46, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* Sidebar styling - Enhanced */
    .css-1d391kg, .css-1lcbmhc, 
    [data-testid="stSidebar"], 
    .css-17eq0hr,
    section[data-testid="stSidebar"] {
        background: var(--iai-background-light) !important;
        border-right: 1px solid var(--iai-primary) !important;
    }
    
    /* Sidebar content */
    .css-1d391kg > div,
    [data-testid="stSidebar"] > div,
    .css-17eq0hr > div {
        background: transparent !important;
        color: var(--iai-text) !important;
    }
    
    /* Fix for sidebar text */
    .css-1d391kg p,
    .css-1d391kg div,
    .css-1d391kg label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: var(--iai-text) !important;
    }
    
    /* Sidebar navigation buttons */
    .stButton > button {
        background: var(--iai-primary);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
    }
    
    .stButton > button:hover {
        background: var(--iai-primary-dark);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
    }
    
    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: var(--iai-primary);
        color: white;
        font-weight: 600;
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: var(--iai-background-lighter);
        color: var(--iai-text);
        border: 1px solid var(--iai-primary);
    }
    
    /* Metrics styling */
    .metric-container {
        background: var(--iai-background-light);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--iai-primary);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Chat messages - More specific selectors */
    .stChatMessage, 
    [data-testid="chat-message"],
    .stChatMessage > div,
    [data-testid="stChatMessage"] {
        background: var(--iai-background-light) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        margin: 0.5rem 0 !important;
        color: var(--iai-text) !important;
    }
    
    /* Chat input - Enhanced selectors */
    .stChatInput > div,
    .stChatInput input,
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInputContainer"] {
        background: var(--iai-background-light) !important;
        border: 2px solid var(--iai-primary) !important;
        border-radius: 12px !important;
        color: var(--iai-text) !important;
    }
    
    /* Fix for chat message content */
    .stChatMessage p,
    .stChatMessage div,
    [data-testid="chat-message"] p,
    [data-testid="chat-message"] div {
        color: var(--iai-text) !important;
    }
    
    /* Fix for markdown content in chat */
    .stChatMessage .stMarkdown,
    [data-testid="chat-message"] .stMarkdown {
        color: var(--iai-text) !important;
    }
    
    /* Text inputs - Enhanced */
    .stTextInput > div > div > input,
    .stTextInput input,
    [data-testid="stTextInput"] input,
    input[type="text"] {
        background: var(--iai-background-light) !important;
        color: var(--iai-text) !important;
        border: 1px solid var(--iai-primary) !important;
        border-radius: 8px !important;
    }
    
    /* Select boxes - Enhanced */
    .stSelectbox > div > div,
    .stSelectbox select,
    [data-testid="stSelectbox"] > div,
    [data-testid="stSelectbox"] select {
        background: var(--iai-background-light) !important;
        border: 1px solid var(--iai-primary) !important;
        border-radius: 8px !important;
        color: var(--iai-text) !important;
    }
    
    /* Selectbox dropdown options */
    .stSelectbox option {
        background: var(--iai-background-light) !important;
        color: var(--iai-text) !important;
    }
    
    /* Number inputs - Enhanced */
    .stNumberInput > div > div > input,
    .stNumberInput input,
    [data-testid="stNumberInput"] input,
    input[type="number"] {
        background: var(--iai-background-light) !important;
        color: var(--iai-text) !important;
        border: 1px solid var(--iai-primary) !important;
        border-radius: 8px !important;
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed var(--iai-primary);
        border-radius: 12px;
        background: var(--iai-background-light);
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: var(--iai-primary);
        border-radius: 4px;
    }
    
    /* Success messages */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--iai-success);
        color: var(--iai-success);
        border-radius: 8px;
    }
    
    /* Warning messages */
    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--iai-warning);
        color: var(--iai-warning);
        border-radius: 8px;
    }
    
    /* Error messages */
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--iai-error);
        color: var(--iai-error);
        border-radius: 8px;
    }
    
    /* Info messages */
    .stInfo {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid var(--iai-primary);
        color: var(--iai-accent);
        border-radius: 8px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--iai-background-light);
        border-radius: 8px;
        border: 1px solid var(--iai-primary);
    }
    
    /* Data frames */
    .stDataFrame {
        border: 1px solid var(--iai-primary);
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--iai-background-light);
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--iai-text-secondary);
        border-radius: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--iai-primary);
        color: white;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--iai-background-light);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--iai-primary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--iai-primary-dark);
    }
    
    /* Headers with gradient effect */
    h1, h2, h3 {
        background: linear-gradient(135deg, var(--iai-text) 0%, var(--iai-accent) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }
    
    /* Custom card styling */
    .iai-card {
        background: var(--iai-background-light);
        border: 1px solid var(--iai-primary);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .iai-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(139, 92, 246, 0.2);
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
    }
    
    .status-approved {
        background: rgba(16, 185, 129, 0.2);
        color: var(--iai-success);
        border: 1px solid var(--iai-success);
    }
    
    .status-declined {
        background: rgba(239, 68, 68, 0.2);
        color: var(--iai-error);
        border: 1px solid var(--iai-error);
    }
    
    .status-partial {
        background: rgba(245, 158, 11, 0.2);
        color: var(--iai-warning);
        border: 1px solid var(--iai-warning);
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .stApp {
            padding: 1rem 0.5rem;
        }
        
        .iai-card {
            padding: 1rem;
        }
    }
    
    /* Enhanced navigation styling */
    .nav-button {
        background: var(--iai-background-lighter);
        border: 1px solid var(--iai-primary);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background: var(--iai-primary);
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
    }
    
    .nav-button.active {
        background: var(--iai-primary);
        border-color: var(--iai-accent);
    }
    
    /* Enhanced sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--iai-background-light) 0%, var(--iai-background) 100%);
    }
    
    /* Logo and title area enhancement */
    .sidebar-header {
        background: linear-gradient(135deg, var(--iai-primary) 0%, var(--iai-accent) 100%);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.2);
    }
    
    /* Status indicators */
    .status-online {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--iai-success);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--iai-success);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--iai-error);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--iai-error);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--iai-warning);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--iai-warning);
    }
    
    /* Enhanced metrics styling */
    .stMetric {
        background: var(--iai-background-light);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        border-color: var(--iai-primary);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.2);
    }
    
    /* Enhanced dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--iai-primary), transparent);
        margin: 1.5rem 0;
    }
    
    /* Glowing effect for important elements */
    .glow {
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        border: 1px solid var(--iai-primary);
    }
    
    /* Loading shimmer effect */
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }
    
    .shimmer {
        background: linear-gradient(90deg, var(--iai-background-light) 0px, rgba(139, 92, 246, 0.2) 40px, var(--iai-background-light) 80px);
        background-size: 200px 100%;
        animation: shimmer 1.5s infinite;
    }
    
    /* Enhanced button hover states */
    .stButton > button:not(:disabled):hover {
        background: linear-gradient(135deg, var(--iai-primary) 0%, var(--iai-accent) 100%);
        box-shadow: 0 6px 12px rgba(139, 92, 246, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
    }
    
    /* Fix for container backgrounds */
    .stContainer,
    [data-testid="stContainer"],
    .element-container {
        background: transparent !important;
    }
    
    /* Fix for expander content */
    .streamlit-expanderContent,
    [data-testid="stExpanderDetails"] {
        background: var(--iai-background-light) !important;
        border-radius: 0 0 8px 8px !important;
        color: var(--iai-text) !important;
    }
    
    /* Fix for markdown in expandable areas */
    .streamlit-expanderContent p,
    .streamlit-expanderContent div,
    [data-testid="stExpanderDetails"] p,
    [data-testid="stExpanderDetails"] div {
        color: var(--iai-text) !important;
    }
    
    /* Fix for main content area */
    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        background: transparent !important;
        color: var(--iai-text) !important;
    }
    
    /* Fix for specific components showing raw content */
    .stMarkdown,
    [data-testid="stMarkdown"] {
        color: var(--iai-text) !important;
    }
    
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown span,
    [data-testid="stMarkdown"] p,
    [data-testid="stMarkdown"] div,
    [data-testid="stMarkdown"] span {
        color: var(--iai-text) !important;
    }
    
    /* Force text color for all elements */
    * {
        color: var(--iai-text);
    }
    
    /* But allow specific elements to override */
    .iai-card,
    .iai-card *,
    .status-badge,
    .status-badge * {
        color: inherit !important;
    }
    
    /* Modern Streamlit selectors for latest versions */
    [data-testid="stApp"] {
        background: var(--iai-gradient) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stHeader"] {
        background: rgba(30, 27, 46, 0.95) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stSidebar"] > div {
        background: var(--iai-background-light) !important;
        border-right: 1px solid var(--iai-primary) !important;
    }
    
    /* Universal text color fix */
    [data-testid="stApp"] *,
    [data-testid="stSidebar"] *,
    [data-testid="stMainBlockContainer"] *,
    .main *,
    div[class*="css-"] * {
        color: var(--iai-text) !important;
    }
    
    /* Override for styled components */
    .iai-card *,
    .status-badge *,
    [style*="color"] {
        color: inherit !important;
    }
    
    /* Chat input placeholder */
    [data-testid="stChatInput"] input::placeholder,
    .stChatInput input::placeholder {
        color: var(--iai-text-secondary) !important;
    }
    
    /* Select dropdown options */
    [data-testid="stSelectbox"] select option,
    .stSelectbox select option {
        background: var(--iai-background-light) !important;
        color: var(--iai-text) !important;
    }
    
    /* Force background for main content */
    .stApp .main,
    [data-testid="stApp"] .main,
    .main .block-container {
        background: transparent !important;
    }
    
    /* Specific fix for visible HTML/CSS content */
    pre, code {
        background: var(--iai-background-light) !important;
        color: var(--iai-accent) !important;
        border: 1px solid var(--iai-primary) !important;
        border-radius: 4px !important;
        padding: 0.5rem !important;
    }
    
    /* Hide or style debugging content */
    div[style*="margin-bottom: 1rem; color: #D1D5DB"] {
        color: var(--iai-text-secondary) !important;
    }
    </style>
    """

def apply_iai_theme():
    """Apply the iAI Solutions theme to Streamlit."""
    import streamlit as st
    st.markdown(get_iai_theme_css(), unsafe_allow_html=True)
