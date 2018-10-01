import { User } from "./types/User";

export const hasPermission = (permission: string, user: User) =>
  user.permissions.map(perm => perm.code).includes(permission);
