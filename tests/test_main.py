import argparse
import shutil
from pathlib import Path
from typing import (
    Final,
    Tuple,
    Optional,
    List,
    Dict,
    Set,
)

import pytest

from files_operations_console_utility import main

current_file_directory: Final[Path] = Path().absolute()


def empty_test_folder() -> Path:
    return current_file_directory / 'empty'


def files_test_folder() -> Path:
    return current_file_directory / 'files'


def files_and_subfolders_test_folder() -> Path:
    return current_file_directory / 'files_and_subfolders'


def files_folders_tree_test_folder() -> Path:
    return current_file_directory / 'files_folders_tree'


subfolder_1_name: Final[str] = 'subfolder_1'
subfolder_2_name: Final[str] = 'subfolder_2'

subfolder_1: Final[Path] = files_and_subfolders_test_folder() / subfolder_1_name
subfolder_2: Final[Path] = files_and_subfolders_test_folder() / subfolder_2_name


def get_source_and_destination_paths(
        source: Path,
        mask: Optional[str],
        destination: Path
) -> Dict[Path, Path]:
    source_paths: List[Path] = \
        main.create_source_paths(
            source=source,
            mask=mask
        )

    source_and_destination_paths: Dict[Path, Path] = \
        main.create_source_and_destination_paths(
            source=source,
            source_paths=source_paths,
            destination=destination
        )

    return source_and_destination_paths


def get_number_of_all_elements_in_dir(source: Path) -> int:
    return len(list(source.glob('**/*')))


def get_elements_must_be_in_input_dir(
        operation_name: str,
        source: Path,
        mask: Optional[str],
        source_and_destination_paths: Dict[Path, Path]
):
    input_dir_all_elements = \
        get_number_of_all_elements_in_dir(source=source)

    if operation_name == 'copy':
        return input_dir_all_elements
    elif operation_name == 'move':
        if (mask is None) or (mask == '**/*'):
            return 0
        else:
            return input_dir_all_elements - len(source_and_destination_paths)


def get_elements_must_be_in_output_dir(
        source: Path,
        destination: Path,
        source_and_destination_paths: Dict[Path, Path]
):
    folders_to_create: Set[Path] = set()

    for source_path in source_and_destination_paths.keys():
        destination_path: Path = destination / source_path.relative_to(source)

        if destination != destination_path.parent:
            folders_to_create.add(destination_path.parent)

    return len(source_and_destination_paths) + len(folders_to_create)


@pytest.mark.parametrize(
    'source, destination, result',
    [
        (empty_test_folder(), files_test_folder(), True),
        (empty_test_folder(), files_and_subfolders_test_folder(), True),
        (files_test_folder(), empty_test_folder(), True),
        (files_and_subfolders_test_folder(), empty_test_folder(), True),
        (empty_test_folder(), subfolder_1, True),
        (empty_test_folder(), subfolder_2, True),
        (empty_test_folder(), Path('not_exists'), False),
        (Path('not_exists'), empty_test_folder(), False),
        (Path('not_exists'), Path('not_exists'), False),
        (files_test_folder(), Path('*.md'), False),
        (Path('*.md'), files_test_folder(), False),
        (Path('*.md'), Path('*.md'), False),
        (empty_test_folder(), Path('dir/*'), False),
        (Path('dir/*'), empty_test_folder(), False),
    ]
)
def test_check_paths_exists(source: Path, destination: Path, result: bool):
    assert result == main.check_paths_exists(source=source, destination=destination)


