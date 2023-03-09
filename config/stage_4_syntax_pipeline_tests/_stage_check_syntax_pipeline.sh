set -ex

echo -e '\n'
echo "Running SyntaxPipeline"

TARGET_SCORE=$(bash config/get_mark.sh lab_6_pipeline)


if [[ ${TARGET_SCORE} != 0 ]]; then
  bash config/unpack_archived_dataset.sh
  bash config/stage_4_syntax_pipeline_tests/run_syntax_pipeline.sh
  echo "Your solution is accepted! Proceed to further tasks from your lecturer."
else
  echo "Skip stage"
fi
