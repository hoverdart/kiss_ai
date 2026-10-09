#!/usr/bin/env python
# Author: Koushik Sen (ksen@berkeley.edu)
# Contributors:
# Koushik Sen (ksen@berkeley.edu)
# add your name here
"""Run a SEA in this process: no kiss-web daemon, no UI.

    uv run python scripts/run_sea_standalone.py <sea_path> "<task>" [--work-dir DIR] [-m MODEL] [-b USD]

Loads the SEA exactly as the daemon does (``sea_layers`` + ``evaluate_sea``)
and runs ``SorcarAgent.run`` with the SEA's settings, prompt and hooks.
Needs only an API key in the environment (``$KISS_HOME/api_keys.env`` is
loaded).  Prints the agent's YAML result; exits 0 on success, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("sea_path", help="path of the SEA file (<name>/<name>_sea.py)")
    parser.add_argument("task", help="the task text the SEA's prompt(task) receives")
    parser.add_argument("--work-dir", default="", help="working directory (default: cwd)")
    parser.add_argument("-m", "--model", default="", help="model (SEA 'model' setting wins)")
    parser.add_argument("-b", "--max-budget", type=float, default=None, help="USD budget")
    args = parser.parse_args()

    from kiss.core.vscode_config import load_api_keys_readonly

    load_api_keys_readonly()

    from kiss.agents.sorcar.sea_commands import evaluate_sea, sea_layers
    from kiss.agents.sorcar.sorcar_agent import SorcarAgent

    sea_path = Path(args.sea_path).resolve()
    run = evaluate_sea(sea_layers(sea_path), args.task)
    s = run.settings
    work_dir = s.get("work_dir") or args.work_dir or os.getcwd()
    result = SorcarAgent(sea_path.stem).run(
        model_name=s.get("model") or args.model or None,
        prompt_template=run.prompt,
        work_dir=work_dir,
        max_budget=s.get("max_budget", args.max_budget),
        tool_profile=s.get("tool_profile", ""),
        web_tools=bool(s.get("use_web_tools", False)),
        use_memory=s.get("use_memory"),
        model_config=s.get("model_config"),
        docker_image=s.get("docker_image") or None,
        system_prompt_hook=run.system_prompt_hook,
        tools_hook=run.tools_hook,
        llm_call_hook=run.llm_call_hook,
        tool_call_hook=run.tool_call_hook,
        verbose=sys.stdout.isatty(),
    )
    if not sys.stdout.isatty():
        print(result)
    try:
        return 0 if yaml.safe_load(result).get("success") else 1
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