@pytest.mark.parametrize(
    'path, result',
    [
        ('/home/user/projects', (Path('/home/user/projects'), None)),
        ('', (Path(''), None)),
        ('test_path', (Path('test_path'), None)),
        ('/home/user/projects/*.md', (Path('/home/user/projects/'), '*.md')),
        ('/home/user/projects/*.json', (Path('/home/user/projects/'), '*.json')),
        ('/home/user/projects/*.*', (Path('/home/user/projects/'), '*.*')),
        ('/home/user/projects/*', (Path('/home/user/projects/'), '*')),
        ('/home/user/projects/*/*', (Path('/home/user/projects/'), '*/*')),
        ('/home/user/projects/*/*.md', (Path('/home/user/projects/'), '*/*.md')),
        ('/home/user*/projects/', (Path('/home/user'), '*/projects/')),
        ('*/home/user/projects/', (Path(''), '*/home/user/projects/')),
        ('*/home/*user/projects/', (Path(''), '*/home/*user/projects/')),
    ]
)
def test_extract_path_and_mask(path: str, result: Tuple[Path, Optional[str]]):
    assert result == main.extract_path_and_mask(path=path)


@pytest.mark.parametrize(
    'source',
    [
        (files_test_folder() / '1.json'),
        (files_test_folder() / '1MiB.bin'),
        (files_test_folder() / '2.md'),
        (files_test_folder() / '10MiB.bin'),
        (files_test_folder() / '5'),
        (files_test_folder() / '7.exe'),
        (files_test_folder() / 'assa.txt'),
        (files_test_folder() / 'e07b20ffd67e495e5f6325dd395d0ac7.png'),
        (files_test_folder() / 'Wat8.jpg'),
        (files_test_folder() / '.env'),
        (files_test_folder() / '.hidden'),
        (subfolder_2 / '5'),
        (subfolder_2 / '9.exe'),
        (subfolder_2 / '10MB.bin'),
        (subfolder_2 / '10MiB.bin'),
        (subfolder_2 / '.env'),
        (subfolder_1 / 'assa.txt'),
        (subfolder_1 / 'e07b20ffd67e495e5f6325dd395d0ac7.png'),
        (subfolder_1 / 'qwqwq.md'),
        (subfolder_1 / 'zzzz.json'),
        (subfolder_1 / '.hidden'),
    ]
)
def test_copy_valid(source: Path, tmp_output_dir: Path):
    main.copy(source=source, destination=tmp_output_dir)

    copied_file_path: Path = tmp_output_dir / source.name

    assert copied_file_path.exists() and source.exists()


@pytest.mark.parametrize(
    'source, destination, result',
    [
        (empty_test_folder(), empty_test_folder(), OSError),
        (files_test_folder(), empty_test_folder(), OSError),
        (files_test_folder() / 'not_exists_file', empty_test_folder(), FileNotFoundError),
        (files_test_folder() / '1.json', Path('not_exists_folder/not_exist_folder'), FileNotFoundError),
        (files_test_folder() / '1.json', files_test_folder(), shutil.SameFileError),
    ]
)
def test_copy_invalid(source: Path, destination: Path, result: Exception):
    with pytest.raises(result):
        main.copy(source=source, destination=destination)


@pytest.mark.parametrize(
    'tmp_input_dir, file',
    [
        (files_test_folder(), Path('1.json')),
        (files_test_folder(), Path('1MiB.bin')),
        (files_test_folder(), Path('2.md')),
        (files_test_folder(), Path('10MiB.bin')),
        (files_test_folder(), Path('5')),
        (files_test_folder(), Path('7.exe')),
        (files_test_folder(), Path('assa.txt')),
        (files_test_folder(), Path('e07b20ffd67e495e5f6325dd395d0ac7.png')),
        (files_test_folder(), Path('Wat8.jpg')),
        (files_test_folder(), Path('.env')),
        (files_test_folder(), Path('.hidden')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_2_name) / Path('5')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_2_name) / Path('9.exe')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_2_name) / Path('10MB.bin')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_2_name) / Path('10MiB.bin')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_2_name) / Path('.env')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_1_name) / Path('assa.txt')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_1_name) / Path('e07b20ffd67e495e5f6325dd395d0ac7.png')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_1_name) / Path('qwqwq.md')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_1_name) / Path('zzzz.json')),
        (files_and_subfolders_test_folder(),
         Path(subfolder_1_name) / Path('.hidden')),
    ],
    indirect=['tmp_input_dir']
)
def test_move_files_valid(tmp_input_dir: Path, file: Path, tmp_output_dir: Path):
    input_file_path: Path = tmp_input_dir / file

    main.move(source=input_file_path, destination=tmp_output_dir)

    moved_file_path: Path = tmp_output_dir / file.name

    assert (not input_file_path.exists()) and moved_file_path.exists()


