# ...existing code...

# (Move run command to end of file)
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Output, Input, State
from layout import sidebar, spring_layout
from Football import *
from SpringFootball import *

# Color variables
WM_GREEN = "#006341"
WM_GOLD = "#FFC72C"
WM_DARK_BG = "#0B2F1A"

# Normalize concept strings (trim + uppercase) for robust filtering
def _norm(s):
	# Safe normalization
	try:
		return str(s).strip().upper()
	except Exception:
		return ""

# Helper: main concept mask supports "MAIN", "MAIN/", and "MAIN " prefixes
def _main_concept_mask(series, main):
    conc = series.astype(str).str.strip().str.upper()
    mc = _norm(main)
    return (conc == mc) | conc.str.startswith(mc + '/', na=False) | conc.str.startswith(mc + ' ', na=False)

# Load William & Mary data for WM_data_df
try:
    from Football import WM_data_df
except ImportError:
    import pandas as pd
    WM_data_df = pd.read_csv('RU_data.csv')

# Create Dash app instance (must exist before any @app.callback decorators)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Base layout placeholders: ensure `app.layout` is not None when server starts.
# The callbacks in this file populate `sidebar-container`, `sidebar-open-btn`, and
# `page-content-container` based on the URL and sidebar state.
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='sidebar-state', data=True),
    html.Div(id='sidebar-container'),
    html.Div(id='sidebar-open-btn'),
    html.Div(id='page-content-container')
])


