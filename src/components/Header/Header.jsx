import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import { withRouter } from 'react-router';
import ReactSVG from 'react-svg';
import { withCookies, Cookies } from 'react-cookie';

import { GitHubLink } from '..';
import css from './header.css';

import { Trans } from '@lingui/macro';

class Header extends Component {

  constructor(props) {
    super(props);
    const { cookies } = props;
    this.toggleMenu = this.toggleMenu.bind(this);
    this.closeNewsBar = this.closeNewsBar.bind(this);
    const { cookieValue } = 
    this.state = { 
      mobileMenu: false, 
      visibleNewsBar: cookies.get('newsbar') ? false : true, 
      sticky: false,
      scrollDirection: 'bottom',
      lastScrollPos: null
    }
  }

  toggleMenu = () => {
    this.setState(({ mobileMenu }) => ({ mobileMenu: !mobileMenu}))
  };

  closeMenu = () => {
    this.setState({ mobileMenu: false });
  }

  closeNewsBar = () => {
    const { cookies } = this.props;
    const maxAge = 14 * (24 * 3600);
    cookies.set('newsbar', 1, { path: '/', maxAge: maxAge });
    this.setState({visibleNewsBar: false});
  }

  componentDidMount() {
    window.addEventListener('scroll', this.handleScroll.bind(this), true);
  }

  componentWillUnmount() {
    window.removeEventListener('scroll', this.handleScroll.bind(this), false);
  }

  handleScroll = (event) => {
    const scrollPosition = window.scrollY;
    if(this.state.lastScrollPos > scrollPosition) {
      this.setState({
        scrollDirection: 'top',
        lastScrollPos: scrollPosition
      });
    } else if(this.state.lastScrollPos < scrollPosition) {
      this.setState({
        scrollDirection: 'bottom',
        lastScrollPos: scrollPosition
      });
    }
    if (scrollPosition > 120) { this.setState({sticky: true}); } else { this.setState({sticky: false}); }
  }

  render() {
    const { pageLanguage } = this.props;
    return (
      <header className={this.state.sticky ? ('sticky '+ this.state.scrollDirection) : null}>
        {this.state.visibleNewsBar ?
        <div className="news">
          <div className="content">
          <Trans><a href="">April release is out. <span className="text-underline">Check out what's new!</span></a></Trans>
            <div className="close-icon" onClick={this.closeNewsBar}></div>
          </div>
        </div> : null}
        <div className="container">
          <div className="grid">
            <div className={this.state.mobileMenu ? 'logo open col-xs-3 col-ls-6 col-sm-6 col-md-3 col-lg-6' : 'logo col-xs-3 col-sm-6 col-md-3 col-lg-6'}>
            
              <NavLink to={pageLanguage ==  'en' || !pageLanguage ? `/` : `/${pageLanguage}`}><ReactSVG className="logo-svg" path="/images/saleor-logo.svg" /></NavLink>
            </div>
            <nav className={this.state.visibleNewsBar ? 'menu newsbar col-xs-9 col-ls-6 col-sm-6 col-md-9 col-lg-6' : 'menu col-xs-9 col-sm-6 col-md-9 col-lg-6'}>
              <ul className={this.state.mobileMenu ? 'menu-mobile hovered' : 'menu-desktop'}>
                <li><span className="count">01. </span><NavLink exact to="/" onClick={this.closeMenu}><Trans>Home</Trans></NavLink></li>
                <li className="underline"><span className="count">02. </span><NavLink to={pageLanguage ==  'en' || !pageLanguage ? `/features` : `/${pageLanguage}/features`} onClick={this.closeMenu}><Trans>Features</Trans></NavLink></li>
                <li className="underline"><span className="count">03. </span><NavLink to={pageLanguage ==  'en' || !pageLanguage ? `/roadmap` : `/${pageLanguage}/roadmap`} onClick={this.closeMenu}><Trans>Roadmap</Trans></NavLink></li>
                <li className="underline"><span className="count">04. </span><a href="https://saleor.readthedocs.io/en/latest/"><Trans>Docs</Trans></a></li>
                <li className="underline"><span className="count">05. </span><a href="https://medium.com/saleor"><Trans>Blog</Trans></a></li>
                <li className="github-link"><GitHubLink owner="mirumee" name="saleor" /></li>
                <li><span className="count">06. </span><a className={this.state.mobileMenu ? null : 'btn btn-primary'} href="https://mirumee.com/hire-us/"><Trans>Contact Us</Trans></a></li>
              </ul>
              <ul className="mobile-btn">
                <li className={this.state.mobileMenu ? 'github-link open' : 'github-link'} onClick={this.toggleMenu}><GitHubLink owner="mirumee" name="saleor" /></li>
                <li className={this.state.mobileMenu ? 'menu-icon open' : 'menu-icon'} onClick={this.toggleMenu}>
                  <span></span>
                  <span></span>
                  <span></span>
                  <span></span>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </header>
    );
  }
}

export default withRouter(withCookies(Header));