@pytest.mark.parametrize(
    'tmp_input_dir, input_folder',
    [
        (files_test_folder(), pytest.lazy_fixture('tmp_input_dir')),
    ],
    indirect=['tmp_input_dir']
)
def test_move_folder_inside_another_folder(
        tmp_input_dir: Path,
        input_folder: Path,
        tmp_output_dir: Path
):
    main.move(source=input_folder, destination=tmp_output_dir)

    moved_folder_path: Path = tmp_output_dir / input_folder.name

    assert (not tmp_input_dir.exists()) and moved_folder_path.exists()


@pytest.mark.parametrize(
    'tmp_input_dir, input_folder',
    [
        (files_test_folder(), pytest.lazy_fixture('tmp_output_dir')),
    ],
    indirect=['tmp_input_dir']
)
def test_move_folder_to_same_folder(
        tmp_input_dir: Path,
        input_folder: Path,
        tmp_output_dir: Path
):
    main.move(source=input_folder, destination=tmp_output_dir)

    moved_folder_path: Path = tmp_output_dir

    assert input_folder.exists() and moved_folder_path.exists()


@pytest.mark.parametrize(
    'source, destination, result',
    [
        (files_test_folder() / 'not_exists_file', empty_test_folder(), FileNotFoundError),
        (files_test_folder() / '1.json', Path('not_exists_folder/not_exist_folder'), FileNotFoundError),
        ('/not_exists_folder/', empty_test_folder(), FileNotFoundError),
        (files_test_folder() / '1.json', files_test_folder(), OSError),
    ]
)
def test_move_invalid(source: Path, destination: Path, result: Exception):
    with pytest.raises(result):
        main.move(source=source, destination=destination)


@pytest.mark.parametrize(
    'source, mask, result',
    [
        (empty_test_folder(), None, 0),
        (empty_test_folder(), '*.md', 0),
        (empty_test_folder(), '**', 0),
        (empty_test_folder(), '*/*', 0),
        (empty_test_folder(), '*/*.json', 0),
        (empty_test_folder(), '**/*', 0),

        (files_test_folder(), None, 26),
        (files_test_folder(), '*.md', 3),
        (files_test_folder(), '*.bin', 6),
        (files_test_folder(), '**', 0),
        (files_test_folder(), '*/*', 0),
        (files_test_folder(), '*/*.json', 0),
        (files_test_folder(), '**/*', 26),
        (files_test_folder(), '.hidden', 1),

        (files_and_subfolders_test_folder(), None, 26),
        (files_and_subfolders_test_folder(), '*.md', 2),
        (files_and_subfolders_test_folder(), '*.bin', 4),
        (files_and_subfolders_test_folder(), '**', 0),
        (files_and_subfolders_test_folder(), '*/*', 18),
        (files_and_subfolders_test_folder(), subfolder_1_name + '/*', 9),
        (files_and_subfolders_test_folder(), subfolder_2_name + '/*', 9),
        (files_and_subfolders_test_folder(), '*/*.json', 1),
        (files_and_subfolders_test_folder(), '*/*.exe', 3),
        (files_and_subfolders_test_folder(), '**/*', 26),
    ]
)
def test_list_files_valid(source: Path, mask: Optional[str], result: int):
    assert result == len(main.list_files(source=source, mask=mask))


@pytest.mark.parametrize(
    'source, mask, result',
    [
        (empty_test_folder(), '***', Exception),
        (empty_test_folder(), '.', Exception),
    ]
)
def test_list_files_invalid(source: Path, mask: Optional[str], result: Exception):
    with pytest.raises(result):
        main.list_files(source=source, mask=mask)


