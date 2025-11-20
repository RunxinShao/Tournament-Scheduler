"""
Visualization utilities for tournament schedules.

Provides functions to create:
- Folium maps showing team locations and travel routes
- Schedule grid/heatmap visualizations

Requires: folium, pandas (optional dependencies)
"""

from typing import List, Dict, Any, Tuple, Optional


def create_team_map(
    teams: List[Dict[str, Any]],
    schedule: List[List[Tuple[int, int]]],
    D: List[List[float]],
    title: str = "Tournament Schedule Map"
) -> Optional[Any]:
    """
    Create an interactive Folium map showing team locations and travel routes.
    
    Args:
        teams: List of team dictionaries with 'lat', 'lon', 'name', 'id'
        schedule: List of rounds with matches
        D: Distance matrix
        title: Map title
        
    Returns:
        Folium Map object, or None if folium is not installed
        
    Requires: folium
    """
    try:
        import folium
    except ImportError:
        print("folium is required for map visualization. Install with: pip install folium")
        return None
    
    # Calculate center of all teams
    center_lat = sum(t['lat'] for t in teams) / len(teams)
    center_lon = sum(t['lon'] for t in teams) / len(teams)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Add team markers
    for team in teams:
        folium.Marker(
            [team['lat'], team['lon']],
            popup=f"{team['name']} (Team {team['id']})",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Add travel routes for a representative team (team 0)
    from tourney_starter import evaluate_schedule_travel
    per_team, total = evaluate_schedule_travel(schedule, teams, D)
    
    # Track team 0's route
    team_id = 0
    current_loc = team_id
    route_points = [[teams[team_id]['lat'], teams[team_id]['lon']]]
    
    for round_matches in schedule:
        next_loc = None
        for home, away in round_matches:
            if home == team_id:
                next_loc = home  # Playing at home
                break
            elif away == team_id:
                next_loc = home  # Playing away at opponent's stadium
                break
        
        if next_loc is None:
            next_loc = current_loc  # Bye or no game
        
        if next_loc != current_loc:
            route_points.append([teams[next_loc]['lat'], teams[next_loc]['lon']])
            folium.PolyLine(
                [[teams[current_loc]['lat'], teams[current_loc]['lon']],
                 [teams[next_loc]['lat'], teams[next_loc]['lon']]],
                color='red',
                weight=3,
                opacity=0.7
            ).add_to(m)
            current_loc = next_loc
    
    # Return home if not already there
    if current_loc != team_id:
        route_points.append([teams[team_id]['lat'], teams[team_id]['lon']])
        folium.PolyLine(
            [[teams[current_loc]['lat'], teams[current_loc]['lon']],
             [teams[team_id]['lat'], teams[team_id]['lon']]],
            color='red',
            weight=3,
            opacity=0.7
        ).add_to(m)
    
    # Add route polyline
    if len(route_points) > 1:
        folium.PolyLine(
            route_points,
            color='green',
            weight=2,
            opacity=0.5,
            popup=f"Team {team_id} route (Total: {per_team[team_id]:.1f} km)"
        ).add_to(m)
    
    # Add title
    title_html = f'<h3 align="center" style="font-size:20px"><b>{title}</b></h3>'
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m


def create_schedule_grid(
    schedule: List[List[Tuple[int, int]]],
    teams: List[Dict[str, Any]],
    output_file: Optional[str] = None
) -> Optional[str]:
    """
    Create a schedule grid visualization showing matches by round.
    
    Args:
        schedule: List of rounds with matches
        teams: List of team dictionaries
        output_file: Optional file path to save HTML output
        
    Returns:
        HTML string representation, or None if pandas is not installed
        
    Requires: pandas (optional, for better formatting)
    """
    try:
        import pandas as pd
    except ImportError:
        # Fallback to simple text representation
        return create_schedule_text(schedule, teams)
    
    # Create grid: rows = rounds, columns = teams
    n_rounds = len(schedule)
    n_teams = len(teams)
    
    # Initialize grid
    grid_data = [['' for _ in range(n_teams)] for _ in range(n_rounds)]
    
    # Fill grid
    for r, round_matches in enumerate(schedule):
        for home, away in round_matches:
            # Mark home team
            grid_data[r][home] = f'H'
            # Mark away team
            grid_data[r][away] = f'@ {home}'
    
    # Create DataFrame
    team_names = [teams[i]['name'] for i in range(n_teams)]
    df = pd.DataFrame(grid_data, columns=team_names, index=[f'Round {i+1}' for i in range(n_rounds)])
    
    # Convert to HTML
    html = df.to_html(classes='table table-striped', table_id='schedule_grid')
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"<html><head><title>Schedule Grid</title></head><body>{html}</body></html>")
        return output_file
    
    return html


def create_schedule_text(
    schedule: List[List[Tuple[int, int]]],
    teams: List[Dict[str, Any]]
) -> str:
    """
    Create a simple text representation of the schedule.
    
    Args:
        schedule: List of rounds with matches
        teams: List of team dictionaries
        
    Returns:
        String representation of schedule
    """
    lines = []
    for r, round_matches in enumerate(schedule):
        lines.append(f"Round {r+1}:")
        for home, away in round_matches:
            lines.append(f"  {teams[home]['name']} vs {teams[away]['name']} (at {teams[home]['name']})")
        lines.append("")
    return "\n".join(lines)


def save_map_html(map_obj: Any, filename: str) -> str:
    """
    Save Folium map to HTML file.
    
    Args:
        map_obj: Folium Map object
        filename: Output filename
        
    Returns:
        Filename if successful
    """
    if map_obj is None:
        return ""
    try:
        map_obj.save(filename)
        return filename
    except Exception as e:
        print(f"Error saving map: {e}")
        return ""

