import argparse
from pathlib import Path


if __name__ == '__main__':
    # Create CLI argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--logs_dir', help='Directory containing the slurm logs', required=True)

    # Parse CLI logs dir and check if it really exists
    args = parser.parse_args()
    logs_dir = Path(args.logs_dir)
    if not logs_dir.exists():
        raise ValueError('Log directory does not exist!')

    log_files = logs_dir.glob('**/sub-*.out', )  # Collect all the log files
    failed_subjects = []
    failed_on_node = []

    for log_file in log_files:
        with open(log_file, 'r') as log_file_obj:
            lines = log_file_obj.readlines()
            loi = lines[-2]  # line of interest. Should start with 'Ended on c[...]'
            if loi.startswith('Ended on c'):
                continue
            else:
                first_split = lines[1].split('.')[0]  # 'Starting on c[Number]'
                node_start_idx = first_split.rfind('c')
                node = first_split[node_start_idx:]  # e.g., 'c78'
                failed_on_node.append(node)
                failed_subjects.append(
                    (log_file.stem, node)
                )
    print('The following subject(s) crashed:')
    for subject, node in failed_subjects:
        print(f'{subject} on {node}')
    failed = set(failed_on_node)
    print(f'Please clean up manually on the following nodes: {failed}')
