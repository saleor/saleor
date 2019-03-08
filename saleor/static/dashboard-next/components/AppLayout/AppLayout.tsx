import Chip from "@material-ui/core/Chip";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import LinearProgress from "@material-ui/core/LinearProgress";
import MenuItem from "@material-ui/core/MenuItem";
import Menu from "@material-ui/core/MenuList";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";
import SVG from "react-inlinesvg";
import { RouteComponentProps, withRouter } from "react-router";

import * as saleorLogo from "../../../images/logo-document.svg";
import { UserContext } from "../../auth";
import {
  appLoaderHeight,
  drawerWidth
} from "../../components/AppLayout/consts";
import MenuList from "../../components/AppLayout/MenuList";
import menuStructure from "../../components/AppLayout/menuStructure";
import ResponsiveDrawer from "../../components/AppLayout/ResponsiveDrawer";
import AppProgress from "../../components/AppProgress";
import Navigator from "../../components/Navigator";
import Toggle from "../../components/Toggle";
import i18n from "../../i18n";
import ArrowDropdown from "../../icons/ArrowDropdown";
import Anchor from "../Anchor";
import Container from "../Container";
import AppActionContext from "./AppActionContext";
import AppHeaderContext from "./AppHeaderContext";

const styles = (theme: Theme) =>
  createStyles({
    appAction: {
      bottom: 0,
      gridColumn: 2,
      position: "sticky"
    },
    appLoader: {
      height: appLoaderHeight,
      zIndex: 1201
    },
    arrow: {
      marginLeft: theme.spacing.unit * 2,
      transition: theme.transitions.duration.standard + "ms"
    },
    content: {
      display: "flex",
      flexDirection: "column",
      minHeight: `calc(100vh - ${appLoaderHeight}px)`
    },
    header: {
      display: "flex",
      height: 40,
      marginBottom: theme.spacing.unit * 3,
      marginTop: theme.spacing.unit * 2
    },
    hide: {
      opacity: 0
    },
    logo: {
      "& svg": {
        height: "100%"
      },
      display: "block",
      height: 28
    },
    menu: {
      marginTop: theme.spacing.unit * 4
    },
    popover: {
      zIndex: 1
    },
    root: {
      [theme.breakpoints.down("sm")]: {
        gridTemplateColumns: "1fr"
      },
      display: "grid",
      gridTemplateColumns: `${drawerWidth}px 1fr`
    },
    rotate: {
      transform: "rotate(180deg)"
    },
    sideBar: {
      [theme.breakpoints.down("sm")]: {
        padding: 0
      },
      background: theme.palette.common.white,
      padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 4}px`
    },
    spacer: {
      flex: 1
    },
    userChip: {
      backgroundColor: theme.palette.common.white,
      border: `1px solid ${theme.palette.grey[200]}`
    },
    userMenuContainer: {
      position: "relative"
    },
    userMenuItem: {
      textAlign: "right"
    },
    view: {
      backgroundColor: theme.palette.background.default,
      flex: 1,
      flexGrow: 1,
      marginLeft: 0,
      paddingBottom: theme.spacing.unit,
      [theme.breakpoints.up("sm")]: {
        paddingBottom: theme.spacing.unit * 3
      }
    }
  });

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout = withStyles(styles, {
  name: "AppLayout"
})(
  withRouter<AppLayoutProps & RouteComponentProps<any>>(
    ({
      classes,
      children,
      location
    }: AppLayoutProps &
      WithStyles<typeof styles> &
      RouteComponentProps<any>) => (
      <AppProgress>
        {({ value: isProgressVisible }) => (
          <UserContext.Consumer>
            {({ logout, user }) => (
              <Anchor>
                {appHeaderAnchor => (
                  <AppHeaderContext.Provider value={appHeaderAnchor}>
                    <Anchor>
                      {appActionAnchor => (
                        <AppActionContext.Provider value={appActionAnchor}>
                          <Navigator>
                            {navigate => (
                              <Toggle>
                                {(isDrawerOpened, { disable: closeDrawer }) => {
                                  const handleMenuItemClick = (
                                    url: string,
                                    event: React.MouseEvent<any>
                                  ) => {
                                    event.stopPropagation();
                                    event.preventDefault();
                                    closeDrawer();
                                    navigate(url);
                                  };
                                  return (
                                    <>
                                      <LinearProgress
                                        className={classNames(
                                          classes.appLoader,
                                          {
                                            [classes.hide]: !isProgressVisible
                                          }
                                        )}
                                        color="secondary"
                                      />
                                      <div className={classes.root}>
                                        <div className={classes.sideBar}>
                                          <ResponsiveDrawer
                                            onClose={closeDrawer}
                                            open={isDrawerOpened}
                                          >
                                            <SVG
                                              className={classes.logo}
                                              src={saleorLogo}
                                            />
                                            <MenuList
                                              className={classes.menu}
                                              menuItems={menuStructure}
                                              location={location.pathname}
                                              user={user}
                                              renderConfigure={true}
                                              onMenuItemClick={
                                                handleMenuItemClick
                                              }
                                            />
                                          </ResponsiveDrawer>
                                        </div>
                                        <div className={classes.content}>
                                          <div>
                                            <Container>
                                              <div className={classes.header}>
                                                <div ref={appHeaderAnchor} />
                                                <div
                                                  className={classes.spacer}
                                                />
                                                <Anchor>
                                                  {anchor => (
                                                    <Toggle>
                                                      {(
                                                        menuOpen,
                                                        {
                                                          disable: closeMenu,
                                                          enable: openMenu
                                                        }
                                                      ) => {
                                                        const handleLogout = () => {
                                                          close();
                                                          logout();
                                                        };
                                                        return (
                                                          <div
                                                            className={
                                                              classes.userMenuContainer
                                                            }
                                                            ref={anchor}
                                                          >
                                                            <Chip
                                                              className={
                                                                classes.userChip
                                                              }
                                                              label={
                                                                <>
                                                                  {user.email}
                                                                  <ArrowDropdown
                                                                    className={classNames(
                                                                      classes.arrow,
                                                                      {
                                                                        [classes.rotate]: menuOpen
                                                                      }
                                                                    )}
                                                                  />
                                                                </>
                                                              }
                                                              onClick={openMenu}
                                                            />
                                                            <Popper
                                                              className={
                                                                classes.popover
                                                              }
                                                              open={menuOpen}
                                                              anchorEl={
                                                                anchor.current
                                                              }
                                                              transition
                                                              disablePortal
                                                              placement="bottom-end"
                                                            >
                                                              {({
                                                                TransitionProps,
                                                                placement
                                                              }) => (
                                                                <Grow
                                                                  {...TransitionProps}
                                                                  style={{
                                                                    transformOrigin:
                                                                      placement ===
                                                                      "bottom"
                                                                        ? "right top"
                                                                        : "right bottom"
                                                                  }}
                                                                >
                                                                  <Paper>
                                                                    <ClickAwayListener
                                                                      onClickAway={
                                                                        closeMenu
                                                                      }
                                                                      mouseEvent="onClick"
                                                                    >
                                                                      <Menu>
                                                                        <MenuItem
                                                                          className={
                                                                            classes.userMenuItem
                                                                          }
                                                                          onClick={
                                                                            handleLogout
                                                                          }
                                                                        >
                                                                          {i18n.t(
                                                                            "Log out",
                                                                            {
                                                                              context:
                                                                                "button"
                                                                            }
                                                                          )}
                                                                        </MenuItem>
                                                                      </Menu>
                                                                    </ClickAwayListener>
                                                                  </Paper>
                                                                </Grow>
                                                              )}
                                                            </Popper>
                                                          </div>
                                                        );
                                                      }}
                                                    </Toggle>
                                                  )}
                                                </Anchor>
                                              </div>
                                            </Container>
                                          </div>
                                          <main className={classes.view}>
                                            {children}
                                          </main>
                                          <div
                                            className={classes.appAction}
                                            ref={appActionAnchor}
                                          />
                                        </div>
                                      </div>
                                    </>
                                  );
                                }}
                              </Toggle>
                            )}
                          </Navigator>
                        </AppActionContext.Provider>
                      )}
                    </Anchor>
                  </AppHeaderContext.Provider>
                )}
              </Anchor>
            )}
          </UserContext.Consumer>
        )}
      </AppProgress>
    )
  )
);

export default AppLayout;
