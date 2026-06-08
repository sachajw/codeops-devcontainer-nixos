"""Tests for deploy.py — NixOS OrbStack deploy script."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from deploy import (
    DeployError,
    add_home_manager_channel,
    channel_exists,
    copy_configs,
    create_machine,
    machine_exists,
    main,
    orb,
    rebuild,
    validate_config_files,
    validate_machine_name,
)


# --- validate_machine_name ---


class TestValidateMachineName:
    def test_valid_simple(self):
        validate_machine_name("dev")

    def test_valid_with_dashes(self):
        validate_machine_name("my-machine")

    def test_valid_with_dots(self):
        validate_machine_name("my.machine")

    def test_valid_with_underscores(self):
        validate_machine_name("my_machine")

    def test_valid_alphanumeric(self):
        validate_machine_name("machine123")

    def test_valid_single_char(self):
        validate_machine_name("a")

    def test_valid_64_chars(self):
        validate_machine_name("a" * 64)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_machine_name("")

    def test_starts_with_dash_raises(self):
        with pytest.raises(ValueError, match="Invalid machine name"):
            validate_machine_name("-machine")

    def test_starts_with_dot_raises(self):
        with pytest.raises(ValueError, match="Invalid machine name"):
            validate_machine_name(".hidden")

    def test_spaces_raises(self):
        with pytest.raises(ValueError, match="Invalid machine name"):
            validate_machine_name("my machine")

    def test_65_chars_raises(self):
        with pytest.raises(ValueError, match="Invalid machine name"):
            validate_machine_name("a" * 65)

    def test_special_chars_raises(self):
        with pytest.raises(ValueError, match="Invalid machine name"):
            validate_machine_name("machine!@#")


# --- validate_config_files ---


class TestValidateConfigFiles:
    def test_all_files_exist(self, tmp_path):
        (tmp_path / "configuration.nix").write_text("# config")
        (tmp_path / "home.nix").write_text("# home")

        with patch("deploy.SCRIPT_DIR", tmp_path):
            validate_config_files()

    def test_missing_config_raises(self, tmp_path):
        (tmp_path / "configuration.nix").write_text("# config")
        # home.nix not created

        with patch("deploy.SCRIPT_DIR", tmp_path):
            with pytest.raises(FileNotFoundError, match="home.nix"):
                validate_config_files()

    def test_all_missing_raises_first(self, tmp_path):
        with patch("deploy.SCRIPT_DIR", tmp_path):
            with pytest.raises(FileNotFoundError, match="configuration.nix"):
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
    def test_orb_not_found_returns_false(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        assert machine_exists("dev") is False


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
    def test_orb_not_found_returns_false(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        assert channel_exists("dev", "home-manager") is False


# --- copy_configs ---


class TestCopyConfigs:
    @patch("deploy.orb")
    def test_copies_all_configs(self, mock_orb):
        copy_configs("dev")
        mock_orb.assert_called_once()
        call_args = mock_orb.call_args[0]
        assert call_args[0] == "-m"
        assert call_args[1] == "dev"
        assert call_args[2] == "sudo"
        assert call_args[3] == "cp"
        # Should have src/dst pairs for each config
        assert len(call_args) > 4

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
        # Should call orb for --add and --update
        assert mock_orb.call_count == 2

    @patch("deploy.orb")
    @patch("deploy.channel_exists")
    def test_skips_add_when_exists(self, mock_exists, mock_orb):
        mock_exists.return_value = True
        add_home_manager_channel("dev")
        # Should only call --update
        assert mock_orb.call_count == 1
        call_args = " ".join(mock_orb.call_args[0])
        assert "nix-channel" in call_args
        assert "--add" not in call_args


# --- rebuild ---


class TestRebuild:
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        rebuild("dev")

    @patch("subprocess.run")
    def test_failure_raises_deploy_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        with pytest.raises(DeployError, match="nixos-rebuild switch failed"):
            rebuild("dev")

    @patch("subprocess.run")
    def test_orb_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(DeployError, match="OrbStack CLI not found"):
            rebuild("dev")

    @patch("subprocess.run")
    def test_error_message_includes_hints(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        with pytest.raises(DeployError) as exc_info:
            rebuild("dev")
        assert "search.nixos.org" in str(exc_info.value)
        assert "--show-trace" in str(exc_info.value)


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
            "--memory", "8G",
            "--cpus", "4",
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
    def test_skips_create_when_exists(
        self, mock_validate, mock_orb, mock_exists,
        mock_create, mock_copy, mock_channel, mock_rebuild, capsys,
    ):
        main()
        captured = capsys.readouterr()
        mock_create.assert_not_called()
        assert "already exists" in captured.out

    @patch("sys.argv", ["deploy.py"])
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
        with patch("sys.argv", ["deploy.py", "custom"]):
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
        with patch("deploy.SCRIPT_DIR", tmp_path):
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
    def test_keyboard_interrupt_exits_130(
        self, mock_validate, mock_orb, mock_exists,
        mock_copy, mock_channel, mock_rebuild,
    ):
        with pytest.raises(SystemExit, match="130"):
            main()