@pytest.mark.parametrize(
    'source, mask, result',
    [
        (files_test_folder() / '1.json', None, 1),
        (files_test_folder() / '1MiB.bin', '*.md', 1),
        (files_test_folder() / '2.md', '**', 1),

        (empty_test_folder(), None, 0),
        (empty_test_folder(), '*.md', 0),

        (files_test_folder(), None, 26),
        (files_test_folder(), '*.md', 3),
        (files_test_folder(), '*.bin', 6),
    ]
)
def test_create_source_paths_valid(source: Path, mask: Optional[str], result: List[Path]):
    assert result == len(main.create_source_paths(source=source, mask=mask))


@pytest.mark.parametrize(
    'source, mask, result',
    [
        (empty_test_folder(), '***', Exception),
        (empty_test_folder(), '.', Exception),
    ]
)
def test_create_source_paths_invalid(source: Path, mask: Optional[str], result: Exception):
    with pytest.raises(result):
        main.create_source_paths(source=source, mask=mask)


@pytest.mark.parametrize(
    'source, mask, destination, result',
    [
        (empty_test_folder(), None, empty_test_folder(), {}),
        (empty_test_folder(), '*.md', empty_test_folder(), {}),

        (files_test_folder(),
         None,
         empty_test_folder(),
         {file: empty_test_folder() / file.name for file in files_test_folder().glob('*')}
         ),

        (files_test_folder(),
         '*.json',
         empty_test_folder(),
         {files_test_folder() / '1.json': empty_test_folder() / '1.json',
          files_test_folder() / '3.json': empty_test_folder() / '3.json',
          files_test_folder() / 'zzzz.json': empty_test_folder() / 'zzzz.json'}
         ),

        (files_and_subfolders_test_folder(),
         '*/*.exe',
         empty_test_folder(),
         {subfolder_1 / 'tertet.exe': empty_test_folder() / subfolder_1_name / 'tertet.exe',
          subfolder_2 / '7.exe': empty_test_folder() / subfolder_2_name / '7.exe',
          subfolder_2 / '9.exe': empty_test_folder() / subfolder_2_name / '9.exe'})
    ]
)
def test_create_source_and_destination_paths(
        source: Path,
        mask: Optional[str],
        destination: Path,
        result: Dict[Path, Path]
):
    source_and_destination_paths: Dict[Path, Path] = \
        get_source_and_destination_paths(
            source=source,
            mask=mask,
            destination=destination
        )

    # Remove subfolders in the destination path.
    for path in empty_test_folder().iterdir():
        shutil.rmtree(path)

    assert result == source_and_destination_paths


