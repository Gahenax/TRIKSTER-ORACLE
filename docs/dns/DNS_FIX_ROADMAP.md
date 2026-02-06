# DNS Fix Roadmap (Minimal)

## Plan A (Immediate): Keep using Render URL
- API base: https://trickster-oracle-api.onrender.com
- No DNS changes required.

## Plan B (Correct fix): Make the subdomain exist in authoritative DNS
### Step 1: Identify authoritative DNS provider
- Run: nslookup -type=NS gahenaxaisolutions.com 8.8.8.8
- The NS returned are the authoritative delegation.

### Step 2: Apply one of the following
#### Option B1: If authoritative is dns-parking
- Log into the dns-parking panel (where DNS is actually served)
- Create: trickster-api  CNAME  trickster-oracle-api.onrender.com
- Ensure there is no A/AAAA for the same host.

#### Option B2: Move DNS to Cloudflare (recommended) or Hostinger
- In your registrar: change nameservers to Cloudflare/Hostinger
- After delegation updates, create the same CNAME in that DNS provider.

### Step 3: Verify
- dig trickster-api.gahenaxaisolutions.com CNAME +trace
- dig trickster-api.gahenaxaisolutions.com CNAME @8.8.8.8 +noall +answer +comments

### Step 4: Render TLS
- Once CNAME resolves, Render will issue TLS for the custom domain.
- Verify: curl -I https://trickster-api.gahenaxaisolutions.com/health
