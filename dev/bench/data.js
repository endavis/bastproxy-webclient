window.BENCHMARK_DATA = {
  "lastUpdate": 1795807100860,
  "repoUrl": "https://github.com/endavis/bastproxy-webclient",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "6662995+endavis@users.noreply.github.com",
            "name": "Eric Davis",
            "username": "endavis"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "d09b6fdbf3de8faf18aedd329345c2c7d9995249",
          "message": "Initial commit",
          "timestamp": "2026-11-27T19:17:40Z",
          "tree_id": "c3eb2a734144931e6a626c96f5b1dc03ddf4aa25",
          "url": "https://github.com/endavis/bastproxy-webclient/commit/d09b6fdbf3de8faf18aedd329345c2c7d9995249"
        },
        "date": 1795807100396,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 8100329.876560538,
            "unit": "iter/sec",
            "range": "stddev: 1.5357125128300484e-8",
            "extra": "mean: 123.45176248854295 nsec\nrounds: 83036"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 8197921.272985117,
            "unit": "iter/sec",
            "range": "stddev: 1.2454026151247692e-8",
            "extra": "mean: 121.98214238716018 nsec\nrounds: 85092"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 5219778.47646747,
            "unit": "iter/sec",
            "range": "stddev: 3.5608331338227555e-8",
            "extra": "mean: 191.57901135236654 nsec\nrounds: 56552"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2102649.2569203484,
            "unit": "iter/sec",
            "range": "stddev: 7.842835556175278e-8",
            "extra": "mean: 475.59049456715053 nsec\nrounds: 199243"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 456890.52828623995,
            "unit": "iter/sec",
            "range": "stddev: 2.2956450473778452e-7",
            "extra": "mean: 2.188708099839409 usec\nrounds: 47396"
          }
        ]
      }
    ]
  }
}