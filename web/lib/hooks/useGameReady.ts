import { useGameStore } from '@/lib/stores/gameStore';

export function useGameReady() {
  const hasHydrated = useGameStore((s) => s.hasHydrated);
  const gameData = useGameStore((s) => s.gameData);

  return {
    hasHydrated,
    gameData,
    ready: hasHydrated && !!gameData,
  };
}
