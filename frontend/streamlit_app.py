"""
Grid Downscaling Service - Streamlit Frontend
Modern dark-themed UI with Point/Polygon query modes using Streamlit + Folium

Run: streamlit run streamlit_app.py
Open: http://localhost:8501
Note: Make sure FastAPI backend is running on port 8000
"""

import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import requests
import os

# Configuration - Use environment variable for Docker, fallback to localhost for local dev
API_URL = os.getenv("API_URL", "http://localhost:8000")
BOUNDS = {
    "min_lon": 106.685455, "min_lat": -6.372739,
    "max_lon": 106.973814, "max_lat": -6.074049
}
CENTER = {"lat": -6.223394, "lon": 106.829634}

# Page config
st.set_page_config(
    page_title="Land Value Insight",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    .main .block-container { padding: 0.5rem 1rem; max-width: 100%; }
    [data-testid="stSidebar"] { background-color: #1e293b; }
    .stMetric { background-color: #1e293b; padding: 0.75rem; border-radius: 8px; }
    .stMetric label { color: #94a3b8 !important; font-size: 0.85rem !important; }
    .stMetric [data-testid="stMetricValue"] { color: #22c55e !important; font-size: 1.5rem !important; }
    h1, h2, h3, h4 { color: #f1f5f9 !important; }
    p, span, label { color: #e2e8f0; }
    .result-title { color: #60a5fa; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; }
    .info-box { background-color: #1e3a5f; border-left: 4px solid #3b82f6; padding: 0.75rem; border-radius: 0 8px 8px 0; color: #e2e8f0; }
    [data-testid="stSidebarContent"] { padding: 1rem; }
    .coord-display { font-family: monospace; background: #334155; padding: 0.5rem; border-radius: 6px; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)


def query_point(lat: float, lon: float) -> dict:
    """Query API for point value."""
    try:
        response = requests.get(f"{API_URL}/land-value", params={"lat": lat, "lon": lon}, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def query_polygon(coordinates: list) -> dict:
    """Query API for polygon values."""
    try:
        response = requests.post(f"{API_URL}/land-value/polygon", json={"coordinates": coordinates}, timeout=60)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def create_map_point(marker_lat: float = None, marker_lon: float = None) -> folium.Map:
    """Create map for point mode."""
    m = folium.Map(location=[CENTER["lat"], CENTER["lon"]], zoom_start=12, tiles="CartoDB dark_matter")
    
    # Add marker if position set (NOT draggable)
    if marker_lat is not None and marker_lon is not None:
        folium.Marker(
            location=[marker_lat, marker_lon],
            icon=folium.Icon(color="blue", icon="map-marker", prefix="fa"),
            draggable=False,
            tooltip=f"Lat: {marker_lat:.4f}, Lon: {marker_lon:.4f}"
        ).add_to(m)
    
    return m


def create_map_polygon() -> folium.Map:
    """Create map for polygon mode."""
    m = folium.Map(location=[CENTER["lat"], CENTER["lon"]], zoom_start=11, tiles="CartoDB dark_matter")
    
    Draw(
        export=False,
        draw_options={
            "polyline": False,
            "polygon": {"shapeOptions": {"color": "#22c55e", "fillOpacity": 0.3}},
            "rectangle": {"shapeOptions": {"color": "#22c55e", "fillOpacity": 0.3}},
            "circle": False, "circlemarker": False, "marker": False
        },
        edit_options={"edit": True, "remove": True}
    ).add_to(m)
    
    return m


def main():
    # Session state init
    if "point_lat" not in st.session_state:
        st.session_state.point_lat = None
    if "point_lon" not in st.session_state:
        st.session_state.point_lon = None
    if "point_result" not in st.session_state:
        st.session_state.point_result = None
    
    # Sidebar
    with st.sidebar:
        st.title("🗺️ Land Value Insight")
        st.markdown("---")
        
        mode = st.radio(
            "Select Mode", options=["point", "polygon"],
            format_func=lambda x: "📍 Point" if x == "point" else "⬡ Polygon",
            horizontal=True
        )
        
        st.markdown("---")
        st.subheader("📖 Instructions")
        
        if mode == "point":
            st.info("👆 **Click anywhere** on the map to query that location. Click again to move marker.", icon="ℹ️")
            
            st.markdown("---")
            st.subheader("📍 Coordinates")
            
            # Display current coordinates
            if st.session_state.point_lat is not None:
                st.markdown(f"""
                <div class="coord-display">
                    Lat: {st.session_state.point_lat:.6f}<br>
                    Lon: {st.session_state.point_lon:.6f}
                </div>
                """, unsafe_allow_html=True)
            
            # Manual input
            with st.expander("📝 Manual Input", expanded=st.session_state.point_lat is None):
                input_lat = st.number_input("Latitude", value=-6.2, format="%.6f", step=0.001)
                input_lon = st.number_input("Longitude", value=106.8, format="%.6f", step=0.001)
                
                if st.button("🔍 Query", use_container_width=True, type="primary"):
                    st.session_state.point_lat = input_lat
                    st.session_state.point_lon = input_lon
                    st.session_state.point_result = query_point(input_lat, input_lon)
                    st.rerun()
        else:
            st.info("✏️ Use polygon/rectangle tools on map.", icon="ℹ️")
        
        st.markdown("---")
        st.markdown(f"[📚 API Docs]({API_URL}/docs)")
    
    # Main content
    col_map, col_result = st.columns([3, 1])
    
    with col_map:
        if mode == "point":
            m = create_map_point(st.session_state.point_lat, st.session_state.point_lon)
            map_data = st_folium(m, width=None, height=700, key="map_point", returned_objects=["last_clicked", "last_object_clicked"])
            
            # Handle click OR marker drag
            new_pos = None
            
            # Check for marker drag (last_object_clicked contains marker position)
            if map_data.get("last_object_clicked"):
                obj = map_data["last_object_clicked"]
                if isinstance(obj, dict) and "lat" in obj:
                    new_pos = {"lat": obj["lat"], "lng": obj["lng"]}
            
            # Check for map click
            if map_data.get("last_clicked"):
                click = map_data["last_clicked"]
                if click:
                    new_pos = click
            
            # Update if position changed
            if new_pos:
                new_lat = round(new_pos["lat"], 6)
                new_lon = round(new_pos["lng"], 6)
                
                if new_lat != st.session_state.point_lat or new_lon != st.session_state.point_lon:
                    st.session_state.point_lat = new_lat
                    st.session_state.point_lon = new_lon
                    st.session_state.point_result = query_point(new_lat, new_lon)
                    st.rerun()
        
        else:  # Polygon mode
            m = create_map_polygon()
            map_data = st_folium(m, width=None, height=700, key="map_polygon")
    
    with col_result:
        st.subheader("📊 Results")
        
        if mode == "point":
            if st.session_state.point_result:
                display_point_result(st.session_state.point_result)
            else:
                st.markdown('<div class="info-box">Click on the map to query land value.</div>', unsafe_allow_html=True)
        
        else:  # Polygon
            if map_data and map_data.get("all_drawings"):
                drawings = map_data["all_drawings"]
                if drawings:
                    last = drawings[-1]
                    geom = last.get("geometry", {})
                    if geom.get("type") in ["Polygon", "Rectangle"]:
                        coords = geom["coordinates"][0]
                        if len(coords) >= 4:
                            with st.spinner("Calculating..."):
                                result = query_polygon(coords)
                            display_polygon_result(result)
                            return
            
            st.markdown('<div class="info-box">Draw polygon on map.</div>', unsafe_allow_html=True)


def display_point_result(result: dict):
    """Display point result."""
    if "error" in result or "detail" in result:
        error_msg = result.get("error") or result.get("detail", "Unknown")
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("error", str(error_msg))
        # Simplify error message
        if "outside" in str(error_msg).lower() or "coverage" in str(error_msg).lower():
            st.warning("⚠️ Outside coverage area")
        else:
            st.error(f"❌ {error_msg}")
    else:
        st.markdown('<div class="result-title">📍 Point Result</div>', unsafe_allow_html=True)
        st.code(result.get('gid', 'N/A'), language=None)
        st.caption(f"Level {result.get('level', 'N/A')} | {result.get('source', '')}")
        
        value = result.get("value")
        if value is not None:
            st.metric("Land Value", f"{value:.4f}")
        else:
            st.warning("⚠️ No data")


def display_polygon_result(result: dict):
    """Display polygon result - simplified."""
    if "error" in result or "detail" in result:
        st.error(f"❌ {result.get('error') or result.get('detail', 'Unknown')}")
    else:
        st.markdown('<div class="result-title">⬡ Polygon Result</div>', unsafe_allow_html=True)
        
        # Just Area and Land Value - simplified
        st.metric("Area", f"{result.get('area_km2', 0):.2f} km²")
        
        avg = result.get("avg_value")
        if avg is not None:
            st.metric("Land Value", f"{avg:.4f}")
        else:
            st.warning("⚠️ No data in area")


if __name__ == "__main__":
    main()
