import { PermissionEnum } from '../types/globalTypes';
import { StaffList_staffUsers_edges_node } from "./types/StaffList";
import { StaffMemberDetails_user } from "./types/StaffMemberDetails";


export const permissions = [
  {
    code:  PermissionEnum.IMPERSONATE_USERS,
    name: "Impersonate customers."
  },
  {
    code: PermissionEnum.MANAGE_DISCOUNTS,
    name: "Manage sales and vouchers."
  },
  {
    code: PermissionEnum.MANAGE_MENUS,
    name: "Manage navigation."
  },
  {
    code: PermissionEnum.MANAGE_ORDERS,
    name: "Manage orders."
  },
  {
    code: PermissionEnum.MANAGE_PAGES,
    name: "Manage pages."
  },
  {
    code: PermissionEnum.MANAGE_PRODUCTS,
    name: "Manage products."
  },
  {
    code: PermissionEnum.MANAGE_SETTINGS,
    name: "Manage settings."
  },
  {
    code: PermissionEnum.MANAGE_SHIPPING,
    name: "Manage shipping."
  },
  {
    code: PermissionEnum.MANAGE_STAFF,
    name: "Manage staff."
  },
  {
    code: PermissionEnum.MANAGE_USERS,
    name: "Manage customers."
  }
].map(perm => ({
  __typename: "PermissionDisplay" as "PermissionDisplay",
  ...perm
}));
export const staffMembers: StaffList_staffUsers_edges_node[] = [
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  }
].map(staffMember => ({ __typename: "User" as "User", ...staffMember }));
export const staffMember: StaffMemberDetails_user = {
  __typename: "User",
  email: "admin@example.com",
  id: "VXNlcjoyMQ==",
  isActive: true,
  permissions: [
    {
      code: PermissionEnum.IMPERSONATE_USERS,
      name: "Impersonate customers."
    },
    {
      code: PermissionEnum.MANAGE_DISCOUNTS,
      name: "Manage sales and vouchers."
    },
    {
      code: PermissionEnum.MANAGE_MENUS,
      name: "Manage navigation."
    },
    {
      code: PermissionEnum.MANAGE_ORDERS,
      name: "Manage orders."
    },
    {
      code: PermissionEnum.MANAGE_PAGES,
      name: "Manage pages."
    },
    {
      code: PermissionEnum.MANAGE_PRODUCTS,
      name: "Manage products."
    },
    {
      code: PermissionEnum.MANAGE_SETTINGS,
      name: "Manage settings."
    },
    {
      code: PermissionEnum.MANAGE_SHIPPING,
      name: "Manage shipping."
    },
    {
      code: PermissionEnum.MANAGE_STAFF,
      name: "Manage staff."
    },
    {
      code: PermissionEnum.MANAGE_USERS,
      name: "Manage customers."
    }
  ].map(perm => ({
    __typename: "PermissionDisplay" as "PermissionDisplay",
    ...perm
  }))
};
