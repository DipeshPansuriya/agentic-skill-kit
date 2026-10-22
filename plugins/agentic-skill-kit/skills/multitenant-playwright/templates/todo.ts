/**
 * todo('why') marks a tenant value nobody has verified yet.
 * Reading it throws (naming tenant and path); a scenario that never touches it still runs.
 * The marker is typed as T so a placeholder type-checks anywhere a real value would.
 */
const MARK = '__tenantTodo__';

interface TodoMarker {
  readonly [MARK]: true;
  readonly why: string;
}

export function todo<T = string>(why: string): T {
  const marker: TodoMarker = { [MARK]: true, why };
  return marker as unknown as T;
}

export function isTodo(value: unknown): value is TodoMarker {
  return typeof value === 'object' && value !== null && (value as Record<string, unknown>)[MARK] === true;
}

/** Deep read-guard. Returns a Proxy over `value` that throws when an unfilled todo is READ. */
export function guardTodos<T extends object>(value: T, tenantId: string, path = ''): T {
  return new Proxy(value, {
    get(target, prop, receiver) {
      const v: unknown = Reflect.get(target, prop, receiver);
      if (typeof prop === 'symbol') return v;
      const here = path ? `${path}.${prop}` : prop;
      if (isTodo(v)) {
        throw new Error(`Tenant "${tenantId}": ${here} is not filled in yet (todo: ${v.why})`);
      }
      if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
        return guardTodos(v as object, tenantId, here);
      }
      return v;
    },
  });
}

/** List every unfilled todo under `value` (use on the RAW profile, not the guarded one). */
export function listTodos(value: unknown, path = ''): Array<{ path: string; why: string }> {
  if (isTodo(value)) return [{ path, why: value.why }];
  if (typeof value !== 'object' || value === null) return [];
  return Object.entries(value).flatMap(([k, v]) => listTodos(v, path ? `${path}.${k}` : k));
}
