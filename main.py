import argparse
import logging
import os
import stat
import json
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command line interface.
    """
    parser = argparse.ArgumentParser(description="Automates permission reviews by generating reports that highlight potential risks and inconsistencies.",
                                     epilog="Example usage: python3 main.py --path /path/to/analyze --config config.json")

    parser.add_argument("--path", required=True, help="The path to the directory or file to analyze.")
    parser.add_argument("--config", required=False, default="config.json", help="Path to the configuration file. Defaults to config.json")
    parser.add_argument("--report", required=False, default="permission_report.txt", help="Path to the report file. Defaults to permission_report.txt")

    return parser.parse_args()

def load_config(config_path):
    """Loads the configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in configuration file: {config_path}")
        raise ValueError(f"Invalid JSON in configuration file: {config_path}")

def check_permissions(path, config, report_file):
    """
    Checks the permissions of files and directories against the configuration.
    Returns the number of entries reviewed inside the path (files and
    subdirectories; the root directory row itself is not counted).
    Raises on a failed report write so the caller can exit non-zero.
    """
    console = Console()
    table = Table(title="Permission Review Report")
    table.add_column("File/Directory")
    table.add_column("Permissions", style="cyan")
    table.add_column("Owner", style="magenta")
    table.add_column("Group", style="green")
    table.add_column("Issues", style="red")
    table.add_column("Recommendation")

    rows = []
    reviewed = 0
    if os.path.isfile(path):
        process_entry(path, config, table, rows)
        # The count is the callers honesty check: a single file counts as one, and a directory counts its contents but not the root row that is also printed. An empty directory reviews zero entries and main refuses it instead of saving a header only report as success.
        reviewed = 1
    elif os.path.isdir(path):
        process_entry(path, config, table, rows)
        for root, dirs, files in os.walk(path):
            for name in dirs:
                process_entry(os.path.join(root, name), config, table, rows)
                reviewed += 1
            for name in files:
                process_entry(os.path.join(root, name), config, table, rows)
                reviewed += 1
    else:
        logging.error(f"Path is not a file or directory: {path}")
        raise ValueError(f"Path is not a file or directory: {path}")

    console.print(table)
    write_report(rows, report_file)
    console.print(f"\nReport saved to: {report_file}")
    return reviewed

def process_entry(full_path, config, table, rows=None):
    """
    Processes a single file or directory entry.
    """
    try:
        file_stats = os.stat(full_path)
        permissions = stat.filemode(file_stats.st_mode)
        owner_uid = file_stats.st_uid
        group_gid = file_stats.st_gid
        owner = get_user_name(owner_uid)
        group = get_group_name(group_gid)

        issues = []
        recommendations = []
        # Both checks are opt in through the config file. A config that names neither key produces a report where every row says no issues, and that report looks the same as one from a tree that was actually checked and clean.
        if config.get("check_world_writable") and (file_stats.st_mode & stat.S_IWOTH):
            issues.append("World writable permission detected")
            recommendations.append("Remove the other-write permission (chmod o-w).")
        # Index 3 of the filemode string is the owner execute position, after the type character and owner read and write. This check therefore flags owner execute only, and a file that is group or world executable but not owner executable passes it clean.
        if config.get("check_executable") and permissions[3] == 'x':
            issues.append("Executable permission detected")
            recommendations.append("Remove the owner execute permission if this entry does not need to run (chmod u-x).")

        issue_text = ", ".join(issues) if issues else "No issues found"
        rec_text = " ".join(recommendations) if recommendations else "No change needed."
        table.add_row(full_path, permissions, owner, group, issue_text, rec_text)
        if rows is not None:
            rows.append((full_path, permissions, owner, group, issue_text, rec_text))

    # A failed stat still gets a row and still counts toward the reviewed total below, because process_entry returns normally. A tree full of broken links can therefore produce a complete looking review built mostly of error rows.
    except OSError as e:
        logging.error(f"Error getting file stats for {full_path}: {e}")
        table.add_row(full_path, "Error", "Error", "Error", "Error getting file stats", "Check that the entry exists and is readable.")
        if rows is not None:
            rows.append((full_path, "Error", "Error", "Error", "Error getting file stats", "Check that the entry exists and is readable."))

def get_user_name(uid):
    """Gets the username from a UID."""
    try:
        import pwd
        return pwd.getpwuid(uid).pw_name
    except ImportError:
        logging.warning("pwd module not available. Returning UID instead of username.")
        return str(uid)
    except KeyError:
        logging.warning(f"User with UID {uid} not found.")
        return str(uid)
    except Exception as e:
        logging.error(f"Error getting username for UID {uid}: {e}")
        return str(uid)

def get_group_name(gid):
    """Gets the group name from a GID."""
    try:
        import grp
        return grp.getgrgid(gid).gr_name
    except ImportError:
        logging.warning("grp module not available. Returning GID instead of group name.")
        return str(gid)
    except KeyError:
        logging.warning(f"Group with GID {gid} not found.")
        return str(gid)
    except Exception as e:
        logging.error(f"Error getting group name for GID {gid}: {e}")
        return str(gid)

def write_report(rows, report_file):
    """Writes the report rows as plain text lines to the report file."""
    try:
        with open(report_file, 'w') as f:
            f.write("Permission Review Report\n")
            for path, permissions, owner, group, issues, recommendation in rows:
                f.write(f"{path} | {permissions} | {owner} | {group} | {issues} | Recommendation: {recommendation}\n")
    except IOError as e:
        logging.error(f"Error writing report to file: {e}")
        raise IOError(f"Error writing report to file: {e}")

def main():
    """
    Main function to execute the permission self-reviewer.
    Returns 0 on success and 1 on every failure shape.
    """
    args = setup_argparse()

    # Input validation
    if not os.path.exists(args.path):
        logging.error(f"Path does not exist: {args.path}")
        print(f"Error: Path does not exist: {args.path}")
        return 1

    report_resolved = os.path.realpath(args.report)
    path_resolved = os.path.realpath(args.path)
    if os.path.isfile(args.path) and report_resolved == path_resolved:
        print("Error: Report file must not overwrite the reviewed file.")
        logging.error("Report file equals the reviewed file.")
        return 1
    # Writing the report inside the tree it reviews would add the report itself to the walk on the next run and, in a longer run, could race the walk in this one. The trailing separator matters: without it a sibling folder whose name starts with the same letters would be refused by mistake.
    if os.path.isdir(args.path) and (report_resolved == path_resolved or report_resolved.startswith(path_resolved + os.sep)):
        print("Error: Report file must not be written inside the reviewed tree.")
        logging.error("Report file lies inside the reviewed tree.")
        return 1

    try:
        # The config is required in practice even though the flag has a default. Run this in a folder with no config.json and it stops here, which surprises people because the help text reads as if the file were optional.
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    try:
        reviewed = check_permissions(args.path, config, args.report)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"Error: {e}")
        return 1

    if reviewed == 0:
        print("Error: No files or directories were reviewed. Nothing was checked.")
        logging.error("Empty review: no entries reviewed.")
        return 1

    return 0


if __name__ == "__main__":
    # Example Usage
    # python3 main.py --path /path/to/analyze --config config.json --report output.txt
    # Create a dummy config.json
    # cat > config.json <<EOL
    # {
    #   "check_world_writable": true,
    #   "check_executable": true
    # }
    # EOL
    import sys
    sys.exit(main())
