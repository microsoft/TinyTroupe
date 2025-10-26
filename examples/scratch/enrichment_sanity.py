import os
import logging
from tinytroupe.enrichment import TinyEnricher

# Set logging to DEBUG temporarily to see errors
logging.basicConfig(level=logging.DEBUG)

def main():
    content = "Short outline about product launch."
    reqs = "Expand into a detailed document with sections and examples."

    res = TinyEnricher().enrich_content(
        requirements=reqs,
        content=content,
        content_type="Document",
        context_info="",
        context_cache=None,
        verbose=True,
    )

    print("\n=== RESULT ===")
    print("Type:", type(res))
    print("Bool:", bool(res))
    if isinstance(res, dict):
        print("keys:", list(res.keys()))
        print("content length:", len(res.get("content", "")))
        print("metadata:", res.get("metadata"))
        print("First 200 chars:", res.get("content", "")[:200])
    else:
        print("Value:", str(res)[:200])


if __name__ == "__main__":
    print("OPENAI_API_KEY set:", bool(os.getenv("OPENAI_API_KEY")))
    main()
