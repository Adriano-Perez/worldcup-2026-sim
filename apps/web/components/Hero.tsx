"use client";

import { useEffect, useState } from "react";

// Homepage hero section with countdown and bracket image.
export default function Hero() {
  const target = new Date("2026-07-19T12:00:00-07:00").getTime();

  const getTimeLeft = () => {
    const diffMs = Math.max(0, target - Date.now());
    const totalSeconds = Math.floor(diffMs / 1000);

    return {
      days: Math.floor(totalSeconds / (3600 * 24)),
      hours: Math.floor((totalSeconds % (3600 * 24)) / 3600),
      minutes: Math.floor((totalSeconds % 3600) / 60),
      seconds: Math.floor(totalSeconds % 60),
    };
  };

  const [timeLeft, setTimeLeft] = useState(getTimeLeft());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(getTimeLeft());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <section id="home">
      <h1>2026 World Cup Predictions</h1>
      <p>Predict matches, explore teams, and simulate the tournament.</p>
      <p>World Cup Final: {timeLeft.days} days, {timeLeft.hours} hours, {timeLeft.minutes} minutes, {timeLeft.seconds} seconds left</p>
      <img src="/worldcup.jpg" alt="World Cup Bracket" style={{ maxWidth: "100%", height: "auto" }} />
      <p></p>
    </section>
  );
}
