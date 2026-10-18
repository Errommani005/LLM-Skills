#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gxformat.py: the Galaxy format v1 library and command line (Python twin of 35-format.js).

One self-contained, standard-library-only file (Python 3.9+). Run it isolated:

    python -I gxformat.py validate <folder|.galaxy|.zip|bundle.txt|stamped.html>
                                   [--profile P] [--work-order wo.json] [--base <galaxy>] [--no-quotes] [--json]
    python -I gxformat.py manifest <folder> [--profile P] [--exported-by S] [--work-order WO --part 1/3]
    python -I gxformat.py pack     <folder> <out.galaxy> [--work-order WO --part 1/3] [--deflate] [--force]
    python -I gxformat.py html     <galaxy path> <reader.html> <out.html> [--force]
    python -I gxformat.py bundle   <folder> [--profile part --galaxy-id ID --work-order WO --part 2/5] [--out f.txt]
    python -I gxformat.py unbundle <bundle.txt> <out-folder> [--force]
    python -I gxformat.py stats    <path> [--work-order wo.json] [--base <galaxy>] [--json]
    python -I gxformat.py merge    <galaxy> <part> <out-folder> [--replace higher|always|never]
                                   [--replace-guide] [--replace-exam] [--force]

Exit codes: 0 = ok, 1 = validation errors, 2 = usage or I/O error.

The spec is GALAXY-FORMAT.md (format version 1). This file ports 35-format.js check for check, so both
validators give the same codes for the same input, and hashes are byte-identical (canonical JSON: keys sorted
by UTF-16 code units, ECMAScript strings and numbers, integral numbers without exponent).
Everything read from a galaxy is data: nothing in it is executed, fetched or followed.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import re
import struct
import sys
import unicodedata
import zipfile
import zlib
from decimal import Decimal

VERSION = 1
TOOL = 'gxformat.py'
TOOL_VERSION = '1'
LIMITS = {'entries': 20000, 'bytes': 150 * 1024 * 1024, 'json': 20 * 1024 * 1024, 'bundle': 8 * 1024 * 1024}
MAX_ERRORS = 2000
# codes that stop a reader from opening the galaxy at all
BLOCKING = ('E-CONTAINER', 'E-PATH', 'E-SIZE', 'E-JSON', 'E-MISSING', 'E-MANIFEST')

PROFILES = ('galaxy', 'pathway', 'part')
KINDS = ('concept', 'skill', 'event', 'scenario')
CATEGORIES = ('technical', 'historical', 'situational')
PRIORITIES = ('core', 'standard', 'detail')
ORIGINS = ('lesson', 'tp', 'hybrid', 'extension')
EDGE_TYPES = ('requires', 'follows', 'relates')
PATHWAY_KINDS = ('main', 'branch', 'exam', 'topic', 'custom')
SECTION_KINDS = ('prereq', 'definition', 'summary', 'formula', 'technique', 'example', 'trap', 'recap', 'history',
                 'scenario', 'command')
PRIMITIVES = ('text', 'stepper', 'compare', 'flow', 'timeline', 'quorum', 'kvrepl', 'chooser')
QTYPES = ('mcq', 'multi', 'fill', 'short')
GUIDE_KINDS = ('howto', 'map', 'reference', 'niche', 'traps', 'checklist', 'route')
CONFIDENCE = ('user-stated', 'derived-from-artifact', 'inferred')
ROLES = ('lecture', 'tp', 'td', 'project', 'report', 'past-paper', 'other')
SOURCE_KINDS = ('pptx', 'docx', 'pdf', 'xlsx', 'txt', 'md')
UNIT_KINDS = ('slide', 'page', 'section', 'sheet')
TEXT_STATES = ('text', 'image-only', 'empty', 'transcribed')
COVERAGE = ('covered', 'no-content')
LEVELS = ('L0', 'L1', 'L2', 'L3')
RANK = {'L0': 0, 'L1': 1, 'L2': 2, 'L3': 3}

RE_GALAXY_ID = re.compile(r'gx_[a-z0-9_-]{3,80}')
RE_NODE_ID = re.compile(r'[a-z0-9][a-z0-9-]{0,79}')
RE_SID = re.compile(r'[A-Z]{1,3}[0-9]{1,3}')
RE_REF = re.compile(r'([A-Z]{1,3}[0-9]{1,3})#([0-9]+)')
RE_DIGEST = re.compile(r'sha256:[0-9a-f]{64}')
RE_NAME = re.compile(r'[a-z0-9._/-]+')
_UNITS_PATH = re.compile(r'sources/units/[A-Z]{1,3}[0-9]{1,3}\.json')

# ECMAScript WhiteSpace + LineTerminator (JS \s and String.prototype.trim)
JS_WS = ('\t\n\x0b\x0c\r              '
         '    　﻿')
_WSC = re.escape(JS_WS)
_WS_RUN = re.compile('[' + _WSC + ']+')


class FormatError(Exception):
    """A container-level problem; code is one of the §9.6 codes."""

    def __init__(self, code, msg, path=''):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.path = path or ''


def _fail(code, msg, path=''):
    raise FormatError(code, msg, path)


# ---------------------------------------------------------------------------------------------
# JS-like value helpers (JSON values only)
# ---------------------------------------------------------------------------------------------

def is_obj(x):
    return isinstance(x, dict)


def is_str(x):
    return isinstance(x, str)


def _as_double(x):
    """The double JSON.parse would produce for a Python number (None when it overflows to Infinity)."""
    try:
        d = float(x)
    except OverflowError:
        return None
    return d if math.isfinite(d) else None


def is_num(x):
    """typeof x === 'number' && isFinite(x)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    return _as_double(x) is not None


def is_int(x):
    """Number.isInteger(x)."""
    if not is_num(x):
        return False
    return isinstance(x, int) or float(x).is_integer()


def arr(x):
    return x if isinstance(x, list) else []


def jtrim(s):
    return s.strip(JS_WS)


def non_empty(x):
    return isinstance(x, str) and jtrim(x) != ''


def clen(s):
    """Length in code points (JS counts surrogate pairs once), so every language counts the same way."""
    return len(s if isinstance(s, str) else js_str(s))


def js_truthy(x):
    if x is None or x is False:
        return False
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return x == x and x != 0
    if isinstance(x, str):
        return x != ''
    return True


def js_str(x):
    """String(x) for a JSON value."""
    if x is None:
        return 'null'
    if x is True:
        return 'true'
    if x is False:
        return 'false'
    if isinstance(x, str):
        return x
    if isinstance(x, (int, float)):
        d = _as_double(x)
        return 'Infinity' if d is None and x > 0 else '-Infinity' if d is None else js_number(d)
    if isinstance(x, list):
        return ','.join('' if v is None else js_str(v) for v in x)
    return '[object Object]'


class _Undefined(object):
    """JS undefined (a missing key), so messages say what JSON.stringify says: undefined vs null."""
    __slots__ = ()

    def __repr__(self):
        return 'undefined'


UNDEF = _Undefined()


def js_json(x):
    """JSON.stringify(x) of a JSON value: compact, keys in insertion order, ECMAScript strings and numbers."""
    if x is None or x is True or x is False:
        return 'null' if x is None else ('true' if x else 'false')
    if isinstance(x, str):
        return js_string(x)
    if isinstance(x, (int, float)):
        d = _as_double(x)
        return 'null' if d is None else js_number(d)
    if isinstance(x, (list, tuple)):
        return '[' + ','.join(js_json(v) for v in x) + ']'
    if isinstance(x, dict):
        return '{' + ','.join(js_string(k) + ':' + js_json(v) for k, v in x.items()) + '}'
    return 'null'


def jstr(x):
    """'' + JSON.stringify(x) for messages (a missing value, UNDEF, prints undefined)."""
    if x is UNDEF:
        return 'undefined'
    try:
        return js_json(x)
    except (TypeError, ValueError, RecursionError):
        return str(x)


def plural(n, w):
    return '%d %s%s' % (n, w, '' if n == 1 else 's')


def fmt_mb(b):
    return '%.1f MB' % (b / 1048576.0)


def _num_str(x):
    """'' + x in JS for a number in a message."""
    return js_str(x)


# ---------------------------------------------------------------------------------------------
# 8.1 canonical JSON
# ---------------------------------------------------------------------------------------------

_ESC_RE = re.compile('[\x00-\x1f"\\\\\ud800-\udfff]')
_ESC_MAP = {'"': '\\"', '\\': '\\\\', '\b': '\\b', '\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t'}


def _esc(m):
    c = m.group(0)
    r = _ESC_MAP.get(c)
    return r if r is not None else '\\u%04x' % ord(c)


def js_string(s):
    """JSON.stringify(string): escapes " \\ and controls (lowercase \\u00xx), lone surrogates as \\udxxx."""
    return '"' + _ESC_RE.sub(_esc, s) + '"'


def js_number(d):
    """ECMAScript Number::toString of a finite double (shortest round-trip digits)."""
    if d == 0:
        return '0'
    neg = d < 0
    _, dig, exp = Decimal(repr(abs(d))).as_tuple()
    digits = ''.join(map(str, dig)).lstrip('0') or '0'
    stripped = digits.rstrip('0') or '0'
    exp += len(digits) - len(stripped)
    digits = stripped
    k = len(digits)
    n = exp + k
    if k <= n <= 21:
        s = digits + '0' * (n - k)
    elif 0 < n <= 21:
        s = digits[:n] + '.' + digits[n:]
    elif -6 < n <= 0:
        s = '0.' + '0' * (-n) + digits
    else:
        e = n - 1
        s = digits[0] + ('.' + digits[1:] if k > 1 else '') + 'e' + ('+' if e >= 0 else '-') + str(abs(e))
    return '-' + s if neg else s


def canon_num(v):
    """35-format.js canonNum: non-finite -> null; integral -> no exponent (exact digits from 1e21 up)."""
    d = _as_double(v)
    if d is None:
        return 'null'
    if d.is_integer():
        return js_number(d) if abs(d) < 1e21 else str(int(d))
    return js_number(d)


def _u16(k):
    return k.encode('utf-16-be', 'surrogatepass')


