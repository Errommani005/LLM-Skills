#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a2z.py: working helpers for the galacticus-pathway skill (stdlib only, run with python -I).

    python -I a2z.py show <galaxy> <sid> [from [to]]      print units exactly as extracted (title, text, notes, tables)
    python -I a2z.py find <galaxy> <phrase> [--sid L3]     units that contain the phrase under the quote-matching rules
    python -I a2z.py plan <galaxy>                         the steps in A-to-Z order: stage, priority, minutes, refs,
                                                           lesson state, and order problems (a step before what it requires)
    python -I a2z.py bar  <galaxy> <stepId>                what the step's lesson has against the full-lesson bar, and
                                                           which card key facts the lesson does not teach yet

gxformat.py validate stays the judge; these commands only help you write. Exit 0 = ok, 1 = problems found, 2 = usage.
"""
import json
import os
import re
import sys
import unicodedata

QMAP = {ord('‘'): "'", ord('’'): "'", ord('′'): "'", ord('“'): '"', ord('”'): '"',
        ord('–'): '-', ord('—'): '-', ord('−'): '-', ord('→'): '->'}
MARKS = re.compile('[̀-ͯ]')
BAR = {'core': dict(sec=(5, 9), slides=(6, 9), inter=2, cp=(4, 5), non_mcq=1),
       'standard': dict(sec=(4, 9), slides=(4, 9), inter=1, cp=(3, 5), non_mcq=0),
       'detail': dict(sec=(3, 7), slides=(3, 7), inter=1, cp=(2, 4), non_mcq=0)}


def out(s=''):
    sys.stdout.buffer.write((s + '\n').encode('utf-8'))


def norm(s):
    s = MARKS.sub('', unicodedata.normalize('NFD', s or '')).translate(QMAP)
    return re.sub(r'\s+', ' ', s).strip().lower()


def load(path):
    with open(path, 'rb') as f:
        b = f.read()
    return json.loads(b.decode('utf-8-sig'))


def cells(t, acc):
    if isinstance(t, list):
        for x in t:
            cells(x, acc)
    elif isinstance(t, (str, int, float)) and not isinstance(t, bool):
        acc.append(str(t))
    return acc


def hay(u):
    return norm(' '.join([u.get('title') or '', u.get('text') or '', u.get('notes') or ''] + cells(u.get('tables'), [])))


def units(g, sid=None):
    d = os.path.join(g, 'sources', 'units')
    if not os.path.isdir(d):
        return []
    res = []
    for f in sorted(os.listdir(d)):
        if f.endswith('.json') and (sid is None or f[:-5] == sid):
            j = load(os.path.join(d, f))
            for u in j.get('units', []):
                res.append((j.get('id', f[:-5]), u))
    return res


def cmd_show(a):
    if len(a) < 2:
        return usage()
    g, sid = a[0], a[1]
    lo = int(a[2]) if len(a) > 2 else 1
    hi = int(a[3]) if len(a) > 3 else (lo if len(a) > 2 else 10 ** 9)
    found = 0
    for s, u in units(g, sid):
        if lo <= u.get('n', 0) <= hi:
            found += 1
            out('=== %s#%s [%s] %s' % (s, u.get('n'), u.get('textState', 'text'), u.get('title') or ''))
            if u.get('text'):
                out(u['text'])
            if u.get('notes'):
                out('NOTES: ' + u['notes'])
            for t in u.get('tables') or []:
                out('TABLE: ' + json.dumps(t, ensure_ascii=False))
    if not found:
        out('No units %s#%s..%s in %s/sources/units/.' % (sid, lo, hi, g))
        return 1
    return 0


def cmd_find(a):
    sid = None
    if '--sid' in a:
        i = a.index('--sid')
        sid = a[i + 1] if i + 1 < len(a) else None
        a = a[:i] + a[i + 2:]
    if len(a) < 2:
        return usage()
    g, phrase = a[0], norm(' '.join(a[1:]))
    hits = 0
    for s, u in units(g, sid):
        h = hay(u)
        i = h.find(phrase)
        if i >= 0:
            hits += 1
            ctx = h[max(0, i - 50):i + len(phrase) + 50]
            out('%s#%s  ...%s...' % (s, u.get('n'), ctx))
    if not hits:
        out('Not found verbatim. Shorten the phrase, or copy it from `show` (typos and punctuation count).')
        return 1
    return 0


def galaxy_parts(g):
    nodes = load(os.path.join(g, 'galaxy', 'nodes.json')).get('nodes', [])
    pw = load(os.path.join(g, 'galaxy', 'pathways.json')).get('pathways', [])
    main = next((p for p in pw if p.get('id') == 'main'), None)
    ep = os.path.join(g, 'galaxy', 'edges.json')
    edges = load(ep).get('edges', []) if os.path.exists(ep) else []
    return {n.get('id'): n for n in nodes}, main, edges


def lesson_of(g, nid):
    p = os.path.join(g, 'lessons', nid + '.json')
    return load(p) if os.path.exists(p) else None


def counts(lesson):
    gd = lesson.get('guide') or {}
    secs = gd.get('sections') or []
    slides = lesson.get('slides') or []
    cp = lesson.get('checkpoint') or []
    return dict(sec=len(secs), slides=len(slides), inter=len([s for s in slides if s.get('primitive') != 'text']),
                cp=len(cp), non_mcq=len([q for q in cp if q.get('type') != 'mcq']),
                first=secs[0].get('kind') if secs else None, last=secs[-1].get('kind') if secs else None,
                needs=len(gd.get('needs') or []), audit=bool(lesson.get('audit')))


def bar_problems(node, lesson):
    b = BAR.get(node.get('priority'), BAR['standard'])
    c = counts(lesson)
    why = []
    for k, label in (('sec', 'guide sections'), ('slides', 'slides'), ('cp', 'checkpoint questions')):
        if c[k] < b[k][0]:
            why.append('%d %s, needs %d-%d' % (c[k], label, b[k][0], b[k][1]))
        elif c[k] > b[k][1]:
            why.append('%d %s, above %d (warning)' % (c[k], label, b[k][1]))
    if c['inter'] < b['inter']:
        why.append('%d interactive slides, needs %d+' % (c['inter'], b['inter']))
    if c['non_mcq'] < b['non_mcq']:
        why.append('the checkpoint needs a question that is not mcq')
    if node.get('priority') == 'core' and c['needs'] and c['first'] != 'prereq':
        why.append('the guide must start with a prereq section')
    if node.get('priority') in ('core', 'standard') and c['last'] != 'recap':
        why.append('the guide must end with a recap section')
    return c, why


def cmd_plan(a):
    if len(a) < 1:
        return usage()
    g = a[0]
    byid, main, edges = galaxy_parts(g)
    if not main:
        out('No pathway with id "main" in galaxy/pathways.json.')
        return 1
    pos, order, problems, total = {}, [], [], 0
    for si, st in enumerate(main.get('stages') or []):
        for nid in st.get('nodeIds') or []:
            pos.setdefault(nid, len(order))
            order.append((si + 1, st.get('title', ''), nid))
    out('%d steps in %d stages' % (len(order), len(main.get('stages') or [])))
    for k, (si, stitle, nid) in enumerate(order):
        n = byid.get(nid)
        if not n:
            problems.append('stage %d lists %s, which is not in nodes.json' % (si, nid))
            continue
        total += n.get('estMin') or 0
        les = lesson_of(g, nid)
        state = 'no lesson'
        if les is not None:
            c, why = bar_problems(n, les)
            state = ('full' if not why else 'below the bar') + (' +audit' if c['audit'] else '')
        out('%2d. [stage %d] %-40s %-8s %3s min  %2d refs  %d facts  %s' % (
            k + 1, si, nid[:40], n.get('priority', '?'), n.get('estMin', '?'), len(n.get('refs') or []),
            len((n.get('card') or {}).get('keyFacts') or []), state))
    for e in edges:
        if e.get('type') == 'requires' and e.get('source') in pos and e.get('target') in pos:
            if pos[e['source']] > pos[e['target']]:
                problems.append('%s comes before %s, which it requires' % (e['target'], e['source']))
    missing = [i for i in byid if i not in pos]
    if missing:
        problems.append('steps not in the main pathway: ' + ', '.join(missing))
    if len(order) != len(set(x[2] for x in order)):
        problems.append('a step appears twice in the main pathway')
    ns = len(main.get('stages') or [])
    if not 3 <= ns <= 10:
        problems.append('%d stages: a pathway course has 3 to 10' % ns)
    out('total: %d min (%dh%02d)' % (total, total // 60, total % 60))
    for p in problems:
        out('PROBLEM: ' + p)
    return 1 if problems else 0


def lesson_text(lesson):
    acc = []

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            acc.append(v)
    walk(lesson)
    return norm(' '.join(acc))


def cmd_bar(a):
    if len(a) < 2:
        return usage()
    g, nid = a[0], a[1]
    byid, _, _ = galaxy_parts(g)
    n = byid.get(nid)
    if not n:
        out('No step %s in galaxy/nodes.json.' % nid)
        return 1
    b = BAR.get(n.get('priority'), BAR['standard'])
    out('%s (%s): guide %d-%d sections, %d-%d slides with %d+ interactive, %d-%d checkpoint questions%s' % (
        nid, n.get('priority'), b['sec'][0], b['sec'][1], b['slides'][0], b['slides'][1], b['inter'], b['cp'][0], b['cp'][1],
        ', 1+ not mcq' if b['non_mcq'] else ''))
    les = lesson_of(g, nid)
    if les is None:
        out('lessons/%s.json does not exist yet.' % nid)
        return 1
    c, why = bar_problems(n, les)
    prims = sorted(set(s.get('primitive') for s in les.get('slides') or []))
    types = sorted(set(q.get('type') for q in les.get('checkpoint') or []))
    out('has: %d sections (%s ... %s), %d slides (%d interactive: %s), %d questions (%s), audit: %s' % (
        c['sec'], c['first'], c['last'], c['slides'], c['inter'], ', '.join(p for p in prims if p), c['cp'],
        ', '.join(t for t in types if t), 'yes' if c['audit'] else 'no'))
    text = lesson_text({k: v for k, v in les.items() if k != 'audit'})
    untaught = [f for f in (n.get('card') or {}).get('keyFacts') or [] if norm(f.get('quote')) not in text]
    for f in untaught:
        out('NOT TAUGHT: key fact %s "%s"' % (f.get('ref'), f.get('quote')))
    for w in why:
        out('BELOW THE BAR: ' + w)
    if not why and not untaught:
        out('OK: meets the full-lesson bar and teaches every key fact.')
    return 1 if (why or untaught) else 0


def usage():
    out(__doc__.strip())
    return 2


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        return usage()
    cmd = {'show': cmd_show, 'find': cmd_find, 'plan': cmd_plan, 'bar': cmd_bar}.get(argv[0])
    if not cmd:
        return usage()
    try:
        return cmd(argv[1:])
    except (OSError, ValueError) as e:
        out('error: %s' % e)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
