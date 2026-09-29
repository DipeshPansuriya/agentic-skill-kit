// Deliberately BAD sample for perf_smells.py - do not copy.
export async function loadStatuses(awbs: string[], blocked: string[]) {
  let html = "";
  for (const awb of awbs) {
    const res = await fetch(`/api/status/${awb}`);        // io-in-loop
    if (blocked.includes(awb)) continue;                 // linear-lookup-loop
    const rx = new RegExp("^\\d{3}-\\d{8}$");             // regex-in-loop
    html += `<li>${awb}</li>`;                           // string-concat-loop
    console.log("loaded", awb);                          // log-in-loop
  }
  awbs.forEach(async (a) => {                            // async-foreach
    await saveAudit(a);                                  // await-in-loop
  });
  return html;
}

export async function sequential(ids: number[]) {
  for (const id of ids) {
    await delay(id);                                     // await-in-loop
  }
}
