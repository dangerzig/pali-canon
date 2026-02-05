#!/usr/bin/env python3
"""
Download GRETIL PTS editions for all Sutta Piṭaka nikāyas.

Direct file access works even though directory listing is blocked.
"""

import urllib.request
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
GRETIL_DIR = DATA_DIR / "gretil-pts"

# GRETIL file URLs for each nikāya
# Based on their naming convention: {nikaya}n{vol}pu.htm
GRETIL_FILES = {
    'dn': [
        ("dn_vol1.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/dighn1pu.htm"),
        ("dn_vol2.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/dighn2pu.htm"),
        ("dn_vol3.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/1_digh/dighn3pu.htm"),
    ],
    'mn': [
        ("mn_vol1.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/2_majjh/majjn1pu.htm"),
        ("mn_vol2.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/2_majjh/majjn2pu.htm"),
        ("mn_vol3.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/2_majjh/majjn3pu.htm"),
    ],
    'sn': [
        ("sn_vol1.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/3_samyu/samyun1pu.htm"),
        ("sn_vol2.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/3_samyu/samyun2pu.htm"),
        ("sn_vol3.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/3_samyu/samyun3pu.htm"),
        ("sn_vol4.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/3_samyu/samyun4pu.htm"),
        ("sn_vol5.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/3_samyu/samyun5pu.htm"),
    ],
    'an': [
        ("an_vol1.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/4_angut/angutn1pu.htm"),
        ("an_vol2.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/4_angut/angutn2pu.htm"),
        ("an_vol3.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/4_angut/angutn3pu.htm"),
        ("an_vol4.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/4_angut/angutn4pu.htm"),
        ("an_vol5.html", "https://gretil.sub.uni-goettingen.de/gretil/2_pali/1_tipit/2_sut/4_angut/angutn5pu.htm"),
    ],
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def download_file(url, output_path):
    """Download a single file."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        response = urllib.request.urlopen(req, timeout=30)
        content = response.read()
        output_path.write_bytes(content)
        return len(content)
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def main():
    print("=" * 60)
    print("Downloading GRETIL PTS Editions")
    print("=" * 60)

    GRETIL_DIR.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0
    total_bytes = 0

    for nikaya, files in GRETIL_FILES.items():
        print(f"\n{nikaya.upper()}:")

        for filename, url in files:
            output_path = GRETIL_DIR / filename

            # Skip if already exists
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"  {filename}: Already exists ({output_path.stat().st_size:,} bytes)")
                continue

            print(f"  Downloading {filename}...", end=" ", flush=True)
            size = download_file(url, output_path)

            if size > 0:
                print(f"OK ({size:,} bytes)")
                total_downloaded += 1
                total_bytes += size
            else:
                print("FAILED")

            # Be polite to the server
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"Downloaded {total_downloaded} files ({total_bytes:,} bytes)")
    print(f"Files saved to: {GRETIL_DIR}")


if __name__ == "__main__":
    main()
