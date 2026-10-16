import type { Report } from '../types';
const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8137/api';
export async function analyzeText(text: string, refs: {filename:string;text:string}[], standalone: boolean): Promise<Report> {
  const url = `${API}/analyze/${standalone ? 'standalone' : 'text'}`;
  const response = await fetch(url, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,references:refs})});
  if (!response.ok) { const body = await response.json().catch(()=>({})); throw new Error(body.detail || `Request failed (${response.status})`); }
  return response.json();
}
export async function analyzeFiles(submission: File|null, text: string, references: File[], ocrLanguage = 'eng'): Promise<Report> {
  const body = new FormData(); if(submission) body.append('submission',submission); else body.append('submitted_text',text); references.forEach(f=>body.append('references',f)); body.append('ocr_language', ocrLanguage);
  const response = await fetch(`${API}/analyze/files`,{method:'POST',body});
  if (!response.ok) { const data=await response.json().catch(()=>({})); throw new Error(data.detail || `Request failed (${response.status})`); }
  return response.json();
}
export async function downloadReport(report: Report) {
  const response=await fetch(`${API}/reports/pdf`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
  if(!response.ok) throw new Error('Could not generate the PDF report.');
  const url=URL.createObjectURL(await response.blob()); const a=document.createElement('a');a.href=url;a.download='veritext-analysis.pdf';a.click();URL.revokeObjectURL(url);
}
