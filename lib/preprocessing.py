import pandas as pd
from tqdm import tqdm
import re
import nltk
from nltk.corpus import stopwords
from contextlib import redirect_stdout
import os
import config.settings as settings

root_path = settings.ROOT_DIR


def preprocess_names_list(names_list: list) -> list:
    nltk.download('stopwords', download_dir=root_path / 'lib/nltk_data')
    stop_words = set(stopwords.words('russian'))
    for i, name in tqdm(enumerate(names_list), total=len(names_list)):
        name = names_list[i]
        text = name
        text = re.sub(r"«.*»", "", text)
        text = re.sub(r"([(][^)]+[)])|([\d]+\s?[в]\s?[\d+]|[№][\d]+)", "", text)
        text = re.sub(r"([\d]+[.,]?[\d]+[%])|([\d]+[%])|(\d+[+])", "", text)
        text = re.sub(r"\b\d+\s?(г|гр|гр\.|мл|л|шт|уп|пакет|%)\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"[ ]{2,}", " ", text)
        words = [w for w in text.lower().split() if w not in stop_words]
        text = " ".join(words)
        names_list[i] = text
    return names_list


def preprocess_categories_list(names_list: list) -> list:
    with redirect_stdout(open(os.devnull, "w")):
        nltk.download('stopwords')
    nltk.download('stopwords', quiet=True, halt_on_error=False)
    stop_words = set(stopwords.words('russian'))
    for item in names_list:
        for i in range(len(item)):
            name = item[i]
            text = name
            text = re.sub(r"«.*»", "", text)
            text = re.sub(r"([(][^)]+[)])|([\d]+\s?[в]\s?[\d+]|[№][\d]+)", "", text)
            text = re.sub(r"([\d]+[.,]?[\d]+[%])|([\d]+[%])|(\d+[+])", "", text)
            text = re.sub(r"\b\d+\s?(г|гр|гр\.|мл|л|шт|уп|пакет|%)\b", "", text, flags=re.IGNORECASE)
            words = [w for w in text.lower().split() if w not in stop_words]
            text = " ".join(words)
            item[i] = text
    return names_list


def return_categories_list(cat_df: pd.DataFrame) -> list:
    categories = [cat_df.loc[x].dropna().tolist() for x in range(len(cat_df))]
    categories = [lst[:1] + lst[2:] for lst in categories]
    return categories
