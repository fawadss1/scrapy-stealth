# Detects JS challenge / CAPTCHA *shells* — structural checks + specific markers.
# Avoid bare vendor names (datadome/akamai/captcha/kasada): real product pages
# embed those in scripts and would never leave the browser wait loop.
_JS_IS_CHALLENGE = (
    "(()=>{"
    "const h=document.documentElement.innerHTML.toLowerCase();"
    "const t=(document.title||'').toLowerCase();"
    ""
    # Specific challenge markers (not bare vendor names).
    "const has_keywords = ["
    "'ray id','cf-challenge','cf_chl','challenge-platform',"
    "'challenges.cloudflare.com','cf-turnstile','turnstile',"
    "'verifying you are human','checking your browser',"
    "'recaptcha','hcaptcha','px-captcha','ak-challenge',"
    "'sec-if-cpt-container','behavioral-content','cf-browser-verification'"
    "].some(k=>h.includes(k));"
    "if (has_keywords) return true;"
    ""
    # Challenge titles.
    "const title_kw = ["
    "'just a moment','access denied','attention required',"
    "'are you a human','are you human','one more step',"
    "'security check','please verify'"
    "].some(k=>t.includes(k));"
    "if (title_kw) return true;"
    ""
    "const b=document.body;"
    "if (!b) return false;"
    ""
    # Empty body.
    "if (b.children.length === 0 && b.innerText.trim().length === 0) {"
    "    return true;"
    "}"
    ""
    # Body is only <script> tag(s).
    "const kids = Array.from(b.children);"
    "if (kids.length > 0 && kids.every(el => el.tagName === 'SCRIPT')) {"
    "    return true;"
    "}"
    ""
    # Body is only <noscript>.
    "if (kids.length === 1 && kids[0].tagName === 'NOSCRIPT') {"
    "    return true;"
    "}"
    ""
    # Meta refresh redirect.
    "const metas=Array.from(document.getElementsByTagName('meta'));"
    "if (metas.some(m=>(m.getAttribute('http-equiv')||'').toLowerCase()==='refresh')) {"
    "    return true;"
    "}"
    ""
    # Body is only a single <iframe>.
    "if (kids.length === 1 && kids[0].tagName === 'IFRAME') {"
    "    return true;"
    "}"
    ""
    "return false;"
    "})()"
)
