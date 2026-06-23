<p align="right">

English · [中文](README_zh.md)

</p>

<h1 align="center">CourseTune Product Development</h1>
<p align="center">
  <strong>A lightweight Qwen3 LoRA/DPO fine-tuning project for the EBU5606 Product Development course.</strong>
  <br />
  <em>Course PDF extraction · SFT dataset construction · LoRA fine-tuning · Chinese test UI</em>
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
| Course-focused dataset | Builds training data from EBU5606 Product Development lecture PDFs. |
| Source-bound extraction | Converts local PDF/PPTX/TXT/Markdown files into JSONL chunks and annotation prompts. |
| SFT and DPO samples | Includes reviewed sample data for supervised fine-tuning and preference alignment. |
| Training configs | Provides Qwen3 LoRA SFT, DPO, inference, and merge YAML files for LLaMA-Factory. |
| Chinese test UI | Provides a browser UI that connects to a local OpenAI-compatible model API. |
| Public-safe repository | Generated chunks and annotation prompts are ignored because they may contain course material text. |

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Build Product Development SFT Data

```bash
python scripts/course_tune_build_data.py \
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode sft_dataset \
  --seed-json data/course_product_development_sft_sample.json \
  --seed-repeat 20 \
  --out data/course_product_development_sft.json
```

### Train

```bash
llamafactory-cli train examples/train_lora/qwen3_course_sft.yaml
llamafactory-cli train examples/train_lora/qwen3_course_dpo.yaml
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
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode chunks \
  --out data/course_product_development_chunks.jsonl
```

The local extraction generated `948` source chunks, `948` SFT annotation prompts, `948` DPO annotation prompts, `1996` SFT training samples, and `948` DPO preference samples. The SFT dataset contains `1896` automatically extracted samples plus `5` reviewed seed samples repeated `20` times. Generated files that contain course text are ignored by Git.

### Generate SFT Training Data

```bash
python scripts/course_tune_build_data.py \
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode sft_dataset \
  --seed-json data/course_product_development_sft_sample.json \
  --seed-repeat 20 \
  --out data/course_product_development_sft.json
```

### Generate DPO Annotation Prompts

```bash
python scripts/course_tune_build_data.py \
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode dpo_prompts \
  --out data/course_product_development_dpo_prompts.jsonl
```

### Generate DPO Training Data

```bash
python scripts/course_tune_build_data.py \
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode dpo_dataset \
  --out data/course_product_development_dpo.json
```

### Merge LoRA

```bash
llamafactory-cli export examples/merge_lora/qwen3_course_lora.yaml
```

## UI Preview

The Chinese test UI lives in `web/index.html` and uses `web/server.py` to proxy requests to the local model API.

![CourseTune Chinese test UI](docs/course-assistant-ui.png)

## Training Result

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
| Local adapter path | `saves/qwen3-4b-product-development/lora/sft` |

Verification prompt:

```text
列出 generic product development process 的六个阶段。
```

The model returned the six course stages: `Planning`, `Concept development`, `System-level design`, `Detail design`, `Testing and refinement`, and `Production ramp-up`. The same prompt was also verified through the `/api/chat` web proxy.

## Architecture

```mermaid
graph TD
    A[EBU5606 Lecture PDFs] --> B[course_tune_build_data.py]
    B --> C[Source Chunks JSONL]
    C --> D[SFT Dataset]
    C --> E[DPO Dataset]
    D --> F[LLaMA-Factory SFT]
    E --> G[LLaMA-Factory DPO]
    F --> H[LLaMA-Factory Training]
    G --> H
    H --> I[Course LoRA Adapter]
    I --> J[Chat / Export]
```

## Project Structure

```text
data/
├── course_product_development_sft_sample.json
├── course_product_development_dpo_sample.json
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
| Data extraction | `pypdf`, `python-pptx` | Extracts course PDF/PPTX content. |
| Training method | LoRA, DPO | Keeps training efficient and adds preference alignment. |

## Upstream

This project uses [hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) as an external fine-tuning runtime.

## License

[Apache-2.0](LICENSE)
