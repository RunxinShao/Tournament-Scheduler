import streamlit as st
import math
import random
from typing import List, Dict, Tuple
import pandas as pd

# Import functions from the main module
from tounrney_starter import (
    generate_teams,
    distance_matrix,
    round_robin_pairs,
    evaluate_schedule_travel,
    greedy_optimize_tours
)

st.set_page_config(page_title="Tournament Scheduler", page_icon="🏆", layout="wide")

st.title("🏆 Tournament Scheduler")
st.markdown("Generate and optimize round-robin tournament schedules to minimize travel distance")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    num_teams = st.number_input("Number of Teams", min_value=2, max_value=20, value=6, step=1)
    
    st.subheader("Location Settings")
    center_lat = st.number_input("Center Latitude", value=37.7749, format="%.4f")
    center_lon = st.number_input("Center Longitude", value=-122.4194, format="%.4f")
    spread_km = st.slider("Spread (km)", min_value=5, max_value=100, value=20)
    
    seed = st.number_input("Random Seed", min_value=0, value=42, step=1)
    
    optimize = st.checkbox("Enable Optimization", value=True)
    
    if st.button("🔄 Generate Schedule", type="primary"):
        st.session_state.generate = True

# Main content
if 'generate' not in st.session_state:
    st.session_state.generate = False

if st.session_state.generate:
    # Generate teams and schedule
    random.seed(seed)
    teams = generate_teams(num_teams, (center_lat, center_lon), spread_km)
    D = distance_matrix(teams)
    rounds = round_robin_pairs(teams)
    
    # Evaluate baseline travel
    per_team, total = evaluate_schedule_travel(rounds, teams, D)
    
    # Display teams
    st.header("📍 Teams")
    teams_df = pd.DataFrame(teams)
    teams_df = teams_df.rename(columns={'id': 'ID', 'name': 'Team Name', 'lat': 'Latitude', 'lon': 'Longitude'})
    st.dataframe(teams_df, use_container_width=True)
    
    # Display schedule
    st.header("📅 Schedule")
    
    schedule_data = []
    for r_idx, rnd in enumerate(rounds):
        for home_id, away_id in rnd:
            schedule_data.append({
                'Round': r_idx + 1,
                'Home Team': teams[home_id]['name'],
                'Away Team': teams[away_id]['name']
            })
    
    schedule_df = pd.DataFrame(schedule_data)
    st.dataframe(schedule_df, use_container_width=True)
    
    # Display travel statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Travel Statistics (Baseline)")
        travel_data = []
        for t, km in enumerate(per_team):
            travel_data.append({
                'Team': teams[t]['name'],
                'Travel Distance (km)': f"{km:.2f}"
            })
        travel_df = pd.DataFrame(travel_data)
        st.dataframe(travel_df, use_container_width=True)
        st.metric("Total Travel Distance", f"{total:.2f} km")
    
    # Optimization
    if optimize:
        with col2:
            st.subheader("⚡ Optimization Results")
            rounds_optimized, improved = greedy_optimize_tours(rounds, D)
            per_team_opt, total_opt = evaluate_schedule_travel(rounds_optimized, teams, D)
            
            if improved:
                st.success("✅ Improvement found!")
                travel_opt_data = []
                for t, km in enumerate(per_team_opt):
                    travel_opt_data.append({
                        'Team': teams[t]['name'],
                        'Travel Distance (km)': f"{km:.2f}"
                    })
                travel_opt_df = pd.DataFrame(travel_opt_data)
                st.dataframe(travel_opt_df, use_container_width=True)
                st.metric("Total Travel Distance", f"{total_opt:.2f} km", 
                         delta=f"{total_opt - total:.2f} km")
                
                # Show optimized schedule
                with st.expander("View Optimized Schedule"):
                    opt_schedule_data = []
                    for r_idx, rnd in enumerate(rounds_optimized):
                        for home_id, away_id in rnd:
                            opt_schedule_data.append({
                                'Round': r_idx + 1,
                                'Home Team': teams[home_id]['name'],
                                'Away Team': teams[away_id]['name']
                            })
                    opt_schedule_df = pd.DataFrame(opt_schedule_data)
                    st.dataframe(opt_schedule_df, use_container_width=True)
            else:
                st.info("ℹ️ No improvement found with current heuristic")
                st.metric("Total Travel Distance", f"{total:.2f} km")
    
    # Distance matrix visualization
    with st.expander("📐 Distance Matrix"):
        dist_df = pd.DataFrame(D, 
                              index=[t['name'] for t in teams],
                              columns=[t['name'] for t in teams])
        st.dataframe(dist_df.style.format("{:.2f}"), use_container_width=True)
    
    # Map visualization (if folium is available)
    try:
        import folium
        from streamlit_folium import st_folium
        
        st.header("🗺️ Team Locations Map")
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
        
        for team in teams:
            folium.Marker(
                [team['lat'], team['lon']],
                popup=team['name'],
                tooltip=team['name']
            ).add_to(m)
        
        st_folium(m, width=700, height=500)
    except ImportError:
        st.info("💡 Install folium and streamlit-folium for map visualization: `pip install folium streamlit-folium`")

else:
    st.info("👈 Configure settings in the sidebar and click 'Generate Schedule' to start")

