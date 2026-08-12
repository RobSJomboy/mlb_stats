# Deploying the relay (once, ~3 minutes)

This replaces ntfy with a relay on your own Cloudflare account. Free plan, no card.

```bash
cd relay
npx wrangler login     # opens a browser; make a free account if you don't have one
npx wrangler deploy
```

The last command prints a URL like:

```
https://jomboy-relay.<your-subdomain>.workers.dev
```

That URL is the relay. Paste it into the **Relay** box on either control page and hit **Use Relay** —
it's remembered, and it rides along in the Copy Control URL / Copy OBS URL links, so the other
machine gets it automatically.

Check it's alive by opening the URL in a browser. It should answer:

```json
{"ok":true,"service":"jomboy-relay","usage":"POST or GET /r/<room>"}
```

## Redeploying

Change `worker.js`, run `npx wrangler deploy` again. The URL stays the same.

## What it costs

Nothing at this volume. The free plan covers 100,000 requests a day; a three-hour show with a
display connected over a WebSocket is a few hundred. Durable Objects hibernate while idle, so a
room between graphics costs nothing.
