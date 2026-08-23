# CodeType Trainer: A Typing Practice App Powered by a Fine-Tuned LLM

An end-to-end generative AI project: build a training dataset, fine-tune a language model on it,
and ship the result as a working application. Not an analysis — a product.

## Problem

Typing practice tools generate prose, which is a poor proxy for writing code. Programmers need
practice on real syntax: brackets, indentation, operators, and language idioms. Off-the-shelf
models asked for a code snippet tend to wrap output in markdown fences and add commentary, both
of which break a typing exercise.

The fix was to fine-tune a model whose only behavior is emitting clean, executable code — no
backticks, no narration — and build an app around it.

## Approach

**1. Dataset construction.** Built 150 Python examples in OpenAI chat fine-tuning format
(`system` → `user` → `assistant`), evenly split across three difficulty tiers (50 beginner,
50 intermediate, 50 advanced). Coverage spans fundamental operations, common algorithms, data
structures, file handling, decorators, recursion, and async patterns. Every assistant response is
pure Python, which gives the model a consistent signal to imitate.

**2. Fine-tuning.** Fine-tuned `gpt-3.5-turbo-0125` through the OpenAI fine-tuning API — dataset
upload, job submission, status polling, and review of the training metrics before promoting the
resulting model.

**3. Application.** A Streamlit app that requests a snippet by language and difficulty, renders it
as a typing exercise, and scores the attempt. Two details worth calling out:

- The system prompt passes the last 10 snippets back as **negative examples**, instructing the
  model not to reuse their structure, logic, variable names, or any full line. This is a
  prompt-level fix for repetition without maintaining server-side state.
- The API key is read from the environment via `dotenv`, never hard-coded, so the repo stays safe
  to publish and the key can be rotated without touching code.

## What's in this folder

```
code/          Streamlit application source, plus the fine-tuning notebook
               (dataset upload → job submission → polling → metrics review)
data/          Fine-tuning datasets in JSONL chat format, at several iterations,
               with notes on dataset construction
deliverables/  Recorded demo video, presentation (pdf/pptx), and the exported
               fine-tuning notebook
```

## Running it

```bash
pip install streamlit openai python-dotenv
echo "OPENAI_API_KEY=sk-..." > .env
streamlit run code/codetype_trainer_app.py
```

The app points at a specific fine-tuned model ID. That model lives under the account that trained
it, so running this against a different account means re-running the fine-tuning notebook and
swapping the `MODEL_NAME` constant.

## Tools

Python · Streamlit · OpenAI API (chat completions + fine-tuning) · python-dotenv · JSONL

## Notes and limitations

- 150 training examples is small. It is enough to reliably shape output *format*, not enough to
  materially improve code *quality* over the base model.
- Fine-tuned model IDs are account-scoped and base models get deprecated — this app will need a
  retrain against a current base model to keep running long-term.
- The repetition guard is prompt-based, so it degrades if the negative-example window is exceeded.
