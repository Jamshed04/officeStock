import time
import psutil
import os
import importlib
import predict_data as predict

names_to_classify = [
    'Печенье LOTTE Choco Pie бисквитное в шоколадной глазури, 336г',
    'Майонез СЛОБОДА Провансаль 67%, 800мл',
    'Лапша DOSHIRAK со вкусом курицы, 90г',
    'Чипсы картофельные SMAKKY с солью, 180г',
    'Батончик TWIX Xtra с карамелью и печеньем, 82г'
]


def run_benchmark(classification_function, data, num_runs: int = 20):
    process = psutil.Process(os.getpid())

    mem_start_bytes = process.memory_info().rss

    print("Инициализация модели и токенайзера (Первый прогон)...")
    classification_function(names_list=data)

    mem_after_load_bytes = process.memory_info().rss

    mem_usage_mb = (mem_after_load_bytes - mem_start_bytes) / (1024 * 1024)


    times = []
    cpu_usages = []

    print(f"Запуск {num_runs} прогонов для сбора статистики...")

    psutil.cpu_percent(interval=None)

    for _ in range(num_runs):
        start_time = time.perf_counter()

        classification_function(names_list=data)

        end_time = time.perf_counter()


        times.append(end_time - start_time)

    avg_time_ms = np.mean(times) * 1000


    return {
        'Memory_Model_Load_MB': round(mem_usage_mb, 2),
        'Avg_Inference_Time_ms': round(avg_time_ms, 3),
        'Names_per_run': len(data)
    }


importlib.reload(predict)
import numpy as np

benchmark_results = run_benchmark(
    classification_function=predict.classify_names,
    data=names_to_classify,
    num_runs=100
)

print("\nРЕЗУЛЬТАТЫ БЕНЧМАРКА")
print(f"1. Потребление ОЗУ (только модель и буферы): {benchmark_results['Memory_Model_Load_MB']} МБ")
print(f"2. Среднее время инференса (5 названий): {benchmark_results['Avg_Inference_Time_ms']} мс")
