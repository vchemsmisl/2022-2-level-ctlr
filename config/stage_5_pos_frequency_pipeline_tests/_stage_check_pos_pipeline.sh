set -ex

echo -e '\n'
echo "Check files processing on student dataset"

TARGET_SCORE=$(bash config/get_mark.sh lab_6_pipeline)


if [[ ${TARGET_SCORE} != 0 ]]; then
  bash config/unpack_archived_dataset.sh
  bash config/stage_5_pos_frequency_pipeline_tests/run_pos_frequency_pipeline.sh
  bash config/stage_5_pos_frequency_pipeline_tests/s4_pos_frequency_pipeline.sh
  echo "Your solution is accepted! Proceed to further tasks from your lecturer."
else
  echo "Skip stage"
fi
