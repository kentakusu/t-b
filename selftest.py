import asyncio
import time
import sys
from src.tui_browser.engine import BrowserEngine

SITES = [
    "https://example.com",
    "https://www.google.com",
    "https://www.wikipedia.org",
    "https://news.ycombinator.com",
    "https://github.com",
    "https://stackoverflow.com",
    "https://www.reddit.com",
    "https://www.amazon.com",
    "https://www.bbc.com",
    "https://www.nytimes.com",
    "https://www.cnn.com",
    "https://www.youtube.com",
    "https://www.twitter.com",
    "https://www.linkedin.com",
    "https://www.instagram.com",
    "https://www.facebook.com",
    "https://www.apple.com",
    "https://www.microsoft.com",
    "https://www.netflix.com",
    "https://www.spotify.com",
    "https://www.twitch.tv",
    "https://www.mozilla.org",
    "https://www.python.org",
    "https://docs.python.org",
    "https://nodejs.org",
    "https://www.rust-lang.org",
    "https://go.dev",
    "https://www.typescriptlang.org",
    "https://reactjs.org",
    "https://vuejs.org",
    "https://angular.io",
    "https://svelte.dev",
    "https://nextjs.org",
    "https://nuxt.com",
    "https://astro.build",
    "https://tailwindcss.com",
    "https://getbootstrap.com",
    "https://www.npmjs.com",
    "https://pypi.org",
    "https://crates.io",
    "https://hub.docker.com",
    "https://kubernetes.io",
    "https://www.terraform.io",
    "https://aws.amazon.com",
    "https://cloud.google.com",
    "https://azure.microsoft.com",
    "https://vercel.com",
    "https://www.netlify.com",
    "https://www.heroku.com",
    "https://www.digitalocean.com",
    "https://www.cloudflare.com",
    "https://www.fastly.com",
    "https://www.elastic.co",
    "https://grafana.com",
    "https://prometheus.io",
    "https://www.datadoghq.com",
    "https://sentry.io",
    "https://www.postgresql.org",
    "https://www.mysql.com",
    "https://www.mongodb.com",
    "https://redis.io",
    "https://www.sqlite.org",
    "https://www.apache.org",
    "https://nginx.org",
    "https://httpd.apache.org",
    "https://www.debian.org",
    "https://ubuntu.com",
    "https://fedoraproject.org",
    "https://archlinux.org",
    "https://www.kernel.org",
    "https://git-scm.com",
    "https://www.vim.org",
    "https://neovim.io",
    "https://code.visualstudio.com",
    "https://www.jetbrains.com",
    "https://www.sublimetext.com",
    "https://atom.io",
    "https://www.eclipse.org",
    "https://www.latex-project.org",
    "https://pandoc.org",
    "https://jupyter.org",
    "https://www.anaconda.com",
    "https://scikit-learn.org",
    "https://pytorch.org",
    "https://www.tensorflow.org",
    "https://huggingface.co",
    "https://openai.com",
    "https://www.anthropic.com",
    "https://www.midjourney.com",
    "https://stability.ai",
    "https://www.figma.com",
    "https://www.canva.com",
    "https://www.adobe.com",
    "https://www.sketch.com",
    "https://dribbble.com",
    "https://www.behance.net",
    "https://unsplash.com",
    "https://www.pexels.com",
    "https://fonts.google.com",
    "https://fontawesome.com",
    "https://iconify.design",
    "https://www.w3.org",
    "https://developer.mozilla.org",
    "https://web.dev",
    "https://css-tricks.com",
    "https://www.smashingmagazine.com",
    "https://dev.to",
    "https://medium.com",
    "https://hashnode.com",
    "https://www.freecodecamp.org",
    "https://www.codecademy.com",
    "https://www.khanacademy.org",
    "https://www.coursera.org",
    "https://www.udemy.com",
    "https://www.edx.org",
    "https://leetcode.com",
    "https://www.hackerrank.com",
    "https://codeforces.com",
    "https://atcoder.jp",
    "https://www.codewars.com",
    "https://exercism.org",
    "https://www.kaggle.com",
    "https://arxiv.org",
    "https://scholar.google.com",
    "https://www.researchgate.net",
    "https://www.nature.com",
    "https://www.science.org",
    "https://www.ieee.org",
    "https://www.acm.org",
    "https://www.springer.com",
    "https://www.wiley.com",
    "https://www.elsevier.com",
    "https://www.jstor.org",
    "https://www.wolframalpha.com",
    "https://www.desmos.com",
    "https://www.geogebra.org",
    "https://www.symbolab.com",
    "https://www.mathway.com",
    "https://www.weather.com",
    "https://www.accuweather.com",
    "https://www.timeanddate.com",
    "https://www.worldometers.info",
    "https://www.imdb.com",
    "https://www.rottentomatoes.com",
    "https://www.goodreads.com",
    "https://www.craigslist.org",
    "https://www.ebay.com",
    "https://www.etsy.com",
    "https://www.aliexpress.com",
    "https://www.walmart.com",
    "https://www.target.com",
    "https://www.ikea.com",
    "https://www.booking.com",
    "https://www.airbnb.com",
    "https://www.tripadvisor.com",
    "https://www.expedia.com",
]

