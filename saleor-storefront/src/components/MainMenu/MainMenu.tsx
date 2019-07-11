import {
  mediumScreen,
  smallScreen
} from "../../globalStyles/scss/variables.scss";
import "./scss/index.scss";

import * as React from "react";
import Media from "react-media";
import { Link } from "react-router-dom";
import ReactSVG from "react-svg";

import {
  MenuDropdown,
  Offline,
  Online,
  OverlayContext,
  OverlayTheme,
  OverlayType
} from "..";
import { maybe } from "../../core/utils";
import { baseUrl } from "../../routes";
import { CartContext } from "../CartProvider/context";
import { UserContext } from "../User/context";
import NavDropdown from "./NavDropdown";
import { TypedMainMenuQuery } from "./queries";

import cartImg from "../../images/cart.svg";
import hamburgerHoverImg from "../../images/hamburger-hover.svg";
import hamburgerImg from "../../images/hamburger.svg";
import logoImg from "../../images/logo.svg";
import searchImg from "../../images/search.svg";
import userImg from "../../images/user.svg";

const MainMenu: React.FC = () => (
  <OverlayContext.Consumer>
    {overlayContext => (
      <nav className="main-menu" id="header">
        <div className="main-menu__left">
          <TypedMainMenuQuery renderOnError displayLoader={false}>
            {({ data }) => {
              const items = maybe(() => data.shop.navigation.main.items, []);

              return (
                <ul>
                  <Media
                    query={{ maxWidth: mediumScreen }}
                    render={() => (
                      <li
                        className="main-menu__hamburger"
                        onClick={() =>
                          overlayContext.show(
                            OverlayType.sideNav,
                            OverlayTheme.left,
                            { data: items }
                          )
                        }
                      >
                        <ReactSVG
                          path={hamburgerImg}
                          className={"main-menu__hamburger--icon"}
                        />
                        <ReactSVG
                          path={hamburgerHoverImg}
                          className={"main-menu__hamburger--hover"}
                        />
                      </li>
                    )}
                  />
                  <Media
                    query={{ minWidth: mediumScreen }}
                    render={() =>
                      items.map(item => (
                        <li className="main-menu__item" key={item.id}>
                          <NavDropdown overlay={overlayContext} {...item} />
                        </li>
                      ))
                    }
                  />
                </ul>
              );
            }}
          </TypedMainMenuQuery>
        </div>

        <div className="main-menu__center">
          <Link to={baseUrl}>
            <ReactSVG path={logoImg} />
          </Link>
        </div>

        <div className="main-menu__right">
          <ul>
            <Online>
              <Media
                query={{ minWidth: smallScreen }}
                render={() => (
                  <UserContext.Consumer>
                    {({ logout, user }) =>
                      user ? (
                        <MenuDropdown
                          head={
                            <li className="main-menu__icon main-menu__user--active">
                              <ReactSVG path={userImg} />
                            </li>
                          }
                          content={
                            <ul className="main-menu__dropdown">
                              <li>
                                <Link to="/my-account">My Account</Link>
                              </li>
                              <li>
                                <Link to="/order-history">Order history</Link>
                              </li>
                              <li>
                                <Link to="/address-book">Address book</Link>
                              </li>
                              <li>
                                <Link to="/payment-options">
                                  Payment options
                                </Link>
                              </li>
                              <li onClick={logout} data-testid="logout-link">
                                Log Out
                              </li>
                            </ul>
                          }
                        />
                      ) : (
                        <li
                          data-testid="login-btn"
                          className="main-menu__icon"
                          onClick={() =>
                            overlayContext.show(
                              OverlayType.login,
                              OverlayTheme.right
                            )
                          }
                        >
                          <ReactSVG path={userImg} />
                        </li>
                      )
                    }
                  </UserContext.Consumer>
                )}
              />
              <CartContext.Consumer>
                {cart => (
                  <li
                    className="main-menu__icon main-menu__cart"
                    onClick={() => {
                      overlayContext.show(OverlayType.cart, OverlayTheme.right);
                    }}
                  >
                    <ReactSVG path={cartImg} />
                    {cart.getQuantity() > 0 ? (
                      <span className="main-menu__cart__quantity">
                        {cart.getQuantity()}
                      </span>
                    ) : null}
                  </li>
                )}
              </CartContext.Consumer>
            </Online>
            <Offline>
              <li className="main-menu__offline">
                <Media
                  query={{ minWidth: mediumScreen }}
                  render={() => <span>Offline</span>}
                />
              </li>
            </Offline>
            <li
              className="main-menu__search"
              onClick={() =>
                overlayContext.show(OverlayType.search, OverlayTheme.right)
              }
            >
              <Media
                query={{ minWidth: mediumScreen }}
                render={() => <span>Search</span>}
              />
              <ReactSVG path={searchImg} />
            </li>
          </ul>
        </div>
      </nav>
    )}
  </OverlayContext.Consumer>
);

export default MainMenu;
