import React from "react";
import { Link, NavLink } from "react-router-dom";
import ReactSVG from "react-svg";

import css from "./footer.css";

const Footer = () => (
  <div>
    <footer>
      <div className="container">
        <div className="logo">
          <Link to="/" aria-label="Saleor Logo">
            <ReactSVG className="saleor-logo" path="images/saleor-logo.svg" />
          </Link>
          <div className="craftedBy">
            <span>crafted by</span>
            <a href="https://mirumee.com" target="_blank">
              <ReactSVG
                className="mirumee-logo"
                path="images/logo-mirumee.svg"
              />
            </a>
          </div>
        </div>
        <div className="content">
          <div className="grid">
            <div className="col-xs-12 col-sm-9 col-md-10 col-lg-11 menu">
              <div className="grid">
                <div className="col-xs-6 col-sm-4 col-md-3 col-lg-2 col-xlg-1 menu-item">
                  <ul>
                    <li>
                      <h4>Company</h4>
                    </li>
                    <li>
                      <a href="https://medium.com/saleor">Blog</a>
                    </li>
                    <li>
                      <a href="https://mirumee.com/jobs/">Careers</a>
                    </li>
                    <li>
                      <a href="https://mirumee.typeform.com/to/Xwfril">
                        Contact
                      </a>
                    </li>
                  </ul>
                </div>
                <div className="col-xs-6 col-sm-4 col-md-3 col-lg-2 col-xlg-1 menu-item">
                  <ul>
                    <li>
                      <h4>Solution</h4>
                    </li>
                    <li>
                      <NavLink to="/features">Features</NavLink>
                    </li>
                    <li>
                      <NavLink to="/roadmap">Roadmap</NavLink>
                    </li>
                    <li>
                      <a href="https://docs.getsaleor.com">Docs</a>
                    </li>
                    <li>
                      <a href="https://demo.getsaleor.com/en/">Demo</a>
                    </li>
                  </ul>
                </div>
                <div className="col-xs-6 col-sm-4 col-md-3 col-lg-2 col-xlg-1 menu-item">
                  <ul>
                    <li>
                      <h4>Community</h4>
                    </li>
                    <li>
                      <a href="https://github.com/mirumee/saleor">Contribute</a>
                    </li>
                    {/* <li><a href="">Case studies</a></li> */}
                    <li>
                      <a href="mailto:hello@mirumee.com">Become a partner</a>
                    </li>
                  </ul>
                </div>
                <div className="col-xs-6 col-sm-4 col-md-3 col-lg-2 col-xlg-1 menu-item">
                  <ul>
                    <li>
                      <h4>About</h4>
                    </li>
                    <li>
                      <Link to="/privacy-policy-terms-and-conditions">
                        Privacy policy
                      </Link>
                    </li>
                    {/* <li><a href="">Terms of service</a></li> */}
                  </ul>
                </div>
              </div>
            </div>
            <div className="col-xs-12 col-sm-3 col-md-2 col-lg-1 icons">
              <h4>Find us</h4>
              <div className="grid">
                <div className="col-sm-1 col-md-4">
                  <a
                    href="https://twitter.com/mirumeelabs"
                    target="_blank"
                    aria-label="Twitter"
                    rel="noopener"
                  >
                    <ReactSVG
                      className="twitter-icon"
                      path="images/twiiter-icon.svg"
                    />
                  </a>
                </div>
                <div className="col-sm-1 col-md-4">
                  <a
                    href="https://www.facebook.com/mirumeelabs/"
                    target="_blank"
                    aria-label="Facebook"
                    rel="noopener"
                  >
                    <ReactSVG
                      className="facebook-icon"
                      path="images/fb-icon.svg"
                    />
                  </a>
                </div>
                <div className="col-sm-1 col-md-4">
                  <a
                    href="https://github.com/mirumee/saleor"
                    target="_blank"
                    aria-label="Github"
                    rel="noopener"
                  >
                    <ReactSVG
                      className="github-icon"
                      path="images/github-icon.svg"
                    />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
    <p className="copyright">COPYRIGHT © 2009–2018 MIRUMEE SOFTWARE</p>
  </div>
);

export default Footer;
