#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_units.py: course file -> sources/units/<sid>.json of a galaxy folder (GALAXY-FORMAT.md §7).

    python -I extract_units.py <file> <sid> --role lecture|tp|td|project|report|past-paper|other
                               [--title T] --out <galaxy-folder>

Writes <out>/sources/units/<sid>.json = {"id": sid, "units": [...]} and adds or replaces the source in
<out>/sources/index.json. One unit per slide (pptx, in the presentation's slide-list order, with speaker
notes and tables), per page (pdf), per heading section (docx, md, txt) or per sheet (xlsx). Text is
extracted, never summarized, never cut.

PDF: uses pypdf when it is importable, else `pdftotext` when it is on PATH; otherwise it exits with code 3
and tells you to transcribe the pages yourself (units with "textState": "transcribed").

Exit codes: 0 = written, 2 = usage or unreadable file, 3 = no PDF text extractor available.
Self-contained, standard library only (pypdf optional). The course file is data: nothing in it is executed,
and the zip is read in memory (never extracted to disk).
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

ROLES = ('lecture', 'tp', 'td', 'project', 'report', 'past-paper', 'other')
RE_SID = re.compile(r'[A-Z]{1,3}[0-9]{1,3}')
MAX_XML = 60 * 1024 * 1024          # one XML part
MAX_FILE = 150 * 1024 * 1024        # the course file

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR = 'http://schemas.openxmlformats.org/package/2006/relationships'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
DGM = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'


