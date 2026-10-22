import * as fs from 'node:fs';
import * as path from 'node:path';
import { REPORT_DIR, resultFile } from './cache';
import type { Cell } from './summary';

/**
 * Kill-resilient, append-only case log: one JSON line per event, written the moment a test ends.
 * If the runner is killed, every finished test is already on disk; a missing "end" line means "incomplete",
 * and the lines that exist still count. The file name carries tenant AND run id (never a shared file).
 */
export type CaseLine =
  | { kind: 'begin'; tenantId: string; runId: string; at: string }
  | { kind: 'test'; tenantId: string; runId: string; title: string; module: string; outcome: Cell; at: string }
  | { kind: 'end'; tenantId: string; runId: string; at: string };

export const caseLogPath = (tenantId: string, runId: string): string =>
  resultFile(path.join(REPORT_DIR, 'cases'), tenantId, runId, 'cases.jsonl');

export function appendCaseLine(line: CaseLine): void {
  const file = caseLogPath(line.tenantId, line.runId);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, JSON.stringify(line) + '\n'); // single small append; safe to interrupt
}

/** Tolerant parse: a line cut off by a kill is dropped, never fatal. */
export function parseCaseLog(text: string): CaseLine[] {
  const out: CaseLine[] = [];
  for (const raw of text.split('\n')) {
    if (!raw.trim()) continue;
    try {
      out.push(JSON.parse(raw) as CaseLine);
    } catch {
      // truncated final line after a kill
    }
  }
  return out;
}
