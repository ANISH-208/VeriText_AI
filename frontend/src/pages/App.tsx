import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Activity, ArrowLeft, ArrowRight, BookOpenCheck, Check, ChevronDown, CircleHelp,
  Download, FileText, Files, Filter, Gauge, HelpCircle, LayoutDashboard, LoaderCircle,
  LockKeyhole, Plus, ScanSearch, ShieldCheck, Sparkles, UploadCloud, X, Library,
  Save, Trash2, Copy, Languages, Eye, BookMarked,
} from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { analyzeFiles, analyzeText, downloadReport } from '../services/api';
import { deleteSavedReference, listSavedReferences, saveReferences, toFile, type SavedReference } from '../services/referenceLibrary';
import type { HighlightRange, Match, Report, SourceCitation } from '../types';

const MAX_FILE_BYTES = 12 * 1024 * 1024;
const MAX_REFERENCES = 50;
const accepted = (file: File) => /\.(txt|pdf|docx)$/i.test(file.name) && file.size <= MAX_FILE_BYTES;
const OCR_LANGUAGES = [
  ['eng', 'English'],
];

export default function App() {
  const [mode, setMode] = useState<'reference' | 'standalone'>('reference');
  const [text, setText] = useState('');
  const [references, setReferences] = useState<File[]>([]);
  const [submission, setSubmission] = useState<File | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [filter, setFilter] = useState('all');
  const [ocrLanguage, setOcrLanguage] = useState('eng');
  const [library, setLibrary] = useState<SavedReference[]>([]);
  const [showLibrary, setShowLibrary] = useState(false);
  const [selectedLibrary, setSelectedLibrary] = useState<string[]>([]);
  const input = useRef<HTMLInputElement>(null);
  const refInput = useRef<HTMLInputElement>(null);
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;

  const refreshLibrary = async () => {
    try { setLibrary(await listSavedReferences()); }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not read the browser reference library.'); }
  };
  useEffect(() => { void refreshLibrary(); }, []);

  const addFiles = (files: FileList | null, kind: 'submission' | 'reference') => {
    if (!files) return;
    const incoming = [...files];
    const bad = incoming.find(file => !accepted(file));
    if (bad) { setError(`“${bad.name}” is unsupported or larger than 12 MB. Use TXT, PDF, or DOCX.`); return; }
    setError(''); setNotice('');
    if (kind === 'submission') setSubmission(incoming[0] || null);
    else setReferences(old => [...old, ...incoming].slice(0, MAX_REFERENCES));
  };

  const addSelectedLibrary = () => {
    const files = library.filter(item => selectedLibrary.includes(item.id)).map(toFile);
    setReferences(old => [...old, ...files].slice(0, MAX_REFERENCES));
    setShowLibrary(false); setSelectedLibrary([]); setNotice(`${files.length} saved reference${files.length === 1 ? '' : 's'} added to this analysis.`);
  };

  const saveCurrentReferences = async () => {
    if (!references.length) return;
    try {
      await saveReferences(references);
      await refreshLibrary();
      setNotice(`${references.length} reference${references.length === 1 ? '' : 's'} saved in this browser only.`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not save references.'); }
  };

  const run = async () => {
    setError(''); setNotice('');
    if (!text.trim() && !submission) { setError('Add text or select a document to analyze.'); return; }
    if (references.length > MAX_REFERENCES) { setError(`Use up to ${MAX_REFERENCES} reference documents per analysis.`); return; }
    setBusy(true);
    try {
      let result: Report;
      if (submission || references.length) result = await analyzeFiles(submission, text, mode === 'reference' ? references : [], ocrLanguage);
      else result = await analyzeText(text, [], mode === 'standalone');
      result.matches = result.matches.map(match => ({ ...match, review_status: 'to_review', review_note: '' }));
      setReport(result); setFilter('all');
    } catch (e) { setError(e instanceof Error ? e.message : 'Analysis failed. Check that the API is running.'); }
    finally { setBusy(false); }
  };

  const updateReport = (next: Report) => setReport(next);
  const exportPdf = async () => {
    if (!report) return;
    try { await downloadReport(report); }
    catch (e) { setError(e instanceof Error ? e.message : 'PDF export failed.'); }
  };
  const reset = () => { setReport(null); setError(''); setNotice(''); };

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark"><BookOpenCheck size={20}/></span><span>VeriText <b>AI</b></span></div>
      <div className="workspace-label">WORKSPACE</div>
      <button className="nav-item active"><LayoutDashboard size={17}/> Overview</button>
      <button className="nav-item" onClick={reset}><ScanSearch size={17}/> New analysis</button>
      <div className="sidebar-note"><div className="note-icon"><LockKeyhole size={16}/></div><strong>Your documents stay local</strong><p>Analysis runs on this computer. A reference is stored in this browser only if you choose Save.</p></div>
      <div className="side-footer"><span className="status-dot"/> Local analysis engine <ChevronDown size={14}/></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> {report ? 'Analysis results' : 'Overview'}</div><div className="top-actions"><span className="local-pill"><span/> Local mode</span><button className="icon-btn" aria-label="Help"><CircleHelp size={18}/></button><div className="avatar">VT</div></div></header>
      {!report ? <section className="content">
        <div className="hero"><div><div className="eyebrow"><span className="eyebrow-line"/> DOCUMENT INTEGRITY WORKSPACE</div><h1>Understand your text.<br/><em>Keep authorship clear.</em></h1><p className="hero-copy">Compare passages against your own sources, review evidence, and save a private local reference library.</p><button className="primary" onClick={() => document.getElementById('analyzer')?.scrollIntoView({ behavior: 'smooth' })}><Plus size={17}/> Start an analysis <ArrowRight size={16}/></button></div><div className="hero-art"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="doc-card"><div className="doc-top"><span/><span/><span/></div><div className="doc-line long"/><div className="doc-line"/><div className="highlight-line"/><div className="doc-line mid"/><div className="doc-line"/><div className="scan-badge"><ShieldCheck size={16}/> Privacy first</div></div><div className="spark spark-one">✳</div><div className="spark spark-two">✦</div></div></div>
        <div className="summary-grid"><div className="summary-card"><span className="summary-icon blue"><ScanSearch size={17}/></span><div><strong>Source comparison</strong><p>Lexical overlap and local semantic signals</p></div></div><div className="summary-card"><span className="summary-icon violet"><Sparkles size={17}/></span><div><strong>Explainable review</strong><p>Highlighted words, source passages, and page numbers</p></div></div><div className="summary-card"><span className="summary-icon green"><LockKeyhole size={17}/></span><div><strong>Private reference library</strong><p>Saved documents stay in this browser</p></div></div></div>
        <div className="analysis-layout" id="analyzer">
          <section className="panel editor-panel">
            <div className="panel-heading"><div><span className="step">01</span><div><h2>New analysis</h2><p>Choose how you’d like to review this document.</p></div></div><span className="secure-label"><LockKeyhole size={13}/> Private session</span></div>
            <div className="mode-switch"><button className={mode === 'reference' ? 'selected' : ''} onClick={() => setMode('reference')}><Files size={15}/> Compare with references</button><button className={mode === 'standalone' ? 'selected' : ''} onClick={() => setMode('standalone')}><Activity size={15}/> Standalone review</button></div>
            {mode === 'standalone' && <div className="info-banner"><CircleHelp size={16}/><span>No external source database is searched in standalone mode. Similarity coverage is unavailable.</span></div>}
            <div className="editor-head"><label htmlFor="text">Your text</label><div className="counts">{words.toLocaleString()} words <i/> {text.length.toLocaleString()} characters</div></div>
            <textarea id="text" value={text} onChange={event => setText(event.target.value)} placeholder="Paste your text here, or upload a document below…"/>
            <div className="upload-row"><button className="upload-box" onClick={() => input.current?.click()} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); addFiles(event.dataTransfer.files, 'submission'); }}><UploadCloud size={17}/><span><b>{submission ? submission.name : 'Upload your document'}</b><small>PDF, DOCX or TXT · up to 12 MB</small></span>{submission ? <X size={16} onClick={event => { event.stopPropagation(); setSubmission(null); }}/> : <Plus size={16}/>}<input ref={input} hidden type="file" accept=".txt,.pdf,.docx" onChange={event => addFiles(event.target.files, 'submission')}/></button><span className="or-label">OR</span><span className="paste-label"><FileText size={15}/> Paste text above</span></div>
            <div className="language-row"><Languages size={15}/><label htmlFor="ocr-language">Scanned PDF OCR language</label><select id="ocr-language" value={ocrLanguage} onChange={event => setOcrLanguage(event.target.value)}>{OCR_LANGUAGES.map(([code, label]) => <option key={code} value={code}>{label}</option>)}</select><small>Requires matching Tesseract language data.</small></div>
            {mode === 'reference' && <div className="refs" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); addFiles(event.dataTransfer.files, 'reference'); }}>
              <div className="refs-head"><div><label>Reference documents</label><p>{references.length}/{MAX_REFERENCES} selected · compare against saved or new sources</p></div><div className="ref-actions"><button className="text-btn" onClick={() => refInput.current?.click()}><Plus size={15}/> Add files</button><button className="text-btn" onClick={() => { void refreshLibrary(); setShowLibrary(value => !value); }}><Library size={15}/> Library ({library.length})</button><button className="text-btn" disabled={!references.length} onClick={() => void saveCurrentReferences()}><Save size={15}/> Save selected</button><input ref={refInput} hidden multiple type="file" accept=".txt,.pdf,.docx" onChange={event => addFiles(event.target.files, 'reference')}/></div></div>
              {showLibrary && <div className="library-box"><div className="library-head"><b>Saved on this device</b><span>Only selected references are added to the current run.</span></div>{library.length ? library.map(item => <div className="library-row" key={item.id}><label><input type="checkbox" checked={selectedLibrary.includes(item.id)} onChange={event => setSelectedLibrary(ids => event.target.checked ? [...ids, item.id] : ids.filter(id => id !== item.id))}/><FileText size={14}/><span>{item.name}<small>{(item.size / 1024).toFixed(0)} KB</small></span></label><button aria-label={`Delete saved ${item.name}`} onClick={async () => { await deleteSavedReference(item.id); await refreshLibrary(); setSelectedLibrary(ids => ids.filter(id => id !== item.id)); }}><Trash2 size={14}/></button></div>) : <p className="library-empty">No references saved yet. Add files and choose “Save selected”.</p>}<button className="primary small-primary" disabled={!selectedLibrary.length || references.length >= MAX_REFERENCES} onClick={addSelectedLibrary}>Add selected to this analysis</button></div>}
              {references.length > 0 ? <div className="file-list">{references.map((file, index) => <div className="file-item" key={`${file.name}-${index}`}><span className="file-type">{file.name.split('.').pop()?.toUpperCase()}</span><span className="file-name">{file.name}<small>{(file.size / 1024).toFixed(0)} KB</small></span><button aria-label="Remove reference" onClick={() => setReferences(items => items.filter((_, i) => i !== index))}><X size={15}/></button></div>)}</div> : <button className="dropzone" onClick={() => refInput.current?.click()}><UploadCloud size={19}/><span><b>Drop reference files here</b><small>Or browse your files · up to {MAX_REFERENCES} files</small></span></button>}
            </div>}
            {error && <div className="error">{error}</div>}{notice && <div className="success-notice"><Check size={15}/>{notice}</div>}
            <div className="submit-row"><span><ShieldCheck size={15}/> Files are processed temporarily unless saved to the local library</span><button className="primary" disabled={busy} onClick={() => void run()}>{busy ? <><LoaderCircle className="spin" size={16}/> Analyzing…</> : <>Run analysis <ArrowRight size={16}/></>}</button></div>
          </section>
          <aside className="explain-panel"><div className="explain-title"><span className="summary-icon blue"><Gauge size={17}/></span><h3>What we look for</h3></div><Explain number="1" title="Text overlap">Word and character patterns surface exact and near-exact passages.</Explain><Explain number="2" title="Meaning similarity">A local sentence-embedding model compares meaning. Set a multilingual model in backend/.env for cross-language matching.</Explain><Explain number="3" title="Review evidence">Highlighted words and page details help you verify each signal.</Explain><div className="caution"><HelpCircle size={17}/><p><b>Use results as a starting point.</b> Similarity can reflect shared topics or facts. A person should review every flagged passage.</p></div><div className="capability"><Check size={14}/> No cloud accounts or paid APIs</div></aside>
        </div>
        <footer className="page-foot"><span>VeriText AI <i/> A private workspace for careful review</span><span><LockKeyhole size={13}/> Runs locally</span></footer>
      </section> : <Results report={report} filter={filter} setFilter={setFilter} goBack={reset} updateReport={updateReport} exportPdf={() => void exportPdf()}/>}
    </main>
  </div>;
}

