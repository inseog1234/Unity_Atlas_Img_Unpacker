from __future__ import annotations

from src.domain.entities import SpriteRecord


class SpriteRecordFactory:
    REQUIRED_KEYS = {
        "sid",
        "sx",
        "sy",
        "sxr",
        "syr",
        "swidth",
        "sheight",
        "scollectionname",
        "spath",
        "sfilpped",
    }

    def create_many(self, raw: dict) -> list[SpriteRecord]:
        missing = self.REQUIRED_KEYS - set(raw.keys())
        if missing:
            raise ValueError(f"SpriteInfo.json 필수 키 누락: {sorted(missing)}")

        count = len(raw["spath"])
        records: list[SpriteRecord] = []

        for key in self.REQUIRED_KEYS:
            if len(raw[key]) != count:
                raise ValueError(f"배열 길이가 서로 다릅니다: {key}")

        for index in range(count):
            records.append(
                SpriteRecord(
                    sid=int(raw["sid"][index]),
                    sx=int(raw["sx"][index]),
                    sy=int(raw["sy"][index]),
                    sxr=int(raw["sxr"][index]),
                    syr=int(raw["syr"][index]),
                    swidth=int(raw["swidth"][index]),
                    sheight=int(raw["sheight"][index]),
                    scollectionname=str(raw["scollectionname"][index]),
                    spath=str(raw["spath"][index]).replace("\\", "/"),
                    sfilpped=bool(raw["sfilpped"][index]),
                )
            )

        return records
