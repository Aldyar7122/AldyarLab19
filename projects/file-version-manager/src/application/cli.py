"""JSON-friendly console commands. Only declared actions are callable."""

import argparse
import inspect
import json
import sqlite3
import sys


def run(factory, actions, default_store):
    parser = argparse.ArgumentParser(
        description="SCM practical work console. Values use key=value; JSON types are accepted."
    )
    parser.add_argument("--store", default=default_store, help="SQLite file or application directory")
    parser.add_argument("action", choices=actions)
    parser.add_argument("parameters", nargs="*", help="key=value; e.g. quantity=5 approve=true")
    parser.add_argument("--input", help="UTF-8 JSON object containing keyword arguments")
    args = parser.parse_args()
    app = None
    try:
        values = {}
        if args.input:
            with open(args.input, encoding="utf-8-sig") as stream:
                values = json.load(stream)
            if not isinstance(values, dict):
                raise ValueError("--input must contain a JSON object")
        for parameter in args.parameters:
            if "=" not in parameter:
                raise ValueError("arguments must use key=value")
            key, value = parameter.split("=", 1)
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
            values[key] = value
        app = factory(args.store)
        method = getattr(app, args.action)
        inspect.signature(method).bind(**values)
        result = method(**values)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get("passed") is False:
            return 1
    except (ValueError, TypeError, OSError, sqlite3.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    finally:
        if app is not None and hasattr(app, "close"):
            app.close()
    return 0
