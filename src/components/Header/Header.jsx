import React from 'react';
import { Link } from 'react-router-dom';
import ReactSVG from 'react-svg';

import { GitHubLink } from '..';

import css from './header.css';

const Header = () => (
    <header>
        <div className="container">
            <div class="grid">
                <div className="logo column-3">
                    <Link to="/"><ReactSVG className="star-icon" path="images/saleor-logo.svg" /></Link>
                </div>
                <nav className="menu column-7">
                    <ul>
                        <li><Link to="/features">Features</Link></li>
                        <li><Link to="/">Roadmap</Link></li>
                        <li><a href="https://saleor.readthedocs.io/en/latest/">Docs</a></li>
                        <li><Link to="/about">About</Link></li>
                        <li><a href="https://medium.com/saleor">Blog</a></li>
                        <li><GitHubLink owner="mirumee" name="saleor" /></li>
                        <li><a class="btn btn-primary" href="#">Contact Us</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>
)

export default Header;