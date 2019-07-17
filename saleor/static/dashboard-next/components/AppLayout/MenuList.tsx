import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";
import SVG from "react-inlinesvg";
import { matchPath } from "react-router";

import useTheme from "@saleor/hooks/useTheme";
import { User } from "../../auth/types/User";
import { configurationMenu, configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import { createHref } from "../../misc";
import { orderDraftListUrl, orderListUrl } from "../../orders/urls";
import { drawerWidth, drawerWidthSmall } from "./consts";
import MenuNested from "./MenuNested";
import { IMenuItem } from "./menuStructure";

import configureIcon from "../../../images/menu-configure-icon.svg";

const styles = (theme: Theme) =>
  createStyles({
    menuIcon: {
      "& svg": {
        height: 32,
        width: 32
      },
      display: "inline-block",
      position: "relative",
      top: 8
    },
    menuIconDark: {
      "& path": {
        fill: theme.palette.common.white
      }
    },
    menuList: {
      display: "flex",
      flexDirection: "column",
      height: "100%",
      marginLeft: theme.spacing.unit * 4,
      marginTop: theme.spacing.unit * 2,
      paddingBottom: theme.spacing.unit * 3
    },
    menuListItem: {
      "& path": {
        transition: "fill 0.5s ease"
      },
      "&:hover": {
        "& path": {
          fill: theme.palette.primary.main
        },
        color: theme.palette.primary.main
      },
      alignItems: "center",
      cursor: "pointer",
      display: "block",
      marginTop: theme.spacing.unit * 2,
      paddingLeft: 0,
      textDecoration: "none",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListItemActive: {
      "& $menuListItemText": {
        color: theme.palette.primary.main
      },
      "& path": {
        color: theme.palette.primary.main,
        fill: theme.palette.primary.main
      },
      "&:before": {
        background: theme.palette.primary.main,
        content: "''",
        height: "100%",
        left: -32,
        position: "absolute",
        width: 5
      }
    },
    menuListItemSmall: {
      marginTop: theme.spacing.unit * 3.5
    },
    menuListItemText: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      cursor: "pointer",
      display: "inline-block",
      fontSize: "1rem",
      fontWeight: 500,
      paddingLeft: 16,
      textTransform: "uppercase",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListNested: {
      "& $menuListItemActive": {
        "& $menuListItemText": {
          color: theme.palette.primary.main
        }
      },
      "& $menuListItemText": {
        textTransform: "none"
      },
      background: theme.palette.background.paper,
      height: "100vh",
      position: "absolute",
      right: 0,
      top: 0,
      transition: "right 1s ease",
      width: 300,
      zIndex: -1
    },
    menuListNestedHide: {
      opacity: 0
    },
    menuListNestedItem: {
      "&:hover": {
        "& p": {
          color: theme.palette.primary.main
        }
      },
      display: "block",
      padding: "0px 30px",
      textDecoration: "none"
    },
    menuListNestedOpen: {
      right: -300,
      zIndex: -1
    },
    subMenu: {
      padding: "0 15px"
    },
    subMenuDrawer: {
      background: "#000",
      cursor: "pointer",
      height: "100vh",
      left: drawerWidth,
      opacity: 0.2,
      position: "absolute",
      top: 0,
      width: 0,
      zIndex: -2
    },
    subMenuDrawerOpen: {
      "&$subMenuDrawerSmall": {
        left: drawerWidthSmall,
        width: `calc(100vw - ${drawerWidthSmall})px`
      },
      width: `calc(100vw - ${drawerWidth}px)`
    },
    subMenuDrawerSmall: {
      left: drawerWidthSmall,
      width: `calc(100vw - ${drawerWidthSmall})px`
    },
    subheader: {
      borderBottom: "solid 1px #EAEAEA",
      margin: "30px",
      paddingBottom: 20
    }
  });

interface MenuListProps {
  className?: string;
  menuItems: IMenuItem[];
  menuToggle: boolean;
  location: string;
  user: User;
  renderConfigure: boolean;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}

export interface IActiveSubMenu {
  isActive: boolean;
  label: string;
}

const MenuList = withStyles(styles, { name: "MenuList" })(
  ({
    classes,
    className,
    menuItems,
    menuToggle,
    location,
    user,
    renderConfigure,
    onMenuItemClick
  }: MenuListProps & WithStyles<typeof styles>) => {
    const { isDark } = useTheme();
    const [activeSubMenu, setActiveSubMenu] = React.useState<IActiveSubMenu>({
      isActive: false,
      label: ""
    });

    const handleSubMenu = itemLabel => {
      setActiveSubMenu({
        isActive:
          itemLabel === activeSubMenu.label ? !activeSubMenu.isActive : true,
        label: itemLabel
      });
    };

    const closeSubMenu = (menuItemUrl, event) => {
      setActiveSubMenu({
        isActive: false,
        label: ""
      });
      if (menuItemUrl && event) {
        onMenuItemClick(menuItemUrl, event);
        event.stopPropagation();
        event.preventDefault();
      }
    };

    return (
      <div className={className}>
        {/* FIXME: this .split("?")[0] looks gross */}
        {menuItems.map(menuItem => {
          const isActive = (menuItem: IMenuItem) =>
            location.split("?")[0] === orderDraftListUrl().split("?")[0] &&
            menuItem.url.split("?")[0] === orderListUrl().split("?")[0]
              ? false
              : !!matchPath(location.split("?")[0], {
                  exact: menuItem.url.split("?")[0] === "/",
                  path: menuItem.url.split("?")[0]
                });

          if (
            menuItem.permission &&
            !user.permissions
              .map(perm => perm.code)
              .includes(menuItem.permission)
          ) {
            return null;
          }

          if (!menuItem.url) {
            const isAnyChildActive = menuItem.children.reduce(
              (acc, child) => acc || isActive(child),
              false
            );

            return (
              <div
                className={classNames(classes.menuListItem, {
                  [classes.menuListItemSmall]: !menuToggle,
                  [classes.menuListItemActive]: isAnyChildActive
                })}
              >
                <div onClick={() => handleSubMenu(menuItem.ariaLabel)}>
                  <SVG
                    className={classNames(classes.menuIcon, {
                      [classes.menuIconDark]: isDark
                    })}
                    src={menuItem.icon}
                  />
                  {menuToggle && (
                    <Typography
                      aria-label={menuItem.ariaLabel}
                      className={classes.menuListItemText}
                    >
                      {menuItem.label}
                    </Typography>
                  )}
                </div>
                <MenuNested
                  activeItem={activeSubMenu}
                  classes={classes}
                  closeSubMenu={setActiveSubMenu}
                  menuItem={menuItem}
                  onMenuItemClick={onMenuItemClick}
                  handleSubMenu={handleSubMenu}
                  title={menuItem.label}
                  ariaLabel={menuItem.ariaLabel}
                />
                <div
                  onClick={event => closeSubMenu(null, event)}
                  className={classNames(classes.subMenuDrawer, {
                    [classes.subMenuDrawerOpen]: activeSubMenu.isActive,
                    [classes.subMenuDrawerSmall]: !menuToggle
                  })}
                />
              </div>
            );
          }

          return (
            <a
              className={classNames(classes.menuListItem, {
                [classes.menuListItemSmall]: !menuToggle,
                [classes.menuListItemActive]: isActive(menuItem)
              })}
              href={createHref(menuItem.url)}
              onClick={event => closeSubMenu(menuItem.url, event)}
              key={menuItem.label}
            >
              <SVG
                className={classNames(classes.menuIcon, {
                  [classes.menuIconDark]: isDark
                })}
                src={menuItem.icon}
              />
              {menuToggle && (
                <Typography
                  aria-label={menuItem.ariaLabel}
                  className={classes.menuListItemText}
                >
                  {menuItem.label}
                </Typography>
              )}
            </a>
          );
        })}
        {renderConfigure &&
          configurationMenu.filter(menuItem =>
            user.permissions
              .map(perm => perm.code)
              .includes(menuItem.permission)
          ).length > 0 && (
            <a
              className={classNames(classes.menuListItem, {
                [classes.menuListItemSmall]: !menuToggle
              })}
              href={createHref(configurationMenuUrl)}
              onClick={event => onMenuItemClick(configurationMenuUrl, event)}
            >
              <SVG
                className={classNames(classes.menuIcon, {
                  [classes.menuIconDark]: isDark
                })}
                src={configureIcon}
              />
              {menuToggle && (
                <Typography
                  aria-label="configure"
                  className={classes.menuListItemText}
                >
                  {i18n.t("Configure")}
                </Typography>
              )}
            </a>
          )}
      </div>
    );
  }
);
export default MenuList;
