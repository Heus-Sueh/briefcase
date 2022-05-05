import os

import pytest

from briefcase.console import Log


def test_call(mock_sub, capsys):
    "A simple call will be invoked"

    mock_sub.Popen(['hello', 'world'])

    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'], text=True)
    assert capsys.readouterr().out == ""


def test_call_with_arg(mock_sub, capsys):
    "Any extra keyword arguments are passed through as-is"

    mock_sub.Popen(['hello', 'world'], universal_newlines=True)

    mock_sub._subprocess.Popen.assert_called_with(
        ['hello', 'world'],
        universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_call_with_path_arg(mock_sub, capsys, tmp_path):
    "Path-based arguments are converted to strings andpassed in as-is"

    mock_sub.Popen(['hello', tmp_path / 'location'], cwd=tmp_path / 'cwd')

    mock_sub._subprocess.Popen.assert_called_with(
        ['hello', os.fsdecode(tmp_path / 'location')],
        cwd=os.fsdecode(tmp_path / 'cwd'),
        text=True,
    )
    assert capsys.readouterr().out == ""


def test_debug_call(mock_sub, capsys):
    "If verbosity is turned up, there is output"
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.Popen(['hello', 'world'])

    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'], text=True)
    assert capsys.readouterr().out == (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
    )


def test_debug_call_with_env(mock_sub, capsys):
    "If verbosity is turned up, and injected env vars are included output"
    mock_sub.command.logger = Log(verbosity=2)

    env = {"NewVar": "NewVarValue"}
    mock_sub.Popen(['hello', 'world'], env=env)

    merged_env = mock_sub.command.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'], env=merged_env, text=True)

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Environment:\n"
        ">>>     NewVar=NewVarValue\n"
    )

    assert capsys.readouterr().out == expected_output


def test_deep_debug_call(mock_sub, capsys):
    "If verbosity is at the max, the full environment and return is output"
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.Popen(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], text=True)

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
    )

    assert capsys.readouterr().out == expected_output


def test_deep_debug_call_with_env(mock_sub, capsys):
    "If verbosity is at the max, the full environment and return is output, and the environment is merged"
    mock_sub.command.logger = Log(verbosity=3)

    env = {"NewVar": "NewVarValue"}
    mock_sub.Popen(['hello', 'world'], env=env)

    merged_env = mock_sub.command.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.Popen.assert_called_with(['hello', 'world'], env=merged_env, text=True)

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
        ">>>     NewVar=NewVarValue\n"
    )

    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        ({}, {'text': True}),
        ({'text': True}, {'text': True}),
        ({'text': False}, {'text': False}),
        ({'universal_newlines': False}, {'universal_newlines': False}),
        ({'universal_newlines': True}, {'universal_newlines': True}),
    ]
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs):
    "if text or universal_newlines is explicitly provided, those should override text=true default"

    mock_sub.Popen(['hello', 'world'], **in_kwargs)
    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **kwargs)
