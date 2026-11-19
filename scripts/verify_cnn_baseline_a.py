"""Read-only independent saved-evidence verification; no model or test inference."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
def main(run):
    report=ROOT/'reports'/run
    read=lambda n:json.loads((report/n).read_text(encoding='utf-8'))
    history=list(csv.DictReader((report/'training_history.csv').open(encoding='utf-8',newline='')))
    config=read('config.json'); result=read('training_result.json'); metrics=read('test_metrics.json')
    bestf=-1;bestl=float('inf');best=0;stale=0
    for epoch,row in enumerate(history,1):
        if int(row['epoch'])!=epoch or int(row['train_samples'])!=6037 or int(row['train_batches'])!=95:
            raise AssertionError('Epoch coverage')
        values=[float(row[k]) for k in ['training_loss','validation_loss','validation_accuracy','validation_macro_f1']]
        if not all(math.isfinite(x) for x in values):raise AssertionError('Nonfinite history')
        f,l=float(row['validation_macro_f1']),float(row['validation_loss'])
        update=f>bestf or (f==bestf and l<bestl)
        if update:bestf,bestl,best,stale=f,l,epoch,0
        else:stale+=1
        if ((row['updated_best']=='True')!=update or int(row['best_epoch'])!=best
                or int(row['early_stopping_count'])!=stale):raise AssertionError('Selection trace mismatch')
        if stale>=8 and epoch!=len(history):raise AssertionError('Continued after early stopping')
        if float(row['learning_rate'])!=.001:raise AssertionError('Learning rate changed')
    if best!=result['best_epoch']:raise AssertionError('Best epoch')
    if len(history)<30 and stale!=8:raise AssertionError('Early stopping')
    predictions=list(csv.DictReader((report/'test_predictions.csv').open(encoding='utf-8',newline='')))
    matrix=[[0]*6 for _ in range(6)]
    for i,row in enumerate(predictions,1):
        t,p=int(row['true_label_0based']),int(row['pred_label_0based'])
        if int(row['official_test_row_1based'])!=i or not(0<=t<6 and 0<=p<6):raise AssertionError('Prediction rows')
        matrix[t][p]+=1
    support=[sum(row) for row in matrix]
    predicted=[sum(matrix[i][j] for i in range(6)) for j in range(6)]
    precision=[matrix[i][i]/predicted[i] if predicted[i] else 0 for i in range(6)]
    recall=[matrix[i][i]/support[i] if support[i] else 0 for i in range(6)]
    f1=[2*matrix[i][i]/(support[i]+predicted[i]) if support[i]+predicted[i] else 0 for i in range(6)]
    accuracy=sum(matrix[i][i] for i in range(6))/len(predictions)
    macro=sum(f1)/6
    if len(predictions)!=2947 or matrix!=metrics['confusion_matrix']:raise AssertionError('Test matrix')
    for name,values in [('precision',precision),('recall',recall),('f1',f1),('support',support)]:
        if any(abs(a-b)>1e-14 for a,b in zip(values,metrics[name])):raise AssertionError(name)
    if abs(accuracy-metrics['accuracy'])>1e-14 or abs(macro-metrics['macro_f1'])>1e-14:
        raise AssertionError('Overall metrics')
    # Independent original-row labels from the fixed NPZ; no model computation.
    import numpy as np
    data=ROOT/'data/processed'/config['source_artifact']
    with np.load(data/'test_standardized.npz',allow_pickle=False) as d:
        if [int(row['true_label_0based']) for row in predictions]!=(d['y']-1).tolist():
            raise AssertionError('Prediction true labels differ from fixed official test')
    for path,expected in read('data_audit.json')['protected_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise AssertionError('Input changed')
    reload=read('checkpoint_reload_verification.json')
    if hashlib.sha256((ROOT/reload['checkpoint_path']).read_bytes()).hexdigest()!=reload['sha256']:
        raise AssertionError('Checkpoint changed')
    check=dict(status='PASS',selection_replayed=True,early_stopping_replayed=True,train_epoch_coverage=True,
               test_prediction_rows=2947,official_true_labels_match=True,
               confusion_and_all_metrics_independently_recomputed=True,max_allowed_metric_error=1e-14,
               protected_input_hashes_unchanged=True,checkpoint_hash_matches=True,
               model_evaluation_performed=False)
    with (report/'independent_result_verification.json').open('x',encoding='utf-8') as f:json.dump(check,f,indent=2)
    print(json.dumps(check))
if __name__=='__main__':main(sys.argv[1])
