set -ex

echo "ConlluToken validation"
echo "Starting tests for ConlluToken"

TARGET_SCORE=$(bash config/get_mark.sh lab_6_pipeline)

source venv/bin/activate
export PYTHONPATH=$(pwd):$PYTHONPATH

if [[ ${TARGET_SCORE} == 4 ]]; then
  echo "Running score four checks"
  python -m pytest -m "mark4 and stage_3_3_conllu_token_checks" --capture=no
elif [[ ${TARGET_SCORE} == 6 ]]; then
  echo "Running score six checks"
  python -m pytest -m "mark6 and stage_3_3_conllu_token_checks" --capture=no
elif [[ ${TARGET_SCORE} == 8 ]]; then
  echo "Running score eight checks"
  python -m pytest -m "mark8 and stage_3_3_conllu_token_checks" --capture=no
fi

echo "ConlluToken is checked. Done"
