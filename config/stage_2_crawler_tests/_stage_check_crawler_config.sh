set -ex

echo -e '\n'
echo 'Running crawler config check...'

TARGET_SCORE=$(bash config/get_mark.sh lab_5_scrapper)
echo $TARGET_SCORE

source venv/bin/activate

if [[ ${TARGET_SCORE} != 0 ]]; then
  python -m pytest -m "mark10 and stage_2_1_crawler_config_check" --capture=no
else
  echo "Skipping stage"
fi
