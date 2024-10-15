def get_filters(filter_categories, filter_start_date, filter_end_date):
    filters = {"operator": "AND", "conditions": []}

    if filter_start_date:
        date_condition = {
            "field": "meta.datestamp",
            "operator": ">=",
            "value": filter_start_date,
        }
        filters["conditions"].append(date_condition)

    if filter_end_date:
        date_condition = {
            "field": "meta.datestamp",
            "operator": "<=",
            "value": filter_end_date,
        }
        filters["conditions"].append(date_condition)

    if filter_categories:
        field_condition = {
            "field": "meta.categories",
            "operator": "in",
            "value": filter_categories,
        }
        filters["conditions"].append(field_condition)

    # 조건이 없으면 None 반환
    if not filters["conditions"]:
        return None

    return filters
