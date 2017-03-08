import React, { Component, PropTypes } from 'react';
import Relay from 'react-relay';

import ReleasePrice from './ReleasePrice'

class ReleaseItem extends Component {

  static propTypes = {
    release: PropTypes.object
  };

  getSchema = () => {
    const { release } = this.props;
    let data = {
      "@context": "http://schema.org/",
      "@type": "MusicAlbum",
      "name": release.title,
      "description": release.artistFirstName + ' ' + release.artistLastName,
      "url": release.url,
      "image": release.thumbnailUrl,
      "potentialAction": {
        "@type": "ListenAction",
        "target": [
          {
            "@type": "EntryPoint",
            "urlTemplate": release.url + "?autoplay=true",
            "actionPlatform": [
              "http://schema.org/DesktopWebPlatform",
              "http://schema.org/IOSPlatform",
              "http://schema.org/AndroidPlatform"
            ],
            "InLanguage": "English"
          }
        ],
        "expectsAcceptanceOf": {
          "@type": "Offer",
          "priceCurrency": release.price.currency,
          "price": release.price.gross,
          "eligibleRegion": [
            {
              "@type": "Country",
              "name": "DE"
            },
            {
              "@type": "Country",
              "name": "AT",
            },
            {
              "@type": "Country",
              "name": "CH",
            },
            {
              "@type": "Country",
              "name": "FR",
            },
            {
              "@type": "Country",
              "name": "GB",
            }
          ]
        },
      },
    };
    return JSON.stringify(data);
  };

  render() {
    const { release } = this.props;
    let productSchema = this.getSchema();
    return (
      <div className="col-12 col-sm-4 col-md-3 col-lg-2 product-list">
        <script type="application/ld+json">{productSchema}</script>
        <a href={release.url}>
          <div className="text-center">
            <div>
                <img className="img-responsive" src={release.thumbnailUrl} alt="" />
                <span className="product-list-item-artist-name"
                      title={release.artist_first_name}>{release.artistFirstName} {release.artistLastName}</span>
                <span className="product-list-item-name" title={release.title}>{release.title}</span>
                <span className="product-list-item-label" title={release.label}>{release.label}</span>
            </div>
            <div className="panel-footer">
              <ReleasePrice price={release.price} availability={release.availability} />
            </div>
          </div>
        </a>
      </div>
    );
  }
}

export default Relay.createContainer(ReleaseItem, {
  fragments: {
    release: () => Relay.QL`
      fragment on ArtikelType {
        id
        title
        artistFirstName
        artistLastName
        price {
          currency
          gross
          grossLocalized
          net
        }
        availability {
          ${ReleasePrice.getFragment('availability')}
        }
        thumbnailUrl
        url
      }
    `
  }
});