@pytest.mark.parametrize(
    'tmp_input_dir, mask, threads',
    [
        (empty_test_folder(), None, 1),
        (empty_test_folder(), '*.md', 5),

        (files_test_folder(), None, 1),
        (files_test_folder(), None, 5),
        (files_test_folder(), '*.md', 3),
        (files_test_folder(), '*.bin', 5),

        (files_and_subfolders_test_folder(), None, 7),
        (files_and_subfolders_test_folder(), '*.json', 6),
        (files_and_subfolders_test_folder(), '*/*.bin', 4),
        (files_and_subfolders_test_folder(), '*/*.exe', 4),
        (files_and_subfolders_test_folder(), '*/*', 4),

        (files_folders_tree_test_folder(), None, 8),
        (files_folders_tree_test_folder(), '*.exe', 4),
        (files_folders_tree_test_folder(), '*/*.json', 4),
        (files_folders_tree_test_folder(), '*/*.txt', 4),
        (files_folders_tree_test_folder(), '*/*', 4),

        (files_test_folder() / 'fc3.jpg', None, 1),
        (files_test_folder() / 'Wat8.jpg', None, 5),
        (files_test_folder() / '2.md', '*.md', 3),
        (files_test_folder() / '1KiB.bin', '*.bin', 5),

        (files_test_folder() / '.env', None, 1),
        (files_test_folder() / '.env', None, 3),
        (files_test_folder() / '.env', '*.json', 3),

        (files_and_subfolders_test_folder() / '.env', None, 2),
        (files_and_subfolders_test_folder() / '.env', '*/*.bin', 2),

        (subfolder_1 / 'assa.txt', None, 2),
        (subfolder_1 / 'fc3.jpg', None, 2),

        (subfolder_2 / '5', None, 2),
        (subfolder_2 / '9.exe', None, 2),
    ],
    indirect=['tmp_input_dir']
)
def test_run_operation_in_threads(
        tmp_input_dir: Path,
        mask: Optional[str],
        tmp_output_dir: Path,
        get_operation: str,
        threads: int
):
    source_and_destination_paths: Dict[Path, Path] = \
        get_source_and_destination_paths(
            source=tmp_input_dir,
            mask=mask,
            destination=tmp_output_dir
        )

    elements_must_be_in_output_dir: int = \
        get_elements_must_be_in_output_dir(
            source=tmp_input_dir,
            destination=tmp_output_dir,
            source_and_destination_paths=source_and_destination_paths
        )

    elements_must_be_in_input_dir: int = \
        get_elements_must_be_in_input_dir(
            operation_name=get_operation,
            source=tmp_input_dir,
            mask=mask,
            source_and_destination_paths=source_and_destination_paths
        )

    main.setup_logging()
    main.run_operation_in_threads(
        source=tmp_input_dir,
        operation_name=get_operation,
        source_and_destination_paths=source_and_destination_paths,
        threads=threads,
        mask=mask
    )

    output_dir_number_of_elements: int = \
        len(list(tmp_output_dir.glob('**/*')))

    current_number_of_elements_in_input_dir: int = \
        get_number_of_all_elements_in_dir(source=tmp_input_dir)

    assert (current_number_of_elements_in_input_dir ==
           elements_must_be_in_input_dir)
    assert (output_dir_number_of_elements ==
            elements_must_be_in_output_dir)


@pytest.mark.parametrize(
    'args, result',
    [
        (['--operation=copy',
          '--from=/home/user/projects/',
          '--to=/root/',
          '--threads=5'],
         argparse.Namespace(
             operation='copy',
             source=Path('/home/user/projects/'),
             destination=Path('/root/'),
             threads=5)
         ),
        (['--operation=move',
          '--from=/home/user/projects/*.md',
          '--to=/root/some_folder'],
         argparse.Namespace(
             operation='move',
             source=Path('/home/user/projects/*.md'),
             destination=Path('/root/some_folder'),
             threads=1)
         ),
        (['--operation=move',
          '--from=sadsd',
          '--to=123'],
         argparse.Namespace(
             operation='move',
             source=Path('sadsd'),
             destination=Path('123'),
             threads=1)
         ),
    ]
)
def test_parse_args_valid(args: List[str], result: argparse.Namespace):
    parsed_args: argparse.Namespace = main.parse_args(args=args)
    assert result == parsed_args


@pytest.mark.parametrize(
    'args, result',
    [
        (['--operation=not_exist',
          '--from=/home/user/projects/',
          '--to=/root/',
          '--threads=5'],
         SystemExit
         ),
        (['--operation=copy',
          '--from=/home/user/projects/',
          '--to=/root/some_folder',
          '--threads=not_int'],
         SystemExit
         ),
        (['--from=/home/user/projects/',
          '--to=/root/some_folder'],
         SystemExit
         ),
        (['--operation=copy',
          '--to=/root/some_folder'],
         SystemExit
         ),
        (['--operation=copy',
          '--from=/home/user/projects/'],
         SystemExit
         ),
        (['--operation=copy',
          '--from=/home/user/projects/',
          '--to=/root/',
          '--threads=0'],
         SystemExit
         ),
        (['--operation=copy',
          '--from=/home/user/projects/',
          '--to=/root/',
          '--threads=-20'],
         SystemExit
         ),
    ]
)
def test_parse_args_invalid(args: List[str], result: SystemExit):
    with pytest.raises(result):
        main.parse_args(args=args)
