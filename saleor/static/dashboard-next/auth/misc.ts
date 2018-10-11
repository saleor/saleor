import { User } from "./types/User";
import { PermissionEnum } from '../types/globalTypes'

export const hasPermission = (permission: PermissionEnum, user: User) =>
  user.permissions.map(perm => perm.code).includes(permission);
