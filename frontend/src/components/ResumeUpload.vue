<template>
  <div class="resume-page">
    <div class="bg-grid"></div>
    <div class="bg-glow bg-glow-1"></div>
    <div class="bg-glow bg-glow-2"></div>

    <section class="hero">
      <div class="hero-left">
        <div class="hero-badge">
          <span class="dot"></span>
          Resume Intelligence Workspace
        </div>
        <h1 class="hero-title">
          AI 简历优化助手
        </h1>
        <p class="hero-desc">
          上传 PDF 简历，自动解析模块结构，定位问题，生成修改建议与改写示例。
          让你的简历从“信息堆砌”变成“有结果感的表达”。
        </p>

        <div class="hero-tags">
          <span class="tag">PDF 解析</span>
          <span class="tag">模块诊断</span>
          <span class="tag">改写建议</span>
          <span class="tag">一键复制</span>
        </div>
      </div>

      <div class="hero-right">
        <div class="status-panel">
          <div class="status-top">
            <div class="status-title">当前状态</div>
            <div class="status-chip-row">
              <span v-if="loading" class="chip chip-info">解析中</span>
              <span v-else-if="resumeId" class="chip chip-success">已完成</span>
              <span v-else class="chip chip-muted">待上传</span>
            </div>
          </div>

          <div class="status-list">
            <div class="status-item">
              <span class="status-label">文件</span>
              <span class="status-value">{{ file?.name || "未选择" }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">模块数</span>
              <span class="status-value">{{ sections.length || 0 }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">resumeId</span>
              <span class="status-value">{{ resumeId ?? "--" }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="upload-card glass-card">
      <div class="upload-header">
        <div>
          <div class="section-kicker">STEP 1</div>
          <h2 class="section-title">上传并解析你的 PDF 简历</h2>
          <p class="section-desc">
            系统会先提取简历原文并分块，再基于每个模块生成问题、建议和改写示例。
          </p>
        </div>
      </div>

      <div class="upload-main">
        <label class="upload-box">
          <input
            class="file-input"
            type="file"
            accept="application/pdf"
            @change="onFileChange"
          />
          <div class="upload-icon">PDF</div>
          <div class="upload-copy">
            <div class="upload-title">
              {{ file ? "已选择文件" : "点击选择 PDF 简历" }}
            </div>
            <div class="upload-subtitle">
              {{ file?.name || "支持 PDF 格式，建议上传排版清晰的中文或英文简历" }}
            </div>
          </div>
        </label>

        <button class="primary-btn" :disabled="!file || loading" @click="handleUpload">
          <span v-if="loading" class="btn-loading"></span>
          {{ loading ? "正在解析中..." : "开始解析并生成建议" }}
        </button>
      </div>

      <div class="upload-footer">
        <p v-if="loading" class="hint">
          模型处理中，请稍候，系统正在识别简历结构并生成模块级建议。
        </p>
        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </section>

    <section v-if="resumeId" class="stats-row">
      <div class="metric-card glass-card">
        <div class="metric-label">识别模块</div>
        <div class="metric-value">{{ sections.length }}</div>
      </div>
      <div class="metric-card glass-card">
        <div class="metric-label">问题条数</div>
        <div class="metric-value">{{ totalIssues }}</div>
      </div>
      <div class="metric-card glass-card">
        <div class="metric-label">建议条数</div>
        <div class="metric-value">{{ totalRecommendations }}</div>
      </div>
      <div class="metric-card glass-card">
        <div class="metric-label">当前选中</div>
        <div class="metric-value metric-value-small">
          {{ selectedSection?.name || "未选择" }}
        </div>
      </div>
    </section>

    <section v-if="resumeId" class="workspace glass-card">
      <div class="workspace-top">
        <div>
          <div class="section-kicker">STEP 2</div>
          <h2 class="section-title">原简历内容与优化建议联动查看</h2>
          <p class="section-desc">
            左侧查看模块原文，右侧查看该模块的问题、建议与改写示例。
          </p>
        </div>

        <div class="toolbar">
          <div class="toolbar-meta">resumeId：{{ resumeId }}</div>
          <button class="ghost-btn" :class="{ active: locked }" @click="toggleLock">
            {{ locked ? "已锁定当前模块" : "锁定当前模块" }}
          </button>
        </div>
      </div>

      <div class="workspace-body">
        <aside class="left-pane">
          <div class="pane-head">
            <div class="pane-title">原简历 Sections</div>
            <div class="pane-meta">{{ sections.length }} 个模块</div>
          </div>

          <div v-if="sections.length" class="section-list" role="list">
            <div
              v-for="(s, idx) in sections"
              :key="idx"
              class="section-card"
              :class="{ active: idx === selectedIdx }"
              @mouseenter="onHoverSelect(idx)"
              @click="onClickSelect(idx)"
            >
              <div class="section-card-top">
                <div class="section-main">
                  <div class="section-index">{{ String(idx + 1).padStart(2, "0") }}</div>
                  <div class="section-name-wrap">
                    <div class="section-name">{{ s.name }}</div>
                    <div class="section-submeta">
                      {{ getSectionIssueCount(s.name, idx) }} 个问题 ·
                      {{ getSectionRecommendationCount(s.name, idx) }} 条建议
                    </div>
                  </div>
                </div>

                <button
                  class="mini-btn"
                  :title="expandedMap[idx] ? '收起全文' : '展开全文'"
                  @click.stop="toggleExpanded(idx)"
                >
                  {{ expandedMap[idx] ? "收起" : "展开" }}
                </button>
              </div>

              <div class="section-content" :class="{ clamp: !expandedMap[idx] }">
                {{ s.content }}
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-title">暂无解析结果</div>
            <div class="empty-desc">上传 PDF 后，这里会展示自动识别出的简历模块。</div>
          </div>
        </aside>

        <main class="right-pane">
          <div class="pane-head">
            <div class="pane-title">模块问题与修改建议</div>
            <div class="pane-meta">悬停或点击左侧模块查看</div>
          </div>

          <div v-if="suggestions" class="right-scroll">
            <div class="overall-card">
              <div class="card-label">整体总结</div>
              <div class="overall-text">
                {{ suggestions.overall_summary || "暂无整体总结" }}
              </div>
            </div>

            <div v-if="selectedIdx !== null && selectedSection" class="detail-card">
              <div class="detail-card-head">
                <div>
                  <div class="card-label">当前模块</div>
                  <div class="detail-name">{{ selectedSection.name }}</div>
                </div>

                <button
                  v-if="selectedSection.rewrite_example"
                  class="copy-btn"
                  @click="copyRewrite"
                >
                  {{ copied ? "已复制" : "复制改写" }}
                </button>
              </div>

              <div class="detail-grid">
                <div class="info-block">
                  <div class="info-title">存在的问题</div>
                  <ul v-if="selectedSection.issues?.length" class="issue-list">
                    <li
                      v-for="(x, i) in selectedSection.issues"
                      :key="i"
                      class="issue-pill"
                    >
                      {{ x }}
                    </li>
                  </ul>
                  <div v-else class="subtle-empty">暂无明显问题</div>
                </div>

                <div class="info-block">
                  <div class="info-title">优化建议</div>
                  <ul v-if="selectedSection.recommendations?.length" class="advice-list">
                    <li
                      v-for="(x, i) in selectedSection.recommendations"
                      :key="i"
                    >
                      {{ x }}
                    </li>
                  </ul>
                  <div v-else class="subtle-empty">暂无建议</div>
                </div>
              </div>

              <div class="rewrite-card">
                <div class="info-title">改写示例</div>
                <div v-if="selectedSection.rewrite_example" class="rewrite-body">
                  {{ selectedSection.rewrite_example }}
                </div>
                <div v-else class="subtle-empty">当前模块暂无改写示例</div>
              </div>
            </div>

            <div v-else class="empty-state">
              <div class="empty-title">请选择左侧模块</div>
              <div class="empty-desc">选择后即可查看该模块的具体问题与修改建议。</div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-title">尚未生成建议</div>
            <div class="empty-desc">解析完成后，这里会展示整体总结和模块级优化建议。</div>
          </div>
        </main>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { generateSuggestions, ocrResume } from "../api/client";
import type { OcrResponse, SuggestionsResponse, Section } from "../types";

const file = ref<File | null>(null);
const error = ref<string>("");

const loading = ref(false);
const resumeId = ref<number | null>(null);
const sections = ref<Section[]>([]);
const suggestions = ref<SuggestionsResponse | null>(null);
const selectedIdx = ref<number | null>(null);
const locked = ref(false);
const expandedMap = ref<Record<number, boolean>>({});
const copied = ref(false);

const selectedSection = computed(() => {
  if (selectedIdx.value === null) return null;
  const idx = selectedIdx.value;
  const sec = sections.value[idx];
  if (!sec) return null;

  const items = suggestions.value?.items || [];
  const byName = items.find((it) => it.name === sec.name);
  return byName || items[idx] || null;
});

const totalIssues = computed(() => {
  const items = suggestions.value?.items || [];
  return items.reduce((sum, item) => sum + (item.issues?.length || 0), 0);
});

const totalRecommendations = computed(() => {
  const items = suggestions.value?.items || [];
  return items.reduce((sum, item) => sum + (item.recommendations?.length || 0), 0);
});

watch(
  () => sections.value,
  (v) => {
    if (!v.length) {
      selectedIdx.value = null;
      locked.value = false;
      expandedMap.value = {};
      return;
    }
    if (selectedIdx.value === null) selectedIdx.value = 0;
  },
  { immediate: true }
);

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const f = input.files?.[0] || null;
  file.value = f;
  error.value = "";
}

async function handleUpload() {
  if (!file.value) return;

  loading.value = true;
  error.value = "";
  resumeId.value = null;
  sections.value = [];
  suggestions.value = null;
  selectedIdx.value = null;
  locked.value = false;
  expandedMap.value = {};
  copied.value = false;

  try {
    const ocr: OcrResponse = await ocrResume(file.value);
    resumeId.value = ocr.resumeId;
    sections.value = Array.isArray(ocr.sections) ? (ocr.sections as Section[]) : [];

    const sug = await generateSuggestions(ocr.resumeId);
    suggestions.value = sug;
  } catch (e: any) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

function onHoverSelect(idx: number) {
  if (locked.value) return;
  selectedIdx.value = idx;
}

function onClickSelect(idx: number) {
  selectedIdx.value = idx;
}

function toggleLock() {
  locked.value = !locked.value;
}

function toggleExpanded(idx: number) {
  expandedMap.value = {
    ...expandedMap.value,
    [idx]: !expandedMap.value[idx],
  };
}

function getMatchedSuggestion(name: string, idx: number) {
  const items = suggestions.value?.items || [];
  return items.find((it) => it.name === name) || items[idx] || null;
}

function getSectionIssueCount(name: string, idx: number) {
  const item = getMatchedSuggestion(name, idx);
  return item?.issues?.length || 0;
}

function getSectionRecommendationCount(name: string, idx: number) {
  const item = getMatchedSuggestion(name, idx);
  return item?.recommendations?.length || 0;
}

async function copyRewrite() {
  const text = selectedSection.value?.rewrite_example;
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const el = document.createElement("textarea");
    el.value = text;
    el.style.position = "fixed";
    el.style.left = "-9999px";
    document.body.appendChild(el);
    el.focus();
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
  }

  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 1600);
}
</script>

<style scoped>
:deep(*) {
  box-sizing: border-box;
}

.resume-page {
  position: relative;
  max-width: 1280px;
  margin: 0 auto;
  padding: 28px 18px 40px;
  color: #e5eefc;
  font-family:
    Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(68, 103, 255, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(0, 224, 193, 0.12), transparent 22%),
    linear-gradient(180deg, #07111f 0%, #0b1424 38%, #0d1729 100%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(255,255,255,0.12));
  pointer-events: none;
}

.bg-glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(60px);
  pointer-events: none;
}

.bg-glow-1 {
  top: -80px;
  left: -20px;
  width: 260px;
  height: 260px;
  background: rgba(76, 110, 245, 0.25);
}

.bg-glow-2 {
  right: -40px;
  top: 80px;
  width: 220px;
  height: 220px;
  background: rgba(34, 197, 94, 0.15);
}

.hero,
.upload-card,
.stats-row,
.workspace {
  position: relative;
  z-index: 1;
}

.glass-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(11, 20, 36, 0.72);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
  gap: 18px;
  align-items: stretch;
  margin-bottom: 20px;
}

