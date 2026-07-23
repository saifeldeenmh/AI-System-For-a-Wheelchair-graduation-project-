from live_regontion import verify_owner


def run_face_authentication(ser=None, max_attempts=3, timeout_per_attempt=30) -> bool:
    for attempt in range(1, max_attempts + 1):
        print(f"\n[FaceAuth] Attempt {attempt} of {max_attempts}")
        success = verify_owner(ser=ser, timeout_seconds=timeout_per_attempt)

        if success:
            print("[FaceAuth] ✓ Owner verified! System starting...")
            return True
        else:
            if attempt < max_attempts:
                print(
                    f"[FaceAuth] ✗ Failed. Retrying... ({max_attempts - attempt} attempts left)")

    print("[FaceAuth] ✗ All attempts failed. Access denied.")
    return False
