// Clean sample for sec_scan.py: expected 0 findings.
import DOMPurify from 'dompurify';

export function Remarks({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
}

export function render(el: HTMLElement, name: string) {
  el.textContent = name;
  const csrfToken = crypto.randomUUID();
  const apiBase = import.meta.env.VITE_API_BASE;
}
