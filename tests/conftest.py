import shutil
from pathlib import Path
from typing import Final

import pytest
from _pytest.fixtures import SubRequest

current_file_directory: Final[Path] = Path().absolute()


@pytest.fixture()
def tmp_input_dir(request: SubRequest) -> Path:
    tmp_input_dir: Path = current_file_directory / 'tmp_input_dir'

    tmp_input_dir.mkdir(exist_ok=True)

    source: Path = request.param

    if source.is_dir():
        shutil.copytree(src=source, dst=tmp_input_dir, dirs_exist_ok=True)
    elif source.is_file():
        shutil.copy2(src=source, dst=tmp_input_dir)

    yield tmp_input_dir

    shutil.rmtree(tmp_input_dir, ignore_errors=True)


@pytest.fixture()
def tmp_output_dir() -> Path:
    tmp_output_dir: Path = current_file_directory / 'tmp_output_dir'

    tmp_output_dir.mkdir(exist_ok=True)

    yield tmp_output_dir

    shutil.rmtree(tmp_output_dir)


@pytest.fixture(params=['copy', 'move'])
def get_operation(request: SubRequest) -> str:
    return request.param
