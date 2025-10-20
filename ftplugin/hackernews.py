# -*- coding: utf-8 -*-

#  vim-hackernews
#  --------------
#  Browse Hacker News (news.ycombinator.com) inside Vim.
#
#  Author:  ryanss <ryanssdev@icloud.com>
#  Website: https://github.com/ryanss/vim-hackernews
#  License: MIT (see LICENSE file)
#  Version: 0.3-dev


from __future__ import print_function
import binascii
import json
import re
import textwrap
import time
import vim
import webbrowser
import warnings
import sys
if sys.version_info >= (3, 0):
    from html.parser import HTMLParser
    from urllib.request import urlopen
    from urllib.error import HTTPError
    unicode = bytes
    unichr = chr
else:
    from HTMLParser import HTMLParser
    from urllib2 import urlopen, HTTPError


# Official API (Firebase)
OFFICIAL_API_URL = "https://hacker-news.firebaseio.com/v0"
MARKDOWN_URL = "http://fuckyeahmarkdown.com/go/?read=1&u="

html = HTMLParser()
warnings.filterwarnings('ignore', category=SyntaxWarning)


def bwrite(s):
    b = vim.current.buffer
    # Never write more than two blank lines in a row
    if not s.strip() and not b[-1].strip() and not b[-2].strip():
        return

    # Vim buffer.append() cannot accept unicode type,
    # must first encode to UTF-8 string
    if isinstance(s, unicode):
        s = s.encode('utf-8', errors='replace')

    # Code block markers for syntax highlighting
    cb = unichr(160)
    if isinstance(cb, unicode):
        cb = cb.encode('utf-8')
    if s == cb and not b[-1]:
        b[-1] = s
        return

    if not b[0]:
        b[0] = s
    else:
        b.append(s)


def hex(s):
    if sys.version_info >= (3, 0):
        return str(binascii.hexlify(bytes(vim.current.buffer[0], 'utf-8')))
    return binascii.hexlify(s)


def main():
    stories = vim.eval("g:hackernews_stories") or "news"
    vim.command("edit %s.hackernews" % (stories if stories != "news" else ""))
    vim.command("setlocal noswapfile")
    vim.command("setlocal buftype=nofile")

    if vim.eval("changenr()") == "1":
        vim.command("setlocal undolevels=-1")

    bwrite("┌───┐")
    bwrite("│ Y │ Hacker News (news.ycombinator.com)")
    bwrite("└───┘")
    bwrite("")

    # Always use the official API
    _progress('Loading stories (Official API) ...')
    try:
        items = fetch_official_items(stories)
    except Exception:
        e = sys.exc_info()[1]
        msg = getattr(e, 'reason', None)
        if msg:
            print("HackerNews.vim Error: %s" % str(msg))
        else:
            print("HackerNews.vim Error: HTTP Request Timeout")
        return

    _notify_api_used(True)
    _progress('Loaded %d stories' % len(items))

    for i, item in enumerate(items):
        if 'title' not in item:
            continue
        if 'domain' in item:
            line = "%s%d. %s (%s) [%s]%s"
            line %= (" " if i+1 < 10 else "", i+1, item['title'],
                     item['domain'], item['url'], unichr(160))
            bwrite(line)
        else:
            line = "%s%d. %s [%d]"
            line %= (" " if i+1 < 10 else "", i+1, item['title'], item['id'])
            bwrite(line)
        if item['type'] in ("link", "ask"):
            line = "%s%d points by %s %s | %d comments [%s]"
            line %= (" "*4, item['points'], item['user'], item['time_ago'],
                     item['comments_count'], str(item['id']))
            bwrite(line)
        elif item['type'] == "job":
            line = "%s%s [%d]"
            line %= (" "*4, item['time_ago'], item['id'])
            bwrite(line)
        bwrite("")
    vim.command("setlocal undolevels=100")


