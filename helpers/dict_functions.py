"Functions related to dictionary objects."
def dict_factory(cursor, row):
    "Causes SQLite3 queries to return as dictionaries."
    dict_template = {}
    for idx, col in enumerate(cursor.description):
        dict_template[col[0]] = row[idx]
    return dict_template
