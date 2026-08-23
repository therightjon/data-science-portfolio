import os
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
from dataclasses import dataclass
from enum import Enum
import re
from openai import OpenAI 

load_dotenv()
# Load OpenAI API key from environment variable
api_key = load_dotenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key)
except Exception: 
    client = None

#My finetuned model
MODEL_NAME = "ft:gpt-3.5-turbo-0125:personal::CXWeMjVI"

# ---------------- OPENAI CODE SNIPPET GENERATION ---------------- #
class Difficulty(str, Enum):
  BEGINNER = "BEGINNER"
  INTERMEDIATE = "INTERMEDIATE"
  ADVANCED = "ADVANCED"

# ---------------- DATA CLASS FOR SNIPPET ---------------- #
@dataclass
class SnippetData:
  code: str
  language: str
  difficulty: Difficulty

# ---------------- FUNCTION TO GENERATE SNIPPET ---------------- #
def generate_code_snippet(
  language: str,
  difficulty: Difficulty,
  prior_snippets: list[str] | None = None,
) -> SnippetData:
  prior_snippets = prior_snippets or []

# Prepare prior snippets block if any
  prior_block = ""
  if prior_snippets:
    joined = "\n\n---\n\n".join(prior_snippets[-10:])
    prior_block = f"""

Previous snippets (treat as negative examples).
Do NOT reuse their structure, logic, or variable names.
Do NOT repeat any full line from them:

{joined}
"""
# Construct system instruction
  system_instruction = f"""You are a strict random code generation engine.
Your task is to provide a single, valid, compilable code snippet
in {language} for a typing practice application.

{prior_block}

Global rules:
- Treat every request as independent from earlier requests
  unless prior snippets are explicitly provided.
- If prior snippets are shown in this conversation, you must treat
  them as negative examples and avoid reusing their structure,
  logic, or variable names.

Strict Output Rules:
1. Return ONLY the raw code. Do NOT wrap it in markdown code blocks.
2. Do NOT include any comments.
3. Do NOT include any conversational text, titles, or explanations.
4. Ensure the code is between 5 and 9 lines long.
5. Use standard indentation (2 or 4 spaces).
6. Keep line lengths under 50 characters.
7. Use clear, descriptive variable names.
8. Avoid complex nested logic or dense syntax.
9. Use idiomatic patterns appropriate for {difficulty} in {language}.
10. Never reuse any full line of code from prior snippets
    mentioned in this conversation.
11. Strongly vary the task, structure, and variable names between
    calls (e.g., sometimes loops, sometimes functions, sometimes
    conditionals, different domains like math, strings, arrays).
12. Adhere strictly to these rules to ensure the output is
    suitable for typing practice. 
13. Do not repeat any code from prior snippets.
"""

  prompt = f"Generate a {difficulty.value} level code snippet."

  try:
    response = client.chat.completions.create(
      model=MODEL_NAME,
      messages=[
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt},
      ],
      temperature=0.8,
    )

    code = response.choices[0].message.content or ""

    # Aggressive cleanup to ensure no markdown remains
    code = code.strip()
    # Remove starting markdown block (e.g. ```python or ```)
    code = re.sub(r"^```[\w]*\s*", "", code)
    # Remove ending markdown block
    code = re.sub(r"\s*```$", "", code)

    return SnippetData(
      code=code.strip(),
      language=language,
      difficulty=difficulty,
    )

  except Exception as e:
    print("OpenAI generation failed:", e)
    return SnippetData(
      code=(
        'print("Connection Error: Unable to fetch snippet.")\n'
        'print("Please check your API Key and internet connection.")'
      ),
      language="System",
      difficulty=Difficulty.BEGINNER,
    )

st.set_page_config(page_title="CodeType Trainer", page_icon="⌨️", layout="centered")

st.title("CodeType Trainer ⌨️")
st.caption("Master your coding syntax with real-time typing practice.")

languages = ["Python", "JavaScript", "HTML", "Java", "C++", "Ruby", "Go", "C#", "PHP", "Swift"]
language = st.selectbox("Language", languages)

difficulty = st.selectbox(
  "Difficulty",
  list(Difficulty),
  format_func=lambda d: d.value.title(),
)

# Button to explicitly request a new snippet without reloading the whole app
new_snippet_requested = st.button("New Snippet")

if new_snippet_requested:
  # Clear stored snippet so the next run regenerates with
  # the current language + difficulty, just like when they change.
  st.session_state.pop("snippet_data", None)
  st.session_state.pop("snippet_lang", None)
  st.session_state.pop("snippet_diff", None)

if client is None:
  snippet = (
    'print("Connection Error: Unable to fetch snippet.")\n'
    'print("Please check your API Key and internet connection.")'
  )
