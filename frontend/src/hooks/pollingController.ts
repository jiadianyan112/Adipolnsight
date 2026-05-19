/**
 * 通用轮询控制器 — 框架无关，可在 React hooks 和 Zustand stores 中复用。
 *
 * 特性：
 * - 指数退避（backoffFactor）
 * - 最大间隔上限（maxIntervalMs）
 * - 最大重试次数（maxRetries）
 * - 页面不可见时暂停（visibilityAware）
 * - 多次 start 不创建多个 timer
 * - stop / cancel 后彻底清理
 */

export interface PollingControllerOptions {
  /** 初始轮询间隔 (ms) */
  intervalMs: number;
  /** 最大间隔 (ms) — 退避上限 */
  maxIntervalMs?: number;
  /** 退避因子 — 每次 × factor，默认 1.5 */
  backoffFactor?: number;
  /** 最大轮询次数 — 超过后自动停止并调用 onStop */
  maxRetries?: number;
  /** 是否创建后立即执行一次 */
  immediate?: boolean;
  /** 是否在 document.hidden 时暂停 */
  visibilityAware?: boolean;
  /**
   * 每次轮询执行的回调。
   * 返回 true 表示应该继续轮询，返回 false 表示已到达终态、应停止。
   */
  onTick: () => Promise<boolean>;
  /** 轮询停止时的回调（终态 / 取消 / 超限） */
  onStop?: () => void;
}

export interface PollingController {
  /** 开始/恢复轮询 */
  start: () => void;
  /** 停止轮询（终态，触发 onStop） */
  stop: () => void;
  /** 取消轮询（静默，不触发 onStop） */
  cancel: () => void;
  /** 重置退避计数，从初始 intervalMs 重新开始 */
  reset: () => void;
  /** 当前是否正在轮询 */
  get active(): boolean;
  /** 已轮询次数 */
  get tickCount(): number;
  /** 当前有效间隔 */
  get currentInterval(): number;
}

export function createPollingController(options: PollingControllerOptions): PollingController {
  const {
    intervalMs,
    maxIntervalMs = 30_000,
    backoffFactor = 1.5,
    maxRetries = Infinity,
    immediate = false,
    visibilityAware = true,
    onTick,
    onStop,
  } = options;

  let timer: ReturnType<typeof setTimeout> | null = null;
  let cancelled = false;
  let stopped = false;
  let _tickCount = 0;
  let _currentInterval = intervalMs;
  let visibilityHandler: (() => void) | null = null;

  function clear() {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function schedule() {
    if (cancelled || stopped) return;

    // Visibility check
    if (visibilityAware && document.hidden) {
      if (!visibilityHandler) {
        visibilityHandler = () => {
          visibilityHandler = null;
          if (!document.hidden) schedule();
        };
        document.addEventListener('visibilitychange', visibilityHandler, { once: true });
      }
      return;
    }

    clear();
    timer = setTimeout(async () => {
      if (cancelled || stopped) return;

      _tickCount++;
      let shouldContinue = false;
      try {
        shouldContinue = await onTick();
      } catch {
        // onTick threw — stop polling
        shouldContinue = false;
      }

      if (cancelled) return;

      if (!shouldContinue) {
        stopped = true;
        clear();
        onStop?.();
        return;
      }

      // Retry limit
      if (_tickCount >= maxRetries) {
        stopped = true;
        clear();
        onStop?.();
        return;
      }

      // Backoff
      _currentInterval = Math.min(
        maxIntervalMs,
        Math.round(_currentInterval * backoffFactor),
      );

      schedule();
    }, _currentInterval);
  }

  function start() {
    if (cancelled || stopped) return;
    clear();
    if (immediate) {
      // Fire first tick immediately, then schedule
      _tickCount++;
      onTick().then((shouldContinue) => {
        if (!shouldContinue || cancelled) {
          stopped = true;
          onStop?.();
          return;
        }
        schedule();
      }).catch(() => {
        stopped = true;
        clear();
        onStop?.();
      });
    } else {
      schedule();
    }
  }

  function stop() {
    stopped = true;
    clear();
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler);
      visibilityHandler = null;
    }
    onStop?.();
  }

  function cancel() {
    cancelled = true;
    clear();
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler);
      visibilityHandler = null;
    }
  }

  function reset() {
    _tickCount = 0;
    _currentInterval = intervalMs;
  }

  return {
    start,
    stop,
    cancel,
    reset,
    get active() { return timer !== null; },
    get tickCount() { return _tickCount; },
    get currentInterval() { return _currentInterval; },
  };
}
