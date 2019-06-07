import * as React from "react";

import useNavigator from "@hooks/useNavigator";
import useUser from "@hooks/useUser";
import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import Navigation from "../icons/Navigation";
import Pages from "../icons/Pages";
import ProductTypes from "../icons/ProductTypes";
import ShippingMethods from "../icons/ShippingMethods";
import SiteSettings from "../icons/SiteSettings";
import StaffMembers from "../icons/StaffMembers";
import Taxes from "../icons/Taxes";
import { maybe } from "../misc";
import { menuListUrl } from "../navigation/urls";
import { pageListUrl } from "../pages/urls";
import { productTypeListUrl } from "../productTypes/urls";
import { shippingZonesListUrl } from "../shipping/urls";
import { siteSettingsUrl } from "../siteSettings/urls";
import { staffListUrl } from "../staff/urls";
import { taxSection } from "../taxes/urls";
import { PermissionEnum } from "../types/globalTypes";
import ConfigurationPage, { MenuItem } from "./ConfigurationPage";

export const configurationMenu: MenuItem[] = [
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
