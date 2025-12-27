import { Suspense } from 'react';
import { JoinRoom } from '@/components/multiplayer/join-room';

export default function JoinRoomPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-base flex items-center justify-center">Loading...</div>}>
      <JoinRoom />
    </Suspense>
  );
}
