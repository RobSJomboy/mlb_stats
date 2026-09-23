# Deploying the relay

It is already deployed and is the default for both pages:

```
https://jomboy-relay.jomboymedia.workers.dev
```

You only need this file to redeploy after changing `worker.js`, or to stand up a second one.

```bash
cd relay
npx wrangler login      # opens a browser; needs an interactive terminal
npx wrangler deploy
```

## If it is a brand-new Cloudflare account

`wrangler deploy` fails with *"could not automatically register … as your workers.dev subdomain
because the name is unavailable"*. The subdomain is **account-level and registered once**, and
wrangler only ever tries the worker's own name. Register one directly instead:

```bash
TOK=$(grep '^oauth_token' ~/Library/Preferences/.wrangler/config/default.toml | sed 's/.*= *"//; s/"$//')
curl -X PUT -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  --data '{"subdomain":"yourname"}' \
  "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/workers/subdomain"
```

The dashboard's own advice — "open the Workers & Pages landing page and one will be created
automatically" — also works, but the PUT does it without leaving the terminal.

**A brand-new subdomain's certificate takes a minute or two.** Until it is issued, every request
fails the TLS handshake (`curl` exit 35), which looks exactly like a broken deploy. It is not.
Wait and retry — ours came up 45 seconds after the subdomain was created.

## What it does

    POST /r/<room>   body = state JSON   -> store and broadcast to every socket in the room
    GET  /r/<room>                       -> last state (polling fallback / backfill)
    GET  /r/<room>   Upgrade: websocket  -> live push, current state sent on connect
    GET  /                               -> health check

CORS is `*` on everything. Payloads over 512KB are rejected with 413. The Durable Object uses the
hibernation API, so a room between graphics costs nothing while connected clients are never dropped.