def link(external=False):
    line = vim.current.line

    item_id = None
    url = None

    # Search for Hacker News [item id]
    m = re.search(r"\[([0-9]{3,})\]$", line)
    if m:
        item_id = m.group(1)

    else:
        # Search for [http] link
        b = vim.current.buffer
        y, x = vim.current.window.cursor
        y -= 1
        while b[y].find("[http") < 0 and y >= 0:
            # The line we were on had no part of a link in it
            if b[y-1].find("]") > 0 \
                    and b[y-1].find("]") > b[y-1].find("[http"):
                return
            y -= 1
        start = y
        loc = max(b[y].find("[http", x, b[y].find("]", x)),
                  b[y].rfind("[http", 0, x))
        if loc >= 0:
            if b[y].find("]", loc) >= 0:
                a = loc + 1
                e = b[y].find("]", loc)
                url = b[y][a:e]
            else:
                url = b[y][loc:]
                y += 1
                while b[y].find("]") < 0:
                    if y != start:
                        url += b[y]
                    y += 1
                if y != start:
                    url += b[y][:b[y].find("]")]
                url = url.replace(" ", "").replace("\n", "")

    if url and url.find("news.ycombinator.com/item?id=") > 0:
        item_id = url[url.find("item?id=")+8:]

    if item_id:
        if external:
            browser = webbrowser.get()
            browser.open("https://news.ycombinator.com/item?id="+item_id)
            return
        try:
            _progress('Loading item %s (Official API) ...' % item_id)
            item = fetch_official_item(item_id)
        except Exception:
            print("HackerNews.vim Error: HTTP Request Timeout")
            return
        _notify_api_used(True)
        _progress('Loaded item %s' % item_id)
        save_pos()
        vim.command("set syntax=hackernews")
        del vim.current.buffer[:]
        if 'title' in item:
            if 'domain' in item:
                bwrite("%s (%s)" % (item['title'], item['domain']))
            else:
                bwrite(item['title'])
            if item.get('comments_count', None) is not None \
                    and item['type'] != "job":
                bwrite("%d points by %s %s | %d comments"
                       % (item['points'], item['user'], item['time_ago'],
                          item['comments_count']))
            else:
                bwrite(item['time_ago'])
            if 'url' in item and item['url'].find(item_id) < 0:
                bwrite("[%s]" % item['url'])
            else:
                bwrite("[http://news.ycombinator.com/item?id=%s]" % item_id)
            if 'content' in item:
                bwrite("")
                print_comments([dict(content=item['content'])])
            if 'poll' in item:
                bwrite("")
                max_score = max((c['points'] for c in item['poll']))
                for c in item['poll']:
                    bwrite("%s (%d points)"
                           % (html.unescape(c['item']), c['points']))
                    bar = int(80.0 * c['points'] / max_score)
                    bwrite("#"*bar)
                    bwrite("")
            bwrite("")
            bwrite("")
        if item['type'] == "comment":
            item['level'] = 0
            print_comments([item])
        else:
            print_comments(item['comments'])
        # Prevent syntax issues in long comment threads with code blocks
        vim.command("syntax sync fromstart")
        # Highlight OP username in comment titles
        if 'level' not in item:
            vim.command("syntax clear Question")
        vim.command("syntax match Question /%s/ contained" % item['user'])

    elif url:
        if external:
            browser = webbrowser.get()
            browser.open(url)
            return
        try:
            content = urlopen(MARKDOWN_URL+url, timeout=8)
            content = content.read().decode('utf-8')
        except HTTPError:
            print("HackerNews.vim Error: %s" % str(sys.exc_info()[1][0]))
            return
        except:
            print("HackerNews.vim Error: HTTP Request Timeout")
            return
        # Wrap plain URLs as [http...] to match buffer link detection
        content = re.sub(r"(http\S+?)([<>\s\n])", r"[\g<1>]\g<2>", content)
        save_pos()
        vim.command("set syntax=markdown")
        del vim.current.buffer[:]
        for i, line in enumerate(content.split('\n')):
            if not line:
                bwrite("")
                continue
            line = textwrap.wrap(line, width=80)
            for j, wrap in enumerate(line):
                bwrite(wrap)


def save_pos():
    marks = vim.eval("g:hackernews_marks")
    m = hex(vim.current.buffer[0])
    marks[m] = list(vim.current.window.cursor)
    marks[m].append(vim.eval("&syntax"))
    vim.command("let g:hackernews_marks = %s" % str(marks))


def recall_pos():
    marks = vim.eval("g:hackernews_marks")
    m = hex(vim.current.buffer[0])
    if m in marks:
        mark = marks[m]
        vim.current.window.cursor = (int(mark[0]), int(mark[1]))
        vim.command("set syntax=%s" % mark[2])


