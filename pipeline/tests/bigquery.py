from pipeline.bigquery import get_table_id_for_model
from pipeline.netfile.models import get_model_classes


def test_get_table_id_for_model():
    for model in get_model_classes():
        assert get_table_id_for_model(model)
