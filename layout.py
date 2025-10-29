# This file will contain the layout and navigation for the dashboard website.
from dash import dcc, html
import dash_bootstrap_components as dbc

# Clean, functional sidebar with toggle button
def sidebar(is_open=True):
    sidebar_style = {
        "position": "fixed",
        "top": 0,
        "left": "0" if is_open else "-240px",
        "width": "240px",
        "height": "100vh",
        "backgroundColor": "#23272A",  # dark grey
        "color": "#FFC72C",
        "zIndex": 3000,
        "transition": "left 0.3s",
        "boxShadow": "0 4px 24px #23272A",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
        "justifyContent": "flex-start",
        "borderRight": "2px solid #FFC72C",
        "borderRadius": "0 12px 12px 0"
    }
    close_btn_style = {
        "position": "absolute",
        "top": "16px",
        "right": "16px",
        "fontSize": "22px",
        "color": "#FFC72C",
        "background": "none",
        "border": "none",
        "cursor": "pointer",
        "zIndex": 3100,
        "display": "block" if is_open else "none"
    }
    return html.Div([
        html.Button("✕", id="sidebar-close", style=close_btn_style),
        html.H2("WM Football Dash", style={"color": "#FFC72C", "fontFamily": "Georgia, serif", "marginTop": "48px", "marginBottom": "32px", "textAlign": "center", "fontSize": "22px"}),
        html.Hr(style={"borderColor": "#FFC72C", "width": "80%"}),
        dcc.Link("William & Mary", href="/wm", style={"display": "block", "color": "#FFC72C", "fontSize": "20px", "fontFamily": "Georgia, serif", "marginBottom": "18px", "textAlign": "center", "textDecoration": "none"}),
        dcc.Link("Richmond", href="/richmond", style={"display": "block", "color": "#FFC72C", "fontSize": "20px", "fontFamily": "Georgia, serif", "marginBottom": "18px", "textAlign": "center", "textDecoration": "none"}),
        html.Hr(style={"borderColor": "#FFC72C", "width": "80%"}),
    ], id="sidebar", style=sidebar_style)

def spring_layout():
    return dbc.Container([
        html.Div(id="offense-section-wm", children=[
            # Page header
            dbc.Row([
                dbc.Col([
                    html.Img(src="/assets/tribe-words-content.jpg", style={"height": "110px", "marginBottom": "5px"}),
                    html.H2("William and Mary Player Analysis", className="mb-0", style={"color": "#006341", "fontFamily": "Georgia, serif"}),
                    html.Div("Spring 2025", style={"textAlign": "center", "fontSize": "22px", "color": "#006341", "fontFamily": "Georgia, serif", "marginTop": "2px"}),
                ], width=12, style={"textAlign": "center", "marginBottom": "15px"})
            ], className="mb-4"),

            # Main content row: left column for photo/dropdowns, right column for boxes/tables
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # Center image above dropdowns
                        html.Div(html.Img(id="player-photo-wm", src="/assets/WMFB.jpg", style={"height": "110px", "width": "80px", "objectFit": "contain", "borderRadius": "10px", "border": "2px solid #006341", "backgroundColor": "#FFF", "marginBottom": "12px", "display": "block"}), style={"display": "flex", "justifyContent": "center", "width": "100%"}),
                        # Dropdowns centered and pulled in from the very edge
                        html.Div([
                            dcc.Dropdown(
                                id="position-dropdown-wm",
                                options=[
                                    {"label": "Quarterback", "value": "QB"},
                                    {"label": "Running Back", "value": "RB"},
                                    {"label": "Wide Receiver / Tight End", "value": "WR_TE"}
                                ],
                                value=None,
                                clearable=True,
                                placeholder="Select Position Group",
                                style={"fontSize": "15px", "color": "#006341", "backgroundColor": "#FFF8E1", "border": "none", "boxShadow": "none", "outline": "none", "width": "220px", "margin": "6px auto 0 auto", "boxSizing": "border-box", "display": "block", "borderBottom": "2px solid #006341", "fontFamily": "Georgia, serif"}
                            ),
                            dcc.Dropdown(
                                id="player-dropdown-wm",
                                options=[],
                                value=None,
                                clearable=True,
                                placeholder="Select Player",
                                style={"fontSize": "15px", "color": "#006341", "backgroundColor": "#FFF8E1", "border": "none", "boxShadow": "none", "outline": "none", "width": "220px", "margin": "6px auto 0 auto", "boxSizing": "border-box", "display": "block", "borderBottom": "2px solid #006341", "fontFamily": "Georgia, serif"}
                            )
                        ], style={"display": "flex", "flexDirection": "column", "alignItems": "center", "paddingLeft": "12px", "paddingRight": "12px"})
                    ])
                ], xs=12, lg=3, style={"paddingLeft": "12px", "paddingRight": "12px"}),

                dbc.Col([
                    dbc.Row([
                        dbc.Col(html.Div(id="efficiency-box-wm"), width=6),
                        dbc.Col(html.Div(id="explosiveness-box-wm"), width=6)
                    ], style={"marginBottom": "20px", "marginTop": "10px"}),
                    dbc.Row([
                        dbc.Col(html.Div(id="player-totals-table-wm", style={"marginBottom": "20px", "color": "#006341", "fontFamily": "Georgia, serif"}), width=6),
                        dbc.Col(html.Div(id="top3-concepts-table-wm", style={"marginBottom": "20px", "color": "#006341", "fontFamily": "Georgia, serif"}), width=6)
                    ])
                ], xs=12, lg=9)
            ], className="mb-4", justify="start"),

            # Plays table row
            dbc.Row([
                dbc.Col([
                    html.Div(id="player-plays-table-wm", style={"marginTop": "20px", "color": "#006341", "fontFamily": "Georgia, serif"})
                ], width=12)
            ])
        ]),  # End offense-section-wm
        html.Div(style={"height": "50px"})
    ], fluid=True, style={"minHeight": "100vh", "paddingTop": "15px", "backgroundColor": "#FFF8E1"})
