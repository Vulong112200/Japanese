"""python -m hub [serve|import|check-online|report]"""
import json
import sys

from .db import connect


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "serve"
    if cmd == "serve":
        import uvicorn
        uvicorn.run("hub.api:app", host="127.0.0.1", port=8000)
    elif cmd == "import":
        from .ingestion import pipeline
        print(json.dumps(pipeline.run_all(connect()), ensure_ascii=False, indent=1))
    elif cmd == "check-online":
        from .ingestion import pipeline
        conn = connect()
        pipeline.register_online(conn)
        for r in pipeline.check_online(conn):
            print(f"{r['source_id']:<20} {r['access_status']:<14} {r['detail']}")
    elif cmd == "report":
        from .reports import write_reports
        print("\n".join(write_reports(connect())))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
