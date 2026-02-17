import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    ok_code, ok_out, ok_err = run(
        ["python", "scripts/core/validate_event.py", "contracts/schemas/order_created.schema.json", "contracts/examples/order_created.valid.json"]
    )
    bad_code, bad_out, bad_err = run(
        ["python", "scripts/core/validate_event.py", "contracts/schemas/order_created.schema.json", "contracts/examples/order_created.invalid.json"]
    )
    print("VALID RESULT:", ok_code, ok_out)
    print("INVALID RESULT:", bad_code, bad_out)
    if ok_code == 0 and bad_code != 0:
        print("TESTS PASSED")
        sys.exit(0)
    else:
        print("TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
