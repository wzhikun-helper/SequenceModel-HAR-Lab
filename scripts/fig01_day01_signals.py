"""Reproduce nine raw physical-unit channels for two fixed training examples."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from day01_audit_uci import ROOT, CHANNELS, safe, jwrite, cwrite
from day01_figure_style import paper_style, save

COLORS = paper_style()


def main(run):
    metadata_path = safe(ROOT / 'data' / 'processed' / run / 'examples' / 'example_metadata.json')
    examples = json.loads(metadata_path.read_text(encoding='utf-8'))
    output = safe(ROOT / 'outputs' / 'figures' / run)
    output.mkdir(parents=True, exist_ok=False)
    # Figure contract exists before any plot is drawn.
    contract = {'figure_id': 'fig01_day01_signals', 'backend': 'matplotlib',
                'core_claim': 'Two explicitly selected training windows expose all nine physical-unit channels without rescaling or hiding any axis.',
                'layout': 'Nine aligned small multiples per activity; all channels required by the audit task.',
                'hero_panel': 'Full channel stack, with body_acc_x as entry point; equal channel visibility is intentional for schema inspection.',
                'source_data': [e['source_csv'] for e in examples], 'export': ['png', 'pdf', 'svg'],
                'sampling_hz': 50, 'time_axis': 't = sample_index / 50; 0..2.54 s; acquisition window duration 2.56 s',
                'uncertainty': 'Not applicable: n=1 observed window per activity, no mean or inferred population claim. No invented CI.',
                'scales': 'Matching per-channel y limits across activities; g and rad/s never share a y-axis.',
                'selection': 'Activities fixed as WALKING and STANDING; first matching window from final training set.',
                'skill_limitations': 'Bundled paperfig package and scripts/critique.py are absent; local explicit style/export and independent artifact checks replace them, not claimed as the bundled gate.'}
    jwrite(output / 'figure_contract.json', contract)
    frames = [np.genfromtxt(safe(ROOT / e['source_csv']), delimiter=',', names=True) for e in examples]
    limits = {}
    for channel in CHANNELS:
        minimum = min(float(frame[channel].min()) for frame in frames)
        maximum = max(float(frame[channel].max()) for frame in frames)
        margin = max((maximum - minimum) * 0.09, 1e-5)
        limits[channel] = (minimum - margin, maximum + margin)
    manifest = []
    for example, frame, color in zip(examples, frames, COLORS):
        fig, axes = plt.subplots(9, 1, figsize=(8.2, 11.5), sharex=True)
        fig.subplots_adjust(left=0.17, right=0.965, bottom=0.075, top=0.88, hspace=0.25)
        fig.suptitle(example['activity_name'], x=0.17, y=0.97, ha='left', fontsize=17, fontweight='bold')
        fig.text(0.17, 0.935,
                 f"Subject {example['subject_id']}  |  official train row {example['official_row_1based']}  |  final train",
                 fontsize=10)
        fig.text(0.17, 0.911, 'n = 1 observed window  |  128 samples x 9 channels  |  50 Hz  |  2.56 s window', fontsize=9)
        for index, (ax, channel) in enumerate(zip(axes, CHANNELS)):
            ax.plot(frame['time_s'], frame[channel], color=color, linestyle='-',
                    marker='o', markevery=16, markersize=2.2)
            unit = 'rad/s' if 'gyro' in channel else 'g'
            ax.set_ylabel(f'{channel}\n({unit})', rotation=0, ha='right', va='center', labelpad=10)
            ax.set_ylim(*limits[channel])
            ax.set_xlim(0, 2.56)
            ax.set_xticks(np.arange(0, 2.51, 0.5))
            ax.yaxis.set_major_locator(plt.MaxNLocator(3))
            ax.tick_params(axis='both', length=3, width=0.6)
            if index < 8:
                ax.tick_params(axis='x', bottom=False)
        axes[-1].set_xlabel('Time within window (s)')
        fig.text(0.17, 0.02, 'Original physical units; no per-window rescaling. Matching y limits across the two activities.\n'
                 'One observed window; uncertainty intervals do not apply. Source: UCI HAR (Reyes-Ortiz et al.).', fontsize=8)
        name = 'fig01_' + example['activity_name'].lower() + '_nine_channels'
        for path in save(fig, output / name):
            manifest.append({'figure_id': name, 'path': path.relative_to(ROOT).as_posix(),
                             'activity': example['activity_name'], 'subject_id': example['subject_id'],
                             'source_data': example['source_csv'], 'generation_script': 'scripts/fig01_day01_signals.py',
                             'claim': contract['core_claim']})
        plt.close(fig)
    cwrite(output / 'figure_manifest.csv', list(manifest[0]), manifest)
    print('Saved 2 activity figures in PNG/PDF/SVG: ' + output.relative_to(ROOT).as_posix(), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run')
    main(parser.parse_args().run)