function Explain({ number, title, children }: { number: string; title: string; children: string }) {
  return <div className="explain-item"><span className="number">{number}</span><div><b>{title}</b><p>{children}</p></div></div>;
}

function Results({ report, filter, setFilter, goBack, updateReport, exportPdf }: { report: Report; filter: string; setFilter: (value: string) => void; goBack: () => void; updateReport: (report: Report) => void; exportPdf: () => void }) {
  const metrics = report.metrics;
  const matches = report.matches.map((match, index) => ({ match, index })).filter(({ match }) => filter === 'all' || (filter === 'lexical' ? match.category !== 'semantic' : match.category === 'semantic'));
  const chart = report.matches.map((match, index) => ({ name: `Passage ${index + 1}`, lexical: Math.round(match.lexical_score * 100), semantic: Math.round(match.semantic_score * 100) }));
  const patchMatch = (index: number, patch: Partial<Match>) => updateReport({ ...report, matches: report.matches.map((match, i) => i === index ? { ...match, ...patch } : match) });
  const patchCitation = (filename: string, patch: Partial<SourceCitation>) => {
    const citations = { ...(report.citations || {}) };
    citations[filename] = { ...(citations[filename] || {}), ...patch };
    const current = citations[filename];
    const authors = current.author?.trim() || 'Author unknown';
    const year = current.year?.trim() || 'n.d.';
    const title = current.title?.trim() || filename;
    current.formatted = `${authors} (${year}). ${title}.${current.url?.trim() ? ` ${current.url.trim()}` : ''}`;
    updateReport({ ...report, citations });
  };

  return <section className="results content">
    <button className="back-link" onClick={goBack}><ArrowLeft size={15}/> New analysis</button>
    <div className="result-heading"><div><div className="eyebrow"><span className="eyebrow-line"/> ANALYSIS COMPLETE</div><h1>Review your <em>results.</em></h1><p>{report.submitted_word_count.toLocaleString()} words reviewed · {report.standalone ? 'Standalone analysis' : 'Reference comparison'} · {report.semantic_model.model}</p></div><button className="outline-btn" onClick={exportPdf}><Download size={16}/> Download report</button></div>
    <div className="disclaimer"><ShieldCheck size={17}/><span><b>Indicators for human review.</b> Similarity does not establish plagiarism. No external source database was searched.</span></div>
    {(report.ocr_pages?.length || Object.keys(report.ocr_reference_pages || {}).length) ? <div className="info-banner"><Eye size={16}/><span>OCR was used for scanned pages{report.ocr_pages?.length ? ` in the submission (${report.ocr_pages.join(', ')})` : ''}{Object.keys(report.ocr_reference_pages || {}).length ? ` and references (${Object.entries(report.ocr_reference_pages || {}).map(([name, pages]) => `${name}: ${pages.join(', ')}`).join('; ')})` : ''}. Verify OCR text against the original documents.</span></div> : null}
    <div className="metric-grid"><Metric label="Matched text coverage" value={metrics.matched_text_coverage === null ? '—' : `${metrics.matched_text_coverage}%`} sub={metrics.matched_text_coverage === null ? 'Unavailable without references' : 'Share of submitted words in flagged passages'} accent="blue"/><Metric label="Passages to review" value={String(metrics.matched_passage_count)} sub="Distinct submitted passages flagged" accent="violet"/><Metric label="Mean lexical signal" value={`${Math.round(Number(metrics.mean_lexical_similarity) * 100)}%`} sub="Word and character n-gram similarity" accent="green"/><Metric label="Mean semantic signal" value={report.standalone ? '—' : metrics.mean_semantic_similarity === null ? 'Unavailable' : `${Math.round(Number(metrics.mean_semantic_similarity) * 100)}%`} sub={report.standalone ? 'No reference documents supplied' : metrics.mean_semantic_similarity === null ? (report.semantic_model.error ? 'Local model could not load' : 'Embedding model unavailable') : 'Embedding cosine similarity'} accent="amber"/></div>
    <div className="results-columns"><section className="panel chart-panel"><div className="result-panel-head"><div><h2>Passage similarity</h2><p>Lexical and semantic signals by flagged passage</p></div><span className="chart-legend"><i className="legend-blue"/> Lexical {report.semantic_available && <><i className="legend-purple"/> Semantic</>}</span></div>{chart.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={chart} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}><CartesianGrid strokeDasharray="3 4" vertical={false} stroke="#e9ebf2"/><XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#80869a' }}/><YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#80869a' }}/><Tooltip formatter={value => `${value}%`}/><Bar dataKey="lexical" fill="#5867db" radius={[4, 4, 0, 0]} maxBarSize={26}/>{report.semantic_available && <Bar dataKey="semantic" fill="#a393ec" radius={[4, 4, 0, 0]} maxBarSize={26}/>}</BarChart></ResponsiveContainer></div> : <div className="empty-chart"><ScanSearch size={22}/><b>No significant matches detected</b><span>No passages crossed the configured review thresholds.</span></div>}<div className="definition"><CircleHelp size={14}/><span>Coverage counts words in flagged passages once. Similarity values are signals, not plagiarism percentages.</span></div></section>
      <section className="panel ai-panel"><div className="result-panel-head"><div><div className="ai-title"><span className="summary-icon violet"><Sparkles size={16}/></span><h2>Writing patterns</h2></div><p>Experimental signals · not an authorship detector</p></div><span className="experimental">EXPLORATORY</span></div><div className="pattern-score"><strong>{report.ai_writing_signals.pattern_score}</strong><span>/ 100 pattern index</span></div><div className="pattern-meter"><span style={{ width: `${report.ai_writing_signals.pattern_score}%` }}/></div><div className="signal-rows"><div><span>Sentence-length variation</span><b>{report.ai_writing_signals.sentence_length_variation}</b></div><div><span>Lexical diversity</span><b>{report.ai_writing_signals.lexical_diversity}</b></div></div><div className="ai-warning"><HelpCircle size={15}/>{report.ai_writing_signals.disclaimer}</div></section></div>
    {report.references.length > 0 && <section className="panel refs-summary"><div className="result-panel-head"><div><h2>Reference documents and citation helper</h2><p>Add source details to create editable citation suggestions for your report.</p></div><BookMarked size={18}/></div><div className="reference-grid">{report.references.map(ref => <div className="reference-summary citation-card" key={ref.filename}><span className="summary-icon blue"><FileText size={15}/></span><div className="reference-summary-name"><b>{ref.filename}</b><small>{ref.match_count} flagged {ref.match_count === 1 ? 'passage' : 'passages'}</small></div><div className="ref-score"><small>Lexical</small><b>{Math.round(ref.strongest_lexical * 100)}%</b></div><div className="ref-score"><small>Semantic</small><b>{Math.round(ref.strongest_semantic * 100)}%</b></div><div className="citation-fields"><input aria-label={`Author of ${ref.filename}`} placeholder="Author / organization" value={report.citations?.[ref.filename]?.author || ''} onChange={event => patchCitation(ref.filename, { author: event.target.value })}/><input aria-label={`Year of ${ref.filename}`} placeholder="Year" value={report.citations?.[ref.filename]?.year || ''} onChange={event => patchCitation(ref.filename, { year: event.target.value })}/><input aria-label={`Title of ${ref.filename}`} placeholder="Source title" value={report.citations?.[ref.filename]?.title || ''} onChange={event => patchCitation(ref.filename, { title: event.target.value })}/><input aria-label={`URL of ${ref.filename}`} placeholder="URL (optional)" value={report.citations?.[ref.filename]?.url || ''} onChange={event => patchCitation(ref.filename, { url: event.target.value })}/>{report.citations?.[ref.filename]?.formatted && <div className="formatted-citation"><span>{report.citations[ref.filename].formatted}</span><button aria-label="Copy citation" onClick={() => void navigator.clipboard.writeText(report.citations?.[ref.filename]?.formatted || '')}><Copy size={13}/></button></div>}</div></div>)}</div></section>}
    <section className="panel matches-panel"><div className="result-panel-head match-head"><div><h2>Passage review</h2><p>Highlighted token overlap, why it matched, and review notes.</p></div><div className="filter-select"><Filter size={14}/><select value={filter} onChange={event => setFilter(event.target.value)}><option value="all">All signals</option><option value="lexical">Exact / near-exact</option><option value="semantic">Semantic matches</option></select></div></div>
      {matches.length ? matches.map(({ match, index }) => <MatchCard key={`${match.reference_name}-${index}`} match={match} onChange={patch => patchMatch(index, patch)}/>) : <div className="no-matches"><Check size={18}/><div><b>No significant match detected</b><p>There are no passages in this filter. This does not establish that the document is original.</p></div></div>}
    </section>
    <section className="bottom-note"><b>How to interpret this report</b><p>Exact and near-exact categories use normalized text and lexical evidence. Semantic matches use the configured local sentence-embedding model and may reflect common concepts. OCR can misread scanned text. Review the original source before drawing conclusions.</p></section>
  </section>;
}

