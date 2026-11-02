"""Child process for API image providers. Run ONLY via `secrets-runner run --ref ... -- python3 api_call.py <provider> <aspect> <out>`,
prompt on stdin. The key is read from this process's env and never printed. Stdlib only.

Status: request shapes follow each provider's public docs as of 2026-10; none has been exercised against the live API
(no keys exist yet). Tests run them against a local mock server via IMAGEGEN_API_BASE.
"""
import base64
import json
import os
import sys
import urllib.request

SIZES = {"1:1": (1024, 1024), "3:2": (1536, 1024), "2:3": (1024, 1536), "4:5": (1024, 1280), "5:4": (1280, 1024),
         "16:9": (1536, 864), "9:16": (864, 1536), "21:9": (1536, 658)}
BASE = os.environ.get("IMAGEGEN_API_BASE")  # tests point every provider at a mock server


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def openai(prompt, aspect):
    w, h = SIZES[aspect]
    size = "1024x1024" if w == h else ("1536x1024" if w > h else "1024x1536")  # gpt-image-1 sizes
    d = post((BASE or "https://api.openai.com") + "/v1/images/generations",
             {"model": os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"), "prompt": prompt, "size": size, "n": 1},
             {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]})
    return base64.b64decode(d["data"][0]["b64_json"])


def fal(prompt, aspect):
    w, h = SIZES[aspect]
    d = post((BASE or "https://fal.run") + "/" + os.environ.get("FAL_MODEL", "fal-ai/flux/schnell"),
             {"prompt": prompt, "image_size": {"width": w, "height": h}, "num_images": 1},
             {"Authorization": "Key " + os.environ["FAL_KEY"]})
    return fetch(d["images"][0]["url"])


def gemini_api(prompt, aspect):
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    d = post((BASE or "https://generativelanguage.googleapis.com") + f"/v1beta/models/{model}:generateContent",
             {"contents": [{"parts": [{"text": f"{prompt} Aspect ratio {aspect}."}]}]},
             {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for part in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError("no image part in Gemini response")


def together(prompt, aspect):
    w, h = SIZES[aspect]
    d = post((BASE or "https://api.together.xyz") + "/v1/images/generations",
             {"model": os.environ.get("TOGETHER_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"), "prompt": prompt,
              "width": w, "height": h, "n": 1, "response_format": "b64_json"},
             {"Authorization": "Bearer " + os.environ["TOGETHER_API_KEY"]})
    return base64.b64decode(d["data"][0]["b64_json"])


def replicate(prompt, aspect):
    model = os.environ.get("REPLICATE_MODEL", "black-forest-labs/flux-schnell")
    d = post((BASE or "https://api.replicate.com") + f"/v1/models/{model}/predictions",
             {"input": {"prompt": prompt, "aspect_ratio": aspect, "output_format": "png"}},
             {"Authorization": "Bearer " + os.environ["REPLICATE_API_TOKEN"], "Prefer": "wait"})
    out = d.get("output")
    if not out:
        raise RuntimeError(f"replicate status {d.get('status')}")
    return fetch(out[0] if isinstance(out, list) else out)


ADAPTERS = {"openai": openai, "fal": fal, "gemini-api": gemini_api, "together": together, "replicate": replicate}

if __name__ == "__main__":
    provider, aspect, out = sys.argv[1:4]
    data = ADAPTERS[provider](sys.stdin.read(), aspect)
    with open(out, "wb") as f:
        f.write(data)
    print(f"wrote {out} ({len(data)} bytes)")