else:
  snippet_data = st.session_state.get("snippet_data")
  stored_lang = st.session_state.get("snippet_lang")
  stored_diff = st.session_state.get("snippet_diff")
  if (
    snippet_data is None
    or stored_lang != language
    or stored_diff != difficulty
  ):
    with st.spinner("Generating code snippet..."):
      prior_snips = st.session_state.get("snippet_history", [])
      snippet_data = generate_code_snippet(
        language,
        difficulty,
        prior_snippets=prior_snips,
      )
    st.session_state["snippet_data"] = snippet_data
    st.session_state["snippet_lang"] = language
    st.session_state["snippet_diff"] = difficulty
  snippet = snippet_data.code

# Track prior snippets in session_state to reduce duplicates
if "snippet_history" not in st.session_state:
  st.session_state["snippet_history"] = []

if snippet and "Connection Error" not in snippet:
  history = st.session_state["snippet_history"]
  if snippet not in history:
    history.append(snippet)
    # keep only last 10 snippets
    st.session_state["snippet_history"] = history[-10:]

# simple HTML escaping for putting snippet text inside <pre>
def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

escaped_snippet = escape_html(snippet)

# ---------------- JS + HTML COMPONENT ---------------- #

html = f"""
<div id="trainer-root" style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; color:#e5e7eb; background:#020617; padding:16px; border-radius:16px; border:1px solid #1f2937; max-width:900px; margin:0 auto;">
  <div style="margin-bottom:10px; font-size:14px; color:#9ca3af; text-transform:uppercase; letter-spacing:0.12em;">
    Target Snippet ({language})
  </div>

  <!-- raw snippet (hidden) -->
  <pre id="snippet-raw" style="display:none; white-space:pre-wrap;">{escaped_snippet}</pre>

  <!-- rendered snippet -->
  <div style="border-radius:12px; background:#020617; border:1px solid #334155; padding:14px; margin-bottom:16px; max-height:none; overflow:auto;">
    <pre id="snippet-display" style="margin:0; white-space:pre-wrap; font-family:'Source Code Pro', Menlo, monospace; font-size:16px; line-height:1.5;"></pre>
  </div>

  <div style="margin-bottom:6px; font-size:14px; color:#9ca3af; text-transform:uppercase; letter-spacing:0.12em;">
    Type Here
  </div>
  <textarea
    id="typing-area"
    rows="6"
    style="width:100%; box-sizing:border-box; border-radius:12px; border:1px solid #334155; background:#020617; color:#e5e7eb; padding:10px 12px; font-family:'Source Code Pro', Menlo, monospace; font-size:16px; line-height:1.5; outline:none; resize:none; overflow:hidden; min-height:260px;"
    placeholder="Start typing the code above..."
  ></textarea>

  <div id="stats" style="margin-top:16px; display:flex; gap:16px; flex-wrap:wrap; font-size:13px; color:#9ca3af;">
    <div><span style="text-transform:uppercase; letter-spacing:0.12em;">Speed</span><br><span id="stat-wpm" style="font-size:20px; color:#e5e7eb;">0 WPM</span></div>
    <div><span style="text-transform:uppercase; letter-spacing:0.12em;">Accuracy</span><br><span id="stat-acc" style="font-size:20px; color:#e5e7eb;">0%</span></div>
    <div><span style="text-transform:uppercase; letter-spacing:0.12em;">Errors</span><br><span id="stat-err" style="font-size:20px; color:#e5e7eb;">0</span></div>
    <div><span style="text-transform:uppercase; letter-spacing:0.12em;">Time</span><br><span id="stat-time" style="font-size:20px; color:#e5e7eb;">0.00 s</span></div>
  </div>

  <div id="status-message" style="margin-top:14px; font-size:14px; color:#a5b4fc;"></div>
</div>
<div class="attribution" style="margin-top:12px; font-size:12px; color:#FFF; text-align:center;"> 
Presented by Jon Steen | Powered by Streamlit (Python & JavaScript) | OpenAI GPT-3.5 Turbo Fine-tuned Model
</div>
<script>
(function() {{
  const rawEl = document.getElementById("snippet-raw");
  const displayEl = document.getElementById("snippet-display");
  const inputEl = document.getElementById("typing-area");
  const statusEl = document.getElementById("status-message");

  const wpmEl = document.getElementById("stat-wpm");
  const accEl = document.getElementById("stat-acc");
  const errEl = document.getElementById("stat-err");
  const timeEl = document.getElementById("stat-time");

  if (!rawEl || !displayEl || !inputEl) return;

  const snippet = rawEl.innerText;  // full text including newlines
  let started = false;
  let finished = false;
  let startTime = 0;
  let endTime = 0;

  // --------------- RENDER SNIPPET --------------- //
  function renderSnippet() {{
    const typed = inputEl.value;
    const L = snippet.length;
    const T = typed.length;
    let html = "";

    for (let i = 0; i < L; i++) {{
      const ch = snippet[i];
      const esc = ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch === "&" ? "&amp;" : ch;
      if (i < T) {{
        if (typed[i] === ch) {{
          html += '<span style="color:#4ade80;">' + esc + '</span>';  // green
        }} else {{
          html += '<span style="color:#f87171; background:rgba(248,113,113,0.16);">' + esc + '</span>';  // red
        }}
      }} else {{
        html += '<span style="color:#475569;">' + esc + '</span>';  // muted
      }}
    }}

    // cursor
    if (!finished && started && T < L) {{
      html += '<span style="border-right:2px solid #38bdf8;">&nbsp;</span>';
    }}

    displayEl.innerHTML = html;
  }}

  // --------------- STATS UPDATE --------------- //
  function updateStats() {{
    if (!started) {{
      wpmEl.textContent = "0 WPM";
      accEl.textContent = "0%";
      errEl.textContent = "0";
      timeEl.textContent = "0.00 s";
      return;
    }}

    // elapsed time
    const now = finished ? endTime : performance.now();
    const elapsedMs = now - startTime;
    const elapsedSec = elapsedMs / 1000;
    const elapsedMin = elapsedSec / 60;

    // typed text
    const typed = inputEl.value;
    const snippetText = snippet;
    const charsTyped = typed.length;

    // WPM (5 chars per word, based on what was typed)
    const wordsTyped = charsTyped / 5;
    const wpm = elapsedMin > 0 ? Math.round(wordsTyped / elapsedMin) : 0;

    // accuracy and errors (based on typed characters)
    let matches = 0;
    const compareLen = Math.min(charsTyped, snippetText.length);
    for (let i = 0; i < compareLen; i++) {{
      if (typed[i] === snippetText[i]) {{
        matches++;
      }}
    }}

    const acc = charsTyped > 0 ? Math.round((matches / charsTyped) * 100) : 0;
    const errors = charsTyped - matches;

    wpmEl.textContent = wpm + " WPM";
    accEl.textContent = acc + "%";
    errEl.textContent = String(errors);
    timeEl.textContent = elapsedSec.toFixed(2) + " s";
  }}


  function showCompletionUI() {{
    statusEl.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span>✅ Snippet completed!</span>
      </div>
      <div style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;">
        <button id="retry-btn" style="padding:8px 16px; border-radius:999px; border:1px solid #4ade80; background:transparent; color:#e5e7eb; font-size:13px; cursor:pointer;">Retry</button>
        <button id="new-btn" style="padding:8px 16px; border-radius:999px; border:1px solid #38bdf8; background:#0f172a; color:#e5e7eb; font-size:13px; cursor:pointer;">New Snippet</button>
      </div>
    `;

    const retryBtn = document.getElementById("retry-btn");
    const newBtn = document.getElementById("new-btn");

    if (retryBtn) {{
      retryBtn.addEventListener("click", () => {{
        inputEl.value = "";
        started = false;
        finished = false;
        startTime = 0;
        endTime = 0;
        statusEl.textContent = "";
        renderSnippet();
        updateStats();
        inputEl.focus();
      }});
    }}

    if (newBtn) {{
      newBtn.addEventListener("click", () => {{
        
        // Trigger Streamlit's New Snippet button via query param
        const url = new URL(window.location.href);
        url.searchParams.set("new_snippet", Date.now().toString());
        window.location.href = url.toString();
      }});
    }}
  }}

  function checkFinished() {{
    const typed = inputEl.value;
    if (!finished && typed.length === snippet.length && typed === snippet) {{
      finished = true;
      endTime = performance.now();
      showCompletionUI();
    }}
  }}

  inputEl.addEventListener("input", () => {{
    if (!started && inputEl.value.length > 0) {{
      started = true;
      startTime = performance.now();
      statusEl.textContent = "Keep going...";
    }}
    renderSnippet();
    updateStats();
    checkFinished();
    
    // Auto-grow textarea height to fit content without scrollbars
    inputEl.style.height = "auto";
    inputEl.style.height = inputEl.scrollHeight + "px";
  }});

  inputEl.addEventListener("keydown", (e) => {{
    if (e.key === "Tab") {{
      e.preventDefault();
      const start = inputEl.selectionStart;
      const end = inputEl.selectionEnd;
      const value = inputEl.value;
      const insert = "    "; 

      inputEl.value = value.slice(0, start) + insert + value.slice(end);
      const newPos = start + insert.length;
      inputEl.selectionStart = newPos;
      inputEl.selectionEnd = newPos;

      renderSnippet();
      updateStats();
      checkFinished();
    }}
  }});

  // Initial render
  renderSnippet();
  updateStats();
}})();
</script>
"""

components.html(html, height=2000, scrolling=True)