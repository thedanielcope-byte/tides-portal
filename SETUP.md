# First-Time Setup Guide

One-time setup to get the portal live at `portal.tidesbookkeeping.com`. Budget about 45-60 minutes for your first time through.

## Overview of what you're setting up

1. **Cloudflare Pages project** (hosts the portal files from this repo)
2. **Custom domain** (portal.tidesbookkeeping.com)
3. **Cloudflare Access** (locks the site behind email login)
4. **OneDrive folders** per client (report delivery + upload destination)
5. **GHL chat widget** (embedded in every portal page)

Do these in order. Each step depends on the previous.

---

## Step 1: Deploy to Cloudflare Pages

1. Log in to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Workers & Pages → Create application → Pages → Connect to Git
3. Select the `tides-portal` GitHub repo
4. Build settings:
   - **Framework preset:** None
   - **Build command:** *(leave blank)*
   - **Build output directory:** `/`
5. Deploy — takes ~30 seconds
6. Note the pages.dev URL Cloudflare assigns (e.g., `tides-portal.pages.dev`)

At this point, the portal is live but UNPROTECTED. Don't share the URL yet.

---

## Step 2: Add custom domain

1. In the Pages project: **Custom domains** → **Set up a custom domain**
2. Enter: `portal.tidesbookkeeping.com`
3. Cloudflare will tell you what DNS record to add

### Add the DNS record at your registrar

Where is `tidesbookkeeping.com` registered? Log in there and add a **CNAME** record:

| Type | Name | Target | TTL |
|---|---|---|---|
| CNAME | `portal` | `tides-portal.pages.dev` | Auto/3600 |

DNS propagates in 1-60 minutes. Once it's live, https://portal.tidesbookkeeping.com loads your portal (still unprotected).

---

## Step 3: Enable Cloudflare Access (the auth layer)

This is what makes the portal secure.

1. Cloudflare dashboard → **Zero Trust** (left sidebar)
2. If first time: follow the setup wizard to activate Zero Trust (it's free for up to 50 users)
3. Zero Trust → **Access** → **Applications** → **Add an application**
4. Type: **Self-hosted**
5. Application configuration:
   - **Application name:** `Tides Client Portal`
   - **Session duration:** `24 hours` (adjust to preference)
   - **Application domain:** `portal.tidesbookkeeping.com`
   - **Application logo:** Upload `/assets/logo.png`
6. Identity providers: Keep default (Cloudflare One-time PIN)
   - This is what sends a 6-digit code to the client's email
7. Next → **Add a policy**
   - **Policy name:** `Allow clients`
   - **Action:** `Allow`
   - **Session duration:** Same as app
   - **Rules → Include:**
     - Selector: `Emails`
     - Value: Add each client's email (comma-separated)
     - Example: `acme@example.com, beta@example.com, daniel@tidesbookkeeping.com`
   - Save
8. Next → **Setup** → Add your authentication methods → pick **One-time PIN** (already default)
9. Add application → Done

Test: visit `portal.tidesbookkeeping.com` in an incognito window. You should see Cloudflare's email prompt. Enter a whitelisted email, get the code, and land on the portal.

---

## Step 4: OneDrive per-client folder setup (do this for each client)

For each client, create two things in your OneDrive:

### 4a. Reports folder (Tides → Client, read-only)

1. In OneDrive, create: `/Tides Clients/{Client Name}/Reports/`
2. Inside that folder, create year subfolders: `/2026/`, `/2025/`, etc.
3. Upload monthly reports into each year folder, named like:
   - `2026-01 Profit & Loss.pdf`
   - `2026-01 Balance Sheet.pdf`
   - `2026-01 Cash Flow Statement.pdf`
   - `2026-01 Executive Summary.pdf`
4. Right-click the `/Reports/` folder → **Share** → **Anyone with the link can view** → **Copy link**
5. Paste this link into `_scripts/clients.csv` as `reports_url`

*(Note: "Anyone with the link" is fine because Cloudflare Access already gates the portal page that displays this link. Unauthorized people will never see it.)*

### 4b. Uploads folder (Client → Tides)

1. In OneDrive, create: `/Tides Clients/{Client Name}/Uploads/`
2. Right-click → **Request files** (OneDrive feature)
3. Description: `Upload any receipts, invoices, or documents for your Tides team here.`
4. Copy the request-files URL
5. Paste into `_scripts/clients.csv` as `upload_url`

OneDrive will notify you via email whenever the client uploads. Files land in that folder automatically.

### 4c. Optional: Puzzle.io and Gusto URLs

- **Puzzle.io:** Grab the client's dashboard URL (or their workspace invite link)
- **Gusto:** Either the client's company login page or just `https://app.gusto.com`

---

## Step 5: GoHighLevel Chat Widget

1. In GHL: **Sites** → **Chat Widgets** → Create or select widget
2. Copy the embed `<script>` tag
3. In this repo, open `_template/client.html`
4. Find the line near the bottom:
   ```html
   <script src="https://widgets.leadconnectorhq.com/loader.js" data-widget-id="REPLACE_WITH_YOUR_GHL_WIDGET_ID"></script>
   ```
5. Replace with your actual embed code
6. Regenerate all client pages:
   ```
   python3 _scripts/add-client.py --csv
   ```
7. Commit and push

---

## Step 6: Verify end-to-end

Have a teammate (not already in Cloudflare Access) try the full flow:

1. Add their email to `_scripts/clients.csv` as a test client
2. Add their email to the Cloudflare Access policy
3. Regenerate: `python3 _scripts/add-client.py --csv`
4. Push: `git push`
5. Wait ~30 sec for Cloudflare to redeploy
6. In their browser: visit `portal.tidesbookkeeping.com`
7. Enter their email → receive code → log in
8. Should auto-redirect to `/clients/{slug}/` and see the hub
9. Test: click a month tile, click upload, test chat widget

When that works, you're done. Remove the test client from both the CSV and the Access policy.

---

## Troubleshooting

**"Access Denied" after entering email**
- Email not in Cloudflare Access policy. Add it and retry.

**Stuck on "Welcome" page, doesn't auto-redirect**
- Email not in `CLIENT_MAP` in `/index.html`. Run the generator script.

**Cloudflare Access keeps re-prompting**
- Cookies blocked in browser, or session expired. Try incognito + fresh login.

**Client says the upload link doesn't work**
- OneDrive request-files links expire by default after 1 year. Recreate the link.

**Ongoing: how to refresh a client's Reports link?**
- You don't need to — OneDrive shared folder links are permanent until revoked.
- You just drop new PDFs into the existing year folder. Client sees them next time they click the month.

---

## Support

Questions about this setup: reach out during the build phase. Once deployed, this should run itself with only the 3-minute "add new client" workflow.
