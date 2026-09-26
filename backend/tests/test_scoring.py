"""Normalization, weighted fusion, and PASS/HOLD/REJECT boundary cases."""

from services import scoring_service as s


def test_normalize_qa_linear():
    assert s.normalize_qa(0) == 0
    assert s.normalize_qa(2.5) == 50
    assert s.normalize_qa(5) == 100
    assert s.normalize_qa(None) is None


def test_weights_normalized():
    assert s.normalized_weights({"resume": 60, "qa": 40}) == {"resume": 0.6, "qa": 0.4}
    assert s.normalized_weights({"resume": 1, "qa": 1}) == {"resume": 0.5, "qa": 0.5}
    assert s.normalized_weights(None) == {"resume": 0.6, "qa": 0.4}


def test_band_boundaries():
    assert s.band_for(70, 70) == "PASS"      # exactly threshold
    assert s.band_for(69.99, 70) == "HOLD"   # just below -> within margin
    assert s.band_for(55, 70) == "HOLD"      # threshold - margin inclusive
    assert s.band_for(54.99, 70) == "REJECT"  # below margin
    assert s.band_for(90, 70) == "PASS"


def test_fuse_weighted_average():
    combined, band = s.fuse(80, 60, {"resume": 50, "qa": 50}, 70)
    assert combined == 70.0
    assert band == "PASS"

    combined2, band2 = s.fuse(100, 0, {"resume": 60, "qa": 40}, 70)
    assert combined2 == 60.0
    assert band2 == "HOLD"