function MatchCard({ match, onChange }: { match: Match; onChange: (patch: Partial<Match>) => void }) {
  const categoryLabel = match.category === 'semantic' ? 'Potential paraphrase / semantic match' : match.category === 'exact' ? 'Exact overlap' : 'Near-exact overlap';
  return <article className={`match-card review-${match.review_status || 'to_review'}`}>
    <div className="match-meta"><span className={`category ${match.category}`}>{categoryLabel}</span><span className="source"><FileText size={14}/>{match.reference_name}{match.reference_page ? ` · p. ${match.reference_page}` : ''}</span><span className="method">{match.detection_method}</span><span className="scores">Lexical <b>{Math.round(match.lexical_score * 100)}%</b><i/> Semantic <b>{Math.round(match.semantic_score * 100)}%</b></span></div>
    <div className="passage-grid"><div><label>SUBMITTED TEXT{match.submitted_page ? ` · PAGE ${match.submitted_page}` : ''}</label><p>{renderHighlights(match.submitted_passage, match.submitted_highlights || [])}</p></div><div><label>REFERENCE PASSAGE{match.reference_page ? ` · PAGE ${match.reference_page}` : ''}</label><p>{renderHighlights(match.reference_passage, match.reference_highlights || [])}</p></div></div>
    <div className="review-tools"><label>Review status<select value={match.review_status || 'to_review'} onChange={event => onChange({ review_status: event.target.value as Match['review_status'] })}><option value="to_review">Needs review</option><option value="reviewed">Reviewed</option><option value="dismissed">Dismissed</option></select></label><label className="review-note">Reviewer note<textarea value={match.review_note || ''} onChange={event => onChange({ review_note: event.target.value })} placeholder="Add context or explain your decision…"/></label></div>
  </article>;
}

function renderHighlights(text: string, ranges: HighlightRange[]) {
  const valid = ranges.filter(range => range.start >= 0 && range.end <= text.length && range.end > range.start).sort((a, b) => a.start - b.start);
  if (!valid.length) return text;
  const nodes: ReactNode[] = [];
  let cursor = 0;
  valid.forEach((range, index) => {
    const start = Math.max(cursor, range.start);
    if (start > cursor) nodes.push(text.slice(cursor, start));
    if (range.end > start) nodes.push(<mark key={index}>{text.slice(start, range.end)}</mark>);
    cursor = Math.max(cursor, range.end);
  });
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes;
}

function Metric({ label, value, sub, accent }: { label: string; value: string; sub: string; accent: string }) {
  return <div className="metric-card"><span className={`metric-dot ${accent}`}/><label>{label}</label><strong>{value}</strong><p>{sub}</p></div>;
}
