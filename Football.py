import pandas as pd # type: ignore
from collections import defaultdict

RU_data = pd.read_csv('RU_data.csv')
RU_data.shape

RU_clean = RU_data.drop(columns=[' .1', 'S1', 'S2', 'S3', 'S4', 'V', 'L', 'PRAC DRILL', 'JERSEY #', 'PLAY CALL', 
                            'REC#', 'PLAY RESULT', 'FORM FAM', 'FIB', 'TAPE LABELS'])

RU_clean['GAIN'].value_counts()
RU_clean = RU_clean[RU_clean['DN'] != ' ']
RU_clean['DN'] = pd.to_numeric(RU_clean['DN'])
RU_clean = RU_clean[RU_clean['GAIN'] != ' ']
RU_clean['GAIN'] = pd.to_numeric(RU_clean['GAIN'])
RU_clean = RU_clean[RU_clean['DIST'] != ' ']
RU_clean['DIST'] = pd.to_numeric(RU_clean['DIST'])
RU_clean = RU_clean[RU_clean['OVO CONCEPT'] != ' ']
# Define your key defensive columns
defensive_cols = ['BLITZ', 'FRONT', 'RUSHERS', 'STUNT', 'COVERAGE']

# Drop rows where ALL defensive columns are either NaN or just blank/whitespace,
# but ALWAYS KEEP concepts that start with 'GREEN' (case-insensitive)
has_any_def_info = RU_clean[defensive_cols].apply(
    lambda row: any(pd.notna(val) and str(val).strip() != '' for val in row),
    axis=1
)
is_green_concept = RU_clean['OVO CONCEPT'].astype(str).str.strip().str.upper().str.startswith('GREEN')
RU_clean = RU_clean[has_any_def_info | is_green_concept]


# After initial cleaning:
RU_clean['Is_Successful'] = (
    (
        (RU_clean['R/P'] == 'R') & (
            ((RU_clean['DN'] == 1) & ((RU_clean['GAIN'] >= 4) | (RU_clean['GAIN'] >= RU_clean['DIST']))) |
            ((RU_clean['DN'] == 2) & (RU_clean['GAIN'] >= RU_clean['DIST'] / 2)) |
            ((RU_clean['DN'].isin([3, 4])) & (RU_clean['GAIN'] >= RU_clean['DIST']))
        )
    )
    |
    (
        (RU_clean['R/P'] == 'P') &
        (RU_clean['GAIN'] > 0)
    )
).astype(int)

RU_clean['Is_Explosive'] = (
    ((RU_clean['R/P'] == 'R') & (RU_clean['GAIN'] >= 10))
    | ((RU_clean['R/P'] == 'P') & (RU_clean['GAIN'] >= 15))
).astype(int)

def make_indented_concept_options(concepts):
    groups = defaultdict(list)

    for c in concepts:
        if not isinstance(c, str) or not c.strip():
            continue

        parts = c.split('/')
        prefix = '/'.join(parts[:2]) if len(parts) >= 2 else c
        groups[prefix].append(c)

    options = []

    for prefix in sorted(groups):
        # Add a disabled group header
        options.append({'label': prefix, 'value': prefix, 'disabled': True})

        # Add all child concepts (allow the prefix itself if it's alone)
        for play in sorted(groups[prefix]):
            if play == prefix and len(groups[prefix]) > 1:
                continue
            label = f'  {play}' if play != prefix else play
            options.append({'label': label, 'value': play})

    return options


# Build coverage/concept breakdowns and per-down data_sources
coverage_counts = RU_clean['COVERAGE'].value_counts().reset_index()
coverage_counts.columns = ['COVERAGE', 'Coverage Count']
coverage_counts['Coverage %'] = (coverage_counts['Coverage Count'] / len(RU_clean)) * 100
coverage_eff = RU_clean.groupby('COVERAGE')['Is_Successful'].mean().reset_index()
coverage_eff.columns = ['COVERAGE', 'Success Rate']
coverage_eff['Success Rate'] *= 100
coverage_breakdown = coverage_counts.merge(coverage_eff, on='COVERAGE', how='left')
coverage_breakdown = coverage_breakdown.sort_values(by='Coverage Count', ascending=False)

