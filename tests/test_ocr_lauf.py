"""IMPORTANT 3: SEITEN/LOG müssen unter der Repo-Wurzel liegen (ocr/seiten,
ocr/log), nicht unter strassen/ — sonst landet der OCR-Output am falschen Ort und
.gitignore (das genau diese beiden Pfade ausschließt) greift nicht.
"""
from strassen.ocr_lauf import SEITEN, LOG, WURZEL


def test_seiten_und_log_liegen_unter_ocr_in_der_repo_wurzel():
    assert SEITEN == WURZEL / "ocr" / "seiten"
    assert LOG == WURZEL / "ocr" / "log"
    assert (WURZEL / "strassen").is_dir()          # WURZEL ist die Repo-Wurzel, nicht strassen/
    assert (WURZEL / ".gitignore").read_text(encoding="utf-8").count("ocr/seiten/") == 1
