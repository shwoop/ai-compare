import os
from unittest.mock import patch

import pytest

from tasks.clone_and_solve import make_dataset


def test_repo_url_from_env(monkeypatch):
    monkeypatch.setenv("REPO_URL", "https://github.com/test/myrepo.git")
    dataset = make_dataset()
    assert "https://github.com/test/myrepo.git" in dataset.samples[0].setup


def test_repo_url_default_when_env_not_set(monkeypatch):
    monkeypatch.delenv("REPO_URL", raising=False)
    dataset = make_dataset()
    assert "shwoop/siggy" in dataset.samples[0].setup
