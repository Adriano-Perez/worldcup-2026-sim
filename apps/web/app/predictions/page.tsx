import GroupStage from './GroupStage.client';

export default function PredictionsPage() {
  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-semibold mb-4">Group stage</h1>
      <p className="mb-6 text-gray-700">View all group stage match predictions and results.</p>
      <GroupStage />
    </main>
  );
}
