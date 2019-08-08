import React from "react";

import { attributeListUrl } from "@saleor/attributes/urls";
import { WindowTitle } from "@saleor/components/WindowTitle";
import useNavigator from "@saleor/hooks/useNavigator";
import useUser from "@saleor/hooks/useUser";
import i18n from "@saleor/i18n";
import Navigation from "@saleor/icons/Navigation";
import Pages from "@saleor/icons/Pages";
import ProductTypes from "@saleor/icons/ProductTypes";
import ShippingMethods from "@saleor/icons/ShippingMethods";
import SiteSettings from "@saleor/icons/SiteSettings";
import StaffMembers from "@saleor/icons/StaffMembers";
import Taxes from "@saleor/icons/Taxes";
import { maybe } from "@saleor/misc";
import { menuListUrl } from "@saleor/navigation/urls";
import { pageListUrl } from "@saleor/pages/urls";
import { productTypeListUrl } from "@saleor/productTypes/urls";
import { shippingZonesListUrl } from "@saleor/shipping/urls";
import { siteSettingsUrl } from "@saleor/siteSettings/urls";
import { staffListUrl } from "@saleor/staff/urls";
import { taxSection } from "@saleor/taxes/urls";
import { PermissionEnum } from "@saleor/types/globalTypes";
import ConfigurationPage, { MenuItem } from "./ConfigurationPage";

export const configurationMenu: MenuItem[] = [
  {
    description: i18n.t("Determine attributes used to create product types"),
    icon: <ProductTypes fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_PRODUCTS,
    title: i18n.t("Attributes"),
    url: attributeListUrl()
  },
  {
    description: i18n.t("Define types of products you sell"),
    icon: <ProductTypes fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_PRODUCTS,
    title: i18n.t("Product Types"),
    url: productTypeListUrl()
  },
  {
    description: i18n.t("Manage your employees and their permissions"),
    icon: <StaffMembers fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_STAFF,
    title: i18n.t("Staff Members"),
    url: staffListUrl()
  },
  {
    description: i18n.t("Manage how you ship out orders."),
    icon: <ShippingMethods fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_SHIPPING,
    title: i18n.t("Shipping Methods"),
    url: shippingZonesListUrl()
  },
  {
    description: i18n.t("Manage how your store charges tax"),
    icon: <Taxes fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_PRODUCTS,
    title: i18n.t("Taxes"),
    url: taxSection
  },
  {
    description: i18n.t("Define how users can navigate through your store"),
    icon: <Navigation fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_MENUS,
    title: i18n.t("Navigation"),
    url: menuListUrl()
  },
  {
    description: i18n.t("View and update your site settings"),
    icon: <SiteSettings fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_SETTINGS,
    title: i18n.t("Site Settings"),
    url: siteSettingsUrl()
  },
  {
    description: i18n.t("Manage and add additional pages"),
    icon: <Pages fontSize="inherit" viewBox="0 0 44 44" />,
    permission: PermissionEnum.MANAGE_PAGES,
    title: i18n.t("Pages"),
    url: pageListUrl()
  }
];

export const configurationMenuUrl = "/configuration/";

export const ConfigurationSection: React.StatelessComponent = () => {
  const navigate = useNavigator();
  const user = useUser();

  return (
    <>
      <WindowTitle title={i18n.t("Configuration")} />
      <ConfigurationPage
        menu={configurationMenu}
        user={maybe(() => user.user)}
        onSectionClick={navigate}
      />
    </>
  );
};
export default ConfigurationSection;
