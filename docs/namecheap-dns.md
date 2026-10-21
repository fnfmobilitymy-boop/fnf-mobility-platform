# kennystudio.space — Namecheap DNS

A browser `ERR_NAME_NOT_RESOLVED` occurs before the website loads. Repository updates do not change registrar DNS records. Check the active nameservers and existing records before making changes.

If **Domain List → kennystudio.space → Manage → Nameservers** is **Namecheap BasicDNS**, open **Advanced DNS → Host Records**. The GitHub Pages target records are:

| Type | Host | Value | TTL |
| --- | --- | --- | --- |
| A Record | @ | 185.199.108.153 | Automatic |
| A Record | @ | 185.199.109.153 | Automatic |
| A Record | @ | 185.199.110.153 | Automatic |
| A Record | @ | 185.199.111.153 | Automatic |
| CNAME Record | www | fnfmobilitymy-boop.github.io | Automatic |

If nameservers are **Custom DNS**, records must be checked at the provider named there; editing Namecheap Host Records would not change the active zone. Do not switch nameservers just to follow this example.

Only replace conflicting website records after confirming them. Preserve MX, TXT, verification and other unrelated records. The CNAME target contains no `https://` and no repository path.

The repository's root CNAME remains `kennystudio.space`. GitHub Pages must retain the same custom domain; its DNS check should pass after public records resolve. Existing correct records may instead require checking the visitor's DNS resolver/cache. DNS changes are not instantaneous.

The English share image is `/kenny-studio-share-20261021.jpg` (JPEG, 1200 × 630). It requires working domain DNS, as does the homepage. Once the domain works, social platforms may need a fresh scrape; an existing post's cached preview is not guaranteed to update automatically.

Official GitHub instructions: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
