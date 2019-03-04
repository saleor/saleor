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

import * as saleorLogo from "../../../images/logo-document.svg";
import { UserContext } from "../../auth";
import { drawerWidth } from "../../components/AppLayout/consts";
import MenuList from "../../components/AppLayout/MenuList";
import menuStructure from "../../components/AppLayout/menuStructure";
import ResponsiveDrawer from "../../components/AppLayout/ResponsiveDrawer";
import AppProgress from "../../components/AppProgress";
import MenuToggle from "../../components/MenuToggle";
import Navigator from "../../components/Navigator";
import Toggle from "../../components/Toggle";
import i18n from "../../i18n";
import ArrowDropdown from "../../icons/ArrowDropdown";
import Anchor from "../Anchor";
import Container from "../Container";
import AppHeaderContext from "./AppHeaderContext";

const styles = (theme: Theme) =>
  createStyles({
    appLoader: {
      height: 2
    },
    arrow: {
      marginLeft: theme.spacing.unit * 2,
      transition: theme.transitions.duration.standard + "ms"
    },
    content: {
      backgroundColor: theme.palette.background.default,
      flexGrow: 1,
      marginLeft: 0,
      padding: theme.spacing.unit,
      [theme.breakpoints.up("sm")]: {
        padding: theme.spacing.unit * 2
      }
    },
    header: {
      display: "flex",
      height: 40,
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
    root: {
      display: "grid",
      gridTemplateColumns: `${drawerWidth}px 1fr`
    },
    rotate: {
      transform: "rotate(180deg)"
    },
    sideBar: {
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
    }
  });

interface AppLayoutProps {
  children: React.ReactNode;
}
// const AppLayout = withStyles(styles, {
//   name: "AppLayout"
// })(({ classes, children }: AppLayoutProps & WithStyles<typeof styles>) => (
//   <AppProgress>
//     {({ value: isProgressVisible }) => (
//       <UserContext.Consumer>
//         {({ logout, user }) => (
//           <Navigator>
//             {navigate => (
//               <Toggle>
//                 {(
//                   isDrawerOpened,
//                   { toggle: toggleDrawer, disable: closeDrawer }
//                 ) => {
//                   const handleMenuItemClick = (
//                     url: string,
//                     event: React.MouseEvent<any>
//                   ) => {
//                     event.preventDefault();
//                     closeDrawer();
//                     navigate(url);
//                   };
//                   return (
//                     <div className={classes.appFrame}>
//                       <AppBar className={classes.appBar}>
//                         <Toolbar disableGutters className={classes.toolBarMenu}>
//                           <IconButton
//                             color="inherit"
//                             aria-label="open drawer"
//                             onClick={toggleDrawer}
//                             className={classes.menuButton}
//                           >
//                             <MenuIcon />
//                           </IconButton>
//                           <SVG className={classes.logo} src={saleorLogo} />
//                         </Toolbar>
//                         <Toolbar
//                           disableGutters
//                           className={classes.toolBarContent}
//                         >
//                           <div className={classes.spacer} />
//                           <MenuToggle ariaOwns="user-menu">
//                             {({
//                               open: menuOpen,
//                               actions: { open: openMenu, close: closeMenu }
//                             }) => {
//                               const handleLogout = () => {
//                                 close();
//                                 logout();
//                               };
//                               return (
//                                 <Anchor>
//                                   {anchor => (
//                                     <>
//                                       <div
//                                         className={classes.email}
//                                         ref={anchor}
//                                         onClick={
//                                           !menuOpen ? openMenu : undefined
//                                         }
//                                       >
//                                         <Hidden smDown>
//                                           <Typography
//                                             className={classes.emailLabel}
//                                             component="span"
//                                             variant="subheading"
//                                           >
//                                             {user.email}
//                                           </Typography>
//                                           <ArrowDropdown
//                                             className={classNames({
//                                               [classes.arrow]: true,
//                                               [classes.rotate]: menuOpen
//                                             })}
//                                           />
//                                         </Hidden>
//                                         <Hidden mdUp>
//                                           <IconButton
//                                             className={classes.userIcon}
//                                           >
//                                             <Person />
//                                           </IconButton>
//                                         </Hidden>
//                                       </div>
//                                       <Popper
//                                         open={menuOpen}
//                                         anchorEl={anchor.current}
//                                         transition
//                                         disablePortal
//                                         placement="bottom-end"
//                                       >
//                                         {({ TransitionProps, placement }) => (
//                                           <Grow
//                                             {...TransitionProps}
//                                             style={{
//                                               minWidth: "10rem",
//                                               transformOrigin:
//                                                 placement === "bottom"
//                                                   ? "right top"
//                                                   : "right bottom"
//                                             }}
//                                           >
//                                             <Paper>
//                                               <ClickAwayListener
//                                                 onClickAway={closeMenu}
//                                                 mouseEvent="onClick"
//                                               >
//                                                 <Menu>
//                                                   <MenuItem
//                                                     className={
//                                                       classes.userMenuItem
//                                                     }
//                                                     onClick={handleLogout}
//                                                   >
//                                                     {i18n.t("Log out", {
//                                                       context: "button"
//                                                     })}
//                                                   </MenuItem>
//                                                 </Menu>
//                                               </ClickAwayListener>
//                                             </Paper>
//                                           </Grow>
//                                         )}
//                                       </Popper>
//                                     </>
//                                   )}
//                                 </Anchor>
//                               );
//                             }}
//                           </MenuToggle>
//                         </Toolbar>
//                         {isProgressVisible && (
//                           <LinearProgress
//                             className={classes.appLoader}
//                             color="secondary"
//                           />
//                         )}
//                       </AppBar>
//                       <ResponsiveDrawer
//                         onClose={closeDrawer}
//                         open={isDrawerOpened}
//                       >
//                         <div className={classes.menuList}>
//                           <MenuList
//                             menuItems={menuStructure}
//                             user={user}
//                             onMenuItemClick={handleMenuItemClick}
//                           />
//                           <div className={classes.spacer} />
//                           {configurationMenu.filter(menuItem =>
//                             user.permissions
//                               .map(perm => perm.code)
//                               .includes(menuItem.permission)
//                           ).length > 0 && (
//                             <a
//                               className={classes.menuListItem}
//                               href={removeDoubleSlashes(
//                                 appMountPoint + configurationMenuUrl
//                               )}
//                               onClick={event =>
//                                 handleMenuItemClick(configurationMenuUrl, event)
//                               }
//                             >
//                               <SettingsIcon />
//                               <Typography
//                                 aria-label="configure"
//                                 className={classes.menuListItemText}
//                               >
//                                 {i18n.t("Configure")}
//                               </Typography>
//                             </a>
//                           )}
//                         </div>
//                       </ResponsiveDrawer>
//                       <main className={classes.content}>{children}</main>
//                     </div>
//                   );
//                 }}
//               </Toggle>
//             )}
//           </Navigator>
//         )}
//       </UserContext.Consumer>
//     )}
//   </AppProgress>
// ));

const AppLayout = withStyles(styles, {
  name: "AppLayout"
})(({ classes, children }: AppLayoutProps & WithStyles<typeof styles>) => (
  <AppProgress>
    {({ value: isProgressVisible }) => (
      <UserContext.Consumer>
        {({ logout, user }) => (
          <Anchor>
            {appHeaderAnchor => (
              <AppHeaderContext.Provider value={appHeaderAnchor}>
                <Navigator>
                  {navigate => (
                    <Toggle>
                      {(
                        isDrawerOpened,
                        { toggle: toggleDrawer, disable: closeDrawer }
                      ) => {
                        const handleMenuItemClick = (
                          url: string,
                          event: React.MouseEvent<any>
                        ) => {
                          event.preventDefault();
                          closeDrawer();
                          navigate(url);
                        };
                        return (
                          <>
                            <LinearProgress
                              className={classNames(classes.appLoader, {
                                [classes.hide]: !isProgressVisible
                              })}
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
                                    user={user}
                                    onMenuItemClick={handleMenuItemClick}
                                  />
                                </ResponsiveDrawer>
                              </div>
                              <div>
                                <Container width="md">
                                  <div className={classes.header}>
                                    <div ref={appHeaderAnchor} />
                                    <div className={classes.spacer} />
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
                                                  className={classes.userChip}
                                                  label={
                                                    <>
                                                      {user.email}
                                                      <ArrowDropdown
                                                        className={classNames({
                                                          [classes.arrow]: true,
                                                          [classes.rotate]: menuOpen
                                                        })}
                                                      />
                                                    </>
                                                  }
                                                  onClick={openMenu}
                                                />
                                                <Popper
                                                  open={menuOpen}
                                                  anchorEl={anchor.current}
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
                                                          placement === "bottom"
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
                                <main className={classes.content}>
                                  {children}
                                </main>
                              </div>
                            </div>
                          </>
                        );
                      }}
                    </Toggle>
                  )}
                </Navigator>
              </AppHeaderContext.Provider>
            )}
          </Anchor>
        )}
      </UserContext.Consumer>
    )}
  </AppProgress>
));

export default AppLayout;