.hero-left,
.hero-right {
  min-width: 0;
}

.hero-left {
  padding: 24px 6px 12px 2px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  color: #c8d7f2;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border: 1px solid rgba(125, 149, 255, 0.18);
  background: rgba(91, 114, 255, 0.08);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #66a3ff, #4ff1d2);
  box-shadow: 0 0 16px rgba(79, 241, 210, 0.7);
}

.hero-title {
  margin: 18px 0 10px;
  font-size: clamp(34px, 4vw, 52px);
  line-height: 1.04;
  letter-spacing: -0.04em;
  color: #f7fbff;
  font-weight: 900;
}

.hero-desc {
  max-width: 760px;
  margin: 0;
  color: #9fb2cc;
  font-size: 15px;
  line-height: 1.8;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.tag {
  padding: 9px 12px;
  border-radius: 999px;
  color: #dbe7fb;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
}

.status-panel {
  height: 100%;
  padding: 18px;
  border-radius: 24px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.025)),
    rgba(10, 18, 32, 0.86);
  border: 1px solid rgba(255,255,255,0.08);
}

.status-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-title {
  color: #f5f8ff;
  font-size: 15px;
  font-weight: 800;
}

.status-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.status-list {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.status-item {
  padding: 14px 14px;
  border-radius: 16px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.06);
}

