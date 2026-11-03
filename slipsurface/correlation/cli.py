"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys

from . import APP_NAME, __version__

#: Default port of the local interface (the family counts up from 8777)
PORT = 8785


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="slipsurface-correlation",
        description="Soil parameters from laboratory and field tests (SPT, CPT(u), Vs) "
                    "through the correlations of the literature, with reports and project "
                    "files for SlipSurface IQ Settle and SlipSurface IQ Bearing.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    # Running the program with no subcommand means "web", so the top level
    # carries that subcommand's defaults: without them the bare `slipsurface-correlation`
    # would reach serve() with a Namespace that has no host, port or language.
    parser.set_defaults(host="127.0.0.1", port=PORT, lang="en", no_browser=False)
    sub = parser.add_subparsers(dest="command")

    web = sub.add_parser("web", help="start the interface in a browser")
    web.add_argument("--port", type=int, default=PORT)
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--lang", default="en", choices=["en", "tr"])
    web.add_argument("--no-browser", action="store_true")

    run = sub.add_parser("run", help="derive the parameters of a project file and print them")
    run.add_argument("project", help="path to a .correlation / .json project file")
    run.add_argument("-o", "--out", default=None,
                     help="write a report here (.pdf / .html / .docx) or the parameters (.csv)")
    run.add_argument("--lang", default="en", choices=["en", "tr"])

    export = sub.add_parser("export", help="write a SlipSurface IQ Settle or SlipSurface IQ Bearing project "
                                           "with the derived parameters")
    export.add_argument("project", help="path to a .correlation / .json project file")
    export.add_argument("target", choices=["settle", "bearing"])
    export.add_argument("-o", "--out", default=None,
                        help="where to write it (default: project.settle / project.bearing)")

    example = sub.add_parser("example", help="write a starter project file")
    example.add_argument("-o", "--out", default="project.correlation")

    args = parser.parse_args(argv)
    command = args.command or "web"
    try:
        return _dispatch(command, args)
    except (ValueError, RuntimeError, OSError) as exc:
        # The analysis refuses impossible input with a sentence worth reading
        # (a profile without layers, a negative water content, an unreadable
        # project file). A traceback would bury it, so only unexpected
        # failures keep theirs.
        print(f"{APP_NAME}: {exc}", file=sys.stderr)
        return 1


def _dispatch(command: str, args) -> int:
    """Runs one command; raises on anything that goes wrong."""
    if command == "web":
        from .web.server import serve
        serve(host=args.host, port=args.port, open_browser=not args.no_browser,
              lang=args.lang)
        return 0

    from . import forms

    if command == "example":
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(forms.project_file(forms.defaults()), fh, indent=2, ensure_ascii=False)
        print(args.out)
        return 0

    with open(args.project, encoding="utf-8") as fh:
        data = json.load(fh)

    from .web.session import Session
    session = Session(lang=getattr(args, "lang", "en"))
    values = session.load_project(data)["values"]
    result = session.analyse(values)

    if command == "export":
        out = args.out or f"project.{args.target}"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(session.export(args.target), fh, indent=2, ensure_ascii=False)
        print(out)
        return 0

    print(result["text"])
    if args.out:
        fmt = args.out.lower().rsplit(".", 1)[-1]
        if fmt == "csv":
            print(session.export_csv(args.out))
        else:
            print(session.report(fmt if fmt in ("pdf", "html", "docx") else "pdf", args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
