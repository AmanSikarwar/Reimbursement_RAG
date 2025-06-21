"""
Enhanced UI components with iAI Solutions branding and theme.
"""

import streamlit as st

def render_iai_header(title: str, subtitle: str = "", icon: str = "🏢"):
    """
    Render an enhanced header with iAI Solutions branding.
    
    Args:
        title: Main title text
        subtitle: Optional subtitle text
        icon: Icon to display with the title
    """
    st.markdown(f"""
    <div class="iai-header" style="
        background: linear-gradient(135deg, #1E1B2E 0%, #2D2A3F 50%, #8B5CF6 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0 2rem 0;
        text-align: center;
        box-shadow: 0 8px 16px rgba(139, 92, 246, 0.3);
        border: 1px solid #8B5CF6;
    ">
        <h1 style="
            color: white;
            font-size: 2.5rem;
            margin: 0;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        ">
            {icon} {title}
        </h1>
        {f'<p style="color: #A78BFA; font-size: 1.2rem; margin: 0.5rem 0 0 0; font-weight: 500;">{subtitle}</p>' if subtitle else ''}
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            margin-top: 1rem;
            display: inline-block;
        ">
            <span style="color: #A78BFA; font-size: 0.9rem; font-weight: 600;">
                Powered by iAI Solutions
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_status_card(title: str, value: str, delta: str = "", delta_color: str = "normal", icon: str = "📊"):
    """
    Render a status card with enhanced styling.
    
    Args:
        title: Card title
        value: Main value to display
        delta: Change indicator
        delta_color: Color for delta (normal, inverse)
        icon: Icon for the card
    """
    delta_html = ""
    if delta:
        color = "#10B981" if delta_color == "normal" else "#EF4444"
        delta_html = f'<span style="color: {color}; font-size: 0.9rem; font-weight: 500;">{delta}</span>'
    
    st.markdown(f"""
    <div class="iai-card" style="
        background: linear-gradient(135deg, #2D2A3F 0%, #3D3A4F 100%);
        border: 1px solid #8B5CF6;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <h3 style="color: #A78BFA; margin: 0; font-size: 0.9rem; font-weight: 500; text-transform: uppercase;">{title}</h3>
        <div style="color: white; font-size: 2rem; font-weight: 700; margin: 0.5rem 0;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render_progress_card(title: str, progress: float, subtitle: str = "", icon: str = "⏳"):
    """
    Render a progress card with enhanced styling.
    
    Args:
        title: Card title
        progress: Progress value (0.0 to 1.0)
        subtitle: Optional subtitle
        icon: Icon for the card
    """
    progress_percent = int(progress * 100)
    
    st.markdown(f"""
    <div class="iai-card" style="
        background: linear-gradient(135deg, #2D2A3F 0%, #3D3A4F 100%);
        border: 1px solid #8B5CF6;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h3 style="color: white; margin: 0; font-weight: 600;">{title}</h3>
        </div>
        <div style="
            background: #1E1B2E;
            border-radius: 10px;
            padding: 4px;
            margin-bottom: 0.5rem;
        ">
            <div style="
                background: linear-gradient(90deg, #8B5CF6 0%, #A78BFA 100%);
                height: 8px;
                border-radius: 6px;
                width: {progress_percent}%;
                transition: width 0.5s ease;
            "></div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #A78BFA; font-size: 0.9rem;">{subtitle if subtitle else 'Progress'}</span>
            <span style="color: white; font-weight: 600;">{progress_percent}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_info_banner(message: str, type: str = "info", icon: str = "ℹ️"):
    """
    Render an information banner with enhanced styling.
    
    Args:
        message: Banner message
        type: Banner type (info, success, warning, error)
        icon: Icon for the banner
    """
    colors = {
        "info": {"bg": "rgba(139, 92, 246, 0.1)", "border": "#8B5CF6", "text": "#A78BFA"},
        "success": {"bg": "rgba(16, 185, 129, 0.1)", "border": "#10B981", "text": "#10B981"},
        "warning": {"bg": "rgba(245, 158, 11, 0.1)", "border": "#F59E0B", "text": "#F59E0B"},
        "error": {"bg": "rgba(239, 68, 68, 0.1)", "border": "#EF4444", "text": "#EF4444"}
    }
    
    color = colors.get(type, colors["info"])
    
    st.markdown(f"""
    <div style="
        background: {color['bg']};
        border: 1px solid {color['border']};
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        backdrop-filter: blur(10px);
    ">
        <span style="font-size: 1.5rem; margin-right: 0.75rem;">{icon}</span>
        <span style="color: {color['text']}; font-weight: 500;">{message}</span>
    </div>
    """, unsafe_allow_html=True)

def render_feature_highlight(title: str, description: str, icon: str = "✨"):
    """
    Render a feature highlight box.
    
    Args:
        title: Feature title
        description: Feature description
        icon: Feature icon
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #2D2A3F 0%, #8B5CF6 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 8px 16px rgba(139, 92, 246, 0.2);
        transform: perspective(1000px) rotateX(2deg);
        transition: all 0.3s ease;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h2 style="color: white; margin: 0 0 1rem 0; font-weight: 700;">{title}</h2>
        <p style="color: #D1D5DB; font-size: 1.1rem; line-height: 1.6; margin: 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
