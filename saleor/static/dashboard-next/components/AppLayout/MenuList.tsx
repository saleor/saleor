import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import * as React from "react";
import { matchPath } from "react-router";
import * as urlJoin from "url-join";

import { appMountPoint } from "../..";
import { User } from "../../auth/types/User";
import { configurationMenu, configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import Toggle from "../Toggle";
import { IMenuItem } from "./menuStructure";

const styles = (theme: Theme) =>
  createStyles({
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
      color: "#616161",
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
        width: 2
      },
      position: "relative"
    },
    menuListItemText: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      cursor: "pointer",
      fontSize: "1rem",
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
      {menuItems.map(menuItem => {
        if (
          menuItem.permission &&
          !user.permissions.map(perm => perm.code).includes(menuItem.permission)
        ) {
          return null;
        }
        if (!menuItem.url) {
          const isActive = menuItem.children.reduce(
            (acc, child) =>
              acc ||
              !!matchPath(location, {
                exact: child.url === "/",
                path: child.url
              }),
            false
          );
          return (
            <Toggle key={menuItem.label} initial={isActive}>
              {(openedMenu, { enable: enableMenu }) => (
                <>
                  <div
                    onClick={enableMenu}
                    className={classNames(classes.menuListItem, {
                      [classes.menuListItemActive]: isActive
                    })}
                  >
                    <Typography
                      aria-label={menuItem.ariaLabel}
                      className={classes.menuListItemText}
                    >
                      {menuItem.label}
                    </Typography>
                    {openedMenu && (
                      <div className={classes.menuListNested}>
                        <MenuList
                          menuItems={menuItem.children}
                          location={location}
                          user={user}
                          renderConfigure={false}
                          onMenuItemClick={onMenuItemClick}
                        />
                      </div>
                    )}
                  </div>
                </>
              )}
            </Toggle>
          );
        }
        const isActive = !!matchPath(location, {
          exact: menuItem.url === "/",
          path: menuItem.url
        });

        return (
          <a
            className={classNames(classes.menuListItem, {
              [classes.menuListItemActive]: isActive
            })}
            href={urlJoin(appMountPoint, menuItem.url)}
            onClick={event => onMenuItemClick(menuItem.url, event)}
            key={menuItem.label}
          >
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
            href={urlJoin(appMountPoint, configurationMenuUrl)}
            onClick={event => onMenuItemClick(configurationMenuUrl, event)}
          >
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
