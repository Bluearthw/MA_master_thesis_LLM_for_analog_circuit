# material

This directory contains external dataset files used by the project.

## expected layout

- `material/dataset/tb_dataset/`
  - `{cir_num}/{cir_num}.cir`
  - `Port{cir_num}.txt`
  - `edited_explanation.md`

- `material/classified_dataset_from_mohsen/Dataset/`
  - `{cir_num}/detected_class.txt`

## instructions

1. Place your dataset files under `material/dataset/tb_dataset/`.
2. Place classified dataset files under `material/classified_dataset_from_mohsen/Dataset/`.
3. The actual dataset files are intentionally ignored by `.gitignore`.
4. Keep this README in the repo to document the expected layout.