.status-label {
  color: #93a7c4;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.status-value {
  color: #f7fbff;
  font-size: 13px;
  font-weight: 800;
  text-align: right;
  word-break: break-all;
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid transparent;
}

.chip-info {
  color: #9fcbff;
  background: rgba(59, 130, 246, 0.14);
  border-color: rgba(59, 130, 246, 0.3);
}

.chip-success {
  color: #8af0be;
  background: rgba(34, 197, 94, 0.14);
  border-color: rgba(34, 197, 94, 0.3);
}

.chip-muted {
  color: #b7c3d8;
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.2);
}

.upload-card {
  border-radius: 28px;
  padding: 24px;
  margin-bottom: 18px;
}

.upload-header {
  margin-bottom: 18px;
}

.section-kicker {
  color: #7ba6ff;
  font-size: 12px;
  letter-spacing: 0.1em;
  font-weight: 800;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.section-title {
  margin: 0;
  color: #f7fbff;
  font-size: 24px;
  line-height: 1.2;
  font-weight: 900;
  letter-spacing: -0.03em;
}

.section-desc {
  margin: 10px 0 0;
  color: #94a9c7;
  font-size: 14px;
  line-height: 1.75;
}

.upload-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: stretch;
}

.upload-box {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 108px;
  padding: 18px;
  border-radius: 22px;
  cursor: pointer;
  overflow: hidden;
  border: 1px dashed rgba(125, 149, 255, 0.28);
  background:
    linear-gradient(135deg, rgba(91, 114, 255, 0.12), rgba(61, 198, 255, 0.05)),
    rgba(255,255,255,0.025);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.upload-box:hover {
  transform: translateY(-1px);
  border-color: rgba(125, 149, 255, 0.45);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.12);
}

