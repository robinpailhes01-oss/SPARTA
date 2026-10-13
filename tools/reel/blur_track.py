"""Floute une zone plane (ex. champs manuscrits d'un formulaire) qui bouge dans un plan de coupe, avec suivi.

La zone est donnée sur une image de référence ; pour chaque image du passage traité, on estime l'homographie
référence → image par points SIFT appariés (RANSAC) limités à l'objet suivi, on lisse les coins dans le temps,
puis on applique un flou fort à bords adoucis dans le quadrilatère obtenu. Le reste du clip est recopié tel quel
(réencodage x264 avec image clé chaque seconde, balises bt709).

Usage : python3 tools/reel/blur_track.py <in.mp4> <out.mp4> --ref 2.3 --zone x0,y0,x1,y1 --objet x0,y0,x1,y1 \
            --de 0 --a 4.3 [--controle planche.jpg]
  --zone   rectangle à flouter sur l'image de référence (pixels du clip)
  --objet  rectangle de l'objet suivi sur l'image de référence (où chercher les points : la feuille entière)
  --controle  écrit une planche où la zone suivie est tracée en rouge au lieu d'être floutée
"""
import argparse
import subprocess

import cv2
import numpy as np


def rect(s):
    return [int(v) for v in s.split(",")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--ref", type=float, required=True)
    ap.add_argument("--zone", type=rect, required=True)
    ap.add_argument("--objet", type=rect, required=True)
    ap.add_argument("--de", type=float, default=0.0)
    ap.add_argument("--a", type=float, default=1e9)
    ap.add_argument("--controle")
    o = ap.parse_args()

    cap = cv2.VideoCapture(o.src)
    fps = cap.get(cv2.CAP_PROP_FPS)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    f0, f1 = max(0, int(o.de * fps)), min(n - 1, int(o.a * fps))
    S = 0.5                                                   # analyse à mi-définition
    sift = cv2.SIFT_create(nfeatures=4000)
    bf = cv2.BFMatcher(cv2.NORM_L2)

    cap.set(cv2.CAP_PROP_POS_FRAMES, int(o.ref * fps))
    ok, ref = cap.read()
    g = cv2.resize(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), None, fx=S, fy=S)
    m = np.zeros_like(g)
    x0, y0, x1, y1 = [int(v * S) for v in o.objet]
    m[y0:y1, x0:x1] = 255
    kr, dr = sift.detectAndCompute(g, m)
    zx0, zy0, zx1, zy1 = o.zone
    quad = np.float32([[zx0, zy0], [zx1, zy0], [zx1, zy1], [zx0, zy1]]).reshape(-1, 1, 2)

    # 1. Homographie par image
    corners, inl = {}, {}
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
    for i in range(f0, f1 + 1):
        ok, fr = cap.read()
        if not ok:
            break
        gi = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), None, fx=S, fy=S)
        ki, di = sift.detectAndCompute(gi, None)
        good = []
        if di is not None and len(ki) > 10:
            for pair in bf.knnMatch(dr, di, k=2):
                if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance:
                    good.append(pair[0])
        Hm, mask = None, None
        if len(good) >= 12:
            a = np.float32([kr[g_.queryIdx].pt for g_ in good]).reshape(-1, 1, 2) / S
            b = np.float32([ki[g_.trainIdx].pt for g_ in good]).reshape(-1, 1, 2) / S
            Hm, mask = cv2.findHomography(a, b, cv2.RANSAC, 6.0)
        inl[i] = int(mask.sum()) if mask is not None else 0
        if Hm is not None and inl[i] >= 15:
            corners[i] = cv2.perspectiveTransform(quad, Hm).reshape(4, 2)
    # trous : on reprend le voisin le plus proche
    keys = sorted(corners)
    if not keys:
        raise SystemExit("suivi impossible")
    for i in range(f0, f1 + 1):
        if i not in corners:
            corners[i] = corners[min(keys, key=lambda k: abs(k - i))]
    # lissage temporel (moyenne glissante sur 5 images)
    sm = {}
    for i in range(f0, f1 + 1):
        win = [corners[j] for j in range(max(f0, i - 2), min(f1, i + 2) + 1)]
        sm[i] = np.mean(win, axis=0)
    weak = [i for i in range(f0, f1 + 1) if inl.get(i, 0) < 30]
    print(f"{f1 - f0 + 1} images suivies, inliers min {min(inl.values()) if inl else 0}, "
          f"médian {int(np.median(list(inl.values())))}, faibles (<30) : {len(weak)}")

    # 2. Écriture
    if o.controle:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
        tiles = []
        for i in range(f0, f1 + 1):
            ok, fr = cap.read()
            if (i - f0) % max(1, (f1 - f0) // 15) == 0:
                cv2.polylines(fr, [sm[i].astype(np.int32)], True, (0, 0, 255), 6)
                cv2.putText(fr, f"{i / fps:.2f}s inl={inl.get(i, 0)}", (20, 80), 0, 2, (0, 255, 255), 4)
                tiles.append(cv2.resize(fr, (270, 480)))
        while len(tiles) % 8:
            tiles.append(np.zeros_like(tiles[0]))
        rows = [np.hstack(tiles[k:k + 8]) for k in range(0, len(tiles), 8)]
        cv2.imwrite(o.controle, np.vstack(rows))
        return

    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                            "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-pix_fmt", "yuv420p",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "-movflags", "+faststart", o.dst], stdin=subprocess.PIPE)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    for i in range(n):
        ok, fr = cap.read()
        if not ok:
            break
        if f0 <= i <= f1:
            q = sm[i].astype(np.int32)
            bx, by, bw, bh = cv2.boundingRect(q)
            pad = 60
            X0, Y0 = max(0, bx - pad), max(0, by - pad)
            X1, Y1 = min(W, bx + bw + pad), min(H, by + bh + pad)
            roi = fr[Y0:Y1, X0:X1]
            small = cv2.resize(roi, None, fx=0.125, fy=0.125, interpolation=cv2.INTER_AREA)
            blur = cv2.GaussianBlur(cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_LINEAR), (0, 0), 9)
            mk = np.zeros(roi.shape[:2], np.float32)
            cv2.fillPoly(mk, [q - [X0, Y0]], 1.0)
            mk = cv2.GaussianBlur(mk, (0, 0), 10)[..., None]
            fr[Y0:Y1, X0:X1] = (roi * (1 - mk) + blur * mk).astype(np.uint8)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
