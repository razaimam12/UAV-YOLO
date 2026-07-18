"""
Real-time multi-object detection for UAV / aerial footage using YOLOv8.

Runs on an image, a video file, or a live stream (e.g. an RTSP drone feed),
and reports per-frame latency and FPS so real-time performance is measurable.

Usage:
    python src/detect.py --source samples/street.jpg --show-fps
    python src/detect.py --source video.mp4 --model yolov8n.pt
    python src/detect.py --source rtsp://drone-stream --model yolov8n.pt
"""
import argparse
import time
from pathlib import Path

import cv2
from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser(description="UAV real-time object detection")
    p.add_argument("--source", required=True,
                   help="Image path, video path, RTSP/HTTP stream, or webcam index")
    p.add_argument("--model", default="yolov8n.pt",
                   help="YOLO weights (default: yolov8n.pt, auto-downloaded)")
    p.add_argument("--conf", type=float, default=0.25,
                   help="Confidence threshold")
    p.add_argument("--device", default=None,
                   help="cpu, 0 (first CUDA GPU), etc. Auto-selected if omitted")
    p.add_argument("--show-fps", action="store_true",
                   help="Print per-frame latency and running FPS")
    p.add_argument("--save", action="store_true",
                   help="Save annotated output under outputs/")
    return p.parse_args()


def is_image(source: str) -> bool:
    return Path(source).suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def run(args):
    model = YOLO(args.model)
    print(f"[info] loaded model '{args.model}' "
          f"({len(model.names)} classes)")

    if is_image(args.source):
        t0 = time.perf_counter()
        results = model.predict(args.source, conf=args.conf,
                                device=args.device, verbose=False)
        latency_ms = (time.perf_counter() - t0) * 1000
        r = results[0]
        print(f"[result] {len(r.boxes)} objects detected "
              f"in {latency_ms:.1f} ms ({1000 / latency_ms:.1f} FPS)")
        for box in r.boxes:
            cls = model.names[int(box.cls)]
            print(f"    - {cls:<15} conf={float(box.conf):.2f}")
        if args.save:
            out = Path("outputs")
            out.mkdir(exist_ok=True)
            cv2.imwrite(str(out / "annotated.jpg"), r.plot())
            print(f"[info] saved outputs/annotated.jpg")
        return

    # Video / stream path
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"[error] could not open source: {args.source}")

    frames, total_ms = 0, 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t0 = time.perf_counter()
        results = model.predict(frame, conf=args.conf,
                                device=args.device, verbose=False)
        latency_ms = (time.perf_counter() - t0) * 1000
        frames += 1
        total_ms += latency_ms
        if args.show_fps:
            inst = 1000 / latency_ms if latency_ms else 0
            avg = 1000 / (total_ms / frames) if total_ms else 0
            print(f"frame {frames:>5} | {latency_ms:6.1f} ms | "
                  f"{inst:5.1f} FPS (avg {avg:5.1f})")

    cap.release()
    if frames:
        print(f"[done] {frames} frames | "
              f"avg {total_ms / frames:.1f} ms/frame | "
              f"{1000 / (total_ms / frames):.1f} FPS")


if __name__ == "__main__":
    run(parse_args())
