"""Point the existing workspace at corrected DFM14 v2 population averages."""
import copy
import json
from pathlib import Path
import uuid

VIEW = '3fvncok3gjh'
OUT = Path('logs/wandb_workspace_specs/3fvncok3gjh-dfm14-v2-20261008')
DEFINITIONS = [
    ('Multilingual headline average (48 languages)', 'dfm14_multilingual_v2'),
    ('All-language average (50 languages)', 'dfm14_all_languages_v2'),
    ('New-language average (16 languages)', 'dfm14_new_languages_v2'),
]


def build(spec):
    result = copy.deepcopy(spec)
    sections = result['section']['panelBankConfig']['sections']
    headline = next(s for s in sections if s['name'] == 'Headline Averages')
    multilingual = next(s for s in sections if s['name'] == 'Multilingual Headline Metrics')
    current = next(p for p in headline['panels'] if p.get('config', {}).get('chartTitle')
                   == 'Multilingual headline average')
    existing = {m for s in sections for p in s.get('panels', [])
                for m in p.get('config', {}).get('metrics', [])}
    if any('avg_population/'+kind+'/score' in existing for _, kind in DEFINITIONS):
        raise ValueError('DFM14 v2 panels already present; inspect before changing')

    def panel(title, kind):
        p = copy.deepcopy(current)
        p['__id__'] = uuid.uuid4().hex[:16]
        p['config'].update(chartTitle=title, metrics=['avg_population/'+kind+'/score'],
                           xAxis='avg_population/epoch')
        return p

    multilingual['panels'] = [panel(*d) for d in DEFINITIONS] + multilingual['panels']
    extras = [panel(*d) for d in DEFINITIONS[1:]]
    current['config'].update(chartTitle=DEFINITIONS[0][0],
        metrics=['avg_population/dfm14_multilingual_v2/score'], xAxis='avg_population/epoch')
    index = headline['panels'].index(current)
    headline['panels'][index+1:index+1] = extras
    assert result['section']['runSets'] == spec['section']['runSets']
    return result


def main():
    import wandb
    from wandb_workspaces.workspaces import internal
    from wandb_workspaces.workspaces.internal import gql
    OUT.mkdir(parents=True, exist_ok=True)
    before = internal.get_view_dict('peter-sk-sdu', 'DFM5', VIEW)
    spec = json.loads(before['spec'])
    after = build(spec)
    for name, value in [('before-apply', before), ('intended', after)]:
        (OUT/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')
    if internal.get_view_dict('peter-sk-sdu', 'DFM5', VIEW) != before:
        raise RuntimeError('Concurrent workspace edit; refusing overwrite')
    mutation = gql('''mutation UpdateExistingView($id: ID!, $spec: String!) {
        upsertView(input: {id: $id, spec: $spec}) {view {id name} inserted}
    }''')
    wandb.Api().client.execute(mutation, {'id': before['id'], 'spec': json.dumps(after)})
    actual = internal.get_view_dict('peter-sk-sdu', 'DFM5', VIEW)
    (OUT/'after.json').write_text(json.dumps(actual, indent=2)+'\n')
    assert json.loads(actual['spec']) == after and actual['id'] == before['id']
    print('Verified: 48/50/16-language v2 panels in both sections; selections preserved.')


if __name__ == '__main__':
    main()
