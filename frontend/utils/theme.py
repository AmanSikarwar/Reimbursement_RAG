"""
Theme CSS Styling for Streamlit
"""


def get_theme_css():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #8B5CF6;
        --primary-dark: #7C3AED;
        --background: #1E1B2E;
        --background-light: #2D2A3F;
        --background-lighter: #3D3A4F;
        --text: #FFFFFF;
        --text-secondary: #D1D5DB;
        --accent: #A78BFA;
        --success: #10B981;
        --warning: #F59E0B;
        --error: #EF4444;
        --gradient: linear-gradient(135deg, #1E1B2E 0%, #2D2A3F 100%);
    }
    
    .stApp {
        background: var(--gradient);
        font-family: 'Inter', sans-serif;
    }
    
    .stApp > header {
        background: rgba(30, 27, 46, 0.95);
        backdrop-filter: blur(10px);
    }
    
    .css-1d391kg, .css-1lcbmhc, 
    [data-testid="stSidebar"], 
    .css-17eq0hr,
    section[data-testid="stSidebar"] {
        background: var(--background-light) !important;
        border-right: 1px solid var(--primary) !important;
    }
    
    .css-1d391kg > div,
    [data-testid="stSidebar"] > div,
    .css-17eq0hr > div {
        background: transparent !important;
        color: var(--text) !important;
    }
    
    .css-1d391kg p,
    .css-1d391kg div,
    .css-1d391kg label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: var(--text) !important;
    }
    
    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
    }
    
    .stButton > button:hover {
        background: var(--primary-dark);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
    }
    
    .stButton > button[kind="primary"] {
        background: var(--primary);
        color: white;
        font-weight: 600;
    }
    
    .stButton > button[kind="secondary"] {
        background: var(--background-lighter);
        color: var(--text);
        border: 1px solid var(--primary);
    }
    
    .metric-container {
        background: var(--background-light);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--primary);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stChatMessage, 
    [data-testid="chat-message"],
    .stChatMessage > div,
    [data-testid="stChatMessage"] {
        background: var(--background-light) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        margin: 0.5rem 0 !important;
        color: var(--text) !important;
    }
    
    .stChatInput > div,
    .stChatInput input,
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInputContainer"] {
        background: var(--background-light) !important;
        border: 2px solid var(--primary) !important;
        border-radius: 12px !important;
        color: var(--text) !important;
    }
    
    .stChatMessage p,
    .stChatMessage div,
    [data-testid="chat-message"] p,
    [data-testid="chat-message"] div {
        color: var(--text) !important;
    }
    
    .stChatMessage .stMarkdown,
    [data-testid="chat-message"] .stMarkdown {
        color: var(--text) !important;
    }
    
    .stTextInput > div > div > input,
    .stTextInput input,
    [data-testid="stTextInput"] input,
    input[type="text"] {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > div,
    .stSelectbox select,
    [data-testid="stSelectbox"] > div,
    [data-testid="stSelectbox"] select {
        background: var(--background-light) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }
    
    .stSelectbox option {
        background: var(--background-light) !important;
        color: var(--text) !important;
    }
    
    .stNumberInput > div > div > input,
    .stNumberInput input,
    [data-testid="stNumberInput"] input,
    input[type="number"] {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
    }
    
    .stFileUploader {
        border: 2px dashed var(--primary);
        border-radius: 12px;
        background: var(--background-light);
    }
    
    .stProgress > div > div > div {
        background: var(--primary);
        border-radius: 4px;
    }
    
    .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--success);
        color: var(--success);
        border-radius: 8px;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--warning);
        color: var(--warning);
        border-radius: 8px;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--error);
        color: var(--error);
        border-radius: 8px;
    }
    
    .stInfo {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid var(--primary);
        color: var(--accent);
        border-radius: 8px;
    }
    
    .streamlit-expanderHeader {
        background: var(--background-light);
        border-radius: 8px;
        border: 1px solid var(--primary);
    }
    
    .stDataFrame {
        border: 1px solid var(--primary);
        border-radius: 8px;
        overflow: hidden;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--background-light);
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        border-radius: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary);
        color: white;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--background-light);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-dark);
    }
    
    h1, h2, h3 {
        background: linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }
    
    .card {
        background: var(--background-light);
        border: 1px solid var(--primary);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(139, 92, 246, 0.2);
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
    }
    
    .status-approved {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success);
        border: 1px solid var(--success);
    }
    
    .status-declined {
        background: rgba(239, 68, 68, 0.2);
        color: var(--error);
        border: 1px solid var(--error);
    }
    
    .status-partial {
        background: rgba(245, 158, 11, 0.2);
        color: var(--warning);
        border: 1px solid var(--warning);
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    @media (max-width: 768px) {
        .stApp {
            padding: 1rem 0.5rem;
        }
        
        .card {
            padding: 1rem;
        }
    }
    
    .nav-button {
        background: var(--background-lighter);
        border: 1px solid var(--primary);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background: var(--primary);
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
    }
    
    .nav-button.active {
        background: var(--primary);
        border-color: var(--accent);
    }
    
    .css-1d391kg {
        background: linear-gradient(180deg, var(--background-light) 0%, var(--background) 100%);
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.2);
    }
    
    .status-online {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--success);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--success);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--error);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--error);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--warning);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--warning);
    }
    
    .stMetric {
        background: var(--background-light);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        border-color: var(--primary);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.2);
    }
    
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--primary), transparent);
        margin: 1.5rem 0;
    }
    
    .glow {
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        border: 1px solid var(--primary);
    }
    
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }
    
    .shimmer {
        background: linear-gradient(90deg, var(--background-light) 0px, rgba(139, 92, 246, 0.2) 40px, var(--background-light) 80px);
        background-size: 200px 100%;
        animation: shimmer 1.5s infinite;
    }
    
    .stButton > button:not(:disabled):hover {
        background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
        box-shadow: 0 6px 12px rgba(139, 92, 246, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
    }
    
    .stContainer,
    [data-testid="stContainer"],
    .element-container {
        background: transparent !important;
    }
    
    .streamlit-expanderContent,
    [data-testid="stExpanderDetails"] {
        background: var(--background-light) !important;
        border-radius: 0 0 8px 8px !important;
        color: var(--text) !important;
    }
    
    .streamlit-expanderContent p,
    .streamlit-expanderContent div,
    [data-testid="stExpanderDetails"] p,
    [data-testid="stExpanderDetails"] div {
        color: var(--text) !important;
    }
    
    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        background: transparent !important;
        color: var(--text) !important;
    }
    
    .stMarkdown,
    [data-testid="stMarkdown"] {
        color: var(--text) !important;
    }
    
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown span,
    [data-testid="stMarkdown"] p,
    [data-testid="stMarkdown"] div,
    [data-testid="stMarkdown"] span {
        color: var(--text) !important;
    }
    
    * {
        color: var(--text);
    }
    
    .card,
    .card *,
    .status-badge,
    .status-badge * {
        color: inherit !important;
    }
    
    [data-testid="stApp"] {
        background: var(--gradient) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stHeader"] {
        background: rgba(30, 27, 46, 0.95) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stSidebar"] > div {
        background: var(--background-light) !important;
        border-right: 1px solid var(--primary) !important;
    }
    
    [data-testid="stApp"] *,
    [data-testid="stSidebar"] *,
    [data-testid="stMainBlockContainer"] *,
    .main *,
    div[class*="css-"] * {
        color: var(--text) !important;
    }
    
    .card *,
    .status-badge *,
    [style*="color"] {
        color: inherit !important;
    }
    
    [data-testid="stChatInput"] input::placeholder,
    .stChatInput input::placeholder {
        color: var(--text-secondary) !important;
    }
    
    [data-testid="stSelectbox"] select option,
    .stSelectbox select option {
        background: var(--background-light) !important;
        color: var(--text) !important;
    }
    
    .stApp .main,
    [data-testid="stApp"] .main,
    .main .block-container {
        background: transparent !important;
    }
    
    pre, code {
        background: var(--background-light) !important;
        color: var(--accent) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 4px !important;
        padding: 0.5rem !important;
    }
    
    div[style*="margin-bottom: 1rem; color: #D1D5DB"] {
        color: var(--text-secondary) !important;
    }
    </style>
    """


def apply_theme():
    """Apply the theme to Streamlit."""
    import streamlit as st

    st.markdown(get_theme_css(), unsafe_allow_html=True)