CONCURRENCY = 5


async def test_site(engine: BrowserEngine, url: str) -> dict:
    start = time.time()
    try:
        content = await engine.navigate(url)
        elapsed = time.time() - start
        has_text = len(content.text_content.strip()) > 0
        has_screenshot = content.screenshot is not None and len(content.screenshot) > 0
        return {
            "url": url,
            "status": "ok",
            "title": content.title[:60],
            "text_len": len(content.text_content),
            "links": len(content.links),
            "images": len(content.images),
            "has_screenshot": has_screenshot,
            "time": round(elapsed, 1),
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "url": url,
            "status": "error",
            "error": str(e)[:80],
            "time": round(elapsed, 1),
        }


async def run_batch(sites: list[str], batch_id: int) -> list[dict]:
    engine = BrowserEngine()
    await engine.start()
    results = []
    for url in sites:
        result = await test_site(engine, url)
        status_icon = "+" if result["status"] == "ok" else "!"
        print(f"[B{batch_id}] {status_icon} {url} ({result['time']}s)")
        results.append(result)
    await engine.stop()
    return results


async def main():
    sites = SITES
    batch_size = len(sites) // CONCURRENCY
    batches = []
    for i in range(CONCURRENCY):
        start = i * batch_size
        end = start + batch_size if i < CONCURRENCY - 1 else len(sites)
        batches.append(sites[start:end])

    print(f"Testing {len(sites)} sites in {CONCURRENCY} parallel batches...")
    print(f"Batch sizes: {[len(b) for b in batches]}")
    print("=" * 70)

    start_time = time.time()
    tasks = [run_batch(batch, i) for i, batch in enumerate(batches)]
    all_results = await asyncio.gather(*tasks)

    results = [r for batch in all_results for r in batch]
    total_time = time.time() - start_time

    ok = [r for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] == "error"]

    print("\n" + "=" * 70)
    print(f"RESULTS: {len(ok)}/{len(results)} OK, {len(errors)} errors")
    print(f"Total time: {total_time:.1f}s")

    if ok:
        avg_time = sum(r["time"] for r in ok) / len(ok)
        avg_text = sum(r["text_len"] for r in ok) / len(ok)
        avg_links = sum(r["links"] for r in ok) / len(ok)
        screenshots = sum(1 for r in ok if r.get("has_screenshot"))
        print(f"Avg load time: {avg_time:.1f}s")
        print(f"Avg text length: {avg_text:.0f} chars")
        print(f"Avg links: {avg_links:.0f}")
        print(f"Screenshots captured: {screenshots}/{len(ok)}")

    if errors:
        print(f"\nFailed sites:")
        for r in errors:
            print(f"  {r['url']}: {r.get('error', 'unknown')}")

    success_rate = len(ok) / len(results) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")

    if success_rate < 80:
        print("WARNING: Success rate below 80%!")
        sys.exit(1)
    else:
        print("PASS: Browser is working well across diverse sites.")


if __name__ == "__main__":
    asyncio.run(main())