# Richmond dashboard layout (clean, balanced)
def richmond_layout():
    # Header: logo placed directly next to the centered title for the Richmond page
    header = html.Div([
        html.Div([
            html.Img(src="/assets/wm_football_logo.png", style={"height": "60px", "marginRight": "12px", "verticalAlign": "middle", "boxShadow": "0 2px 8px #FFC72C", "borderRadius": "8px"}),
            html.H2("Offensive Concept Analysis", style={
                "color": WM_GOLD,
                "fontFamily": "Georgia, serif",
                "margin": 0,
                "paddingLeft": "6px",
                "letterSpacing": "2px"
            })
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "background": WM_DARK_BG, "padding": "12px 18px", "borderRadius": "12px", "boxShadow": "0 2px 12px #FFC72C"})
    ], style={"display": "flex", "justifyContent": "center", "marginBottom": "8px"})

    # Top row: graph (left) and OVO results table (right)
    # Graph column: put graph inside a green padded box so the graph is centered in its own box
    graph_col = dbc.Col([
        html.Div(
            html.Div(
                dcc.Graph(id="play-graph", style={
                    "height": "440px",
                    "width": "100%",
                    "borderRadius": "8px",
                    "boxShadow": "0 6px 20px rgba(0,0,0,0.08)"
                }),
                style={"backgroundColor": "white", "padding": "6px", "borderRadius": "6px", "height": "100%"}
            ),
            style={"backgroundColor": WM_GREEN, "padding": "8px", "borderRadius": "10px", "border": f"4px solid {WM_GOLD}", "display": "flex", "alignItems": "center", "justifyContent": "center", "height": "100%"}
        )
    ], width=8, style={"padding": "12px", "minHeight": "520px"})

    ovo_table_col = dbc.Col([
        html.Div(id="table-output", style={
            "backgroundColor": "#FFF",
            "color": WM_GOLD,
            "border": f"2px solid {WM_GOLD}",
            "borderRadius": "12px",
            "padding": "12px",
            "boxShadow": "0 2px 8px #FFC72C",
            "maxHeight": "520px",
            "overflowY": "auto",
            "height": "100%",
        })
    ], width=4, style={"padding": "12px"})

    # Top row: graph box (left) and OVO results table (right)
    top_row = dbc.Row([graph_col, ovo_table_col], align="start", style={"marginBottom": "8px"})

    # Bottom row: dropdowns (left, narrower) and dataframe (right)
    # Bring dropdowns up so they sit directly beneath the graph area and take less vertical space
    dropdowns_col = dbc.Col([
        html.Div([
            dcc.Dropdown(id="down-dropdown", placeholder="Select Down", clearable=True, style={"marginTop": "6px", "width": "240px"}),
            dcc.Dropdown(id="distance-dropdown", placeholder="Select Distance", clearable=True, style={"marginTop": "6px", "width": "240px"}),
            dcc.Dropdown(id="main-concept-dropdown", placeholder="Select Main Concept", clearable=True, style={"marginTop": "6px", "width": "240px"}),
            dcc.Dropdown(id="tag-dropdown", placeholder="Select Tag", clearable=True, style={"marginTop": "6px", "width": "240px"}),
            dcc.Dropdown(id="filter-dropdown", placeholder="Filter Plays", clearable=True, style={"marginTop": "6px", "width": "240px"}),

            # Stacked percentage cards (Tendency / Efficiency / Explosiveness)
            html.Div([
                dbc.Card([dbc.CardBody([html.H6("Tendency", className="text-center"), html.H3(id='tendency-value', className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": f"2px solid #006341", "marginBottom": "8px"}),
                dbc.Card([dbc.CardBody([html.H6("Efficiency %", className="text-center"), html.H3(id='efficiency-value', className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": f"2px solid #006341", "marginBottom": "8px"}),
                dbc.Card([dbc.CardBody([html.H6("Explosiveness %", className="text-center"), html.H3(id='explosive-value', className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": f"2px solid #006341", "marginBottom": "8px"})
            ], style={"marginTop": "12px", "width": "100%"})

        ], style={"marginTop": "6px", "textAlign": "left", "paddingLeft": "18px"})
    ], width=4, style={"padding": "12px", "paddingLeft": "24px"})

    dataframe_col = dbc.Col([
        html.Div(id="dataframe-output", style={
            "backgroundColor": "#FFF",
            "color": WM_GOLD,
            "border": f"2px solid {WM_GOLD}",
            "borderRadius": "12px",
            "padding": "12px",
            "boxShadow": "0 2px 8px #FFC72C",
            # Give the dataframe area more room so the DataTable can render visibly
            "minHeight": "420px",
            "height": "520px",
            "overflowY": "auto",
            "width": "100%",
        })
    ], width=8, style={"padding": "18px"})

    bottom_row = dbc.Row([dropdowns_col, dataframe_col], style={"alignItems": "flex-start"})

    # Coverage vs Play selector row (side-by-side dropdowns) and results table below
    # Title and coverage/play selector row
    title_row = dbc.Row([
        dbc.Col(html.H4("Defensive Coverage Breakdowns", style={"color": WM_GREEN, "textAlign": "center", "marginTop": "8px", "marginBottom": "12px", "fontWeight": "bold", "fontSize": "28px"}), width=12)
    ], style={"marginTop": "8px"})

    coverage_play_row = dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='coverage-dropdown', placeholder='Select Defensive Coverage', clearable=True, style={'width': '100%'}),
        ], width=6, style={'padding': '6px 18px'}),
        dbc.Col([
            dcc.Dropdown(id='play-dropdown', placeholder='Select Offensive Play (OVO CONCEPT)', clearable=True, style={'width': '100%'}),
        ], width=6, style={'padding': '6px 18px'})
    ], style={'marginTop': '8px'})

    # Results container: yellow background by default; when a table is returned it will be white inside
    coverage_table_col = dbc.Row([
        dbc.Col([
            # Yellow holder: empty until a white table card is returned by the callback
            html.Div(id='coverage-play-table-output', style={
                'backgroundColor': WM_GOLD,
                'border': f'2px solid {WM_GOLD}',
                'borderRadius': '10px',
                'padding': '18px',
                'boxShadow': '0 2px 8px #FFC72C',
                'minHeight': '220px',
                'overflowY': 'auto'
            })
        ], width=12)
    ], style={'marginTop': '8px'})

    # Move the green footer bar above the dropdowns per user request
    footer_bar = html.Div(style={"height": "24px", "backgroundColor": WM_GREEN, "borderBottom": f"4px solid {WM_GOLD}", "borderTop": f"4px solid {WM_GOLD}", "marginTop": "18px"})

    # Add spacing to separate offensive breakdown (above) from defensive section
    spacer_between = html.Div(style={'height': '26px'})

    # Yellow container that stretches up behind the title and contains the defensive dropdowns + results
    yellow_container = html.Div([title_row, coverage_play_row, coverage_table_col], style={
        'backgroundColor': WM_GOLD,
        'paddingTop': '24px',
        'paddingBottom': '36px',
        'paddingLeft': '14px',
        'paddingRight': '14px',
        'borderRadius': '10px',
        'marginTop': '8px',
        'minHeight': '420px'
    })

    main_row = html.Div([top_row, footer_bar, bottom_row, spacer_between, yellow_container])

    return html.Div([header, main_row], style={"maxWidth": "1280px", "margin": "0 auto", "padding": "8px"})

@app.callback(
    Output('player-totals-table-wm', 'children'),
    Output('efficiency-box-wm', 'children'),
    Output('explosiveness-box-wm', 'children'),
    Output('top3-concepts-table-wm', 'children'),
    Output('player-plays-table-wm', 'children'),
    Input('position-dropdown-wm', 'value'),
    Input('player-dropdown-wm', 'value')
)
def update_player_stats(position, player):
    import pandas as pd
    df = WM_clean.copy()

    # Ensure jersey / QB numeric and trim R/P
    for col in ["JERSEY #", "QB"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "R/P" in df.columns:
        df["R/P"] = df["R/P"].astype(str).str.strip()

    # Extract digits from "JERSEY #" into numeric helper column used for matching
    if "JERSEY #" in df.columns:
        jersey_digits = df["JERSEY #"].astype(str).str.extract(r'(\d+)')[0]
        df["JERSEY_NUM"] = pd.to_numeric(jersey_digits, errors="coerce")
    else:
        df["JERSEY_NUM"] = pd.NA

    # Helper to normalize dropdown names (e.g., 'Garrett_Robertson' -> 'Garrett Robertson')
    def _normalize_player_key(s: str) -> str:
        s = str(s or "").strip().replace("_", " ")
        return " ".join(s.split())

    # Known jersey map (include explicit alias)
    jersey_map = {
        "Damian Harris": 4, "Tyler Hughes": 6, "Noah Brannock": 8, "Joey Tomasso": 17,
        "Carson Jenkins": 14, "Derrick Gurley": 15, "George White": 16, "Leonte Oulahi": 13,
        "Isaiah Lemmond": 18, "Jor'dyn Whitelaw": 26, "Jack Zamer": 30, "Jack Reuter": 31,
        "Josh Miller": 33, "Quinn Devlin": 37, "Tyson Garrett": 41, "Armon Wright": 80,
        "Garrett Robertson": 81, "Garret Robertson": 81,  # alias: common single-t typo maps to 81
        "Jack Baumgartner": 82, "Nasir Mahmoud": 83, "Joseph Johnson": 84, "Trey McDonald": 85,
        "Jackson Blee": 86, "Sean McElwain": 87, "Owen Copeland": 88, "Haven Mullins": 89
    }

    # Robust jersey resolver: direct, case-insensitive, then fuzzy match
    def _resolve_jersey(name_raw: str):
        import difflib
        name = _normalize_player_key(name_raw)
        # direct/alias match
        num = jersey_map.get(name)
        if num is not None:
            return num
        # case-insensitive match
        lower = name.lower()
        for k, v in jersey_map.items():
            if k.lower() == lower:
                return v
        # fuzzy match for minor typos
        candidates = list(jersey_map.keys())
        match = difflib.get_close_matches(name, candidates, n=1, cutoff=0.85)
        if match:
            return jersey_map.get(match[0])
        return None

    # Normalize incoming player value and strip optional "(...)" suffix
    player = str(player)
    if '(' in player:
        name = player.split(' (')[0]
    else:
        name = player
    name = _normalize_player_key(name)

    # Use numeric helper JERSEY_NUM for comparisons
    if position == "QB":
        jersey = _resolve_jersey(name)
        df_player = df[(df["QB"] == jersey) & ((df["R/P"] == "P") | ((df["R/P"] == "R") & (df["JERSEY_NUM"] == jersey)))]
    elif position == "RB":
        jersey = _resolve_jersey(name)
        df_player = df[df["JERSEY_NUM"] == jersey]
    elif position == "WR_TE":
        jersey = _resolve_jersey(name)
        # Special case for Leonte Oulahi: always use #13
        if name.lower() == "leonte oulahi":
            df_player = df[df["JERSEY_NUM"] == 13]
        else:
            df_player = df[df["JERSEY_NUM"] == jersey]
    else:
        df_player = pd.DataFrame()
    # Fallback: if no data, show message
    if df_player.empty:
        # Show empty tables/cards if no data found
        empty_table = dash_table.DataTable(
            data=[],
            columns=[{"name": "OVO RESULT", "id": "OVO RESULT"}, {"name": "Count", "id": "Count"}],
            page_size=5,
            style_table={"width": "100%", "marginBottom": "10px"},
            style_cell={"fontSize": "14px", "padding": "6px", "textAlign": "center"}
        )
        eff_box = dbc.Card([dbc.CardBody([html.H6("Efficiency %", className="text-center"), html.H4("–", className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": "2px solid #006341"})
        exp_box = dbc.Card([dbc.CardBody([html.H6("Explosiveness %", className="text-center"), html.H4("–", className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": "2px solid #006341"})
        empty_concept_table = dash_table.DataTable(
            data=[],
            columns=[{"name": "OVO CONCEPT", "id": "OVO CONCEPT"}, {"name": "Plays", "id": "Plays"}, {"name": "Efficiency", "id": "Efficiency"}, {"name": "Explosiveness", "id": "Explosiveness"}],
            page_size=3,
            style_table={"width": "100%", "marginBottom": "10px"},
            style_cell={"fontSize": "14px", "padding": "6px", "textAlign": "center"}
        )
        # Always show the plays table with all columns, but no data
        empty_plays_table = dash_table.DataTable(
            data=[],
            columns=[{"name": c, "id": c} for c in WM_data_df.columns],
            page_size=10,
            style_table={"width": "100%", "marginBottom": "10px", "maxHeight": "350px", "overflowY": "auto"},
            style_cell={"fontSize": "13px", "padding": "5px", "textAlign": "center"}
        )
        return empty_table, eff_box, exp_box, empty_concept_table, empty_plays_table
    # Totals table for OVO RESULT (max 5 rows per page)
    ovo_counts = df_player["OVO RESULT"].value_counts().reset_index()
    ovo_counts.columns = ["OVO RESULT", "Count"]
    totals_table = dash_table.DataTable(
        data=ovo_counts.to_dict('records'),
        columns=[{"name": c, "id": c} for c in ovo_counts.columns],
        page_size=5,
        style_table={"width": "100%", "marginBottom": "10px"},
        style_cell={"fontSize": "14px", "padding": "6px", "textAlign": "center"}
    )
    # Efficiency and Explosiveness boxes
    eff_pct = f"{df_player['Efficient'].mean()*100:.1f}%" if not df_player.empty else "–"
    exp_pct = f"{df_player['Explosive'].mean()*100:.1f}%" if not df_player.empty else "–"
    eff_box = dbc.Card([dbc.CardBody([html.H6("Efficiency %", className="text-center"), html.H4(eff_pct, className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": "2px solid #006341"})
    exp_box = dbc.Card([dbc.CardBody([html.H6("Explosiveness %", className="text-center"), html.H4(exp_pct, className="text-center")])], style={"backgroundColor": "#FFF8E1", "border": "2px solid #006341"})
    # Top 5 concepts table (show top 5 by play count)
    concept_stats = df_player.groupby("OVO CONCEPT").agg(
        Plays=("OVO CONCEPT", "count"),
        Efficiency=("Efficient", "mean"),
        Explosiveness=("Explosive", "mean")
    ).reset_index()
    concept_stats["Efficiency"] = (concept_stats["Efficiency"] * 100).round(2)
    concept_stats["Explosiveness"] = (concept_stats["Explosiveness"] * 100).round(2)
    # Show top 5 by play count
    top5 = concept_stats.sort_values(by=["Plays"], ascending=False).head(5)
    top5_table = dash_table.DataTable(
        data=top5.to_dict('records'),
        columns=[{"name": c, "id": c} for c in top5.columns],
        page_size=5,
        style_table={"width": "100%", "marginBottom": "10px"},
        style_cell={"fontSize": "14px", "padding": "6px", "textAlign": "center"}
    )
    # All plays table (after filtering and dropping image-like columns)
    df_for_table = df_player.copy()
    # Drop any column that contains image filenames, asset paths, or raw <img> HTML
    img_like_patterns = [r"<img", r"\.webp", r"/assets/", r"\.jpg", r"data:image/"]
    cols_to_drop = []
    for col in df_for_table.columns:
        try:
            as_str = df_for_table[col].astype(str)
            if any(as_str.str.contains(pat, na=False).any() for pat in img_like_patterns):
                cols_to_drop.append(col)
        except Exception:
            # If conversion fails, be conservative and skip dropping
            continue
    if cols_to_drop:
        df_for_table = df_for_table.drop(columns=cols_to_drop)
    # Group rows together by OVO RESULT for easier review:
    # collapse families like R* and C* so they render contiguously, then stable sort
    if 'OVO RESULT' in df_for_table.columns:
        def _group_result(series: pd.Series) -> pd.Series:
            s = series.astype(str).str.strip().str.upper()
            # Collapse families: any string starting with 'R' -> 'R'; starting with 'C' -> 'C'
            s = s.str.replace(r'^\s*R.*$', 'R', regex=True)
            s = s.str.replace(r'^\s*C.*$', 'C', regex=True)
            return s
        df_for_table['__RES_G__'] = _group_result(df_for_table['OVO RESULT'])
        by_cols = ['__RES_G__', 'OVO RESULT'] + (['OVO CONCEPT'] if 'OVO CONCEPT' in df_for_table.columns else [])
        df_for_table = df_for_table.sort_values(
            by=by_cols,
            key=lambda s: s.astype(str).str.strip().str.upper(),
            kind='mergesort'
        ).drop(columns='__RES_G__')

    plays_table = dash_table.DataTable(
        data=df_for_table.to_dict('records'),
        columns=[{"name": c, "id": c} for c in df_for_table.columns],
        page_size=10,
        style_table={"width": "100%", "marginBottom": "10px", "maxHeight": "350px", "overflowY": "auto"},
        style_cell={"fontSize": "13px", "padding": "5px", "textAlign": "center"}
    )
    return totals_table, eff_box, exp_box, top5_table, plays_table


# Callback to show/hide sidebar

# Callback to populate player-dropdown-wm options
@app.callback(
    Output('player-dropdown-wm', 'options'),
    Input('position-dropdown-wm', 'value')
)
def update_player_dropdown_options(position):
    # Use the player list from the assets folder (photo filenames)
    import os
    base_path = os.path.join(os.path.dirname(__file__), 'assets', 'Players Photos')
    if not position:
        return []
    position_folder = position if position != 'WR_TE' else 'WR_TE'
    folder_path = os.path.join(base_path, position_folder)
    if not os.path.exists(folder_path):
        return []
    # List .webp files and strip extension
    players = [f[:-5] for f in os.listdir(folder_path) if f.endswith('.webp')]
    # Sort alphabetically
    players.sort()
    return [{'label': name, 'value': name} for name in players]

# Callback for sidebar close button and open button
@app.callback(
    Output('sidebar-state', 'data'),
    Input('sidebar-close', 'n_clicks'),
    Input('sidebar-open', 'n_clicks'),
    State('sidebar-state', 'data')
)
def toggle_sidebar(n_close, n_open, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'sidebar-close' and n_close:
        return False
    if trigger == 'sidebar-open' and n_open:
        return True
    return is_open


# Callback to render sidebar, open button, and page content
@app.callback(
    Output('sidebar-container', 'children'),
    Output('sidebar-open-btn', 'children'),
    Output('page-content-container', 'children'),
    Input('sidebar-state', 'data'),
    Input('url', 'pathname')
)
def render_sidebar_and_content(is_open, pathname):
    from layout import sidebar, spring_layout
    sidebar_component = sidebar(is_open)
    open_btn_style = {
        "fontSize": "28px", "color": "#FFC72C", "background": "#23272A", "border": "2px solid #FFC72C", "borderRadius": "8px", "width": "44px", "height": "44px", "boxShadow": "0 0 8px #23272A", "cursor": "pointer", "position": "fixed", "top": "18px", "left": "18px", "zIndex": 4000,
        "display": "none" if is_open else "block"
    }
    open_btn = html.Button(
        html.Div([
            html.Div(style={"height": "4px", "width": "24px", "background": "#FFC72C", "margin": "2px auto", "borderRadius": "2px"}),
            html.Div(style={"height": "4px", "width": "24px", "background": "#FFC72C", "margin": "2px auto", "borderRadius": "2px"}),
            html.Div(style={"height": "4px", "width": "24px", "background": "#FFC72C", "margin": "2px auto", "borderRadius": "2px"})
        ], style={"display": "flex", "flexDirection": "column", "justifyContent": "center", "alignItems": "center", "height": "100%"}),
        id="sidebar-open",
        style=open_btn_style
    )
    if pathname in [None, '/', '/wm']:
        content = spring_layout()
    elif pathname == '/richmond':
        content = richmond_layout()
    else:
        content = spring_layout()
    return sidebar_component, open_btn, html.Div(content, id='page-content')

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname in [None, '/', '/wm']:
        return spring_layout()
    elif pathname == '/richmond':
        return richmond_layout()
    else:
        return spring_layout()

@app.callback(
    Output("tag-dropdown", "options"),
    Output("tag-dropdown", "value"),
    Input("main-concept-dropdown", "value"),
    Input("down-dropdown", "value"),
    Input("tag-dropdown", "value"),
)
def update_tag_options(main_concept, down, current_tag):
    if not main_concept:
        return [], None
    df = data_sources.get(down)
    if df is None or df.empty:
        df = pd.concat(data_sources.values(), ignore_index=True)
    concepts = df["OVO CONCEPT"].dropna().astype(str).unique()
    mc_norm = _norm(main_concept)
    # Allow "MAIN/" and "MAIN " (space) tag prefixes
    tags = sorted([
        c for c in concepts
        if _norm(c).startswith(mc_norm + '/') or _norm(c).startswith(mc_norm + ' ')
    ])
    options = [{"label": tag, "value": tag} for tag in tags]
    if current_tag not in tags:
        current_tag = None
    return options, current_tag

# ...existing code...

@app.callback(
    Output('tendency-value', 'children'),
    Output('efficiency-value', 'children'),
    Output('explosive-value', 'children'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value')
    ,
    Input('filter-dropdown', 'value')
)
def update_stat_cards(down, distance, main_concept, tag, filter_value):
    # Compute all three cards from the same filtered dataset used by the tables/graph
    # but intentionally do NOT apply the 'efficient' filter when computing these cards
    # (so explosiveness doesn't disappear when the user selects Efficient)
    # Load the correct data source for the selected down
    if down in data_sources:
        df = data_sources[down].copy()
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)

    # Build a mask that applies concept/tag and distance filters. We'll apply the
    # additional filter-dropdown condition only when it is NOT 'efficient'.
    mask = pd.Series(True, index=df.index)
    conc_col = df['OVO CONCEPT']
    if tag:
        mask &= conc_col.astype(str).str.strip().str.upper() == _norm(tag)
    elif main_concept:
        mask &= _main_concept_mask(conc_col, main_concept)
    if distance:
        mask &= df['DIST'] == distance

    # Prepare a second mask to apply filter-dropdown (but skip when filter_value == 'efficient')
    filter_mask = pd.Series(True, index=df.index)
    if filter_value and filter_value != 'efficient':
        if filter_value == 'nonefficient':
            if 'Is_Successful' in df.columns:
                filter_mask &= df['Is_Successful'] == 0
            elif 'Efficient' in df.columns:
                filter_mask &= df['Efficient'] == 0
        elif filter_value == 'explosive':
            if 'Is_Explosive' in df.columns:
                filter_mask &= df['Is_Explosive'] == 1
            elif 'Explosive' in df.columns:
                filter_mask &= df['Explosive'] == 1
        elif filter_value == 'nonexplosive':
            if 'Is_Explosive' in df.columns:
                filter_mask &= df['Is_Explosive'] == 0
            elif 'Explosive' in df.columns:
                filter_mask &= df['Explosive'] == 0

    # Combine masks: concept/distance always applied; filter_mask applied only when not 'efficient'
    combined_mask = mask & filter_mask
    filtered_df = df[combined_mask]

    # If no concept/main selected then return blanks
    if not tag and not main_concept:
        if down:
            # Use df (already down-filtered if a per-down source was selected) to compute totals
            total_plays = len(df[df['DIST'] == distance]) if distance else len(df)
            plays_for_concept = len(df)
            if plays_for_concept == 0 or total_plays == 0:
                return "–", "–", "–"
            # compute totals across df
            if 'Is_Successful' in df.columns:
                efficient_count = int(df['Is_Successful'].sum())
            elif 'Efficient' in df.columns:
                efficient_count = int(df['Efficient'].sum())
            else:
                efficient_count = 0
            if 'Is_Explosive' in df.columns:
                explosive_count = int(df['Is_Explosive'].sum())
            elif 'Explosive' in df.columns:
                explosive_count = int(df['Explosive'].sum())
            else:
                explosive_count = 0
            tendency_val = f"{(plays_for_concept / total_plays * 100):.1f}%" if total_plays > 0 else "–"
            efficiency_val = f"{(efficient_count / plays_for_concept * 100):.1f}%" if plays_for_concept > 0 else "–"
            explosive_val = f"{(explosive_count / plays_for_concept * 100):.1f}%" if plays_for_concept > 0 else "–"
            return tendency_val, efficiency_val, explosive_val
        else:
            return "–", "–", "–"

    # Compute denominator: use same logic as other callbacks (if distance is selected, denominator is plays at that distance)
    total_plays = len(df[df['DIST'] == distance]) if distance else len(df)
    plays_for_concept = len(filtered_df)
    if plays_for_concept == 0 or total_plays == 0:
        return "–", "–", "–"

    # Efficiency: prefer Is_Successful, then Efficient
    if 'Is_Successful' in filtered_df.columns:
        efficient_count = int(filtered_df['Is_Successful'].sum())
    elif 'Efficient' in filtered_df.columns:
        efficient_count = int(filtered_df['Efficient'].sum())
    else:
        efficient_count = 0

    # Explosive: prefer Is_Explosive, then Explosive
    if 'Is_Explosive' in filtered_df.columns:
        explosive_count = int(filtered_df['Is_Explosive'].sum())
    elif 'Explosive' in filtered_df.columns:
        explosive_count = int(filtered_df['Explosive'].sum())
    else:
        explosive_count = 0

    tendency_val = f"{(plays_for_concept / total_plays * 100):.1f}%" if total_plays > 0 else "–"
    efficiency_val = f"{(efficient_count / plays_for_concept * 100):.1f}%" if plays_for_concept > 0 else "–"
    explosive_val = f"{(explosive_count / plays_for_concept * 100):.1f}%" if plays_for_concept > 0 else "–"
    return tendency_val, efficiency_val, explosive_val


@app.callback(
    Output('table-output', 'children'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_table(down, distance, main_concept, tag, filter_value):
    if down in data_sources:
        df = data_sources[down]
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)
    conc_col = df['OVO CONCEPT']
    if tag:
        df = df[conc_col.astype(str).str.strip().str.upper() == _norm(tag)]
    elif main_concept:
        df = df[_main_concept_mask(conc_col, main_concept)]
    if distance:
        df = df[df['DIST'] == distance]
    # Apply filter dropdown
    if filter_value == 'efficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 1]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 1]
    elif filter_value == 'nonefficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 0]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 0]
    elif filter_value == 'explosive':
        if 'Is_Explosive' in df.columns:
            df = df[df['Is_Explosive'] == 1]
        elif 'Explosive' in df.columns:
            df = df[df['Explosive'] == 1]
    elif filter_value == 'nonexplosive':
        if 'Is_Explosive' in df.columns:
            df = df[df['Is_Explosive'] == 0]
        elif 'Explosive' in df.columns:
            df = df[df['Explosive'] == 0]
    if df.empty:
        return html.Div("No matching plays found.", className="text-warning", style={"color": WM_GREEN})
    # Aggregate OVO RESULT counts and percentages for the OVO Results table
    if 'OVO RESULT' in df.columns:
        counts = df['OVO RESULT'].value_counts(dropna=False).reset_index()
        counts.columns = ['OVO RESULT', 'Count']
        total = counts['Count'].sum()
        counts['Percentage'] = counts['Count'].apply(lambda x: f"{(x/total*100):.1f}%")
        ovo_table = dash_table.DataTable(
            data=counts.to_dict('records'),
            columns=[
                {'name': 'OVO RESULT', 'id': 'OVO RESULT'},
                {'name': 'Count', 'id': 'Count'},
                {'name': '%', 'id': 'Percentage'}
            ],
            page_size=10,
            style_table={'maxHeight': '480px', 'overflowY': 'auto', 'marginBottom': '20px'},
            style_cell={
                'fontSize': '14px',
                'padding': '6px',
                'textAlign': 'left',
                'color': 'black',
                'backgroundColor': 'white',
                'fontFamily': 'Georgia, serif'
            },
            style_header={
                'backgroundColor': WM_GOLD,
                'color': WM_GREEN,
                'fontWeight': 'bold',
                'fontFamily': 'Georgia, serif'
            }
        )
        return ovo_table
    else:
        # Fallback: show the whole dataframe as before
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in df.columns],
            page_size=10,
            style_table={'maxHeight': '480px', 'overflowY': 'auto', 'marginBottom': '20px'},
            style_cell={'fontSize': '14px', 'padding': '6px', 'textAlign': 'left', 'color': 'black', 'backgroundColor': 'white', 'fontFamily': 'Georgia, serif'},
            style_header={'backgroundColor': WM_GOLD, 'color': WM_GREEN, 'fontWeight': 'bold', 'fontFamily': 'Georgia, serif'}
        )


@app.callback(
    Output('dataframe-output', 'children'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_dataframe(down, distance, main_concept, tag, filter_value):
    # Provide the full filtered dataframe for the bottom-right display
    if down in data_sources:
        df = data_sources[down]
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)
    conc_col = df['OVO CONCEPT']
    if tag:
        df = df[conc_col.astype(str).str.strip().str.upper() == _norm(tag)]
    elif main_concept:
        df = df[_main_concept_mask(conc_col, main_concept)]
    if distance:
        df = df[df['DIST'] == distance]
    # Apply filter dropdown
    if filter_value == 'efficient':
        df = df[df['Is_Successful'] == 1]
    elif filter_value == 'nonefficient':
        df = df[df['Is_Successful'] == 0]
    elif filter_value == 'explosive':
        df = df[df['Is_Explosive'] == 1]
    elif filter_value == 'nonexplosive':
        df = df[df['Is_Explosive'] == 0]

    if df.empty:
        return html.Div("No matching plays found.", className="text-warning", style={"color": WM_GREEN})

    # Return full DataTable for the dataframe-output container with larger visible area
    count = len(df)
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': c, 'id': c} for c in df.columns],
        page_size=12,
        style_table={'maxHeight': '520px', 'overflowY': 'auto', 'width': '100%'},
        style_cell={'fontSize': '13px', 'padding': '5px', 'textAlign': 'center', 'fontFamily': 'Georgia, serif', 'color': 'black'},
        style_header={'backgroundColor': WM_GOLD, 'color': WM_GREEN, 'fontWeight': 'bold'}
    )
    return html.Div([
        html.Div(f"Plays: {count}", style={"fontWeight": "bold", "color": WM_GOLD, "marginBottom": "6px"}),
        table
    ], style={"width": "100%", "minHeight": "420px"})



# Add filter dropdown to inputs
@app.callback(
    Output('play-graph', 'figure'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_success_vs_gain(down, distance, main_concept, tag, filter_value):
    # Always plot all points for the selected down, but only show points that match the filter
    if down in data_sources:
        df_all = data_sources[down]
    else:
        df_all = pd.concat(data_sources.values(), ignore_index=True)

    # Build mask for filter (ensure mask uses same index as df_all to avoid alignment errors)
    mask = pd.Series(True, index=df_all.index)
    conc_col = df_all['OVO CONCEPT']
    if tag:
        mask &= conc_col.astype(str).str.strip().str.upper() == _norm(tag)
    elif main_concept:
        mask &= _main_concept_mask(conc_col, main_concept)
    if distance:
        mask &= df_all['DIST'] == distance
    if filter_value == 'efficient':
        if 'Is_Successful' in df_all.columns:
            mask &= df_all['Is_Successful'] == 1
        elif 'Efficient' in df_all.columns:
            mask &= df_all['Efficient'] == 1
    elif filter_value == 'nonefficient':
        if 'Is_Successful' in df_all.columns:
            mask &= df_all['Is_Successful'] == 0
        elif 'Efficient' in df_all.columns:
            mask &= df_all['Efficient'] == 0
    elif filter_value == 'explosive':
        if 'Is_Explosive' in df_all.columns:
            mask &= df_all['Is_Explosive'] == 1
        elif 'Explosive' in df_all.columns:
            mask &= df_all['Explosive'] == 1
    elif filter_value == 'nonexplosive':
        if 'Is_Explosive' in df_all.columns:
            mask &= df_all['Is_Explosive'] == 0
        elif 'Explosive' in df_all.columns:
            mask &= df_all['Explosive'] == 0

    # Only show points that match the filter
    df_plot = df_all[mask].copy()
    df_plot['Success_Jitter'] = df_plot['Is_Successful'].apply(lambda x: int(x)) + np.random.uniform(-0.15, 0.15, size=len(df_plot))

    title_parts = []
    if tag:
        title_parts.append(tag)
    elif main_concept:
        title_parts.append(main_concept)
    if down:
        title_parts.append(f"{down} Down")
    if distance:
        title_parts.append(f"{distance} Yards")
    title = " - ".join(title_parts) or "Play Breakdown"

    if df_plot.empty:
        fig = px.scatter(x=[], y=[])
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(title="Yards Gained"),
            yaxis=dict(
                title="Successful Play",
                tickvals=[0, 1],
                ticktext=["Unsuccessful", "Successful"],
                range=[-0.25, 1.25],
                showticklabels=True
            ),
            annotations=[dict(
                text="No plays found for selected filters.",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=18, color=WM_GOLD)
            )]
        )
        return fig

    fig = px.scatter(
        df_plot,
        x='GAIN',
        y='Success_Jitter',
        hover_data={
            'GAIN': True,
            'DIST': True,
            'OVO CONCEPT': True,
            'DN': True,
            'COVERAGE': True,
            'FRONT': True,
            'MOTION': True,
            'HASH': True,
            'Is_Successful': True
        },
        labels={
            'GAIN': 'Yards Gained',
            'Success_Jitter': 'Successful Play',
            'OVO CONCEPT': 'Concept'
        },
        title=title,
        template='plotly_white'
    )

    fig.update_traces(
        marker=dict(
            size=12,
            color=WM_GOLD,
            line=dict(width=2, color=WM_GREEN)
        ),
        selector=dict(mode='markers')
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_x=0.5,
        height=340,
        margin=dict(t=30, b=30, l=60, r=60),
        showlegend=False,
        font=dict(color='black', family='Georgia, serif'),
        xaxis=dict(title="Yards Gained"),
        yaxis=dict(
            title="Successful Play",
            tickvals=[0, 1],
            ticktext=["Unsuccessful", "Successful"],
            range=[-0.25, 1.25],
            showticklabels=True
        )
    )

    return fig



@app.callback(
    Output('coverage-concept-table', 'children'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value')
)
def update_coverage_concept_table(down, distance, main_concept, tag):
    # Show top 20 coverages and concepts from coverage_breakdown
    df = coverage_breakdown.copy()
    # Optionally filter by dropdowns if needed
    if down:
        df = df[df['COVERAGE'].notna()]
    # Only filter by main_concept/tag if column exists
    if 'OVO CONCEPT' in df.columns:
        conc_col = df['OVO CONCEPT']
        if main_concept:
            df = df[_main_concept_mask(conc_col, main_concept)]
        if tag:
            df = df[conc_col.astype(str).str.strip().str.upper() == _norm(tag)]
    else:
        if main_concept or tag:
            return html.Div("No OVO CONCEPT data available for breakdown table.", style={"color": WM_GOLD, "fontWeight": "bold"})
    # Show top 20 by coverage count (not Play_Count)
    sort_col = 'Coverage Count' if 'Coverage Count' in df.columns else df.columns[0]
    top20 = df.sort_values(by=[sort_col], ascending=False).head(20)
    if top20.empty:
        return html.Div("No defensive breakdown data found.", style={"color": WM_GOLD, "fontWeight": "bold"})
    return dash_table.DataTable(
        data=top20.to_dict('records'),
        columns=[{'name': c, 'id': c} for c in top20.columns],
        page_size=20,
        style_table={'maxHeight': '350px', 'overflowY': 'auto', 'marginBottom': '20px'},
        style_cell={
            'fontSize': '14px',
            'padding': '6px',
            'minWidth': '80px',
            'whiteSpace': 'normal',
            'textAlign': 'left',
            'color': WM_GOLD,
            'backgroundColor': WM_GREEN,
            'fontFamily': 'Georgia, serif',
            'fontWeight': 'bold'
        },
        style_header={
            'backgroundColor': WM_GOLD,
            'color': WM_GREEN,
            'fontWeight': 'bold',
            'fontFamily': 'Georgia, serif'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#ffeeb0'},
            {'if': {'row_index': 'even'}, 'backgroundColor': WM_GOLD}
        ]
    )


# Populate coverage dropdown (top 20 coverages by frequency)
@app.callback(
    Output('coverage-dropdown', 'options'),
    Output('coverage-dropdown', 'value'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def populate_coverage_dropdown(down, distance, filter_value):
    # Use RU_clean as the default source (per-down filter applied if provided)
    if down in data_sources:
        df = data_sources[down].copy()
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)
    if distance:
        df = df[df['DIST'] == distance]
    # Optionally apply simple filter (efficient/non)
    if filter_value == 'efficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 1]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 1]
    elif filter_value == 'nonefficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 0]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 0]
    # Get top 20 coverages
    if 'COVERAGE' not in df.columns:
        return [], None
    top_coverages = df['COVERAGE'].dropna().value_counts().head(20)
    options = [{'label': cov, 'value': cov} for cov in top_coverages.index]
    return options, None


# Populate play dropdown (top 20 OVO CONCEPTs by frequency)
@app.callback(
    Output('play-dropdown', 'options'),
    Output('play-dropdown', 'value'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def populate_play_dropdown(down, distance, filter_value):
    if down in data_sources:
        df = data_sources[down].copy()
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)
    if distance:
        df = df[df['DIST'] == distance]
    if filter_value == 'efficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 1]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 1]
    elif filter_value == 'nonefficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 0]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 0]
    top_plays = df['OVO CONCEPT'].dropna().value_counts().head(20)
    options = [{'label': p, 'value': p} for p in top_plays.index]
    return options, None


# Render the coverage-play cross table: when coverage selected -> show top 10 plays that faced that coverage
# when play selected -> show top 10 coverages that play saw; when both selected -> show stats for that pair
@app.callback(
    Output('coverage-play-table-output', 'children'),
    Input('coverage-dropdown', 'value'),
    Input('play-dropdown', 'value'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def render_coverage_play_table(coverage, play, down, distance, filter_value):
    # Base df
    if down in data_sources:
        df = data_sources[down].copy()
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)
    if distance:
        df = df[df['DIST'] == distance]
    # Apply filter dropdown normally here
    if filter_value == 'efficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 1]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 1]
    elif filter_value == 'nonefficient':
        if 'Is_Successful' in df.columns:
            df = df[df['Is_Successful'] == 0]
        elif 'Efficient' in df.columns:
            df = df[df['Efficient'] == 0]
    elif filter_value == 'explosive':
        if 'Is_Explosive' in df.columns:
            df = df[df['Is_Explosive'] == 1]
        elif 'Explosive' in df.columns:
            df = df[df['Explosive'] == 1]
    elif filter_value == 'nonexplosive':
        if 'Is_Explosive' in df.columns:
            df = df[df['Is_Explosive'] == 0]
        elif 'Explosive' in df.columns:
            df = df[df['Explosive'] == 0]

    # No selection: show instructive message
    if not coverage and not play:
        return html.Div("Select a defensive coverage or an offensive play to see the top-10 breakdown.", style={"color": WM_GOLD, "fontWeight": "bold"})

    # Coverage selected: show top 10 plays that faced this coverage
    if coverage and not play:
        sub = df[df['COVERAGE'] == coverage]
        if sub.empty:
            return html.Div("No plays found for this coverage.", style={"color": WM_GOLD})
        counts = sub['OVO CONCEPT'].value_counts().head(10).reset_index()
        counts.columns = ['OVO CONCEPT', 'Plays']
        # Compute efficiency per concept
        effs = sub.groupby('OVO CONCEPT').apply(lambda g: (g['Is_Successful'].sum() / len(g) * 100) if 'Is_Successful' in g.columns else (g['Efficient'].sum() / len(g) * 100 if 'Efficient' in g.columns else np.nan)).reset_index()
        effs.columns = ['OVO CONCEPT', 'Efficiency %']
        merged = counts.merge(effs, on='OVO CONCEPT', how='left')
        merged['Efficiency %'] = merged['Efficiency %'].round(1).astype(str) + '%'
        table = dash_table.DataTable(
            data=merged.to_dict('records'),
            columns=[{'name': 'OVO CONCEPT', 'id': 'OVO CONCEPT'}, {'name': 'Plays', 'id': 'Plays'}, {'name': 'Efficiency %', 'id': 'Efficiency %'}],
            page_size=10,
            style_table={'maxHeight': '300px', 'overflowY': 'auto', 'backgroundColor': 'white'},
            style_cell={'textAlign': 'left', 'fontFamily': 'Georgia, serif', 'fontSize': '13px', 'color': 'black', 'backgroundColor': 'white'},
            style_header={'backgroundColor': 'white', 'color': WM_GREEN, 'fontWeight': 'bold'}
        )
        return dbc.Card(dbc.CardBody([table]), style={'backgroundColor': 'white', 'borderRadius': '6px'})

    # Play selected: show top 10 coverages that play saw
    if play and not coverage:
        sub = df[df['OVO CONCEPT'] == play]
        if sub.empty:
            return html.Div("No coverages found for this play.", style={"color": WM_GOLD})
        counts = sub['COVERAGE'].value_counts().head(10).reset_index()
        counts.columns = ['COVERAGE', 'Plays']
        effs = sub.groupby('COVERAGE').apply(lambda g: (g['Is_Successful'].sum() / len(g) * 100) if 'Is_Successful' in g.columns else (g['Efficient'].sum() / len(g) * 100 if 'Efficient' in g.columns else np.nan)).reset_index()
        effs.columns = ['COVERAGE', 'Efficiency %']
        merged = counts.merge(effs, on='COVERAGE', how='left')
        merged['Efficiency %'] = merged['Efficiency %'].round(1).astype(str) + '%'
        table = dash_table.DataTable(
            data=merged.to_dict('records'),
            columns=[{'name': 'COVERAGE', 'id': 'COVERAGE'}, {'name': 'Plays', 'id': 'Plays'}, {'name': 'Efficiency %', 'id': 'Efficiency %'}],
            page_size=10,
            style_table={'maxHeight': '300px', 'overflowY': 'auto', 'backgroundColor': 'white'},
            style_cell={'textAlign': 'left', 'fontFamily': 'Georgia, serif', 'fontSize': '13px', 'color': 'black', 'backgroundColor': 'white'},
            style_header={'backgroundColor': 'white', 'color': WM_GREEN, 'fontWeight': 'bold'}
        )
        return dbc.Card(dbc.CardBody([table]), style={'backgroundColor': 'white', 'borderRadius': '6px'})

    # Both selected: show single-row stats for that pair
    sub = df[(df['COVERAGE'] == coverage) & (df['OVO CONCEPT'] == play)]
    if sub.empty:
        return html.Div("No plays found for this coverage/play pair.", style={"color": WM_GOLD})
    plays = len(sub)
    eff = (sub['Is_Successful'].sum() / plays * 100) if 'Is_Successful' in sub.columns else ((sub['Efficient'].sum() / plays * 100) if 'Efficient' in sub.columns else np.nan)
    eff_str = f"{eff:.1f}%" if not np.isnan(eff) else "–"
    row = {'COVERAGE': coverage, 'OVO CONCEPT': play, 'Plays': plays, 'Efficiency %': eff_str}
    table = dash_table.DataTable(
        data=[row],
        columns=[{'name': c, 'id': c} for c in row.keys()],
        page_size=10,
        style_table={'maxHeight': '300px', 'overflowY': 'auto', 'backgroundColor': 'white'},
        style_cell={'textAlign': 'left', 'fontFamily': 'Georgia, serif', 'fontSize': '13px', 'color': 'black', 'backgroundColor': 'white'},
        style_header={'backgroundColor': 'white', 'color': WM_GREEN, 'fontWeight': 'bold'}
    )
    return dbc.Card(dbc.CardBody([table]), style={'backgroundColor': 'white', 'borderRadius': '6px'})

@app.callback(
    Output('result-table-output', 'children'),
    Input('down-dropdown', 'value'),
    Input('distance-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_result_table(down, distance, main_concept, tag, filter_value):
    if down in data_sources:
        df = data_sources[down]
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)
    conc_col = df['OVO CONCEPT']
    if tag:
        df = df[conc_col.astype(str).str.strip().str.upper() == _norm(tag)]
    elif main_concept:
        df = df[_main_concept_mask(conc_col, main_concept)]
    if distance:
        df = df[df['DIST'] == distance]
    # Apply filter dropdown
    if filter_value == 'efficient':
        df = df[df['Is_Successful'] == 1]
    elif filter_value == 'nonefficient':
        df = df[df['Is_Successful'] == 0]
    elif filter_value == 'explosive':
        df = df[df['Is_Explosive'] == 1]
    elif filter_value == 'nonexplosive':
        df = df[df['Is_Explosive'] == 0]
    # Group by OVO RESULT
    result_counts = df['OVO RESULT'].value_counts(dropna=False)
    total = result_counts.sum()
    table_data = [
        {
            'Result': str(result),
            'Count': count,
            'Percentage': f"{(count / total * 100):.1f}%"
        }
        for result, count in result_counts.items()
    ]
    return dash_table.DataTable(
        data=table_data,
        columns=[
            {'name': 'Result', 'id': 'Result'},
            {'name': 'Count', 'id': 'Count'},
            {'name': 'Percentage', 'id': 'Percentage'}
        ],
        page_size=10,
        style_table={'maxHeight': '350px', 'overflowY': 'auto', 'marginBottom': '20px'},
        style_cell={
            'fontSize': '14px',
            'padding': '6px',
            'minWidth': '80px',
            'whiteSpace': 'normal',
            'textAlign': 'left',
            'color': 'black',
            'backgroundColor': 'white',
            'fontFamily': 'Georgia, serif'
        },
        style_header={
            'backgroundColor': WM_GOLD,
            'color': WM_GREEN,
            'fontWeight': 'bold',
            'fontFamily': 'Georgia, serif'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f6f1'},
            {'if': {'row_index': 'even'}, 'backgroundColor': 'white'}
        ]
    )



# === William & Mary Callbacks ===

# Dropdown for main concept (WM)
@app.callback(
    Output("main-concept-dropdown-wm", "options"),
    Output("main-concept-dropdown-wm", "value"),
    Input("down-dropdown-wm", "value"),
    Input("main-concept-dropdown-wm", "value")
)
def update_main_concepts_wm(down, current_value):
    df = WM_data_df.copy()
    # Map down string to number for WM data
    down_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    if down:
        down_val = down_map.get(down, down)
        df = df[df["DN"] == down_val]
    concepts = df["OVO CONCEPT"].dropna()
    def extract_main(concept):
        if '#' in concept:
            return concept.split('#')[0].strip()
        elif '/' in concept:
            parts = concept.split('/')
            return '/'.join(parts[:2]) if len(parts) > 1 else concept
        else:
            return concept
    main_concepts_list = concepts.apply(extract_main)
    main_concepts = main_concepts_list.unique()
    total_plays = len(df)
    tendency_pct = {mc: (main_concepts_list == mc).sum() / total_plays * 100 for mc in main_concepts}
    main_concepts_sorted = sorted(main_concepts, key=lambda x: -tendency_pct.get(x, 0))
    options = [{"label": mc, "value": mc} for mc in main_concepts_sorted]
    # Only reset if options are not empty and current_value is not in options
    if options and current_value not in [opt['value'] for opt in options]:
        current_value = None
    return options, current_value

# Dropdown for tag (WM)
@app.callback(
    Output("tag-dropdown-wm", "options"),
    Output("tag-dropdown-wm", "value"),
    Input("main-concept-dropdown-wm", "value"),
    Input("down-dropdown-wm", "value"),
    Input("tag-dropdown-wm", "value"),
)
def update_tag_options_wm(main_concept, down, current_tag):
    df = WM_data_df.copy()
    down_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    if down:
        down_val = down_map.get(down, down)
        df = df[df["DN"] == down_val]
    if not main_concept:
        return [], None
    concepts = df["OVO CONCEPT"].dropna()
    tags = sorted([c for c in concepts if c.startswith(main_concept + '/')])
    options = [{"label": tag, "value": tag} for tag in tags]
    if options and current_tag not in [opt['value'] for opt in options]:
        current_tag = None
    return options, current_tag

# Dropdown for distance (WM)
@app.callback(
    Output('distance-dropdown-wm', 'options'),
    Output('distance-dropdown-wm', 'value'),
    Input('down-dropdown-wm', 'value'),
    Input('main-concept-dropdown-wm', 'value'),
    Input('tag-dropdown-wm', 'value'),
    Input('distance-dropdown-wm', 'value')
)
def update_distance_options_wm(down, main_concept, tag, current_distance):
    df = WM_data_df.copy()
    down_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    if down:
        down_val = down_map.get(down, down)
        df = df[df["DN"] == down_val]
    if tag:
        df = df[df['OVO CONCEPT'] == tag]
    elif main_concept:
        df = df[df['OVO CONCEPT'].str.startswith(main_concept + '/', na=False) | (df['OVO CONCEPT'] == main_concept)]
    distances = sorted(df['DIST'].dropna().unique())
    options = [{'label': dist, 'value': dist} for dist in distances]
    # Always default to None unless user picks
    return options, None

# Stat cards (WM)
@app.callback(
    Output('tendency-value-wm', 'children'),
    Output('efficiency-value-wm', 'children'),
    Output('explosive-value-wm', 'children'),
    Input('down-dropdown-wm', 'value'),
    Input('distance-dropdown-wm', 'value'),
    Input('main-concept-dropdown-wm', 'value'),
    Input('tag-dropdown-wm', 'value')
)
def update_stat_cards_wm(down, distance, main_concept, tag):
    df = WM_data_df.copy()
    down_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    if down:
        down_val = down_map.get(down, down)
        df = df[df["DN"] == down_val]
    if tag:
        filtered_df = df[df['OVO CONCEPT'] == tag]
    elif main_concept:
        filtered_df = df[df['OVO CONCEPT'].str.startswith(main_concept + '/', na=False) | (df['OVO CONCEPT'] == main_concept)]
    else:
        return "–", "–", "–"
    if distance:
        filtered_df = filtered_df[filtered_df['DIST'] == distance]
    total_plays = len(df[df['DIST'] == distance]) if distance else len(df)
    plays_for_concept = len(filtered_df)
    efficient_plays = filtered_df['Efficient'].sum() if 'Efficient' in filtered_df.columns else 0
    explosive_plays = filtered_df['Explosive'].sum() if 'Explosive' in filtered_df.columns else 0
    tendency_val = f"{(plays_for_concept / total_plays * 100):.1f}%" if total_plays > 0 else "–"
    efficiency_val = f"{(efficient_plays / plays_for_concept * 100):.1f}%" if plays_for_concept > 0 else "–"
    explosive_val = f"{(explosive_plays / plays_for_concept * 100):.1f}%" if plays_for_concept > 0 else "–"
    return tendency_val, efficiency_val, explosive_val

# Table output (WM)
@app.callback(
    Output('table-output-wm', 'children'),
    Input('down-dropdown-wm', 'value'),
    Input('distance-dropdown-wm', 'value'),
    Input('main-concept-dropdown-wm', 'value'),
    Input('tag-dropdown-wm', 'value'),
    Input('filter-dropdown-wm', 'value')
)
def update_table_wm(down, distance, main_concept, tag, filter_value):
    df = WM_data_df.copy()
    down_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    if down:
        down_val = down_map.get(down, down)
        df = df[df["DN"] == down_val]
    if tag:
        df = df[df['OVO CONCEPT'] == tag]
    elif main_concept:
        df = df[df['OVO CONCEPT'].str.startswith(main_concept + '/', na=False) | (df['OVO CONCEPT'] == main_concept)]
    if distance:
        df = df[df['DIST'] == distance]
    if filter_value == 'efficient':
        df = df[df['Efficient'] == 1]
    elif filter_value == 'nonefficient':
        df = df[df['Efficient'] == 0]
    elif filter_value == 'explosive':
        df = df[df['Explosive'] == 1]
    elif filter_value == 'nonexplosive':
        df = df[df['Explosive'] == 0]
    if df.empty:
        return html.Div("No matching plays found.", className="text-warning", style={"color": "#006341"})
    # Group rows together by OVO RESULT for easier review (collapse families like R*, C*)
    if 'OVO RESULT' in df.columns:
        def _group_result(series: pd.Series) -> pd.Series:
            s = series.astype(str).str.strip().str.upper()
            s = s.str.replace(r'^\s*R.*$', 'R', regex=True)
            s = s.str.replace(r'^\s*C.*$', 'C', regex=True)
            return s
        df['__RES_G__'] = _group_result(df['OVO RESULT'])
        by_cols = ['__RES_G__', 'OVO RESULT'] + (['OVO CONCEPT'] if 'OVO CONCEPT' in df.columns else [])
        df = df.sort_values(
            by=by_cols,
            key=lambda s: s.astype(str).str.strip().str.upper(),
            kind='mergesort'
        ).drop(columns='__RES_G__')

    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': c, 'id': c} for c in df.columns],
        page_size=10,
        style_table={'maxHeight': '350px', 'overflowY': 'auto', 'marginBottom': '20px'},
        style_cell={
            'fontSize': '14px',
            'padding': '6px',
            'minWidth': '80px',
            'whiteSpace': 'normal',
            'textAlign': 'left',
            'color': 'black',
            'backgroundColor': 'white',
            'fontFamily': 'Georgia, serif'
        },
        style_header={
            'backgroundColor': '#FFC72C',
            'color': '#006341',
            'fontWeight': 'bold',
            'fontFamily': 'Georgia, serif'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f6f1'},
            {'if': {'row_index': 'even'}, 'backgroundColor': 'white'}
        ]
    )


# Update player photo when a player is selected (William & Mary page)
@app.callback(
    Output('player-photo-wm', 'src'),
    Input('position-dropdown-wm', 'value'),
    Input('player-dropdown-wm', 'value')
)
def update_player_photo_src(position, player):
    import os
    # Default image
    default = '/assets/WMFB.jpg'
    if not position or not player:
        return default
    # Map position to folder name
    pos_folder = position if position in ['QB', 'RB', 'WR_TE'] else None
    if pos_folder is None:
        return default
    base_path = os.path.join(os.path.dirname(__file__), 'assets', 'Players Photos', pos_folder)
    if not os.path.exists(base_path):
        return default
    # File names in assets include the extension; look for the matching name
    # Player dropdown values were created by stripping the .webp extension
    candidates = [f for f in os.listdir(base_path) if f.lower().startswith(player.lower())]
    if not candidates:
        # Try case-insensitive contains match
        candidates = [f for f in os.listdir(base_path) if player.lower() in f.lower()]
    if not candidates:
        return default
    # Prefer exact match; otherwise use first candidate
    chosen = None
    for f in candidates:
        name_no_ext = os.path.splitext(f)[0]
        if name_no_ext.lower() == player.lower():
            chosen = f
            break
    if chosen is None:
        chosen = candidates[0]
    # Build web path for the asset
    web_path = f"/assets/Players Photos/{pos_folder}/{chosen}"
    return web_path

# Play graph (WM)
@app.callback(
    Output('play-graph-wm', 'figure'),
    Input('down-dropdown-wm', 'value'),
    Input('distance-dropdown-wm', 'value'),
    Input('main-concept-dropdown-wm', 'value'),
    Input('tag-dropdown-wm', 'value')
)
def update_success_vs_gain_wm(down, distance, main_concept, tag):
    df = WM_data_df.copy()
    if down:
        df = df[df["DN"] == down]
    if tag:
        df = df[df['OVO CONCEPT'] == tag]
    elif main_concept:
        df = df[df['OVO CONCEPT'].str.startswith(main_concept + '/', na=False) | (df['OVO CONCEPT'] == main_concept)]
    if distance:
        df = df[df['DIST'] == distance]
    if df.empty:
        fig = px.scatter(x=[], y=[])
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(title="Yards Gained"),
            yaxis=dict(
                title="Successful Play",
                tickvals=[0, 1],
                ticktext=["Unsuccessful", "Successful"]
            ),
            annotations=[dict(
                text="No plays found for selected filters.",
                               xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=18, color=WM_GOLD)
            )]
        )
        return fig
    df_plot = df.copy()
    df_plot['Success_Jitter'] = df_plot['Is_Successful'].apply(lambda x: int(x)) + np.random.uniform(-0.15, 0.15, size=len(df_plot))
    title_parts = []
    if tag:
        title_parts.append(tag)
    elif main_concept:
        title_parts.append(main_concept)
    if down:
        title_parts.append(f"{down} Down")
    if distance:
        title_parts.append(f"{distance} Yards")
    title = " - ".join(title_parts) or "Play Breakdown"
    fig = px.scatter(
        df_plot,
        x='GAIN',
        y='Success_Jitter',
        hover_data={
            'GAIN': True,
            'DIST': True,
            'OVO CONCEPT': True,
            'DN': True,
            'COVERAGE': True,
            'FRONT': True,
            'MOTION': True,
            'HASH': True,
            'Is_Successful': True
        },
        labels={
            'GAIN': 'Yards Gained',
            'Success_Jitter': 'Successful Play',
            'OVO CONCEPT': 'Concept'
        },
        title=title,
        template='plotly_white'
    )
    fig.update_traces(
        marker=dict(
            size=12,
            color="#FFC72C",
            line=dict(width=2, color="#006341")
        ),
        selector=dict(mode='markers')
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_x=0.5,
        height=520,
        margin=dict(t=50, b=40, l=80, r=80),
        showlegend=False,
        font=dict(color='black', family='Georgia, serif'),
        xaxis=dict(title="Yards Gained"),
        yaxis=dict(
            title="Successful Play",
            tickvals=[0, 1],
            ticktext=["Unsuccessful", "Successful"],
            range=[-0.25, 1.25]
        )
    )
    return fig

# Results breakdown table (WM)
@app.callback(
    Output('result-table-output-wm', 'children'),
    Input('down-dropdown-wm', 'value'),
    Input('distance-dropdown-wm', 'value'),
    Input('main-concept-dropdown-wm', 'value'),
    Input('tag-dropdown-wm', 'value'),
    Input('filter-dropdown-wm', 'value')
)
def update_result_table_wm(down, distance, main_concept, tag, filter_value):
    df = WM_data_df.copy()
    if down:
        df = df[df["DN"] == down]
    if tag:
        df = df[df['OVO CONCEPT'] == tag]
    elif main_concept:
        df = df[df['OVO CONCEPT'].str.startswith(main_concept + '/', na=False) | (df['OVO CONCEPT'] == main_concept)]
    if distance:
        df = df[df['DIST'] == distance]
    if filter_value == 'efficient':
        df = df[df['Is_Successful'] == 1]
    elif filter_value == 'nonefficient':
        df = df[df['Is_Successful'] == 0]
    elif filter_value == 'explosive':
        df = df[df['Is_Explosive'] == 1]
    elif filter_value == 'nonexplosive':
        df = df[df['Is_Explosive'] == 0]
    result_counts = df['OVO RESULT'].value_counts(dropna=False)
    total = result_counts.sum()
    table_data = [
        {
            'Result': str(result),
            'Count': count,
            'Percentage': f"{(count / total * 100):.1f}%"
        }
        for result, count in result_counts.items()
    ]
    return dash_table.DataTable(
        data=table_data,
        columns=[
            {'name': 'Result', 'id': 'Result'},
            {'name': 'Count', 'id': 'Count'},
            {'name': 'Percentage', 'id': 'Percentage'}
        ],
        page_size=10,
        style_table={'maxHeight': '350px', 'overflowY': 'auto', 'marginBottom': '20px'},
        style_cell={
            'fontSize': '14px',
            'padding': '6px',
            'minWidth': '80px',
            'whiteSpace': 'normal',
            'textAlign': 'left',
            'color': 'black',
            'backgroundColor': 'white',
            'fontFamily': 'Georgia, serif'
        },
        style_header={
            'backgroundColor': '#FFC72C',
            'color': '#006341',
            'fontWeight': 'bold',
            'fontFamily': 'Georgia, serif'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f6f1'},
            {'if': {'row_index': 'even'}, 'backgroundColor': 'white'}
        ]
    )


# === Shared Callbacks ===

@app.callback(
    Output('distance-dropdown', 'options'),
    Output('distance-dropdown', 'value'),
    Input('down-dropdown', 'value'),
    Input('main-concept-dropdown', 'value'),
    Input('tag-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_distance_dropdown(down, main_concept, tag, filter_value):
    # Use the correct data source
    if down in data_sources:
        df = data_sources[down]
    else:
        df = pd.concat(data_sources.values(), ignore_index=True)

    conc_col = df['OVO CONCEPT']
    if tag:
        df = df[conc_col.astype(str).str.strip().str.upper() == _norm(tag)]
    elif main_concept:
        df = df[_main_concept_mask(conc_col, main_concept)]
    elif filter_value:
        df = df[conc_col.astype(str).str.strip().str.upper() == _norm(filter_value)]

    distances = sorted(df['DIST'].dropna().unique())
    options = [{'label': dist, 'value': dist} for dist in distances]
    return options, None


# Filter dropdown options (Efficient, Non-Efficient, Explosive, Non-Explosive)
@app.callback(
    Output('filter-dropdown', 'options'),
    Output('filter-dropdown', 'value'),
    Input('filter-dropdown', 'value')
)
def update_filter_dropdown(current_value):
    options = [
        {'label': 'Efficient', 'value': 'efficient'},
        {'label': 'Non-Efficient', 'value': 'nonefficient'},
        {'label': 'Explosive', 'value': 'explosive'},
        {'label': 'Non-Explosive', 'value': 'nonexplosive'}
    ]
    if current_value not in [opt['value'] for opt in options]:
        current_value = None
    return options, current_value

@app.callback(
    Output('main-concept-dropdown', 'options'),
    Output('main-concept-dropdown', 'value'),
    Input('down-dropdown', 'value'),
    Input('main-concept-dropdown', 'value')
)
def update_main_concept_dropdown(down, current_value):
    # Explicit list provided by user
    main_concepts_list = [
        '8/9', '12/13', '14/15', '16/17', '18/19', '22/23', '24/25', '28/29', '34/35', '36/37', '40/41', '46/47', '72/73',
        '74/75', '212/213/LK/POP', '214/215', '218/219', '220/221', '222/223', '234/235/POP', '236/237/MOSS/TORPEDO', '240/241',
        'AGGIE/STOP', 'AIR FORCE', 'ALOHA', 'ANIMAL HOUSE', 'ARMY', 'AUSSIE', 'BAYSIDE', 'BEAR/BULL', 'BERMUDA', 'BEYONCE',
        'BILL/MARY', 'BLADE/RAZOR', 'BLAZE', 'BLUE/RED', 'BOLT/CRNR', 'BRANCH', 'BUNKER/OBOE/WHL', 'BURRITO', 'BUTCHER/GO',
        'CALGARY/RODEO', 'CAMO', 'CAVALIER', 'CENTER', 'CHEESE', 'CHICAGO', 'COCAINE', 'COLT', 'COPPERHEAD/GUCCI', 'COWBOY/SHERIFF',
        'CROSS', 'DANCER', 'DASH', 'DBL BOW', 'DELTA', 'DODGER', 'DOLPHIN', 'DONKEY', 'DRAGON', 'DRAKE/MIGOS', 'DRIVE', 'DSL',
        'EAST/WEST', 'FADE', 'FOLLOW', 'FOX', 'GEE GEE', 'GODFATHER', 'GRASS 12/13/F/S', 'GREEN', 'HAWAII', 'HAWKEYE', 'HOOK',
        'HOOSIERS/WHL/FOLLOW', 'HOSS', 'IOWA', 'JAY Z', 'JORDAN', 'KENTUCKY DERBY', 'KILL', 'LAMAR', 'LIMO', 'LINCOLN', 'MASSAGE',
        'MAUI', 'MAYWEATHER', 'MESH', 'MOSS', 'NAS', 'NAVY', 'NO PLAY', 'NOVA', 'NY', 'OUTBACK', 'PEANUTS', 'PEDRO 36/37/MOSS',
        'PELICAN', 'PIN', 'PIVOT', 'PLATINUM', 'PRISON', 'RACE/LEGGO', 'RAMBO/LIMBO', 'RATTLER', 'RENO/LAS VEGAS', 'RICKY/LUCY',
        'RIP/LIZ', 'ROAST', 'ROCK/LAVA/PO', 'ROGER/LOUIE', 'RUNBACKS', 'SCAT', 'SEA/SYR', 'SHAVE', 'SKITTLES', 'SLAM', 'SNAG',
        'SPACE', 'ST.LOUIS/RANGERS', 'STALLION', 'STICK', 'STING', 'STK 1/2', 'STOPS', 'STUTTER', 'SUBMARINE', 'SUBWAY', 'SWIPE',
        'SWORD', 'T-PAIN', 'TANK', 'TENNESSEE', 'THOR', 'THRONE', 'THUNDERCAT', 'TOP GUN/MAVERICK/ROSCOE/BLF', 'TRAIN', 'TRIANGLE',
        'TRICK', 'TRIM', 'TULSA', 'TUXEDO', 'TYSON', 'VENOM', 'VICTORY', 'WAHOO', 'WAVES', 'WHL/FOLLOW', 'WRENCH/BULLET', 'YOGI'
    ]
    main_concepts = list(set(main_concepts_list))
    from Football import data_sources

    # Use per-down data if down is selected, else all data
    if down in data_sources:
        df = data_sources[down]
    else:
        import pandas as pd
        df = pd.concat(data_sources.values(), ignore_index=True)

    # Normalize OVO CONCEPT and count plays per main concept:
    # match exact MAIN, MAIN/..., or MAIN ... (space)
    conc = df['OVO CONCEPT'].astype(str).str.strip().str.upper()
    counts = {}
    for mc in main_concepts:
        mc_norm = _norm(mc)
        mask = (conc == mc_norm) | conc.str.startswith(mc_norm + '/', na=False) | conc.str.startswith(mc_norm + ' ', na=False)
        cnt = int(mask.sum())
        if cnt > 0:
            counts[mc] = cnt

    # Sort by greatest tendency (count desc) and build options
    main_concepts_sorted = sorted(counts.keys(), key=lambda k: -counts[k])
    options = [{'label': mc, 'value': mc} for mc in main_concepts_sorted]

    if current_value not in counts:
        current_value = None
    return options, current_value

# Down dropdown options
@app.callback(
    Output('down-dropdown', 'options'),
    Output('down-dropdown', 'value'),
    Input('down-dropdown', 'value')
)
def update_down_dropdown(current_value):
    downs = list(data_sources.keys())
    options = [{'label': down, 'value': down} for down in downs]
    if current_value not in downs:
        current_value = None
    return options, current_value

# Keep only ONE main guard and no stray code below it.
if __name__ == "__main__":
    app.run(debug=True, port=8051)

