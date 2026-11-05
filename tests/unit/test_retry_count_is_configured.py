def test_retry_count_is_configured():
    """R21: download retries 3 times, 60 seconds apart. No other task retries."""
    from flows import green_trips

    assert green_trips.download.retries == 3
    assert green_trips.download.retry_delay_seconds == 60
    for task in (green_trips.load, green_trips.transform, green_trips.export):
        assert not task.retries