def canon(v):
    """§8.1 canonical JSON, byte-identical with F.canon."""
    if v is None:
        return 'null'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, str):
        return js_string(v)
    if isinstance(v, (int, float)):
        return canon_num(v)
    if isinstance(v, (list, tuple)):
        return '[' + ','.join(canon(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ','.join(js_string(k) + ':' + canon(v[k]) for k in sorted(v, key=_u16)) + '}'
    raise TypeError('not a JSON value: %r' % type(v))


# ---------------------------------------------------------------------------------------------
# SHA-256, JSON access, 8.2 digests and contentHash
# ---------------------------------------------------------------------------------------------

def _bytes(d):
    if isinstance(d, str):
        return d.encode('utf-8', 'replace') if _has_lone_surrogate(d) else d.encode('utf-8')
    return bytes(d)


def _has_lone_surrogate(s):
    try:
        s.encode('utf-8')
        return False
    except UnicodeEncodeError:
        return True


def sha256(data):
    """'sha256:' + hex; a str is hashed as UTF-8 (TextEncoder)."""
    return 'sha256:' + hashlib.sha256(_bytes(data)).hexdigest()


def is_json_path(p):
    return bool(re.search(r'\.(json|galsave)\Z', str(p)))


def in_scope(p):
    """True when the path counts in the contentHash (§8.2)."""
    return (p != 'manifest.json' and p != 'README.txt' and p != 'galaxy/layout.json'
            and not re.match(r'(saves|originals|work|patches)/', p))


class JsonError(FormatError, ValueError):
    """E-JSON from parse_json_text. Also a ValueError, so callers that catch ValueError keep working."""

    def __init__(self, msg, path=''):
        FormatError.__init__(self, 'E-JSON', msg, path)


def _bad_constant(name):
    # Python's json accepts NaN / Infinity / -Infinity; JSON.parse does not
    raise JsonError('%s is not valid JSON' % name)


# JSON nested deeper than this is treated as not parseable (E-JSON; raw-bytes digest), exactly as 35-format.js does, so
# both validators agree whatever their recursion limits (real galaxy files nest about 8 levels)
MAX_JSON_DEPTH = 128


def _too_deep(v, mx):
    st = [(v, 1)]
    while st:
        x, d = st.pop()
        if isinstance(x, (dict, list)):
            if d > mx:
                return True
            st.extend((k, d + 1) for k in (x.values() if isinstance(x, dict) else x) if isinstance(k, (dict, list)))
    return False


def parse_json_text(text, max_depth=None):
    """JSON.parse(stripBom(text)); raises JsonError (a FormatError with code E-JSON, and a ValueError)."""
    if text.startswith('﻿'):
        text = text[1:]
    try:
        v = json.loads(text, parse_constant=_bad_constant)
    except JsonError:
        raise
    except RecursionError:
        raise JsonError('JSON nested more than %d levels deep' % MAX_JSON_DEPTH)
    except ValueError as e:  # json.JSONDecodeError
        raise JsonError(str(e))
    if _too_deep(v, max_depth or MAX_JSON_DEPTH):
        raise JsonError('JSON nested more than %d levels deep' % MAX_JSON_DEPTH)
    return v


def _decode_fatal(b):
    """new TextDecoder('utf-8', {fatal: true}).decode(b): strict, one leading BOM removed."""
    t = bytes(b).decode('utf-8')
    return t[1:] if t.startswith('﻿') else t


def _decode(b):
    """new TextDecoder().decode(b): invalid sequences replaced, one leading BOM removed."""
    t = bytes(b).decode('utf-8', 'replace')
    return t[1:] if t.startswith('﻿') else t


def read_json(files, path):
    """F.readJson: None when absent; FormatError E-SIZE / E-JSON with the path."""
    if path not in files:
        return None
    d = files[path]
    b = _bytes(d)
    if len(b) > LIMITS['json']:
        _fail('E-SIZE', '%s is %s; a JSON file may be at most %s.' % (path, fmt_mb(len(b)), fmt_mb(LIMITS['json'])), path)
    try:
        text = d if isinstance(d, str) else _decode_fatal(b)
    except UnicodeDecodeError:
        _fail('E-JSON', path + ' is not valid UTF-8 text.', path)
    try:
        return parse_json_text(text)
    except ValueError as e:
        _fail('E-JSON', '%s is not valid JSON (%s). Fix the syntax and save it again.' % (path, str(e)[:160]), path)


def digest(path, data):
    """§8.2: sha256 of the canonical JSON for .json/.galsave (raw bytes when it does not parse), else raw bytes."""
    if is_json_path(path):
        try:
            text = data if isinstance(data, str) else _decode_fatal(data)
            return sha256(canon(parse_json_text(text)))
        except (UnicodeDecodeError, ValueError):
            pass
    return sha256(_bytes(data))


def digests(files):
    """{path: digest} for every file except manifest.json."""
    return {p: digest(p, files[p]) for p in sorted(files) if p != 'manifest.json'}


def content_hash(entries):
    """contentHash of {path: digest} (or of {path: bytes}: digests are computed); out-of-scope paths dropped."""
    all_digests = all(isinstance(v, str) and RE_DIGEST.fullmatch(v) for v in entries.values())
    E = {}
    for p in sorted(entries):
        if not in_scope(p):
            continue
        E[p] = entries[p] if all_digests else digest(p, entries[p])
    return sha256(canon(E))


# ---------------------------------------------------------------------------------------------
# paths and zip (§2)
# ---------------------------------------------------------------------------------------------

def path_problem(p):
    """Why a path is unsafe (None when it is fine)."""
    if not isinstance(p, str) or not p:
        return 'empty path'
    if re.search('[\x00-\x1f\x7f-\x9f]', p):
        return 'it contains a control character'
    if '\\' in p:
        return 'it contains a backslash (paths use /)'
    if p[0] == '/':
        return 'it is absolute (starts with /)'
    if re.match(r'[A-Za-z]:', p):
        return 'it starts with a drive letter'
    segs = p.split('/')
    if '..' in segs:
        return 'it contains a ".." segment'
    if '.' in segs:
        return 'it contains a "." segment'
    if '' in segs:
        return 'it contains an empty segment (//)'
    return None


def check_path(p):
    why = path_problem(p)
    if why:
        _fail('E-PATH', 'Unsafe or duplicate path: %s (%s). The galaxy was not opened.' % (jstr(js_str(p)), why), js_str(p))


def crc32(b):
    return zlib.crc32(bytes(b)) & 0xFFFFFFFF


def zip_bytes(files, date=(2026, 1, 1, 0, 0, 0), deflate=False):
    """{path: bytes|str} -> zip bytes: UTF-8 names, no wrapping folder; STORED (as the JS writer) or DEFLATED."""
    import io
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for p in files:
            check_path(p)
            info = zipfile.ZipInfo(p, date_time=date)
            info.external_attr = 0o644 << 16
            info.flag_bits |= 0x800
            packed = re.search(r'\.(pptx|docx|xlsx|zip|png|jpe?g|gif|webp|pdf|mp4|galaxy)\Z', p.lower())
            info.compress_type = zipfile.ZIP_DEFLATED if deflate and not packed else zipfile.ZIP_STORED
            z.writestr(info, _bytes(files[p]))
    return out.getvalue()


def zip_read(u8, limits=None):
    """F.zip.read port: zip bytes -> [(name, bytes)] (directories skipped), STORE + DEFLATE, §2 hardening."""
    lim = dict(LIMITS)
    lim.update(limits or {})
    u8 = bytes(u8)
    N = len(u8)
    if N < 22:
        _fail('E-CONTAINER', 'Not a zip archive: the file is too short.')
    u16 = lambda o: struct.unpack_from('<H', u8, o)[0]
    u32 = lambda o: struct.unpack_from('<I', u8, o)[0]
    eo = -1
    for i in range(N - 22, max(0, N - 65557) - 1, -1):
        if u32(i) == 0x06054b50:
            eo = i
            break
    if eo < 0:
        _fail('E-CONTAINER', 'Not a zip archive: no end-of-archive record was found.')
    if u16(eo + 4) != 0 or u16(eo + 6) != 0:
        _fail('E-CONTAINER', 'Corrupt central directory: multi-disk archives are not supported.')
    count, cd_size, p = u16(eo + 10), u32(eo + 12), u32(eo + 16)
    if count == 0xFFFF or p == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:
        _fail('E-CONTAINER', 'Unsupported zip64 archive: re-zip it as a regular zip (galaxies are far below 4 GB).')
    if count > lim['entries']:
        _fail('E-SIZE', 'Too many entries (%d; the limit is %d).' % (count, lim['entries']))
    if p + cd_size > eo:
        _fail('E-CONTAINER', 'Corrupt central directory: it points outside the file.')
    out, names, total = [], set(), 0
    for k in range(count):
        if p + 46 > eo or u32(p) != 0x02014b50:
            _fail('E-CONTAINER', 'Corrupt central directory (entry %d).' % (k + 1))
        flags, method, crc = u16(p + 8), u16(p + 10), u32(p + 16)
        csize, usize = u32(p + 20), u32(p + 24)
        nl, xl, cl, lo = u16(p + 28), u16(p + 30), u16(p + 32), u32(p + 42)
        if p + 46 + nl > eo:
            _fail('E-CONTAINER', 'Corrupt central directory (entry %d).' % (k + 1))
        name = u8[p + 46:p + 46 + nl].decode('utf-8', 'replace')
        p += 46 + nl + xl + cl
        is_dir = name.endswith('/')
        check_path(name[:-1] if is_dir else name)
        if name in names:
            _fail('E-PATH', 'Unsafe or duplicate path: %s appears twice in the archive.' % jstr(name), name)
        names.add(name)
        if flags & 1:
            _fail('E-CONTAINER', 'Encrypted entry %s: password-protected zips are not supported.' % name, name)
        if is_dir:
            continue
        total += usize
        if total > lim['bytes']:
            _fail('E-SIZE', 'Archive too large when unpacked (more than %s).' % fmt_mb(lim['bytes']))
        if csize == 0xFFFFFFFF or usize == 0xFFFFFFFF or lo == 0xFFFFFFFF:
            _fail('E-CONTAINER', 'Unsupported zip64 entry %s.' % name, name)
        if lo + 30 > N or u32(lo) != 0x04034b50:
            _fail('E-CONTAINER', 'Corrupt local header for %s.' % name, name)
        start = lo + 30 + u16(lo + 26) + u16(lo + 28)
        if start + csize > N:
            _fail('E-CONTAINER', 'Corrupt archive: %s is truncated.' % name, name)
        raw = u8[start:start + csize]
        if method == 0:
            if csize != usize:
                _fail('E-CONTAINER', 'Size mismatch in %s.' % name, name)
            data = raw
        elif method == 8:
            # accepted when the stream gives exactly usize bytes (then the CRC-32 is checked); whatever follows in the
            # stream (junk, a missing end block) is ignored, like 35-format.js (browsers' DecompressionStream differ there)
            dobj = zlib.decompressobj(-15)
            try:
                data = dobj.decompress(raw, usize) if usize else b''
            except zlib.error:
                _fail('E-CONTAINER', 'Corrupt compressed data in %s: the archive is damaged.' % name, name)
            if len(data) != usize:
                _fail('E-CONTAINER', 'Size mismatch in %s: the archive is damaged.' % name, name)
            if not dobj.eof:
                try:
                    extra = dobj.decompress(dobj.unconsumed_tail if usize else raw, 1)
                except zlib.error:
                    extra = b''
                if extra:
                    _fail('E-CONTAINER', 'Size mismatch in %s: it unpacks to more than the archive declares.' % name, name)
        else:
            _fail('E-CONTAINER', 'Unsupported compression in %s (method %d): re-zip with Deflate or without '
                                 'compression.' % (name, method), name)
        if crc32(data) != crc:
            _fail('E-CONTAINER', 'Corrupt archive: the checksum of %s does not match (the file is damaged).' % name, name)
        out.append((name, data))
    return out


# ---------------------------------------------------------------------------------------------
# reading inputs: zip, folder, text bundle, embedded galaxy
# ---------------------------------------------------------------------------------------------

_JUNK = [re.compile(r'(^|/)__MACOSX/'), re.compile(r'(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)\Z', re.I),
         re.compile(r'(^|/)\._[^/]*\Z')]


def is_junk(p):
    return any(r.search(p) for r in _JUNK)


def detect_root(paths):
    """§2 root detection: the shallowest directory (depth <= 2) holding manifest.json or galaxy/meta.json."""
    cands = set()
    for p in paths:
        segs = p.split('/')
        if segs[-1] == 'manifest.json':
            cands.add('/'.join(segs[:-1]))
        if segs[-1] == 'meta.json' and len(segs) >= 2 and segs[-2] == 'galaxy':
            cands.add('/'.join(segs[:-2]))
    depth = lambda d: len(d.split('/')) if d else 0
    ok = [d for d in cands if depth(d) <= 2]
    if not ok:
        _fail('E-CONTAINER', 'No galaxy found: there is no manifest.json or galaxy/meta.json in the top two folder levels.')
    mn = min(depth(d) for d in ok)
    at = sorted(d for d in ok if depth(d) == mn)
    if len(at) > 1:
        _fail('E-CONTAINER', 'Two galaxies found side by side (%s): open one at a time.'
              % ' and '.join((d or '.') + '/' for d in at))
    return at[0]


def _rooted(raw, notes, find_root):
    keys = list(raw)
    junk = [k for k in keys if is_junk(k)]
    if junk:
        notes.append({'code': 'W-UNKNOWN-PATH', 'path': '',
                      'msg': plural(len(junk), 'system file') + ' (__MACOSX, .DS_Store, Thumbs.db) ignored.'})
    real = [k for k in keys if not is_junk(k)]
    root = detect_root(real) if find_root else ''
    pre = root + '/' if root else ''
    files, outside, total = {}, 0, 0
    for p in real:
        if pre and not p.startswith(pre):
            outside += 1
            continue
        rel = p[len(pre):]
        check_path(rel)
        if rel in files:
            _fail('E-PATH', 'Unsafe or duplicate path: %s appears twice.' % jstr(rel), rel)
        files[rel] = raw[p]
        total += len(raw[p])
    if outside:
        notes.append({'code': 'W-UNKNOWN-PATH', 'path': '',
                      'msg': '%s outside the galaxy folder (%s/) ignored.' % (plural(outside, 'file'), root)})
    if len(files) > LIMITS['entries']:
        _fail('E-SIZE', 'Too many files (%d; the limit is %d).' % (len(files), LIMITS['entries']))
    if total > LIMITS['bytes']:
        _fail('E-SIZE', 'The galaxy is too large (%s; the limit is %s).' % (fmt_mb(total), fmt_mb(LIMITS['bytes'])))
    return files, root


def _is_zip_bytes(b):
    return len(b) >= 4 and b[0] == 0x50 and b[1] == 0x4B and ((b[2] == 3 and b[3] == 4) or (b[2] == 5 and b[3] == 6))


def _from_zip(b, notes):
    raw = {}
    for name, data in zip_read(b):
        raw[name] = data
    files, root = _rooted(raw, notes, True)
    return {'kind': 'zip', 'files': files, 'root': root, 'notes': notes, 'header': None, 'bundles': None}


def _utf8_len(s):
    return len(_bytes(s))


def _from_bundle_text(text, notes):
    if _utf8_len(text) > LIMITS['bundle']:
        _fail('E-SIZE', 'The pasted text is %s; a text bundle may be at most %s. Ask the AI for smaller parts.'
              % (fmt_mb(_utf8_len(text)), fmt_mb(LIMITS['bundle'])))
    r = parse_text_bundle(text)
    if not r['bundles']:
        e = r['errors'][0] if r['errors'] else {'code': 'E-CONTAINER', 'msg': 'No text bundle found.', 'path': ''}
        _fail(e['code'], e['msg'], e.get('path', ''))
    for e in r['errors']:
        notes.append({'code': e['code'], 'path': e.get('path') or '', 'msg': e['msg']})
    files, bundles = {}, []
    for b in r['bundles']:
        bf = {}
        for p, s in b['files'].items():
            data = _bytes(s)
            bf[p] = data
            if p in files:
                notes.append({'code': 'W-UNKNOWN-PATH', 'path': p, 'msg': p + ' appears in several bundles: the last one is used.'})
            files[p] = data
        bundles.append({'header': b['header'], 'files': bf})
    return {'kind': 'bundle', 'files': files, 'root': '', 'notes': notes, 'header': r['bundles'][0]['header'],
            'bundles': bundles}


def _from_embed_text(text, notes):
    files, _ = _rooted(unembed(text), notes, False)
    return {'kind': 'embed', 'files': files, 'root': '', 'notes': notes, 'header': None, 'bundles': None}


def read_input(path):
    """F.readInput for a path on disk: a folder, a .galaxy/.zip, a text bundle or a stamped HTML page.
    -> {kind, files: {path: bytes}, root, notes: [{code, path, msg}], header, bundles}.
    Raises FormatError (E-CONTAINER / E-PATH / E-SIZE / E-MANIFEST) and OSError."""
    notes = []
    if os.path.isdir(path):
        return _from_folder(path, notes)
    if not os.path.isfile(path):
        raise FileNotFoundError('not found: ' + path)
    name = os.path.basename(path)
    size = os.path.getsize(path)
    if size > LIMITS['bytes']:
        _fail('E-SIZE', '%s is %s; the limit is %s.' % (name, fmt_mb(size), fmt_mb(LIMITS['bytes'])))
    with open(path, 'rb') as f:
        b = f.read()
    if _is_zip_bytes(b):
        return _from_zip(b, notes)
    if re.search(r'\.(galaxy|zip)\Z', name, re.I):
        _fail('E-CONTAINER', name + ' is not a zip archive. A .galaxy file is a zip with manifest.json inside.')
    text = _decode(b)
    is_html = bool(re.search(r'\.html?\Z', name, re.I))
    has_embed = bool(re.search(r'id=["\']?gx-embedded-galaxy', text))
    if is_html and has_embed:          # a reader page carries bundle-marker text in its own scripts
        return _from_embed_text(text, notes)
    if _HDR_START.search(text):                                  # JS /<<<GALAXY-BUNDLE\b/ (ASCII word boundary)
        return _from_bundle_text(text, notes)
    if has_embed:
        return _from_embed_text(text, notes)
    if re.search(r'\.(txt|md|markdown|text)\Z', name, re.I):
        return _from_bundle_text(text, notes)
    _fail('E-CONTAINER', name + ' is not a galaxy: open a .galaxy or .zip file, a galaxy folder, or a text bundle (.txt).')


def _from_folder(folder, notes):
    listing = []
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dirnames.sort()
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            if os.path.islink(full):
                continue
            listing.append((os.path.relpath(full, folder).replace(os.sep, '/'), full))
    if len(listing) > LIMITS['entries']:
        _fail('E-SIZE', 'Too many files (%d; the limit is %d).' % (len(listing), LIMITS['entries']))
    total = sum(os.path.getsize(full) for _, full in listing)
    if total > LIMITS['bytes']:
        _fail('E-SIZE', 'The folder is too large (%s; the limit is %s).' % (fmt_mb(total), fmt_mb(LIMITS['bytes'])))
    raw = {}
    for rel, full in listing:
        if is_junk(rel):
            raw[rel] = b''
            continue
        check_path(rel)
        if rel in raw:
            _fail('E-PATH', 'Unsafe or duplicate path: %s appears twice.' % jstr(rel), rel)
        with open(full, 'rb') as f:
            raw[rel] = f.read()
    files, root = _rooted(raw, notes, True)
    return {'kind': 'folder', 'files': files, 'root': root, 'notes': notes, 'header': None, 'bundles': None}


def read_files(files, kind='folder', find_root=True):
    """A {path: bytes} map as an input (like F.readInput(Map)): path checks, junk, root, limits."""
    notes = []
    for p in files:
        check_path(p)
    f, root = _rooted({p: _bytes(d) for p, d in files.items()}, notes, find_root)
    return {'kind': kind, 'files': f, 'root': root, 'notes': notes, 'header': None, 'bundles': None}


# ---------------------------------------------------------------------------------------------
# §10 text bundle
# ---------------------------------------------------------------------------------------------

M_END_FILE = '<<<END FILE>>>'
M_END = '<<<END GALAXY-BUNDLE>>>'
_FENCE_OPEN = re.compile('[' + _WSC + ']*```[A-Za-z0-9_+-]*[' + _WSC + ']*')
_FENCE_CLOSE = re.compile('[' + _WSC + ']*```[' + _WSC + ']*')
_HDR = re.compile(r'<<<GALAXY-BUNDLE v([0-9]+)((?: +[^' + _WSC + r'=<>]+=[^' + _WSC + r'<>]*)*) *>>>')
_HDR_START = re.compile(r'<<<GALAXY-BUNDLE(?![A-Za-z0-9_])')
_FILE_LINE = re.compile(r'<<<FILE (.+)>>>', re.S)
_ANY_FILE = re.compile(r'<<<FILE .*>>>', re.S)


def parse_part(p):
    """F.parsePart: {n, of} from {n, of} or 'n/of'; None unless n and of are whole numbers with 1 <= n <= of (§8.3)."""
    def in_range(x):
        return x if 1 <= x['n'] <= x['of'] else None
    if is_obj(p) and is_int(p.get('n')) and is_int(p.get('of')):
        return in_range({'n': int(p['n']), 'of': int(p['of'])})
    m = re.fullmatch(r'([0-9]+)/([0-9]+)', jtrim(js_str(p)) if p is not None else '')
    return in_range({'n': int(m.group(1)), 'of': int(m.group(2))}) if m else None


def meta_profile(meta):
    """The profile galaxy/meta.json states, when it is one meta may state (galaxy or pathway); None otherwise.
    A folder is a part only through its manifest or bundle header, never through meta (§3.1)."""
    return meta['profile'] if is_obj(meta) and meta.get('profile') in ('galaxy', 'pathway') else None


def _parse_header(t):
    m = _HDR.fullmatch(t)
    if not m:
        return {'error': 'The bundle header is malformed: %s (expected <<<GALAXY-BUNDLE v1 profile=... >>>).' % t[:120]}
    h = {}
    for kv in [x for x in re.split(' +', m.group(2).strip(' ')) if x]:
        i = kv.index('=')
        h[kv[:i]] = kv[i + 1:]
    h['version'] = int(m.group(1))
    return {'header': h}


def parse_text_bundle(text):
    """F.parseTextBundle -> {bundles: [{header, files: {path: str}}], errors: [{code, path, msg}]}."""
    errors, bundles = [], []
    text = '' if text is None else js_str(text)
    if text.startswith('﻿'):
        text = text[1:]
    if _utf8_len(text) > LIMITS['bundle']:
        errors.append({'code': 'E-SIZE', 'path': '', 'msg': 'The pasted text is %s; a text bundle may be at most %s. '
                       'Ask the AI for smaller parts.' % (fmt_mb(_utf8_len(text)), fmt_mb(LIMITS['bundle']))})
        return {'bundles': bundles, 'errors': errors}
    lines = re.split(r'\r\n|\r|\n', text)
    st = {'cur': None, 'file': None, 'seen': False}

    def cut_off(b):
        return 'The answer was cut off: ask the AI to continue from FILE %s.' % (b['last'] or '(the first file)')

    def close_file():
        cur, file = st['cur'], st['file']
        ls = list(file['lines'])
        while ls and not jtrim(ls[0]):
            ls.pop(0)
        while ls and not jtrim(ls[-1]):
            ls.pop()
        if len(ls) >= 2 and _FENCE_OPEN.fullmatch(ls[0]) and _FENCE_CLOSE.fullmatch(ls[-1]):
            ls = ls[1:-1]
        else:
            ls = file['lines']
        if file['path'] in cur['files']:
            errors.append({'code': 'E-PATH', 'path': file['path'], 'msg': 'FILE %s appears twice in the same bundle.'
                           % file['path']})
            cur['bad'] = True
        else:
            cur['files'][file['path']] = '\n'.join(ls)
        st['file'] = None

    def close_bundle():
        cur = st['cur']
        h = cur['header'] or {}
        miss = []
        if not h.get('profile'):
            miss.append('profile')
        if h.get('profile') == 'part':
            miss += [k for k in ('galaxyId', 'workOrder', 'part') if not h.get(k)]
        if miss:
            errors.append({'code': 'E-MANIFEST', 'path': '', 'msg': 'The bundle header lacks %s (for example '
                           '<<<GALAXY-BUNDLE v1 profile=part galaxyId=gx_x workOrder=wo_x part=1/2>>>).' % ', '.join(miss)})
            cur['bad'] = True
        elif h.get('profile') and h['profile'] not in PROFILES:
            errors.append({'code': 'E-MANIFEST', 'path': '', 'msg': 'Unknown bundle profile "%s" (use galaxy, pathway '
                           'or part).' % h['profile']})
            cur['bad'] = True
        elif h.get('part') and not parse_part(h['part']):
            errors.append({'code': 'E-MANIFEST', 'path': '', 'msg': 'The bundle header part=%s must look like part=2/5 '
                           '(whole numbers, 1 <= n <= of).' % h['part']})
            cur['bad'] = True
        if not cur['bad']:
            bundles.append({'header': h, 'files': cur['files']})
        st['cur'] = None

    for raw in lines:
        t = jtrim(raw)
        if st['file'] is not None:
            if t == M_END_FILE:
                close_file()
                continue
            if t == M_END or _ANY_FILE.fullmatch(t) or _HDR_START.match(t):
                fp = st['file']['path']
                errors.append({'code': 'E-CONTAINER', 'path': fp, 'msg': 'FILE %s has no <<<END FILE>>> line: ask the AI '
                               'to send FILE %s again, complete.' % (fp, fp)})
                st['cur']['bad'] = True
                st['file'] = None
            else:
                st['file']['lines'].append(raw)
                continue
        if _HDR_START.match(t):
            st['seen'] = True
            if st['cur'] is not None:
                errors.append({'code': 'E-CONTAINER', 'path': st['cur']['last'] or '', 'msg': cut_off(st['cur'])})
                st['cur'] = None
            h = _parse_header(t)
            st['cur'] = {'header': h.get('header'), 'files': {}, 'last': None, 'bad': False}
            if h.get('error'):
                errors.append({'code': 'E-CONTAINER', 'path': '', 'msg': h['error']})
                st['cur']['bad'] = True
            elif h['header']['version'] > VERSION:
                errors.append({'code': 'E-MANIFEST', 'path': '', 'msg': 'This bundle uses format v%d: update the reader '
                               '(it reads v%d).' % (h['header']['version'], VERSION)})
                st['cur']['bad'] = True
            continue
        if st['cur'] is None:
            continue
        if t == M_END:
            close_bundle()
            continue
        fm = _FILE_LINE.fullmatch(t)
        if fm:
            p = jtrim(fm.group(1))
            why = path_problem(p)
            if why:
                errors.append({'code': 'E-PATH', 'path': p, 'msg': 'FILE %s has an unsafe path (%s).' % (jstr(p), why)})
                st['cur']['bad'] = True
            st['file'] = {'path': p, 'lines': []}
            st['cur']['last'] = p
            continue
        # anything else between files inside a bundle (a stray remark) is ignored
    if st['file'] is not None and st['cur'] is not None:
        st['cur']['last'] = st['file']['path']
        st['file'] = None
        st['cur']['bad'] = True
    if st['cur'] is not None:
        errors.append({'code': 'E-CONTAINER', 'path': st['cur']['last'] or '', 'msg': cut_off(st['cur'])})
    if not st['seen']:
        errors.append({'code': 'E-CONTAINER', 'path': '', 'msg': 'No text bundle found: the answer has no '
                       '<<<GALAXY-BUNDLE v1 ...>>> line.'})
    return {'bundles': bundles, 'errors': errors}


_MARKER_LINE = re.compile(r'<<<(FILE .*|END FILE|END GALAXY-BUNDLE|GALAXY-BUNDLE(?![A-Za-z0-9_]).*)>>>', re.S)


def emit_text_bundle(header, files):
    """F.emitTextBundle: header {profile, galaxyId?, workOrder?, part?} + {path: str|bytes} -> text."""
    header = dict(header or {})
    if not header.get('profile'):
        _fail('E-MANIFEST', 'emitTextBundle needs header.profile.')
    if is_obj(header.get('part')):
        header['part'] = '%s/%s' % (js_str(header['part'].get('n')), js_str(header['part'].get('of')))
    if header.get('part') not in (None, '') and not parse_part(header['part']):
        _fail('E-MANIFEST', 'emitTextBundle: part=%s must look like 2/5 (whole numbers, 1 <= n <= of).' % js_str(header['part']))
    header.pop('version', None)
    first = ['profile', 'galaxyId', 'workOrder', 'part']
    keys = [k for k in first if header.get(k) not in (None, '')]
    keys += sorted(k for k in header if k not in first and header[k] not in (None, ''))
    out = '<<<GALAXY-BUNDLE v1 ' + ' '.join('%s=%s' % (k, re.sub('[' + _WSC + '<>]+', '_', js_str(header[k])))
                                           for k in keys) + '>>>\n'
    for p, d in files.items():
        if p.startswith('originals/'):
            continue
        why = path_problem(p)
        if why:
            _fail('E-PATH', 'Cannot bundle %s: %s.' % (p, why), p)
        text = d if isinstance(d, str) else _decode(d)
        text = re.sub(r'\n+\Z', '', re.sub(r'\r\n?', '\n', text))
        if any(_MARKER_LINE.fullmatch(jtrim(l)) for l in text.split('\n')):
            _fail('E-CONTAINER', p + ' contains a bundle marker line and cannot be bundled.', p)
        out += '<<<FILE ' + p + '>>>\n' + text + '\n' + M_END_FILE + '\n'
    return out + M_END + '\n'


# ---------------------------------------------------------------------------------------------
# §9.1 / §9.2 fill levels
# ---------------------------------------------------------------------------------------------

BAR = {
    'core': {'sec': (5, 9), 'slides': (6, 9), 'inter': 2, 'cp': (4, 5), 'nonMcq': 1, 'prereqFirst': True, 'recapLast': True},
    'standard': {'sec': (4, 9), 'slides': (4, 9), 'inter': 1, 'cp': (3, 5), 'nonMcq': 0, 'prereqFirst': False,
                 'recapLast': True},
    'detail': {'sec': (3, 7), 'slides': (3, 7), 'inter': 1, 'cp': (2, 4), 'nonMcq': 0, 'prereqFirst': False,
               'recapLast': False},
}


def lesson_bar(node, lesson, ctx=None):
    """The §9.2 bar: {ok, why: [below the minimum], over: [above the maximum]}.
    ctx = {'hasPrereq': bool} (default: the lesson lists guide.needs)."""
    pr = node.get('priority') if is_obj(node) else None
    b = BAR.get(pr) if isinstance(pr, str) and pr in BAR else BAR['standard']
    why, over = [], []
    if not is_obj(lesson):
        return {'ok': False, 'why': ['no lesson'], 'over': over}
    g = lesson.get('guide') if is_obj(lesson.get('guide')) else {}
    secs = [s for s in arr(g.get('sections')) if is_obj(s)]
    slides = [s for s in arr(lesson.get('slides')) if is_obj(s)]
    cp = [q for q in arr(lesson.get('checkpoint')) if is_obj(q)]
    if is_obj(ctx) and isinstance(ctx.get('hasPrereq'), bool):
        has_prereq = ctx['hasPrereq']
    else:
        has_prereq = len(arr(g.get('needs'))) > 0

    def rng(n, r, what):
        if n < r[0]:
            why.append('%d %s (needs %d to %d)' % (n, what, r[0], r[1]))
        elif n > r[1]:
            over.append('%d %s (at most %d)' % (n, what, r[1]))
    rng(len(secs), b['sec'], 'guide sections')
    if b['prereqFirst'] and has_prereq and secs and secs[0].get('kind') != 'prereq':
        why.append('the guide must start with a prereq section')
    if b['recapLast'] and secs and secs[-1].get('kind') != 'recap':
        why.append('the guide must end with a recap section')
    rng(len(slides), b['slides'], 'slides')
    inter = len([s for s in slides if is_str(s.get('primitive')) and s.get('primitive') != 'text'])
    if inter < b['inter']:
        why.append('%d interactive slides (needs %d+)' % (inter, b['inter']))
    rng(len(cp), b['cp'], 'checkpoint questions')
    if b['nonMcq'] and len([q for q in cp if q.get('type') != 'mcq']) < b['nonMcq']:
        why.append('the checkpoint needs at least one question that is not mcq')
    return {'ok': not why, 'why': why, 'over': over}


def has_audit(a):
    return is_obj(a) and (non_empty(a.get('note')) or (is_num(a.get('refuted')) and is_num(a.get('fixed'))
                                                       and float(a['fixed']) >= float(a['refuted'])))


def fill_level(node, lesson, ctx=None):
    """F.fillLevel: 'L0' | 'L1' | 'L2' | 'L3' (§9.1)."""
    card = node.get('card') if is_obj(node) and is_obj(node.get('card')) else None
    if card is None or not non_empty(card.get('definition')):
        return 'L0'
    if not is_obj(lesson) or js_truthy(lesson.get('quick')):
        return 'L1'
    if not lesson_bar(node, lesson, ctx)['ok']:
        return 'L1'
    return 'L3' if has_audit(lesson.get('audit')) else 'L2'


# ---------------------------------------------------------------------------------------------
# §3.6 quotes
# ---------------------------------------------------------------------------------------------

_QMAP = {ord('‘'): "'", ord('’'): "'", ord('′'): "'", ord('“'): '"', ord('”'): '"',
         ord('–'): '-', ord('—'): '-', ord('−'): '-', ord('→'): '->'}
_MARKS = re.compile('[̀-ͯ]')


def norm_quote(s):
    """F.normQuote: NFD, drop U+0300-U+036F, fold quotes/dashes/arrow, collapse whitespace, trim, lowercase."""
    s = '' if s is None else js_str(s)
    s = _MARKS.sub('', unicodedata.normalize('NFD', s)).translate(_QMAP)
    return jtrim(_WS_RUN.sub(' ', s)).lower()


def _cells_of(t, out):
    if isinstance(t, list):
        for x in t:
            _cells_of(x, out)
    elif isinstance(t, str):
        out.append(t)
    elif is_num(t):
        out.append(js_str(t))
    return out


def unit_hay(u):
    if not is_obj(u):
        return ''
    h = u.get('\x00hay')
    if h is None:
        parts = [u.get(k) if is_str(u.get(k)) else '' for k in ('title', 'text', 'notes')] + _cells_of(u.get('tables'), [])
        h = norm_quote(' '.join(parts))
    return h


def quote_in(unit, quote):
    """True when the quote is a substring of the normalized unit (title, text, notes, every table cell)."""
    q = norm_quote(quote)
    return bool(q) and q in unit_hay(unit)


# ---------------------------------------------------------------------------------------------
# §8.3 manifest
# ---------------------------------------------------------------------------------------------

def _iso_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _get(files, p):
    try:
        return read_json(files, p)
    except FormatError:
        return None


def _prereq_targets(edges):
    return set(e.get('target') for e in arr(edges) if is_obj(e) and e.get('type') == 'requires'
               and isinstance(e.get('target'), str))


def build_manifest(files, profile=None, exported_by=None, includes=None, base=None, work_order_id=None, part=None,
                   exported_at=None):
    """F.buildManifest: §8.3 manifest of {path: bytes}. base = {galaxyId, revision, contentHash} or a base context."""
    keys = sorted(p for p in files if p != 'manifest.json')
    meta = _get(files, 'galaxy/meta.json')
    meta = meta if is_obj(meta) else {}
    profile = profile or meta_profile(meta) or ('galaxy' if 'galaxy/meta.json' in files else 'part')
    entries = {p: digest(p, files[p]) for p in keys}
    ch = content_hash(entries)
    base_ctx = base if is_obj(base) and isinstance(base.get('nodes'), list) else None
    if base_ctx:
        bm = base_ctx.get('meta') or {}
        base_ref = {'galaxyId': bm.get('galaxyId'), 'revision': bm.get('revision') or 1,
                    'contentHash': bm.get('contentHash')}
    else:
        base_ref = json.loads(canon(base)) if is_obj(base) else None
    nodes_doc, edges_doc = _get(files, 'galaxy/nodes.json'), _get(files, 'galaxy/edges.json')
    pw_doc, idx = _get(files, 'galaxy/pathways.json'), _get(files, 'sources/index.json')
    nodes = [n for n in arr(nodes_doc.get('nodes') if is_obj(nodes_doc) else None) if is_obj(n)]
    if base_ctx and not nodes_doc:
        nodes += base_ctx['nodes']
    lessons = {}
    for p in keys:
        m = re.fullmatch(r'lessons/([^/]+)\.json', p)
        if not m:
            continue
        l = _get(files, p)
        if is_obj(l):
            lessons[l['nodeId'] if is_str(l.get('nodeId')) else m.group(1)] = l
    edges = arr(edges_doc.get('edges') if is_obj(edges_doc) else None)
    if base_ctx and not edges_doc:
        edges = edges + base_ctx['edges']
    pre = _prereq_targets(edges)
    fill = {k: 0 for k in LEVELS}

    def hp(i, l):
        g = l.get('guide') if is_obj(l) and is_obj(l.get('guide')) else {}
        return {'hasPrereq': i in pre or len(arr(g.get('needs'))) > 0}
    if profile == 'part':
        for i, l in lessons.items():
            n = next((x for x in nodes if x.get('id') == i), None) or {
                'id': i, 'priority': 'standard', 'card': {'definition': 'unknown node'}}
            fill[fill_level(n, l, hp(i, l))] += 1
    else:
        for n in nodes:
            l = lessons.get(n.get('id')) if is_str(n.get('id')) else None
            fill[fill_level(n, l, hp(n.get('id'), l))] += 1
    units = 0
    for p in keys:
        if re.fullmatch(r'sources/units/[^/]+\.json', p):
            u = _get(files, p)
            units += len(arr(u.get('units') if is_obj(u) else None))
    counts = {'nodes': 0 if profile == 'part' else len(nodes),
              'edges': len(arr(edges_doc.get('edges') if is_obj(edges_doc) else None)),
              'pathways': len(arr(pw_doc.get('pathways') if is_obj(pw_doc) else None)), 'lessons': len(lessons),
              'sources': len(arr(idx.get('sources'))) if is_obj(idx) else len([p for p in keys if p.startswith('sources/units/')]),
              'units': units, 'saves': len([p for p in keys if re.fullmatch(r'saves/[^/]+\.galsave', p)])}
    inc = {'unitText': any(p.startswith('sources/units/') for p in keys), 'originals': any(p.startswith('originals/') for p in keys),
           'progress': counts['saves'] > 0, 'layout': 'galaxy/layout.json' in keys}
    inc.update(includes if is_obj(includes) else {})
    rev = meta.get('revision') if is_int(meta.get('revision')) else ((base_ref or {}).get('revision') or 1)
    m = {'format': 'galaxy', 'schemaVersion': VERSION, 'minReaderVersion': 1, 'profile': profile,
         'galaxyId': meta.get('galaxyId') or (base_ref or {}).get('galaxyId') or None, 'revision': rev,
         'contentHash': ch, 'hashScope': 'v1', 'title': meta.get('title') or '', 'subject': meta.get('subject') or '',
         'language': meta.get('language') or 'en', 'exportedAt': exported_at or _iso_now(),
         'exportedBy': exported_by or '%s %s' % (TOOL, TOOL_VERSION), 'counts': counts, 'fill': fill, 'includes': inc}
    if profile == 'part':
        m['base'] = base_ref or {'galaxyId': m['galaxyId'], 'revision': None, 'contentHash': None}
    # any profile: a split answer's part 1 is a galaxy or pathway that declares its part and work order (§11.1)
    if work_order_id:
        m['workOrderId'] = work_order_id
    if part not in (None, ''):
        pt = parse_part(part)
        if not pt:
            _fail('E-MANIFEST', 'buildManifest: part %s must be {n, of} or "n/of" (whole numbers, 1 <= n <= of).'
                  % canon(part))
        m['part'] = pt
    m['entries'] = entries
    return m


def verify_manifest(files):
    """F.verifyManifest -> {ok, mismatched, unlisted, missingListed, contentHashOk, contentHash, digests, manifest, error?}."""
    res = {'ok': False, 'mismatched': [], 'unlisted': [], 'missingListed': [], 'contentHashOk': False,
           'contentHash': None, 'digests': {}, 'manifest': None}
    try:
        m = read_json(files, 'manifest.json')
    except FormatError as e:
        res['error'] = e.msg
        return res
    if not is_obj(m):
        res['error'] = 'manifest.json is not an object.' if 'manifest.json' in files else 'There is no manifest.json.'
        return res
    res['manifest'] = m
    if not is_obj(m.get('entries')):
        res['error'] = 'manifest.json has no entries table.'
        return res
    ent = m['entries']
    for p in sorted(ent, key=_u16):
        if p == 'manifest.json':
            continue
        if p not in files:
            res['missingListed'].append(p)
            continue
        d = digest(p, files[p])
        res['digests'][p] = d
        if d != ent[p]:
            res['mismatched'].append(p)
    res['unlisted'] = sorted((p for p in files if p != 'manifest.json' and p not in ent), key=_u16)
    res['contentHash'] = content_hash(res['digests'])
    res['contentHashOk'] = res['contentHash'] == m.get('contentHash') and not any(in_scope(p) for p in res['missingListed'])
    res['ok'] = not res['mismatched'] and not res['missingListed'] and res['contentHashOk']
    return res


# ---------------------------------------------------------------------------------------------
# a galaxy's files as the base of a part (what F.toPack(base).pack gives the JS validator)
# ---------------------------------------------------------------------------------------------

def base_context(files):
    """{meta, nodes, sources: {sid: {meta, units}}, edges, pathways, lessons} of a galaxy's {path: bytes}."""
    if is_obj(files) and isinstance(files.get('nodes'), list) and 'sources' in files:
        return files                                   # already a context
    try:
        man = read_json(files, 'manifest.json') if 'manifest.json' in files else None
    except FormatError:
        man = None
    listed = man.get('entries') if is_obj(man) and is_obj(man.get('entries')) else None

    def get(p):
        if listed is not None and p not in listed:
            return None
        return _get(files, p)
    paths = sorted(p for p in files if listed is None or p in listed)
    meta = dict(get('galaxy/meta.json')) if is_obj(get('galaxy/meta.json')) else {}
    meta.pop('contentHash', None)
    if is_obj(man) and is_str(man.get('contentHash')):
        meta['contentHash'] = man['contentHash']
    nd = get('galaxy/nodes.json')
    nodes = [n for n in arr(nd.get('nodes') if is_obj(nd) else None) if is_obj(n)]
    pd = get('galaxy/pathways.json') or {}
    pathways = arr(pd.get('pathways')) if is_obj(pd) else []
    ed = get('galaxy/edges.json')
    edges = arr(ed.get('edges')) if is_obj(ed) else []
    lessons = {}
    for p in paths:
        m = re.fullmatch(r'lessons/([^/]+)\.json', p)
        if m:
            l = get(p)
            if is_obj(l):
                lessons[l['nodeId'] if is_str(l.get('nodeId')) else m.group(1)] = l
    sources = {}
    idx = get('sources/index.json')
    for s in arr(idx.get('sources') if is_obj(idx) else None):
        if is_obj(s) and is_str(s.get('id')):
            sources[s['id']] = {'meta': s, 'units': None}
    for p in paths:
        m = re.fullmatch(r'sources/units/([^/]+)\.json', p)
        if not m:
            continue
        u = get(p)
        if not is_obj(u):
            continue
        sid = u['id'] if is_str(u.get('id')) else m.group(1)
        if sid not in sources:
            sources[sid] = {'meta': {'id': sid, 'unitCount': len(arr(u.get('units')))}, 'units': None}
        sources[sid]['units'] = arr(u.get('units'))
    return {'meta': meta, 'nodes': nodes, 'sources': sources, 'edges': edges, 'pathways': pathways, 'lessons': lessons}


# ---------------------------------------------------------------------------------------------
# §9.6 validator (a port of runValidate in 35-format.js)
# ---------------------------------------------------------------------------------------------

_BAD = object()
_KNOWN = [re.compile(x) for x in (r'manifest\.json', r'README\.txt', r'galaxy/(meta|nodes|edges|pathways|layout|tombstones)\.json',
                                  r'lessons/[^/]+\.json', r'guide/main\.json', r'exam/(mock|profiles)\.json',
                                  r'sources/index\.json', r'sources/units/[^/]+\.json', r'ledger/coverage\.json',
                                  r'originals/.+', r'saves/[^/]+\.galsave', r'work/.+', r'patches/.+')]
_PART_OK = [re.compile(x) for x in (r'manifest\.json', r'README\.txt', r'lessons/[^/]+\.json', r'guide/main\.json',
                                    r'exam/mock\.json', r'work/.+')]
_HTML_TAG = re.compile(r'</?(a|b|i|u|p|br|hr|div|span|img|script|style|iframe|table|tr|td|th|ul|ol|li|strong|em|code|pre'
                       r'|h[1-6]|svg|video|audio|object|embed|form|input|button|link|meta)\b[^>]*>', re.I | re.A)
_MD_LINK = re.compile(r'!?\[[^\]]*\]\([^)]*\)')
_CODE_SPAN = re.compile(r'`[^`\n]+`')


def outside_code(s):
    """Text outside markdown-lite code spans (a backtick pair on one line, CR removed, as readers render them):
    markup shown as content goes in backticks (§4.1)."""
    return _CODE_SPAN.sub(' ', s.replace('\r', ''))


def known_path(p, profile='galaxy'):
    """True when the path is in the §2.1 file table (for a part: the files a part may carry)."""
    pats = _PART_OK if profile == 'part' else _KNOWN
    return any(r.fullmatch(p) for r in pats)


def _flat_ids(pw):
    if not is_obj(pw):
        return []
    out = []
    for s in arr(pw.get('stages')):
        out.extend(arr(s.get('nodeIds')) if is_obj(s) else [])
    return out


def _find_cycles(ids, adj, mx):
    color, cycles = {}, []
    for s in ids:
        if color.get(s):
            continue
        stack, path = [[s, 0]], [s]
        color[s] = 1
        while stack:
            top = stack[-1]
            nb = adj.get(top[0], [])
            if top[1] < len(nb):
                w = nb[top[1]]
                top[1] += 1
                c = color.get(w, 0)
                if c == 0:
                    color[w] = 1
                    stack.append([w, 0])
                    path.append(w)
                elif c == 1:
                    cycles.append(path[path.index(w):] + [w])
                    if len(cycles) >= mx:
                        return cycles
            else:
                color[top[0]] = 2
                stack.pop()
                path.pop()
    return cycles


def validate(files, profile=None, work_order=None, base=None, check_quotes=True, kind=None, header=None, notes=None,
             check_focus=True):
    """F.validate: the §9.6 report for {path: bytes}. base = the base galaxy (its {path: bytes} or base_context()).
    kind = 'zip'|'folder'|'bundle'|'embed' (a zip needs a manifest; a folder without one opens Unverified).
    check_focus=False skips the focus-coverage check (E-FOCUS), as merge_part does for each lesson.
    -> {ok, profile, errors, warnings, stats, verified, verification, contentHash, manifest}"""
    pre = {'verify': None, 'contentHash': None}
    if 'manifest.json' in files:
        pre['verify'] = verify_manifest(files)
    v = pre['verify']
    pre['contentHash'] = v['contentHash'] if v and is_obj(v['manifest']) and is_obj(v['manifest'].get('entries')) \
        else content_hash(files)
    opts = {'profile': profile, 'workOrder': work_order, 'base': base_context(base) if base is not None else None,
            'checkQuotes': check_quotes, 'kind': kind, 'header': header, 'notes': notes, 'checkFocus': check_focus}
    return _run_validate(files, opts, pre)


def validate_input(inp, profile=None, work_order=None, base=None, check_quotes=True):
    """validate() on a read_input() result (its kind, header and notes are used)."""
    return validate(inp['files'], profile=profile, work_order=work_order, base=base, check_quotes=check_quotes,
                    kind=inp.get('kind'), header=inp.get('header'), notes=inp.get('notes'))


def _run_validate(files, opts, pre):
    R = {'ok': False, 'profile': None, 'errors': [], 'warnings': [],
         'stats': {'nodes': 0, 'lessons': 0, 'fill': {k: 0 for k in LEVELS}, 'focus': {},
                   'quotes': {'checked': 0, 'verified': 0, 'unverifiable': 0, 'failed': 0}},
         'verified': False, 'verification': 'unverified', 'contentHash': None, 'manifest': None}
    dropped = [0]

    def E(code, path, msg):
        if len(R['errors']) < MAX_ERRORS:
            R['errors'].append({'code': code, 'path': path or '', 'msg': msg})
        else:
            dropped[0] += 1

    def W(code, path, msg):
        if len(R['warnings']) < MAX_ERRORS:
            R['warnings'].append({'code': code, 'path': path or '', 'msg': msg})
    for n in arr(opts.get('notes')):
        if is_obj(n) and is_str(n.get('code')):
            (E if n['code'].startswith('E-') else W)(n['code'], n.get('path'), n.get('msg'))

    # ---- paths and limits ----
    total = 0
    for p, d in files.items():
        why = path_problem(p)
        if why:
            E('E-PATH', p, 'Unsafe path %s: %s.' % (jstr(js_str(p)), why))
        n = len(_bytes(d))
        total += n
        if is_json_path(p) and n > LIMITS['json']:
            E('E-SIZE', p, '%s is %s; a JSON file may be at most %s.' % (p, fmt_mb(n), fmt_mb(LIMITS['json'])))
    if len(files) > LIMITS['entries']:
        E('E-SIZE', '', 'Too many files (%d; the limit is %d).' % (len(files), LIMITS['entries']))
    if total > LIMITS['bytes']:
        E('E-SIZE', '', 'The galaxy is too large (%s; the limit is %s).' % (fmt_mb(total), fmt_mb(LIMITS['bytes'])))

    # ---- JSON (each file parsed once) ----
    vf = [files]
    J = {}

    def getJ(p):
        if p in J:
            return J[p]
        val = None
        if p in vf[0]:
            try:
                val = read_json(vf[0], p)
            except FormatError as e:
                E(e.code or 'E-JSON', p, e.msg)
                val = _BAD
        J[p] = val
        return val

    def ok(x):
        return x is not None and x is not _BAD

    # ---- manifest + digests ----
    mf = None
    mp = 'manifest.json'
    if 'manifest.json' in files:
        try:
            mf = read_json(files, 'manifest.json')
        except FormatError as e:
            E(e.code or 'E-JSON', 'manifest.json', e.msg)
            mf = _BAD
        J['manifest.json'] = mf
    if ok(mf):
        R['manifest'] = mf if is_obj(mf) else None
        if not is_obj(mf):
            E('E-MANIFEST', mp, 'manifest.json must be a JSON object.')
        else:
            if mf.get('format') == 'galaxy-handoff':
                E('E-MANIFEST', mp, 'This is a handoff package (a work order for an AI), not a galaxy: give it to the AI, '
                                    'then open the galaxy it returns.')
            elif mf.get('format') != 'galaxy':
                E('E-MANIFEST', mp, 'manifest.json "format" must be "galaxy".')
            sv = mf.get('schemaVersion')
            if not is_int(sv) or sv < 1:
                E('E-MANIFEST', mp, 'manifest.json needs an integer "schemaVersion" (1).')
            elif sv > VERSION:
                E('E-MANIFEST', mp, 'This galaxy uses schema version %s: update the reader (it reads version %d).'
                  % (_num_str(sv), VERSION))
            mr = mf.get('minReaderVersion')
            if mr is not None and not is_int(mr):
                E('E-MANIFEST', mp, '"minReaderVersion" must be an integer.')
            elif is_int(mr) and mr > VERSION:
                E('E-MANIFEST', mp, 'This galaxy needs reader version %s: update the reader (it is version %d).'
                  % (_num_str(mr), VERSION))
            if mf.get('profile') is not None and mf.get('profile') not in PROFILES:
                E('E-MANIFEST', mp, 'manifest.json "profile" must be galaxy, pathway or part.')
            if not non_empty_raw(mf.get('galaxyId')):
                E('E-MANIFEST', mp, 'manifest.json needs "galaxyId".')
            if not (is_str(mf.get('contentHash')) and RE_DIGEST.fullmatch(mf['contentHash'])):
                E('E-MANIFEST', mp, 'manifest.json needs "contentHash" ("sha256:" and 64 hex digits).')
            if mf.get('hashScope') is not None and mf.get('hashScope') != 'v1':
                W('W-MANIFEST', mp, '"hashScope" should be "v1".')
            ent = mf.get('entries')
            entries_ok = is_obj(ent) and all(is_str(x) and RE_DIGEST.fullmatch(x) for x in ent.values())
            if not entries_ok:
                E('E-MANIFEST', mp, 'manifest.json needs an "entries" table mapping every file to "sha256:" + 64 hex digits.')
            if mf.get('profile') == 'part' and not is_obj(mf.get('base')):
                E('E-MANIFEST', mp, 'A part manifest needs "base": {galaxyId, revision, contentHash}.')
            if mf.get('part') is not None and not (is_obj(mf['part']) and parse_part(mf['part'])):
                E('E-MANIFEST', mp, 'manifest.json "part" must be {"n": n, "of": of} with whole numbers 1 <= n <= of.')
            if entries_ok:
                unlisted = sorted((p for p in files if p != 'manifest.json' and p not in ent), key=_u16)
                for p in unlisted:
                    W('W-UNLISTED', p, p + ' is not listed in manifest.json: ignored.')
                if unlisted:
                    vf[0] = {p: d for p, d in files.items() if p == 'manifest.json' or p in ent}
                vv = pre and pre['verify']
                if vv:
                    for p in vv['mismatched']:
                        E('E-HASH', p, p + ' does not match its digest in manifest.json: it was changed after export. '
                                           'Export again, or refresh the manifest.')
                    for p in vv['missingListed']:
                        E('E-HASH', p, p + ' is listed in manifest.json but missing.')
                    if is_str(mf.get('contentHash')) and RE_DIGEST.fullmatch(mf['contentHash']) and not vv['contentHashOk']:
                        E('E-HASH', mp, 'The contentHash in manifest.json does not match the files.')
                    R['verified'] = vv['ok']
        R['verification'] = 'unchecked' if not pre else (
            'verified' if R['verified'] and not any(e['code'] == 'E-MANIFEST' for e in R['errors']) else 'failed')
    elif mf is _BAD:
        R['verification'] = 'failed'
    else:
        if opts.get('kind') == 'zip':
            E('E-MANIFEST', mp, 'A .galaxy or .zip must contain manifest.json: export it again (or run the pack command).')
        elif opts.get('kind') != 'bundle':
            W('W-MANIFEST', mp, 'No manifest.json: the galaxy opens as Unverified.')
    R['contentHash'] = pre['contentHash'] if pre else None
    if R['verification'] != 'verified':
        R['verified'] = False
    VF = vf[0]

    # ---- profile ----
    meta = getJ('galaxy/meta.json')
    hdr = opts['header'] if is_obj(opts.get('header')) else {}
    profile = opts.get('profile') or (mf.get('profile') if is_obj(mf) and is_str(mf.get('profile')) and mf.get('profile') else None) \
        or (hdr.get('profile') if is_str(hdr.get('profile')) and hdr.get('profile') else None) \
        or meta_profile(meta)
    if not profile:
        profile = 'galaxy' if 'galaxy/meta.json' in VF else ('part' if any(p.startswith('lessons/') for p in VF) else 'galaxy')
    if profile not in PROFILES:
        E('E-SCHEMA', '', 'Unknown profile "%s": use galaxy, pathway or part.' % js_str(profile))
        profile = 'galaxy'
    R['profile'] = profile
    is_part, is_pathway = profile == 'part', profile == 'pathway'
    if is_obj(mf) and is_str(mf.get('profile')) and is_obj(meta) and is_str(meta.get('profile')) \
            and mf['profile'] != meta['profile']:
        E('E-MANIFEST', mp, 'manifest.json says profile "%s" but galaxy/meta.json says "%s".' % (mf['profile'], meta['profile']))

    # ---- known paths ----
    for p in VF:
        if path_problem(p):
            continue
        if is_part and not any(r.fullmatch(p) for r in _PART_OK):
            W('W-UNKNOWN-PATH', p, p + ' is ignored in a part (a part carries lessons, optionally guide/main.json or '
                                       'exam/mock.json, and work/report.json).')
            continue
        if not any(r.fullmatch(p) for r in _KNOWN):
            W('W-UNKNOWN-PATH', p, 'Unknown file ' + p + ': ignored.')
        # README.txt and sources/units/<SID>.json are spec names (source ids are capitals); originals keep their names
        elif (p != 'README.txt' and not p.startswith('originals/') and not _UNITS_PATH.fullmatch(p)
              and not RE_NAME.fullmatch(p)):
            W('W-PATH', p, 'File names should use only a-z, 0-9, ".", "_", "-" and "/": ' + p + '.')

    # ---- required files ----
    def need(p, must):
        if p not in VF:
            if must:
                E('E-MISSING', p, '%s is missing (required in a %s).' % (p, profile))
            else:
                W('W-MISSING', p, '%s is missing (recommended in a %s).' % (p, profile))
    if profile == 'galaxy':
        for p in ('galaxy/meta.json', 'galaxy/nodes.json', 'galaxy/edges.json', 'galaxy/pathways.json'):
            need(p, True)
        for p in ('guide/main.json', 'sources/index.json', 'ledger/coverage.json'):
            need(p, False)
    if is_pathway:
        for p in ('galaxy/meta.json', 'galaxy/nodes.json', 'galaxy/pathways.json', 'guide/main.json'):
            need(p, True)
        for p in ('exam/mock.json', 'sources/index.json'):
            need(p, False)
    if is_part and not any(re.fullmatch(r'lessons/[^/]+\.json|guide/main\.json|exam/mock\.json', p) for p in VF):
        E('E-MISSING', '', 'This part contains no lessons (lessons/<nodeId>.json), no guide and no paper.')

    # ---- W-NUMBER ----
    def num_scan(val, p):
        stack = [val]
        while stack:
            x = stack.pop()
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                a = abs(x)
                if a != 0 and (a < 1e-6 or a >= 1e21 or a != a):
                    W('W-NUMBER', p, '%s contains the number %s: magnitudes below 1e-6 or from 1e21 up are not portable; '
                                     'round or scale it.' % (p, js_str(x)))
                    return
            elif isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, dict):
                stack.extend(x.values())

    # ---- context: nodes, sources ----
    base = opts.get('base')
    node_by_id = {}
    sources = {}
    have_sources = [False]
    if is_part:
        if base:
            for n in arr(base.get('nodes')):
                if is_obj(n) and is_str(n.get('id')) and not js_truthy(n.get('stress')):
                    node_by_id[n['id']] = n
            for sid, s in (base.get('sources') or {}).items():
                units = s.get('units') if isinstance(s.get('units'), list) else None
                by_n = None
                if units is not None:
                    by_n = {}
                    for u in units:
                        if is_obj(u) and _hashable(u.get('n')):
                            by_n[_nkey(u.get('n'))] = u
                sources[sid] = {'meta': s.get('meta') or {'id': sid}, 'units': units, 'byN': by_n}
                have_sources[0] = True
    else:
        idx_p = 'sources/index.json'
        idx = getJ(idx_p)
        if ok(idx):
            num_scan(idx, idx_p)
            if not is_obj(idx) or not isinstance(idx.get('sources'), list):
                E('E-SCHEMA', idx_p, 'sources/index.json must be {"sources": [...]}.')
            else:
                for i, s in enumerate(idx['sources']):
                    w = 'source ' + (s['id'] if is_obj(s) and is_str(s.get('id')) else '#%d' % (i + 1))
                    if not is_obj(s):
                        E('E-SCHEMA', idx_p, w + ' must be an object.')
                        continue
                    if not is_str(s.get('id')) or not RE_SID.fullmatch(s['id']):
                        E('E-ID', idx_p, w + ': the source id must look like L1, T2, P1 or D3 (1-3 capitals and 1-3 digits).')
                        continue
                    if s['id'] in sources:
                        E('E-ID', idx_p, 'Duplicate source id ' + s['id'] + '.')
                        continue
                    if not non_empty(s.get('title')):
                        E('E-SCHEMA', idx_p, w + ': title is missing.')
                    if s.get('role') not in ROLES:
                        E('E-SCHEMA', idx_p, w + ': role must be one of ' + ', '.join(ROLES) + '.')
                    if s.get('kind') is not None and s.get('kind') not in SOURCE_KINDS:
                        E('E-SCHEMA', idx_p, w + ': kind must be one of ' + ', '.join(SOURCE_KINDS) + '.')
                    if s.get('unitKind') not in UNIT_KINDS:
                        E('E-SCHEMA', idx_p, w + ': unitKind must be slide, page, section or sheet.')
                    if not is_int(s.get('unitCount')) or s['unitCount'] < 0:
                        E('E-SCHEMA', idx_p, w + ': unitCount must be an integer.')
                    io_ = s.get('imageOnly')
                    if io_ is not None and not (isinstance(io_, list) and all(is_int(x) for x in io_)):
                        E('E-SCHEMA', idx_p, w + ': imageOnly must be a list of unit numbers.')
                    if s.get('sha256') is not None and not (is_str(s['sha256']) and RE_DIGEST.fullmatch(s['sha256'])):
                        W('W-SCHEMA', idx_p, w + ': sha256 should be "sha256:" and 64 hex digits.')
                    sources[s['id']] = {'meta': s, 'units': None, 'byN': None}
                    have_sources[0] = True
        for p in sorted(VF):
            m = re.fullmatch(r'sources/units/([^/]+)\.json', p)
            if not m:
                continue
            d = getJ(p)
            if not ok(d):
                continue
            num_scan(d, p)
            sid = m.group(1)
            if not is_obj(d) or not isinstance(d.get('units'), list):
                E('E-SCHEMA', p, '%s must be {"id": "%s", "units": [...]}.' % (p, sid))
                continue
            if d.get('id') != sid:
                E('E-ID', p, '%s: "id" must be "%s" (the file name).' % (p, sid))
            if sid not in sources:
                if ok(idx):
                    E('E-ID', p, 'Source %s has units but is not listed in sources/index.json.' % sid)
                sources[sid] = {'meta': {'id': sid}, 'units': None, 'byN': None}
            have_sources[0] = True
            units, by_n, gap = d['units'], {}, False
            for i, u in enumerate(units):
                w = '%s unit %d' % (sid, i + 1)
                if not is_obj(u):
                    E('E-SCHEMA', p, w + ' must be an object.')
                    continue
                if not _num_eq(u.get('n'), i + 1) and not gap:
                    E('E-SCHEMA', p, 'Units must be numbered 1..%d in order without gaps: entry %d has n=%s.'
                      % (len(units), i + 1, jstr(u.get('n', UNDEF))))
                    gap = True
                if is_int(u.get('n')):
                    by_n[_nkey(u['n'])] = u
                for k in ('title', 'text', 'notes'):
                    if u.get(k) is not None and not is_str(u.get(k)):
                        E('E-SCHEMA', p, '%s: %s must be text.' % (w, k))
                t = u.get('tables')
                if t is not None and not (isinstance(t, list) and all(isinstance(tb, list) and all(isinstance(r, list) for r in tb)
                                                                       for tb in t)):
                    E('E-SCHEMA', p, w + ': tables must be a list of tables, each a list of rows, each a list of cells.')
                if u.get('textState') is not None and u.get('textState') not in TEXT_STATES:
                    E('E-SCHEMA', p, w + ': textState must be text, image-only, empty or transcribed.')
            sm = sources[sid]['meta']
            if is_int(sm.get('unitCount')) and sm['unitCount'] != len(units):
                E('E-SCHEMA', p, '%s has %d units but sources/index.json says unitCount %s.' % (sid, len(units), js_str(sm['unitCount'])))
            sources[sid]['units'] = units
            sources[sid]['byN'] = by_n
        if profile == 'galaxy':
            for sid in sources:
                if sources[sid]['units'] is None:
                    W('W-MISSING', 'sources/units/%s.json' % sid, 'sources/units/%s.json is missing: refs to %s are checked '
                                                                  'for range only and its quotes cannot be verified.' % (sid, sid))
    unver, transcribed = {}, {}
    hay_cache = {}

    def hay(u):
        k = id(u)
        if k not in hay_cache:
            hay_cache[k] = unit_hay(u)
        return hay_cache[k]

    def check_ref_quote(ref, quote, p, where, require_ref=False, require_quote=False, missing_code=None, ref_code=None):
        unit, src, ref_ok = None, None, False
        if ref is None or ref == '':
            if require_ref:
                E(ref_code or 'E-REF', p, where + ': a ref (e.g. L3#12) is required.')
        else:
            r = parse_ref(ref)
            if not r:
                E('E-REF', p, '%s: %s is not a valid ref (use <source>#<unit>, e.g. L3#12).' % (where, jstr(js_str(ref))))
            elif not have_sources[0]:
                ref_ok = 'nosources'
            elif r['sid'] not in sources:
                E('E-REF', p, '%s: ref %s points to an unknown source %s.' % (where, js_str(ref), r['sid']))
            else:
                src = sources[r['sid']]
                if src['byN'] is not None:
                    unit = src['byN'].get(r['n'])
                    if unit is None:
                        E('E-REF', p, '%s: ref %s is out of range (%s has units 1..%d).' % (where, ref, r['sid'], len(src['units'])))
                    else:
                        ref_ok = True
                elif is_int(src['meta'].get('unitCount')) and r['n'] > src['meta']['unitCount']:
                    E('E-REF', p, '%s: ref %s is out of range (%s has %s units).' % (where, ref, r['sid'], js_str(src['meta']['unitCount'])))
                else:
                    ref_ok = 'nounits'
        if quote is None or quote == '':
            if require_quote and js_truthy(ref):
                E(missing_code or 'E-SCHEMA', p, '%s: a verbatim "quote" from %s is required.' % (where, js_str(ref)))
            return
        if not is_str(quote):
            E('E-SCHEMA', p, where + ': quote must be text.')
            return
        ql = clen(quote)
        if ql < 8 or ql > 240:
            E('E-SCHEMA', p, '%s: quote must be 8-240 characters (it has %d).' % (where, ql))
            return
        if not opts.get('checkQuotes') or not ref_ok:
            return
        R['stats']['quotes']['checked'] += 1
        if ref_ok is not True:
            R['stats']['quotes']['unverifiable'] += 1
            k = src['meta'].get('id') if src else '(no sources)'
            k = k if is_str(k) else js_str(k)
            unver[k] = unver.get(k, 0) + 1
            return
        nq = norm_quote(quote)
        if nq and nq in hay(unit):
            R['stats']['quotes']['verified'] += 1
            if unit.get('textState') == 'transcribed':
                k = js_str(src['meta'].get('id'))
                transcribed[k] = transcribed.get(k, 0) + 1
            return
        R['stats']['quotes']['failed'] += 1
        state = (' (that unit is %s: it has no text to quote)' % unit.get('textState')
                 if unit.get('textState') in ('image-only', 'empty') else '')
        E('E-QUOTE', p, '%s: quote not found verbatim in %s%s: "%s". Copy the words exactly from the unit, or drop the claim.'
          % (where, ref, state, quote[:90]))

    def check_fact(f, p, where):
        if not is_obj(f):
            E('E-SCHEMA', p, where + ': a fact must be {text, ref, quote}.')
            return
        if not non_empty(f.get('text')) or clen(f['text']) < 4 or clen(f['text']) > 300:
            E('E-SCHEMA', p, where + ': text must be 4-300 characters.')
        if f.get('ref') is None or f.get('ref') == '':
            E('E-SCHEMA', p, where + ': a fact needs a ref and a verbatim quote (or move the claim into an authored section).')
            return
        check_ref_quote(f.get('ref'), f.get('quote'), p, where, require_quote=True)

    def check_refs(refs, p, where):
        if refs is None:
            return
        if not isinstance(refs, list):
            E('E-SCHEMA', p, where + ': refs must be a list.')
            return
        for r in refs:
            check_ref_quote(r, None, p, where)

    # ---- meta ----
    meta_p = 'galaxy/meta.json'
    if not is_part and ok(meta):
        num_scan(meta, meta_p)
        if not is_obj(meta):
            E('E-SCHEMA', meta_p, 'galaxy/meta.json must be a JSON object.')
        else:
            if not is_str(meta.get('galaxyId')) or not RE_GALAXY_ID.fullmatch(meta['galaxyId']):
                E('E-ID', meta_p, 'galaxyId %s must look like gx_my_subject (gx_ then 3-80 of a-z, 0-9, _ and -).'
                  % jstr(meta.get('galaxyId', UNDEF)))
            if meta.get('profile') not in ('galaxy', 'pathway'):
                E('E-SCHEMA', meta_p, 'profile must be "galaxy" or "pathway".')
            if not is_int(meta.get('revision')) or meta['revision'] < 1:
                E('E-SCHEMA', meta_p, 'revision must be an integer of at least 1.')
            if not non_empty(meta.get('title')):
                E('E-SCHEMA', meta_p, 'title is missing.')
            for k in ('subject', 'semester', 'language', 'createdAt', 'description'):
                if meta.get(k) is not None and not is_str(meta.get(k)):
                    E('E-SCHEMA', meta_p, k + ' must be text.')
            ef = meta.get('examFacts')
            if ef is not None and not (isinstance(ef, list) and all(is_str(x) for x in ef)):
                E('E-SCHEMA', meta_p, 'examFacts must be a list of sentences.')
            if meta.get('generator') is not None and not is_obj(meta.get('generator')):
                E('E-SCHEMA', meta_p, 'generator must be an object.')
            if meta.get('contentHash') is not None:
                W('W-SCHEMA', meta_p, 'contentHash in galaxy/meta.json is ignored (the manifest owns hashes).')
            if is_obj(mf) and is_str(mf.get('galaxyId')) and is_str(meta.get('galaxyId')) and mf['galaxyId'] != meta['galaxyId']:
                E('E-MANIFEST', mp, 'manifest.json says galaxyId "%s" but galaxy/meta.json says "%s".' % (mf['galaxyId'], meta['galaxyId']))
            if is_obj(mf) and is_int(mf.get('revision')) and is_int(meta.get('revision')) and mf['revision'] != meta['revision']:
                W('W-MANIFEST', mp, 'manifest.json revision %s differs from galaxy/meta.json revision %s.'
                  % (js_str(mf['revision']), js_str(meta['revision'])))

    # ---- nodes ----
    nodes_p = 'galaxy/nodes.json'
    nodes_list = []
    if not is_part:
        nd = getJ(nodes_p)
        if ok(nd):
            num_scan(nd, nodes_p)
            if not is_obj(nd) or not isinstance(nd.get('nodes'), list):
                E('E-SCHEMA', nodes_p, 'galaxy/nodes.json must be {"nodes": [...]}.')
            else:
                for i, n in enumerate(nd['nodes']):
                    w = 'node ' + (n['id'] if is_obj(n) and is_str(n.get('id')) else '#%d' % (i + 1))
                    if not is_obj(n):
                        E('E-SCHEMA', nodes_p, w + ' must be an object.')
                        continue
                    if not is_str(n.get('id')) or not RE_NODE_ID.fullmatch(n['id']):
                        E('E-ID', nodes_p, w + ': the id must use a-z, 0-9 and "-", start with a letter or digit, at most 80 characters.')
                        continue
                    if _reserved(n['id']):
                        E('E-ID', nodes_p, w + ': "__root" and ids starting with hub- or stress- are reserved.')
                        continue
                    if n['id'] in node_by_id:
                        E('E-ID', nodes_p, 'Duplicate node id ' + n['id'] + '.')
                        continue
                    node_by_id[n['id']] = n
                    nodes_list.append(n)
    node_ids = set(node_by_id)
    know_nodes = not is_part or bool(base)

    def has_node(x):
        return isinstance(x, str) and x in node_ids
    for n in nodes_list:
        w = 'node ' + n['id']
        if not non_empty(n.get('label')) or clen(n['label']) > 200:
            E('E-SCHEMA', nodes_p, w + ': label must be 1-200 characters.')
        if not (n.get('kind') is None and is_pathway) and n.get('kind') not in KINDS:
            E('E-SCHEMA', nodes_p, w + ': kind must be concept, skill, event or scenario.')
        if not (n.get('category') is None and is_pathway) and n.get('category') not in CATEGORIES:
            E('E-SCHEMA', nodes_p, w + ': category must be technical, historical or situational.')
        if n.get('priority') not in PRIORITIES:
            E('E-SCHEMA', nodes_p, w + ': priority must be core, standard or detail.')
        em = n.get('estMin')
        if not is_int(em) or em < 1 or em > 90:
            E('E-SCHEMA', nodes_p, w + ': estMin must be a whole number of minutes from 1 to 90.')
        card = n.get('card')
        if card is None or (is_obj(card) and (card.get('definition') is None or card.get('definition') == '')):
            W('W-FILL', nodes_p, w + ' has no card definition: fill level L0.')
        elif not is_obj(card):
            E('E-SCHEMA', nodes_p, w + ': card must be {definition, keyFacts}.')
        else:
            dfn = card.get('definition')
            if not is_str(dfn) or clen(dfn) < 10 or clen(dfn) > 1200:
                E('E-SCHEMA', nodes_p, w + ': card.definition must be 10-1,200 characters.')
            kf = card.get('keyFacts')
            if kf is not None and not isinstance(kf, list):
                E('E-SCHEMA', nodes_p, w + ': card.keyFacts must be a list of facts.')
            else:
                for k, f in enumerate(arr(kf)):
                    check_fact(f, nodes_p, '%s key fact %d' % (w, k + 1))
        check_refs(n.get('refs'), nodes_p, w)
        if profile == 'galaxy' and not arr(n.get('refs')):
            W('W-SCHEMA', nodes_p, w + ': refs should list every unit the node covers.')
        an = n.get('anchors')
        if an is not None and not isinstance(an, list):
            E('E-SCHEMA', nodes_p, w + ': anchors must be a list of {ref, quote}.')
        else:
            for k, a in enumerate(arr(an)):
                if not is_obj(a):
                    E('E-SCHEMA', nodes_p, '%s anchor %d must be {ref, quote}.' % (w, k + 1))
                else:
                    check_ref_quote(a.get('ref'), a.get('quote'), nodes_p, '%s anchor %d' % (w, k + 1),
                                    require_ref=True, require_quote=True)
        if n.get('origin') is not None and n.get('origin') not in ORIGINS:
            E('E-SCHEMA', nodes_p, w + ': origin must be lesson, tp, hybrid or extension.')
        hs = n.get('homeSkill')
        if hs is not None and not has_node(hs):
            E('E-ID', nodes_p, '%s: homeSkill %s is not a node.' % (w, jstr(hs)))
        cv = n.get('covers')
        if cv is not None and not (isinstance(cv, list) and all(is_str(x) for x in cv)):
            E('E-SCHEMA', nodes_p, w + ': covers must be a list of ids.')

    # ---- edges, bubbles, requires DAG ----
    edges_p = 'galaxy/edges.json'
    edges = []
    if is_part:
        edges = [e for e in arr(base.get('edges')) if is_obj(e)] if base else []
    else:
        ed = getJ(edges_p)
        if ok(ed):
            num_scan(ed, edges_p)
            if not is_obj(ed) or not isinstance(ed.get('edges'), list):
                E('E-SCHEMA', edges_p, 'galaxy/edges.json must be {"edges": [...], "bubbles": [...]}.')
            else:
                seen = set()
                for i, e in enumerate(ed['edges']):
                    w = 'edge #%d' % (i + 1) + (' (%s -> %s)' % (_cat(e.get('source')), _cat(e.get('target'))) if is_obj(e) else '')
                    if not is_obj(e):
                        E('E-SCHEMA', edges_p, w + ' must be an object.')
                        continue
                    if e.get('type') not in EDGE_TYPES:
                        E('E-SCHEMA', edges_p, w + ': type must be requires, follows or relates.')
                    if not has_node(e.get('source')) or not has_node(e.get('target')):
                        E('E-GRAPH', edges_p, '%s: dangling edge, %s is not a node.'
                          % (w, jstr(e.get('source', UNDEF)) if not has_node(e.get('source')) else jstr(e.get('target', UNDEF))))
                        continue
                    if e['source'] == e['target']:
                        E('E-GRAPH', edges_p, w + ': self-loop.')
                        continue
                    if e.get('why') is not None and not is_str(e.get('why')):
                        E('E-SCHEMA', edges_p, w + ': why must be text.')
                    k = '%s|%s|%s' % (e['source'], e['target'], _cat(e.get('type')))
                    if k in seen:
                        W('W-GRAPH', edges_p, '%s: duplicate %s edge.' % (w, _cat(e.get('type'))))
                    seen.add(k)
                    edges.append(e)
                bub = ed.get('bubbles')
                if bub is not None and not isinstance(bub, list):
                    E('E-SCHEMA', edges_p, 'bubbles must be a list.')
                b_ids = set()
                for i, b in enumerate(arr(bub)):
                    w = 'bubble ' + (b['id'] if is_obj(b) and is_str(b.get('id')) else '#%d' % (i + 1))
                    if not is_obj(b):
                        E('E-SCHEMA', edges_p, w + ' must be an object.')
                        continue
                    if not non_empty(b.get('id')):
                        E('E-SCHEMA', edges_p, w + ': id is missing.')
                    elif b['id'] in b_ids:
                        E('E-ID', edges_p, 'Duplicate bubble id ' + b['id'] + '.')
                    else:
                        b_ids.add(b['id'])
                    sk = node_by_id.get(b['skillId']) if is_str(b.get('skillId')) else None
                    if not sk:
                        E('E-ID', edges_p, '%s: skillId %s is not a node.' % (w, jstr(b.get('skillId', UNDEF))))
                    elif sk.get('kind') != 'skill':
                        E('E-SCHEMA', edges_p, '%s: skillId %s must be a node of kind skill.' % (w, b['skillId']))
                    for k in ('memberIds', 'tethers'):
                        if b.get(k) is None:
                            continue
                        if not isinstance(b[k], list):
                            E('E-SCHEMA', edges_p, '%s: %s must be a list of node ids.' % (w, k))
                            continue
                        for x in b[k]:
                            if not has_node(x):
                                E('E-ID', edges_p, '%s: %s contains %s, which is not a node.' % (w, k, jstr(x)))
                adj = {}
                for e in edges:
                    if e.get('type') == 'requires':
                        adj.setdefault(e['source'], []).append(e['target'])
                for c in _find_cycles(list(node_by_id), adj, 20):
                    E('E-GRAPH', edges_p, '"requires" edges form a cycle: %s. Remove one of them.' % ' -> '.join(c))
    pre_t = _prereq_targets(edges)

    # ---- pathways ----
    pw_p = 'galaxy/pathways.json'
    pathways = []
    if is_part:
        pathways = [x for x in arr(base.get('pathways')) if is_obj(x)] if base else []
    else:
        pd = getJ(pw_p)
        if ok(pd):
            num_scan(pd, pw_p)
            if not is_obj(pd) or not isinstance(pd.get('pathways'), list):
                E('E-SCHEMA', pw_p, 'galaxy/pathways.json must be {"pathways": [...], "deviations": [...]}.')
            else:
                pids = set()
                for i, pw in enumerate(pd['pathways']):
                    w = 'pathway ' + (pw['id'] if is_obj(pw) and is_str(pw.get('id')) else '#%d' % (i + 1))
                    if not is_obj(pw):
                        E('E-SCHEMA', pw_p, w + ' must be an object.')
                        continue
                    if not is_str(pw.get('id')) or not RE_NODE_ID.fullmatch(pw['id']):
                        E('E-ID', pw_p, w + ': the id must use a-z, 0-9 and "-".')
                    elif pw['id'] in pids:
                        E('E-ID', pw_p, 'Duplicate pathway id ' + pw['id'] + '.')
                    else:
                        pids.add(pw['id'])
                    if not non_empty(pw.get('name')):
                        E('E-SCHEMA', pw_p, w + ': name is missing.')
                    if pw.get('kind') not in PATHWAY_KINDS:
                        E('E-SCHEMA', pw_p, w + ': kind must be main, branch, exam, topic or custom.')
                    if pw.get('why') is not None and not is_str(pw.get('why')):
                        E('E-SCHEMA', pw_p, w + ': why must be text.')
                    if pw.get('focus') is not None and not isinstance(pw.get('focus'), bool):
                        E('E-SCHEMA', pw_p, w + ': focus must be true or false.')
                    if pw.get('scope') is not None and not is_obj(pw.get('scope')):
                        E('E-SCHEMA', pw_p, w + ': scope must be an object.')
                    stages = pw.get('stages')
                    if not isinstance(stages, list) or len(stages) < 1 or len(stages) > 40:
                        E('E-SCHEMA', pw_p, w + ': stages must be a list of 1-40 stages.')
                        continue
                    in_pw = set()
                    for k, st in enumerate(stages):
                        ws = '%s stage %d' % (w, k + 1)
                        if not is_obj(st):
                            E('E-SCHEMA', pw_p, ws + ' must be an object.')
                            continue
                        if not non_empty(st.get('title')):
                            E('E-SCHEMA', pw_p, ws + ': title is missing.')
                        if not non_empty(st.get('why')):
                            E('E-SCHEMA', pw_p, ws + ': why is missing.')
                        if not isinstance(st.get('nodeIds'), list) or not st['nodeIds']:
                            E('E-SCHEMA', pw_p, ws + ': nodeIds must list at least one node.')
                            continue
                        for x in st['nodeIds']:
                            if not has_node(x):
                                E('E-PATHWAY', pw_p, '%s: unknown node %s.' % (ws, jstr(x)))
                            elif x in in_pw:
                                E('E-PATHWAY', pw_p, '%s: node %s appears more than once.' % (w, x))
                            if _hashable(x):
                                in_pw.add(x)
                    if pw.get('optional') is not None:
                        if not isinstance(pw['optional'], list):
                            E('E-SCHEMA', pw_p, w + ': optional must be a list of node ids.')
                        else:
                            for x in pw['optional']:
                                if not has_node(x):
                                    E('E-PATHWAY', pw_p, '%s: optional lists unknown node %s.' % (w, jstr(x)))
                    pathways.append(pw)
                mains = [x for x in pathways if x.get('kind') == 'main']
                if not mains:
                    E('E-PATHWAY', pw_p, 'There is no main pathway: add one with "id": "main" and "kind": "main".')
                elif len(mains) > 1:
                    E('E-PATHWAY', pw_p, 'Only one pathway may have kind "main" (found %d).' % len(mains))
                elif mains[0].get('id') != 'main':
                    E('E-PATHWAY', pw_p, 'The main pathway must have the id "main".')
                main = mains[0] if mains else None
                if main and isinstance(main.get('stages'), list):
                    order, pos = _flat_ids(main), {}
                    for i, x in enumerate(order):
                        if isinstance(x, str) and x not in pos:
                            pos[x] = i
                    missing = [n['id'] for n in nodes_list if n['id'] not in pos]
                    for x in missing[:40]:
                        E('E-PATHWAY', pw_p, 'The main pathway misses node %s: every node must appear in it exactly once.' % x)
                    if len(missing) > 40:
                        E('E-PATHWAY', pw_p, 'The main pathway misses %d more nodes.' % (len(missing) - 40))
                    ns = len(main['stages'])
                    r = (3, 10) if is_pathway else (6, 10)
                    if ns < r[0] or ns > r[1]:
                        W('W-PATHWAY', pw_p, 'The main pathway has %d stages; %d-%d are recommended.' % (ns, r[0], r[1]))
                    devs = [d for d in arr(pd.get('deviations')) if is_obj(d)]

                    def dev_ok(a, b):
                        return any((d.get('nodeId') == a and d.get('movedBefore') == b) or
                                   (d.get('nodeId') == b and d.get('movedBefore') == a) for d in devs)
                    warned = 0
                    for e in edges:
                        if e.get('type') != 'requires' or e['source'] not in pos or e['target'] not in pos:
                            continue
                        if pos[e['target']] < pos[e['source']] and not dev_ok(e['source'], e['target']):
                            if warned < 30:
                                W('W-PATHWAY', pw_p, 'In the main pathway %s comes before %s, which it requires (move it, or '
                                                     'list the move in deviations).' % (e['target'], e['source']))
                            warned += 1
                if pd.get('deviations') is not None and not isinstance(pd.get('deviations'), list):
                    E('E-SCHEMA', pw_p, 'deviations must be a list.')
                for i, d in enumerate(arr(pd.get('deviations'))):
                    w = 'deviation #%d' % (i + 1)
                    if not is_obj(d):
                        E('E-SCHEMA', pw_p, w + ' must be an object.')
                        continue
                    if not has_node(d.get('nodeId')):
                        E('E-ID', pw_p, '%s: nodeId %s is not a node.' % (w, jstr(d.get('nodeId', UNDEF))))
                    if d.get('movedBefore') is not None and not has_node(d.get('movedBefore')):
                        E('E-ID', pw_p, '%s: movedBefore %s is not a node.' % (w, jstr(d.get('movedBefore', UNDEF))))
                    if not non_empty(d.get('why')):
                        W('W-SCHEMA', pw_p, w + ': why should say why the node was moved.')

    # ---- lessons ----
    lesson_files = {}

    def check_prim(prim, sp, p, w):
        def bad(msg):
            E('E-PRIM', p, '%s (%s): %s' % (w, prim, msg))
        if not is_obj(sp):
            bad('spec must be an object.')
            return

        def strs(x, keys):
            return all(is_str(x.get(k)) for k in keys)

        def count(a, lo, hi):
            return isinstance(a, list) and lo <= len(a) <= hi
        if prim == 'text':
            if not non_empty(sp.get('body')) or clen(sp['body']) > 1500:
                bad('spec.body must be markdown-lite text of at most 1,500 characters.')
        elif prim == 'stepper':
            if not count(sp.get('steps'), 2, 10):
                bad('spec.steps must hold 2-10 steps.')
            elif not all(is_obj(s) and strs(s, ('title', 'body')) for s in sp['steps']):
                bad('every step needs a title and a body.')
        elif prim == 'compare':
            cols = sp.get('columns')
            if not count(cols, 2, 6) or not all(is_str(c) for c in cols):
                bad('spec.columns must name 2-6 columns.')
                return
            if not count(sp.get('rows'), 2, 12):
                bad('spec.rows must hold 2-12 rows.')
                return
            for i, r in enumerate(sp['rows']):
                if not isinstance(r, list):
                    bad('row %d must be a list: a label, then one cell per column.' % (i + 1))
                elif len(r) != len(cols) + 1:
                    bad('row %d has %d cells; each row is a label followed by exactly one cell per column (%d in all).'
                        % (i + 1, len(r), len(cols) + 1))
                elif not all(is_str(c) or is_num(c) for c in r):
                    bad('row %d: cells must be text.' % (i + 1))
            if sp.get('note') is not None and not is_str(sp.get('note')):
                bad('note must be text.')
        elif prim == 'flow':
            nodes = sp.get('nodes')
            if not count(nodes, 2, 8) or not all(is_obj(b) and non_empty(b.get('id')) and is_str(b.get('label')) for b in nodes):
                bad('spec.nodes must hold 2-8 boxes {id, label, sub?}.')
                return
            ids = set(b['id'] for b in nodes)
            if len(ids) != len(nodes):
                bad('box ids must be unique.')
            if not count(sp.get('steps'), 2, 10):
                bad('spec.steps must hold 2-10 steps.')
                return
            for i, s in enumerate(sp['steps']):
                if not is_obj(s) or not strs(s, ('title', 'body')):
                    bad('step %d needs a title and a body.' % (i + 1))
                    continue
                act = s.get('active')
                if act is not None and not (isinstance(act, list) and all(isinstance(x, str) and x in ids for x in act)):
                    bad('step %d: active must list existing box ids.' % (i + 1))
                ar = s.get('arrows')
                if ar is not None and not (isinstance(ar, list) and all(
                        isinstance(a, list) and len(a) == 2 and all(isinstance(x, str) and x in ids for x in a) for a in ar)):
                    bad('step %d: arrows must be [from, to] pairs of existing box ids.' % (i + 1))
        elif prim == 'timeline':
            if not count(sp.get('events'), 3, 12):
                bad('spec.events must hold 3-12 events.')
            elif not all(is_obj(e) and strs(e, ('when', 'title', 'body')) for e in sp['events']):
                bad('every event needs when, title and body.')
        elif prim == 'quorum':
            r = sp.get('replicas')
            if not is_int(r) or r < 3 or r > 9:
                bad('spec.replicas must be a whole number from 3 to 9.')
            if sp.get('intro') is not None and not is_str(sp.get('intro')):
                bad('intro must be text.')
        elif prim == 'kvrepl':
            if sp.get('intro') is not None and not is_str(sp.get('intro')):
                bad('intro must be text.')
            if not count(sp.get('script'), 3, 20):
                bad('spec.script must hold 3-20 commands.')
            elif not all(is_obj(s) and non_empty(s.get('cmd')) and is_str(s.get('out')) and
                         (s.get('explain') is None or is_str(s.get('explain'))) for s in sp['script']):
                bad('every script line needs cmd and out (and explain as text).')
            if sp.get('hint') is not None and not is_str(sp.get('hint')):
                bad('hint must be text.')
        elif prim == 'chooser':
            if sp.get('intro') is not None and not is_str(sp.get('intro')):
                bad('intro must be text.')
            ch = sp.get('choices')
            if not count(ch, 2, 5) or not all(is_str(c) for c in ch):
                bad('spec.choices must hold 2-5 choices (it has %d).' % len(arr(ch)))
                return
            if not count(sp.get('cases'), 2, 8):
                bad('spec.cases must hold 2-8 cases.')
                return
            for i, c in enumerate(sp['cases']):
                if not is_obj(c) or not is_str(c.get('scenario')) or not is_str(c.get('why')):
                    bad('case %d needs a scenario and a why.' % (i + 1))
                elif not is_int(c.get('answer')) or c['answer'] < 0 or c['answer'] >= len(ch):
                    bad('case %d: answer must be a choice index (0-%d).' % (i + 1, len(ch) - 1))

    def check_question(q, p, w, paper):
        def bad(msg):
            E('E-QUESTION', p, '%s: %s' % (w, msg))
        if not is_obj(q):
            bad('must be an object.')
            return
        if not non_empty(q.get('id')):
            bad('id is missing.')
        t = q.get('type')
        if t not in QTYPES:
            bad('type must be mcq, multi, fill or short.')
            return
        if not non_empty(q.get('prompt')):
            bad('prompt is missing.')
        opts_ = q.get('options')

        def opts2(lo, hi):
            return isinstance(opts_, list) and lo <= len(opts_) <= hi and all(is_str(o) for o in opts_)
        if t == 'mcq':
            if not opts2(2, 6):
                bad('an mcq needs 2-6 options.')
            elif not is_int(q.get('answer')) or q['answer'] < 0 or q['answer'] >= len(opts_):
                bad('answer must be the index of the right option (0-%d).' % (len(opts_) - 1))
        elif t == 'multi':
            ans = q.get('answers')
            if not opts2(3, 8):
                bad('a multi question needs 3-8 options.')
            elif not isinstance(ans, list) or not ans or not all(is_int(a) and 0 <= a < len(opts_) for a in ans) \
                    or len(set(float(a) for a in ans)) != len(ans):
                bad('answers must list the indices of the right options (at least one, no repeats).')
        elif t == 'fill':
            if is_str(q.get('prompt')) and len(re.findall(r'_{4,}', q['prompt'])) != 1:
                bad('a fill prompt must contain the blank ____ exactly once.')
            acc = q.get('accepted')
            if not isinstance(acc, list) or len(acc) < 1 or len(acc) > 8 or not all(non_empty(a) for a in acc):
                bad('accepted must list 1-8 accepted answers.')
        elif t == 'short':
            if not non_empty(q.get('modelAnswer')):
                bad('modelAnswer is missing.')
            rb = q.get('rubric')
            if isinstance(rb, list):
                pts = rb
            elif is_str(rb):
                pts = [x for x in (jtrim(s) for s in re.split(r'\r?\n|;', rb)) if x]
            else:
                pts = None
            if not pts or len(pts) < 2 or len(pts) > 6 or not all(non_empty(x) for x in pts):
                bad('rubric must give 2-6 marking points (a list, or one text split by new lines or ";").')
        if not non_empty(q.get('explanation')):
            bad('explanation is missing.')
        ref, quote = q.get('ref'), q.get('quote')
        if ref is None or ref == '':
            bad('a ref (e.g. L3#12) is required.')
        elif quote is None or quote == '':
            check_ref_quote(ref, None, p, w)
            bad('a verbatim quote from %s is required.' % js_str(ref))
        else:
            check_ref_quote(ref, quote, p, w)
        if q.get('trap') is not None and not is_str(q.get('trap')):
            bad('trap must be text.')
        if paper:
            if not non_empty(q.get('form')):
                bad('form is missing.')
            pt = q.get('points')
            if not is_num(pt) or pt <= 0 or not float(pt * 2).is_integer():
                bad('points must be a positive multiple of 0.5.')
            if not isinstance(q.get('nodeIds'), list):
                bad('nodeIds must list the nodes this question tests.')
            else:
                for x in q['nodeIds']:
                    if know_nodes and not has_node(x):
                        E('E-ID', p, '%s: nodeIds names %s, which is not a node.' % (w, jstr(x)))

    def check_lesson(l, p, file_id):
        if not is_obj(l):
            E('E-SCHEMA', p, p + ' must be a JSON object.')
            return
        if l.get('nodeId') != file_id:
            E('E-ID', p, 'nodeId %s must match the file name (lessons/%s.json).' % (jstr(l.get('nodeId', UNDEF)), file_id))
        if is_str(l.get('nodeId')) and know_nodes and l['nodeId'] not in node_ids:
            if is_part:
                E('E-BASE', p, 'Node %s is not in the base galaxy: a part may only fill existing nodes.' % l['nodeId'])
            else:
                E('E-ID', p, 'Lesson for unknown node %s.' % l['nodeId'])
        g = l.get('guide')
        if not is_obj(g):
            E('E-SCHEMA', p, 'guide is missing.')
        else:
            ix = g.get('index')
            if ix is not None and not (isinstance(ix, list) and all(is_str(x) for x in ix)):
                E('E-SCHEMA', p, 'guide.index must be a list of section titles.')
            if not isinstance(g.get('sections'), list):
                E('E-SCHEMA', p, 'guide.sections must be a list.')
            s_ids = set()
            for k, s in enumerate(arr(g.get('sections'))):
                w = 'guide section ' + (s['id'] if is_obj(s) and is_str(s.get('id')) else '#%d' % (k + 1))
                if not is_obj(s):
                    E('E-SCHEMA', p, w + ' must be an object.')
                    continue
                if not non_empty(s.get('id')):
                    E('E-SCHEMA', p, w + ': id is missing.')
                elif s['id'] in s_ids:
                    W('W-SCHEMA', p, w + ': duplicate section id.')
                else:
                    s_ids.add(s['id'])
                if not non_empty(s.get('title')):
                    E('E-SCHEMA', p, w + ': title is missing.')
                if s.get('kind') not in SECTION_KINDS:
                    E('E-SCHEMA', p, w + ': kind must be one of ' + ', '.join(SECTION_KINDS) + '.')
                if not is_str(s.get('body')):
                    E('E-SCHEMA', p, w + ': body must be markdown-lite text.')
                elif _HTML_TAG.search(outside_code(s['body'])) or _MD_LINK.search(s['body']):
                    W('W-SCHEMA', p, w + ': body contains HTML outside backticks, or a link; it is shown as plain text (markdown-lite only).')
                fs = s.get('facts')
                if fs is not None and not isinstance(fs, list):
                    E('E-SCHEMA', p, w + ': facts must be a list.')
                else:
                    for j, f in enumerate(arr(fs)):
                        check_fact(f, p, '%s fact %d' % (w, j + 1))
                check_refs(s.get('refs'), p, w)
                if s.get('provenance') is not None and s.get('provenance') != 'authored':
                    W('W-SCHEMA', p, w + ': provenance should be "authored" (or absent).')
            for k in ('needs', 'related'):
                if g.get(k) is None:
                    continue
                if not isinstance(g[k], list):
                    E('E-SCHEMA', p, 'guide.%s must be a list of {nodeId, why}.' % k)
                    continue
                for x in g[k]:
                    if not is_obj(x) or not is_str(x.get('nodeId')):
                        E('E-SCHEMA', p, 'guide.%s entries must be {nodeId, why}.' % k)
                    elif know_nodes and x['nodeId'] not in node_ids:
                        E('E-ID', p, 'guide.%s names %s, which is not a node.' % (k, x['nodeId']))
        if not isinstance(l.get('slides'), list):
            E('E-SCHEMA', p, 'slides must be a list.')
        sl_ids = set()
        for k, s in enumerate(arr(l.get('slides'))):
            w = 'slide ' + (s['id'] if is_obj(s) and is_str(s.get('id')) else '#%d' % (k + 1))
            if not is_obj(s):
                E('E-SCHEMA', p, w + ' must be an object.')
                continue
            if not non_empty(s.get('id')):
                E('E-SCHEMA', p, w + ': id is missing.')
            elif s['id'] in sl_ids:
                E('E-ID', p, 'Duplicate slide id ' + s['id'] + '.')
            else:
                sl_ids.add(s['id'])
            if not non_empty(s.get('title')):
                E('E-SCHEMA', p, w + ': title is missing.')
            if s.get('primitive') not in PRIMITIVES:
                E('E-PRIM', p, '%s: unknown primitive %s (use %s).' % (w, jstr(s.get('primitive', UNDEF)), ', '.join(PRIMITIVES)))
            else:
                check_prim(s['primitive'], s.get('spec'), p, w)
            check_ref_quote(s.get('ref'), None, p, w, require_ref=True)
            if s.get('provenance') is not None and s.get('provenance') != 'authored':
                W('W-SCHEMA', p, w + ': provenance should be "authored" (or absent).')
        if not isinstance(l.get('checkpoint'), list):
            E('E-SCHEMA', p, 'checkpoint must be a list of questions.')
        q_ids = set()
        for k, q in enumerate(arr(l.get('checkpoint'))):
            if is_obj(q) and non_empty(q.get('id')):
                if q['id'] in q_ids:
                    E('E-ID', p, 'Duplicate question id ' + q['id'] + '.')
                q_ids.add(q['id'])
            check_question(q, p, 'checkpoint ' + (q['id'] if is_obj(q) and is_str(q.get('id')) else '#%d' % (k + 1)), False)
        a = l.get('audit')
        if a is not None:
            if not is_obj(a):
                E('E-SCHEMA', p, 'audit must be {by, refuted, fixed, at} or carry a note.')
            else:
                for k in ('refuted', 'fixed'):
                    if a.get(k) is not None and (not is_int(a[k]) or a[k] < 0):
                        E('E-SCHEMA', p, 'audit.%s must be a whole number.' % k)

    for p in sorted(VF):
        m = re.fullmatch(r'lessons/([^/]+)\.json', p)
        if not m:
            continue
        l = getJ(p)
        if not ok(l):
            continue
        num_scan(l, p)
        check_lesson(l, p, m.group(1))
        if is_obj(l) and is_str(l.get('nodeId')):
            lesson_files[l['nodeId']] = l

    # pathway profile: every step has a lesson
    if is_pathway:
        for n in nodes_list:
            if 'lessons/%s.json' % n['id'] not in VF:
                E('E-MISSING', 'lessons/%s.json' % n['id'], 'Step %s has no lesson: every step of an A-to-Z course must be '
                                                           'fully generated.' % n['id'])

    # ---- main guide ----
    g_p = 'guide/main.json'
    gd = getJ(g_p)
    if ok(gd):
        num_scan(gd, g_p)
        if not is_obj(gd) or not isinstance(gd.get('sections'), list):
            E('E-SCHEMA', g_p, 'guide/main.json must be {"sections": [...]}.')
        else:
            kinds = []
            for i, s in enumerate(gd['sections']):
                w = 'guide section ' + (s['id'] if is_obj(s) and is_str(s.get('id')) else '#%d' % (i + 1))
                if not is_obj(s):
                    E('E-SCHEMA', g_p, w + ' must be an object.')
                    continue
                if not non_empty(s.get('id')):
                    E('E-SCHEMA', g_p, w + ': id is missing.')
                if s.get('kind') not in GUIDE_KINDS:
                    E('E-SCHEMA', g_p, w + ': kind must be one of ' + ', '.join(GUIDE_KINDS) + '.')
                else:
                    kinds.append(s['kind'])
                if not non_empty(s.get('title')):
                    E('E-SCHEMA', g_p, w + ': title is missing.')
                if s.get('intro') is not None and not is_str(s.get('intro')):
                    E('E-SCHEMA', g_p, w + ': intro must be text.')
                if not isinstance(s.get('items'), list):
                    E('E-SCHEMA', g_p, w + ': items must be a list.')
                    continue
                for k, it in enumerate(s['items']):
                    wi = '%s item %d' % (w, k + 1)
                    if not is_obj(it) or not non_empty(it.get('text')):
                        E('E-SCHEMA', g_p, wi + ': text is missing.')
                        continue
                    if it.get('ref') is not None and it.get('ref') != '':
                        check_ref_quote(it['ref'], it.get('quote'), g_p, wi, require_quote=True)
            missing_k = [k for k in GUIDE_KINDS if k not in kinds]
            in_order = all(i == 0 or GUIDE_KINDS.index(k) >= GUIDE_KINDS.index(kinds[i - 1]) for i, k in enumerate(kinds))
            if missing_k or not in_order:
                W('W-SCHEMA', g_p, 'A complete guide has all seven sections in this order: %s%s.' % (
                    ', '.join(GUIDE_KINDS), (' (missing: ' + ', '.join(missing_k) + ')') if missing_k else ' (they are out of order)'))

    # ---- practice paper / final quiz ----
    x_p = 'exam/mock.json'
    xd = getJ(x_p)
    if ok(xd):
        num_scan(xd, x_p)
        if not is_obj(xd):
            E('E-SCHEMA', x_p, 'exam/mock.json must be {profile, blueprint, mock}.')
        else:
            bp = xd.get('blueprint')
            qs = xd['mock']['questions'] if is_obj(xd.get('mock')) and isinstance(xd['mock'].get('questions'), list) else None
            if xd.get('profile') is not None and not is_obj(xd.get('profile')):
                E('E-SCHEMA', x_p, 'profile must be an object.')
            if qs is None:
                E('E-SCHEMA', x_p, 'mock.questions must be a list.')
            q_ids = set()
            for i, q in enumerate(arr(qs)):
                if is_obj(q) and non_empty(q.get('id')):
                    if q['id'] in q_ids:
                        E('E-ID', x_p, 'Duplicate question id ' + q['id'] + '.')
                    q_ids.add(q['id'])
                check_question(q, x_p, 'question ' + (q['id'] if is_obj(q) and is_str(q.get('id')) else '#%d' % (i + 1)), True)
            if not is_obj(bp) or not isinstance(bp.get('sections'), list):
                E('E-SCHEMA', x_p, 'blueprint must be {durationMin, totalPoints, sections: [...]}.')
            else:
                if bp.get('durationMin') is not None and (not is_num(bp['durationMin']) or bp['durationMin'] <= 0):
                    E('E-SCHEMA', x_p, 'blueprint.durationMin must be a number of minutes or null.')
                if not is_num(bp.get('totalPoints')):
                    E('E-SCHEMA', x_p, 'blueprint.totalPoints must be a number.')
                sp_, sc_, sane = 0.0, 0, True
                for i, s in enumerate(bp['sections']):
                    w = 'blueprint section ' + (s['id'] if is_obj(s) and is_str(s.get('id')) else '#%d' % (i + 1))
                    if not is_obj(s) or not non_empty(s.get('title')) or not is_int(s.get('count')) or s['count'] < 0 \
                            or not is_num(s.get('points')):
                        E('E-SCHEMA', x_p, w + ' needs id, title, form, count and points.')
                        sane = False
                        continue
                    sp_ += float(s['points'])
                    sc_ += int(s['count'])
                    if qs is not None and is_str(s.get('form')):
                        mine = [q for q in qs if is_obj(q) and q.get('form') == s['form']]
                        same = len([x for x in bp['sections'] if is_obj(x) and x.get('form') == s['form']])
                        if same == 1 and len(mine) != s['count']:
                            W('W-SCHEMA', x_p, '%s (%s) expects %s questions; the paper has %d.' % (w, s['form'], js_str(s['count']), len(mine)))
                if sane and is_num(bp.get('totalPoints')):
                    tp = float(bp['totalPoints'])
                    if not abs(sp_ - tp) < 1e-9:
                        E('E-SCHEMA', x_p, 'The blueprint sections add up to %s points, but totalPoints is %s.' % (js_number(sp_), js_str(bp['totalPoints'])))
                    if qs is not None:
                        if sc_ != len(qs):
                            E('E-SCHEMA', x_p, 'The blueprint sections count %d questions, but the paper has %d.' % (sc_, len(qs)))
                        qp = sum(float(q['points']) for q in qs if is_obj(q) and is_num(q.get('points')))
                        if not abs(qp - tp) < 1e-9:
                            E('E-SCHEMA', x_p, 'The questions add up to %s points, but totalPoints is %s.' % (js_number(qp), js_str(bp['totalPoints'])))
            if is_pathway and qs is not None and (len(qs) < 10 or len(qs) > 30):
                W('W-FILL', x_p, 'The final quiz has %d questions; 10-30 across the steps are recommended.' % len(qs))

    # ---- exam profiles ----
    pr_p = 'exam/profiles.json'
    prd = None if is_part else getJ(pr_p)
    if ok(prd):
        num_scan(prd, pr_p)
        if not is_obj(prd) or not isinstance(prd.get('profiles'), list):
            E('E-SCHEMA', pr_p, 'exam/profiles.json must be {"profiles": [...]}.')
        else:
            for i, x in enumerate(prd['profiles']):
                w = 'profile ' + (x['subject'] if is_obj(x) and is_str(x.get('subject')) else '#%d' % (i + 1))
                if not is_obj(x):
                    E('E-SCHEMA', pr_p, w + ' must be an object.')
                    continue
                if not non_empty(x.get('subject')):
                    E('E-SCHEMA', pr_p, w + ': subject is missing.')
                if x.get('confidence') is not None and x.get('confidence') not in CONFIDENCE:
                    E('E-SCHEMA', pr_p, w + ': confidence must be user-stated, derived-from-artifact or inferred.')
                if x.get('durationMin') is not None and not is_num(x.get('durationMin')):
                    E('E-SCHEMA', pr_p, w + ': durationMin must be a number or null (never invent it: list it in unknownFields).')
                for k in ('openBook', 'lessonOnly'):
                    if x.get(k) is not None and not isinstance(x.get(k), bool):
                        E('E-SCHEMA', pr_p, '%s: %s must be true, false or null.' % (w, k))
                for k in ('forms', 'emphasis', 'unknownFields', 'refineWith'):
                    if x.get(k) is not None and not isinstance(x.get(k), list):
                        E('E-SCHEMA', pr_p, '%s: %s must be a list.' % (w, k))
                for k, f in enumerate(arr(x.get('forms'))):
                    if not is_obj(f) or not non_empty(f.get('id')) or not non_empty(f.get('name')):
                        E('E-SCHEMA', pr_p, '%s form %d needs an id and a name.' % (w, k + 1))
                    elif f.get('confidence') is not None and f.get('confidence') not in CONFIDENCE:
                        E('E-SCHEMA', pr_p, '%s form %s: confidence must be user-stated, derived-from-artifact or inferred.' % (w, f['id']))

    # ---- coverage ledger ----
    c_p = 'ledger/coverage.json'
    cd = None if is_part else getJ(c_p)
    if ok(cd):
        num_scan(cd, c_p)
        if not is_obj(cd):
            E('E-SCHEMA', c_p, 'ledger/coverage.json must map each source id to {items, niche, units: [...]}.')
        else:
            cited = set()
            for n in nodes_list:
                for r in arr(n.get('refs')):
                    if _hashable(r):
                        cited.add(r)
            for sid in cd:
                c = cd[sid]
                if not is_obj(c) or not isinstance(c.get('units'), list):
                    E('E-SCHEMA', c_p, sid + ' must be {items, niche, units: [...]}.')
                    continue
                if have_sources[0] and sid not in sources:
                    W('W-SCHEMA', c_p, sid + ' is not a source of this galaxy.')
                seen, uncited = set(), 0
                for i, u in enumerate(c['units']):
                    if not is_obj(u) or not is_int(u.get('n')) or not is_str(u.get('status')):
                        E('E-SCHEMA', c_p, '%s ledger entry %d needs n and status.' % (sid, i + 1))
                        continue
                    nk = _nkey(u['n'])
                    if nk in seen:
                        W('W-SCHEMA', c_p, '%s unit %s is listed twice.' % (sid, js_str(u['n'])))
                    seen.add(nk)
                    if u['status'] not in COVERAGE:
                        W('W-SCHEMA', c_p, '%s unit %s: status should be covered or no-content.' % (sid, js_str(u['n'])))
                    if u['status'] == 'covered' and ('%s#%s' % (sid, js_str(u['n']))) not in cited:
                        uncited += 1
                if uncited:
                    W('W-REF', c_p, '%s of %s are not cited by any node ref.' % (plural(uncited, 'covered unit'), sid))
                s = sources.get(sid)
                if s and s['units'] is not None and len(seen) < len(s['units']):
                    W('W-SCHEMA', c_p, 'The ledger lists %d of the %d units of %s (one entry per unit is expected).'
                      % (len(seen), len(s['units']), sid))

    # ---- parts: E-BASE ----
    part_info = ((parse_part(mf['part']) if is_obj(mf['part']) else None) if is_obj(mf) and mf.get('part') is not None
                 else parse_part(hdr.get('part')))
    if is_part:
        base_gid = (mf['base'].get('galaxyId') if is_obj(mf) and is_obj(mf.get('base')) and mf['base'].get('galaxyId') else None) \
            or (mf.get('galaxyId') if is_obj(mf) and mf.get('galaxyId') else None) or hdr.get('galaxyId') or None
        if not base:
            W('W-BASE', '', 'No base galaxy was given: node ids, refs and quotes of this part were not checked against it.')
        else:
            bm = base.get('meta') if is_obj(base.get('meta')) else {}
            if not base_gid:
                E('E-BASE', mp, 'The part does not say which galaxy it belongs to (base.galaxyId, or galaxyId= in the bundle header).')
            elif base_gid != bm.get('galaxyId'):
                E('E-BASE', mp, 'This part is for galaxy %s, not %s.' % (js_str(base_gid), js_str(bm.get('galaxyId'))))
            bh = mf['base'].get('contentHash') if is_obj(mf) and is_obj(mf.get('base')) else None
            if bh and bm.get('contentHash') and bh != bm['contentHash']:
                W('W-BASE', mp, 'The base galaxy changed since the work order was made (contentHash differs); the part is '
                                'still merged by node id.')
        wo_id = opts['workOrder'].get('workOrderId') if is_obj(opts.get('workOrder')) else None
        part_wo = (mf.get('workOrderId') if is_obj(mf) and mf.get('workOrderId') else None) or hdr.get('workOrder') or None
        if wo_id and part_wo and wo_id != part_wo:
            W('W-BASE', mp, 'This part answers work order %s, not %s.' % (js_str(part_wo), js_str(wo_id)))

    # ---- fill levels and focus pathways ----
    eff_lessons = dict(base.get('lessons') or {}) if is_part and base else {}
    all_nodes = list(node_by_id.values()) if is_part else nodes_list

    def ctx_of(i, l):
        g = l.get('guide') if is_obj(l) and is_obj(l.get('guide')) else {}
        return {'hasPrereq': i in pre_t or len(arr(g.get('needs'))) > 0}

    level_cache = {}

    def level_of(i):
        if i in level_cache:
            return level_cache[i]
        n = node_by_id.get(i) if isinstance(i, str) else None
        if not n:
            return 'L0'
        a, b = eff_lessons.get(i), lesson_files.get(i)
        la = fill_level(n, a, ctx_of(i, a)) if a else fill_level(n, None)
        lb = fill_level(n, b, ctx_of(i, b)) if b else None
        lv = lb if lb and RANK[lb] > RANK[la] else la
        level_cache[i] = lv
        return lv
    for n in all_nodes:
        R['stats']['fill'][level_of(n['id'])] += 1
    for i in lesson_files:
        n, l = node_by_id.get(i), lesson_files[i]
        if not n:
            continue
        bar = lesson_bar(n, l, ctx_of(i, l))
        path_l = 'lessons/%s.json' % i
        if not bar['ok']:
            W('W-FILL', path_l, 'Lesson %s (%s) is below the full-lesson bar, so it counts as L1: %s.'
              % (i, n.get('priority') or 'standard', '; '.join(bar['why'])))
        if bar['over']:
            W('W-FILL', path_l, 'Lesson %s is above the recommended range: %s.' % (i, '; '.join(bar['over'])))
    wo = opts['workOrder'] if is_obj(opts.get('workOrder')) else None
    # check_focus=False skips focus coverage (merge_part checks one lesson at a time; the full validate of the part checks coverage)
    check_focus = opts.get('checkFocus') is not False
    focus_pw = [pw for pw in pathways if pw.get('focus') is True] if check_focus else []
    for f in arr(wo.get('focus') if wo and check_focus else None):
        if not is_obj(f):
            continue
        key = f['pathway'] if is_str(f.get('pathway')) else (f['name'] if is_str(f.get('name')) else None)
        if not key:
            continue
        pw = next((x for x in pathways if x.get('id') == key), None) or next((x for x in pathways if x.get('name') == key), None)
        if pw is None:
            E('E-FOCUS', pw_p, 'Focus pathway %s from the work order is not in galaxy/pathways.json (build it there with '
                               '"focus": true).' % jstr(key))
        elif not any(x is pw for x in focus_pw):
            focus_pw.append(pw)
    scope = None
    if part_info and part_info['n'] < part_info['of']:
        plan = None
        if wo and is_obj(wo.get('parts')):
            plan = next((x for x in arr(wo['parts'].get('plan')) if is_obj(x) and _num_eq(x.get('n'), part_info['n'])), None)
        scope = set(x for x in arr(plan.get('nodes')) if _hashable(x)) if plan else set()
        if focus_pw:
            W('W-FOCUS', '', 'Part %d of %d: %s.' % (part_info['n'], part_info['of'],
                                                     ('only the %d nodes planned for this part are required now' % len(scope))
                                                     if scope else 'focus pathways are checked when the last part arrives'))
    want_l3 = bool(wo and is_obj(wo.get('generate')) and wo['generate'].get('focusLevel') == 'L3')
    for pw in focus_pw:
        ids, seen_ids = [], set()
        for x in _flat_ids(pw) + arr(pw.get('optional')):
            if isinstance(x, str) and x not in seen_ids:
                seen_ids.add(x)
                if x in node_by_id:
                    ids.append(x)
        missing = [x for x in ids if RANK[level_of(x)] < 2]
        R['stats']['focus'][js_str(pw.get('id'))] = {'nodes': len(ids), 'full': len(ids) - len(missing), 'missing': missing}
        req = [x for x in missing if x in scope] if scope is not None else missing
        if req:
            E('E-FOCUS', pw_p, 'Focus pathway "%s" is not fully generated: %d of %d nodes are below L2 (%s%s). Write full '
                               'lessons for them.' % (js_str(pw.get('name') or pw.get('id')), len(req), len(ids),
                                                      ', '.join(req[:8]), ', ...' if len(req) > 8 else ''))
        if want_l3:
            l2 = [x for x in ids if level_of(x) == 'L2']
            if l2:
                W('W-FOCUS', pw_p, 'Focus pathway "%s": %d nodes are L2; the work order asks for L3 (add the audit).'
                  % (js_str(pw.get('name') or pw.get('id')), len(l2)))

    # ---- aggregated quote warnings ----
    for k in unver:
        W('W-QUOTE', '' if k == '(no sources)' else 'sources/units/%s.json' % k, plural(unver[k], 'quote') + (
            ' could not be verified: no source text is available.' if k == '(no sources)'
            else ' against %s are unverifiable: its units are not included.' % k))
    for k in transcribed:
        W('W-QUOTE', 'sources/units/%s.json' % k, '%s matched transcribed text in %s (read by a model, not extracted): '
                                                 'check them against the original.' % (plural(transcribed[k], 'quote'), k))
    if not is_part and not have_sources[0] and nodes_list:
        W('W-REF', 'sources/index.json', 'No sources are included: refs were checked for grammar only.')
    if dropped[0]:
        R['errors'].append({'code': R['errors'][-1]['code'], 'path': '', 'msg': '%d more errors were not listed.' % dropped[0]})
    R['stats']['nodes'] = len(all_nodes)
    R['stats']['lessons'] = len(lesson_files)
    R['ok'] = not R['errors']
    R['_levels'] = {n['id']: level_of(n['id']) for n in all_nodes}
    return R


def non_empty_raw(x):
    """isStr(x) && x (a non-empty string; whitespace counts)."""
    return isinstance(x, str) and x != ''


def parse_ref(ref):
    """F.parseRef: {sid, n} or None."""
    m = RE_REF.fullmatch('' if ref is None else js_str(ref))
    return {'sid': m.group(1), 'n': int(m.group(2))} if m and int(m.group(2)) >= 1 else None


def _reserved(i):
    return i == '__root' or i.startswith('hub-') or i.startswith('stress-')


def _hashable(x):
    return isinstance(x, (str, int, float, bool)) or x is None


def _nkey(n):
    """Map key for a unit number (1 and 1.0 are the same JS number)."""
    if isinstance(n, float) and n.is_integer():
        return int(n)
    return n


def _num_eq(a, b):
    return isinstance(a, (int, float)) and not isinstance(a, bool) and a == b


def _cat(x):
    """'' + x in JS (string concatenation) for a JSON value."""
    return 'undefined' if x is None else js_str(x)


# ---------------------------------------------------------------------------------------------
# §12 merging a part into a galaxy (on files)
# ---------------------------------------------------------------------------------------------

def merge_part(galaxy_files, part_files, replace='higher', replace_guide=False, replace_exam=False, check_quotes=True):
    """F.mergePart on files: -> {files, added, replaced, skipped: [{id, why}], guideReplaced, examReplaced, revision}.
    Every lesson (and the guide/paper when asked) is validated as a part of this galaxy; nothing passed in changes."""
    if replace not in ('higher', 'always', 'never'):
        raise ValueError('replace must be higher, always or never')
    ctx = base_context(galaxy_files)
    gid = (ctx['meta'] or {}).get('galaxyId') or ''
    nodes = {n['id']: n for n in ctx['nodes'] if is_str(n.get('id'))}
    pre = _prereq_targets(ctx['edges'])
    lv = lambda n, l: fill_level(n, l, {'hasPrereq': n['id'] in pre or len(arr((l.get('guide') if is_obj(l) and is_obj(l.get('guide')) else {}).get('needs'))) > 0})

    # each piece alone: focus coverage is skipped (one lesson cannot cover a focus pathway; the full validate of the part checks it)
    def errors_of(p):
        return validate({p: part_files[p]}, profile='part', base=ctx, kind='bundle', check_quotes=check_quotes,
                        header={'profile': 'part', 'galaxyId': gid}, check_focus=False)['errors']
    out = dict(galaxy_files)
    res = {'added': [], 'replaced': [], 'skipped': [], 'guideReplaced': False, 'examReplaced': False,
           'guideOffered': 'guide/main.json' in part_files, 'examOffered': 'exam/mock.json' in part_files}
    for p in sorted(part_files):
        m = re.fullmatch(r'lessons/([^/]+)\.json', p)
        if not m:
            continue
        try:
            l = read_json(part_files, p)
        except FormatError as e:
            res['skipped'].append({'id': m.group(1), 'why': e.msg})
            continue
        i = l['nodeId'] if is_obj(l) and is_str(l.get('nodeId')) else m.group(1)
        n = nodes.get(i)
        if not n:
            res['skipped'].append({'id': i, 'why': 'node %s is not in this galaxy' % i})
            continue
        errs = errors_of(p)
        if errs:
            res['skipped'].append({'id': i, 'why': '%s: %s' % (plural(len(errs), 'error'), errs[0]['msg']), 'errors': errs})
            continue
        cur = ctx['lessons'].get(i)
        lv_new, lv_old = lv(n, l), (lv(n, cur) if cur else None)
        target = 'lessons/%s.json' % i
        if not cur:
            out[target] = part_files[p]
            res['added'].append(i)
        elif replace == 'always' or (replace == 'higher' and RANK[lv_new] > RANK[lv_old]):
            out[target] = part_files[p]
            res['replaced'].append(i)
        else:
            res['skipped'].append({'id': i, 'why': 'it already has a lesson (replace: never)' if replace == 'never'
                                   else 'the current lesson is already %s (incoming %s)' % (lv_old, lv_new)})
    for p, flag, done in (('guide/main.json', replace_guide, 'guideReplaced'), ('exam/mock.json', replace_exam, 'examReplaced')):
        if p not in part_files or flag is not True:
            continue
        try:
            read_json(part_files, p)
        except FormatError as e:
            res['skipped'].append({'id': p, 'why': e.msg})
            continue
        errs = errors_of(p)
        if errs:
            res['skipped'].append({'id': p, 'why': '%s: %s' % (plural(len(errs), 'error'), errs[0]['msg']), 'errors': errs})
            continue
        out[p] = part_files[p]
        res[done] = True
    res['revision'] = None
    if res['added'] or res['replaced'] or res['guideReplaced'] or res['examReplaced']:
        meta = _get(galaxy_files, 'galaxy/meta.json')
        meta = dict(meta) if is_obj(meta) else {}
        meta['revision'] = (int(meta['revision']) if is_int(meta.get('revision')) else 1) + 1
        meta.pop('contentHash', None)
        out['galaxy/meta.json'] = pretty_json(meta).encode('utf-8')
        res['revision'] = meta['revision']
    out.pop('manifest.json', None)            # the caller writes a fresh manifest (new contentHash)
    res['files'] = out
    return res


def pretty_json(v):
    """Readable JSON text (2-space indent). Digests are over canonical JSON, so formatting never matters."""
    return json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


# ---------------------------------------------------------------------------------------------
# §14 single-file embedding
# ---------------------------------------------------------------------------------------------

EMBED_MARKER = '<!--GX:EMBED-->'
_EMBED_RE = re.compile(r'<script\b[^>]*\bid=["\']?gx-embedded-galaxy["\']?[^>]*>([\s\S]*?)</script>', re.I)


def embed(files):
    """F.embed: the <script type="application/json" id="gx-embedded-galaxy">...</script> string; originals/ left out."""
    out = {}
    for p, d in files.items():
        if p.startswith('originals/'):
            continue
        why = path_problem(p)
        if why:
            _fail('E-PATH', 'Cannot embed %s: %s.' % (p, why), p)
        if is_json_path(p):
            try:
                out[p] = parse_json_text(d if isinstance(d, str) else _decode(d))
            except ValueError:
                _fail('E-JSON', p + ' is not valid JSON, so it cannot be embedded.', p)
        else:
            out[p] = d if isinstance(d, str) else _decode(d)
    js = canon({'format': 'galaxy-embed', 'schemaVersion': 1, 'files': out}).replace('<', '\\u003c')
    return '<script type="application/json" id="gx-embedded-galaxy">' + js + '</script>'


def unembed(text):
    """F.unembed: the embedded JSON (or a whole page holding it) -> {path: bytes}."""
    text = '' if text is None else js_str(text)
    m = _EMBED_RE.search(text)
    if m:
        text = m.group(1)
    try:
        o = parse_json_text(jtrim(text), MAX_JSON_DEPTH + 2)      # + 2: {files: {path: value}}
    except ValueError:
        _fail('E-CONTAINER', 'The embedded galaxy is not valid JSON.')
    if not is_obj(o) or o.get('format') != 'galaxy-embed' or not is_obj(o.get('files')):
        _fail('E-CONTAINER', 'This is not an embedded galaxy ({"format": "galaxy-embed", "files": {...}}).')
    if not is_int(o.get('schemaVersion')) or o['schemaVersion'] > VERSION:
        _fail('E-MANIFEST', 'The embedded galaxy uses schema version %s: update the reader.' % _cat(o.get('schemaVersion')))
    files, total = {}, 0
    for p, v in o['files'].items():
        check_path(p)
        b = _bytes(canon(v) if is_json_path(p) else (v if is_str(v) else canon(v)))
        total += len(b)
        files[p] = b
    if len(files) > LIMITS['entries']:
        _fail('E-SIZE', 'Too many embedded files (%d).' % len(files))
    if total > LIMITS['bytes']:
        _fail('E-SIZE', 'The embedded galaxy is too large (%s).' % fmt_mb(total))
    return files


def stamp_html(reader_html, files):
    """Replace the reader's <!--GX:EMBED--> marker (it must occur exactly once) with the embedded galaxy."""
    n = reader_html.count(EMBED_MARKER)
    if n != 1:
        _fail('E-CONTAINER', 'The reader must contain the %s marker exactly once (found %d): use an unstamped '
                             'galacticus-reader.html.' % (EMBED_MARKER, n))
    return reader_html.replace(EMBED_MARKER, embed(files), 1)


# ---------------------------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------------------------

class _Usage(Exception):
    pass


def _out(text=''):
    sys.stdout.write(text + '\n')


def _load(path):
    try:
        return read_input(path)
    except OSError as e:
        raise _Usage('cannot read %s: %s' % (path, e))


def _load_base(path):
    if not path:
        return None
    try:
        return _load(path)['files']
    except FormatError as e:
        raise _Usage('the base galaxy %s cannot be opened: %s %s' % (path, e.code, e.msg))


def _load_work_order(path):
    if not path:
        return None
    try:
        if os.path.isdir(path):
            path = os.path.join(path, 'work-order.json')
        if re.search(r'\.(zip|galaxy)\Z', path, re.I):
            with open(path, 'rb') as f:
                entries = zip_read(f.read())
            cands = sorted((n for n, _ in entries if n.split('/')[-1] == 'work-order.json'), key=len)
            if not cands:
                raise _Usage('no work-order.json in ' + path)
            wo = read_json(dict(entries), cands[0])
        else:
            with open(path, 'rb') as f:
                wo = read_json({'work-order.json': f.read()}, 'work-order.json')
    except OSError as e:
        raise _Usage('cannot read the work order %s: %s' % (path, e))
    except FormatError as e:
        raise _Usage('the work order cannot be read: %s %s' % (e.code, e.msg))
    if not is_obj(wo):
        raise _Usage('the work order must be a JSON object')
    return wo


def _container_report(e):
    return {'ok': False, 'profile': None, 'errors': [{'code': e.code, 'path': e.path, 'msg': e.msg}], 'warnings': [],
            'stats': {'nodes': 0, 'lessons': 0, 'fill': {k: 0 for k in LEVELS}, 'focus': {},
                      'quotes': {'checked': 0, 'verified': 0, 'unverifiable': 0, 'failed': 0}},
            'verified': False, 'verification': 'unverified', 'contentHash': None, 'manifest': None}


def _print_report(rep, inp=None, label=''):
    st = rep['stats']
    fill = st.get('fill', {})
    head = 'gxformat validate%s' % (' ' + label if label else '')
    if inp:
        head += '  [%s%s]' % (inp['kind'], (', root ' + inp['root'] + '/') if inp.get('root') else '')
    _out(head)
    _out('  profile %s | %d nodes | %d lessons | fill L0 %d, L1 %d, L2 %d, L3 %d'
         % (rep['profile'], st.get('nodes', 0), st.get('lessons', 0), fill.get('L0', 0), fill.get('L1', 0),
            fill.get('L2', 0), fill.get('L3', 0)))
    q = st.get('quotes', {})
    _out('  quotes: %d checked, %d verified, %d unverifiable, %d failed'
         % (q.get('checked', 0), q.get('verified', 0), q.get('unverifiable', 0), q.get('failed', 0)))
    for pid, f in sorted(st.get('focus', {}).items()):
        _out('  focus %s: %d/%d full%s' % (pid, f['full'], f['nodes'],
                                         (' | missing: ' + ', '.join(f['missing'][:10])) if f['missing'] else ''))
    _out('  manifest: %s%s' % (rep.get('verification', 'unverified'),
                               (' (contentHash %s)' % rep['contentHash']) if rep.get('contentHash') else ''))
    if rep['errors']:
        _out('ERRORS (%d)' % len(rep['errors']))
        for e in rep['errors'][:300]:
            _out('  %-15s %s  %s' % (e['code'], e['path'] or '-', e['msg']))
        if len(rep['errors']) > 300:
            _out('  ... %d more (use --json for all)' % (len(rep['errors']) - 300))
    if rep['warnings']:
        _out('WARNINGS (%d)' % len(rep['warnings']))
        by = {}
        for w in rep['warnings']:
            by.setdefault(w['code'], []).append(w)
        for code in sorted(by):
            items = by[code]
            for w in items[:6]:
                _out('  %-15s %s  %s' % (w['code'], w['path'] or '-', w['msg']))
            if len(items) > 6:
                _out('  %-15s ... and %d more like this' % (code, len(items) - 6))
    if rep['errors']:
        codes = {}
        for e in rep['errors']:
            codes[e['code']] = codes.get(e['code'], 0) + 1
        _out('RESULT: %d error(s) [%s], %d warning(s): fix the errors and validate again'
             % (len(rep['errors']), ', '.join('%s x%d' % kv for kv in sorted(codes.items())), len(rep['warnings'])))
    else:
        _out('RESULT: OK, 0 errors, %d warning(s)' % len(rep['warnings']))


def _write_folder(folder, files, force=False):
    if os.path.exists(folder) and not os.path.isdir(folder):
        raise _Usage('%s exists and is not a folder' % folder)
    if os.path.isdir(folder) and os.listdir(folder) and not force:
        raise _Usage('%s is not empty: choose a new folder (or pass --force to write into it)' % folder)
    root = os.path.realpath(folder)
    for p in sorted(files):
        check_path(p)
        full = os.path.realpath(os.path.join(root, *p.split('/')))
        if not full.startswith(root + os.sep):
            _fail('E-PATH', 'unsafe path ' + p, p)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'wb') as f:
            f.write(_bytes(files[p]))


