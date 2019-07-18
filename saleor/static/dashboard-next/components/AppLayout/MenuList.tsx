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
import configureIcon from "../../../images/menu-configure-icon.svg";
import { User } from "../../auth/types/User";
import { configurationMenu, configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import { createHref } from "../../misc";
import { orderDraftListUrl, orderListUrl } from "../../orders/urls";
import MenuNested from "./MenuNested";
import { IMenuItem } from "./menuStructure";

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
    menuIsActive: {
      boxShadow: "0px 0px 12px 1px rgba(0,0,0,0.2)"
    },
    menuItemHover: {
      "& path": {
        transition: "fill 0.5s ease"
      },
      "&:hover": {
        "& path": {
          fill: theme.palette.primary.main
        },
        "&:before": {
          borderLeft: `solid 2px ${theme.palette.primary.main}`,
          content: "''",
          height: 33,
          left: -25,
          position: "absolute",
          top: 8
        },
        color: theme.palette.primary.main
      },
      cursor: "pointer",
      position: "relative"
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
      alignItems: "center",
      display: "block",
      marginBottom: theme.spacing.unit * 5,
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
      }
    },
    menuListItemOpen: {
      "&:after": {
        borderBottom: `10px solid transparent`,
        borderLeft: `10px solid ${theme.palette.background.paper}`,
        borderTop: `10px solid transparent`,
        content: "''",
        height: 0,
        position: "absolute",
        right: -35,
        top: 15,
        width: 0
      },
      position: "relative"
    },
    menuListItemText: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      cursor: "pointer",
      display: "inline-block",
      fontSize: "1rem",
      fontWeight: 500,
      opacity: 1,
      paddingLeft: 16,
      textTransform: "uppercase",
      transition: "opacity 0.2s ease 0.1s"
    },
    menuListItemTextHide: {
      opacity: 0,
      position: "absolute",
      transition: "opacity 0.2s ease"
    },
    subMenu: {
      padding: "0 15px"
    },
    subMenuDrawer: {
      background: "#000",
      cursor: "pointer",
      height: "100vh",
      left: 0,
      opacity: 0.2,
      position: "absolute",
      top: 0,
      width: 0,
      zIndex: -2
    },
    subMenuDrawerOpen: {
      width: `100vw`
    }
  });

interface MenuListProps {
  className?: string;
  menuItems: IMenuItem[];
  isMenuSmall: boolean;
  location: string;
  user: User;
  renderConfigure: boolean;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}

export interface IActiveSubMenu {
  isActive: boolean;
  label: string | null;
}

const MenuList = withStyles(styles, { name: "MenuList" })(
  ({
    classes,
    className,
    menuItems,
    isMenuSmall,
    location,
    user,
    renderConfigure,
    onMenuItemClick
  }: MenuListProps & WithStyles<typeof styles>) => {
    const { isDark } = useTheme();
    const [activeSubMenu, setActiveSubMenu] = React.useState<IActiveSubMenu>({
      isActive: false,
      label: null
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
        label: null
      });
      if (menuItemUrl && event) {
        onMenuItemClick(menuItemUrl, event);
        event.stopPropagation();
        event.preventDefault();
      }
    };

    return (
      <div
        className={classNames(className, {
          [classes.menuIsActive]: activeSubMenu.isActive
        })}
      >
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
                  [classes.menuListItemActive]: isAnyChildActive
                })}
              >
                <div
                  className={classNames(classes.menuItemHover, {
                    [classes.menuListItemOpen]:
                      menuItem.ariaLabel === activeSubMenu.label &&
                      activeSubMenu.isActive
                  })}
                  onClick={() => handleSubMenu(menuItem.ariaLabel)}
                >
                  <SVG
                    className={classNames(classes.menuIcon, {
                      [classes.menuIconDark]: isDark
                    })}
                    src={menuItem.icon}
                  />
                  <Typography
                    aria-label={menuItem.ariaLabel}
                    className={classNames(classes.menuListItemText, {
                      [classes.menuListItemTextHide]: !isMenuSmall
                    })}
                  >
                    {menuItem.label}
                  </Typography>
                </div>
                <MenuNested
                  activeItem={activeSubMenu}
                  closeSubMenu={setActiveSubMenu}
                  menuItem={menuItem}
                  onMenuItemClick={onMenuItemClick}
                  handleSubMenu={handleSubMenu}
                  title={menuItem.label}
                  icon={menuItem.icon}
                  ariaLabel={menuItem.ariaLabel}
                />
                <div
                  onClick={event => closeSubMenu(null, event)}
                  className={classNames(classes.subMenuDrawer, {
                    [classes.subMenuDrawerOpen]: activeSubMenu.isActive
                  })}
                />
              </div>
            );
          }

          return (
            <a
              className={classNames(classes.menuListItem, {
                [classes.menuListItemActive]: isActive(menuItem)
              })}
              href={createHref(menuItem.url)}
              onClick={event => closeSubMenu(menuItem.url, event)}
              key={menuItem.label}
            >
              <div className={classes.menuItemHover}>
                <SVG
                  className={classNames(classes.menuIcon, {
                    [classes.menuIconDark]: isDark
                  })}
                  src={menuItem.icon}
                />
                <Typography
                  aria-label={menuItem.ariaLabel}
                  className={classNames(classes.menuListItemText, {
                    [classes.menuListItemTextHide]: !isMenuSmall
                  })}
                >
                  {menuItem.label}
                </Typography>
              </div>
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
              className={classes.menuListItem}
              href={createHref(configurationMenuUrl)}
              onClick={event => onMenuItemClick(configurationMenuUrl, event)}
            >
              <div className={classes.menuItemHover}>
                <SVG
                  className={classNames(classes.menuIcon, {
                    [classes.menuIconDark]: isDark
                  })}
                  src={configureIcon}
                />
                <Typography
                  aria-label="configure"
                  className={classNames(classes.menuListItemText, {
                    [classes.menuListItemTextHide]: !isMenuSmall
                  })}
                >
                  {i18n.t("Configure")}
                </Typography>
              </div>
            </a>
          )}
      </div>
    );
  }
);
export default MenuList;
