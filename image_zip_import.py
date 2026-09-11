import hashlib
import json
import re
import stat
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from PySide6.QtCore import QObject, Signal, Slot


class zipimageimportworker(QObject):
    tien_do = Signal(object)
    ket_qua = Signal(object)
    hoan_tat = Signal()

    allowed_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff",
    }

    def __init__(self, zip_paths, dataset_path, stop_event):
        super().__init__()
        self.zip_paths = [Path(path) for path in zip_paths]
        self.dataset_path = Path(dataset_path)
        self.image_root = self.dataset_path / "images"
        self.manifest_path = self.image_root / "image_import_manifest.json"
        self.stop_event = stop_event
        self.max_total_bytes = 4 * 1024 * 1024 * 1024
        self.max_member_bytes = 512 * 1024 * 1024
        self.max_files = 250000

    @staticmethod
    def safe_member_path(member_name):
        normalized = str(member_name).replace("\\", "/")
        candidate = PurePosixPath(normalized)
        if candidate.is_absolute() or len(candidate.parts) == 0:
            return None
        if any(part in ("", ".", "..") for part in candidate.parts):
            return None
        if ":" in candidate.parts[0]:
            return None
        if Path(candidate.name).suffix.lower() not in zipimageimportworker.allowed_extensions:
            return None
        return Path(*candidate.parts)

    @staticmethod
    def file_sha256(file_path):
        digest = hashlib.sha256()
        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def safe_archive_name(file_path):
        archive_name = re.sub(r"[^A-Za-z0-9._-]+", "_", file_path.stem)
        return archive_name[:80] or "archive"

    def _target_for(self, base_target, digest):
        target = base_target
        while target.exists():
            if self.file_sha256(target) == digest:
                return target, True
            target = target.with_name(
                f"{base_target.stem}_{digest[:12]}{base_target.suffix}"
            )
            base_target = target
        return target, False

    def _copy_member(self, archive, info, target, bytes_read):
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.part")
        digest = hashlib.sha256()
        member_bytes = 0
        try:
            with archive.open(info, "r") as source, open(temporary, "wb") as destination:
                while True:
                    if self.stop_event.is_set():
                        raise InterruptedError("ZIP image import cancelled")
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    member_bytes += len(chunk)
                    if member_bytes > self.max_member_bytes:
                        raise ValueError("image exceeds the 512 MiB per-file limit")
                    if bytes_read + member_bytes > self.max_total_bytes:
                        raise ValueError("ZIP import exceeds the 4 GiB batch limit")
                    digest.update(chunk)
                    destination.write(chunk)
            if info.file_size != member_bytes:
                raise ValueError("ZIP member size changed while it was being read")
            digest_text = digest.hexdigest()
            final_target, duplicate = self._target_for(target, digest_text)
            if duplicate:
                temporary.unlink(missing_ok=True)
                return member_bytes, True, digest_text, final_target
            temporary.replace(final_target)
            return member_bytes, False, digest_text, final_target
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _write_manifest(self, imports):
        self.image_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "updated_at": datetime.now().isoformat(),
            "dataset": str(self.image_root.resolve()),
            "imports": imports,
        }
        temporary = self.manifest_path.with_name(
            f".{self.manifest_path.name}.{uuid.uuid4().hex}.tmp"
        )
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(self.manifest_path)

    def _existing_imports(self):
        if not self.manifest_path.exists():
            return []
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            imports = payload.get("imports", [])
            return imports if isinstance(imports, list) else []
        except Exception:
            return []

    @Slot()
    def chay(self):
        stats = {
            "archives_seen": 0,
            "files_seen": 0,
            "imported": 0,
            "duplicates": 0,
            "skipped": 0,
            "errors": 0,
            "bytes_read": 0,
            "warnings": [],
        }
        import_records = []
        try:
            self.image_root.mkdir(parents=True, exist_ok=True)
            for zip_path in self.zip_paths:
                if self.stop_event.is_set():
                    break
                archive_record = {
                    "archive": str(zip_path.resolve()),
                    "started_at": datetime.now().isoformat(),
                    "imported": 0,
                    "duplicates": 0,
                    "skipped": 0,
                    "errors": 0,
                }
                try:
                    with zipfile.ZipFile(zip_path, "r") as archive:
                        stats["archives_seen"] += 1
                        archive_folder = self.image_root / self.safe_archive_name(zip_path)
                        for info in archive.infolist():
                            if self.stop_event.is_set():
                                break
                            if stats["files_seen"] >= self.max_files:
                                stats["warnings"].append("The 250,000-file safety limit was reached.")
                                break
                            stats["files_seen"] += 1
                            safe_path = self.safe_member_path(info.filename)
                            mode = (info.external_attr >> 16) & 0xFFFF
                            if info.is_dir() or stat.S_ISLNK(mode) or safe_path is None:
                                stats["skipped"] += 1
                                archive_record["skipped"] += 1
                                continue
                            if info.file_size <= 0:
                                stats["skipped"] += 1
                                archive_record["skipped"] += 1
                                continue
                            if info.file_size > self.max_member_bytes:
                                stats["skipped"] += 1
                                archive_record["skipped"] += 1
                                stats["warnings"].append(f"Skipped oversized image: {info.filename}")
                                continue
                            if stats["bytes_read"] + info.file_size > self.max_total_bytes:
                                stats["warnings"].append("The 4 GiB ZIP batch limit was reached.")
                                break
                            target = archive_folder / safe_path
                            try:
                                member_bytes, duplicate, digest, final_target = self._copy_member(
                                    archive, info, target, stats["bytes_read"]
                                )
                                stats["bytes_read"] += member_bytes
                                archive_record.setdefault("images", []).append({
                                    "path": str(final_target.relative_to(self.image_root)),
                                    "sha256": digest,
                                })
                                if duplicate:
                                    stats["duplicates"] += 1
                                    archive_record["duplicates"] += 1
                                else:
                                    stats["imported"] += 1
                                    archive_record["imported"] += 1
                            except InterruptedError:
                                raise
                            except Exception as error:
                                stats["errors"] += 1
                                archive_record["errors"] += 1
                                stats["warnings"].append(f"{info.filename}: {error}")
                            if stats["files_seen"] % 25 == 0:
                                self.tien_do.emit({**stats, "archive": zip_path.name})
                    archive_record["finished_at"] = datetime.now().isoformat()
                    import_records.append(archive_record)
                except InterruptedError:
                    archive_record["cancelled"] = True
                    import_records.append(archive_record)
                    break
                except Exception as error:
                    stats["errors"] += 1
                    archive_record["errors"] += 1
                    archive_record["error"] = str(error)
                    import_records.append(archive_record)
            self._write_manifest(self._existing_imports() + import_records)
            stats["cancelled"] = self.stop_event.is_set()
            stats["dataset_path"] = str(self.image_root.resolve())
            self.ket_qua.emit(stats)
        except Exception as error:
            stats["error"] = str(error)
            self.ket_qua.emit(stats)
        finally:
            self.hoan_tat.emit()