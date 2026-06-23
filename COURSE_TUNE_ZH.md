# 课程资料智能答疑助手微调方案

这个仓库已经基于 LLaMA-Factory 增加了一个 EBU5606 产品开发课程资料助手的最小改造版本。目标是用 `/Users/gumishdo/Desktop/大三下/产开` 中的产品开发 Topic 课件 PDF 构建 SFT 和 DPO 数据，微调 Qwen3 Instruct 模型，让模型更稳定地按照课程资料回答问题。

## 已添加内容

- `data/course_product_development_sft_sample.json`：产品开发 SFT 样例数据。
- `data/course_product_development_dpo_sample.json`：产品开发 DPO 偏好样例数据。
- `data/course_product_development_chunks.jsonl`：从产品开发 Topic 课件抽取出的文本块，本地生成并已加入 `.gitignore`。
- `data/course_product_development_sft_prompts.jsonl`：SFT 标注提示词，本地生成并已加入 `.gitignore`。
- `data/course_product_development_dpo_prompts.jsonl`：DPO 标注提示词，本地生成并已加入 `.gitignore`。
- `data/dataset_info.json`：新增 `course_product_development_sft` 和 `course_product_development_dpo` 两个数据集注册项。
- `examples/train_lora/qwen3_course_sft.yaml`：课程助手 SFT LoRA 配置。
- `examples/train_lora/qwen3_course_dpo.yaml`：课程助手 DPO LoRA 配置。
- `examples/inference/qwen3_course_lora.yaml`：加载课程助手 LoRA 的推理配置。
- `examples/merge_lora/qwen3_course_lora.yaml`：合并课程助手 LoRA 的导出配置。
- `scripts/course_tune_build_data.py`：从课程 PDF/PPTX/TXT/Markdown 生成文本块或标注提示词。
- `requirements/course_tune.txt`：课程资料抽取脚本需要的额外依赖。

## 数据准备

先安装课程资料抽取依赖：

```bash
pip install -r requirements/course_tune.txt
```

从你的课程资料生成 SFT 标注提示词：

```bash
python scripts/course_tune_build_data.py \
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode sft_prompts \
  --out data/course_product_development_sft_prompts.jsonl
```

生成 DPO 标注提示词：

```bash
python scripts/course_tune_build_data.py \
  --source "/Users/gumishdo/Desktop/大三下/产开" \
  --name-regex "^(EBU5606 - Topic|EBU5606_Topic 11|Product Development)" \
  --mode dpo_prompts \
  --out data/course_product_development_dpo_prompts.jsonl
```

把标注后的结果分别整理成：

- `data/course_product_development_sft_sample.json`
- `data/course_product_development_dpo_sample.json`

正式训练时可以保留文件名，也可以在 `data/dataset_info.json` 中改成新的文件名。

## 训练

SFT：

```bash
llamafactory-cli train examples/train_lora/qwen3_course_sft.yaml
```

DPO：

```bash
llamafactory-cli train examples/train_lora/qwen3_course_dpo.yaml
```

推理测试：

```bash
llamafactory-cli chat examples/inference/qwen3_course_lora.yaml
```

合并 LoRA：

```bash
llamafactory-cli export examples/merge_lora/qwen3_course_lora.yaml
```

## 简历表达

可以写成：

> 基于 LLaMA-Factory、Qwen3 和 LoRA/DPO 构建课程资料智能答疑助手，从课程 PPT/PDF 抽取文本并构造 SFT 与偏好数据，完成模型微调、偏好对齐、推理验证和 LoRA 合并导出流程。

等你完成正式数据和训练后，再补充量化指标，例如训练样本数量、验证集正确率、术语召回率、DPO 前后人工评分提升等。