def print_comments(comments, level=0):
    for comment in comments:
        if 'level' in comment:
            # This is a comment (not content) so add comment header
            bwrite("%sComment by %s %s: [%s]"
                   % (" "*level*4, comment.get('user', '???'),
                      comment['time_ago'], comment['id']))
        if not comment.get('content', False):
            bwrite("")
            bwrite("")
            continue
        for p in comment['content'].split("<p>"):
            if not p:
                continue
            p = html.unescape(p)
            p = p.replace("<i>", "_").replace("</i>", "_")

            # Extract code block before textwrap to conserve whitespace
            code = None
            if p.find("<code>") >= 0:
                m = re.search("<pre><code>([\S\s]*?)</code></pre>", p)
                code = m.group(1)
                p = p.replace(m.group(0), "!CODE!")

            # Convert <a href="http://url/">Text</a> tags
            # to markdown equivalent: (Text)[http://url/]
            s = p.find("a>")
            while s > 0:
                s += 2
                section = p[:s]
                m = re.search(r"<a.*href=[\"\']([^\"\']*)[\"\'].*>(.*)</a>",
                              section)
                if m:
                    # Do not bother with anchor text if it is same as href url
                    if m.group(1)[:20] == m.group(2)[:20]:
                        p = p.replace(m.group(0), "[%s]" % m.group(1))
                    else:
                        p = p.replace(m.group(0),
                                      "(%s)[%s]" % (m.group(2), m.group(1)))
                    s = p.find("a>")
                else:
                    s = p.find("a>", s)

            contents = textwrap.wrap(p, width=80,
                                     initial_indent=" "*4*level,
                                     subsequent_indent=" "*4*level)
            for line in contents:
                if line.find("!CODE!") >= 0:
                    bwrite(unichr(160))
                    for c in code.split("\n"):
                        if c.strip():
                            bwrite(" "*4*level + c)
                    bwrite(unichr(160))
                    line = " "*4*level + line.replace("!CODE!", "").strip()
                if line.strip():
                    bwrite(line)
            if contents and line.strip():
                bwrite("")
        bwrite("")
        if 'comments' in comment:
            print_comments(comment['comments'], level+1)


# -------------------------
# Official API
# -------------------------

def _notify_api_used(official=True):
    try:
        # Always official now; keep param for compatibility
        msg = 'HackerNews: using Official API'
        # Use echomsg so it lands in :messages; avoid breaking redraws
        vim.command("silent! echomsg '%s'" % msg.replace("'", "''"))
    except Exception:
        pass

def _progress(msg):
    try:
        if str(vim.eval("get(g:, 'hackernews_show_progress', 1)")) == '0':
            return
        msg = 'HackerNews: ' + msg
        vim.command("echo '%s'" % msg.replace("'", "''"))
        vim.command("redraw")
    except Exception:
        pass


# Override print_comments to avoid regex escape warnings and keep behavior.
def print_comments(comments, level=0):
    for comment in comments:
        if 'level' in comment:
            bwrite("%sComment by %s %s: [%s]"
                   % (" "*level*4, comment.get('user', '???'),
                      comment['time_ago'], comment['id']))
        if not comment.get('content', False):
            bwrite("")
            bwrite("")
            continue
        for p in comment['content'].split("<p>"):
            if not p:
                continue
            p = html.unescape(p)
            p = p.replace("<i>", "_").replace("</i>", "_")

            code = None
            if p.find("<code>") >= 0:
                m = re.search(r"<pre><code>([\S\s]*?)</code></pre>", p)
                if m:
                    code = m.group(1)
                    p = p.replace(m.group(0), "!CODE!")

            s = p.find("a>")
            while s > 0:
                s += 2
                section = p[:s]
                m = re.search(r"<a.*href=[\"\']([^\"\']*)[\"\'].*>(.*)</a>",
                              section)
                if m:
                    if m.group(1)[:20] == m.group(2)[:20]:
                        p = p.replace(m.group(0), "[%s]" % m.group(1))
                    else:
                        p = p.replace(m.group(0),
                                      "(%s)[%s]" % (m.group(2), m.group(1)))
                    s = p.find("a>")
                else:
                    s = p.find("a>", s)

            contents = textwrap.wrap(p, width=80,
                                     initial_indent=" "*4*level,
                                     subsequent_indent=" "*4*level)
            for line in contents:
                if line.find("!CODE!") >= 0 and code is not None:
                    bwrite(unichr(160))
                    for c in code.split("\n"):
                        if c.strip():
                            bwrite(" "*4*level + c)
                    bwrite(unichr(160))
                    line = " "*4*level + line.replace("!CODE!", "").strip()
                if line.strip():
                    bwrite(line)
            if contents and line.strip():
                bwrite("")
        bwrite("")
        if 'comments' in comment:
            print_comments(comment['comments'], level+1)

def _official_fetch_json(path, timeout=8):
    return json.loads(urlopen(OFFICIAL_API_URL + path, timeout=timeout)
                      .read().decode('utf-8'))