#group by concept type
concept_counts = RU_clean['OVO CONCEPT'].value_counts().reset_index()
concept_counts.columns = ['OVO CONCEPT', 'Concept Count']
concept_counts['Concept %'] = (concept_counts['Concept Count'] / len(RU_clean)) * 100

concept_eff = RU_clean.groupby('OVO CONCEPT')['Is_Successful'].mean().reset_index()
concept_eff.columns = ['OVO CONCEPT', 'Success Rate']
concept_eff['Success Rate'] *= 100

concept_breakdown = concept_counts.merge(concept_eff, on='OVO CONCEPT', how='left')
concept_breakdown = concept_breakdown.sort_values(by='Concept Count', ascending=False)


#tendencies data
RU_tendencies = RU_clean[RU_clean['DN'].isin([1, 2, 3, 4])]
first = RU_tendencies[RU_tendencies['DN'] == 1]
second = RU_tendencies[RU_tendencies['DN'] == 2]
third = RU_tendencies[RU_tendencies['DN'] == 3]
fourth = RU_tendencies[RU_tendencies['DN'] == 4]

data_sources = {
    "First": first,
    "Second": second,
    "Third": third,
    "Fourth": fourth
}

#First Down
firstd_counts = first['OVO CONCEPT'].value_counts().reset_index()
firstd_counts.columns = ['OVO CONCEPT', '1st Down Count']
firstd_counts['1st Down %'] = (firstd_counts['1st Down Count'] / len(first)) * 100
efficiency_first = first.groupby('OVO CONCEPT')['Is_Successful'].mean().reset_index()
efficiency_first.columns = ['OVO CONCEPT', 'Efficiency %']
efficiency_first['Efficiency %'] *= 100
firstd_counts = firstd_counts.merge(efficiency_first, on='OVO CONCEPT', how='left')

#Second Down
sd_counts = second['OVO CONCEPT'].value_counts().reset_index()
sd_counts.columns = ['OVO CONCEPT', '2nd Down Count']
sd_counts['2nd Down %'] = (sd_counts['2nd Down Count'] / len(second)) * 100
efficiency_s = second.groupby('OVO CONCEPT')['Is_Successful'].mean().reset_index()
efficiency_s.columns = ['OVO CONCEPT', 'Efficiency %']
efficiency_s['Efficiency %'] *= 100
sd_counts = sd_counts.merge(efficiency_s, on='OVO CONCEPT', how='left')


#Third Down
td_counts = third['OVO CONCEPT'].value_counts().reset_index()
td_counts.columns = ['OVO CONCEPT', '3rd Down Count']
td_counts['3rd Down %'] = (td_counts['3rd Down Count'] / len(third)) * 100
efficiency = third.groupby('OVO CONCEPT')['Is_Successful'].mean().reset_index()
efficiency.columns = ['OVO CONCEPT', 'Efficiency %']
efficiency['Efficiency %'] *= 100
td_counts = td_counts.merge(efficiency, on='OVO CONCEPT', how='left')


#Fourth Down
fourthd_counts = fourth['OVO CONCEPT'].value_counts().reset_index()
fourthd_counts.columns = ['OVO CONCEPT', '4th Down Count']
fourthd_counts['4th Down %'] = (fourthd_counts['4th Down Count'] / len(fourth)) * 100
efficiency_fourth = fourth.groupby('OVO CONCEPT')['Is_Successful'].mean().reset_index()
efficiency_fourth.columns = ['OVO CONCEPT', 'Efficiency %']
efficiency_fourth['Efficiency %'] *= 100
fourthd_counts = fourthd_counts.merge(efficiency_fourth, on='OVO CONCEPT', how='left')


tendency_breakdowns = {
    "First Down Tendencies": firstd_counts,
    "Second Down Tendencies": sd_counts,
    "Third Down Tendencies": td_counts,
    "Fourth Down Tendencies": fourthd_counts
}
