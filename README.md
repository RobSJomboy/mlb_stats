# Trade Snapshot

A live MLB stat lookup that puts a Talkin' Baseball lower third on screen. Browse all 30 teams,
open any player, pick a timeframe, and the stat line goes straight to OBS — plus a matching
1920×1080 PNG if you want it baked out.

Everything is one HTML file. No build step, no npm, no API key. Stats come from the public MLB
StatsAPI at page load, so the numbers are whatever the league is showing right now.

---

## Running it

**Just looking things up?** Double-click `index.html`. That's the whole install.

**Putting it on screen?** See the OBS section below. For the two-computer setup, the page needs to
be served from GitHub Pages rather than opened off disk — Settings → Pages → Branch `main` / root.

---

## What's in it

**Team directory** — all 30 clubs, grouped by league and division. Filter to one division with the
Division dropdown, or jump straight to a club with the Team dropdown.

**Roster view** — 40-man split into Active / Injured List / 40-Man Reserve. Click any column header
to sort; jersey numbers sort numerically, everything else alphabetically.

**Global search** — type a name and it filters every rostered player in the league instantly. No
network call, the index is loaded up front.

**Player card** — click a name. Six timeframes:

| Pill | What it pulls |
|---|---|
| Full Season | season totals |
| Last 7 / 14 / 30 Days | rolling date range ending today |
| Vs Lefties | vs LHP for a hitter, vs LHB for a pitcher |
| Vs Righties | vs RHP for a hitter, vs RHB for a pitcher |

Hitters get AVG/OBP/SLG/OPS plus HR, RBI, BB, K, SB, HBP and K%. Pitchers get IP/ERA/W-L plus WHIP,
K, BB, SV, ER, K%. Two-way players get both.

**Team stats** — from a team's roster, hit **■ Team Stats — Ranks & Splits**. Four categories, each
showing the club's season numbers *and* where they rank in all 30:

| Category | Stats |
|---|---|
| Team Batting | AVG, OBP, SLG, OPS, R, HR |
| Starting Pitching | ERA, WHIP, K, BAA, IP |
| Relief Pitching | ERA, WHIP, SV, K, BAA |
| Team Defense | FLD%, E, DP, CS% |

On the graphic, the category is the headline and the crest identifies the club, with each stat
carrying its rank underneath — `ERA / 3.47 / 3RD OF 30`. Ranks are computed here from all 30 clubs
rather than trusting a sort parameter to mean what we want, and the direction is per-category:
`strikeOuts` is good for a staff and bad for a lineup, and `avg` is the batting average in a hitting
split but the average *against* in a pitching one. Ties share a rank.

**Cycling** — both the player card and the team card have a **Cycle** checkbox and a seconds box
(default 7). On, the graphic rotates through every split or category; off, whatever you've selected
stays up indefinitely. Splits with no data are dropped rather than cycled as blank screens, so an
IL player cycles the three that exist instead of six with three empty.

The display does the rotating on a local timer — one publish drives a whole rotation. A 7-second
cycle isn't nine posts a minute at ntfy, and the pacing stays smooth regardless of network jitter.

**● DISPLAY LIVE / ■ OFF AIR** in the header is a master kill switch. Click it from anywhere to pull
the lower third without first digging back into whichever player or team is up. The card set stays
loaded, so clicking back to LIVE puts the same graphic straight back on screen.

**Season picker** goes back to 2014.

---

## Getting it into OBS

Two ways in, depending on how much setup you want.

### Option A — second window (nothing to install)

1. Click **Open Display ↗**. A second tab opens showing only the lower third on a transparent
   background.
2. In OBS add a **Window Capture** of that tab.
3. Leave it on a second monitor. Every player you click in the control tab swaps the bar live.

Works because both tabs are the same browser and talk over BroadcastChannel.

### Option B — Connect a topic (works across computers, no server)

