import * as React from "react";
import Navigator from "../components/Navigator";

import i18n from "../i18n";
import AccountCircle from "../icons/AccountCircle";
import Ballot from "../icons/Ballot";
import Folder from "../icons/Folder";
import LocalShipping from "../icons/LocalShipping";
import Monetization from "../icons/Monetization";
import Navigation from "../icons/Navigation";
import Pages from "../icons/Pages";
import StoreMall from "../icons/StoreMall";
import { productTypeListUrl } from "../productTypes";
import ConfigurationPage from "./ConfigurationPage";

export const configurationMenu = [
  {
    description: i18n.t("Define types of products you sell"),
    icon: <Folder fontSize="inherit" />,
    title: i18n.t("Product Types"),
    url: productTypeListUrl
  },
  {
    description: i18n.t("Define attributes of products yousell"),
    disabled: true,
    icon: <Ballot fontSize="inherit" />,
    title: i18n.t("Attributes")
  },
  {
    description: i18n.t("Manage your employees and their permissions"),
    disabled: true,
    icon: <AccountCircle fontSize="inherit" />,
    title: i18n.t("Staff Members")
  },
  {
    description: i18n.t("Manage how you ship out orders."),
    disabled: true,
    icon: <LocalShipping fontSize="inherit" />,
    title: i18n.t("Shipping Methods")
  },
  {
    description: i18n.t("Manage how your store charges tax"),
    disabled: true,
    icon: <Monetization fontSize="inherit" />,
    title: i18n.t("Taxes")
  },
  {
    description: i18n.t("Define how users can navigate through your store"),
    disabled: true,
    icon: <Navigation fontSize="inherit" />,
    title: i18n.t("Navigation")
  },
  {
    description: i18n.t("View and update your site settings"),
    disabled: true,
    icon: <StoreMall fontSize="inherit" />,
    title: i18n.t("Site Settings")
  },
  {
    description: i18n.t("Manage and add additional pages"),
    disabled: false,
    icon: <Pages fontSize="inherit" />,
    title: i18n.t("Pages")
  }
];

export const configurationMenuUrl = "/configuration/";

export const ConfigurationSection: React.StatelessComponent = () => (
  <Navigator>
    {navigate => (
      <ConfigurationPage menu={configurationMenu} onSectionClick={navigate} />
    )}
  </Navigator>
);
export default ConfigurationSection;
