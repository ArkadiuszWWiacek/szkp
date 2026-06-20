import base64
import io

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_COLORS = {
    'w_toku':     '#B8960C',
    'nowa':       '#3B6EA8',
    'zawieszona': '#9999AA',
    'zakończona': '#1A6B3A',
}
_ORDER = ['w_toku', 'nowa', 'zawieszona', 'zakończona']


def generate_case_dist_chart(cases_by_status: dict, cases_total: int) -> str:
    if not cases_total:
        return ''
    sizes = [cases_by_status.get(s, 0) for s in _ORDER]
    colors = [_COLORS[s] for s in _ORDER]
    pairs = [(sz, c) for sz, c in zip(sizes, colors) if sz > 0]
    if not pairs:
        return ''
    sizes_nz, colors_nz = zip(*pairs)
    total_nz = sum(sizes_nz)
    fig, ax = plt.subplots(figsize=(4, 4))
    _, _, autotexts = ax.pie(
        sizes_nz,
        colors=colors_nz,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(linewidth=0),
        autopct=lambda pct: str(int(round(pct * total_nz / 100))) if pct >= 3 else '',
        pctdistance=0.65,
    )
    for at in autotexts:
        at.set_fontsize(13)
        at.set_fontweight('bold')
        at.set_color('white')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