Same as the Trade Deadline control. Both pages subscribe to a named topic on
[ntfy.sh](https://ntfy.sh), so the two machines don't have to be on the same network — or in the
same building. Nothing to install.

1. In **Connection**, take the suggested topic (or type your own) and hit **Connect**. The pill
   goes green.
2. Hit **Copy Display URL**.
3. On the OBS computer, paste that into a **Browser Source**, 1920×1080.

That's it. The topic is remembered, so next show you just open the page and it reconnects itself.

```
https://robsjomboy.github.io/mlb_stats/index.html?display=1&topic=tb-snapshot-2kb024
```

**This needs the page on a real host** — GitHub Pages. The OBS machine can't open a `file://` path
off your laptop, and the control page will warn you if you're running it that way.

Sync is SSE with a polling safety net and a reconnect watchdog, same belt-and-braces as the
Deadline display: some networks silently buffer streaming connections, and a plain poll isn't
subject to that. If OBS refreshes the Browser Source mid-show, the display replays the last few
minutes on load, so the current graphic comes straight back up instead of sitting blank.

**It doesn't depend on one host.** ntfy.sh went down mid-use once, so the control page publishes to
several public ntfy instances and the display subscribes to all of them — any one being up is
enough, and no reconfiguring happens mid-show. Receiving the same payload from three hosts is free:
the duplicate guard that exists for SSE-plus-poll covers it, and payload timestamps only move
forward so a slow mirror can't put a stale graphic back on screen. `?ntfy=https://host` pins one
host if you need to.

**Topics are public to anyone who knows the name.** That's why the suggested one has a random tail
— a guessable topic is a stranger's write access to your lower third. Don't shorten it to something
tidy like `talkinbaseball`.

### Option C — Local relay (no internet)

Only worth it if you can't rely on the internet, since the app needs it for stats anyway. Runs on
your network instead of through ntfy:

```bash
python3 trade_snapshot_server.py
```

- Control page: `http://localhost:8787/index.html`
- The header shows a copyable **OBS Browser Source URL** with the key already in it:
  `http://192.168.1.29:8787/index.html?display=1&src=server&key=xKP8OCplbCY`

Both machines have to be on the same network. The panel appears whenever the relay is running and
the topic isn't carrying — including when a topic is saved but unreachable, which is exactly when
you need the fallback URL in front of you.

**About that key.** Anything from another machine has to present it; anything from this machine
doesn't. So the control page needs no key, and the one URL that carries one is the OBS URL, handed
to you fully built. It's generated on first run, kept in `.relay_key` (mode 600, gitignored), and
stays the same across restarts so you set the Browser Source up once.

- `--new-key` rotates it. Re-copy the URL into OBS after.
- `--local` skips the network entirely; OBS then has to run on this machine.

### If OBS shows nothing

**On a topic (Option B):**

**First: does the Connection pill say `connected` in green?** If it says `not reaching topic`,
nothing is getting out and OBS cannot possibly update — skip to point 4.

1. **Stale page in OBS.** Check the build stamp in the control header, then re-copy the display URL
   (it carries `&v=<build>`, so a re-paste fetches new code) or right-click the Browser Source →
   **Refresh cache of current page**. A cached OBS page is the most common cause and it fails
   silently.
2. **Topic mismatch.** The display URL in OBS has an older topic than the one you connected. Re-copy.
3. **`file://`.** The OBS machine can't open a path on your laptop. Host it on Pages.
4. **ntfy.sh unreachable.** Some networks block it, and it's a free service that can throttle. Test
   it directly: `curl -m 10 https://ntfy.sh/anytopic/json?poll=1&since=1m`. A timeout means blocked —
   fall back to Option C, which stays on your own network.

**Careful with "Open Display ↗" as a test.** With a topic connected it opens the exact URL OBS gets,
so it's a real check. With no topic it falls back to BroadcastChannel, which only works between tabs
of one browser — it will light up on your laptop and stay dark in OBS no matter what's wrong.

**On the local relay (Option C):**

1. **Firewall.** macOS asks whether to allow incoming connections for Python the first time — say
   yes. If you missed it: System Settings → Network → Firewall → Options.
2. **Different networks.** Guest wifi and client-isolated networks block machine-to-machine traffic
   even when both have internet.
3. **The IP moved.** DHCP hands out a new one after a reboot. The control page picks it up on its
   own — just re-copy.
4. **Stale key**, if you've run `--new-key` since. Re-copy.

Running the relay on the OBS box instead? Point the control page at it:

```
http://localhost:8787/index.html?relay=192.168.1.50:8787&key=xKP8OCplbCY
```

### Driving it during a show

Open a player → the bar comes up automatically with their primary line (hitting for position
players, pitching for pitchers). Click a different timeframe pill → the bar updates in place.
Click a different player → the old bar fades out before the new one fades in, never a hard cut.

**✕ Exit Lower Third** (in the header or on the player card) takes it off screen.

### Baking a still

**⤓ Hitting PNG** / **⤓ Pitching PNG** on the player card downloads a 1920×1080 transparent PNG of
the same bar, drawn on canvas — same layout, same fonts, no screenshotting. It also pushes that
line on air, so what you saved is what's up.

If the graphic saves without a headshot, MLB's image host declined the cross-origin read that day.
The rest of the bar is unaffected.

---

## Look

Shared with the rest of the Talkin' Baseball tools:

- Navy `#0d1f2d` → `#173a56`, gold `#fbcc7a`
- Bebas Neue for names and numbers, DM Sans for body copy, DM Mono for labels
- Gold rule across the top of the lower third, gold ring on the headshot

---

## Notes

- **The bar never wraps to two rows.** Timeframes carry different stat counts, so both the live bar
  and the PNG shrink cell width and font until everything fits on one line.
- **K% is derived, not fetched.** The API doesn't return it, but every stat shape used here carries
  the raw counts — strikeouts over plate appearances for hitters, over batters faced for pitchers.
- **Vs-L/R pitching splits have no ERA, W-L, or saves.** Those aren't real concepts split by
  opposing-batter handedness, so that view swaps in IP/WHIP/K/BB/BAA/HR instead.
- **Stat responses are cached per URL for the session.** Clicking back to a timeframe you already
  looked at is instant; reload the page to force fresh numbers.
- Older seasons work, but the roster shown is the current 40-man, not that year's.
- **The background never animates on a stat change.** Only the content cross-fades, and the
  headshot/crest only fades when the picture actually differs — cycling a team's categories keeps
  the same crest, so fading it would read as a flicker on something that didn't change. The bar
  itself only fades coming on air and going off.
- **Cells scale to fill the bar, not just to fit.** Font size comes from the width each cell ends up
  with, measured after layout and after Bebas Neue has loaded — measuring early or against a
  fallback font is how you end up with 32px numbers in a 250px bar.
- **Coming back from a hidden tab re-snaps the layers.** Browsers freeze CSS transitions in a hidden
  tab, so a swap interrupted by hiding could resume with the content stuck transparent — background
  on screen, no stats in it. Visibility changes force the resting state rather than trusting an
  interrupted transition to have finished.
- **The overlay holds its last frame if the network drops.** A failed poll is ignored rather than
  blanking the bar, so a brief wifi hiccup doesn't yank a graphic off air mid-sentence.
- **Identical content never re-renders.** The same message arrives twice by design — SSE delivers
  it and the polling safety net delivers it again — and the load backfill replays several at once.
  Every payload is fingerprinted (excluding its timestamp) and duplicates are dropped before they
  touch the DOM. Without that guard each duplicate restarted the fade, which showed up as a
  graphic flickering while it just sat there.
