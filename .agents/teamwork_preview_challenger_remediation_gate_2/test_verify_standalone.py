"""Test ALLOW_MAIN_COMMIT=1 agy-verify in isolation after clean-logs."""

import asyncio
import os
from agy_graphify.tasks import clean_logs_action
from agy_graphify.verify import EnvironmentVerifier, Decision


async def main():
    # 1. First clean logs
    await clean_logs_action()

    # 2. Set ALLOW_MAIN_COMMIT=1
    os.environ["ALLOW_MAIN_COMMIT"] = "1"

    # 3. Run verifier check
    verifier = EnvironmentVerifier()
    res = await verifier.run_check(use_cache=False)

    print("DECISION:", res.decision.value)
    print("REASON:", res.reason)

    assert res.decision == Decision.allow, f"Expected allow, got {res.decision}: {res.reason}"
    print("✓ Standalone verification passed!")


if __name__ == "__main__":
    asyncio.run(main())
