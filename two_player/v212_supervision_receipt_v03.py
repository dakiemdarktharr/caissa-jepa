"""Versioned accepted-receipt boundary requiring both local counter samples.

This draft boundary delegates evidence validation and classification to v02,
but rejects an absent counter pair. It does not collect evidence or integrate
with the request adapter or a live service.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from two_player import v212_supervision_receipt_v02 as v02


SCHEMA = "caissa.v212.supervision-receipt.v03"
ASSEMBLER_VERSION = "v03"


ReceiptError = v02.ReceiptError


def assemble_receipt(*, requested_unit: str, request_boot_id: str,
                     request_started_monotonic_us: int,
                     worker_snapshot: Mapping[str, Any],
                     manager_snapshot: Mapping[str, Any],
                     journal_records: Sequence[Mapping[str, Any]],
                     events_before: Mapping[str, Any] | None = None,
                     events_after: Mapping[str, Any] | None = None
                     ) -> dict[str, Any]:
    """Assemble v03 only when both worker-local counter samples are present."""
    if events_before is None or events_after is None:
        raise ReceiptError("v03 requires both counter snapshots")

    receipt = v02.assemble_receipt(
        requested_unit=requested_unit,
        request_boot_id=request_boot_id,
        request_started_monotonic_us=request_started_monotonic_us,
        worker_snapshot=worker_snapshot,
        manager_snapshot=manager_snapshot,
        journal_records=journal_records,
        events_before=events_before,
        events_after=events_after,
    )
    try:
        source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError as exc:
        raise ReceiptError(
            "v03 assembler source digest unavailable; do not persist receipt"
        ) from exc

    receipt["schema"] = SCHEMA
    receipt["assembler"] = {
        "version": ASSEMBLER_VERSION,
        "source_sha256": source_hash,
        "delegated_assembler": dict(receipt["assembler"]),
    }
    return receipt
