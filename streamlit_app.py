"""
Interactive Streamlit application for tournament scheduling.

Provides a web interface to:
- Generate teams with configurable parameters
- Run optimizers (baseline, hill-climbing, simulated annealing, exact)
- Visualize schedules on interactive maps
- Compare optimization results
- Export schedules and results
"""

import streamlit as st
import sys
import os
import json
import random
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tourney_starter import generate_teams, distance_matrix, round_robin_pairs, evaluate_schedule_travel
from optimizers import hill_climb, simulated_annealing
from validators import validate_schedule, check_max_consecutive_aways, check_repeaters, check_home_away_balance
from visualize import create_team_map, create_schedule_grid, save_map_html

# Page config
st.set_page_config(
    page_title="Tournament Scheduler",
    page_icon="🏆",
    layout="wide"
)

# Title
st.title("🏆 Tournament Scheduler - Traveling Tournament Problem Solver")
st.markdown("Optimize tournament schedules to minimize team travel while maintaining realistic constraints.")


# Sidebar for inputs
st.sidebar.header("Configuration")

# Team generation parameters
st.sidebar.subheader("Team Generation")
n_teams = st.sidebar.slider("Number of Teams", min_value=4, max_value=20, value=6, step=1)
seed = st.sidebar.number_input("Random Seed", min_value=0, value=42, step=1)

center_lat = st.sidebar.number_input("Center Latitude", value=37.7749, format="%.4f")
center_lon = st.sidebar.number_input("Center Longitude", value=-122.4194, format="%.4f")
spread_km = st.sidebar.slider("Spread (km)", min_value=5.0, max_value=100.0, value=20.0, step=5.0)

# Constraint parameters
st.sidebar.subheader("Constraints")
max_consecutive_aways = st.sidebar.slider("Max Consecutive Away Games", min_value=2, max_value=5, value=3, step=1)

# Optimizer selection
st.sidebar.subheader("Optimizers")
run_baseline = st.sidebar.checkbox("Baseline", value=True)
run_hill_climb = st.sidebar.checkbox("Hill Climbing", value=True)
run_simanneal = st.sidebar.checkbox("Simulated Annealing", value=True)
run_exact = st.sidebar.checkbox("Exact Solver (CP-SAT)", value=False)

