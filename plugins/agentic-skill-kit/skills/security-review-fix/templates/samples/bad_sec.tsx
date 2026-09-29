// Deliberately VULNERABLE sample for sec_scan.py - do not copy.
import { DomSanitizer } from '@angular/platform-browser';

export function Remarks({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;                 // react-dangerous-html
}

export function render(el: HTMLElement, name: string) {
  el.innerHTML = `<b>${name}</b>`;                                            // dom-innerhtml
  const fn = new Function('x', name);                                         // code-eval
  const csrfToken = Math.random().toString(36).slice(2);                      // insecure-random
}

export class NoteComponent {
  constructor(private s: DomSanitizer) {}
  trusted(v: string) { return this.s.bypassSecurityTrustHtml(v); }           // angular-bypass
}

const apiKey = "8kQ4nF7pL2vR9tZ3wD6yB5mX1cH0aG4s";                           // high-entropy-secret
