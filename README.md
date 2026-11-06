# pa-permission-self-reviewer
Automates permission reviews by generating reports that highlight potential risks and inconsistencies based on organizational policies and best practices. Provides actionable recommendations for permission adjustments, one per issue found. The review covers directories as well as files, and the saved report holds the same rows as the console table in plain text. Missing input, a missing or invalid config, a failed report write, and a review that checks nothing all exit 1. The report file must not be written inside the reviewed tree. - Focused on Tools for analyzing and assessing file system permissions

## Install
`git clone https://github.com/ShadowGuard-AI/pa-permission-self-reviewer`
`cd pa-permission-self-reviewer`
`pip install -r requirements.txt`

## Usage
`python3 main.py --path <path> [--config config.json] [--report permission_report.txt]`

A sample run over a small tree with a config enabling both checks flagged a world-writable file and wrote the same rows to the report file, exiting 0.

## Parameters
- `-h`: Show help message and exit
- `--path` (required): The path to the directory or file to analyze.
- `--config` (optional, default `config.json`): Path to the configuration file. Defaults to config.json. The config file itself must exist: a run with no config file exits 1 even though the flag has a default. It enables checks with keys such as `check_world_writable` and `check_executable`.
- `--report` (optional, default `permission_report.txt`): Path to the report file. Defaults to permission_report.txt

## License
Licensed under the MIT License, see LICENSE.
