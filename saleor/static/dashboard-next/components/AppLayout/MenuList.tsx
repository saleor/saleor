import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";
import { matchPath } from "react-router";
import SVG from "react-inlinesvg";

import { User } from "../../auth/types/User";
import { configurationMenu, configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import { createHref } from "../../misc";
import { orderDraftListUrl, orderListUrl } from "../../orders/urls";
import MenuNested from "./MenuNested";
import { IMenuItem } from "./menuStructure";

import configureIcon from "../../../images/menu-configure-icon.svg";

const styles = (theme: Theme) =>
  createStyles({
    menuIcon: {
      display: "inline-block",
      position: "relative",
      top: 8,
      "& svg": {
        width: 32,
        height: 32
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
      "&:hover": {
        color: theme.palette.primary.main
      },
      alignItems: "center",
      display: "block",
      marginTop: theme.spacing.unit * 2,
      paddingLeft: 0,
      textDecoration: "none",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListItemActive: {
      "&:before": {
        background: theme.palette.primary.main,
        content: "''",
        height: "100%",
        left: -32,
        position: "absolute",
        width: 5
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
      paddingLeft: 16,
      textTransform: "uppercase",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListNested: {
      "& $menuListItemActive": {
        "& $menuListItemText": {
          color: theme.palette.primary.main
        },
        "&:before": {
          borderRadius: "100%",
          height: 8,
          marginLeft: 9,
          marginTop: 7,
          width: 8
        }
      },
      "& $menuListItemText": {
        textTransform: "none"
      },
      marginLeft: theme.spacing.unit * 3
    }
  });

interface MenuListProps {
  className?: string;
  menuItems: IMenuItem[];
  location: string;
  user: User;
  renderConfigure: boolean;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}
const MenuList = withStyles(styles, { name: "MenuList" })(
  ({
    classes,
    className,
    menuItems,
    location,
    user,
    renderConfigure,
    onMenuItemClick
  }: MenuListProps & WithStyles<typeof styles>) => (
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
          !user.permissions.map(perm => perm.code).includes(menuItem.permission)
        ) {
          return null;
        }

        if (!menuItem.url) {
          const isAnyChildActive = menuItem.children.reduce(
            (acc, child) => acc || isActive(child),
            false
          );

          return (
            <MenuNested
              classes={classes}
              isAnyChildActive={isAnyChildActive}
              location={location}
              menuItem={menuItem}
              onMenuItemClick={onMenuItemClick}
              user={user}
              key={menuItem.label}
            />
          );
        }

        return (
          <a
            className={classNames(classes.menuListItem, {
              [classes.menuListItemActive]: isActive(menuItem)
            })}
            href={createHref(menuItem.url)}
            onClick={event => onMenuItemClick(menuItem.url, event)}
            key={menuItem.label}
          >
            <SVG className={classes.menuIcon} src={menuItem.icon} />
            <Typography
              aria-label={menuItem.ariaLabel}
              className={classes.menuListItemText}
            >
              {menuItem.label}
            </Typography>
          </a>
        );
      })}
      {renderConfigure &&
        configurationMenu.filter(menuItem =>
          user.permissions.map(perm => perm.code).includes(menuItem.permission)
        ).length > 0 && (
          <a
            className={classes.menuListItem}
            href={createHref(configurationMenuUrl)}
            onClick={event => onMenuItemClick(configurationMenuUrl, event)}
          >
            <SVG className={classes.menuIcon} src={configureIcon} />
            <Typography
              aria-label="configure"
              className={classes.menuListItemText}
            >
              {i18n.t("Configure")}
            </Typography>
          </a>
        )}
    </div>
  )
);
export default MenuList;
