import { useCallback, useEffect, useRef, useState } from 'react';

/** Fetch on mount and when deps change. fn receives an AbortSignal. */
export function useFetch(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const ctrl = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    fn(ctrl.signal).then(
      (data) => setState({ data, error: null, loading: false }),
      (error) => error.kind !== 'cancelled' && setState({ data: null, error, loading: false })
    );
    return () => ctrl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}

/** Calls `fn` every `ms` while `enabled` is true (used for processing status). */
export function usePolling(fn, ms, enabled) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    if (!enabled) return undefined;
    const id = setInterval(() => ref.current(), ms);
    return () => clearInterval(id);
  }, [ms, enabled]);
}
