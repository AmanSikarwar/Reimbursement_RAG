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
    [data-testid="textInput"] input,
    [data-testid="stTextInput"] > div > div > input,
    input[type="text"],
    input[aria-label] {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div,
    .stTextInput > div,
    [data-testid="stTextInput"] > div,
    [data-testid="textInput"] > div {
        border: none !important;
        background: transparent !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextInput input:focus,
    [data-testid="stTextInput"] input:focus,
    [data-testid="textInput"] input:focus,
    input[type="text"]:focus,
    input[aria-label]:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="textInput"] input::placeholder,
    input[type="text"]::placeholder {
        color: var(--text-secondary) !important;
        opacity: 0.7 !important;
    }
    
    .stSelectbox > div > div,
    .stSelectbox select,
    [data-testid="stSelectbox"] > div,
    [data-testid="stSelectbox"] select,
    [data-testid="stSelectbox"] > div > div > div,
    div[data-baseweb="select"] {
        background: var(--background-light) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        transition: all 0.3s ease !important;
    }
    
    .stSelectbox > div,
    [data-testid="stSelectbox"],
    .stSelectbox {
        border: none !important;
        background: transparent !important;
    }
    
    .stSelectbox > div > div:focus-within,
    [data-testid="stSelectbox"] > div:focus-within,
    div[data-baseweb="select"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
    }
    
    .stSelectbox option {
        background: var(--background-light) !important;
        color: var(--text) !important;
    }
    
    .stNumberInput > div > div > input,
    .stNumberInput input,
    [data-testid="stNumberInput"] input,
    [data-testid="stNumberInput"] > div > div > input,
    input[type="number"] {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stNumberInput > div > div,
    .stNumberInput > div,
    [data-testid="stNumberInput"] > div {
        border: none !important;
        background: transparent !important;
    }
    
    .stNumberInput > div > div > input:focus,
    .stNumberInput input:focus,
    [data-testid="stNumberInput"] input:focus,
    input[type="number"]:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
        outline: none !important;
    }
    
    /* File Upload Styling */
    .stFileUploader,
    [data-testid="stFileUploader"],
    [data-testid="fileUploader"] {
        border: 1px dashed var(--primary) !important;
        border-radius: 12px !important;
        background: var(--background-light) !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader:hover,
    [data-testid="stFileUploader"]:hover,
    [data-testid="fileUploader"]:hover {
        border-color: var(--accent) !important;
        background: var(--background-lighter) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2) !important;
    }
    
    .stFileUploader > div,
    [data-testid="stFileUploader"] > div,
    [data-testid="fileUploader"] > div {
        background: transparent !important;
        border: none !important;
    }
    
    .stFileUploader label,
    [data-testid="stFileUploader"] label,
    [data-testid="fileUploader"] label {
        color: var(--text) !important;
        font-weight: 500 !important;
    }
    
    .stFileUploader small,
    [data-testid="stFileUploader"] small,
    [data-testid="fileUploader"] small {
        color: var(--text-secondary) !important;
    }
    
    /* File Upload Button */
    .stFileUploader button,
    [data-testid="stFileUploader"] button,
    [data-testid="fileUploader"] button,
    button[kind="secondary"] {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    .stFileUploader button:hover,
    [data-testid="stFileUploader"] button:hover,
    [data-testid="fileUploader"] button:hover,
    button[kind="secondary"]:hover {
        background: var(--primary-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3) !important;
    }
    
    /* File Upload Drop Zone */
    .stFileUploader > div > div,
    [data-testid="stFileUploader"] > div > div,
    [data-testid="fileUploader"] > div > div {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 2rem !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div > div:hover,
    [data-testid="stFileUploader"] > div > div:hover,
    [data-testid="fileUploader"] > div > div:hover {
        background: rgba(139, 92, 246, 0.05) !important;
    }
    
    /* Drag and Drop Text */
    .stFileUploader [data-testid="stFileDropzoneInstructions"],
    [data-testid="stFileUploader"] [data-testid="stFileDropzoneInstructions"],
    [data-testid="fileUploader"] [data-testid="stFileDropzoneInstructions"] {
        color: var(--text) !important;
        font-size: 1rem !important;
    }
    
    .stFileUploader [data-testid="stFileDropzoneInstructions"] span,
    [data-testid="stFileUploader"] [data-testid="stFileDropzoneInstructions"] span,
    [data-testid="fileUploader"] [data-testid="stFileDropzoneInstructions"] span {
        color: var(--accent) !important;
        font-weight: 600 !important;
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
    
    /* Additional Input Field Coverage */
    div[data-baseweb="input"] {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="input"] input {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
    }
    
    div[data-baseweb="input"]:focus-within input {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
    }
    
    /* Form Labels */
    .stFormSubmitButton,
    [data-testid="stFormSubmitButton"] {
        background: var(--primary) !important;
    }
    
    .stFormSubmitButton button,
    [data-testid="stFormSubmitButton"] button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stFormSubmitButton button:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        background: var(--primary-dark) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3) !important;
    }
    
    /* Input Focus States */
    input:focus,
    select:focus,
    textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
        outline: none !important;
    }
    
    /* Generic Input Styling */
    input[class*="st-"],
    select[class*="st-"],
    textarea[class*="st-"] {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
    }
    
    /* Modern Streamlit Component Selectors */
    [data-testid*="input"],
    [data-testid*="Input"],
    [class*="input"],
    [class*="Input"] {
        background: transparent !important;
        color: var(--text) !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    [data-testid*="input"] input,
    [data-testid*="Input"] input,
    [class*="input"] input,
    [class*="Input"] input {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
    }
    
    [data-testid*="input"]:focus-within,
    [data-testid*="Input"]:focus-within,
    [class*="input"]:focus-within,
    [class*="Input"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
    }
    
    /* File Upload Modern Selectors */
    [data-testid*="fileUpload"],
    [data-testid*="file-upload"],
    [class*="fileUpload"],
    [class*="file-upload"] {
        border: 1px dashed var(--primary) !important;
        border-radius: 12px !important;
        background: var(--background-light) !important;
    }
    
    [data-testid*="fileUpload"]:hover,
    [data-testid*="file-upload"]:hover,
    [class*="fileUpload"]:hover,
    [class*="file-upload"]:hover {
        border-color: var(--accent) !important;
        background: var(--background-lighter) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1) !important;
    }
    
    /* Button Modern Selectors */
    [data-testid*="button"],
    [data-testid*="Button"],
    [class*="button"]:not(.nav-button),
    [class*="Button"]:not(.nav-button) {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid*="button"]:hover,
    [data-testid*="Button"]:hover,
    [class*="button"]:not(.nav-button):hover,
    [class*="Button"]:not(.nav-button):hover {
        background: var(--primary-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3) !important;
    }
    
    /* Universal Input Styling - Fallback for any missed inputs */
    input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
    select,
    textarea {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):focus,
    select:focus,
    textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3) !important;
        outline: none !important;
    }
    
    input:not([type="checkbox"]):not([type="radio"]):not([type="file"])::placeholder,
    textarea::placeholder {
        color: var(--text-secondary) !important;
        opacity: 0.7 !important;
    }
    
    /* File input specific styling */
    input[type="file"] {
        background: var(--background-light) !important;
        color: var(--text) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
    }
    
    /* Ensure all buttons follow theme */
    button:not(.nav-button) {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    
    button:not(.nav-button):hover {
        background: var(--primary-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3) !important;
    }
    </style>
    """


def apply_theme():
    """Apply the theme to Streamlit."""
    import streamlit as st

    st.markdown(get_theme_css(), unsafe_allow_html=True)
