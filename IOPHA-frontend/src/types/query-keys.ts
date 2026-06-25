export const queryKeys = {
  user: () => ["user"] as const,
  userById: (id: number) => ["user", id] as const,
  userByIdWithProfile: (id: number) => ["user", id, "profile"] as const,
} as const;
