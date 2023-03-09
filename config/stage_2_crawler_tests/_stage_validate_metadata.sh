set -ex

echo -e '\n'
echo "Validate raw data"

TARGET_SCORE=$(bash config/get_mark.sh lab_5_scrapper)

if [[ ${TARGET_SCORE} != 0 ]]; then
  ls
  mkdir -p tmp/articles
  mv *_raw.txt tmp/articles
  if [[ ${TARGET_SCORE} != 4 ]]; then
    mv *_meta.json tmp/articles
  fi
  bash config/stage_2_crawler_tests/s2_5_check_raw_data.sh
else
  echo "Skipping stage"
fi
