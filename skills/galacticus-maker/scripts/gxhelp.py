#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gxhelp.py: working helpers for the galacticus-maker pipeline (references/pipeline.md).

    python -I gxhelp.py show     <galaxy> <sid> [from [to]]        print units, exactly as extracted
    python -I gxhelp.py find     <galaxy> <phrase> [--sid L1]       where does this phrase occur (quote matching rules)
    python -I gxhelp.py nodes    <job>                              notes/nodes/*.json -> gx/galaxy/nodes.json
    python -I gxhelp.py coverage <job>                              notes/inventory/*.json + node refs -> gx/ledger/coverage.json
    python -I gxhelp.py order    <galaxy> --sources L1,T1,L2 [--closure id,id]
                                                                    main-pathway order, deviations, stage hints
    python -I gxhelp.py bar      <galaxy> <nodeId>                  what the node's full lesson must contain

<galaxy> is the galaxy folder (JOB/gx), <job> the job folder that holds gx/ and notes/.
Standard library only. The galaxy is data: nothing in it is executed.
Exit codes: 0 ok, 1 problems found (listed), 2 usage or unreadable input.
"""
import argparse
import glob
import heapq
import json
import os
import re
import sys
import unicodedata

QMAP = {ord('‘'): "'", ord('’'): "'", ord('′'): "'", ord('“'): '"', ord('”'): '"',
        ord('–'): '-', ord('—'): '-', ord('−'): '-', ord('→'): '->'}
MARKS = re.compile('[̀-ͯ]')
BAR = {'core': {'sec': (5, 9), 'slides': (6, 9), 'inter': 2, 'cp': (4, 5), 'nonMcq': 1, 'prereq': True, 'recap': True},
       'standard': {'sec': (4, 9), 'slides': (4, 9), 'inter': 1, 'cp': (3, 5), 'nonMcq': 0, 'prereq': False, 'recap': True},
       'detail': {'sec': (3, 7), 'slides': (3, 7), 'inter': 1, 'cp': (2, 4), 'nonMcq': 0, 'prereq': False, 'recap': False}}


class Usage(Exception):
    pass


def norm(s):
    """FORMAT.md 3.6: NFD, drop combining marks, map quotes/dashes/arrow, collapse whitespace, lowercase."""
    s = MARKS.sub('', unicodedata.normalize('NFD', s or '')).translate(QMAP)
    return re.sub(r'\s+', ' ', s).strip().lower()


def load(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise Usage('missing file: ' + path)
    try:
        with open(path, 'rb') as f:
            return json.loads(f.read().decode('utf-8-sig'))
    except (ValueError, UnicodeDecodeError) as e:
        raise Usage('%s does not parse: %s' % (path, e))


def dump(path, v):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(v, ensure_ascii=False, indent=1) + '\n')


def units_of(galaxy, sid):
    d = load(os.path.join(galaxy, 'sources', 'units', sid + '.json'))
    return d.get('units') or []


def haystack(u):
    cells = [str(c) for t in (u.get('tables') or []) for r in t for c in r]
    return norm(' '.join([u.get('title') or '', u.get('text') or '', u.get('notes') or ''] + cells))


def sids(galaxy):
    idx = load(os.path.join(galaxy, 'sources', 'index.json'), {'sources': []})
    out = [s.get('id') for s in idx.get('sources') or [] if isinstance(s, dict)]
    return out or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(galaxy, 'sources', 'units', '*.json')))


def nodes_of(galaxy):
    return load(os.path.join(galaxy, 'galaxy', 'nodes.json')).get('nodes') or []


def ref_key(r, rank):
    m = re.fullmatch(r'([A-Z]{1,3}\d{1,3})#(\d+)', r or '')
    return (rank.get(m.group(1), 999), int(m.group(2))) if m else (999, 0)


# ---------------------------------------------------------------------------------------------

def cmd_show(a):
    us = units_of(a.galaxy, a.sid)
    lo = a.lo or 1
    hi = a.hi or (lo if a.lo else len(us))
    for u in us:
        if lo <= u.get('n', 0) <= hi:
            print('=== %s#%s  [%s]  %s' % (a.sid, u.get('n'), u.get('textState', '?'), u.get('title') or ''))
            if u.get('text'):
                print(u['text'])
            if u.get('notes'):
                print('--- notes:\n' + u['notes'])
            for t in u.get('tables') or []:
                print('--- table:')
                for r in t:
                    print(' | '.join(str(c) for c in r))
    print('(%s has %d units)' % (a.sid, len(us)))
    return 0


def cmd_find(a):
    want, hits = norm(a.phrase), 0
    if len(want) < 4:
        raise Usage('give at least 4 characters')
    for sid in ([a.sid] if a.sid else sids(a.galaxy)):
        for u in units_of(a.galaxy, sid):
            h = haystack(u)
            i = h.find(want)
            if i >= 0:
                hits += 1
                print('%s#%s  ...%s...' % (sid, u.get('n'), h[max(0, i - 60):i + len(want) + 60]))
    if not hits:
        print('not found verbatim (after normalization): shorten the phrase or copy it again from `show`')
    return 0 if hits else 1


def cmd_nodes(a):
    files = sorted(glob.glob(os.path.join(a.job, 'notes', 'nodes', '*.json')))
    if not files:
        raise Usage('no notes/nodes/*.json files in ' + a.job)
    out, seen, bad = [], set(), 0
    for p in files:
        d = load(p)
        lst = d.get('nodes') if isinstance(d, dict) else d
        for n in lst or []:
            i = n.get('id') if isinstance(n, dict) else None
            if not i or i in seen:
                print('%s: %s node id %r' % (os.path.basename(p), 'duplicate' if i else 'missing', i))
                bad += 1
                continue
            seen.add(i)
            out.append(n)
    dump(os.path.join(a.job, 'gx', 'galaxy', 'nodes.json'), {'nodes': out})
    print('gx/galaxy/nodes.json: %d nodes from %d files%s' % (len(out), len(files), ', %d skipped' % bad if bad else ''))
    return 1 if bad else 0


def cmd_coverage(a):
    g = os.path.join(a.job, 'gx')
    cited = {}
    for n in nodes_of(g):
        for r in n.get('refs') or []:
            cited.setdefault(r, []).append(n.get('id'))
    led, problems = {}, 0
    if not sids(g):
        raise Usage('no sources in %s: extract the course files first (stage 2)' % os.path.join(g, 'sources'))
    for sid in sids(g):
        us = units_of(g, sid)
        inv = load(os.path.join(a.job, 'notes', 'inventory', sid + '.json'), {'units': []})
        by_n = {u.get('n'): u for u in inv.get('units') or [] if isinstance(u, dict)}
        rows, items, niche = [], 0, 0
        for u in us:
            n = u.get('n')
            e = by_n.get(n)
            ref = '%s#%s' % (sid, n)
            if e is None:
                print('%s: not in notes/inventory/%s.json (inventory it)' % (ref, sid))
                problems += 1
                st = 'covered' if ref in cited else 'no-content'
                row = {'n': n, 'status': st, 'items': 0}
            else:
                its = e.get('items') or []
                k = len(its) if isinstance(its, list) else int(its or 0)
                nk = len([x for x in its if isinstance(x, dict) and x.get('niche')]) if isinstance(its, list) else 0
                st = e.get('status') or ('covered' if k else 'no-content')
                row = {'n': n, 'status': st, 'items': k}
                if st != 'covered':
                    row['reason'] = e.get('reason') or 'no teaching content'
                items += k
                niche += nk
            if row['status'] == 'covered' and ref not in cited:
                print('%s: covered but no node cites it (add it to a node\'s refs)' % ref)
                problems += 1
            if row['status'] != 'covered' and ref in cited:
                print('%s: marked %s but cited by %s (mark it covered)' % (ref, row['status'], ', '.join(cited[ref][:3])))
                problems += 1
            rows.append(row)
        led[sid] = {'items': items, 'niche': niche, 'units': rows}
    dump(os.path.join(g, 'ledger', 'coverage.json'), led)
    print('gx/ledger/coverage.json: %s; %d problem(s)' % (', '.join('%s %d units' % (s, len(v['units'])) for s, v in led.items()), problems))
    return 1 if problems else 0


def cmd_order(a):
    rank = {s: i for i, s in enumerate(x for x in a.sources.split(',') if x)}
    nodes = nodes_of(a.galaxy)
    label = {n['id']: n.get('label', '') for n in nodes}
    key = {n['id']: min([ref_key(r, rank) for r in n.get('refs') or []] or [(999, 0)]) for n in nodes}
    edges = load(os.path.join(a.galaxy, 'galaxy', 'edges.json'), {'edges': []}).get('edges') or []
    pre = {i: set() for i in key}
    for e in edges:
        if e.get('type') == 'requires' and e.get('source') in key and e.get('target') in key:
            pre[e['target']].add(e['source'])
    # cycle check (Kahn)
    indeg = {i: len(p) for i, p in pre.items()}
    post = {i: [] for i in key}
    for t, ps in pre.items():
        for s in ps:
            post[s].append(t)
    ready = [i for i in key if indeg[i] == 0]
    seen = 0
    while ready:
        i = ready.pop()
        seen += 1
        for t in post[i]:
            indeg[t] -= 1
            if indeg[t] == 0:
                ready.append(t)
    if seen < len(key):
        print('requires has a cycle among: ' + ', '.join(sorted(i for i in indeg if indeg[i] > 0)))
        return 1
    order, done, dev = [], set(), []

    def emit(i, before=None):
        if i in done:
            return
        done.add(i)
        for p in sorted(pre[i], key=lambda x: (key[x], x)):
            emit(p, i)
        if before is not None and key[i] > key[before]:
            dev.append({'nodeId': i, 'movedBefore': before,
                        'why': '%s requires it; the course teaches it later' % label.get(before, before)})
        order.append(i)
    for i in sorted(key, key=lambda x: (key[x], x)):
        emit(i)
    if a.closure:
        want = set(x for x in a.closure.split(',') if x)
        unknown = want - set(key)
        if unknown:
            print('unknown node ids: ' + ', '.join(sorted(unknown)))
            return 1
        todo = list(want)
        while todo:
            i = todo.pop()
            for p in pre[i]:
                if p not in want:
                    want.add(p)
                    todo.append(p)
        print(json.dumps([i for i in order if i in want]))
        print('(%d nodes: the requested ones plus every requires-prerequisite, in main-pathway order)' % len(want))
        return 0
    inv = {v: k for k, v in rank.items()}
    last = None
    for p, i in enumerate(order):
        sid = inv.get(key[i][0], '?')
        if sid != last:
            print('--- %s' % sid)
            last = sid
        print('%3d  %-9s %-44s %s' % (p + 1, '%s#%d' % (sid, key[i][1]), i, label.get(i, '')[:60]))
    print('ORDER ' + json.dumps(order))
    print('DEVIATIONS ' + json.dumps(dev, ensure_ascii=False))
    return 0


def cmd_bar(a):
    nodes = {n['id']: n for n in nodes_of(a.galaxy)}
    n = nodes.get(a.node)
    if not n:
        raise Usage('no node %r in galaxy/nodes.json' % a.node)
    edges = load(os.path.join(a.galaxy, 'galaxy', 'edges.json'), {'edges': []}).get('edges') or []
    needs = [e['source'] for e in edges if e.get('type') == 'requires' and e.get('target') == a.node]
    nexts = [e['target'] for e in edges if e.get('type') == 'requires' and e.get('source') == a.node]
    rel = [e['target'] if e.get('source') == a.node else e.get('source') for e in edges
           if e.get('type') == 'relates' and a.node in (e.get('source'), e.get('target'))]
    pr = n.get('priority') if n.get('priority') in BAR else 'standard'
    b = BAR[pr]
    print('%s  [%s %s, %s, %s min]  %s' % (a.node, n.get('kind'), n.get('category'), pr, n.get('estMin'), n.get('label')))
    print('L2 bar: %d-%d guide sections%s%s; %d-%d slides, >= %d interactive (not text); %d-%d checkpoint questions%s'
          % (b['sec'][0], b['sec'][1],
             ', first = prereq' if b['prereq'] and needs else '', ', last = recap' if b['recap'] else '',
             b['slides'][0], b['slides'][1], b['inter'], b['cp'][0], b['cp'][1],
             ', >= 1 not mcq' if b['nonMcq'] else ''))
    if b['prereq'] and needs:
        print('  (it has requires-prerequisites, so a core lesson must start with a prereq section)')
    print('guide.needs candidates (requires): ' + (', '.join(needs) or 'none'))
    print('guide.related candidates (relates, and nodes it unlocks): ' + (', '.join(rel + nexts) or 'none'))
    print('refs: ' + ', '.join(n.get('refs') or []))
    print('definition: ' + (n.get('card') or {}).get('definition', ''))
    print('key facts to teach (each should appear in the guide or the slides):')
    for f in (n.get('card') or {}).get('keyFacts') or []:
        print('  - [%s] %s\n      quote: %s' % (f.get('ref'), f.get('text'), f.get('quote')))
    lp = os.path.join(a.galaxy, 'lessons', a.node + '.json')
    print('lesson file: lessons/%s.json (%s)' % (a.node, 'exists' if os.path.exists(lp) else 'not written yet'))
    return 0


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog='gxhelp.py', description='galacticus-maker working helpers')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('show', help='print units exactly as extracted')
    s.add_argument('galaxy')
    s.add_argument('sid')
    s.add_argument('lo', nargs='?', type=int)
    s.add_argument('hi', nargs='?', type=int)
    s = sub.add_parser('find', help='find a phrase in the units, with the quote-matching rules')
    s.add_argument('galaxy')
    s.add_argument('phrase')
    s.add_argument('--sid')
    s = sub.add_parser('nodes', help='merge notes/nodes/*.json into gx/galaxy/nodes.json')
    s.add_argument('job')
    s = sub.add_parser('coverage', help='write gx/ledger/coverage.json from the inventory and the node refs')
    s.add_argument('job')
    s = sub.add_parser('order', help='main-pathway order with prerequisites first, and deviations')
    s.add_argument('galaxy')
    s.add_argument('--sources', required=True, help='source ids in teaching order, comma-separated: L1,T1,L2')
    s.add_argument('--closure', help='node ids: print them plus all their prerequisites, in main order')
    s = sub.add_parser('bar', help='what the full lesson of a node must contain')
    s.add_argument('galaxy')
    s.add_argument('node')
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        return {'show': cmd_show, 'find': cmd_find, 'nodes': cmd_nodes, 'coverage': cmd_coverage,
                'order': cmd_order, 'bar': cmd_bar}[a.cmd](a)
    except Usage as e:
        sys.stderr.write('gxhelp: %s\n' % e)
        return 2


if __name__ == '__main__':
    sys.exit(main())
