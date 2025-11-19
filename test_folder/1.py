import importlib
import predict_data as predict

names_to_classify = [
    'Печенье LOTTE Choco Pie бисквитное в шоколадной глазури, 336г',
    'Майонез СЛОБОДА Провансаль 67%, 800мл',
    'Лапша DOSHIRAK со вкусом курицы, 90г',
    'Чипсы картофельные SMAKKY с солью, 180г',
    'Батончик TWIX Xtra с карамелью и печеньем, 82г'
]
importlib.reload(predict)
results = predict.classify_names(names_list=names_to_classify)
print(results)