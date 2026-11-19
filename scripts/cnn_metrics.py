"""Fixed six-class single-label metrics, confusion rows=true, columns=predicted."""
import numpy as np


def classification_metrics(y_true, y_pred):
    true, pred = np.asarray(y_true), np.asarray(y_pred)
    if (true.ndim != 1 or pred.shape != true.shape or true.size == 0
            or not np.issubdtype(true.dtype, np.integer)
            or not np.issubdtype(pred.dtype, np.integer)
            or ((true < 0) | (true > 5) | (pred < 0) | (pred > 5)).any()):
        raise ValueError('Expected nonempty equal-length integer labels in 0..5')
    cm = np.bincount(true * 6 + pred, minlength=36).reshape(6, 6)
    tp = np.diag(cm).astype(np.float64)
    support, predicted = cm.sum(1), cm.sum(0)
    precision = np.divide(tp, predicted, out=np.zeros(6), where=predicted != 0)
    recall = np.divide(tp, support, out=np.zeros(6), where=support != 0)
    f1 = np.divide(2 * tp, support + predicted, out=np.zeros(6), where=(support + predicted) != 0)
    return {'n': int(true.size), 'accuracy': float(tp.sum() / true.size),
            'macro_f1': float(f1.mean()), 'precision': precision.tolist(),
            'recall': recall.tolist(), 'f1': f1.tolist(), 'support': support.tolist(),
            'confusion_matrix': cm.tolist(), 'zero_division': 0,
            'macro_classes': list(range(6)), 'confusion_orientation': 'rows=true, columns=predicted'}


def improves(f1, loss, best_f1, best_loss):
    return f1 > best_f1 or (f1 == best_f1 and loss < best_loss)
