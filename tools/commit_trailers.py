"""Keep AI-attribution trailers out of commit messages.

Commits here are published under the maintainer's name. Agent tools append
"Co-Authored-By: Claude ..." and "Claude-Session: ..." lines by default; this
removes them before a commit is written and fails CI if one slips through.

    python tools/commit_trailers.py strip MSGFILE     # .githooks/commit-msg
    python tools/commit_trailers.py check REV_RANGE   # CI, e.g. origin/main..HEAD
"""
import re
import subprocess
import sys

TRAILER = re.compile(
    r"(?im)^(co-authored-by:[^\n]*(claude|anthropic)[^\n]*|claude-session:[^\n]*)\n?"
)


def strip(message):
    cleaned = TRAILER.sub("", message)
    return message if cleaned == message else cleaned.rstrip() + "\n"


def offenders(rev_range):
    log = subprocess.run(
        ["git", "log", "--format=%H%x00%B%x01", rev_range],
        check=True, capture_output=True, text=True,
    ).stdout
    found = []
    for entry in log.split("\x01"):
        if "\x00" not in entry:
            continue
        sha, body = entry.split("\x00", 1)
        if TRAILER.search(body):
            found.append(sha.strip())
    return found


def main(argv):
    if len(argv) == 3 and argv[1] == "strip":
        with open(argv[2], encoding="utf-8") as f:
            message = f.read()
        cleaned = strip(message)
        if cleaned != message:
            with open(argv[2], "w", encoding="utf-8") as f:
                f.write(cleaned)
            print("commit-msg: removed AI attribution trailers", file=sys.stderr)
        return 0
    if len(argv) == 3 and argv[1] == "check":
        bad = offenders(argv[2])
        for sha in bad:
            print(f"{sha}: commit message carries an AI attribution trailer")
        return 1 if bad else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
