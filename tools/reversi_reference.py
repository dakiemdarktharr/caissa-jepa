"""Pinned, isolated y-tetsu PyListBoard differential rules audit.

acquire SOURCE creates a fresh ignored original-source directory.
smoke SOURCE runs only small loader/wrapper checks in an isolated subprocess.
audit SOURCE OUTPUT runs the frozen finite audit; do not run alongside training.
No dataset, checkpoint, label solver or training modules are used.
"""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types
import urllib.request

VERSION = 'reversi-reference-audit01'
COMMIT = '60b386dd16fb9d753e50736443a600cae24a5170'
TREE = 'a8b01cfbea84be41fbde7c33dd78cdcbe706d554'
REPOSITORY = 'https://github.com/y-tetsu/reversi'
RAW = 'https://raw.githubusercontent.com/y-tetsu/reversi/' + COMMIT + '/'
API = 'https://api.github.com/repos/y-tetsu/reversi/git/'
# Verified against the original GitHub commit and its recursive tree before coding.
BLOBS = {
    'LICENSE': ('25f8c51833edf4da3778bc4e9c638b57e9b0e0b2', 1064),
    'reversi/color.py': ('a76272d98cc71481a64b42fd247fd57f49d18884', 1262),
    'reversi/disc.py': ('88c57617defbbe5c522e6aa4ec4ca3982a5008e4', 1576),
    'reversi/board.py': ('35aaade5cd62d47516d223dca25b2aa60f083d3c', 19958),
    'reversi/game.py': ('61eebcb31f2e335bd022122f22447aec46d80fcb', 3692),
}
LIMIT_SECONDS = 120.
LIMIT_BYTES = 256_000_000
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'chess_data/external-y-tetsu-60b386d'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def write_new(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    require(len(data) + sum(p.stat().st_size for p in Path(path).parent.rglob('*') if p.is_file()) < LIMIT_BYTES, 'Output cap exceeded')
    with Path(path).open('xb') as stream:
        stream.write(data)


def fetch(url):
    require(url.startswith(('https://api.github.com/', 'https://raw.githubusercontent.com/')), 'HTTPS origin rejected')
    request = urllib.request.Request(url, headers={'User-Agent': VERSION})
    with urllib.request.urlopen(request, timeout=20) as response:
        require(response.url.startswith(('https://api.github.com/', 'https://raw.githubusercontent.com/')), 'Redirect origin rejected')
        data = response.read(2_000_001)
    require(len(data) <= 2_000_000, 'Source response too large')
    return data


def acquire(destination):
    destination = Path(destination)
    require(not destination.exists(), 'Acquisition destination already exists')
    commit = json.loads(fetch(API + 'commits/' + COMMIT))
    require(commit['sha'] == COMMIT and commit['tree']['sha'] == TREE, 'Pinned commit/tree mismatch')
    tree = json.loads(fetch(API + 'trees/' + TREE + '?recursive=1'))
    require(tree['sha'] == TREE and not tree.get('truncated', False), 'Invalid upstream tree')
    index = {row['path']: row for row in tree['tree']}
    originals = {}
    for name, (blob, size) in BLOBS.items():
        row = index[name]
        require(row['sha'] == blob and row['size'] == size and row['type'] == 'blob' and row['mode'] == '100644', 'Pinned blob identity mismatch')
        data = fetch(RAW + name)
        require(len(data) == size and blob_sha(data) == blob, 'Downloaded bytes do not match Git blob')
        originals[name] = data
    license_text = originals['LICENSE'].decode('utf-8')
    require('MIT License' in license_text and 'Copyright (c) 2019 y-tetsu' in license_text and
            'Permission is hereby granted, free of charge' in license_text, 'Pinned MIT notice missing')
    manifest = {'version': VERSION, 'repository': REPOSITORY, 'commit': COMMIT,
                'tree': TREE, 'acquired_utc': datetime.now(timezone.utc).isoformat(),
                'license': 'MIT', 'license_path': 'LICENSE', 'license_sha256': sha(originals['LICENSE']),
                'files': [{'path': name, 'url': RAW + name, 'bytes': len(data),
                           'sha256': sha(data), 'git_blob_sha1': blob_sha(data)}
                          for name, data in originals.items()]}
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in originals.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    write_new(destination / 'manifest.json', manifest)
    verify_source(destination)
    return manifest


def verify_source(source):
    source = Path(source).resolve()
    require(not any(p.is_symlink() for p in source.rglob('*')), 'Source symlinks rejected')
    require({p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()} == set(BLOBS) | {'manifest.json'}, 'Unexpected source file inventory')
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    require(manifest['version'] == VERSION and manifest['commit'] == COMMIT and manifest['tree'] == TREE and
            manifest['repository'] == REPOSITORY and manifest['license'] == 'MIT' and manifest['license_path'] == 'LICENSE', 'Invalid source manifest identity')
    rows = manifest['files']
    require(len(rows) == len(BLOBS) and {r['path'] for r in rows} == set(BLOBS), 'Invalid manifest path inventory')
    for row in rows:
        blob, size = BLOBS[row['path']]
        data = (source / row['path']).read_bytes()
        require(row['url'] == RAW + row['path'] and row['bytes'] == len(data) == size and
                row['git_blob_sha1'] == blob_sha(data) == blob and row['sha256'] == sha(data), 'Source hash mismatch: ' + row['path'])
    require(manifest['license_sha256'] == sha((source / 'LICENSE').read_bytes()), 'License hash mismatch')
    return manifest


@contextmanager
def reference_namespace(source):
    """Private worker only; original Python bytes, sentinel imports, full cleanup."""
    require(sys.flags.isolated, 'Reference loader requires isolated Python subprocess')
    source = Path(source).resolve()
    verify_source(source)
    require(not any(k == 'reversi' or k.startswith('reversi.') for k in sys.modules), 'Reference namespace already loaded')
    forbidden = ('pyximport', 'Cython', 'tkinter')
    require(not any(k.split('.')[0] in forbidden for k in sys.modules), 'Forbidden dependency already loaded')
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    touched = []

    def reject(name):
        touched.append(name)
        raise RuntimeError('Unexpected reference dependency access: ' + name)

    try:
        package = types.ModuleType('reversi')
        package.__path__ = []
        sys.modules['reversi'] = package
        for leaf in ('cy', 'BitBoardMethods'):
            module = types.ModuleType('reversi.' + leaf)
            module.__path__ = []
            module.__getattr__ = lambda name, leaf=leaf: reject(leaf + '.' + name)
            if leaf == 'cy':
                module.IMPORTED = False
            sys.modules[module.__name__] = module
            setattr(package, leaf, module)
        for leaf in ('color', 'disc', 'board'):
            name = 'reversi.' + leaf
            spec = importlib.util.spec_from_file_location(name, source / ('reversi/' + leaf + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            setattr(package, leaf, module)
            spec.loader.exec_module(module)
        board_class = package.board.PyListBoard
        require(board_class.__module__ == 'reversi.board' and
                Path(board_class.__init__.__code__.co_filename).resolve() == source / 'reversi/board.py', 'Wrong reference implementation')
        yield board_class
        require(not touched, 'Sentinel was accessed')
        require(not any(k.split('.')[0] in forbidden or k.startswith('reversi.cy.') for k in sys.modules), 'Forbidden dependency imported')
    finally:
        for name in list(sys.modules):
            if name == 'reversi' or name.startswith('reversi.'):
                del sys.modules[name]
        sys.dont_write_bytecode = old_bytecode


@dataclass(frozen=True)
class ReferenceState:
    board: tuple
    player: int = 1


class Reference:
    def __init__(self, board_class, size):
        require(type(size) is int and size in (4, 6), 'Audit supports sizes4/6 only')
        self.board_class, self.size = board_class, size

    def validate(self, state):
        require(type(state.player) is int and state.player in (-1, 1), 'Invalid player')
        require(isinstance(state.board, tuple) and len(state.board) == self.size**2 and
                all(type(x) is int and x in (-1, 0, 1) for x in state.board), 'Invalid board')

    def original(self, state):
        self.validate(state)
        masks = [sum(1 << (self.size**2 - 1 - i) for i, x in enumerate(state.board) if x == color) for color in (1, -1)]
        board = self.board_class(size=self.size, hole=0, ini_black=masks[0], ini_white=masks[1])
        require(self.export(board) == state.board, 'Original bitmask roundtrip mismatch')
        self.counts_original(board)
        return board

    @staticmethod
    def export(board):
        return tuple(v for row in board.get_board_info() for v in row)

    @staticmethod
    def counts_original(board):
        values = Reference.export(board)
        counts = (values.count(1), values.count(-1))
        require(counts == (board._black_score, board._white_score), 'Upstream disc-count inconsistency')
        return counts

    def initial(self):
        return ReferenceState(self.export(self.board_class(size=self.size)))

    def inspect(self, state):
        board = self.original(state)
        legal = {p: tuple(sorted(y*8+x for x, y in board.get_legal_moves('black' if p == 1 else 'white'))) for p in (1, -1)}
        counts = self.counts_original(board)
        terminal = None if legal[1] or legal[-1] else (counts[0] > counts[1]) - (counts[0] < counts[1])
        actions = () if terminal is not None else legal[state.player] or (64,)
        return actions, terminal, counts

    def transition(self, state, action):
        require(type(action) is int, 'Action must be integer')
        actions, _, _ = self.inspect(state)
        require(action in actions, 'Illegal reference action')
        if action == 64:
            return ReferenceState(state.board, -state.player), ()
        y, x = divmod(action, 8)
        require(0 <= y < self.size and 0 <= x < self.size, 'Padded action')
        board = self.original(state)  # Every branch starts from a fresh original board.
        color = 'black' if state.player == 1 else 'white'
        require((x, y) in board.get_legal_moves(color), 'Placement must be upstream-legal')
        flips = tuple(sorted(yy*self.size+xx for xx, yy in board.get_flippable_discs(color, x, y)))
        require(bool(flips), 'Legal placement has no flips')
        bits = board.put_disc(color, x, y)
        require(bits == sum(1 << (self.size**2-1-i) for i in flips), 'Upstream returned flip-mask mismatch')
        self.counts_original(board)
        return ReferenceState(self.export(board), -state.player), flips


def fixtures(reference):
    n = reference.size
    corner = [0]*(n*n)
    for y, x in ((0, 1), (1, 0), (1, 1)):
        corner[y*n+x] = -1
    for y, x in ((0, 2), (2, 0), (2, 2)):
        corner[y*n+x] = 1
    empty_terminal = [1]*(n*n); empty_terminal[0] = 0
    forced = [1]*(n*n); forced[1] = -1; forced[2] = 0
    rows = [('initial', reference.initial()), ('corner', ReferenceState(tuple(corner))),
            ('full_black', ReferenceState((1,)*(n*n))), ('full_white', ReferenceState((-1,)*(n*n))),
            ('full_draw', ReferenceState((1,)*(n*n//2)+(-1,)*(n*n//2))),
            ('terminal_empty', ReferenceState(tuple(empty_terminal))), ('forced_pass', ReferenceState(tuple(forced), -1))]
    return rows + [(name+'_role_swap', ReferenceState(tuple(-x for x in state.board), -state.player)) for name, state in rows]


class Disagreement(ValueError):
    def __init__(self, check, state, expected, actual):
        self.detail = {'check': check, 'state': {'board': state.board, 'player': state.player}, 'reference': expected, 'project': actual}
        super().__init__(check)


def compare_state(reference, game, state, counters, guard):
    # Implementation under test only. No other project package may be imported.
    from two_player.games import State
    counters['visited_states'] += 1
    for player in (1, -1):
        guard()
        refstate = ReferenceState(state.board, player)
        project = State(state.board, player)
        actions, terminal, counts = reference.inspect(refstate)

        def same(check, expected, actual):
            counters['comparisons'] += 1
            if expected != actual:
                raise Disagreement(check, refstate, expected, actual)

        counters['player_states'] += 1
        same('legal_actions', actions, game.legal_actions(project))
        same('terminal_absolute', terminal, game.terminal(project))
        same('disc_counts', counts, (project.board.count(1), project.board.count(-1)))
        if terminal is not None:
            counters['terminal_player_states'] += 1
            counters['terminal_empty_player_states'] += int(0 in state.board)
        for action in actions:
            guard()
            successor, flips = reference.transition(refstate, action)
            predicted = game.transition(project, action)
            same('successor_board', successor.board, predicted.board)
            same('successor_player', successor.player, predicted.player)
            same('flips', flips, tuple(sorted(game.flips(project, action))) if action != 64 else ())
            same('successor_counts', reference.inspect(successor)[2], (predicted.board.count(1), predicted.board.count(-1)))
            counters['legal_branches'] += 1
            counters['pass_branches'] += int(action == 64)
            counters['placement_branches'] += int(action != 64)
            counters['corner_capture_branches'] += int(action in (0, reference.size-1, 8*(reference.size-1), 9*(reference.size-1)))


def counters():
    return dict.fromkeys(('visited_states', 'player_states', 'comparisons', 'terminal_player_states',
                         'terminal_empty_player_states', 'legal_branches', 'pass_branches',
                         'placement_branches', 'corner_capture_branches', 'invalid_action_rejections'), 0)


def reject_invalid(reference, state, counts):
    legal, _, _ = reference.inspect(state)
    invalid = {-1, 65, reference.size, 8*reference.size}
    invalid.update(y*8+x for y in range(reference.size) for x in range(reference.size) if y*8+x not in legal)
    if 64 not in legal:
        invalid.add(64)
    for action in sorted(invalid):
        try:
            reference.transition(state, action)
        except ValueError:
            counts['invalid_action_rejections'] += 1
        else:
            raise ValueError('Wrapper accepted invalid action')


def smoke(source):
    with reference_namespace(source) as board_class:
        result = {}
        for size in (4, 6):
            reference = Reference(board_class, size)
            rows = dict(fixtures(reference))
            require(reference.inspect(rows['forced_pass'])[0] == (64,), 'Forced pass fixture failed')
            require(reference.inspect(rows['terminal_empty'])[1] == 1, 'Empty terminal fixture failed')
            require(reference.transition(rows['corner'], 0)[1] == (1, size, size+1), 'Corner fixture failed')
            counts = counters()
            for state in (rows['initial'], rows['forced_pass'], rows['terminal_empty']):
                reject_invalid(reference, state, counts)
            result[str(size)] = {'initial_actions': reference.inspect(rows['initial'])[0], 'invalid_rejections': counts['invalid_action_rejections']}
        return {'status': 'smoke_only', 'sizes': result, 'trajectory_audit_executed': False}


def provenance(source):
    manifest = verify_source(source)
    return {'source': manifest, 'source_manifest_sha256': sha((Path(source)/'manifest.json').read_bytes()),
            'wrapper_sha256': sha(Path(__file__).read_bytes()), 'project_rules_sha256': sha((ROOT/'two_player/games.py').read_bytes()),
            'protocol_sha256': sha((ROOT/'docs/THIRD_PARTY_RULES_REFERENCE_PLAN.md').read_bytes()),
            'python': sys.version, 'loader': 'original PyListBoard; synthetic cy(IMPORTED=False)/BitBoardMethods import sentinels; no package init',
            'pass_terminal': 'wrapper orchestration from upstream both-color legal sets and original disc counts'}


def audit_worker(source, output, deadline):
    import numpy as np
    sys.path.insert(0, str(ROOT))
    from two_player.games import BoardGame
    output = Path(output)
    receipt = {'version': VERSION, 'status': 'failed', 'provenance': provenance(source), 'numpy': np.__version__,
               'seed_protocol': 'SeedSequence([2601,size,trajectory]); sizes4,6; trajectories0..99; sorted reference action order',
               'trajectories_per_size': 100, 'max_plies': 100, 'limit_seconds': LIMIT_SECONDS, 'limit_output_bytes': LIMIT_BYTES,
               'sizes': {}, 'scope': 'rules compatibility on tested states; no oracle-label validation or strength evidence'}
    started = time.monotonic()

    def guard():
        require(time.monotonic() < deadline, 'Audit time cap exceeded')
        require(sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) < LIMIT_BYTES, 'Audit output cap exceeded')

    try:
        with reference_namespace(source) as board_class:
            for size in (4, 6):
                reference = Reference(board_class, size)
                game = BoardGame('reference-reversi'+str(size), size, size, k=0, reversi=True)
                result = {'fixtures': counters(), 'fixture_names': [name for name, _ in fixtures(reference)],
                          'trajectories': counters(), 'completed_trajectories': 0, 'trajectory_receipts': []}
                receipt['sizes'][str(size)] = result
                require(reference.initial().board == game.initial().board and reference.initial().player == game.initial().player,
                        'Initial project/reference state mismatch')
                for name, state in fixtures(reference):
                    receipt['active_case'] = {'size': size, 'fixture': name}
                    compare_state(reference, game, state, result['fixtures'], guard)
                    reject_invalid(reference, state, result['fixtures'])
                for trajectory in range(100):
                    rng = np.random.default_rng(np.random.SeedSequence([2601, size, trajectory]))
                    state = reference.initial()
                    transcript = hashlib.sha256()
                    for ply in range(101):
                        receipt['active_case'] = {'size': size, 'trajectory': trajectory, 'ply': ply}
                        compare_state(reference, game, state, result['trajectories'], guard)
                        actions, terminal, _ = reference.inspect(state)
                        transcript.update(json.dumps([state.board, state.player], separators=(',', ':')).encode())
                        if terminal is not None:
                            result['trajectory_receipts'].append({'trajectory': trajectory, 'plies': ply, 'terminal': terminal, 'sha256': transcript.hexdigest()})
                            result['completed_trajectories'] += 1
                            break
                        require(ply < 100, 'Trajectory ply cap exceeded')
                        action = actions[int(rng.integers(len(actions)))]
                        transcript.update(str(action).encode()+b'\n')
                        state, _ = reference.transition(state, action)
                for key in ('pass_branches', 'terminal_empty_player_states', 'corner_capture_branches'):
                    require(result['fixtures'][key] + result['trajectories'][key] > 0, 'Required coverage absent: '+key)
                require(result['completed_trajectories'] == 100, 'Incomplete trajectory inventory')
            guard()
        receipt.pop('active_case', None)
        receipt['status'] = 'passed'
    except Exception as error:
        receipt['error'] = {'type': type(error).__name__, 'message': str(error), 'detail': getattr(error, 'detail', None)}
    receipt['worker_seconds'] = time.monotonic()-started
    receipt['elapsed_seconds'] = LIMIT_SECONDS-(deadline-time.monotonic())
    if receipt['elapsed_seconds'] >= LIMIT_SECONDS:
        receipt['status'] = 'failed'
        receipt['budget_failure'] = 'Audit time cap exceeded'
    write_new(output/'receipt.json', receipt)
    return 0 if receipt['status'] == 'passed' else 1


def isolated(source, output=None):
    verify_source(source)
    started = time.monotonic()
    mode = '_smoke' if output is None else '_audit'
    command = [sys.executable, '-I', '-B', str(Path(__file__).resolve()), mode, str(Path(source).resolve())]
    if output is not None:
        output = Path(output).resolve()
        output.mkdir(parents=True, exist_ok=False)
        command += [str(output), str(started+LIMIT_SECONDS)]
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    try:
        result = subprocess.run(command, env=env, timeout=LIMIT_SECONDS, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        if output is not None and not (output/'receipt.json').exists():
            write_new(output/'receipt.json', {'version': VERSION, 'status': 'failed', 'error': 'Parent watchdog timeout', 'elapsed_seconds': time.monotonic()-started, 'provenance': provenance(source)})
        if output is not None:
            write_new(output/'run.json', {'version': VERSION, 'status': 'failed', 'error': 'Parent watchdog timeout',
                                         'elapsed_seconds': time.monotonic()-started,
                                         'receipt_sha256': sha((output/'receipt.json').read_bytes())})
        raise
    if output is not None and not (output/'receipt.json').exists():
        write_new(output/'receipt.json', {'version': VERSION, 'status': 'failed', 'error': 'Worker exited without receipt', 'returncode': result.returncode, 'stderr': result.stderr[-8000:], 'provenance': provenance(source)})
    if output is not None:
        worker = json.loads((output/'receipt.json').read_text(encoding='utf-8'))
        elapsed = time.monotonic()-started
        passed = result.returncode == 0 and worker['status'] == 'passed' and elapsed < LIMIT_SECONDS
        write_new(output/'run.json', {'version': VERSION, 'status': 'passed' if passed else 'failed',
                                     'elapsed_seconds': elapsed, 'returncode': result.returncode,
                                     'receipt_sha256': sha((output/'receipt.json').read_bytes()),
                                     'acceptance': 'Both run.json and hash-bound receipt.json must pass'})
        if not passed and result.returncode == 0:
            result.returncode = 1
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('acquire', 'smoke', 'audit', '_smoke', '_audit'))
    parser.add_argument('source', type=Path)
    parser.add_argument('output', nargs='?', type=Path)
    parser.add_argument('deadline', nargs='?', type=float)
    args = parser.parse_args()
    if args.mode == 'acquire':
        print(json.dumps(acquire(args.source), indent=2))
    elif args.mode == '_smoke':
        print(json.dumps(smoke(args.source), sort_keys=True))
    elif args.mode == '_audit':
        require(args.output is not None and args.deadline is not None and sys.flags.isolated, 'Internal audit worker contract')
        return audit_worker(args.source, args.output, args.deadline)
    else:
        require(args.mode != 'audit' or args.output is not None, 'Audit requires fresh output directory')
        result = isolated(args.source, args.output if args.mode == 'audit' else None)
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        return result.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
