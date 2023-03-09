set -ex

echo -e '\n'
echo "Check files processing on student dataset"

TARGET_SCORE=$(bash config/get_mark.sh lab_6_pipeline)


if [[ ${TARGET_SCORE} != 0 ]]; then
  mkdir -p tmp/articles
  mv *_cleaned.txt tmp/articles
  mv *_raw.txt tmp/articles

  if [[ ${TARGET_SCORE} != 4 ]]; then
    mv *_meta.json tmp/articles
    mv *_morphological_conllu.conllu tmp/articles || echo "no files to move"
    mv *_full_conllu.conllu tmp/articles || echo "no files to move"
  fi
else
  echo "Skip unpacking dataset"
fi