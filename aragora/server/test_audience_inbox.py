"""
Tests for AudienceInbox and TokenBucket rate limiting.
"""

import time
import threading
from aragora.server.stream import TokenBucket, AudienceInbox, AudienceMessage


def test_token_bucket():
    """Test token bucket rate limiting."""
    # 5 tokens per minute = 1 token every 12 seconds
    bucket = TokenBucket(rate_per_minute=5.0, burst_size=10)

    # Should have full tokens initially
    assert bucket.consume(10) == True
    assert bucket.consume(1) == False  # Should be empty

    # Wait for tokens to refill (at least 12 seconds for 1 token)
    time.sleep(13)

    # Should have at least 1 token now
    assert bucket.consume(1) == True


def test_audience_inbox():
    """Test thread-safe audience message queuing."""
    inbox = AudienceInbox()

    # Add some messages
    messages = [
        AudienceMessage(type="vote", loop_id="test-loop", payload={"choice": "option1"}),
        AudienceMessage(type="suggestion", loop_id="test-loop", payload={"suggestion": "Great idea!"}),
        AudienceMessage(type="vote", loop_id="test-loop", payload={"choice": "option2"}),
    ]

    for msg in messages:
        inbox.put(msg)

    # Drain messages
    drained = inbox.get_all()

    assert len(drained) == 3
    assert drained[0].type == "vote"
    assert drained[0].payload["choice"] == "option1"
    assert drained[1].type == "suggestion"
    assert drained[1].payload["suggestion"] == "Great idea!"
    assert drained[2].type == "vote"
    assert drained[2].payload["choice"] == "option2"

    # Should be empty now
    assert len(inbox.get_all()) == 0


def test_audience_inbox_thread_safety():
    """Test that AudienceInbox is thread-safe."""
    inbox = AudienceInbox()
    results = []

    def producer():
        for i in range(100):
            msg = AudienceMessage(
                type="vote",
                loop_id="test-loop",
                payload={"choice": f"option{i}"}
            )
            inbox.put(msg)

    def consumer():
        messages = inbox.get_all()
        results.append(len(messages))

    # Start producer and consumer threads
    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)

    producer_thread.start()
    producer_thread.join()  # Wait for producer to finish

    consumer_thread.start()
    consumer_thread.join()

    # Should have consumed all 100 messages
    assert sum(results) == 100


if __name__ == "__main__":
    test_token_bucket()
    print("✓ TokenBucket test passed")

    test_audience_inbox()
    print("✓ AudienceInbox test passed")

    test_audience_inbox_thread_safety()
    print("✓ AudienceInbox thread safety test passed")

    print("All tests passed!")