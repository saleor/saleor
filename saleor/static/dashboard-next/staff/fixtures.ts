import { StaffList_staffUsers_edges_node } from "./types/StaffList";
import { StaffMemberDetails_user } from "./types/StaffMemberDetails";

export const permissions = [
  {
    code: "account.impersonate_users",
    name: "Impersonate customers."
  },
  {
    code: "discount.manage_discounts",
    name: "Manage sales and vouchers."
  },
  {
    code: "menu.manage_menus",
    name: "Manage navigation."
  },
  {
    code: "order.manage_orders",
    name: "Manage orders."
  },
  {
    code: "page.manage_pages",
    name: "Manage pages."
  },
  {
    code: "product.manage_products",
    name: "Manage products."
  },
  {
    code: "site.manage_settings",
    name: "Manage settings."
  },
  {
    code: "shipping.manage_shipping",
    name: "Manage shipping."
  },
  {
    code: "account.manage_staff",
    name: "Manage staff."
  },
  {
    code: "account.manage_users",
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
      code: "account.impersonate_users",
      name: "Impersonate customers."
    },
    {
      code: "discount.manage_discounts",
      name: "Manage sales and vouchers."
    },
    {
      code: "menu.manage_menus",
      name: "Manage navigation."
    },
    {
      code: "order.manage_orders",
      name: "Manage orders."
    },
    {
      code: "page.manage_pages",
      name: "Manage pages."
    },
    {
      code: "product.manage_products",
      name: "Manage products."
    },
    {
      code: "site.manage_settings",
      name: "Manage settings."
    },
    {
      code: "shipping.manage_shipping",
      name: "Manage shipping."
    },
    {
      code: "account.manage_staff",
      name: "Manage staff."
    },
    {
      code: "account.manage_users",
      name: "Manage customers."
    }
  ].map(perm => ({
    __typename: "PermissionDisplay" as "PermissionDisplay",
    ...perm
  }))
};
