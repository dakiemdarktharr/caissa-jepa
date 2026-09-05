"""Protocol fixture only; not a chess engine and never used by the application."""
import sys

for line in sys.stdin:
    command = line.strip()
    if command == "uci":
        print("id name Test referee", flush=True)
        print("uciok", flush=True)
    elif command == "isready":
        print("readyok", flush=True)
    elif command.startswith("go "):
        print("info depth 4 nodes 120 nps 800 score cp 25 wdl 200 700 100 pv e2e4", flush=True)
        print("bestmove e2e4", flush=True)
    elif command == "quit":
        break
