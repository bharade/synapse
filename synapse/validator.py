import subprocess
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """A simple data structure to hold the results of a validation run."""
    passed: bool
    stdout: str
    stderr: str

def run_tests(repo_path: Path) -> ValidationResult:
    """
    Runs the pytest test suite for the given repository.

    Args:
        repo_path: The path to the repository to test.

    Returns:
        A ValidationResult object with the outcome.
    """
    print(f"\n===== Running tests in {repo_path} =====")
    try:
        # We use subprocess.run to execute the pytest command.
        # `capture_output=True` saves stdout and stderr.
        # `text=True` decodes them as text.
        # `check=False` prevents raising an exception on non-zero exit codes (i.e., test failures).
        process = subprocess.run(
            ["python", "-m", "pytest"],
            cwd=repo_path,  # Critically, run the command *inside* the target repo
            capture_output=True,
            text=True,
            check=False,
            timeout=300  # Add a 5-minute timeout to prevent hangs
        )
        
        # Pytest returns exit code 0 on success, and other codes for failures.
        if process.returncode == 0:
            print("✅ All tests passed!")
            return ValidationResult(passed=True, stdout=process.stdout, stderr=process.stderr)
        else:
            print("❌ Tests failed!")
            return ValidationResult(passed=False, stdout=process.stdout, stderr=process.stderr)

    except FileNotFoundError:
        print("❌ Error: 'pytest' not found. Make sure the target repo's dependencies are installed.")
        return ValidationResult(passed=False, stdout="", stderr="pytest command not found.")
    except subprocess.TimeoutExpired:
        print("❌ Error: Tests timed out.")
        return ValidationResult(passed=False, stdout="", stderr="Test run timed out after 300 seconds.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during testing: {e}")
        return ValidationResult(passed=False, stdout="", stderr=str(e))