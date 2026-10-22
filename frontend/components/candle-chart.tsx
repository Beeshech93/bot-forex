"use client";

import { CandlestickSeries, ColorType, createChart, LineSeries, type UTCTimestamp } from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Candle } from "@/lib/types";

type Point = { time: string; ema_fast: number | null; ema_slow: number | null };

export function CandleChart({ candles, indicators }: { candles: Candle[]; indicators: Point[] }) {
  const element = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!element.current) return;
    const chart = createChart(element.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "#101310" }, textColor: "#a2aaa0" },
      grid: { vertLines: { color: "#202620" }, horzLines: { color: "#202620" } },
      rightPriceScale: { borderColor: "#303830" },
      timeScale: { borderColor: "#303830", timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    const price = chart.addSeries(CandlestickSeries, {
      upColor: "#72d49b", downColor: "#e77f73", borderUpColor: "#72d49b",
      borderDownColor: "#e77f73", wickUpColor: "#72d49b", wickDownColor: "#e77f73",
    });
    const ema20 = chart.addSeries(LineSeries, { color: "#d6ba72", lineWidth: 2, title: "EMA 20" });
    const ema50 = chart.addSeries(LineSeries, { color: "#7c9ce8", lineWidth: 2, title: "EMA 50" });
    price.setData(candles.map((c) => ({ ...c, time: Math.floor(new Date(c.time).getTime() / 1000) as UTCTimestamp })));
    ema20.setData(indicators.flatMap((p) => p.ema_fast == null ? [] : [{ time: Math.floor(new Date(p.time).getTime() / 1000) as UTCTimestamp, value: p.ema_fast }]));
    ema50.setData(indicators.flatMap((p) => p.ema_slow == null ? [] : [{ time: Math.floor(new Date(p.time).getTime() / 1000) as UTCTimestamp, value: p.ema_slow }]));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [candles, indicators]);
  return <div className="chart-shell"><div ref={element} className="chart" aria-label="Gráfico de velas con EMA 20 y EMA 50" /></div>;
}
