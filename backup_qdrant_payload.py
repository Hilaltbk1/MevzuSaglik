import json
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from backend.database.crud import _get_qdrant_client, COLLECTION_NAME


def main():
    client = _get_qdrant_client()
    os.makedirs("backups", exist_ok=True)
    path = f"backups/qdrant_payload_{datetime.now():%Y%m%d_%H%M}.jsonl"
    n = 0
    offset = None
    with open(path, "w", encoding="utf-8") as f:
        while True:
            points, offset = client.scroll(COLLECTION_NAME, limit=256, offset=offset,
                                           with_payload=True, with_vectors=False)
            for p in points:
                f.write(json.dumps({"id": p.id, "payload": p.payload}, ensure_ascii=False) + "\n")
                n += 1
            if offset is None:
                break
    print(f"{n} parça yedeklendi -> {path}")
    print("Qdrant'taki toplam parça:", client.count(COLLECTION_NAME).count)


if __name__ == "__main__":
    main()