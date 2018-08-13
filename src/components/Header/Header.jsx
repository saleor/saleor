import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import ReactSVG from 'react-svg';

import { GitHubLink } from '..';

import css from './header.css';

class Header extends Component {
  constructor(props) {
    super(props);
    this.toggleMenu= this.toggleMenu.bind(this);
    this.state = { mobileMenu: false };
  }

  toggleMenu() {
    const currentState = this.state.mobileMenu;
    this.setState({ mobileMenu: !currentState });
  };

  render() {
    return (
      <header>
        <div className="container">
          <div className="grid">
            <div className={this.state.mobileMenu ? 'logo open col-xs-3 col-sm-3' : 'logo col-xs-3 col-sm-3'}>
              <Link to="/"><ReactSVG className="logo-svg" path="images/saleor-logo.svg" /></Link>
            </div>
            <nav className="menu col-xs-9 col-sm-9">
              <ul className={this.state.mobileMenu ? 'menu-mobile hovered' : null}>
                <li className="home"><span className="count">01. </span><Link to="/">Home</Link></li>
                <li><span className="count">02. </span><Link to="/features">Features</Link></li>
                <li><span className="count">03. </span><Link to="/roadmap">Roadmap</Link></li>
                <li><span className="count">04. </span><a href="https://saleor.readthedocs.io/en/latest/">Docs</a></li>
                <li><span className="count">05. </span><Link to="/about">About</Link></li>
                <li><span className="count">06. </span><a href="https://medium.com/saleor">Blog</a></li>
                <li className="github-link"><GitHubLink owner="mirumee" name="saleor" /></li>
                <li><span className="count">07. </span><a className={this.state.mobileMenu ? null : 'btn btn-primary'} href="https://mirumee.com/hire-us/">Contact Us</a></li>
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

export default Header;