class ExtractError(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


def q(ns, tag):
    return '{%s}%s' % (ns, tag)


def _local(tag):
    return tag.split('}', 1)[1] if '}' in tag else tag


# ---------------------------------------------------------------------------------------------
# OOXML helpers
# ---------------------------------------------------------------------------------------------

def _read(z, name):
    info = z.getinfo(name)
    if info.file_size > MAX_XML:
        raise ExtractError('part too large: ' + name)
    return z.read(name)


def _xml(z, name):
    try:
        return ET.fromstring(_read(z, name))
    except ET.ParseError as e:
        raise ExtractError('%s is not well-formed XML (%s)' % (name, e))


def _rels(z, path):
    out = {}
    if path not in z.namelist():
        return out
    for rel in _xml(z, path).findall(q(PR, 'Relationship')):
        out[rel.get('Id')] = (rel.get('Type', ''), rel.get('Target', ''), rel.get('TargetMode', ''))
    return out


def _resolve(base_dir, target):
    if target.startswith('/'):
        base_dir, target = '', target[1:]
    stack = []
    for part in (base_dir + '/' + target).split('/'):
        if part == '..':
            if stack:
                stack.pop()
        elif part and part != '.':
            stack.append(part)
    return '/'.join(stack)


def _rels_path(part):
    d, f = part.rsplit('/', 1) if '/' in part else ('', part)
    return (d + '/' if d else '') + '_rels/' + f + '.rels'


# ---------------------------------------------------------------------------------------------
# pptx
# ---------------------------------------------------------------------------------------------

def _a_para_text(p):
    buf = []
    for child in p:
        tag = _local(child.tag)
        if tag in ('r', 'fld'):
            t = child.find(q(A, 't'))
            if t is not None and t.text:
                buf.append(t.text)
        elif tag == 'br':
            buf.append('\n')
    return ''.join(buf).strip()


def _shape_lines(el):
    lines = []
    for p in el.iter(q(A, 'p')):
        txt = _a_para_text(p)
        if not txt:
            continue
        ppr = p.find(q(A, 'pPr'))
        try:
            lvl = int(ppr.get('lvl', '0')) if ppr is not None else 0
        except ValueError:
            lvl = 0
        lines.append(('  ' * max(0, min(lvl, 8))) + txt)
    return lines


def _ph_type(sp):
    ph = sp.find('%s/%s/%s' % (q(P, 'nvSpPr'), q(P, 'nvPr'), q(P, 'ph')))
    return ph.get('type') if ph is not None else None


def _table(tbl):
    rows = []
    for tr in tbl.findall(q(A, 'tr')):
        cells = []
        for tc in tr.findall(q(A, 'tc')):
            if tc.get('hMerge') == '1' or tc.get('vMerge') == '1':
                cells.append('')
                continue
            cells.append(' '.join(l.strip() for l in _shape_lines(tc)))
        rows.append(cells)
    return rows


def _slide_unit(z, path, n):
    root = _xml(z, path)
    title, body, tables, pics = '', [], [], 0
    for el in root.iter():
        tag = _local(el.tag)
        if tag == 'pic':
            pics += 1
        elif tag == 'tbl':
            tables.append(_table(el))
    for sp in root.iter(q(P, 'sp')):
        t = _ph_type(sp)
        if t in ('sldNum', 'dt', 'ftr'):
            continue
        lines = _shape_lines(sp)
        if not lines:
            continue
        if t in ('title', 'ctrTitle') and not title:
            title = ' '.join(l.strip() for l in lines)
        else:
            body.extend(lines)
    notes = ''
    rels = _rels(z, _rels_path(path))
    base = path.rsplit('/', 1)[0]
    for typ, tgt, mode in rels.values():
        if mode == 'External':
            continue
        if typ.endswith('/notesSlide'):
            np_ = _resolve(base, tgt)
            if np_ in z.namelist():
                nl = []
                for sp in _xml(z, np_).iter(q(P, 'sp')):
                    if _ph_type(sp) == 'body':
                        nl.extend(_shape_lines(sp))
                notes = '\n'.join(nl)
        elif typ.endswith('/diagramData'):            # SmartArt text
            dp = _resolve(base, tgt)
            if dp in z.namelist():
                body.extend(_shape_lines(_xml(z, dp)))
    text = '\n'.join(body)
    has_text = bool(title or text or any(c for t in tables for r in t for c in r))
    state = 'text' if has_text else ('image-only' if pics else 'empty')
    return {'n': n, 'title': title, 'text': text, 'notes': notes, 'tables': tables, 'textState': state}


def extract_pptx(path):
    with zipfile.ZipFile(path) as z:
        pres = _xml(z, 'ppt/presentation.xml')
        prel = _rels(z, 'ppt/_rels/presentation.xml.rels')
        order = []
        lst = pres.find(q(P, 'sldIdLst'))
        for sld in (lst.findall(q(P, 'sldId')) if lst is not None else []):
            rid = sld.get(q(R, 'id'))
            if rid in prel:
                order.append(_resolve('ppt', prel[rid][1]))
        units = [_slide_unit(z, p, i + 1) for i, p in enumerate(order) if p in z.namelist()]
    for i, u in enumerate(units):
        u['n'] = i + 1
    return 'pptx', 'slide', units


# ---------------------------------------------------------------------------------------------
# docx
# ---------------------------------------------------------------------------------------------

def _w_text(p):
    buf = []
    for el in p.iter():
        if el.tag == q(W, 't') and el.text:
            buf.append(el.text)
        elif el.tag == q(W, 'tab'):
            buf.append('\t')
        elif el.tag in (q(W, 'br'), q(W, 'cr')):
            buf.append('\n')
    return ''.join(buf).strip()


def _styles(z):
    """styleId -> heading level (0 = not a heading), from the style name or its outline level."""
    out = {}
    if 'word/styles.xml' not in z.namelist():
        return out
    for st in _xml(z, 'word/styles.xml').findall(q(W, 'style')):
        sid = st.get(q(W, 'styleId')) or ''
        name_el = st.find(q(W, 'name'))
        name = (name_el.get(q(W, 'val')) if name_el is not None else '') or ''
        lvl = _level_from_name(name) or _level_from_name(sid)
        ppr = st.find(q(W, 'pPr'))
        ol = ppr.find(q(W, 'outlineLvl')) if ppr is not None else None
        if not lvl and ol is not None:
            try:
                v = int(ol.get(q(W, 'val'), '9'))
                lvl = v + 1 if v < 9 else 0
            except ValueError:
                pass
        out[sid] = lvl
    return out


def _level_from_name(name):
    n = name.lower().replace(' ', '')
    if n == 'title':
        return 1
    for pre in ('heading', 'titre', 'berschrift', 'titolo', 'encabezado', 'kop'):
        if n.startswith(pre) or n.endswith(pre):
            digits = ''.join(c for c in n if c.isdigit())
            return int(digits) if digits else 1
    return 0


def _p_level(p, styles):
    ppr = p.find(q(W, 'pPr'))
    if ppr is None:
        return 0
    ol = ppr.find(q(W, 'outlineLvl'))
    if ol is not None:
        try:
            v = int(ol.get(q(W, 'val'), '9'))
            if v < 9:
                return v + 1
        except ValueError:
            pass
    ps = ppr.find(q(W, 'pStyle'))
    if ps is None:
        return 0
    val = ps.get(q(W, 'val')) or ''
    return styles.get(val, 0) or _level_from_name(val)


def _w_blocks(el, styles, out):
    for child in el:
        if child.tag == q(W, 'p'):
            txt = _w_text(child)
            if txt:
                out.append(('p', _p_level(child, styles), txt))
        elif child.tag == q(W, 'tbl'):
            rows = []
            for tr in child.iter(q(W, 'tr')):
                cells = []
                for tc in tr.findall(q(W, 'tc')):
                    cells.append(' '.join(t for t in (_w_text(p) for p in tc.iter(q(W, 'p'))) if t))
                rows.append(cells)
            out.append(('t', 0, rows))
        elif child.tag in (q(W, 'sdt'), q(W, 'sdtContent'), q(W, 'customXml'), q(W, 'ins'), q(W, 'smartTag')):
            _w_blocks(child, styles, out)


def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        styles = _styles(z)
        root = _xml(z, 'word/document.xml')
    body = root.find(q(W, 'body'))
    blocks = []
    if body is not None:
        _w_blocks(body, styles, blocks)
    return 'docx', 'section', _sections(blocks)


def _sections(blocks, chunk=25):
    """Heading sections; without headings, chunks of `chunk` blocks (paragraphs or tables, never cut inside one).
    Section boundaries are the P0 spike's (demo/tools/docx_units.py), so unit numbers, and refs, stay the same."""
    has_head = any(k == 'p' and lvl > 0 for k, lvl, _ in blocks)
    units, cur, count = [], {'title': '', 'lines': [], 'tables': []}, 0

    def flush():
        if cur['lines'] or cur['tables'] or cur['title']:
            units.append(dict(cur))
    for kind, lvl, val in blocks:
        if has_head and kind == 'p' and lvl > 0:
            flush()
            cur = {'title': val, 'lines': [], 'tables': []}
            continue
        if kind == 't':
            cur['tables'].append(val)
        else:
            cur['lines'].append(val)
        count += 1
        if not has_head and count % chunk == 0:
            flush()
            cur = {'title': '', 'lines': [], 'tables': []}
    flush()
    out = []
    for i, u in enumerate(units):
        text = '\n'.join(u['lines'])
        has = bool(u['title'].strip() or text.strip() or any(c for t in u['tables'] for r in t for c in r))
        out.append({'n': i + 1, 'title': u['title'], 'text': text, 'notes': '', 'tables': u['tables'],
                    'textState': 'text' if has else 'empty'})
    return out


# ---------------------------------------------------------------------------------------------
# xlsx
# ---------------------------------------------------------------------------------------------

def extract_xlsx(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            for si in _xml(z, 'xl/sharedStrings.xml').findall(q(S, 'si')):
                shared.append(''.join(t.text or '' for t in si.iter(q(S, 't'))))
        wb = _xml(z, 'xl/workbook.xml')
        rels = _rels(z, 'xl/_rels/workbook.xml.rels')
        units = []
        sheets = wb.find(q(S, 'sheets'))
        for i, sh in enumerate(sheets.findall(q(S, 'sheet')) if sheets is not None else []):
            name = sh.get('name') or 'Sheet %d' % (i + 1)
            rid = sh.get(q(R, 'id'))
            target = _resolve('xl', rels[rid][1]) if rid in rels else None
            rows = []
            if target and target in z.namelist():
                for row in _xml(z, target).iter(q(S, 'row')):
                    cells = []
                    for c in row.findall(q(S, 'c')):
                        t = c.get('t')
                        if t == 'inlineStr':
                            val = ''.join(x.text or '' for x in c.iter(q(S, 't')))
                        else:
                            v = c.find(q(S, 'v'))
                            val = v.text if v is not None and v.text is not None else ''
                            if t == 's' and val.isdigit() and int(val) < len(shared):
                                val = shared[int(val)]
                        cells.append(val)
                    while cells and cells[-1] == '':
                        cells.pop()
                    if cells:
                        rows.append(cells)
            units.append({'n': i + 1, 'title': name, 'text': '', 'notes': '', 'tables': [rows] if rows else [],
                          'textState': 'text' if rows else 'empty'})
    return 'xlsx', 'sheet', units


# ---------------------------------------------------------------------------------------------
# pdf
# ---------------------------------------------------------------------------------------------

def extract_pdf(path):
    try:
        import pypdf  # optional dependency
    except Exception:
        pypdf = None
    pages = None
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(path)
            pages = [(pg.extract_text() or '') for pg in reader.pages]
        except Exception as e:
            sys.stderr.write('pypdf could not read the file (%s); trying pdftotext\n' % e)
            pages = None
    if pages is None:
        exe = shutil.which('pdftotext')
        if exe:
            try:
                res = subprocess.run([exe, '-layout', '-enc', 'UTF-8', path, '-'], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, timeout=600, check=False)
            except (OSError, subprocess.SubprocessError) as e:
                raise ExtractError('pdftotext failed: %s' % e)
            if res.returncode != 0:
                raise ExtractError('pdftotext failed: %s' % res.stderr.decode('utf-8', 'replace').strip())
            pages = res.stdout.decode('utf-8', 'replace').split('\f')
            if pages and not pages[-1].strip():
                pages = pages[:-1]
    if pages is None:
        raise ExtractError(
            'no PDF text extractor here (pypdf is not installed and pdftotext is not on PATH).\n'
            'Transcribe the PDF yourself: read every page in order and write sources/units/<sid>.json as\n'
            '  {"id": "<sid>", "units": [{"n": 1, "title": "", "text": "<the page text, word for word>", "notes": "",\n'
            '                            "tables": [], "textState": "transcribed"}, ...]}\n'
            'one unit per page, n = page number, text copied exactly (never summarized), then add the source to\n'
            'sources/index.json with "kind": "pdf", "unitKind": "page" and "unitCount" = number of pages.', code=3)
    units = []
    for i, t in enumerate(pages):
        t = t.replace('\r\n', '\n').replace('\r', '\n')
        t = '\n'.join(l.rstrip() for l in t.split('\n')).strip('\n')
        units.append({'n': i + 1, 'title': '', 'text': t, 'notes': '', 'tables': [],
                      'textState': 'text' if t.strip() else 'image-only'})
    return 'pdf', 'page', units


# ---------------------------------------------------------------------------------------------
# txt / md
# ---------------------------------------------------------------------------------------------

_MD_HEAD = re.compile(r' {0,3}(#{1,6})[ \t]+(.*)')


def extract_text(path, kind):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8-sig', 'replace').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks, i, fence = [], 0, False
    para = []

    def flush_para():
        if para:
            blocks.append(('p', 0, '\n'.join(para)))
            del para[:]
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            fence = not fence
            para.append(line)
            i += 1
            continue
        m = None if fence else _MD_HEAD.fullmatch(line)
        if m and m.group(2).strip().rstrip('#').strip():
            flush_para()
            blocks.append(('p', len(m.group(1)), m.group(2).strip().rstrip('#').strip()))
            i += 1
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        if not fence and line.strip() and re.fullmatch(r'\s*(=+|-+)\s*', nxt) and len(nxt.strip()) >= 3:
            flush_para()
            blocks.append(('p', 1 if '=' in nxt else 2, line.strip()))
            i += 2
            continue
        if not line.strip() and not fence:
            flush_para()
        else:
            para.append(line.rstrip())
        i += 1
    flush_para()
    return kind, 'section', _sections(blocks)


# ---------------------------------------------------------------------------------------------
# galaxy folder output
# ---------------------------------------------------------------------------------------------

def extract(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pptx':
        return extract_pptx(path)
    if ext == '.docx':
        return extract_docx(path)
    if ext == '.xlsx':
        return extract_xlsx(path)
    if ext == '.pdf':
        return extract_pdf(path)
    if ext in ('.md', '.markdown'):
        return extract_text(path, 'md')
    if ext == '.txt':
        return extract_text(path, 'txt')
    raise ExtractError('unsupported file type %s: convert it to pptx, docx, pdf, xlsx, md or txt, or transcribe it '
                       'yourself ("textState": "transcribed")' % (ext or '(none)'))


def _dump(v):
    return json.dumps(v, ensure_ascii=False, indent=1) + '\n'


def write_units(out, sid, units, entry):
    os.makedirs(os.path.join(out, 'sources', 'units'), exist_ok=True)
    with open(os.path.join(out, 'sources', 'units', sid + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(_dump({'id': sid, 'units': units}))
    ipath = os.path.join(out, 'sources', 'index.json')
    idx = {'sources': []}
    if os.path.exists(ipath):
        try:
            with open(ipath, 'rb') as f:
                idx = json.loads(f.read().decode('utf-8-sig'))
        except ValueError as e:
            raise ExtractError('sources/index.json does not parse (%s): fix it first' % e)
        if not isinstance(idx, dict) or not isinstance(idx.get('sources'), list):
            raise ExtractError('sources/index.json must be {"sources": [...]}')
    srcs = idx['sources']
    for i, s in enumerate(srcs):
        if isinstance(s, dict) and s.get('id') == sid:
            srcs[i] = entry
            break
    else:
        srcs.append(entry)
    with open(ipath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(_dump(idx))


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog='extract_units.py', description='Extract the units of a course file into a '
                                                                       'galaxy folder (sources/units/<sid>.json).')
    ap.add_argument('file')
    ap.add_argument('sid', help='source id: L1 (lecture), T1 (TP or lab), P1 (past paper), D1 (other)')
    ap.add_argument('--role', required=True, choices=ROLES)
    ap.add_argument('--title')
    ap.add_argument('--out', required=True, help='the galaxy folder')
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if not RE_SID.fullmatch(a.sid):
        sys.stderr.write('extract_units: source id %r must be 1-3 capitals then 1-3 digits (L1, T2, P1)\n' % a.sid)
        return 2
    if not os.path.isfile(a.file):
        sys.stderr.write('extract_units: not a file: %s\n' % a.file)
        return 2
    if os.path.getsize(a.file) > MAX_FILE:
        sys.stderr.write('extract_units: the file is larger than 150 MB\n')
        return 2
    try:
        kind, unit_kind, units = extract(a.file)
    except ExtractError as e:
        sys.stderr.write('extract_units: %s\n' % e)
        return e.code
    except (zipfile.BadZipFile, KeyError, OSError) as e:
        sys.stderr.write('extract_units: cannot read %s as %s (%s)\n' % (a.file, os.path.splitext(a.file)[1], e))
        return 2
    with open(a.file, 'rb') as f:
        sha = 'sha256:' + hashlib.sha256(f.read()).hexdigest()
    title = a.title or os.path.splitext(os.path.basename(a.file))[0]
    entry = {'id': a.sid, 'title': title, 'role': a.role, 'kind': kind, 'unitKind': unit_kind,
             'file': os.path.basename(a.file), 'unitCount': len(units),
             'imageOnly': [u['n'] for u in units if u['textState'] == 'image-only'], 'sha256': sha}
    try:
        write_units(a.out, a.sid, units, entry)
    except ExtractError as e:
        sys.stderr.write('extract_units: %s\n' % e)
        return 2
    except OSError as e:
        sys.stderr.write('extract_units: cannot write into %s (%s)\n' % (a.out, e))
        return 2
    empty = [u['n'] for u in units if u['textState'] == 'empty']
    print('%s: %d %ss (%d with text, image-only %s, empty %s) -> %s' % (
        a.sid, len(units), unit_kind, sum(1 for u in units if u['textState'] == 'text'), entry['imageOnly'] or 'none',
        empty or 'none', os.path.join(a.out, 'sources', 'units', a.sid + '.json')))
    if entry['imageOnly']:
        print('  image-only units have no extractable text: look at them and transcribe what they teach '
              '(set "textState": "transcribed") or mark them no-content in the coverage ledger')
    return 0


if __name__ == '__main__':
    sys.exit(main())
