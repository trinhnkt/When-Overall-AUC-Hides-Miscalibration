"""C3: fetch Reference [21] metadata by DOI content negotiation (IEEE text and BibTeX)."""
import sys
import urllib.request

DOI = "10.1007/978-3-032-37673-2_33"
sys.stdout.reconfigure(encoding="utf-8")
for accept in ("text/x-bibliography; style=ieee", "application/x-bibtex"):
    req = urllib.request.Request(f"https://doi.org/{DOI}", headers={"Accept": accept, "User-Agent": "ref-check/1.0"})
    print("---", accept)
    print(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore"))
