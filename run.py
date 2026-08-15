#!/usr/bin/env python3
"""
Quick-start helper script.
Usage: python run.py [seed|api|demo]
"""
import sys
import asyncio
import subprocess


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "api"

    if cmd == "seed":
        from backend.database.seed import seed
        asyncio.run(seed())

    elif cmd == "demo":
        from backend.ml.water_equity import run_sample_scenario
        result = run_sample_scenario(0.18)
        print(result.summary)
        for a in result.allocations:
            print(f"  {a.farmer_id} ({a.reach_type.value:6}): "
                  f"{a.allocated_water:6.1f} / {a.expected_water:6.1f} m³  "
                  f"fairness={a.fairness_score:.2%}  {a.notes}")

    elif cmd == "api":
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
        ])

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python run.py [seed|api|demo]")


if __name__ == "__main__":
    main()
