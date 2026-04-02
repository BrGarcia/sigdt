#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from sqlmodel import Session, select

from app.database import engine
from app.models import DiretivaTecnica


COLUMN_ORDER = ["ELT", "ELE", "MOT", "CEL", "HID", "EST", "ARM", "TOD"]
SPECIALTY_MAP = {
    "ELT": "ELT",
    "ELE": "ELE",
    "MOT": "MOT",
    "CEL": "CEL",
    "HID": "HID",
    "EST": "EST",
    "ARM": "ARM",
    "TOD": "TODAS",
}


def normalize_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def split_line(line: str) -> List[str]:
    if "\t" in line:
        return [part.strip() for part in line.split("\t")]
    if ";" in line:
        return [part.strip() for part in line.split(";")]
    if "," in line:
        return next(csv.reader([line], skipinitialspace=True))
    return re.split(r"\s+", line.strip())


@dataclass
class ParsedDirective:
    code: str
    flags: Dict[str, int] = field(default_factory=dict)

    def merge(self, other_flags: Dict[str, int]) -> None:
        for key in COLUMN_ORDER:
            self.flags[key] = max(self.flags.get(key, 0), other_flags.get(key, 0))

    def to_especialidade(self) -> str:
        if self.flags.get("TOD", 0):
            return "TODAS"
        values = [SPECIALTY_MAP[key] for key in COLUMN_ORDER if key != "TOD" and self.flags.get(key, 0)]
        return ";".join(values)


def parse_file(path: Path) -> Dict[str, ParsedDirective]:
    directives: Dict[str, ParsedDirective] = {}

    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = split_line(line)
            if line_number == 1 and parts and normalize_code(parts[0]) == "DIRETIVATECNICA":
                continue

            if len(parts) < 1 + len(COLUMN_ORDER):
                raise ValueError(
                    f"Linha {line_number} invalida: esperado codigo + {len(COLUMN_ORDER)} colunas, recebido {len(parts)}."
                )

            code = normalize_code(parts[0])
            flags = {}
            for index, column in enumerate(COLUMN_ORDER, start=1):
                value = parts[index].strip()
                if value not in {"0", "1"}:
                    raise ValueError(f"Linha {line_number} invalida: coluna {column} deve ser 0 ou 1, recebeu {value!r}.")
                flags[column] = int(value)

            if code not in directives:
                directives[code] = ParsedDirective(code=code, flags=flags)
            else:
                directives[code].merge(flags)

    return directives


def build_lookup(rows: Iterable[DiretivaTecnica]) -> Dict[str, DiretivaTecnica]:
    lookup: Dict[str, DiretivaTecnica] = {}
    for row in rows:
        lookup[normalize_code(row.codigo_simplificado)] = row
        lookup.setdefault(normalize_code(row.codigo), row)
    return lookup


def update_directives(file_path: Path, dry_run: bool) -> int:
    parsed = parse_file(file_path)

    with Session(engine) as session:
        directives = session.exec(select(DiretivaTecnica)).all()
        lookup = build_lookup(directives)

        updated = 0
        missing: List[str] = []

        for code, parsed_row in parsed.items():
            row = lookup.get(code)
            if row is None:
                missing.append(code)
                continue

            new_value = parsed_row.to_especialidade() or None
            if row.especialidade == new_value:
                continue

            row.especialidade = new_value
            row.updated_at = datetime.now(timezone.utc)
            session.add(row)
            updated += 1

        if dry_run:
            session.rollback()
        else:
            session.commit()

    print(f"Diretivas lidas: {len(parsed)}")
    print(f"Diretivas atualizadas: {updated}")
    print(f"Diretivas nao encontradas: {len(missing)}")
    if missing:
        print("Codigos nao encontrados:")
        for code in missing:
            print(f" - {code}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atualiza a especialidade das diretivas tecnicas a partir de um arquivo tabular."
    )
    parser.add_argument(
        "--file",
        default="script_diretiva.txt",
        help="Caminho para o arquivo de entrada. Padrao: script_diretiva.txt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Processa e mostra o resumo sem persistir alteracoes.",
    )
    args = parser.parse_args()

    return update_directives(Path(args.file), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
