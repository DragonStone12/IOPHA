import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../types/query-keys";

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
}

async function fetchUser(): Promise<User> {
  const response = await fetch("/api/user");
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export function useUser() {
  return useQuery({
    queryKey: queryKeys.user(),
    queryFn: fetchUser,
  });
}

interface UserDisplayProps {
  className?: string;
}

export function UserDisplay({ className = "" }: UserDisplayProps) {
  const { data: user, isLoading, error } = useUser();

  if (isLoading) return <div className={className}>Loading user...</div>;
  if (error) return <div className={className}>Error loading user</div>;
  if (!user) return <div className={className}>No user data</div>;

  return (
    <div className={className} data-testid="user-display">
      <p data-testid="user-name">{user.name}</p>
      <p data-testid="user-email">{user.email}</p>
      <p data-testid="user-role">{user.role}</p>
    </div>
  );
}
