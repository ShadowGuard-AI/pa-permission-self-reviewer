# pa-permission-self-reviewer
Automates permission reviews by generating reports that highlight potential risks and inconsistencies based on organizational policies and best practices. Provides actionable recommendations for permission adjustments, one per issue found. The review covers directories as well as files, and the saved report holds the same rows as the console table in plain text. Missing input, a missing or invalid config, a failed report write, and a review that checks nothing all exit 1. The report file must not be written inside the reviewed tree. - Focused on Tools for analyzing and assessing file system permissions

## Install
`git clone https://github.com/ShadowStrikeHQ/pa-permission-self-reviewer`

## Usage
`./pa-permission-self-reviewer [params]`

## Parameters
- `-h`: Show help message and exit
- `--path`: The path to the directory or file to analyze.
- `--config`: Path to the configuration file. Defaults to config.json
- `--report`: Path to the report file. Defaults to permission_report.txt

## License
Copyright (c) ShadowStrikeHQ
