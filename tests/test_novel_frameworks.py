import glob, os, json, importlib.util, math
def test_novel_frameworks_load():
    for p in glob.glob("novel-frameworks/qualia-math/qualia_eq_*_*.json"):
        with open(p) as f2: j=json.load(f2); assert j["validation"]["sanity"]
