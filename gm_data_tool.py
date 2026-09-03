"""Thu thập các ván thắng của GM từ kho PGN The Week in Chess.

Mỗi archive ZIP chỉ tồn tại trong thư mục tạm trong lúc xử lý và được xóa
ngay sau đó. Tổng dữ liệu đầu ra mặc định bị chặn ở 4 GiB.
"""

import argparse
import hashlib
import json
import re
import tempfile
import unicodedata
import urllib.request
import zipfile
from pathlib import Path


ARCHIVE_PAGE = "https://theweekinchess.com/twic"
ZIP_TEMPLATE = "https://theweekinchess.com/zips/twic{issue}g.zip"
DEFAULT_MAX_BYTES = 4 * 1024 * 1024 * 1024
USER_AGENT = "CAISSA-JEPA research dataset builder/1.0"


def download_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def find_latest_issue():
    html = download_bytes(ARCHIVE_PAGE).decode("utf-8", errors="replace")
    issues = [
        int(value)
        for value in re.findall(r"twic(\d+)g\.zip", html, re.IGNORECASE)
    ]

    if not issues:
        raise RuntimeError("Không tìm thấy số TWIC mới nhất")

    return max(issues)


def split_games(pgn_text):
    starts = [
        match.start()
        for match in re.finditer(r"(?m)^\s*\[Event\s+\"", pgn_text)
    ]

    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(pgn_text)
        game = pgn_text[start:end].strip()

        if game:
            yield game + "\n"


def parse_headers(game_text):
    return {
        key: value
        for key, value in re.findall(
            r'^\s*\[([A-Za-z0-9_]+)\s+"((?:\\.|[^"\\])*)"\]\s*$',
            game_text,
            re.MULTILINE,
        )
    }


def is_exact_gm(title):
    return re.search(r"(?:^|\s)GM(?:\s|$)", title.strip(), re.IGNORECASE) is not None


def select_winning_gm(headers):
    result = headers.get("Result", "")

    if result == "1-0" and is_exact_gm(headers.get("WhiteTitle", "")):
        return headers.get("White", "Unknown")

    if result == "0-1" and is_exact_gm(headers.get("BlackTitle", "")):
        return headers.get("Black", "Unknown")

    return None


def safe_name(value, max_length=70):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_value)
    ascii_value = ascii_value.strip("._-")
    return (ascii_value or "Unknown")[:max_length]


def load_state(state_path):
    if not state_path.exists():
        return {"hashes": [], "issues": []}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"hashes": [], "issues": []}


def save_state(state_path, hashes, issues):
    state_path.write_text(
        json.dumps(
            {"hashes": sorted(hashes), "issues": sorted(issues)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def current_output_size(output_dir):
    return sum(
        path.stat().st_size
        for path in output_dir.glob("*.txt")
        if path.is_file()
    )


def build_file_content(game_text, headers, winner, issue):
    white = headers.get("White", "Unknown")
    black = headers.get("Black", "Unknown")
    summary = (
        f"Player 1: {white}\n"
        f"Player 2: {black}\n"
        f"Winner: {winner}\n"
        f"TWIC issue: {issue}\n\n"
    )
    return (summary + game_text).encode("utf-8")


def process_archive(issue, output_dir, hashes, byte_limit, used_bytes):
    url = ZIP_TEMPLATE.format(issue=issue)

    with tempfile.TemporaryDirectory(prefix=f"caissa_twic_{issue}_") as temp_dir:
        zip_path = Path(temp_dir) / f"twic{issue}g.zip"
        zip_path.write_bytes(download_bytes(url))

        with zipfile.ZipFile(zip_path) as archive:
            pgn_names = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".pgn")
            ]

            if not pgn_names:
                raise RuntimeError(f"TWIC {issue} không chứa PGN")

            for pgn_name in pgn_names:
                pgn_text = archive.read(pgn_name).decode(
                    "utf-8-sig",
                    errors="replace",
                )

                for game_text in split_games(pgn_text):
                    headers = parse_headers(game_text)
                    winner = select_winning_gm(headers)

                    if winner is None:
                        continue

                    digest = hashlib.sha256(game_text.encode("utf-8")).hexdigest()

                    if digest in hashes:
                        continue

                    content = build_file_content(game_text, headers, winner, issue)

                    if used_bytes + len(content) > byte_limit:
                        return used_bytes, True, 0

                    white = safe_name(headers.get("White", "Unknown"))
                    black = safe_name(headers.get("Black", "Unknown"))
                    winner_name = safe_name(winner)
                    file_name = (
                        f"{white}__vs__{black}__winner-{winner_name}__"
                        f"{digest[:12]}.txt"
                    )
                    (output_dir / file_name).write_bytes(content)
                    hashes.add(digest)
                    used_bytes += len(content)

    return used_bytes, False, 1


def main():
    parser = argparse.ArgumentParser(
        description="Tải tuần tự TWIC và giữ riêng các ván bên thắng là GM.",
    )
    parser.add_argument("--output", default="gm_games")
    parser.add_argument("--latest", type=int, default=None)
    parser.add_argument(
        "--oldest",
        type=int,
        default=1200,
        help="Số issue cũ nhất cần thử (mặc định 1200)",
    )
    parser.add_argument(
        "--max-gb",
        type=float,
        default=4.0,
        help="Dung lượng tối đa của các file TXT đầu ra",
    )
    arguments = parser.parse_args()

    output_dir = Path(arguments.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "download_state.json"
    state = load_state(state_path)
    hashes = set(state.get("hashes", []))
    completed_issues = set(int(item) for item in state.get("issues", []))
    latest = arguments.latest or find_latest_issue()
    byte_limit = min(DEFAULT_MAX_BYTES, int(arguments.max_gb * 1024 ** 3))
    used_bytes = current_output_size(output_dir)

    print(f"Nguồn: {ARCHIVE_PAGE}")
    print(f"Khoảng TWIC: {latest} xuống {arguments.oldest}")
    print(f"Giới hạn: {byte_limit / 1024 ** 3:.2f} GiB")

    for issue in range(latest, arguments.oldest - 1, -1):
        if issue in completed_issues:
            continue

        try:
            used_bytes, full, completed = process_archive(
                issue,
                output_dir,
                hashes,
                byte_limit,
                used_bytes,
            )

            if completed:
                completed_issues.add(issue)

            save_state(state_path, hashes, completed_issues)
            print(
                f"TWIC {issue}: {len(hashes)} ván | "
                f"{used_bytes / 1024 ** 2:.1f} MiB"
            )

            if full:
                print("Đã đạt giới hạn dữ liệu; dừng an toàn.")
                break
        except Exception as error:
            print(f"TWIC {issue}: bỏ qua vì {error}")

    print("Hoàn tất. Import các file TXT bằng nút IMPORT PGN trong app.")
    print("Lưu ý: TWIC ghi rõ dữ liệu miễn phí cho mục đích cá nhân.")


if __name__ == "__main__":
    main()
