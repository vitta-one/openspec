"""Local QA login guard should reject production-like targets."""
from unittest.mock import patch
import pytest
from scripts import qa_local_logins

@pytest.mark.parametrize("url,flag", [
    ("postgresql+psycopg://vittaqa:pw@prod.example:5433/vitta_one_qa", "true"),
    ("postgresql+psycopg://vittaqa:pw@127.0.0.1:5432/vitta_one_qa", "true"),
    ("postgresql+psycopg://vittaqa:pw@127.0.0.1:5433/vitta_one_qa", "false"),
])
def test_reject_unsafe_target(monkeypatch, url, flag):
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", flag)
    with patch("sys.argv", ["qa_local_logins", "--role", "medico", "--email", "qa@example.invalid"]):
        with pytest.raises(SystemExit, match="Recusado"):
            qa_local_logins.main()
