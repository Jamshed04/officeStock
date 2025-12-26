from functools import lru_cache
from ml.predict_data import Predictor
import os

@lru_cache
def get_predictor() -> Predictor:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(ROOT, "ml_data/bert_model/rubert_tiny2_seq_class.onnx")
    tokenizer_folder = os.path.join(ROOT, "ml_data/bert_model")
    category_table_path = os.path.join(ROOT, "category_table.csv")

    return Predictor(
        model_path=model_path,
        tokenizer_folder=tokenizer_folder,
        category_table_path=category_table_path
    )
