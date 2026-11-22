"""Reuse independent saved-prediction verifier; add Transformer-specific contracts."""
import json
from pathlib import Path
import sys
import numpy as np
import torch

from verify_gru_baseline import verify as verify_saved_classification

ROOT=Path(__file__).resolve().parents[1]


def main(run):
    report=ROOT/'reports'/run
    read=lambda n:json.loads((report/n).read_text(encoding='utf-8'))
    config=read('config.json')
    expected=dict(d_model=64,nhead=4,num_layers=1,dim_feedforward=128,activation='ReLU',
                  dropout=0.0,batch_first=True,norm_first=False,positional_trainable=False,
                  positional_max_length=128,pooling='time mean',final_encoder_norm=None,input_scaling=None)
    assert all(config[k]==v for k,v in expected.items())
    summary=read('model_summary.json')
    assert summary['actual_parameters']==34502==sum(item['numel'] for item in summary['parameters'].values())
    assert summary['position_buffer_shape']==[1,128,64]
    assert 'position.encoding' not in summary['parameters']
    assert summary['buffers']['position.encoding']==dict(shape=[1,128,64],numel=8192,requires_grad=False)
    check=read('integrated_preflight.json')
    assert check['status']=='PASS' and check['batches']>=2
    assert check['position_buffer_unchanged'] and check['reload_max_abs_difference']==0
    assert read('training_result.json')['formal_initialization_matches_precheck_initial']
    reload=read('checkpoint_reload_verification.json')
    assert reload['best_max_abs_difference']==reload['last_max_abs_difference']==0
    assert reload['validation_replay_exact']
    verify_saved_classification(run)
    position=np.arange(128,dtype=np.float64)[:,None]
    scale=np.exp(np.arange(0,64,2,dtype=np.float64)*(-np.log(10000.0)/64))
    expected_encoding=np.zeros((1,128,64),dtype=np.float64)
    expected_encoding[0,:,0::2]=np.sin(position*scale)
    expected_encoding[0,:,1::2]=np.cos(position*scale)
    buffer_checks={}
    for kind in ['best','last']:
        path=ROOT/reload['checkpoints'][kind]['path']
        state=torch.load(path,map_location='cpu',weights_only=True)['state_dict']
        actual=state['position.encoding'].numpy()
        difference=float(np.max(np.abs(actual-expected_encoding)))
        assert np.allclose(actual,expected_encoding,atol=1e-5,rtol=0)
        buffer_checks[kind]=dict(max_abs_error_vs_float64_formula=difference,atol=1e-5)
    with (report/'transformer_contract_verification.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(status='PASS',fixed_position_buffer_nontrainable=True,
                  exact_approved_architecture_and_parameter_count=True,
                  preflight_and_best_last_reload_exact=True,
                  formal_initialization_signature_matches_seed42_initial=True,
                  shared_saved_classification_verifier_used=True,
                  checkpoint_position_buffer_checks=buffer_checks,model_inference_performed=False),stream,indent=2)
    print('TRANSFORMER CONTRACT PASS; no additional model inference or test evaluation')


if __name__=='__main__':main(sys.argv[1])
