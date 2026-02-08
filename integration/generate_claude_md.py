#!/usr/bin/env python3
"""
Generate CLAUDE.md from template by filling in placeholders.
Reads values from config.env and command-line overrides.
"""

import os
import re
import sys
import argparse


def load_env_file(path: str) -> dict:
    """Load key=value pairs from an env file."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                value = os.path.expandvars(value)
                env[key.strip()] = value
    return env


def fill_template(template_text: str, values: dict) -> str:
    """Replace {{PLACEHOLDER}} markers with values."""
    def replacer(match):
        key = match.group(1)
        if key in values:
            return values[key]
        return match.group(0)  # Leave unfilled placeholders as-is

    return re.sub(r"\{\{(\w+)\}\}", replacer, template_text)


def main():
    parser = argparse.ArgumentParser(
        description="Generate CLAUDE.md from template"
    )
    parser.add_argument("--template", default=None,
                        help="Path to template file")
    parser.add_argument("--output", default=None,
                        help="Output path (default: stdout)")
    parser.add_argument("--config", default=None,
                        help="Path to config.env")
    parser.add_argument("--set", action="append", default=[],
                        metavar="KEY=VALUE",
                        help="Set a placeholder value (can be repeated)")

    args = parser.parse_args()

    sak_home = os.environ.get("SAK_HOME",
                              os.path.expanduser("~/.sovereign-ai"))

    # Load config
    config_path = args.config or os.path.join(sak_home, "config.env")
    values = load_env_file(config_path)

    # Map config values to template placeholders
    values["SAK_HOME"] = values.get("SAK_HOME", sak_home)
    values["AI_NAME"] = values.get("SAK_AI_NAME", "Assistant")
    values["USER_NAME"] = values.get("SAK_USER_NAME", "User")

    # Apply command-line overrides
    for override in args.set:
        if "=" in override:
            key, _, val = override.partition("=")
            values[key.strip()] = val.strip()

    # Find template
    template_path = args.template
    if not template_path:
        template_path = os.path.join(sak_home,
                                     "identity/templates/CLAUDE.md.template")
        if not os.path.exists(template_path):
            template_path = os.path.join(os.path.dirname(__file__),
                                         "../identity/templates/CLAUDE.md.template")

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, "r") as f:
        template_text = f.read()

    result = fill_template(template_text, values)

    # Check for unfilled placeholders
    unfilled = re.findall(r"\{\{(\w+)\}\}", result)
    if unfilled:
        print(f"Warning: Unfilled placeholders: {', '.join(set(unfilled))}",
              file=sys.stderr)
        print(f"Use --set KEY=VALUE to fill them.", file=sys.stderr)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Generated: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
