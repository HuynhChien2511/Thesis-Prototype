"""
Script Tải Mô hình Giọng nói Tiếng Việt Piper ONNX (vi_VN-vais1000-medium)
từ Hugging Face về thư mục `data/models/piper/`.
Sử dụng cho Kiến trúc Hybrid Dual-Engine TTS (Chạy Offline hoàn toàn).
"""
import sys
import os
import urllib.request
from pathlib import Path

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
PIPER_DIR = PROTOTYPE_DIR / "data" / "models" / "piper"

BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium"
FILES = [
    ("vi_VN-vais1000-medium.onnx", f"{BASE_URL}/vi_VN-vais1000-medium.onnx"),
    ("vi_VN-vais1000-medium.onnx.json", f"{BASE_URL}/vi_VN-vais1000-medium.onnx.json"),
]


def download_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100.0, downloaded * 100.0 / total_size)
        mb = downloaded / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        sys.stdout.write(f"\r[*] Đang tải: {mb:.1f}/{total_mb:.1f} MB ({percent:.1f}%)")
        sys.stdout.flush()


def download_piper_models(force: bool = False):
    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("📥 TẢI MÔ HÌNH PIPER ONNX TIẾNG VIỆT CHO LOCAL OFFLINE TTS")
    print(f"[*] Thư mục đích: {PIPER_DIR}")
    print("=" * 70)

    for filename, url in FILES:
        dest_path = PIPER_DIR / filename
        if dest_path.exists() and not force and dest_path.stat().st_size > 1000:
            print(f"[✓] File đã tồn tại: {filename} ({dest_path.stat().st_size / 1024:.1f} KB)")
            continue

        print(f"\n[+] Đang tải từ: {url}")
        print(f"    Lưu vào: {dest_path}")
        try:
            urllib.request.urlretrieve(url, str(dest_path), reporthook=download_progress)
            print(f"\n[SUCCESS] Đã tải xong: {filename}")
        except Exception as e:
            print(f"\n[!] Lỗi khi tải {filename}: {e}")
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except Exception:
                    pass
            return False

    print("\n" + "=" * 70)
    print("🎉 Hoàn tất! Mô hình Piper ONNX tiếng Việt đã sẵn sàng phục vụ Offline TTS.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    force_download = "--force" in sys.argv
    download_piper_models(force=force_download)
