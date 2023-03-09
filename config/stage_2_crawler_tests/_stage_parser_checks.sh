set -ex

echo -e '\n'
echo "Parser checks"

TARGET_SCORE=$(bash config/get_mark.sh lab_5_scrapper)

if [[ ${TARGET_SCORE} != 0 ]]; then
  bash config/stage_2_crawler_tests/s2_3_check_parser.sh
else
  echo "Skipping stage"
fi
