"use client";

import { CountdownTimer } from './CountdownTimer';

// Homepage section with countdown and bracket image.
export default function Home() {
  const timerTarget = '2026-07-19T12:00:00-07:00';

  return (
    <section id="home" className="max-w-2xl mx-auto py-4">
      <div className="w-full text-left">
        <h1 className="text-2xl font-medium mb-3">2026 World Cup Predictions</h1>
        <p className="mb-3 text-gray-700">
          Using machine learning and real-world match data to predict World Cup tournament
          outcomes including group stage results, knockout rounds, and the eventual champion.
        </p>
        <CountdownTimer target={timerTarget} />
        <img
          src="/worldcup.jpg"
          alt="World Cup Bracket"
          className="max-w-full h-auto mt-4"
        />
      </div>
    </section>
  );
}
