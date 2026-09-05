"""Bounded, non-destructive cache/model microbenchmark; never trains production weights."""
import argparse
import itertools
import json
import statistics
import tempfile
import time
from pathlib import Path

from adversarial_jepa import AdversarialJEPA, iter_dataset_games, dataset_manifest_fingerprint
from lejepa import LeJEPA
from nnue_baseline import NNUEStyleBaseline
from policy_value_baseline import DirectPolicyValueBaseline
from training_runtime import SampleCache
from train_caissa_v7 import batches, atomic_json


def benchmark(dataset, games=16, repeats=3):
    with tempfile.TemporaryDirectory(prefix="caissa-benchmark-") as folder:
        root = Path(folder)
        selected = list(itertools.islice(iter_dataset_games(dataset), games))
        shard = root/"sample.jsonl"
        with shard.open("w", encoding="utf-8") as handle:
            for game in selected:
                handle.write(json.dumps(game)+"\n")
        atomic_json(root/"dataset_manifest.json", {"shards":[{"path":shard.name}],"positions":sum(len(g['positions']) for g in selected)})
        started = time.perf_counter()
        cache = SampleCache(root,dataset_manifest_fingerprint(root),10).prepare()
        preparation = time.perf_counter()-started
        measurements = {"uncached":[],"cached":[]}
        for _ in range(repeats):
            for kind in measurements:
                started=time.perf_counter()
                iterator = batches(root,"train",64,7,10) if kind=="uncached" else cache.batches("train",64,7)
                count = sum(len(batch) for batch in iterator)
                measurements[kind].append(time.perf_counter()-started)
        sample = next(cache.batches("train",64,7))
        models = {}
        for name,cls,kwargs in (("h1",AdversarialJEPA,{"variant":"h1"}),
                                ("multi-horizon",AdversarialJEPA,{}),
                                ("lejepa",LeJEPA,{}),("policy-value",DirectPolicyValueBaseline,{}),
                                ("nnue-style",NNUEStyleBaseline,{})):
            model=cls(root/f"{name}.npz",latent_size=96,**kwargs)
            values=[]
            for _ in range(4):
                started=time.perf_counter()
                model.train_batch(sample)
                values.append(time.perf_counter()-started)
            models[name]={"median_batch_seconds":statistics.median(values),"batch_positions":len(sample)}
        return {"scope":"microbenchmark; warm cache; NOT full training speedup",
                "games":len(selected),"train_positions":count,"build_seconds":preparation,
                "cache_bytes":cache.path.stat().st_size,"timings_seconds":measurements,
                "cached_preparation_speedup":statistics.median(measurements['uncached'])/statistics.median(measurements['cached']),
                "models":models}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset",type=Path,default=Path("fen_dataset"))
    parser.add_argument("--games",type=int,default=16)
    parser.add_argument("--output",type=Path,default=Path("docs/validation/training-benchmark.json"))
    args=parser.parse_args()
    result=benchmark(args.dataset,args.games)
    atomic_json(args.output,result)
    print(json.dumps(result,indent=2))
