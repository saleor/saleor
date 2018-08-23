import React from 'react';
import { Link } from 'react-router-dom';
import ReactSVG from 'react-svg';

import css from './footer.css';

const Footer = () => (
  <footer>
    <div className="container">
      <div className="logo">
        <Link to="/"><ReactSVG path="images/saleor-logo.svg" /></Link>
      </div>
      <div className="content">
        <div className="grid">
          <div className="col-xs-12 col-sm-9 col-md-9 menu">
            <div className="grid">
              <div className="col-xs-4 col-sm-3 col-md-2">
                <ul>
                  <li><h4>Company</h4></li>
                  <li><a href="">About</a></li>
                  <li><a href="">Carieers</a></li>
                  <li><a href="">Contact</a></li>
                </ul>
              </div>
              <div className="col-xs-4 col-sm-3 col-md-2">
                <ul>
                  <li><h4>Solution</h4></li>
                  <li><a href="">Features</a></li>
                  <li><a href="">Roadmap</a></li>
                  <li><a href="">Docs</a></li>
                  <li><a href="">Demo</a></li>
                </ul>
              </div>
              <div className="col-xs-4 col-sm-3 col-md-2">
                <ul>
                  <li><h4>Community</h4></li>
                  <li><a href="">Contribute</a></li>
                  <li><a href="">Case studies</a></li>
                  <li><a href="">Become a partner</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="col-xs-12 col-sm-3 col-md-3 icons">
            <div className="grid">
              <div className="col-sm-1">
                <a href=""><ReactSVG className="twitter-icon" path="images/twiiter-icon.svg" /></a>
              </div>
              <div className="col-sm-1">
                <a href=""><ReactSVG className="facebook-icon" path="images/fb-icon.svg" /></a>
              </div>
              <div className="col-sm-1">
                <a href=""><ReactSVG className="github-icon" path="images/github-icon.svg" /></a>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="privacy-links grid">
        <div className="col-xs-6 col-sm-3 col-md-2">
          <a href="">Terms of service</a>
        </div>
        <div className="col-xs-6 col-sm-3 col-md-2">
          <Link to="/privacy-policy">Privacy policy</Link>
        </div>
      </div>
    </div>
  </footer>
)

export default Footer;