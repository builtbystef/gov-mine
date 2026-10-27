from datetime import UTC, date, datetime

from gov_mine.modules.extract.service import latest_date, window_cutoff


def test_the_cutoff_is_five_years_before_the_day():
    assert window_cutoff(date(2026, 10, 27)) == date(2021, 10, 27)
    assert window_cutoff(date(2028, 2, 29)) == date(2023, 2, 28)


def test_a_documents_date_is_the_latest_it_states():
    first_published = datetime(2019, 6, 1, tzinfo=UTC)
    updated = {"name": "Dunn House", "phase": "Delivery", "start_date": "2024-03-01"}

    assert latest_date(first_published, [updated]) == date(2024, 3, 1)
    assert latest_date(first_published, [{"name": "Dunn House"}]) == date(2019, 6, 1)
    assert latest_date(None, [{"name": "2019-06-01 is not a date field"}]) is None