def cmd_validate(a):
    wo = _load_work_order(a.work_order)
    base = _load_base(a.base)
    try:
        inp = _load(a.path)
        rep = validate_input(inp, profile=a.profile, work_order=wo, base=base, check_quotes=not a.no_quotes)
    except FormatError as e:
        inp, rep = None, _container_report(e)
    rep.pop('_levels', None)
    if a.json:
        _out(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        _print_report(rep, inp, a.path)
    return 0 if rep['ok'] else 1


def cmd_stats(a):
    wo = _load_work_order(a.work_order)
    base = _load_base(a.base)
    try:
        inp = _load(a.path)
    except FormatError as e:
        _out('%s %s' % (e.code, e.msg))
        return 1
    rep = validate_input(inp, work_order=wo, base=base)
    by_node = rep.pop('_levels', {})
    st = rep['stats']
    if a.json:
        _out(json.dumps({'profile': rep['profile'], 'stats': st, 'fillByNode': by_node, 'verification': rep['verification'],
                         'contentHash': rep['contentHash'], 'errors': len(rep['errors']), 'warnings': len(rep['warnings'])},
                        ensure_ascii=False, indent=1))
        return 0
    _out('gxformat stats %s  [%s]' % (a.path, inp['kind']))
    _out('  profile %s | %d nodes | %d lessons | manifest %s' % (rep['profile'], st['nodes'], st['lessons'], rep['verification']))
    _out('  fill: ' + ', '.join('%s %d' % (k, st['fill'].get(k, 0)) for k in LEVELS))
    q = st['quotes']
    _out('  quotes: %d checked, %d verified, %d unverifiable, %d failed'
         % (q['checked'], q['verified'], q['unverifiable'], q['failed']))
    if st['focus']:
        for pid, f in sorted(st['focus'].items()):
            _out('  focus %s: %d/%d full%s' % (pid, f['full'], f['nodes'],
                                             (' | missing: ' + ', '.join(f['missing'])) if f['missing'] else ''))
    else:
        _out('  focus pathways: none')
    lv = {}
    for nid, l in by_node.items():
        lv.setdefault(l, []).append(nid)
    for k in ('L3', 'L2'):
        if lv.get(k):
            _out('  %s: %s' % (k, ', '.join(sorted(lv[k]))))
    _out('  validation: %d error(s), %d warning(s) (run validate for details)' % (len(rep['errors']), len(rep['warnings'])))
    return 0


def _folder_input(folder, what):
    if not os.path.isdir(folder):
        raise _Usage('%s needs a galaxy folder: %s' % (what, folder))
    inp = _load(folder)
    if inp['root']:
        raise _Usage('the galaxy root is %s/ inside this folder: run %s on that folder' % (inp['root'], what))
    return inp


def cmd_manifest(a):
    inp = _folder_input(a.folder, 'manifest')
    files = inp['files']
    old = _get(files, 'manifest.json')
    old = old if is_obj(old) else {}
    prof = a.profile or old.get('profile')
    wo, pt = _part_args(a, old)
    m = build_manifest(files, profile=prof, exported_by=a.exported_by, base=old.get('base') if prof == 'part' else None,
                       work_order_id=wo, part=pt)
    with open(os.path.join(a.folder, 'manifest.json'), 'wb') as f:
        f.write(pretty_json(m).encode('utf-8'))
    _out('wrote %s/manifest.json: %d entries, contentHash %s' % (a.folder.rstrip('/\\'), len(m['entries']), m['contentHash']))
    return 0


def _part_args(a, old):
    """--work-order and --part, else the folder's manifest (stub) values: written for any profile (§8.3, §11.1)."""
    if a.part and not parse_part(a.part):
        raise _Usage('--part must look like 1/3 (whole numbers, 1 <= n <= of)')
    return a.work_order or old.get('workOrderId'), a.part or old.get('part')


def cmd_pack(a):
    inp = _folder_input(a.folder, 'pack')
    files = dict(inp['files'])
    old = _get(files, 'manifest.json')
    old = old if is_obj(old) else {}
    meta = _get(files, 'galaxy/meta.json')
    prof = old.get('profile') or meta_profile(meta) or ('galaxy' if 'galaxy/meta.json' in files else 'part')
    wo, pt = _part_args(a, old)
    outp = os.path.realpath(a.out)
    left = []
    for p in list(files):
        if os.path.realpath(os.path.join(a.folder, *p.split('/'))) == outp or not known_path(p, prof):
            del files[p]
            left.append(p)
    if left:
        _out('left out (not galaxy paths): ' + ', '.join(sorted(left)))
    files.pop('manifest.json', None)
    m = build_manifest(files, profile=prof, exported_by=a.exported_by, base=old.get('base') if prof == 'part' else None,
                       work_order_id=wo, part=pt)
    files['manifest.json'] = pretty_json(m).encode('utf-8')
    rep = validate(files, kind='zip')
    if rep['errors'] and not a.force:
        _print_report(rep, None, a.folder)
        _out('not packed: fix the errors first (or pass --force)')
        return 1
    with open(os.path.join(a.folder, 'manifest.json'), 'wb') as f:
        f.write(files['manifest.json'])
    data = zip_bytes(files, deflate=a.deflate)
    with open(a.out, 'wb') as f:
        f.write(data)
    _out('packed %s: %d files, %s, contentHash %s, %d error(s), %d warning(s)'
         % (a.out, len(files), fmt_mb(len(data)), m['contentHash'], len(rep['errors']), len(rep['warnings'])))
    return 0


def cmd_html(a):
    inp = _load(a.galaxy)
    files = {p: d for p, d in inp['files'].items() if not p.startswith('originals/')}
    try:
        with open(a.reader, 'rb') as f:
            reader = f.read().decode('utf-8')
    except (OSError, UnicodeDecodeError) as e:
        raise _Usage('cannot read the reader %s: %s' % (a.reader, e))
    if reader.count(EMBED_MARKER) != 1:
        raise _Usage('the reader must contain %s exactly once (found %d): use an unstamped galacticus-reader.html'
                     % (EMBED_MARKER, reader.count(EMBED_MARKER)))
    hdr = inp.get('header') or {}
    old = _get(files, 'manifest.json')
    listed = old.get('entries') if is_obj(old) and is_obj(old.get('entries')) else None
    if listed is None or any(p not in files for p in listed if p != 'manifest.json'):
        old = old if is_obj(old) else {}
        prof = old.get('profile') or hdr.get('profile')
        m = build_manifest({p: d for p, d in files.items() if p != 'manifest.json'}, profile=prof,
                           exported_by=old.get('exportedBy'),
                           base=old.get('base') or ({'galaxyId': hdr.get('galaxyId')} if prof == 'part' else None),
                           work_order_id=old.get('workOrderId') or hdr.get('workOrder'), part=old.get('part') or hdr.get('part'))
        files['manifest.json'] = pretty_json(m).encode('utf-8')
        _out('note: manifest.json computed for the page (%s)' % ('originals/ are not embedded' if listed else 'there was none'))
    rep = validate(files, kind='embed', header=hdr or None)
    if rep['errors'] and not a.force:
        _print_report(rep, inp, a.galaxy)
        _out('not stamped: fix the errors first (or pass --force)')
        return 1
    html = stamp_html(reader, files)
    with open(a.out, 'wb') as f:
        f.write(html.encode('utf-8'))
    _out('wrote %s (%s): profile %s, %d error(s), %d warning(s), %s'
         % (a.out, fmt_mb(len(html.encode('utf-8'))), rep['profile'], len(rep['errors']), len(rep['warnings']), rep['verification']))
    return 0


def cmd_bundle(a):
    inp = _load(a.folder)
    files = inp['files']
    meta = _get(files, 'galaxy/meta.json')
    man = _get(files, 'manifest.json')
    meta = meta if is_obj(meta) else {}
    man = man if is_obj(man) else {}
    prof = a.profile or man.get('profile') or meta_profile(meta) or ('galaxy' if 'galaxy/meta.json' in files else 'part')
    hdr = {'profile': prof}
    if prof == 'part':
        b = man.get('base') if is_obj(man.get('base')) else {}
        pt = parse_part(a.part) if a.part else parse_part(man.get('part'))
        hdr['galaxyId'] = a.galaxy_id or b.get('galaxyId') or man.get('galaxyId')
        hdr['workOrder'] = a.work_order or man.get('workOrderId')
        hdr['part'] = '%d/%d' % (pt['n'], pt['of']) if pt else None
        missing = [k for k in ('galaxyId', 'workOrder', 'part') if not hdr.get(k)]
        if missing:
            raise _Usage('a part bundle needs --galaxy-id, --work-order and --part n/of (missing: %s)' % ', '.join(missing))
    else:
        mpt = parse_part(man.get('part')) if is_obj(man.get('part')) else None     # what manifest/pack --part wrote
        for k, v in (('galaxyId', a.galaxy_id or meta.get('galaxyId')), ('workOrder', a.work_order or man.get('workOrderId')),
                     ('part', a.part or ('%d/%d' % (mpt['n'], mpt['of']) if mpt else None))):
            if v:
                hdr[k] = v
    out, skipped = {}, []
    for p in sorted(files):
        if p == 'manifest.json' or p.startswith('originals/') or is_junk(p):
            continue
        if not known_path(p, prof):
            skipped.append(p)
            continue
        try:
            out[p] = _decode_fatal(files[p])
        except UnicodeDecodeError:
            skipped.append(p)
    text = emit_text_bundle(hdr, out)
    if a.out:
        with open(a.out, 'wb') as f:
            f.write(text.encode('utf-8'))
        sys.stderr.write('wrote %s: %d files%s\n' % (a.out, len(out), (', skipped ' + ', '.join(skipped)) if skipped else ''))
    else:
        sys.stdout.flush()
        sys.stdout.buffer.write(text.encode('utf-8'))
        sys.stdout.buffer.flush()
        if skipped:
            sys.stderr.write('skipped (binary or not part of a %s): %s\n' % (prof, ', '.join(skipped)))
    return 0


def cmd_unbundle(a):
    try:
        with open(a.bundle, 'rb') as f:
            raw = f.read()
    except OSError as e:
        raise _Usage('cannot read %s: %s' % (a.bundle, e))
    parsed = parse_text_bundle(_decode(raw))
    for e in parsed['errors']:
        _out('%s %s' % (e['code'], e['msg']))
    if not parsed['bundles']:
        return 1
    files, hdr = {}, parsed['bundles'][0]['header']
    for b in parsed['bundles']:
        for p, c in b['files'].items():
            files[p] = _bytes(c)
    prof = hdr.get('profile')
    try:
        m = build_manifest(files, profile=prof, base={'galaxyId': hdr.get('galaxyId'), 'revision': None, 'contentHash': None}
                           if prof == 'part' else None, work_order_id=hdr.get('workOrder'), part=hdr.get('part'))
        files['manifest.json'] = pretty_json(m).encode('utf-8')
    except FormatError as e:
        _out('%s %s (no manifest written)' % (e.code, e.msg))
    _write_folder(a.out, files, force=a.force)
    _out('unbundled %d file(s) from %d bundle(s) into %s' % (len(files), len(parsed['bundles']), a.out))
    return 1 if parsed['errors'] else 0


def cmd_merge(a):
    g = _load(a.galaxy)
    p = _load(a.part)
    pre = validate_input(p, profile='part', base=g['files'])
    fatal = [e for e in pre['errors'] if (e['code'] in BLOCKING or e['code'] == 'E-BASE') and not e['path'].startswith('lessons/')]
    if fatal:
        for e in fatal:
            _out('%s %s  %s' % (e['code'], e['path'] or '-', e['msg']))
        _out('nothing merged: this part cannot be merged into %s' % a.galaxy)
        return 1
    res = merge_part(g['files'], p['files'], replace=a.replace, replace_guide=a.replace_guide, replace_exam=a.replace_exam)
    files = res['files']
    m = build_manifest(files, exported_by='%s %s merge' % (TOOL, TOOL_VERSION))
    files['manifest.json'] = pretty_json(m).encode('utf-8')
    _write_folder(a.out, files, force=a.force)
    meta = _get(files, 'galaxy/meta.json')
    rev = res['revision'] if res['revision'] is not None else (
        '%s (unchanged: nothing was merged)' % (meta.get('revision') if is_obj(meta) else '?'))
    _out('merged into %s: added %d, replaced %d, skipped %d%s%s; revision %s; contentHash %s'
         % (a.out, len(res['added']), len(res['replaced']), len(res['skipped']),
            ', main guide replaced' if res['guideReplaced'] else '', ', paper replaced' if res['examReplaced'] else '',
            rev, m['contentHash']))
    for x in ('guide', 'exam'):
        if res[x + 'Offered'] and not res[x + 'Replaced']:
            _out('  the part also carries %s: pass --replace-%s to take it' % ('guide/main.json' if x == 'guide' else 'exam/mock.json', x))
    for s in res['skipped']:
        _out('  skipped %s: %s' % (s['id'], s['why']))
    rep = validate(files, kind='folder')
    _out('merged galaxy: %d error(s), %d warning(s)' % (len(rep['errors']), len(rep['warnings'])))
    return 0 if rep['ok'] else 1


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))
    ap = argparse.ArgumentParser(prog='gxformat.py', description='Galaxy format v1: validate, hash, pack, bundle, stamp '
                                                                 'and merge galaxies.')
    sub = ap.add_subparsers(dest='cmd')
    v = sub.add_parser('validate', help='validate a galaxy, a part or a pathway course')
    v.add_argument('path')
    v.add_argument('--profile', choices=PROFILES)
    v.add_argument('--work-order')
    v.add_argument('--base')
    v.add_argument('--no-quotes', action='store_true')
    v.add_argument('--json', action='store_true')
    m = sub.add_parser('manifest', help='write or refresh manifest.json in a galaxy folder')
    m.add_argument('folder')
    m.add_argument('--profile', choices=PROFILES)
    m.add_argument('--exported-by')
    m.add_argument('--work-order', help='write this "workOrderId" (any profile; default: the existing manifest\'s)')
    m.add_argument('--part', help='write "part": {n, of} from n/of, e.g. 1/3 for part 1 of a split answer')
    p = sub.add_parser('pack', help='manifest + zip a galaxy folder into a .galaxy')
    p.add_argument('folder')
    p.add_argument('out')
    p.add_argument('--exported-by')
    p.add_argument('--work-order', help='write this "workOrderId" (any profile; default: the existing manifest\'s)')
    p.add_argument('--part', help='write "part": {n, of} from n/of, e.g. 1/3 for part 1 of a split answer')
    p.add_argument('--deflate', action='store_true', help='compress JSON and text (default: STORED, like the app)')
    p.add_argument('--force', action='store_true', help='pack even when validation finds errors')
    h = sub.add_parser('html', help='stamp a galaxy into the portable reader (one self-contained file)')
    h.add_argument('galaxy')
    h.add_argument('reader')
    h.add_argument('out')
    h.add_argument('--force', action='store_true')
    b = sub.add_parser('bundle', help='print a text bundle of a folder')
    b.add_argument('folder')
    b.add_argument('--profile', choices=PROFILES)
    b.add_argument('--galaxy-id')
    b.add_argument('--work-order')
    b.add_argument('--part')
    b.add_argument('--out', help='write to this file instead of stdout')
    u = sub.add_parser('unbundle', help='write the files of a text bundle (and a manifest) into a folder')
    u.add_argument('bundle')
    u.add_argument('out')
    u.add_argument('--force', action='store_true')
    s = sub.add_parser('stats', help='fill levels, focus pathways and quotes')
    s.add_argument('path')
    s.add_argument('--work-order')
    s.add_argument('--base')
    s.add_argument('--json', action='store_true')
    g = sub.add_parser('merge', help='merge a part into a galaxy, writing the result to a new folder')
    g.add_argument('galaxy')
    g.add_argument('part')
    g.add_argument('out')
    g.add_argument('--replace', choices=('higher', 'always', 'never'), default='higher')
    g.add_argument('--replace-guide', action='store_true', help='take the part\'s guide/main.json')
    g.add_argument('--replace-exam', action='store_true', help='take the part\'s exam/mock.json')
    g.add_argument('--force', action='store_true')
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if not a.cmd:
        ap.print_help()
        return 2
    fn = {'validate': cmd_validate, 'manifest': cmd_manifest, 'pack': cmd_pack, 'html': cmd_html, 'bundle': cmd_bundle,
          'unbundle': cmd_unbundle, 'stats': cmd_stats, 'merge': cmd_merge}[a.cmd]
    try:
        return fn(a)
    except _Usage as e:
        sys.stderr.write('gxformat: %s\n' % e)
        return 2
    except FormatError as e:
        sys.stderr.write('gxformat: %s %s\n' % (e.code, e.msg))
        return 1 if a.cmd in ('validate', 'merge', 'unbundle', 'html', 'stats') else 2
    except OSError as e:
        sys.stderr.write('gxformat: %s\n' % e)
        return 2


if __name__ == '__main__':
    sys.exit(main())