def _time_ago(ts):
    try:
        diff = int(time.time() - int(ts))
    except Exception:
        return "just now"
    units = [
        (365*24*3600, "year"),
        (30*24*3600, "month"),
        (7*24*3600, "week"),
        (24*3600, "day"),
        (3600, "hour"),
        (60, "minute"),
    ]
    for seconds, name in units:
        if diff >= seconds:
            val = int(diff / seconds)
            return "%d %s%s ago" % (val, name, "s" if val != 1 else "")
    return "%d seconds ago" % max(diff, 0)


def _domain(url):
    try:
        if sys.version_info >= (3, 0):
            from urllib.parse import urlparse
        else:
            from urlparse import urlparse
        host = urlparse(url).netloc or ""
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return None


def _normalize_story(item):
    """Normalize an official API item to the shape expected by the plugin."""
    if not item or item.get('deleted') or item.get('dead'):
        return None
    typ = item.get('type')
    story = {
        'id': item.get('id'),
        'title': item.get('title', ''),
        'user': item.get('by', '???'),
        'time_ago': _time_ago(item.get('time', time.time())),
        'points': item.get('score', 0),
        'comments_count': item.get('descendants', 0),
    }
    url = item.get('url')
    if url:
        story['url'] = url
        d = _domain(url)
        if d:
            story['domain'] = d
    # Map types to plugin expectations
    if typ == 'job':
        story['type'] = 'job'
    elif typ == 'poll':
        story['type'] = 'ask'
    else:
        story['type'] = 'link' if url else 'ask'
    return story


def fetch_official_items(kind):
    mapping = {
        'news': 'topstories',
        'newest': 'newstories',
        'best': 'beststories',
        'show': 'showstories',
        'ask': 'askstories',
        'jobs': 'jobstories',
    }
    feed = mapping.get(kind, 'topstories')
    _progress('Official: fetching %s ids ...' % feed)
    ids = _official_fetch_json('/%s.json' % feed, timeout=8) or []
    # Limit to avoid long delays; news/news2 pages typically list ~60 stories
    limit = 60 if kind in ('news', 'newest', 'best') else 30
    out = []
    total = min(len(ids), limit)
    if total:
        _progress('Official: fetching %d items ...' % total)
    for iid in ids[:limit]:
        try:
            itm = _official_fetch_json('/item/%d.json' % int(iid), timeout=8)
        except Exception:
            continue
        norm = _normalize_story(itm)
        if norm:
            out.append(norm)
        if total and len(out) % 10 == 0:
            _progress('Official: fetched %d/%d items ...' % (len(out), total))
    return out


def _build_comments(ids, depth=0, depth_limit=6, node_budget=None):
    # node_budget is [count, max] mutable to track across recursion
    if node_budget is None:
        node_budget = [0, 200]
    comments = []
    if not ids:
        return comments
    if depth > depth_limit:
        return comments
    if depth == 0:
        _progress('Official: fetching comments ...')
    for cid in ids:
        if node_budget[0] >= node_budget[1]:
            break
        try:
            c = _official_fetch_json('/item/%d.json' % int(cid), timeout=8)
        except Exception:
            continue
        if not c or c.get('deleted') or c.get('dead'):
            continue
        node_budget[0] += 1
        comment = {
            'id': c.get('id'),
            'user': c.get('by', '???'),
            'time_ago': _time_ago(c.get('time', time.time())),
            'content': c.get('text', '') or '',
        }
        kids = c.get('kids') or []
        if kids:
            comment['comments'] = _build_comments(
                kids, depth+1, depth_limit, node_budget
            )
        comments.append(comment)
        if depth == 0 and node_budget[0] % 20 == 0:
            _progress('Official: fetched %d comments ...' % node_budget[0])
    return comments


def fetch_official_item(item_id):
    try:
        iid = int(item_id)
    except Exception:
        iid = item_id
    item = _official_fetch_json('/item/%d.json' % int(iid), timeout=8)
    if not item:
        return {}
    # If this is a comment, normalize minimal fields for print_comments
    if item.get('type') == 'comment':
        return {
            'type': 'comment',
            'id': item.get('id'),
            'user': item.get('by', '???'),
            'time_ago': _time_ago(item.get('time', time.time())),
            'content': item.get('text', '') or '',
        }

    norm = _normalize_story(item) or {}
    # Build poll options if any
    parts = item.get('parts') or []
    if parts:
        poll = []
        for pid in parts:
            try:
                po = _official_fetch_json('/item/%d.json' % int(pid),
                                          timeout=8)
            except Exception:
                continue
            if not po:
                continue
            poll.append({'item': po.get('text', '') or '',
                         'points': po.get('score', 0)})
        if poll:
            norm['poll'] = poll
    # Build comments tree
    kids = item.get('kids') or []
    norm['comments'] = _build_comments(kids)
    return norm
