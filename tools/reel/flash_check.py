"""flash_check.py <video>... : repère les plans très courts (< 0,45 s) entre deux changements d'image nets — signe d'un « flash » (image qui apparaît puis disparaît)."""
import subprocess, sys, re
for f in sys.argv[1:]:
    out = subprocess.run(["ffmpeg", "-nostdin", "-i", f, "-vf", "scale=270:-2,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", out)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)
    flashes = [(round(a, 2), round(b - a, 2)) for a, b in zip(cuts, cuts[1:]) if b - a < 0.45]
    print(("FLASH " if flashes else "ok    ") + f.split("/")[-1], f"{dur:.1f}s", flashes)
