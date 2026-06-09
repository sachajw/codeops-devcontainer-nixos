"""Tests for deploy.py — NixOS OrbStack deploy script."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config import (
    CONFIGS,
    MAC_PATH,
    validate_config_files,
    validate_machine_name,
)
from deploy import (
    add_home_manager_channel,
    copy_configs,
    create_machine,
    main,
    rebuild,
)
from orb import DeployError, channel_exists, machine_exists, orb, orb_run


# --- validate_machine_name ---


class TestValidateMachineName:
    @pytest.mark.parametrize("name", [
        "dev",
        "my-machine",
        "my.machine",
        "my_machine",
        "machine123",
        "a",
        "a" * 64,
        "A",
        "1machine",
        "under_score",
    ])
    def test_valid_names(self, name):
        validate_machine_name(name)

    @pytest.mark.parametrize("name", [
        "",
    ])
    def test_empty_raises(self, name):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_machine_name(name)

    @pytest.mark.parametrize("name", [
        "-machine",
        ".hidden",
        "_underscore",
        "my machine",
        "a" * 65,
        "machine!@#",
        "name/slash",
        "name:colon",
        "\t",
        " ",
    ])
    def test_invalid_names_raise(self, name):
        with pytest.raises(ValueError, match="Invalid machine name"):
            validate_machine_name(name)

    @pytest.mark.parametrize("name", [123, None, True, False, 3.14, [], {}])
    def test_non_string_raises_type_error(self, name):
        with pytest.raises(TypeError, match="must be a string"):
            validate_machine_name(name)


# --- validate_config_files ---


class TestValidateConfigFiles:
    def test_all_files_exist(self, tmp_path):
        (tmp_path / "configuration.nix").write_text("# config")
        (tmp_path / "home.nix").write_text("# home")

        with patch("config.SCRIPT_DIR", tmp_path):
            validate_config_files()

    def test_missing_config_raises(self, tmp_path):
        (tmp_path / "configuration.nix").write_text("# config")

        with patch("config.SCRIPT_DIR", tmp_path):
            with pytest.raises(FileNotFoundError, match="home.nix"):
                validate_config_files()

    def test_all_missing_raises_first(self, tmp_path):
        with patch("config.SCRIPT_DIR", tmp_path):
            with pytest.raises(FileNotFoundError, match="configuration.nix"):
                validate_config_files()

    def test_missing_script_dir_raises(self):
        with patch("config.SCRIPT_DIR", Path("/nonexistent/path")):
            with pytest.raises(FileNotFoundError, match="Script directory does not exist"):
                validate_config_files()


# --- orb ---


class TestOrb:
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        orb("status")

    @patch("subprocess.run")
    def test_command_failure_raises_deploy_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "orb status")
        with pytest.raises(DeployError, match="orb status failed"):
            orb("status")

    @patch("subprocess.run")
    def test_orb_not_found_raises_deploy_error(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(DeployError, match="OrbStack CLI not found"):
            orb("status")

    @patch("subprocess.run")
    def test_chains_exception(self, mock_run):
        original = subprocess.CalledProcessError(1, "orb test")
        mock_run.side_effect = original
        with pytest.raises(DeployError) as exc_info:
            orb("test")
        assert exc_info.value.__cause__ is original

    @patch("subprocess.run")
    def test_failure_includes_stderr(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "orb create", stderr="disk full"
        )
        with pytest.raises(DeployError, match="disk full"):
            orb("create", "test")


# --- orb_run ---


class TestOrbRun:
    @patch("subprocess.run")
    def test_returns_result(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = orb_run("status")
        assert result.returncode == 0

    @patch("subprocess.run")
    def test_returns_nonzero_without_raising(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        result = orb_run("some-command")
        assert result.returncode == 1

    @patch("subprocess.run")
    def test_orb_not_found_raises(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(DeployError, match="OrbStack CLI not found"):
            orb_run("status")

    @patch("subprocess.run")
    def test_os_error_raises(self, mock_run):
        mock_run.side_effect = OSError("permission denied")
        with pytest.raises(DeployError, match="permission denied"):
            orb_run("status")

    @patch("subprocess.run")
    def test_streams_output(self, mock_run):
        """orb_run should not buffer output — capture_output=False."""
        mock_run.return_value = MagicMock(returncode=0)
        orb_run("status")
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("capture_output") is False


# --- machine_exists ---


class TestMachineExists:
    @patch("subprocess.run")
    def test_exists(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="dev  running  nixos\n"
        )
        assert machine_exists("dev") is True

    @patch("subprocess.run")
    def test_not_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="other  running\n")
        assert machine_exists("dev") is False

    @patch("subprocess.run")
    def test_empty_list(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        assert machine_exists("dev") is False

    @patch("subprocess.run")
    def test_orb_fails_returns_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert machine_exists("dev") is False

    @patch("subprocess.run")
    def test_orb_not_found_raises(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(DeployError, match="OrbStack CLI not found"):
            machine_exists("dev")

    @patch("subprocess.run")
    def test_os_error_raises(self, mock_run):
        mock_run.side_effect = OSError("permission denied")
        with pytest.raises(DeployError, match="Failed to run 'orb list'"):
            machine_exists("dev")


# --- channel_exists ---


class TestChannelExists:
    @patch("subprocess.run")
    def test_channel_present(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="home-manager https://...\n"
        )
        assert channel_exists("dev", "home-manager") is True

    @patch("subprocess.run")
    def test_channel_absent(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        assert channel_exists("dev", "home-manager") is False

    @patch("subprocess.run")
    def test_orb_not_found_raises(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(DeployError, match="OrbStack CLI not found"):
            channel_exists("dev", "home-manager")

    @patch("subprocess.run")
    def test_orb_failure_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        with pytest.raises(DeployError, match="Failed to list nix channels"):
            channel_exists("dev", "home-manager")

    @patch("subprocess.run")
    def test_orb_failure_includes_stderr(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="machine not running")
        with pytest.raises(DeployError, match="machine not running"):
            channel_exists("dev", "home-manager")

    @patch("subprocess.run")
    def test_os_error_raises(self, mock_run):
        mock_run.side_effect = OSError("permission denied")
        with pytest.raises(DeployError, match="Failed to query channels"):
            channel_exists("dev", "home-manager")


# --- copy_configs ---


class TestCopyConfigs:
    @patch("deploy.orb")
    def test_copies_all_configs(self, mock_orb):
        copy_configs("dev")
        assert mock_orb.call_count == len(CONFIGS)
        for i, config in enumerate(CONFIGS):
            call_args = mock_orb.call_args_list[i][0]
            assert call_args == ("-m", "dev", "sudo", "cp", f"{MAC_PATH}/{config}", f"/etc/nixos/{config}")

    @patch("deploy.orb")
    def test_raises_on_failure(self, mock_orb):
        mock_orb.side_effect = DeployError("cp failed")
        with pytest.raises(DeployError, match="cp failed"):
            copy_configs("dev")


# --- add_home_manager_channel ---


class TestAddHomeManagerChannel:
    @patch("deploy.orb")
    @patch("deploy.channel_exists")
    def test_adds_channel_when_missing(self, mock_exists, mock_orb):
        mock_exists.return_value = False
        add_home_manager_channel("dev")
        assert mock_orb.call_count == 2

    @patch("deploy.orb")
    @patch("deploy.channel_exists")
    def test_skips_add_when_exists(self, mock_exists, mock_orb):
        mock_exists.return_value = True
        add_home_manager_channel("dev")
        assert mock_orb.call_count == 1
        call_args = " ".join(mock_orb.call_args[0])
        assert "nix-channel" in call_args
        assert "--add" not in call_args


# --- rebuild ---


class TestRebuild:
    @patch("deploy.orb_run")
    def test_success(self, mock_orb_run):
        mock_orb_run.return_value = MagicMock(returncode=0)
        rebuild("dev")

    @patch("deploy.orb_run")
    def test_failure_raises_deploy_error(self, mock_orb_run):
        mock_orb_run.return_value = MagicMock(returncode=1)
        with pytest.raises(DeployError, match="nixos-rebuild switch failed"):
            rebuild("dev")

    @patch("deploy.orb_run")
    def test_orb_not_found(self, mock_orb_run):
        mock_orb_run.side_effect = DeployError("OrbStack CLI not found. Is OrbStack installed?")
        with pytest.raises(DeployError, match="OrbStack CLI not found"):
            rebuild("dev")

    @patch("deploy.orb_run")
    def test_error_message_includes_hints(self, mock_orb_run):
        mock_orb_run.return_value = MagicMock(returncode=1)
        with pytest.raises(DeployError) as exc_info:
            rebuild("dev")
        assert "search.nixos.org" in str(exc_info.value)
        assert "--show-trace" in str(exc_info.value)

    @patch("deploy.orb_run")
    def test_error_message_uses_machine_name(self, mock_orb_run):
        mock_orb_run.return_value = MagicMock(returncode=1)
        with pytest.raises(DeployError, match="on 'my-box'"):
            rebuild("my-box")


# --- create_machine ---


class TestCreateMachine:
    @patch("deploy.orb")
    def test_success(self, mock_orb, capsys):
        create_machine("test-box")
        captured = capsys.readouterr()
        assert "Creating NixOS machine 'test-box'" in captured.out
        assert "Machine created." in captured.out
        mock_orb.assert_called_once_with(
            "create",
            "--memory", "4G",
            "--cpus", "2",
            "--disk", "64G",
            "nixos",
            "test-box",
        )

    @patch("deploy.orb")
    def test_raises_on_failure(self, mock_orb):
        mock_orb.side_effect = DeployError("orb create failed (exit 1)")
        with pytest.raises(DeployError, match="orb create failed"):
            create_machine("dev")


# --- main ---


class TestMain:
    @patch("deploy.rebuild")
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.create_machine")
    @patch("deploy.machine_exists", return_value=False)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_full_deploy_new_machine(
        self, mock_validate, mock_orb, mock_exists,
        mock_create, mock_copy, mock_channel, mock_rebuild, capsys,
    ):
        main()
        captured = capsys.readouterr()
        mock_create.assert_called_once_with("dev")
        mock_copy.assert_called_once_with("dev")
        mock_channel.assert_called_once_with("dev")
        mock_rebuild.assert_called_once_with("dev")
        assert "Deploy complete" in captured.out

    @patch("deploy.rebuild")
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.create_machine")
    @patch("deploy.machine_exists", return_value=True)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_skips_create_when_exists(
        self, mock_validate, mock_orb, mock_exists,
        mock_create, mock_copy, mock_channel, mock_rebuild, capsys,
    ):
        main()
        captured = capsys.readouterr()
        mock_create.assert_not_called()
        assert "already exists" in captured.out

    @patch("deploy.rebuild")
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.machine_exists", return_value=True)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    def test_uses_custom_machine_name(
        self, mock_validate, mock_orb, mock_exists,
        mock_copy, mock_channel, mock_rebuild,
    ):
        with patch("deploy.MACHINE", "custom"):
            main()
            mock_copy.assert_called_once_with("custom")

    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    def test_invalid_machine_name_exits(self, mock_validate, mock_orb):
        with patch("deploy.MACHINE", "bad name!"):
            with pytest.raises(SystemExit, match="1"):
                main()

    @patch("deploy.orb")
    def test_missing_config_exits(self, mock_orb, tmp_path):
        with patch("config.SCRIPT_DIR", tmp_path):
            with pytest.raises(SystemExit, match="1"):
                main()

    @patch("deploy.validate_config_files")
    @patch("deploy.orb", side_effect=DeployError("OrbStack CLI not found"))
    def test_orbstack_not_running_exits(self, mock_orb, mock_validate):
        with pytest.raises(SystemExit, match="1"):
            main()

    @patch("deploy.create_machine", side_effect=DeployError("create failed"))
    @patch("deploy.machine_exists", return_value=False)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    def test_create_failure_exits(
        self, mock_validate, mock_orb, mock_exists, mock_create,
    ):
        with pytest.raises(SystemExit, match="1"):
            main()

    @patch("deploy.rebuild", side_effect=DeployError("rebuild failed"))
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.machine_exists", return_value=True)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    def test_deploy_failure_exits(
        self, mock_validate, mock_orb, mock_exists,
        mock_copy, mock_channel, mock_rebuild,
    ):
        with pytest.raises(SystemExit, match="1"):
            main()

    @patch("deploy.rebuild", side_effect=KeyboardInterrupt)
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.machine_exists", return_value=True)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_keyboard_interrupt_exits_130(
        self, mock_validate, mock_orb, mock_exists,
        mock_copy, mock_channel, mock_rebuild,
    ):
        with pytest.raises(SystemExit, match="130"):
            main()

    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    def test_type_error_machine_name_exits(self, mock_validate, mock_orb):
        """TypeError from non-string MACHINE is caught and exits."""
        with patch("deploy.MACHINE", 123):
            with pytest.raises(SystemExit, match="1"):
                main()

    @patch("deploy.MACHINE", "dev")
    @patch("deploy.orb")
    def test_missing_config_prints_error_and_exits(self, mock_orb, tmp_path, capsys):
        """FileNotFoundError from validate_config_files is caught with message."""
        with patch("config.SCRIPT_DIR", tmp_path):
            with pytest.raises(SystemExit, match="1"):
                main()
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    @patch("deploy.MACHINE", "dev")
    @patch("deploy.validate_config_files")
    @patch("deploy.orb", side_effect=DeployError("OrbStack CLI not found"))
    def test_orb_status_fail_prints_hint(self, mock_orb, mock_validate, capsys):
        """orb status failure prints the 'Start OrbStack' hint."""
        with pytest.raises(SystemExit, match="1"):
            main()
        captured = capsys.readouterr()
        assert "Start OrbStack first" in captured.out

    @patch("deploy.create_machine")
    @patch("deploy.machine_exists", side_effect=DeployError("orb list failed"))
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_machine_exists_failure_exits(
        self, mock_validate, mock_orb, mock_exists, mock_create, capsys,
    ):
        """DeployError from machine_exists is caught with message."""
        with pytest.raises(SystemExit, match="1"):
            main()
        captured = capsys.readouterr()
        assert "Error checking machine status" in captured.out

    @patch("deploy.create_machine", side_effect=DeployError("create failed"))
    @patch("deploy.machine_exists", return_value=False)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_create_failure_prints_error(
        self, mock_validate, mock_orb, mock_exists, mock_create, capsys,
    ):
        """DeployError from create_machine prints specific message."""
        with pytest.raises(SystemExit, match="1"):
            main()
        captured = capsys.readouterr()
        assert "Error creating machine" in captured.out

    @patch("deploy.rebuild", side_effect=DeployError("rebuild failed"))
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.machine_exists", return_value=True)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_deploy_failure_prints_error(
        self, mock_validate, mock_orb, mock_exists,
        mock_copy, mock_channel, mock_rebuild, capsys,
    ):
        """DeployError in deploy phase prints 'Deploy failed' message."""
        with pytest.raises(SystemExit, match="1"):
            main()
        captured = capsys.readouterr()
        assert "Deploy failed" in captured.out

    @patch("deploy.rebuild")
    @patch("deploy.add_home_manager_channel")
    @patch("deploy.copy_configs")
    @patch("deploy.machine_exists", return_value=True)
    @patch("deploy.orb")
    @patch("deploy.validate_config_files")
    @patch("deploy.MACHINE", "dev")
    def test_successful_deploy_prints_summary(
        self, mock_validate, mock_orb, mock_exists,
        mock_copy, mock_channel, mock_rebuild, capsys,
    ):
        """Successful deploy prints the completion summary."""
        main()
        captured = capsys.readouterr()
        assert "Deploy complete" in captured.out
        assert "orb -m dev -u tvl" in captured.out
