window.CONFIGURATION_DATA = {
    "suites": {
        "ubuntu-latest,django": {
            "header": "Pytest Benchmarks (ubuntu-latest, django)",
            "description": "Performance benchmark tests, generated using pytest-benchmark."
        }
    },
    "groups": {
        "node": {
            "header": "Single Node",
            "description": "Comparison of basic node interactions, such as storage and retrieval from the database.",
            "single_chart": true,
            "xAxis": "id",
            "backgroundFill": false
        }
    }
}