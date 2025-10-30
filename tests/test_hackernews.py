import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


class FakeBuffer(list):
    def __init__(self, initial=None):
        super().__init__(initial if initial is not None else [''])

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return list.__getitem__(self, idx)
        if -len(self) <= idx < len(self):
            return list.__getitem__(self, idx)
        return ''

    def __setitem__(self, idx, value):
        if isinstance(idx, slice):
            list.__setitem__(self, idx, value)
            return
        if idx >= len(self):
            self.extend([''] * (idx - len(self) + 1))
        list.__setitem__(self, idx, value)


class VimState:
    def __init__(self):
        self.buffer = FakeBuffer(['stale line'])
        self.window = SimpleNamespace(cursor=(1, 0))
        self.line = ''
        self.commands = []
        self.eval_map = {
            "get(g:, 'hackernews_show_progress', 1)": '0',
            "g:hackernews_stories": 'news',
            "changenr()": '2',
            "&syntax": 'hackernews',
        }

    def to_module(self):
        module = ModuleType('vim')
        module.current = SimpleNamespace(
            buffer=self.buffer,
            window=self.window,
            line=self.line,
        )
        module.command = self.command
        module.eval = self.eval
        module.Function = lambda name: lambda *args, **kwargs: None
        return module

    def command(self, cmd):
        self.commands.append(cmd)

    def eval(self, expr):
        return self.eval_map.get(expr, "0")

    def reset(self, lines=None):
        self.buffer[:] = lines if lines is not None else ['stale line']
        self.window.cursor = (1, 0)
        self.commands.clear()


@pytest.fixture
def hackernews_module():
    root = Path(__file__).resolve().parents[1]
    ftplugin_dir = root / 'ftplugin'
    sys.path.insert(0, str(ftplugin_dir))
    state = VimState()
    vim_mod = state.to_module()
    sys.modules['vim'] = vim_mod
    sys.modules.pop('hackernews', None)
    import hackernews
    importlib.reload(hackernews)
    try:
        yield state, hackernews
    finally:
        sys.modules.pop('hackernews', None)
        sys.modules.pop('vim', None)
        try:
            sys.path.remove(str(ftplugin_dir))
        except ValueError:
            pass


def sample_items():
    return [
        {
            'id': 1,
            'title': 'Story One',
            'domain': 'example.com',
            'url': 'https://example.com/story',
            'type': 'link',
            'points': 42,
            'user': 'alice',
            'time_ago': '1 hour ago',
            'comments_count': 7,
        },
        {
            'id': 2,
            'title': 'Ask Something',
            'type': 'ask',
            'points': 3,
            'user': 'bob',
            'time_ago': 'just now',
            'comments_count': 0,
        },
    ]


def test_render_frontpage_replaces_buffer(hackernews_module):
    state, hackernews = hackernews_module
    state.reset(['old line'])
    hackernews._render_frontpage(sample_items())
    assert state.buffer[0] == '┌───┐'
    assert state.buffer[1] == '│ Y │ Hacker News (news.ycombinator.com)'
    assert state.buffer[2] == '└───┘'
    assert any('Story One' in line for line in state.buffer)
    assert 'setlocal filetype=hackernews' in state.commands


def test_load_frontpage_fetches_and_renders(monkeypatch, hackernews_module):
    state, hackernews = hackernews_module
    state.reset(['existing line'])
    monkeypatch.setattr(hackernews, 'fetch_official_items', lambda kind: sample_items())
    monkeypatch.setattr(hackernews, '_notify_api_used', lambda: None)
    monkeypatch.setattr(hackernews, '_progress', lambda msg: None)
    hackernews._load_frontpage('news', reuse_buffer=True)

    assert state.buffer[0] == '┌───┐'
    assert state.buffer[1] == '│ Y │ Hacker News (news.ycombinator.com)'
    assert state.buffer[2] == '└───┘'
    assert any('Story One' in line for line in state.buffer)
    assert 'setlocal undolevels=100' in state.commands
    assert not any(cmd.startswith('edit ') for cmd in state.commands)


def test_load_frontpage_failure_keeps_existing_lines(monkeypatch, hackernews_module):
    state, hackernews = hackernews_module
    state.reset(['keep me'])

    def boom(_kind):
        raise RuntimeError('boom')

    monkeypatch.setattr(hackernews, 'fetch_official_items', boom)
    monkeypatch.setattr(hackernews, '_notify_api_used', lambda: None)
    monkeypatch.setattr(hackernews, '_progress', lambda msg: None)
    hackernews._load_frontpage('news', reuse_buffer=True)

    assert state.buffer[0] == 'keep me'
    assert 'setlocal undolevels=100' in state.commands


def test_refresh_respects_current_story_setting(monkeypatch, hackernews_module):
    state, hackernews = hackernews_module
    captured = {}

    def fetch(kind):
        captured['kind'] = kind
        return sample_items()

    state.eval_map["g:hackernews_stories"] = 'best'
    monkeypatch.setattr(hackernews, 'fetch_official_items', fetch)
    monkeypatch.setattr(hackernews, '_notify_api_used', lambda: None)
    monkeypatch.setattr(hackernews, '_progress', lambda msg: None)
    hackernews.refresh()

    assert captured['kind'] == 'best'
    assert state.buffer[0] == '┌───┐'
    assert not any(cmd.startswith('edit ') for cmd in state.commands)
