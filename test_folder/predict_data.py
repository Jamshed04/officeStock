#%%
import numpy as np
import onnxruntime
import re
import os.path
from transformers import AutoTokenizer
import threading
from typing import List, Dict, Optional, Set, Union
import nltk
#%%
def get_russian_stopwords_with_timeout(timeout_seconds: float = 3.0) -> Optional[Set[str]]:
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


def classify_names(names_list: List[str], max_length: int = 32):


    ONNX_FILE = "rubert_tiny2_seq_class.onnx"
    TOKENIZER_FOLDER = 'ml_data/bert_model'

    try:
        nltk.download('stopwords', quiet=True)
        stop_words = set(nltk.corpus.stopwords.words('russian'))
    except Exception:
        stop_words = None

    def preprocess_inputs(names: List[str]) -> List[str]:
        processed_names = list(names)
        for i, name in enumerate(processed_names):
            text = name
            text = re.sub(r"«.*»", "", text)
            text = re.sub(r"([(][^)]+[)])|([\d]+\s?[в]\s?[\d+]|[№][\d]+)", "", text)
            text = re.sub(r"([\d]+[.,]?[\d]+[%])|([\d]+[%])|(\d+[+])", "", text)
            text = re.sub(r"\b\d+\s?(г|гр|гр\.|мл|л|шт|уп|пакет|%)\b", "", text, flags=re.IGNORECASE)
            text = re.sub(r"[ ]{2,}", " ", text)
            if stop_words is not None:
                words = [w for w in text.lower().split() if w not in stop_words]
                text = " ".join(words)
            processed_names[i] = text.strip()
        return processed_names

    new_names_list = preprocess_inputs(names_list)

    try:
        tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_FOLDER)
    except Exception as e:
        print(f"Ошибка загрузки токенайзера из {TOKENIZER_FOLDER}. {e}")
        return None, new_names_list

    def tokenize_inputs(texts: List[str]) -> Dict[str, np.ndarray]:
        encoded_inputs = tokenizer(
            texts,
            truncation=True,
            padding='max_length',
            max_length=max_length,
            return_tensors='np'
        )
        input_ids = encoded_inputs['input_ids'].astype(np.int64)
        attention_mask = encoded_inputs['attention_mask'].astype(np.int64)
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask
        }

    tokenized_data = tokenize_inputs(new_names_list)
    path = os.path.join(TOKENIZER_FOLDER, ONNX_FILE)
    try:
        session = onnxruntime.InferenceSession(path)
    except onnxruntime as e:
        print(f"Ошибка загрузки ONNX модели из {path}. {e}")
        return None, new_names_list

    input_feed = {
        'input_ids': tokenized_data['input_ids'],
        'attention_mask': tokenized_data['attention_mask']
    }

    raw_outputs = session.run(None, input_feed)
    logits = raw_outputs[0]
    predictions = np.argmax(logits, axis=1).tolist()

    def get_category_by_id(id: int) -> str:
        import pandas as pd
        try:
            df = pd.read_csv('category_table.csv')
            name = df.loc[df['Номер категории'] == id]['Категория'].tolist()[0]
            return name
        except FileNotFoundError:
            return "Файл 'category_table.csv' не найден."
        except IndexError:
            return "ID категории не найден в таблице."
        except Exception as e:
            return f"Ошибка при получении категории: {e}"

    def format_classification_results(names_list: List[str], predictions: List[int]) -> Dict[
        str, List[Union[int, str]]]:
        results: Dict[str, List[Union[int, str]]] = {}

        for name, category_id in zip(names_list, predictions):
            category_name = get_category_by_id(category_id)
            results[name] = [category_id, category_name]

        return results

    results = format_classification_results(names_list, predictions)

    return results
