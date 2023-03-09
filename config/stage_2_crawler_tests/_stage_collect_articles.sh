set -ex

echo -e '\n'
echo 'Collect articles...'

TARGET_SCORE=$(bash config/get_mark.sh lab_5_scrapper)

if [[ ${TARGET_SCORE} != 0 ]]; then
  bash config/stage_2_crawler_tests/s2_4_collect_articles_from_internet.sh
  ls -la tmp/articles
else
  echo "Skipping stage"
fi
