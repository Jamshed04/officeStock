from typing import List, Dict, Union

import matplotlib.pyplot as plt


def extract_metrics(log_history: List[Dict]) -> Dict[str, Union[List, List[float]]]:
    train_steps = []
    train_losses = []

    eval_epochs = []
    eval_losses = []
    eval_accuracy = []

    other_eval_metrics = {}

    for log in log_history:

        if 'loss' in log and 'step' in log and 'eval_loss' not in log:
            train_steps.append(log['step'])
            train_losses.append(log['loss'])



        elif 'eval_loss' in log and 'epoch' in log:
            epoch = log['epoch']
            eval_epochs.append(epoch)
            eval_losses.append(log['eval_loss'])

            if 'eval_accuracy' in log:
                eval_accuracy.append(log['eval_accuracy'])

            for key, value in log.items():
                if key.startswith('eval_') and key not in ['eval_loss', 'eval_accuracy']:

                    metric_name = key.replace('eval_', '')
                    if metric_name not in other_eval_metrics:
                        other_eval_metrics[metric_name] = []

                    other_eval_metrics[metric_name].append(value)

    results = {
        'train_steps': train_steps,
        'train_losses': train_losses,
        'eval_epochs': [int(e) for e in eval_epochs],
        'eval_losses': eval_losses,
        'eval_accuracy': eval_accuracy,
    }

    results.update(other_eval_metrics)

    return results


def collect_validation_metrics(log_history):
    validation_metrics = []

    for log in log_history:
        if 'eval_loss' in log:

            cleaned_metrics = {
                key.replace('eval_', ''): value
                for key, value in log.items() if key.startswith('eval_')
            }

            if 'epoch' in log:
                cleaned_metrics['epoch'] = log['epoch']

            validation_metrics.append(cleaned_metrics)

    return validation_metrics


def plot_metrics(metrics: Dict):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    ax1.plot(metrics['train_steps'], metrics['train_losses'], label='Train Loss (Steps)', alpha=0.6, color='blue')

    ax1.plot(
        [e * (metrics['train_steps'][-1] / metrics['eval_epochs'][-1]) for e in metrics['eval_epochs']],
        metrics['eval_losses'],
        label='Validation Loss (Epochs)',
        marker='o',
        linestyle='--',
        color='red'
    )

    ax1.set_title('Training and Validation Loss')
    ax1.set_xlabel('Steps')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True, linestyle=':', alpha=0.6)

    ax2.plot(
        metrics['eval_epochs'],
        metrics['eval_accuracy'],
        label='Validation Accuracy',
        marker='o',
        linestyle='-',
        color='green'
    )

    ax2.set_xticks(metrics['eval_epochs'])
    ax2.set_title('Validation Accuracy over Epochs')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.legend()
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.show()
