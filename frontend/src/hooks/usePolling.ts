/**
 * usePolling — React hook 封装 createPollingController
 *
 * 用于组件级别的轮询（如 ReportPage 报告生成状态轮询）。
 * 自动处理组件卸载清理、依赖变化重置。
 * 回调函数通过 ref 持有最新版本，避免不必要的 controller 重建。
 */

import { useEffect, useRef, useCallback } from 'react';
import { createPollingController, type PollingController } from './pollingController';

export interface UsePollingOptions {
  /** 主开关 — 为 false 时停止且不重新开始 */
  enabled: boolean;
  /** 初始轮询间隔 (ms) */
  intervalMs: number;
  /** 最大间隔 (ms) — 退避上限，默认 30s */
  maxIntervalMs?: number;
  /** 退避因子 — 每次 × factor，默认 1.5 */
  backoffFactor?: number;
  /** 最大轮询次数 — 超过后自动停止 */
  maxRetries?: number;
  /** 是否创建后立即执行一次 */
  immediate?: boolean;
  /** 是否在 document.hidden 时暂停 */
  visibilityAware?: boolean;
  /**
   * 每次轮询的回调。
   * 返回 false 表示已到达终态、应停止；返回 true 表示继续。
   */
  onTick: () => Promise<boolean>;
  /** 轮询停止时的回调（终态/超限/取消都触发） */
  onStop?: () => void;
  /** 轮询出错时的回调（onTick 抛出异常） */
  onError?: (error: unknown) => void;
}

export interface UsePollingReturn {
  retryCount: number;
  currentInterval: number;
  isActive: boolean;
  reset: () => void;
  cancel: () => void;
}

export function usePolling(options: UsePollingOptions): UsePollingReturn {
  const {
    enabled,
    intervalMs,
    maxIntervalMs = 30_000,
    backoffFactor = 1.5,
    maxRetries,
    immediate = false,
    visibilityAware = true,
    onTick,
    onStop,
    onError,
  } = options;

  const controllerRef = useRef<PollingController | null>(null);
  const retryCountRef = useRef(0);
  const intervalRef = useRef(intervalMs);
  const activeRef = useRef(false);

  // Keep latest callbacks in refs — avoids rebuild-on-render
  const onTickRef = useRef(onTick);
  onTickRef.current = onTick;
  const onStopRef = useRef(onStop);
  onStopRef.current = onStop;
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;

  // Create controller once; recreate only when timing params change
  const ensureController = useCallback((): PollingController => {
    if (controllerRef.current) return controllerRef.current;

    const ctrl = createPollingController({
      intervalMs,
      maxIntervalMs,
      backoffFactor,
      maxRetries: maxRetries ?? Infinity,
      immediate,
      visibilityAware,
      onTick: async () => {
        if (!enabledRef.current) return false;
        try {
          const shouldContinue = await onTickRef.current();
          retryCountRef.current = ctrl.tickCount;
          intervalRef.current = ctrl.currentInterval;
          activeRef.current = ctrl.active;
          return shouldContinue;
        } catch (e) {
          onErrorRef.current?.(e);
          return false;
        }
      },
      onStop: () => {
        activeRef.current = false;
        retryCountRef.current = ctrl.tickCount;
        onStopRef.current?.();
      },
    });

    controllerRef.current = ctrl;
    return ctrl;
  }, [intervalMs, maxIntervalMs, backoffFactor, maxRetries, immediate, visibilityAware]);

  // Main effect: start/stop based on enabled
  useEffect(() => {
    const ctrl = ensureController();

    if (enabled) {
      ctrl.reset();
      ctrl.start();
      activeRef.current = true;
    } else {
      ctrl.stop();
    }

    return () => {
      const c = controllerRef.current;
      if (c) {
        c.cancel();
        controllerRef.current = null;
      }
    };
  }, [enabled, ensureController]);

  const reset = useCallback(() => { controllerRef.current?.reset(); }, []);
  const cancel = useCallback(() => { controllerRef.current?.cancel(); }, []);

  return {
    get retryCount() { return controllerRef.current?.tickCount ?? retryCountRef.current; },
    get currentInterval() { return controllerRef.current?.currentInterval ?? intervalRef.current; },
    get isActive() { return controllerRef.current?.active ?? activeRef.current; },
    reset,
    cancel,
  };
}
