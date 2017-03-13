import React, {PropTypes} from 'react';
import Relay from 'react-relay';
import {Link, browserHistory} from 'react-router'
import DjangoCSRFToken from 'django-react-csrftoken'
import ReactMarkdown from 'react-markdown'

import ReleasePrice from './ReleasePrice';

class ReleaseDetailView extends React.Component {

  goBack = () => {
    this.props.onShowList()
    browserHistory.goBack()
  }

  render() {
    const {release} = this.props;
    return (
      <div>
        <div className="row">
          <div className="col-md-1 col-1">
            <button onClick={() => this.goBack()} className="btn secondary">&lt; Back to list</button>
          </div>
          <div className="row product">
            {/*<div id="product-schema-component">*/}
            {/*<script type="application/ld+json">{{json_ld_product_data | safe }}</script>*/}
            {/*</div>*/}
            <div className="col-md-3 col-12 product__gallery">
              <img className="d-block img-fluid"
                   src={release.thumbnailUrl} alt=""/>
              <div className="product__info__details">
                <div className="product__info__genre">
                  Genres
                  <p>
                    {release.genres.map(function (genre, i) {
                      return <span key={i}>{i > 0 ? ' / ' : ''}
                        <a href={genre.url}>{genre.name}</a>
                    </span>
                    })}
                  </p>
                </div>
                <div className="product__info__release_date">
                  Release Date
                  <p>{release.releasedAt}</p>
                </div>
                <div className="product__info__catno">
                  Cat No
                  <p>{release.catalogueNumber}</p>
                </div>
                <div className="product__info__original_release">
                  Original Release
                  <p>{release.originalReleasedAt}</p>
                </div>
              </div>
            </div>
            <div className="col-md-9 col-12 product__info">
              <h2
                className="product__info__artist">{release.artistFirstName} {release.artistLastName}</h2>
              <h2 className="product__info__name">{release.title}</h2>
              <h3 className="product__info__format">{release.format}</h3>
              <div className="product__info__form-error">
                <small className="text-danger"></small>
              </div>

              <div className="product__info__description">
                <hr/>
                <ReactMarkdown source={release.description}/>
              </div>
              <h2 className="product__info__price">
            <span>
              <ReleasePrice price={release.price} availability={release.availability}/>
            </span>
              </h2>
              <form id="product-form" role="form" className="product-form form-vertical"
                    method="post"
                    action={release.addToCartUrl} noValidate>
                <DjangoCSRFToken/>
                <div className="product__info__quantity"
                     style={{display: release.availability.status != 'out' ? 'block' : 'none'}}>
                  <label className="control-label" htmlFor="id_quantity">Quantity</label>
                  <input className="form-control" id="id_quantity" max="50" min="0" name="quantity"
                         title=""
                         type="number" defaultValue={1} required=""/>
                </div>
                <div className="form-group product__info__button">
                  {release.availability.status != 'out' ?
                    <button className="btn primary">Add to cart</button> :
                    <button className="btn secondary">Reserve</button>}
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    )
  }
}
export default Relay.createContainer(ReleaseDetailView, {
  initialVariables: {
    pageSize: 5
  },
  fragments: {
    release: () => Relay.QL`
      fragment on ArtikelType {
        id
        title
        artistFirstName
        artistLastName
        description
        format
        catalogueNumber
        originalReleasedAt
        releasedAt
        genres {
          pk
          name
          slug
          url
        }
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
        addToCartUrl
      }
    `
  }
});
