# ml/predict_data.py
import numpy as np
import onnxruntime
import re
import os
from transformers import AutoTokenizer
from typing import List, Dict, Union
import pandas as pd
import nltk
import threading

class Predictor:
    def __init__(
        self,
        model_path: str,
        tokenizer_folder: str,
        category_table_path: str,
        max_length: int = 32
    ):
        self.model_path = model_path
        self.tokenizer_folder = tokenizer_folder
        self.category_table_path = category_table_path
        self.category_df = pd.read_csv(self.category_table_path)
        self.max_length = max_length

        # Загрузка токенизатора
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_folder)
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки токенизатора из {tokenizer_folder}: {e}")

        # Загрузка модели
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ONNX модель не найдена по пути {self.model_path}")
        self.session = onnxruntime.InferenceSession(self.model_path)

        # Загрузка стоп-слов
        self.stop_words = self._load_russian_stopwords()

    def _load_russian_stopwords(self, timeout_seconds: float = 3.0) -> Union[set, None]:
        result = {'stop_words': None}

        def download_task():
            nonlocal result
            try:
                result['stop_words'] = set(nltk.corpus.stopwords.words('russian'))
            except LookupError:
                try:
                    nltk.download('stopwords', quiet=True)
                    result['stop_words'] = set(nltk.corpus.stopwords.words('russian'))
                except Exception:
                    pass

        download_thread = threading.Thread(target=download_task)
        download_thread.start()
        download_thread.join(timeout=timeout_seconds)

        if download_thread.is_alive():
            print(f"NLTK download timed out after {timeout_seconds}s.")
            return None

        if result['stop_words'] is None:
            print("NLTK download failed.")
            return None

        return result['stop_words']

    def _preprocess(self, texts: List[str]) -> List[str]:
        processed = list(texts)
        for i, text in enumerate(processed):
            text = re.sub(r"«.*»", "", text)
            text = re.sub(r"([(][^)]+[)])|([\d]+\s?[в]\s?[\d+]|[№][\d]+)", "", text)
            text = re.sub(r"([\d]+[.,]?[\d]+[%])|([\d]+[%])|(\d+[+])", "", text)
            text = re.sub(r"\b\d+\s?(г|гр|гр\.|мл|л|шт|уп|пакет|%)\b", "", text, flags=re.IGNORECASE)
            text = re.sub(r"[ ]{2,}", " ", text)
            if self.stop_words:
                words = [w for w in text.lower().split() if w not in self.stop_words]
                text = " ".join(words)
            processed[i] = text.strip()
        return processed

    def _tokenize(self, texts: List[str]) -> Dict[str, np.ndarray]:
        encoded = self.tokenizer(
            texts,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='np'
        )
        return {
            'input_ids': encoded['input_ids'].astype(np.int64),
            'attention_mask': encoded['attention_mask'].astype(np.int64)
        }

    def _get_category_by_id(self, id: int) -> str:
        try:
            return self.category_df.loc[
            self.category_df['Номер категории'] == id,
            'Категория'
        ].values[0]
        except FileNotFoundError:
            return "Файл 'category_table.csv' не найден."
        except IndexError:
            return "ID категории не найден в таблице."
        except Exception as e:
            return f"Ошибка при получении категории: {e}"

    def predict(self, names: List[str]) -> Dict[str, List[Union[int, str]]]:
        if not names:
            return {}

        processed = self._preprocess(names)
        tokenized = self._tokenize(processed)

        input_feed = {
            'input_ids': tokenized['input_ids'],
            'attention_mask': tokenized['attention_mask']
        }

        logits = self.session.run(None, input_feed)[0]
        predictions = np.argmax(logits, axis=1).tolist()

        results = {}
        for name, cat_id in zip(names, predictions):
            results[name] = [cat_id, self._get_category_by_id(cat_id)]

        return results
