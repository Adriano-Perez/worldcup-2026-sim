"use client";

import { useEffect, useState } from 'react';

type CountdownTimerProps = {
  target: string;
};

export function CountdownTimer({ target }: CountdownTimerProps) {
  const targetMs = new Date(target).getTime();

  const getTimeLeft = () => {
    const diffMs = Math.max(0, targetMs - Date.now());
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
  }, [targetMs]);

  return (
    <p>
      World Cup Final: {timeLeft.days} days, {timeLeft.hours} hours, {timeLeft.minutes} minutes,{' '}
      {timeLeft.seconds} seconds left
    </p>
  );
}
