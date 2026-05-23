"use client";

import React from 'react';

type Match = { home: string; away: string; date?: string };
type Group = { id: string; teams: string[]; matches: Match[] };

const SAMPLE_GROUPS: Group[] = [
  { id: 'A', teams: ['Team A1', 'Team A2', 'Team A3', 'Team A4'], matches: [{ home: 'Team A1', away: 'Team A2', date: 'Jun 28' }, { home: 'Team A3', away: 'Team A4', date: 'Jun 29' }] },
  { id: 'B', teams: ['Team B1', 'Team B2', 'Team B3', 'Team B4'], matches: [{ home: 'Team B1', away: 'Team B2', date: 'Jun 29' }, { home: 'Team B3', away: 'Team B4', date: 'Jun 30' }] },
];

export default function GroupStageClient() {
  return (
    <section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {SAMPLE_GROUPS.map((g) => (
          <div key={g.id} className="bg-white rounded-lg shadow p-4">
            <h2 className="text-xl font-medium mb-2">Group {g.id}</h2>
            <div className="mb-3">
              <div className="text-sm text-gray-600 mb-1">Teams</div>
              <ul className="list-disc list-inside text-sm">
                {g.teams.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-2">Matches</div>
              <div className="space-y-2">
                {g.matches.map((m, idx) => (
                  <div key={idx} className="flex justify-between items-center text-sm">
                    <div>{m.home} vs {m.away}</div>
                    <div className="text-gray-500">{m.date ?? 'TBD'}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
