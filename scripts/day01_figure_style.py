"""Local reproducible style; bundled Icarus paperfig helpers are unavailable."""
from pathlib import Path
import matplotlib as mpl


def paper_style():
    mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.titlesize': 10, 'axes.labelsize': 9,
                         'xtick.labelsize': 8, 'ytick.labelsize': 8,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.linewidth': 0.6, 'lines.linewidth': 1.15,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42,
                         'figure.facecolor': 'white', 'savefig.facecolor': 'white',
                         'savefig.dpi': 300, 'axes.unicode_minus': False})
    return ['#0072B2', '#D55E00']


def save(fig, stem):
    paths = []
    for extension in ['png', 'pdf', 'svg']:
        path = Path(str(stem) + '.' + extension)
        with path.open('xb') as stream:
            fig.savefig(stream, format=extension, dpi=300)
        paths.append(path)
    return paths
