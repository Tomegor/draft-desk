const essayEl = document.getElementById("essay");
const promptEl = document.getElementById("prompt");
const wordLimitEl = document.getElementById("wordLimit");
const promptPresetEl = document.getElementById("promptPreset");
const submitBtn = document.getElementById("submitBtn");
const liveCount = document.getElementById("liveCount");
const notesEmpty = document.getElementById("notesEmpty");
const notesContent = document.getElementById("notesContent");

// Common App essay prompts, 2026-2027 cycle (unchanged from prior years).
// Paraphrased in plain language -- word limit is 250-650 for all of them.
const COMMON_APP_PROMPTS = [
  {
    label: "1. Background, identity, interest, or talent",
    text: "Describe a background, identity, interest, or talent that is so meaningful to you that you feel your application would be incomplete without sharing this story.",
  },
  {
    label: "2. Facing a challenge or failure",
    text: "Recount a time you faced a challenge, setback, or failure. How did it affect you, and what did you learn from it?",
  },
  {
    label: "3. Questioning a belief or idea",
    text: "Describe a time you questioned or challenged a belief or idea. What sparked your thinking? What was the outcome?",
  },
  {
    label: "4. Gratitude",
    text: "Describe something someone did for you that made you happy or thankful in an unexpected way. How has this gratitude affected or motivated you?",
  },
  {
    label: "5. Personal growth",
    text: "Discuss an accomplishment, event, or realization that sparked a period of personal growth and a new understanding of yourself or others.",
  },
  {
    label: "6. A captivating topic or idea",
    text: "Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time. Why does it captivate you? Where do you go or who do you turn to when you want to learn more?",
  },
  {
    label: "7. Topic of your choice",
    text: "Share an essay on any topic of your choice -- it can be one you've already written, one that responds to a different prompt, or one of your own design.",
  },
];

function populatePromptPresets() {
  COMMON_APP_PROMPTS.forEach((p, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = p.label;
    promptPresetEl.appendChild(opt);
  });
}
populatePromptPresets();

promptPresetEl.addEventListener("change", () => {
  if (promptPresetEl.value === "") return; // custom -- leave prompt as-is
  const preset = COMMON_APP_PROMPTS[promptPresetEl.value];
  promptEl.value = preset.text;
  if (!wordLimitEl.value) wordLimitEl.value = 650;
});

function countWords(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

essayEl.addEventListener("input", () => {
  liveCount.textContent = `${countWords(essayEl.value)} words`;
});

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderNotes(data) {
  let html = "";

  html += `<div class="summary-block">
    <h3>Structure</h3>
    <p>${escapeHtml(data.structure_feedback || "")}</p>
  </div>`;

  if (data.prompt_alignment) {
    html += `<div class="summary-block">
      <h3>Answers the prompt?</h3>
      <span class="score-badge">${data.prompt_alignment.score}/5</span>
      <p>${escapeHtml(data.prompt_alignment.explanation || "")}</p>
    </div>`;
  }

  html += `<div class="summary-block">
    <h3>Voice</h3>
    <p>${escapeHtml(data.voice_feedback || "")}</p>
  </div>`;

  if (data.word_count) {
    const wc = data.word_count;
    let statusText = "";
    if (wc.status === "over") statusText = " — over your limit";
    if (wc.status === "short") statusText = " — you have room to add more";
    if (wc.status === "good") statusText = " — right in range";
    html += `<div class="summary-block">
      <h3>Word count</h3>
      <p>${wc.count}${wc.limit ? ` / ${wc.limit}` : ""}${statusText}</p>
    </div>`;
  }

  (data.strengths || []).forEach((s) => {
    html += `<div class="note-card strength">
      <div class="note-label">Strength</div>
      <p class="note-body">${escapeHtml(s)}</p>
    </div>`;
  });

  (data.cliches || []).forEach((c) => {
    html += `<div class="note-card cliche">
      <div class="note-label">Cliché</div>
      <p class="note-quote">"${escapeHtml(c.quote)}"</p>
      <p class="note-body">${escapeHtml(c.why)}</p>
    </div>`;
  });

  (data.show_dont_tell || []).forEach((t) => {
    html += `<div class="note-card tell">
      <div class="note-label">Show, don't tell</div>
      <p class="note-quote">"${escapeHtml(t.quote)}"</p>
      <p class="note-body">${escapeHtml(t.suggestion)}</p>
    </div>`;
  });

  notesContent.innerHTML = html;
  notesContent.hidden = false;
  notesEmpty.hidden = true;
}

submitBtn.addEventListener("click", async () => {
  const essay = essayEl.value.trim();
  if (!essay) {
    alert("Paste your essay draft first.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Marking up...";

  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        essay,
        prompt: promptEl.value.trim(),
        wordLimit: wordLimitEl.value || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Something went wrong.");
    }
    renderNotes(data);
  } catch (err) {
    notesContent.innerHTML = `<div class="note-card cliche"><p class="note-body">${escapeHtml(err.message)}</p></div>`;
    notesContent.hidden = false;
    notesEmpty.hidden = true;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Mark it up";
  }
});
