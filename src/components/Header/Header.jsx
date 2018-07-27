import React from 'react';
import { Link } from 'react-router-dom';

import { GitHubLink } from '..';
import Logo from '../../images/saleor-logo.svg';

const Header = () => (
    <header>
        <div className="container">
            <div class="grid">
                <div className="logo column-4">
                    <Link to="/"><img src={Logo} /></Link>
                </div>
                <nav className="menu column-6">
                    <ul>
                        <li><Link to="/">Saleor</Link></li>
                        <li><Link to="/features">Features</Link></li>
                        <li><a href="https://saleor.readthedocs.io/en/latest/">Docs</a></li>
                        <li><a href="https://medium.com/saleor">Blog</a></li>
                        <GitHubLink owner="mirumee" name="saleor" />
                    </ul>
                </nav>
            </div>
        </div>
    </header>
)

export default Header;