import pandas as pd
import numpy as np
from dash import dcc, html
import dash_bootstrap_components as dbc


WM_data = pd.read_excel(r'spring_data.xlsx')
WM_clean = WM_data.drop(columns=[' .1', 'S1', 'S2', 'S3', 'S4', 'V', 'L', 'GAIN', 'REC#', 'PLAY RESULT', 'BLITZ', 
                                 'FRONT', 'RUSHERS', 'STUNT', 'COVERAGE', 'FORM FAM', 'FIB', 'TAPE LABELS'])

keep_periods = [
    'TEAM SITUATION', 'TEAM SITUATION #2', 'OFFENSE TEAM SITUATIONS',
    'TEAM TEMPO', 'TEAM TEMPO #2', 'TEAM PERIOD', 'OFFENSE TEAM TEMPO',
    'OVERTIME PERIOD', 'TEAM PERIOD #2 (FIXED)',
    'TEAM SITUATION PART 2', 'TEAM SITUATION 2 MIN', 'PASS SKELLY',
    'TEAM PASS SKELLY', 'TEAM 2', 'OFFENSE PASS SKELLY',
    '4TH DOWN', 'TEAM PERIOD #1 (FIXED)', 'END OF  HALF'
]

WM_clean = WM_clean[WM_clean['PRAC DRILL'].isin(keep_periods)]

# Remove unwanted OVO RESULT rows
remove_results = [' ', 'MAYDAY', 'FALSE START', 'FG', 'RUN REVIEW', 'TEMPO TEACH']
WM_clean = WM_clean[~WM_clean['OVO RESULT'].isin(remove_results)]

# Efficient / Explosive result lists (passes/runs)
efficient_pass_results = [
    'C', 'C+', 'C++', 'C+++', 'C+++2', 'C++2', 'CBOG', 'CGRT', 'CGRT+', 'CGRT++', 'CGRT+++', 'CGRT+++2', 'CGRT++2'
]

# Efficient running plays (OVO RESULT)
efficient_run_results = [
 'R+', 'R++', 'R++15', 
]

# Explosive running plays (OVO RESULT)
explosive_run_results = [
    'R+', 'R++', 'R++15'
]

# Explosive passing plays (OVO RESULT)
explosive_pass_results = [
    'CGRT++', 'CGRT+++', 'CGRT+++2', 'CGRT++2', 'C++', 'C+++', 'C+++2', 'C++2'
]

# Update Efficient column (passes and runs)
WM_clean['Efficient'] = np.where(
    ((WM_clean['R/P'] == 'P') & (WM_clean['OVO RESULT'].isin(efficient_pass_results))) |
    ((WM_clean['R/P'] == 'R') & (WM_clean['OVO RESULT'].isin(efficient_run_results))),
    1, 0
)

# Update Explosive column (passes and runs)
WM_clean['Explosive'] = np.where(
    ((WM_clean['R/P'] == 'R') & (WM_clean['OVO RESULT'].isin(explosive_run_results))) |
    ((WM_clean['R/P'] == 'P') & (WM_clean['OVO RESULT'].isin(explosive_pass_results))),
    1, 0
)


