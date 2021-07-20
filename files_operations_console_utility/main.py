import argparse
import logging
import logging.config
import os
import shutil
import sys
from concurrent.futures import (
    ThreadPoolExecutor,
    Future,
    as_completed,
)
from pathlib import Path
from typing import (
    Dict,
    Final,
    Callable,
    Tuple,
    Optional,
    List,
    Set,
)

import yaml


def setup_logging(config_file_path: str = '../logging.yaml'):
    """Setup logging from yaml file."""
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    logging.config.dictConfig(config)


def check_paths_exists(source: Path, destination: Path) -> bool:
    """Check that source and destination paths exist."""
    def check_path_exists(path: Path) -> bool:
        if not path.exists():
            logging.error(msg=f'{path.name} does not exists.')

        return path.exists()

    return check_path_exists(path=source) and check_path_exists(path=destination)


def extract_path_and_mask(path: str) -> Tuple[Path, Optional[str]]:
    """Extract path and mask (if any) from the specified path."""
    elements: Tuple[str, str, str] = path.partition('*')

    new_path: Path = Path(elements[0])
    mask: Optional[str] = None

    if elements[1] != '':
        mask = f'{elements[1]}{elements[2]}'

    return new_path, mask


def copy(source: Path, destination: Path) -> None:
    """Copy the file data and metadata to the destination."""
    shutil.copy2(src=source, dst=destination)


def move(source: Path, destination: Path) -> None:
    """Move the file to the destination."""
    shutil.move(src=source, dst=destination)


operations: Final[Dict[str, Callable[[Path, Path], None]]] = {
    'copy': copy,
    'move': move
}


def list_files(source: Path, mask: Optional[str]) -> List[Path]:
    """Returns all files in the source with using a mask (if any)."""
    files: List[Path] = []

    if mask is None:
        mask = '**/*'

    for entry in source.glob(mask):
        if entry.is_file():
            files.append(entry)

    return files


def create_source_paths(source: Path, mask: Optional[str]) -> List[Path]:
    """Returns a list of paths to source files."""
    source_paths: List[Path] = []

    if source.is_file():
        source_paths.append(source)
    else:
        try:
            source_paths = list_files(source=source, mask=mask)
        except Exception:
            logging.exception(msg=f'Invalid search pattern in {source} path.')
            raise

    return source_paths


def create_source_and_destination_paths(
        source: Path,
        source_paths: List[Path],
        destination: Path
) -> Dict[Path, Path]:
    """Returns a dictionary with
    the key - the path to the source file
    and value - the destination path, including subfolders and the file name.

    Also creates subfolders in the destination path.

    Example:
        /home/user/projects/ - source
        /home/user/projects/subfolder/file.txt - the path to the source file
        /root/ - destination
        /root/subfolder/file.txt - the destination path
    """
    source_and_destination_paths: Dict[Path, Path] = {}
    folders_to_create: Set[Path] = set()

    for source_path in source_paths:
        destination_path: Path = destination / source_path.relative_to(source)

        source_and_destination_paths.update({source_path: destination_path})

        if destination != destination_path.parent:
            folders_to_create.add(destination_path.parent)

    # Create subfolders in the destination path.
    for folder in folders_to_create:
        os.makedirs(folder, exist_ok=True)

    return source_and_destination_paths


def run_operation_in_threads(
        source: Path,
        operation_name: str,
        source_and_destination_paths: Dict[Path, Path],
        threads: int,
        mask: Optional[str]
) -> None:
    """Runs the specified operation using the specified number of threads."""
    success_count: int = 0
    error_count: int = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        operation: Callable[[Path, Path], None] = operations.get(operation_name)
        future_to_file: Dict[Future, Path] = {}

        # Submit operation.
        for source_path, destination_path in source_and_destination_paths.items():
            future: Future = executor.submit(
                operation,
                source=source_path,
                destination=destination_path
            )

            future_to_file.update({future: source_path})

        # Output result.
        for future in as_completed(future_to_file):
            file: Path = future_to_file.get(future)

            try:
                future.result()

                logging.info(msg=f'success: {file}')

                success_count += 1
            except Exception as exception:
                logging.error(msg=f'error: {file} - {str(exception)}')
                error_count += 1

    # Delete the source folder
    # when all files have been successfully moved out of it.
    if (operation_name == 'move') and \
       (error_count == 0) and \
       ((mask is None) or (mask == '**/*')):
        shutil.rmtree(source)

    logging.info(f'\nSuccess {success_count} files')
    logging.info(f'Error {error_count} files')


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser: argparse.ArgumentParser = \
        argparse.ArgumentParser(
            description='A utility for performing file operations '
                        'using multithreading.',
            formatter_class=argparse.RawTextHelpFormatter
        )
    parser.add_argument(
        '--operation',
        type=str,
        required=True,
        choices=operations.keys(),
        help='Operation to be performed on files.'
    )
    parser.add_argument(
        '--from',
        dest='source',
        type=Path,
        required=True,
        help='The path to the source folder or file.\n'
             'You can also select the necessary files '
             'corresponding to the specified mask.\n'
             'Example:\n'
             '/home/user/projects/ - select all files.\n'
             '/home/user/projects/*.md - select files only with the .md extension.'
    )
    parser.add_argument(
        '--to',
        dest='destination',
        type=Path,
        required=True,
        help='The destination folder path.'
    )
    parser.add_argument(
        '--threads',
        type=int,
        default=1,
        help='The number of threads used to perform operation on files.\n'
             'Default - 1 thread.\n'
             'The minimum number of threads is 1.\n'
             'When the source is a file, 1 thread is used.'
    )

    parsed_args: argparse.Namespace = parser.parse_args(args=args)

    if parsed_args.threads <= 0:
        parser.error(message='the minimum number of threads is 1.')

    return parsed_args


def main():
    args: argparse.Namespace = parse_args(args=sys.argv[1:])
    mask: Optional[str] = None

    args.source, mask = extract_path_and_mask(path=str(args.source.absolute()))

    if check_paths_exists(source=args.source, destination=args.destination):
        if args.source.is_file():
            args.threads = 1

        source_paths: List[Path] = \
            create_source_paths(
                source=args.source,
                mask=mask
            )

        source_and_destination_paths: Dict[Path, Path] = \
            create_source_and_destination_paths(
                source=args.source,
                source_paths=source_paths,
                destination=args.destination
            )

        logging.info(msg=f'{args.operation} files to {args.destination}\n')
        run_operation_in_threads(
            source=args.source,
            operation_name=args.operation,
            source_and_destination_paths=source_and_destination_paths,
            threads=args.threads,
            mask=mask
        )


if __name__ == '__main__':
    setup_logging()
    main()
