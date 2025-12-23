import { RoomLobby } from '@/components/multiplayer/room-lobby';

export default function RoomPage({ params }: { params: { code: string } }) {
  return <RoomLobby roomCode={params.code} />;
}
