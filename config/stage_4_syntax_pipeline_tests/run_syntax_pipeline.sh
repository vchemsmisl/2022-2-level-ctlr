set -ex

TARGET_SCORE=$(bash config/get_mark.sh lab_6_pipeline)

source venv/bin/activate
export PYTHONPATH=$(pwd):$PYTHONPATH

if [[ ${TARGET_SCORE} == 10 ]]; then
  python lab_6_pipeline/syntax_pipeline.py
fi
