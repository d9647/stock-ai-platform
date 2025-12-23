import { LeaderboardView } from '@/components/multiplayer/leaderboard';

export default function LeaderboardPage({ params }: { params: { code: string } }) {
  return <LeaderboardView roomCode={params.code} />;
}
