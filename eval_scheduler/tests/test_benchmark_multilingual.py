import json

from eval_scheduler.benchmark_multilingual import summarize


def test_telemetry_tracks_each_server_lifetime_and_active_window(tmp_path):
    path = tmp_path / 'telemetry.jsonl'
    rows = []
    for pid, count, active in [(10, 2, 1), (10, 5, 0), (20, 3, 1)]:
        rows.append({'gpus': {'0': {'utilization': 80 if active else 0}},
                     'servers': {'0': {'pid': pid, 'values': {
                         'vllm:request_success_total': count,
                         'vllm:num_requests_running': active,
                         'vllm:kv_cache_usage_perc': .5}}}})
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    result = summarize(path, 60)
    assert result['requests_per_wall_minute'] == 8
    assert result['windows']['inference_active']['samples'] == 2
    assert result['windows']['inference_active']['gpu_mean_utilization']['0'] == 80
    assert result['windows']['whole_campaign']['mean_kv_percent'] == 50
