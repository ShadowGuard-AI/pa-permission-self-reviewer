import argparse
import logging
import os
import stat
import json
from rich.console import Console
from rich.table import Table
from pathspec import PathSpec

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command line interface.
    """
    parser = argparse.ArgumentParser(description="Automates permission reviews by generating reports that highlight potential risks and inconsistencies.",
                                     epilog="Example usage: python pa_permission_self_reviewer.py --path /path/to/analyze --config config.json")

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
    """
    console = Console()
    table = Table(title="Permission Review Report")
    table.add_column("File/Directory")
    table.add_column("Permissions", style="cyan")
    table.add_column("Owner", style="magenta")
    table.add_column("Group", style="green")
    table.add_column("Issues", style="red")

    try:
        if os.path.isfile(path):
             process_entry(path, config, table)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    process_entry(full_path, config, table)
        else:
            logging.error(f"Path is not a file or directory: {path}")
            raise ValueError(f"Path is not a file or directory: {path}")

        console.print(table)
        write_report(table, report_file)
        console.print(f"\nReport saved to: {report_file}")

    except Exception as e:
        logging.error(f"Error processing file/directory: {e}")
        console.print_exception(show_locals=True)

def process_entry(full_path, config, table):
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
        if config.get("check_world_writable") and permissions.endswith("w"):
            issues.append("World writable permission detected")

        if config.get("check_executable") and permissions[3] == 'x':
            issues.append("Executable permission detected")

        if issues:
            table.add_row(full_path, permissions, owner, group, ", ".join(issues))
        else:
            table.add_row(full_path, permissions, owner, group, "No issues found")

    except OSError as e:
        logging.error(f"Error getting file stats for {full_path}: {e}")
        table.add_row(full_path, "Error", "Error", "Error", "Error getting file stats")

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

def write_report(table, report_file):
    """Writes the report to a file."""
    try:
        with open(report_file, 'w') as f:
            f.write(table.__str__()) # Convert rich table to string
    except IOError as e:
        logging.error(f"Error writing report to file: {e}")
        raise IOError(f"Error writing report to file: {e}")

def main():
    """
    Main function to execute the permission self-reviewer.
    """
    args = setup_argparse()

    # Input validation
    if not os.path.exists(args.path):
        logging.error(f"Path does not exist: {args.path}")
        print(f"Error: Path does not exist: {args.path}")
        return

    try:
        config = load_config(args.config)
        check_permissions(args.path, config, args.report)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")
        return


if __name__ == "__main__":
    # Example Usage
    # python pa_permission_self_reviewer.py --path /path/to/analyze --config config.json --report output.txt
    # Create a dummy config.json
    # cat > config.json <<EOL
    # {
    #   "check_world_writable": true,
    #   "check_executable": true
    # }
    # EOL
    main()