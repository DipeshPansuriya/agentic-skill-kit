#!/usr/bin/env python3
"""Execution-plan analyzer for PostgreSQL and SQL Server. Python 3 stdlib only.

Input (auto-detected):
  * PostgreSQL  EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) output  (.json)
  * SQL Server  showplan XML, actual or estimated              (.sqlplan / .xml, UTF-8 or UTF-16)

Flags:
  - Seq Scan / Table Scan / Clustered Index Scan / Index Scan reading >= --rows rows
  - Estimated vs actual rows off by >= --ratio (per execution / per loop)
  - Sorts / hashes spilling to disk (PG external sort, hash batches, temp blocks;
    SQL Server SpillToTempDb, Sort/Hash spill details)
  - Nested loops whose inner side runs >= --loops times
  - Key Lookup / RID Lookup (SQL Server)
  - Implicit conversions (SQL Server PlanAffectingConvert / CONVERT_IMPLICIT)
  - Other plan warnings (no join predicate, columns without statistics, memory grant)
  - Missing index suggestions (SQL Server MissingIndexes): labelled VERIFY
  - Top-N most expensive nodes by exclusive time (actual plans) or exclusive cost

Findings are leads: confirm each in the plan before recommending a fix.

Usage:
  python3 plan_analyzer.py plan.json
  python3 plan_analyzer.py plan.sqlplan --rows 50000 --top 8
Exit code: 0 on success, 2 if the file cannot be parsed.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET

SEV_RANK = {"High": 0, "Medium": 1, "Low": 2, "Info": 3}
NS = "{http://schemas.microsoft.com/sqlserver/2004/07/showplan}"


class Finding:
    def __init__(self, sev, issue, node, evidence, action):
        self.sev, self.issue, self.node, self.evidence, self.action = sev, issue, node, evidence, action


def fmt(n):
    if n is None:
        return "?"
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.3f}" if abs(n) < 1 else f"{n:,.1f}"
    return f"{int(n):,}"


def ratio(est, act):
    """Misestimate factor >= 1 and direction."""
    e, a = max(float(est), 1.0), max(float(act), 1.0)
    return (a / e, "under") if a >= e else (e / a, "over")


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


# --------------------------------------------------------------------------- PostgreSQL
def analyze_pg(doc, a):
    findings, nodes, meta = [], [], []
    plans = doc if isinstance(doc, list) else [doc]
    counter = [0]

    def label(n):
        rel = n.get("Relation Name") or n.get("Index Name") or n.get("CTE Name") or ""
        alias = n.get("Alias")
        if rel and alias and alias != rel:
            rel = f"{rel} {alias}"
        return f"#{n['_id']} {n.get('Node Type', '?')}" + (f" on {rel}" if rel else "")

    def walk(n, parent_type=None, is_inner=False):
        counter[0] += 1
        n["_id"] = counter[0]
        kids = n.get("Plans", []) or []
        analyzed = "Actual Rows" in n
        loops = n.get("Actual Loops", 1) or 1
        total_t = (n.get("Actual Total Time", 0.0) or 0.0) * loops if analyzed else None
        for i, k in enumerate(kids):
            walk(k, n.get("Node Type"), is_inner=(n.get("Node Type") == "Nested Loop" and i == 1))
        if analyzed:
            child_t = sum(k["_incl"] for k in kids if k.get("_incl") is not None)
            n["_incl"] = total_t
            n["_excl"] = max(total_t - child_t, 0.0)
        else:
            n["_incl"] = None
        child_cost = sum(k.get("Total Cost", 0.0) for k in kids)
        n["_excl_cost"] = max(n.get("Total Cost", 0.0) - child_cost, 0.0)
        nodes.append(n)

        nt = n.get("Node Type", "")
        lab = label(n)
        # 1. large scans
        if nt == "Seq Scan":
            if analyzed:
                read = ((n.get("Actual Rows", 0) or 0) + (n.get("Rows Removed by Filter", 0) or 0)) * loops
                basis = "actual rows read"
            else:
                read, basis = n.get("Plan Rows", 0), "estimated rows"
            if read >= a.rows:
                removed = n.get("Rows Removed by Filter")
                ev = f"{fmt(read)} {basis}"
                if removed is not None:
                    ev += f"; returned {fmt(n.get('Actual Rows', 0) * loops)}, removed by filter {fmt(removed * loops)}"
                if n.get("Filter"):
                    ev += f"; Filter: {n['Filter']}"
                if n.get("Filter"):
                    sev = "High" if read >= a.rows * 10 else "Medium"
                    act = "Check SARGability of the filter, then an index serving it (state write cost)"
                else:
                    sev = "Medium"
                    ev += "; no filter: whole table feeds the parent"
                    act = "Expected if most rows are needed; else push a filter/join key to allow an index-driven plan"
                findings.append(Finding(sev, "Seq Scan on large row count", lab, ev, act))
        # 2. misestimates
        n["_mis"] = 0
        if analyzed and "Plan Rows" in n:
            f, d = ratio(n["Plan Rows"], n.get("Actual Rows", 0))
            if f >= a.ratio and max(n["Plan Rows"], n.get("Actual Rows", 0)) >= 100:
                n["_mis"] = f
                src = [k for k in kids if k.get("_mis", 0) >= a.ratio]
                sev = "High" if f >= a.ratio * 10 else "Medium"
                issue = f"Row estimate {d}-estimated {f:,.0f}x"
                if src:
                    sev, issue = "Low", issue + f" (inherited from #{src[0]['_id']})"
                findings.append(Finding(sev, issue, lab,
                                        f"estimated {fmt(n['Plan Rows'])} vs actual {fmt(n.get('Actual Rows', 0))} rows per loop (loops={fmt(loops)})",
                                        "ANALYZE / SET STATISTICS / CREATE STATISTICS; remove functions on columns"))
        # 3. spills
        sm = n.get("Sort Method", "") or ""
        spilled = "external" in sm.lower() or n.get("Sort Space Type") == "Disk" or (hb_ := (n.get("Hash Batches") or n.get("HashAgg Batches") or 0)) > 1
        if "external" in sm.lower() or n.get("Sort Space Type") == "Disk":
            findings.append(Finding("High", "Sort spilled to disk", lab,
                                    f"Sort Method: {sm}, {fmt(n.get('Sort Space Used'))} kB {n.get('Sort Space Type', '')}".strip(),
                                    "Fix row estimate; index providing the order; session work_mem"))
        hb = n.get("Hash Batches") or n.get("HashAgg Batches")
        if hb and hb > 1:
            findings.append(Finding("High", f"{nt} spilled ({fmt(hb)} batches)", lab,
                                    f"Batches {fmt(hb)} (original {fmt(n.get('Original Hash Batches', '?'))}); "
                                    f"peak memory {fmt(n.get('Peak Memory Usage'))} kB"
                                    + (f"; disk {fmt(n['Disk Usage'])} kB" if n.get("Disk Usage") else ""),
                                    "Reduce rows before the hash; work_mem / hash_mem_multiplier per session"))
        if not spilled and (n.get("Temp Written Blocks") or 0) > 0 and nt in ("Sort", "Hash", "HashAggregate", "Aggregate", "Materialize"):
            findings.append(Finding("Medium", "Temp blocks written", lab,
                                    f"Temp Written Blocks {fmt(n['Temp Written Blocks'])}", "Check work_mem vs rows"))
        # 4. nested loop inner side
        if is_inner and analyzed and loops >= a.loops:
            sev = "High" if loops >= a.loops * 100 else "Medium"
            findings.append(Finding(sev, "Nested Loop inner side executed many times", lab,
                                    f"loops={fmt(loops)}, {fmt(n.get('Actual Total Time', 0))} ms per loop, "
                                    f"{fmt(total_t)} ms total",
                                    "Fix outer estimate so a hash/merge join is chosen; ensure inner index seek"))
        # 5. index-only scan heap fetches
        if nt == "Index Only Scan" and (n.get("Heap Fetches") or 0) >= a.rows / 10:
            findings.append(Finding("Low", "Index Only Scan with many heap fetches", lab,
                                    f"Heap Fetches {fmt(n['Heap Fetches'])}", "VACUUM more often (visibility map)"))

    for p in plans:
        root = p.get("Plan", p)
        walk(root)
        et, pt = p.get("Execution Time"), p.get("Planning Time")
        jit = p.get("JIT", {}) or {}
        jit_t = (jit.get("Timing", {}) or {}).get("Total")
        if isinstance(jit_t, dict):
            jit_t = jit_t.get("Total")
        meta.append(f"planning {fmt(pt)} ms, execution {fmt(et)} ms" + (f", JIT {fmt(jit_t)} ms" if jit_t else ""))
        if jit_t and et and jit_t > 0.3 * et:
            findings.append(Finding("Medium", "JIT compile time is a large share of runtime", "query",
                                    f"JIT {fmt(jit_t)} ms of {fmt(et)} ms execution",
                                    "jit = off for this role or raise jit_above_cost; fix cost over-estimate"))

    analyzed = any(n.get("_incl") is not None for n in nodes)
    key = (lambda n: n["_excl"]) if analyzed else (lambda n: n["_excl_cost"])
    top = sorted(nodes, key=key, reverse=True)[: a.top]
    top_rows = []
    for n in top:
        top_rows.append((label(n),
                         f"{fmt(n['_excl'])} ms" if analyzed else "n/a",
                         f"{fmt(n['_incl'])} ms" if analyzed else "n/a",
                         f"{n['_excl_cost']:,.1f}",
                         f"{fmt(n.get('Plan Rows'))} / {fmt(n.get('Actual Rows'))}" if analyzed else fmt(n.get("Plan Rows")),
                         fmt(n.get("Actual Loops")) if analyzed else "n/a"))
    hdr = ("Node", "Excl. time", "Incl. time", "Excl. cost", "Est / Act rows (per loop)", "Loops")
    return "PostgreSQL", analyzed, meta, findings, hdr, top_rows


# --------------------------------------------------------------------------- SQL Server
def child_relops(el):
    """Direct RelOp descendants (do not descend into nested RelOps)."""
    out = []
    for c in el:
        if c.tag == NS + "RelOp":
            out.append(c)
        else:
            out.extend(child_relops(c))
    return out


def own_elements(el, tag):
    """Elements with tag under el, excluding those inside nested RelOps."""
    out = []
    for c in el:
        if c.tag == NS + "RelOp":
            continue
        if c.tag == NS + tag:
            out.append(c)
        out.extend(own_elements(c, tag))
    return out


def analyze_ms(root, a):
    findings, nodes, meta = [], [], []
    stmts = root.iter(NS + "StmtSimple")
    analyzed_any = False

    def runtime(rel):
        rti = rel.find(NS + "RunTimeInformation")
        if rti is None:
            return None
        rows = execs = reads = rows_read = 0
        elapsed = cpu = 0
        for t in rti.findall(NS + "RunTimeCountersPerThread"):
            rows += int(t.get("ActualRows", 0))
            execs += int(t.get("ActualExecutions", 0))
            reads += int(t.get("ActualLogicalReads", 0))
            rows_read += int(t.get("ActualRowsRead", 0))
            elapsed = max(elapsed, int(t.get("ActualElapsedms", 0)))
            cpu += int(t.get("ActualCPUms", 0))
        return {"rows": rows, "execs": execs, "reads": reads, "rows_read": rows_read,
                "elapsed": elapsed, "cpu": cpu}

    for s_i, stmt in enumerate(stmts, 1):
        qp = stmt.find(NS + "QueryPlan")
        if qp is None:
            continue
        text = re.sub(r"\s+", " ", stmt.get("StatementText", "")).strip()
        meta.append(f"stmt {s_i}: cost {float(stmt.get('StatementSubTreeCost', 0)):,.2f}, "
                    f"DOP {qp.get('DegreeOfParallelism', '1')}: {text[:90]}")
        mg = qp.find(NS + "MemoryGrantInfo")
        if mg is not None and mg.get("MaxUsedMemory") and mg.get("GrantedMemory"):
            g, u = int(mg.get("GrantedMemory")), int(mg.get("MaxUsedMemory"))
            if g >= 102400 and u < g / 10:
                findings.append(Finding("Medium", "Excessive memory grant", f"stmt {s_i}",
                                        f"granted {fmt(g)} KB, max used {fmt(u)} KB",
                                        "Over-estimate: fix stats/row estimates; narrow wide sorted columns"))

        # plan-level warnings
        for w in qp.findall(NS + "Warnings"):
            for c in w:
                tag = c.tag.replace(NS, "")
                if tag == "PlanAffectingConvert":
                    issue = c.get("ConvertIssue", "")
                    sev = "High" if "Seek" in issue else "Medium"
                    findings.append(Finding(sev, f"Implicit conversion ({issue})", f"stmt {s_i}",
                                            c.get("Expression", ""),
                                            "Type the parameter/literal like the column (VARCHAR vs NVARCHAR)"))
                elif tag == "MemoryGrantWarning":
                    findings.append(Finding("Medium", "Memory grant warning", f"stmt {s_i}",
                                            f"{c.get('GrantWarningKind')}: requested {c.get('RequestedMemory')} KB, "
                                            f"granted {c.get('GrantedMemory')} KB, used {c.get('MaxUsedMemory')} KB",
                                            "Fix row estimates"))
                else:
                    findings.append(Finding("Low", f"Plan warning: {tag}", f"stmt {s_i}",
                                            " ".join(f"{k}={v}" for k, v in c.attrib.items())[:160], "Review"))

        # missing indexes
        for g in qp.iter(NS + "MissingIndexGroup"):
            for mi in g.findall(NS + "MissingIndex"):
                cols = {}
                for cg in mi.findall(NS + "ColumnGroup"):
                    cols[cg.get("Usage")] = [c.get("Name") for c in cg.findall(NS + "Column")]
                tbl = f"{mi.get('Schema', '')}.{mi.get('Table', '')}"
                desc = "; ".join(f"{k}: {', '.join(v)}" for k, v in cols.items())
                findings.append(Finding("Info", f"Missing index suggestion (VERIFY), impact {g.get('Impact')}%",
                                        tbl, desc,
                                        "Verify against existing indexes and write cost; choose key order yourself"))

        # walk operators
        top_rel = qp.find(NS + "RelOp")
        if top_rel is None:
            continue

        def walk(rel, is_inner=False):
            rt = runtime(rel)
            kids = child_relops(rel)
            phys = rel.get("PhysicalOp", "?")
            kid_nodes = [walk(k, is_inner=(phys == "Nested Loops" and i == 1)) for i, k in enumerate(kids)]
            obj = None
            for tag in ("IndexScan", "TableScan"):
                e = rel.find(NS + tag)
                if e is not None:
                    o = e.find(NS + "Object")
                    if o is not None:
                        obj = f"{o.get('Table', '')}" + (f".{o.get('Index')}" if o.get("Index") else "")
                    break
            is_lookup = False
            ix = rel.find(NS + "IndexScan")
            if ix is not None and ix.get("Lookup") in ("1", "true"):
                is_lookup = True
            if phys in ("RID Lookup", "Key Lookup"):
                is_lookup = True
            shown = "Key Lookup" if (is_lookup and phys != "RID Lookup") else phys
            lab = f"stmt {s_i} node {rel.get('NodeId')} {shown}" + (f" on {obj}" if obj else "")
            est = float(rel.get("EstimateRows", 0))
            subtree = float(rel.get("EstimatedTotalSubtreeCost", 0))
            excl_cost = max(subtree - sum(float(k.get("EstimatedTotalSubtreeCost", 0)) for k in kids), 0.0)
            node = {"label": lab, "est": est, "rt": rt, "excl_cost": excl_cost, "id": rel.get("NodeId")}
            if rt:
                child_el = sum(runtime(k)["elapsed"] for k in kids if runtime(k))
                node["incl"] = rt["elapsed"]
                node["excl"] = max(rt["elapsed"] - child_el, 0)
            nodes.append(node)

            # large scans
            if phys in ("Table Scan", "Clustered Index Scan", "Index Scan") and not is_lookup:
                if rt:
                    read = rt["rows_read"] or rt["rows"]
                    basis = "actual rows read"
                else:
                    read = float(rel.get("EstimatedRowsRead", rel.get("TableCardinality", est)))
                    basis = "estimated rows read"
                if read >= a.rows:
                    ev = f"{fmt(read)} {basis}"
                    if rt:
                        ev += f"; returned {fmt(rt['rows'])}; logical reads {fmt(rt['reads'])}"
                    pred = own_elements(rel, "Predicate")
                    if pred:
                        so = pred[0].find(NS + "ScalarOperator")
                        if so is not None and so.get("ScalarString"):
                            ev += f"; predicate: {so.get('ScalarString')[:120]}"
                    sev = "High" if read >= a.rows * 10 else "Medium"
                    findings.append(Finding(sev, f"{phys} on large row count", lab, ev,
                                            "Check SARGability/implicit conversion, then an index serving the predicate"))
            # misestimate (per execution)
            node["mis"] = 0
            if rt and rt["execs"] > 0:
                act = rt["rows"] / rt["execs"]
                f, d = ratio(est, act)
                if f >= a.ratio and max(est, act) >= 100:
                    node["mis"] = f
                    src = [x for x in kid_nodes if x["mis"] >= a.ratio]
                    sev = "High" if f >= a.ratio * 10 else "Medium"
                    issue = f"Row estimate {d}-estimated {f:,.0f}x"
                    if src:
                        sev, issue = "Low", issue + f" (inherited from node {src[0]['id']})"
                    findings.append(Finding(sev, issue, lab,
                                            f"estimated {fmt(est)} vs actual {fmt(act)} rows per execution "
                                            f"(executions={fmt(rt['execs'])})",
                                            "UPDATE STATISTICS; SARGable rewrite; avoid table variables/local variables"))
            # lookups
            if is_lookup:
                ex = rt["execs"] if rt else None
                sev = "High" if (ex or 0) >= a.lookups * 100 else "Medium" if (ex or 0) >= a.lookups else "Low"
                findings.append(Finding(sev, "Key/RID Lookup", lab,
                                        f"executions {fmt(ex)}" if rt else f"estimated rows {fmt(est)} (estimated plan)",
                                        "INCLUDE the looked-up columns in the seek index if hot and narrow"))
            # nested loops inner side
            if is_inner and not is_lookup and rt and rt["execs"] >= a.loops:
                sev = "High" if rt["execs"] >= a.loops * 100 else "Medium"
                findings.append(Finding(sev, "Nested Loops inner side executed many times", lab,
                                        f"executions {fmt(rt['execs'])}, est. rows/exec {fmt(est)}",
                                        "Fix outer-input estimate; check join type and inner seek"))
            # operator warnings (spills etc.)
            for w in own_elements(rel, "Warnings"):
                for c in w:
                    tag = c.tag.replace(NS, "")
                    if tag in ("SpillToTempDb", "SortSpillDetails", "HashSpillDetails", "ExchangeSpillDetails"):
                        attrs = ", ".join(f"{k}={v}" for k, v in c.attrib.items())
                        findings.append(Finding("High", f"Spill to tempdb ({tag})", lab, attrs or tag,
                                                "Fix row estimate; memory grant feedback; index for the order"))
                    elif tag == "NoJoinPredicate":
                        findings.append(Finding("High", "No join predicate", lab, "Cartesian product",
                                                "Add the missing join condition"))
                    elif tag == "ColumnsWithNoStatistics":
                        cols = [cr.get("Column") for cr in c.iter(NS + "ColumnReference")]
                        findings.append(Finding("Medium", "Columns with no statistics", lab, ", ".join(cols),
                                                "Enable auto create stats or CREATE STATISTICS"))
                    elif tag not in ("PlanAffectingConvert",):
                        findings.append(Finding("Low", f"Operator warning: {tag}", lab,
                                                " ".join(f"{k}={v}" for k, v in c.attrib.items())[:160], "Review"))
            # CONVERT_IMPLICIT inside predicates of this operator
            for so in own_elements(rel, "ScalarOperator"):
                ss = so.get("ScalarString", "")
                if "CONVERT_IMPLICIT" in ss and ("Seek" in phys or "Scan" in phys or phys == "Filter"):
                    findings.append(Finding("Medium", "CONVERT_IMPLICIT in predicate", lab, ss[:160],
                                            "Match data types between parameter/column or join columns"))
                    break
            return node

        walk(top_rel)
        if top_rel.find(NS + "RunTimeInformation") is not None:
            analyzed_any = True

    analyzed = analyzed_any and any("excl" in n for n in nodes)
    key = (lambda n: n.get("excl", 0)) if analyzed else (lambda n: n["excl_cost"])
    top = sorted(nodes, key=key, reverse=True)[: a.top]
    rows = []
    for n in top:
        rt = n["rt"]
        rows.append((n["label"],
                     f"{fmt(n['excl'])} ms" if analyzed and "excl" in n else "n/a",
                     f"{fmt(n['incl'])} ms" if analyzed and "incl" in n else "n/a",
                     f"{n['excl_cost']:,.3f}",
                     f"{fmt(n['est'])} / {fmt(rt['rows'] / rt['execs']) if rt and rt['execs'] else '?'}" if rt else fmt(n["est"]),
                     fmt(rt["execs"]) if rt else "n/a"))
    hdr = ("Node", "Excl. elapsed", "Incl. elapsed", "Excl. est. cost", "Est / Act rows (per exec)", "Executions")
    return "SQL Server", analyzed, meta, findings, hdr, rows


# --------------------------------------------------------------------------- main
def load(path):
    raw = open(path, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16")
    elif raw[:3] == b"\xef\xbb\xbf":
        text = raw[3:].decode("utf-8")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-16")
    return text.lstrip()


def dedupe(findings):
    seen, out = set(), []
    for f in findings:
        k = (f.issue, f.node, f.evidence)
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def main():
    ap = argparse.ArgumentParser(description="Analyze a PostgreSQL JSON or SQL Server XML execution plan.")
    ap.add_argument("plan", help="plan file: EXPLAIN (ANALYZE, FORMAT JSON) output or .sqlplan XML")
    ap.add_argument("--rows", type=int, default=100000, help="large-scan threshold in rows read (default 100000)")
    ap.add_argument("--ratio", type=float, default=10.0, help="misestimate factor to flag (default 10)")
    ap.add_argument("--loops", type=int, default=1000, help="nested-loop inner executions to flag (default 1000)")
    ap.add_argument("--lookups", type=int, default=1000, help="key-lookup executions for Medium severity (default 1000)")
    ap.add_argument("--top", type=int, default=5, help="number of most expensive nodes to list (default 5)")
    a = ap.parse_args()

    try:
        text = load(a.plan)
    except OSError as e:
        print(f"Cannot read {a.plan}: {e}", file=sys.stderr)
        return 2
    try:
        if text.startswith("<"):
            root = ET.fromstring(text.encode("utf-8") if not text.startswith("<?xml") else
                                 re.sub(r"^<\?xml[^>]*\?>", "", text).encode("utf-8"))
            if not root.tag.startswith(NS):
                print("XML is not a SQL Server showplan (namespace "
                      "http://schemas.microsoft.com/sqlserver/2004/07/showplan expected).", file=sys.stderr)
                return 2
            result = analyze_ms(root, a)
        elif text.startswith("[") or text.startswith("{"):
            result = analyze_pg(json.loads(text), a)
        else:
            print("Unrecognised format. PostgreSQL: use EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON). "
                  "SQL Server: save the actual plan as .sqlplan (showplan XML).", file=sys.stderr)
            return 2
    except (ValueError, ET.ParseError, KeyError, TypeError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 2

    engine, analyzed, meta, findings, hdr, top_rows = result
    findings = sorted(dedupe(findings), key=lambda f: SEV_RANK[f.sev])
    print(f"# Plan analysis: {engine} ({'actual' if analyzed else 'ESTIMATED ONLY: no runtime stats'})\n")
    print(f"File: `{a.plan}` · thresholds: rows>={fmt(a.rows)}, misestimate>={a.ratio:g}x, loops>={fmt(a.loops)}")
    for m in meta:
        print(f"- {m}")
    if not analyzed:
        print("\n> Estimated plan: misestimates and spills cannot be checked. Capture the actual plan.")
    counts = {s: sum(1 for f in findings if f.sev == s) for s in SEV_RANK}
    print(f"\n## Findings ({', '.join(f'{v} {k}' for k, v in counts.items() if v)  or 'none'})\n")
    if findings:
        print("| # | Severity | Issue | Node | Evidence | Next step |")
        print("|---|---|---|---|---|---|")
        for i, f in enumerate(findings, 1):
            print(f"| {i} | {f.sev} | {cell(f.issue)} | {cell(f.node)} | {cell(f.evidence)} | {cell(f.action)} |")
    else:
        print("No rule fired. Still read the costliest nodes below.")
    print(f"\n## Top {len(top_rows)} nodes by {'exclusive time' if analyzed else 'exclusive estimated cost'}\n")
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in top_rows:
        print("| " + " | ".join(cell(x) for x in r) + " |")
    print("\nHeuristic output: confirm each finding in the plan; missing-index suggestions are hints, not answers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
