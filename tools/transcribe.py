import sys, os, wave, time
import numpy as np
from moonshine_onnx import MoonshineOnnxModel, load_tokenizer

SR = 16000
MAXLEN = 20.0   # seconds per chunk
MINLEN = 6.0

def read_wav(path):
    w = wave.open(path)
    n = w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    return a

def split_points(a):
    """Segment audio into <=MAXLEN chunks, cutting at the quietest frame
    inside the allowed window."""
    hop = int(0.02 * SR)
    nf = len(a) // hop
    e = np.array([np.abs(a[i*hop:(i+1)*hop]).mean() for i in range(nf)])
    segs = []
    start = 0
    while start < len(a):
        end_max = start + int(MAXLEN * SR)
        if end_max >= len(a):
            segs.append((start, len(a)))
            break
        lo = (start + int(MINLEN * SR)) // hop
        hi = end_max // hop
        window = e[lo:hi]
        cut = (lo + int(np.argmin(window))) * hop
        segs.append((start, cut))
        start = cut
    return segs

def main(part):
    path = f"audio/part{part}.wav"
    outp = f"transcripts/part{part}.txt"
    os.makedirs("transcripts", exist_ok=True)
    a = read_wav(path)
    segs = split_points(a)
    model = MoonshineOnnxModel(models_dir="models/tiny", model_name="tiny")
    tok = load_tokenizer()
    t0 = time.time()
    with open(outp, "w") as f:
        for i, (s, e) in enumerate(segs):
            clip = a[s:e]
            if np.abs(clip).max() < 1e-3:
                continue
            try:
                out = model.generate(clip[None, :])
                txt = tok.decode_batch(out)[0].strip()
            except Exception as ex:
                txt = ""
            ts = s / SR
            f.write(f"[{int(ts//3600):02d}:{int(ts//60)%60:02d}:{int(ts%60):02d}] {txt}\n")
            f.flush()
            if i % 25 == 0:
                done = e / SR
                print(f"part{part} {i}/{len(segs)} audio={done:.0f}s elapsed={time.time()-t0:.0f}s", flush=True)
    print(f"part{part} DONE in {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main(sys.argv[1])
