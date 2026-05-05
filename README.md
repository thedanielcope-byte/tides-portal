# Tides Bookkeeping Client Portal

Secure, branded client portal hosted on Cloudflare Pages with Cloudflare Access authentication. Scales to 50 clients on the free tier; no monthly subscription.

**Live URL:** https://portal.tidesbookkeeping.com (once DNS is configured)

## Architecture

```
Client visits → portal.tidesbookkeeping.com
    ↓
Cloudflare Access prompts for email
    ↓
Client enters email → gets 6-digit OTP code via email
    ↓
Code verified → Cloudflare sets auth cookie
    ↓
Client lands on /index.html (router)
    ↓
JavaScript reads email from auth cookie, looks up their slug
    ↓
Auto-redirects to /clients/{their-slug}/ (their personal hub)
```

Monthly reports and file uploads live in OneDrive (no file infrastructure in this repo). Each client's hub page embeds links to their specific OneDrive folders.

## Repo structure

```
tides-portal/
├── index.html              Login landing + email→portal router
├── _headers                Cloudflare Pages security headers
├── robots.txt              Disallow search engines (private portal)
├── assets/
│   └── logo.png
├── clients/
│   ├── acme-corp/
│   │   └── index.html      Acme's hub (generated from template)
│   └── beta-llc/
│       └── index.html
├── shared/
│   └── onboarding.html     Shared onboarding/help page
├── _template/
│   └── client.html         Master template for all client hubs
└── _scripts/
    ├── add-client.py       Generate new client hub from CSV or prompts
    └── clients.csv         Client registry (slug, email, URLs)
```

## Adding a new client (3-minute process)

1. Edit `_scripts/clients.csv` — add one row with the client's info:
   - `slug` — URL-safe identifier (e.g., `acme-corp`)
   - `client_name` — Display name (e.g., `Acme Corp`)
   - `email` — Client's login email
   - `reports_url` — OneDrive share link to their Reports folder (read-only)
   - `upload_url` — OneDrive "Request Files" link to their Uploads folder
   - `quick_links` — Pipe-separated label/URL pairs joined by `;`. See format below.

   **Quick links format:** `Label|URL;Label|URL;Label|URL` — wrapped in double-quotes.
   Example:
   ```
   "QuickBooks Online|https://qbo.intuit.com/app/123;Puzzle Dashboard|https://app.puzzle.io/a/acme;Annual Tax Filings|https://1drv.ms/f/s!acme-tax"
   ```
   Icons are auto-matched by label keyword (QuickBooks → 📊, Puzzle → 🧩, Tax → 📑, etc.). To customize, edit `QUICK_LINK_ICONS` in `add-client.py`.

2. Run the generator:
   ```
   python3 _scripts/add-client.py --csv
   ```
   This creates `/clients/{slug}/index.html` and updates the email→slug map in `index.html`.

3. Add the client's email to Cloudflare Access:
   - Cloudflare Dashboard → Zero Trust → Access → Applications → tides-portal
   - Policies → Edit "Allow clients" → Add email
   - Save

4. Commit and push:
   ```
   git add -A && git commit -m "Add client: Acme Corp" && git push
   ```

5. Email the client:
   ```
   Subject: Your Tides Bookkeeping Portal is Ready

   Hi [Name],

   Your secure client portal is live at:
   https://portal.tidesbookkeeping.com

   To sign in, just enter your email ({email}) — we'll send you a 6-digit code. No password to remember.

   Your portal has:
   • Monthly financial reports
   • Secure document upload (for receipts, invoices, etc.)
   • Quick links to your dashboards and tax documents
   • Direct chat with your bookkeeper

   Let us know if you need anything!

   — Tides Bookkeeping
   ```

## Editing an existing client

You have two options:

**Option A — Edit the CSV (recommended for routine changes)**
1. Open `_scripts/clients.csv`
2. Find the client's row, edit any value
3. Run `python3 _scripts/add-client.py --csv` (regenerates ALL clients from CSV)
4. Push: `git add -A && git commit -m "Update [client name]" && git push`

**Option B — Edit the client's HTML directly (for one-off tweaks)**
1. Open `clients/{slug}/index.html` in a text editor
2. Search for the value you want to change (e.g., the QuickBooks URL)
3. Edit + save
4. Push

Note: if you edit the HTML directly, your changes will be **overwritten** the next time someone runs the generator with `--csv`. So always sync changes back to `clients.csv` if you want them to persist.

**Option C — Ask Claude**
Just say: "Update Acme Corp's QuickBooks URL to https://..." and I'll handle it.

## First-time setup

See `SETUP.md` for complete setup instructions (DNS, Cloudflare Pages, Cloudflare Access).

## Updating the template

Edit `_template/client.html`, then regenerate all client pages:

```
python3 _scripts/add-client.py --csv
git add -A && git commit -m "Update portal template" && git push
```

## Design system

Matches tidesbookkeeping.com:
- Primary: `#215197` (navy)
- Accent: `#41cfd0` (teal)
- Blue: `#66c1ee`
- Ink: `#0f1c2e`
- Fonts: Bebas Neue (headings) + Inter (body)

## Security

- **Authentication:** Cloudflare Access email OTP (no passwords to steal)
- **Data isolation:** Each client URL has its own policy; cross-client access is impossible
- **File storage:** OneDrive (Microsoft's bank-grade infrastructure)
- **Transport:** HTTPS-only via Cloudflare
- **Headers:** HSTS, X-Frame-Options: DENY, CSP-ready (see `_headers`)
- **Audit log:** Cloudflare Access dashboard → Logs (every sign-in tracked)

## Cost

- Cloudflare Pages: Free (unlimited bandwidth)
- Cloudflare Access: Free up to 50 users
- OneDrive: Already paid for via Microsoft 365
- **Total: $0/month** up to 50 clients

Above 50 clients: Cloudflare Zero Trust paid tier kicks in (~$7/user/month). At that scale, evaluate Assembly.com Professional ($149/mo flat for 500 clients) vs paying Cloudflare.
