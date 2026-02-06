# DNS Retest Commands

Run these after making DNS changes:

```text
nslookup -type=NS gahenaxaisolutions.com 8.8.8.8
nslookup -type=CNAME trickster-api.gahenaxaisolutions.com 8.8.8.8
nslookup -type=CNAME trickster-api.gahenaxaisolutions.com 1.1.1.1
dig trickster-api.gahenaxaisolutions.com CNAME +trace
dig trickster-api.gahenaxaisolutions.com CNAME @8.8.8.8 +noall +answer +comments
dig trickster-api.gahenaxaisolutions.com CNAME @1.1.1.1 +noall +answer +comments
```
