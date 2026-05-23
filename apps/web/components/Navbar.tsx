'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

type Menu = {
  key: string;
  label: string;
  items: { text: string; href: string }[];
};

export function Navbar() {
  const [open, setOpen] = useState(false);

  const menus: Menu[] = [
    { key: 'home', label: 'Home', items: [{ text: 'Return to the main dashboard and countdown', href: '/' }] },
    { key: 'group', label: 'Group stage', items: [{ text: 'View all group stage match predictions and results', href: '/predictions' }] },
    { key: 'bracket', label: 'Brackets', items: [{ text: 'Explore knockout round predictions and tournament bracket', href: '/bracket' }] },
    { key: 'teams', label: 'Teams', items: [{ text: 'View team statistics and squad information', href: '/teams' }] },
  ];

  const router = useRouter();

  // desktop dropdowns removed; no outside-click listener needed

  return (
    <>
      <nav className="navShell">
        <div className="desktopLinks">
          <div className="menubar">
            {menus.map((m) => (
              <div className="menuGroup" key={m.key}>
                <a
                  className="menuTrigger"
                  href={m.items[0].href}
                  onClick={(e) => {
                    e.preventDefault();
                    setOpen(false);
                    router.push(m.items[0].href);
                  }}
                >
                  {m.label}
                </a>
              </div>
            ))}
          </div>
        </div>

        <button
          type="button"
          className="hamburgerBtn"
          aria-label="Toggle navigation menu"
          aria-expanded={open}
          onClick={() => setOpen((prev) => !prev)}
        >
          <span className="line" />
          <span className="line" />
          <span className="line" />
        </button>
      </nav>

      {open && <div className="overlay" onClick={() => setOpen(false)} />}

      <aside className={`mobileDrawer ${open ? 'open' : ''}`}>
        <button
          type="button"
          className="closeBtn"
          aria-label="Close navigation menu"
          onClick={() => setOpen(false)}
        >
          ×
        </button>

        <a
          href="/"
          onClick={(e) => {
            e.preventDefault();
            setOpen(false);
            router.push('/');
          }}
        >
          Home
        </a>
        <a
          href="/predictions"
          onClick={(e) => {
            e.preventDefault();
            setOpen(false);
            router.push('/predictions');
          }}
        >
          Predictions
        </a>
        <a
          href="/bracket"
          onClick={(e) => {
            e.preventDefault();
            setOpen(false);
            router.push('/bracket');
          }}
        >
          Bracket
        </a>
        <a
          href="/teams"
          onClick={(e) => {
            e.preventDefault();
            setOpen(false);
            router.push('/teams');
          }}
        >
          Teams
        </a>
        <a
          href="/leaderboard"
          onClick={(e) => {
            e.preventDefault();
            setOpen(false);
            router.push('/leaderboard');
          }}
        >
          Leaderboard
        </a>
      </aside>

      <style jsx>{`
        .navShell {
          /* Keep navbar as part of document flow (not fixed). */
          position: static;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          height: 3.5rem;
          box-sizing: border-box;
          margin: 0;
          padding: 0 1rem;
          border-radius: 0;
          background: #cdcdcd;
          color: #000000;
          font-family: inherit;
        }

        .desktopLinks {
          display: none;
          gap: 1rem;
        }

        .menubar {
          display: flex;
          gap: 1.25rem;
          align-items: center;
        }

        .menuTrigger {
          background: transparent !important;
          border: none !important;
          padding: 0 !important;
          margin: 0 !important;
          font-weight: 400;
          cursor: pointer;
          color: inherit;
          font-family: inherit;
          font-size: 1rem;
          line-height: 1.25rem;
        }

        .menuContent {
          position: absolute;
          top: 100%;
          left: 0;
          background: #fff;
          border: 1px solid #e6e6e6;
          border-radius: 6px;
          padding: 0.5rem;
          min-width: 220px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.12);
          margin-top: 0.5rem;
          z-index: 60;
        }

        .menuItem {
          padding: 0.5rem 0.6rem;
          color: #222;
          font-size: 0.95rem;
          cursor: pointer;
          font-family: inherit;
          line-height: 1.25rem;
        }

        .desktopLinks a {
          color: currentColor;
          text-decoration: none;
          font-weight: 500;
        }

        .hamburgerBtn {
          width: 2rem;
          height: 2rem;
          border: none;
          background: transparent;
          padding: 0;
          display: flex;
          flex-direction: column;
          justify-content: space-around;
          cursor: pointer;
        }

        .line {
          width: 2rem;
          height: 0.2rem;
          background: currentColor;
          border-radius: 4px;
        }

        .overlay {
          position: fixed;
          inset: 0;
          background: rgba(150, 150, 150, 0.35);
          z-index: 39;
        }

        .mobileDrawer {
          position: fixed;
          top: 0;
          left: 0;
          width: 240px;
          height: 100vh;
          background: #fff;
          display: flex;
          flex-direction: column;
          gap: 1rem;
          padding: 5rem 1.25rem 1.25rem;
          z-index: 40;
          box-sizing: border-box;
          transform: translateX(-100%);
          opacity: 0;
          visibility: hidden;
          pointer-events: none;
          transition: transform 0.2s ease, opacity 0.2s ease, visibility 0s linear 0.2s;
        }

        .mobileDrawer.open {
          transform: translateX(0);
          opacity: 1;
          visibility: visible;
          pointer-events: auto;
          transition: transform 0.2s ease, opacity 0.2s ease;
        }

        .closeBtn {
          position: absolute;
          top: 1rem;
          right: 1rem;
          width: 2rem;
          height: 2rem;
          border: none;
          background: transparent;
          color: currentColor;
          font-size: 1.8rem;
          line-height: 1;
          cursor: pointer;
        }

        .mobileDrawer a {
          color: currentColor;
          text-decoration: none;
          font-weight: 600;
        }

        @media (min-width: 768px) {
          .desktopLinks {
            display: flex;
          }

          .hamburgerBtn,
          .mobileDrawer,
          .overlay {
            display: none;
          }
        }
      `}</style>
    </>
  );
}
