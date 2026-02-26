CONFIG = {
    "app_name": "JobScout",
    "pipeline": [
        "user",
        "config_file",
        "cli",
        "rule_based_scoring",
    ],
    "input": {
        "source": "job_listings",
        "entity": "jobs",
        "fields": [
            "title",
            "salary",
            "location",
            "skills",
            "description",
        ],
    },
    "processing": {
        "step": "data_processor_formatting",
    },
    "scoring": {
        "type": "rule_based",
        "weights": {
            "title_match": 30,
            "salary_match": 20,
            "location_match": 20,
            "skills_match": 20,
            "description_match": 10,
        },
    },
    "output": {
        "format": "sorted_table",
        "sort_by": "score",
        "order": "desc",
    },
}


if __name__ == "__main__":
    from pprint import pprint

    pprint(CONFIG)