.file-input {
  display: none;
}

.upload-icon {
  flex-shrink: 0;
  width: 58px;
  height: 58px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  color: #f7fbff;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.05em;
  background: linear-gradient(135deg, #547dff, #2dd4bf);
  box-shadow: 0 10px 24px rgba(84, 125, 255, 0.26);
}

.upload-copy {
  min-width: 0;
}

.upload-title {
  color: #f8fbff;
  font-size: 16px;
  font-weight: 800;
}

.upload-subtitle {
  margin-top: 6px;
  color: #98abc6;
  font-size: 13px;
  line-height: 1.7;
  word-break: break-all;
}

.primary-btn {
  min-width: 220px;
  padding: 0 22px;
  border: 0;
  border-radius: 18px;
  color: #06101f;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  background: linear-gradient(135deg, #dbeafe, #7dd3fc 45%, #5eead4 100%);
  box-shadow: 0 16px 30px rgba(83, 208, 255, 0.18);
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 20px 34px rgba(83, 208, 255, 0.25);
}

.primary-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.btn-loading {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-right: 8px;
  border-radius: 50%;
  border: 2px solid rgba(6, 16, 31, 0.28);
  border-top-color: #06101f;
  animation: spin 0.8s linear infinite;
  vertical-align: -2px;
}

.upload-footer {
  margin-top: 12px;
}

.hint {
  margin: 0;
  color: #9fb5d0;
  font-size: 13px;
  line-height: 1.7;
}

.error {
  margin: 0;
  color: #ff9f9f;
  font-size: 13px;
  font-weight: 700;
  white-space: pre-wrap;
  line-height: 1.7;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.metric-card {
  padding: 18px;
  border-radius: 22px;
}

.metric-label {
  color: #93a7c4;
  font-size: 13px;
  font-weight: 700;
}

.metric-value {
  margin-top: 10px;
  color: #f7fbff;
  font-size: 30px;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.04em;
}

.metric-value-small {
  font-size: 18px;
  line-height: 1.3;
  letter-spacing: -0.02em;
  word-break: break-word;
}

.workspace {
  border-radius: 28px;
  padding: 24px;
}

.workspace-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.toolbar-meta {
  color: #93a7c4;
  font-size: 13px;
  font-weight: 700;
}

.ghost-btn {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
  color: #e8f0ff;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.18s ease;
}

.ghost-btn:hover {
  border-color: rgba(125,149,255,0.35);
  background: rgba(91,114,255,0.1);
}

.ghost-btn.active {
  color: #06101f;
  border-color: transparent;
  background: linear-gradient(135deg, #c4d6ff, #82f4d4);
}

.workspace-body {
  display: grid;
  grid-template-columns: 420px minmax(0, 1fr);
  gap: 16px;
  min-height: 660px;
}

.left-pane,
.right-pane {
  min-width: 0;
  border-radius: 22px;
  padding: 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
}

.pane-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.pane-title {
  color: #f7fbff;
  font-size: 16px;
  font-weight: 900;
}

.pane-meta {
  color: #8ea6c7;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 590px;
  overflow: auto;
  padding-right: 4px;
}

.section-list::-webkit-scrollbar,
.right-scroll::-webkit-scrollbar {
  width: 10px;
}

.section-list::-webkit-scrollbar-thumb,
.right-scroll::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.12);
  border-radius: 999px;
}

.section-list::-webkit-scrollbar-track,
.right-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.section-card {
  padding: 14px;
  border-radius: 18px;
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.07);
  background:
    linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.02));
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    background 0.16s ease;
}

