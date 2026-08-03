# Trade Snapshot

A live MLB stat lookup that puts a Talkin' Baseball lower third on screen. Browse all 30 teams,
open any player, pick a timeframe, and the stat line goes straight to OBS — plus a matching
1920×1080 PNG if you want it baked out.

Everything is one HTML file. No build step, no npm, no API key. Stats come from the public MLB
StatsAPI at page load, so the numbers are whatever the league is showing right now.

---

## Running it

**Just looking things up?** Double-click `index.html`. That's the whole install.

**Putting it on screen?** See the OBS section below.

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

### Option B — Browser Source (cleaner, real transparency)

An OBS Browser Source is its own browser, so it can't hear the control tab directly. Run the relay:

```bash
python3 trade_snapshot_server.py
```

- Control page: `http://localhost:8787/index.html`
- OBS **Browser Source**, 1920×1080, URL:
  `http://localhost:8787/index.html?display=1&src=server`

The **Relay** chip in the header turns green when the server is answering, and re-checks every few
seconds — if it goes grey mid-show, the relay died. With it green, **Open Display ↗** hands the
display view the `&src=server` route for you.

Python 3 only, no pip install, all standard library. Nothing is written to disk.

### Option C — OBS on a different computer

Same as B. Run the relay on the laptop you're driving from; it listens on every interface, so the
OBS machine can reach it over the network.

The banner prints the URL to use, and the control page shows the same thing in a copyable
**OBS Browser Source URL** field once the relay is live:

```
http://192.168.1.29:8787/index.html?display=1&src=server&key=xKP8OCplbCY
```

Paste that into the Browser Source on the OBS computer, 1920×1080. Both machines have to be on the
same network. That's the whole setup — you never type the key, it's already in the URL.

**About that key.** Anything coming from another machine has to present it; anything from this
machine doesn't. So the control page you're driving from needs no key at all, and the one URL that
carries one is the OBS URL, handed to you fully built.

It's generated on first run, stored in `.relay_key` next to the script (mode 600, gitignored), and
**stays the same across restarts** — otherwise you'd be re-pasting into OBS before every show. Set
the Browser Source up once and forget it.

- `--new-key` rotates it, if it ever ends up somewhere it shouldn't. Re-copy the URL into OBS after.
- `--local` skips the network entirely; OBS then has to run on this machine.

If OBS shows nothing, in order of likelihood:

1. **Firewall.** macOS will ask whether to allow incoming connections for Python the first time —
   say yes. If you missed the prompt: System Settings → Network → Firewall → Options.
2. **Different networks.** Guest wifi and client-isolated networks block machine-to-machine traffic
   even when both have internet.
3. **The IP moved.** DHCP hands out a new one after a reboot. The control page picks the new one up
   on its own — just re-copy the URL into OBS.
4. **Stale key in OBS**, if you've run `--new-key` since setting it up. Re-copy.

Running the relay on the OBS box instead? Point the control page at it with `?relay=` and the key:

```
http://localhost:8787/index.html?relay=192.168.1.50:8787&key=xKP8OCplbCY
```

**Worth knowing:** the key keeps out anyone who wanders onto the same network, but this is plain
HTTP — someone already capturing traffic on that network could read it. It's guarding which
baseball stats are on screen, so that's the right trade. Don't reuse the key for anything else.

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
- **The overlay holds its last frame if the network drops.** A failed poll is ignored rather than
  blanking the bar, so a brief wifi hiccup doesn't yank a graphic off air mid-sentence.
