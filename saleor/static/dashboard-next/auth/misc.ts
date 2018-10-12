import { PermissionEnum } from '../types/globalTypes'
import { User } from "./types/User";

export const hasPermission = (permission: PermissionEnum, user: User) =>
  user.permissions.map(perm => perm.code).includes(permission);
