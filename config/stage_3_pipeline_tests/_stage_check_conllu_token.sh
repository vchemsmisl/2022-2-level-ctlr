set -ex

echo -e '\n'
echo "Check conllu token is implemented correctly"

TARGET_SCORE=$(bash config/get_mark.sh lab_6_pipeline)

if [[ ${TARGET_SCORE} != 0 ]]; then
  bash config/stage_3_pipeline_tests/s3_3_conllu_token.sh
else
  echo "Skip stage"
fi
