# -*- coding: utf-8; -*-

from guake import paths


def test_try_to_compile_glib_schemas_skips_read_only_directory(mocker):
    mocker.patch.object(paths, "SCHEMA_DIR", "/root-owned/schemas")
    mocker.patch.object(paths.os, "access", return_value=False)
    compiler = mocker.patch.object(paths.subprocess, "check_call")

    assert paths.try_to_compile_glib_schemas() is False

    compiler.assert_not_called()
