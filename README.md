vim-hackernews [![Build Status](https://img.shields.io/travis/ryanss/vim-hackernews.svg)](https://travis-ci.org/ryanss/vim-hackernews) [![Version](https://img.shields.io/badge/version-0.3--dev-orange.svg)](https://github.com/ryanss/vim-hackernews/blob/master/CHANGES) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ryanss/vim-hackernews/raw/master/LICENSE)
==============

Browse [Hacker News](https://news.ycombinator.com) inside Vim.

![Hacker News Front Page in Vim](https://github.com/ryanss/vim-hackernews/raw/master/screenshots/vim-hackernews-home.png)

![Hacker News Comments in Vim](https://github.com/ryanss/vim-hackernews/raw/master/screenshots/vim-hackernews-item.png)

Uses the [official Hacker News Firebase API](https://github.com/HackerNews/API)
to retrieve stories, items, and comments, and
[FUCK YEAH MARKDOWN](http://fuckyeahmarkdown.com) for rendering HTML articles
as text.


Basic Usage
-----------

* Open the Hacker News front page in Vim by executing the `:HackerNews` command
* The HackerNews command takes an optional parameter to view other lists:
    * `:HackerNews ask`
    * `:HackerNews show`
    * `:HackerNews jobs`
    * `:HackerNews best`
    * `:HackerNews newest`
    * (default is the front page/top stories)
* Press lowercase `o` to open links in Vim
* Press uppercase `O` to open links in default web browser
* Numbered lines with story titles on the front page link to the story url
* Comment lines on the front page link to the comments url
* Press uppercase `F` to fold current comment thread
* Press lowercase `u` to go back
* Press `Ctrl+r` to go forward
* Execute the `:bd` command to close and remove the Hacker News buffer


Why the switch to the Official API?
-----------------------------------

We switched from a third-party API to the official Hacker News Firebase API to
improve reliability and reduce external dependencies.

- Reliability: avoids frequent outages/timeouts seen with the previous API.
- Accuracy: works directly with canonical HN items and comment trees.
- Transparency: public, well-documented endpoints maintained by HN.

Note: fetching deep comment trees can be slower because the official API
requires multiple requests. The plugin shows progress messages by default
(`g:hackernews_show_progress`) so you can see what’s happening.


Configuration
-------------

- `g:hackernews_show_progress` (default: 1)
  - Show short progress messages while fetching stories/items and building
    comment trees. Set to 0 to silence messages.

- `g:hackernews_max_items`
  - Max stories fetched per list. Defaults to ~60 for top/newest/best, ~30 for
    others.

- `g:hackernews_concurrency`
  - Number of parallel requests when fetching story details from the official
  API. Default 12.


Performance
-----------

This plugin uses the official API, which returns lists of story IDs. To keep
loads fast, vim-hackernews fetches story details in parallel:

- Threaded fetch: a small thread pool (default 12 threads) pulls items by ID.
  Python threads are appropriate here because HTTP I/O releases the GIL.
- Ordered output: results are reassembled in the original ID order.
- Batching feedback: progress messages are printed every 10 items.
- Tunable limits: `g:hackernews_max_items` controls how many stories are
  fetched per list; `g:hackernews_concurrency` controls the thread pool size.
- Comment trees: still fetched recursively, with sensible internal limits to
  avoid timeouts on very large threads; progress shown for top-level fetches.

Trade-offs:
- Higher concurrency improves latency on fast networks, but can trip rate caps
  or saturate slow links. If you see timeouts, lower `g:hackernews_concurrency`
  or `g:hackernews_max_items`.


Demo
----

We plan to include a short demo GIF showing progress messages while loading
stories and comments.

- Placeholder path for the GIF: `screenshots/demo-progress.gif`
- If you want to record one now, here are two common approaches:

  1) Asciinema + agg (SVG/GIF)
     - Install: `pip install asciinema svg-term-cli` and `npm i -g agg` (or use
       your package manager equivalents).
     - Record: `asciinema rec demo.cast --command "vim -Nu NONE -c 'set rtp+=.' -c 'let g:hackernews_show_progress=1' -c 'HackerNews'"`
     - Convert: `agg demo.cast screenshots/demo-progress.gif --theme solarized-dark --font-size 14 --width 120 --fps 15`

  2) GUI recorder (Peek, Kap, etc.)
     - Open a terminal at least 120x35 chars.
     - Run: `vim -Nu NONE -c 'set rtp+=.' -c 'let g:hackernews_show_progress=1' -c 'HackerNews'`
     - Start recording before running `:HackerNews` and stop once the list
       appears and progress messages complete.

Tip: Ensure `let g:hackernews_show_progress=1` so messages are visible.


Enhanced Motions
----------------

Uppercase `J` and `K` are mapped to helpful new motions based on what type of
content is on the screen:

* Move to next/prev item when viewing the front page. (If the cursor is on a
  numbered line with story title the cursor will move to the next/prev numbered
  line with story title. If the cursor is on a comment line it will move to the
  next/prev comment line.)
* Move to next/prev comment when viewing comments.
* Move to next/prev paragraph when viewing the text version of articles.


Installation
------------

##### Pathogen (https://github.com/tpope/vim-pathogen)
```bash
git clone https://github.com/ryanss/vim-hackernews ~/.vim/bundle/vim-hackernews
```

##### Vundle (https://github.com/gmarik/vundle)
```
Plugin 'ryanss/vim-hackernews'
```

##### NeoBundle (https://github.com/Shougo/neobundle.vim)
```
NeoBundle 'ryanss/vim-hackernews'
```


Running Tests
-------------

```bash
$ vim -c Vader! tests.vader
```


Contributions
-------------

[Issues](https://github.com/ryanss/vim-hackernews/issues) and
[Pull Requests](https://github.com/ryanss/vim-hackernews/pulls) are always
welcome!


License
-------

Code is available according to the MIT License
(see [LICENSE](https://github.com/ryanss/vim-hackernews/raw/master/LICENSE)).
