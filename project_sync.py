"""
project_sync.py
===============
Run this at the start of any Claude session and paste the output into the chat.
Gives Claude instant full project context without pasting entire source files.

Usage:
    python3 project_sync.py              # full sync
    python3 project_sync.py --diff       # only files changed since last sync
    python3 project_sync.py --file foo.py  # dump one specific file in full
    python3 project_sync.py --errors     # syntax check only
"""

import os, sys, json, ast, hashlib, argparse, time
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
EXTENSIONS  = ['.py', '.json']
IGNORE      = ['__pycache__', '.git', 'venv', 'node_modules', '.idea',
               'project_sync.py']  # don't report on ourselves
STATE_FILE  = PROJECT_DIR / '.sync_state.json'

# ── File collection ────────────────────────────────────────────

def collect_files():
    files = []
    for ext in EXTENSIONS:
        # Only direct children — not recursive into subdirs unless they look like game modules
        for f in sorted(PROJECT_DIR.rglob('*' + ext)):
            parts = f.relative_to(PROJECT_DIR).parts
            # Skip if any path component is in ignore list
            if any(ig in parts for ig in IGNORE):
                continue
            # Skip hidden dirs (.cache, .git etc)
            if any(p.startswith('.') for p in parts[:-1]):
                continue
            # Only go one level deep into subdirs that look like game folders
            if len(parts) > 2:
                continue
            files.append(f)
    return sorted(files)

def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]

# ── State tracking (for --diff) ───────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {}

def save_state(files):
    state = {str(f.relative_to(PROJECT_DIR)): file_hash(f) for f in files}
    state['_timestamp'] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state

def changed_since_last(files, state) -> list:
    changed = []
    for f in files:
        key = str(f.relative_to(PROJECT_DIR))
        if key not in state or state[key] != file_hash(f):
            changed.append(f)
    return changed

# ── Python structure extraction ────────────────────────────────

def extract_structure(path: Path) -> list:
    """
    Returns a list of strings describing the structure of a Python file —
    classes, methods, top-level functions, key constants.
    Does NOT return actual code.
    """
    lines = []
    try:
        src  = path.read_text(errors='ignore')
        tree = ast.parse(src)
    except SyntaxError as ex:
        return [f"  !! SYNTAX ERROR: {ex}"]

    # Top-level constants (ALL_CAPS assignments)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    lines.append(f"  CONST {t.id}")

    # Top-level functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            lines.append(f"  def {node.name}({', '.join(args)})")

    # Classes with methods
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else '?' for b in node.bases]
            base_str = '('+', '.join(bases)+')' if bases else ''
            lines.append(f"  class {node.name}{base_str}:")
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in child.args.args if a.arg != 'self']
                    prefix = '    async def' if isinstance(child, ast.AsyncFunctionDef) else '    def'
                    lines.append(f"{prefix} {child.name}({', '.join(args)})")

    return lines if lines else ["  (no public structure)"]

# ── JSON summary ───────────────────────────────────────────────

def summarise_json(path: Path) -> str:
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            keys = list(data.keys())
            first_val = next(iter(data.values())) if data else {}
            # Category library file (dict of geometry dicts)
            if isinstance(first_val, dict) and 'segments' in first_val:
                return (f"  GEOMETRY LIBRARY: {len(data)} entries\n" +
                        '\n'.join(f"    - {k}" for k in sorted(keys)))
            else:
                preview = str(keys[:6])[1:-1]
                return f"  dict: {len(data)} keys — {preview}"
        elif isinstance(data, list):
            return f"  list: {len(data)} items"
        else:
            return f"  value: {type(data).__name__}"
    except Exception as ex:
        return f"  !! JSON ERROR: {ex}"

# ── Syntax check ───────────────────────────────────────────────

def syntax_check(files) -> list:
    errors = []
    ok     = 0
    for f in files:
        if f.suffix != '.py':
            continue
        try:
            ast.parse(f.read_text(errors='ignore'))
            ok += 1
        except SyntaxError as ex:
            errors.append(f"  SYNTAX ERROR in {f.name}: line {ex.lineno} — {ex.msg}")
    return errors, ok

# ── Report builders ────────────────────────────────────────────