.section-card:hover {
  transform: translateY(-1px);
  border-color: rgba(125,149,255,0.22);
}

.section-card.active {
  border-color: rgba(94, 234, 212, 0.34);
  box-shadow:
    0 0 0 1px rgba(94, 234, 212, 0.14),
    0 14px 32px rgba(20, 184, 166, 0.08);
  background:
    linear-gradient(180deg, rgba(81, 116, 255, 0.12), rgba(94, 234, 212, 0.05)),
    rgba(255,255,255,0.03);
}

.section-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-main {
  display: flex;
  gap: 12px;
  min-width: 0;
}

.section-index {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #dce7fa;
  font-size: 12px;
  font-weight: 900;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
}

.section-name-wrap {
  min-width: 0;
}

.section-name {
  color: #f8fbff;
  font-size: 15px;
  font-weight: 900;
  line-height: 1.3;
}

.section-submeta {
  margin-top: 4px;
  color: #8ea6c7;
  font-size: 12px;
  font-weight: 700;
}

.mini-btn,
.copy-btn {
  flex-shrink: 0;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.18s ease;
}

.mini-btn {
  border: 1px solid rgba(255,255,255,0.08);
  color: #dbe7fb;
  background: rgba(255,255,255,0.04);
}

.mini-btn:hover {
  border-color: rgba(125,149,255,0.26);
  background: rgba(91,114,255,0.1);
}

