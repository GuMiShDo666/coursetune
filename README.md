<p align="right">

English · [中文](README_zh.md)

</p>

<h1 align="center">CourseTune</h1>
<p align="center">
  <strong>Turn your own course materials into training data and fine-tune a Qwen3 LoRA course assistant.</strong>
  <br />
  <em>Course material extraction · SFT/DPO data construction · LoRA fine-tuning · Chinese test UI</em>
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/Quick_Start-4CAF50?style=for-the-badge" alt="Quick Start" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-yellow?style=for-the-badge" alt="License" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python_3-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3" />
  <img src="https://img.shields.io/badge/LLaMA--Factory-111827?style=flat" alt="LLaMA-Factory" />
  <img src="https://img.shields.io/badge/Qwen3-2563EB?style=flat" alt="Qwen3" />
  <img src="https://img.shields.io/badge/LoRA_DPO-059669?style=flat" alt="LoRA DPO" />
</p>

## Features

| Feature | Description |
|---|---|
| Custom course materials | Put your own PDF, PPTX, TXT, or Markdown file/folder path after `--source`. |
| Source-bound extraction | Converts materials into JSONL chunks with source file and page/slide location. |
| SFT and DPO data | Generates train-ready data or annotation prompts for manual review. |
| LoRA training configs | Provides Qwen3 LoRA SFT, DPO, inference, and merge YAML files. |
| Chinese test UI | Provides a browser UI that connects to a local OpenAI-compatible model API. |
| Public-safe repository | Generated course text, datasets, and model weights are ignored by default. |

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Build SFT Data

Replace the value after `--source` with the path to your own course materials. It can be a single file or a folder.

```bash
python scripts/course_tune_build_data.py \
  --source "/path/to/your/course/materials" \
  --mode sft_dataset \
  --seed-json data/course_sft_sample.json \
  --seed-repeat 20 \
  --out data/course_sft.json
```

If you only want to include selected files, add `--name-regex`:

```bash
python scripts/course_tune_build_data.py \
  --source "/path/to/your/course/materials" \
  --name-regex "Lecture|Topic|Week" \
  --mode sft_dataset \
  --out data/course_sft.json
```

### Train

```bash
llamafactory-cli train examples/train_lora/qwen3_course_sft.yaml
```

### Start the Model API and Test UI

```bash
llamafactory-cli api examples/inference/qwen3_course_lora.yaml
python web/server.py --port 7860
```

Open `http://127.0.0.1:7860` to test the course assistant.

## Usage

### Extract Source Chunks

```bash
python scripts/course_tune_build_data.py \
  --source "/path/to/your/course/materials" \
  --mode chunks \
  --out data/course_chunks.jsonl
```

### Generate SFT Training Data

```bash
python scripts/course_tune_build_data.py \
  --source "/path/to/your/course/materials" \
  --mode sft_dataset \
  --seed-json data/course_sft_sample.json \
  --seed-repeat 20 \
  --out data/course_sft.json
```

`data/course_sft_sample.json` is a reviewed seed-data template. Replace it with high-quality examples for your own course, or remove `--seed-json` and `--seed-repeat` if you do not have reviewed seed rows yet.

### Generate DPO Annotation Prompts

```bash
python scripts/course_tune_build_data.py \
  --source "/path/to/your/course/materials" \
  --mode dpo_prompts \
  --out data/course_dpo_prompts.jsonl
```

### Generate DPO Training Data

```bash
python scripts/course_tune_build_data.py \
  --source "/path/to/your/course/materials" \
  --mode dpo_dataset \
  --out data/course_dpo.json
```

### Merge LoRA

```bash
llamafactory-cli export examples/merge_lora/qwen3_course_lora.yaml
```

## UI Preview

The Chinese test UI lives in `web/index.html` and uses `web/server.py` to proxy requests to the local model API. The preview below uses imported product-development course materials as an example conversation; replace `--source` with your own course material path to build the same workflow for another course.

![CourseTune Chinese test UI](docs/course-assistant-ui.png)

## Example Training Record

| Item | Result |
|---|---|
| GPU | NVIDIA RTX 4090 24GB |
| Runtime | Ubuntu 22.04, PyTorch 2.5.1+cu124, LLaMA-Factory 0.9.5 |
| Base model | `Qwen/Qwen3-4B-Instruct-2507` |
| Method | LoRA SFT, rank 8, BF16 |
| Training data | `1996` SFT samples |
| Steps | `250` optimization steps |
| Training time | `11m47s` |
| Final train loss | `0.8136` |
| Local adapter path | `saves/qwen3-4b-course-assistant/lora/sft` |

This is an example training record showing the cost of a single-GPU run and the expected project output. Your dataset size, loss, and runtime will depend on your own course materials, data quality, and training parameters.

## Architecture

```mermaid
graph TD
    A[Course materials PDF/PPTX/TXT/Markdown] --> B[course_tune_build_data.py]
    B --> C[Source Chunks JSONL]
    C --> D[SFT Dataset]
    C --> E[DPO Dataset]
    D --> F[LLaMA-Factory SFT]
    E --> G[LLaMA-Factory DPO]
    F --> H[Course LoRA Adapter]
    G --> H
    H --> I[Chat API / Web UI / Export]
```

## Project Structure

```text
data/
├── course_sft_sample.json
├── course_dpo_sample.json
└── dataset_info.json
docs/
└── course-assistant-ui.png
examples/
├── train_lora/
│   ├── qwen3_course_sft.yaml
│   └── qwen3_course_dpo.yaml
├── inference/
│   └── qwen3_course_lora.yaml
└── merge_lora/
    └── qwen3_course_lora.yaml
scripts/
└── course_tune_build_data.py
web/
├── index.html
└── server.py
requirements.txt
```

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Fine-tuning runtime | LLaMA-Factory | Runs SFT, DPO, LoRA merge, and chat workflows. |
| Base model | Qwen3 Instruct | Chinese-capable instruction model for course assistant tuning. |
| Data extraction | `pypdf`, `python-pptx` | Extracts PDF/PPTX course material content. |
| Training method | LoRA, DPO | Keeps training efficient and adds preference alignment. |

## Upstream

This project uses [hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) as an external fine-tuning runtime.

## License

[Apache-2.0](LICENSE)