def build_full_report(files, changed=None) -> str:
    out = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    out.append("=" * 60)
    out.append(f"PROJECT SYNC  —  {PROJECT_DIR.name}  —  {now}")
    out.append("=" * 60)

    # ── File inventory
    out.append("\n── FILES " + "─" * 50)
    py_files   = [f for f in files if f.suffix == '.py']
    json_files = [f for f in files if f.suffix == '.json']
    total_lines = 0
    for f in files:
        rel    = f.relative_to(PROJECT_DIR)
        try:
            lines = len(f.read_text(errors='ignore').splitlines())
        except:
            lines = 0
        total_lines += lines
        size   = f.stat().st_size
        chg    = " ◄ CHANGED" if changed is not None and f in changed else ""
        out.append(f"  {str(rel):<42} {lines:>4} lines  {size:>7}b{chg}")
    out.append(f"\n  Total: {len(files)} files, {total_lines} lines")

    # ── Syntax check
    out.append("\n── SYNTAX CHECK " + "─" * 42)
    errors, ok = syntax_check(files)
    if errors:
        out.extend(errors)
    else:
        out.append(f"  All {ok} Python files OK")

    # ── Python structure
    out.append("\n── PYTHON STRUCTURE " + "─" * 38)
    for f in py_files:
        rel = f.relative_to(PROJECT_DIR)
        out.append(f"\n  {rel}:")
        out.extend(extract_structure(f))

    # ── JSON data files
    if json_files:
        out.append("\n── DATA FILES " + "─" * 44)
        for f in json_files:
            rel = f.relative_to(PROJECT_DIR)
            out.append(f"\n  {rel}:")
            out.append(summarise_json(f))

    # ── Session notes for Claude
    out.append("\n── FOR CLAUDE " + "─" * 45)
    out.append("  Project: Space game (Arcade 3.x, Python)")
    out.append("  Key modules:")
    module_notes = {
        'vector_ships.py':       'geometry dataclasses + renderer + load_library()',
        'vector_editor.py':      'standalone editor — draws/saves vector geometry',
        'warp_effects.py':       'elongation/vortex/fold warp + Picard Manoeuvre',
        'destruction_effects.py':'debris physics, shockwaves, toxic clouds',
        'screen_effects.py':     'camera shake, GUI trauma, engine trails',
        'damage_model.py':       '3-layer damage (shields/armour/hull), 8 types',
        'player_hud.py':         'world-space + screen-space HUD renderers',
        'ai_controller.py':      'faction AI with weighted scoring',
        'galaxy_generator.py':   'Voronoi galaxy with faction territories',
        'weapon_effects.py':     'projectile FX with bloom shader',
        'sound_manager.py':      'spatial audio engine (planned)',
        'builtin_ships.json':    '5 built-in race ships — colonial/machine/pirate/hive/syndicate',
        'ships.json':            'editor-created ship geometries',
        'stations.json':         'editor-created station geometries',
    }
    for fname, note in module_notes.items():
        if any(f.name == fname for f in files):
            out.append(f"    {fname:<30} {note}")

    out.append("\n" + "=" * 60)
    out.append("END SYNC — paste above into Claude chat")
    out.append("=" * 60)
    return '\n'.join(out)

def build_diff_report(files, state) -> str:
    changed = changed_since_last(files, state)
    if not changed:
        return "NO CHANGES since last sync.\nAll files match saved state."
    out = ["CHANGED FILES since last sync:"]
    for f in changed:
        rel = f.relative_to(PROJECT_DIR)
        out.append(f"  ◄ {rel}")
    out.append("")
    out.append("Run without --diff for full report, or --file <name> to dump one file.")
    return '\n'.join(out)

# ── Main ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Project sync tool for Claude sessions')
    parser.add_argument('--diff',   action='store_true', help='Show only changed files')
    parser.add_argument('--file',   type=str,            help='Dump one file in full')
    parser.add_argument('--errors', action='store_true', help='Syntax check only')
    args = parser.parse_args()

    files = collect_files()
    state = load_state()

    if args.file:
        # Dump one specific file in full
        target = PROJECT_DIR / args.file
        if not target.exists():
            # Try fuzzy match
            matches = [f for f in files if args.file in f.name]
            if matches:
                target = matches[0]
            else:
                print(f"File not found: {args.file}")
                sys.exit(1)
        print(f"=== {target.name} ===")
        print(target.read_text(errors='ignore'))
        return

    if args.errors:
        errors, ok = syntax_check(files)
        if errors:
            print('\n'.join(errors))
        else:
            print(f"All {ok} Python files have valid syntax.")
        return

    if args.diff:
        print(build_diff_report(files, state))
        return

    # Full report — save state after
    changed = changed_since_last(files, state) if state else None
    print(build_full_report(files, changed))
    save_state(files)

if __name__ == '__main__':
    main()