.copy-btn {
  border: 0;
  color: #07111f;
  background: linear-gradient(135deg, #dce7ff, #7ae9d4);
}

.copy-btn:hover {
  transform: translateY(-1px);
}

.section-content {
  margin-top: 12px;
  color: #bdd0eb;
  font-size: 13px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.clamp {
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.right-scroll {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 590px;
  overflow: auto;
  padding-right: 4px;
}

.overall-card,
.detail-card,
.rewrite-card {
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.07);
  background: rgba(255,255,255,0.035);
}

.overall-card {
  padding: 16px;
}

.card-label {
  color: #7ba6ff;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.overall-text {
  color: #dbe7fb;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-card {
  padding: 16px;
}

.detail-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.detail-name {
  color: #f7fbff;
  font-size: 22px;
  line-height: 1.2;
  font-weight: 900;
  letter-spacing: -0.03em;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.info-block {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.025);
}

.info-title {
  margin-bottom: 10px;
  color: #f8fbff;
  font-size: 14px;
  font-weight: 900;
}

.issue-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.issue-pill {
  padding: 8px 10px;
  border-radius: 999px;
  color: #ffd8d8;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  border: 1px solid rgba(248, 113, 113, 0.2);
  background: rgba(248, 113, 113, 0.12);
}

.advice-list {
  margin: 0;
  padding-left: 18px;
  color: #dce7fa;
}

.advice-list li {
  margin-bottom: 8px;
  line-height: 1.75;
  font-size: 13px;
  font-weight: 700;
}

.rewrite-card {
  margin-top: 14px;
  padding: 14px;
}

.rewrite-body {
  padding: 14px;
  border-radius: 14px;
  color: #e9f2ff;
  font-size: 13px;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
  border: 1px solid rgba(125,149,255,0.14);
  background:
    linear-gradient(180deg, rgba(91,114,255,0.09), rgba(255,255,255,0.02));
}

.empty-state {
  padding: 32px 18px;
  border-radius: 18px;
  text-align: center;
  border: 1px dashed rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.025);
}

.empty-title {
  color: #f8fbff;
  font-size: 15px;
  font-weight: 900;
}

.empty-desc {
  margin-top: 8px;
  color: #93a7c4;
  font-size: 13px;
  line-height: 1.75;
}

.subtle-empty {
  color: #8ea6c7;
  font-size: 13px;
  line-height: 1.7;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1100px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-body {
    grid-template-columns: 1fr;
  }

  .left-pane,
  .right-pane {
    min-height: auto;
  }

  .section-list,
  .right-scroll {
    max-height: none;
  }
}

@media (max-width: 760px) {
  .resume-page {
    padding: 18px 12px 30px;
  }

  .upload-card,
  .workspace {
    padding: 16px;
    border-radius: 22px;
  }

  .upload-main {
    grid-template-columns: 1fr;
  }

  .primary-btn {
    min-width: 100%;
    min-height: 52px;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .workspace-top,
  .pane-head,
  .detail-card-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar {
    justify-content: flex-start;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 34px;
  }
}
</style>