# Optimizer parameters
st.sidebar.subheader("Optimizer Parameters")
max_iters_hc = st.sidebar.number_input("Hill Climb Max Iterations", min_value=100, max_value=10000, value=1000, step=100)
max_iters_sa = st.sidebar.number_input("Simulated Annealing Max Iterations", min_value=500, max_value=50000, value=5000, step=500)
sa_t0 = st.sidebar.number_input("SA Initial Temperature", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
sa_decay = st.sidebar.number_input("SA Decay Rate", min_value=0.9, max_value=0.999, value=0.995, step=0.001, format="%.3f")


# Main content
if st.button("Generate Schedule", type="primary"):
    # Set random seed
    random.seed(seed)
    
    # Generate teams
    with st.spinner("Generating teams..."):
        teams = generate_teams(n_teams, center=(center_lat, center_lon), spread_km=spread_km)
        D = distance_matrix(teams)
        schedule = round_robin_pairs(teams)
    
    st.session_state['teams'] = teams
    st.session_state['D'] = D
    st.session_state['schedule'] = schedule
    st.session_state['results'] = {}
    
    # Evaluate baseline
    if run_baseline:
        with st.spinner("Evaluating baseline..."):
            per_team, total = evaluate_schedule_travel(schedule, teams, D)
            n_teams_val = len(teams)
            ok1, _ = validate_schedule(schedule, n_teams_val)
            ok2, _ = check_max_consecutive_aways(schedule, k=max_consecutive_aways)
            ok3, _ = check_repeaters(schedule)
            ok4, _ = check_home_away_balance(schedule, n_teams_val)
            
            st.session_state['results']['baseline'] = {
                'schedule': schedule,
                'per_team': per_team,
                'total': total,
                'valid': ok1 and ok2 and ok3 and ok4,
                'runtime': 0.0
            }
    
    # Run optimizers
    if run_hill_climb:
        with st.spinner("Running Hill Climbing..."):
            best_schedule, best_score, log = hill_climb(
                schedule, teams, D,
                max_iters=max_iters_hc,
                max_no_improve=100,
                validate=True,
                random_seed=seed
            )
            per_team, _ = evaluate_schedule_travel(best_schedule, teams, D)
            st.session_state['results']['hill_climb'] = {
                'schedule': best_schedule,
                'per_team': per_team,
                'total': best_score,
                'valid': True,  # Validated in optimizer
                'runtime': log['time_elapsed'],
                'iterations': log['iter'],
                'improvements': log['improvements']
            }
    
    if run_simanneal:
        with st.spinner("Running Simulated Annealing..."):
            best_schedule, best_score, log = simulated_annealing(
                schedule, teams, D,
                max_iters=max_iters_sa,
                T0=sa_t0,
                decay=sa_decay,
                validate=True,
                random_seed=seed
            )
            per_team, _ = evaluate_schedule_travel(best_schedule, teams, D)
            st.session_state['results']['simanneal'] = {
                'schedule': best_schedule,
                'per_team': per_team,
                'total': best_score,
                'valid': True,
                'runtime': log['time_elapsed'],
                'iterations': log['iter'],
                'improvements': log['improvements']
            }
    
    if run_exact:
        try:
            from exact_solver import solve_exact
            with st.spinner("Running Exact Solver (this may take a while)..."):
                if n_teams > 10:
                    st.warning(f"Exact solver limited to N <= 10. Current N = {n_teams}")
                else:
                    best_schedule, best_score, log = solve_exact(
                        teams, D,
                        max_consecutive_aways=max_consecutive_aways
                    )
                    if best_schedule:
                        per_team, _ = evaluate_schedule_travel(best_schedule, teams, D)
                        st.session_state['results']['exact'] = {
                            'schedule': best_schedule,
                            'per_team': per_team,
                            'total': best_score,
                            'valid': log['solved'],
                            'runtime': log['runtime_s'],
                            'status': log['status']
                        }
        except ImportError:
            st.error("ortools is required for exact solver. Install with: pip install ortools")


# Display results
if 'results' in st.session_state and st.session_state['results']:
    teams = st.session_state['teams']
    D = st.session_state['D']
    
    st.header("Results")
    
    # Comparison table
    st.subheader("Optimization Comparison")
    comparison_data = []
    baseline_total = None
    
    for opt_name, result in st.session_state['results'].items():
        if opt_name == 'baseline':
            baseline_total = result['total']
            comparison_data.append({
                'Optimizer': 'Baseline',
                'Total Travel (km)': f"{result['total']:.2f}",
                'Runtime (s)': f"{result['runtime']:.3f}",
                'Valid': '✓' if result['valid'] else '✗',
                'Improvement': '0.00%'
            })
        else:
            improvement = ((baseline_total - result['total']) / baseline_total * 100) if baseline_total else 0.0
            comparison_data.append({
                'Optimizer': opt_name.replace('_', ' ').title(),
                'Total Travel (km)': f"{result['total']:.2f}",
                'Runtime (s)': f"{result['runtime']:.3f}",
                'Valid': '✓' if result['valid'] else '✗',
                'Improvement': f"{improvement:.2f}%"
            })
    
    import pandas as pd
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True)
    
    # Select optimizer for visualization
    st.subheader("Visualization")
    opt_names = list(st.session_state['results'].keys())
    selected_opt = st.selectbox("Select optimizer to visualize", opt_names, format_func=lambda x: x.replace('_', ' ').title())
    
    if selected_opt in st.session_state['results']:
        result = st.session_state['results'][selected_opt]
        schedule = result['schedule']
        
        # Create two columns for map and stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Interactive Map")
            map_obj = create_team_map(teams, schedule, D, title=f"{selected_opt.replace('_', ' ').title()} Schedule")
            if map_obj:
                st.components.v1.html(map_obj._repr_html_(), height=500)
            else:
                st.info("Install folium to view map: pip install folium")
        
        with col2:
            st.markdown("### Travel Statistics")
            st.metric("Total Travel", f"{result['total']:.2f} km")
            if 'improvement' in result:
                st.metric("Improvement", f"{result['improvement']:.2f}%")
            if 'iterations' in result:
                st.metric("Iterations", result['iterations'])
            if 'runtime' in result:
                st.metric("Runtime", f"{result['runtime']:.3f} s")
            
            st.markdown("### Per-Team Travel")
            per_team_data = {
                teams[i]['name']: result['per_team'][i] for i in range(len(teams))
            }
            df_teams = pd.DataFrame(list(per_team_data.items()), columns=['Team', 'Travel (km)'])
            st.dataframe(df_teams, use_container_width=True)
        
        # Schedule grid
        st.subheader("Schedule Grid")
        schedule_html = create_schedule_grid(schedule, teams)
        if schedule_html:
            st.components.v1.html(schedule_html, height=400, scrolling=True)
        else:
            st.text(create_schedule_grid(schedule, teams) if hasattr(create_schedule_grid, '__call__') else "Schedule visualization not available")
        
        # Export options
        st.subheader("Export")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export schedule as JSON
            schedule_json = json.dumps({
                'teams': teams,
                'schedule': schedule,
                'total_travel': result['total'],
                'per_team_travel': result['per_team']
            }, indent=2)
            st.download_button(
                label="Download Schedule (JSON)",
                data=schedule_json,
                file_name=f"schedule_{selected_opt}_{seed}.json",
                mime="application/json"
            )
        
        with col2:
            # Export map as HTML
            if map_obj:
                map_filename = f"map_{selected_opt}_{seed}.html"
                save_map_html(map_obj, map_filename)
                if os.path.exists(map_filename):
                    with open(map_filename, 'rb') as f:
                        st.download_button(
                            label="Download Map (HTML)",
                            data=f.read(),
                            file_name=map_filename,
                            mime="text/html"
                        )
        
        with col3:
            # Export comparison as CSV
            csv_data = df_comparison.to_csv(index=False)
            st.download_button(
                label="Download Comparison (CSV)",
                data=csv_data,
                file_name=f"comparison_{seed}.csv",
                mime="text/csv"
            )

else:
    st.info("👈 Configure parameters in the sidebar and click 'Generate Schedule' to begin.")

# Footer
st.markdown("---")
st.markdown("**Tournament Scheduler** - CS 5800 Algorithms Project")
st.markdown("Implements Traveling Tournament Problem (TTP) with constraint satisfaction and optimization algorithms.")

