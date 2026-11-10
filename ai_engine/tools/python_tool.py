import subprocess
import tempfile
import os
import sys


class PythonTool:
    """
    Executes Python code safely inside a sandbox file.
    """

    def execute(self, code: str):

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".py",
                mode="w",
                encoding="utf-8"
            ) as f:

                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=15
            )

            os.remove(temp_file)

            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:

            return {
                "status": "error",
                "error": str(e)
            }
