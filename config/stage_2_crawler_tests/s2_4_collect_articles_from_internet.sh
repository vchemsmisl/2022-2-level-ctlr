set -ex

echo "Stage: Downloading articles"

source venv/bin/activate
export PYTHONPATH=$(pwd):$PYTHONPATH

python config/config_param_changer.py --config_path="lab_5_scrapper/scrapper_config.json"

echo "Changed config params"

python lab_5_scrapper/scrapper.py

echo "Collected dataset"

echo "Checking volume of files"

TARGET_SCORE=$(bash config/get_mark.sh lab_5_scrapper)

if [[ ${TARGET_SCORE} == 4 ]]; then
  echo "Running score four checks"
  python -m pytest -m "mark4 and stage_2_4_dataset_volume_check" --capture=no
else
  python -m pytest -m "mark10 and stage_2_4_dataset_volume_check" --capture=no
fi

echo "Volume is correct"
