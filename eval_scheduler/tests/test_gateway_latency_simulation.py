import asyncio
import json
import pytest

from eval_scheduler.gateway_latency_simulation import distribution, sample_profile, simulate


def test_profiles_are_reproducible_and_long_tailed():
    short = [sample_profile(i)[0] for i in range(0, 10000, 2)]
    long = [sample_profile(i)[0] for i in range(1, 10000, 2)]
    assert sample_profile(91) == sample_profile(91)
    assert distribution(long)['mean'] > 4 * distribution(short)['mean']
    assert distribution(long)['p99'] > 4 * distribution(long)['p50']
    assert all(.1 <= v <= 90 for v in short + long)


@pytest.mark.parametrize('scheduler', [False, True])
def test_sleeping_campaign_recovers_transport_errors(tmp_path, scheduler):
    result = asyncio.run(simulate(tmp_path, jobs=4, rows=50, active_jobs=4, slots=8, scale=.01, scheduler=scheduler))
    assert result['passed']
    assert result['rows_completed'] == 200
    assert result['retries']['502'] > 0
    assert len(result['requests_per_backend']) == 8
    assert max(result['peak_active_per_backend'].values()) <= 8
    assert result['duplicate_completed_responses'] == 0
    assert result['pending_client_tasks'] == 0
    assert json.loads((tmp_path/'result.json').read_text())['passed']
    if scheduler:
        assert result['coordinator'] == {'outcome': 'done', 'states': {'done': 5}, 'cpu_cores_released': True}
