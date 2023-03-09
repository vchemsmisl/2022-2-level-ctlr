set -x

echo "Stage: Verify core utils"

source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH:"

python -m pytest -m "core_utils"

ret=$?
if [ "$ret" = 5 ]; then
  echo "No tests collected.  Exiting with 0 (instead of 5)."
  exit 0
fi

echo "Core utils checks result (should be 0): $ret"

exit "$ret"

