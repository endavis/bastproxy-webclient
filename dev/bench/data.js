window.BENCHMARK_DATA = {
  "lastUpdate": 1795807843156,
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
      },
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
          "id": "1c34e3cb20c0861440f81e238cd4360cebef314d",
          "message": "chore: configure the project from the template placeholders (merges PR #6, addresses #5)\n\nRun the template's configure step with this project's values: project\nbastproxy-webclient, package bastproxy_webclient, description \"A web\nclient for bastproxy\", author Bast, GitHub user endavis. This fills the\nplaceholders, renames src/package_name to src/bastproxy_webclient, moves\nREADME.template.md onto README.md and records the values in\n.config/pyproject_template/settings.toml. CODEOWNERS, which configure\nleaves alone, now names endavis instead of the @username placeholder.\n\nThe template management suite stays, so template sync keeps working.\n\nAddresses #5\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T19:30:07Z",
          "tree_id": "20ef89109878eb727ffe801842930bfdd585e38a",
          "url": "https://github.com/endavis/bastproxy-webclient/commit/1c34e3cb20c0861440f81e238cd4360cebef314d"
        },
        "date": 1795807842586,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 7976706.44592322,
            "unit": "iter/sec",
            "range": "stddev: 1.0825234487578483e-8",
            "extra": "mean: 125.36502462254776 nsec\nrounds: 83459"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 8357235.175249649,
            "unit": "iter/sec",
            "range": "stddev: 1.0462384488958664e-8",
            "extra": "mean: 119.65679785601198 nsec\nrounds: 87482"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 5457756.3920481745,
            "unit": "iter/sec",
            "range": "stddev: 1.357435352556596e-8",
            "extra": "mean: 183.22547365012056 nsec\nrounds: 56202"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2059408.58342418,
            "unit": "iter/sec",
            "range": "stddev: 6.448349842252064e-8",
            "extra": "mean: 485.57629993815954 nsec\nrounds: 199243"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 452273.7520295903,
            "unit": "iter/sec",
            "range": "stddev: 1.9907092665529327e-7",
            "extra": "mean: 2.211050266597329 usec\nrounds: 47825"
          }
        ]
      }
    ]
  }
}