import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => (
    <header>
        <nav>
            <ul>
                <li><Link to="/">Saleor</Link></li>
                <li><Link to="/features">Features</Link></li>
                <li><a href="https://saleor.readthedocs.io/en/latest/">Docs</a></li>
                <li><a href="https://medium.com/saleor">Blog</a></li>
            </ul>
        </nav>
    </header>
)

export default Header;