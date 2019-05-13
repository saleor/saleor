import _ from 'lodash';
import $ from 'jquery';
import classNames from 'classnames';
import { observer } from 'mobx-react';
import React, { Component } from 'react';
import PropTypes from 'prop-types';

import AttributeSelectionWidget from './AttributeSelectionWidget';
import QuantityInput from './QuantityInput';
import * as queryString from 'query-string';

export default observer(class VariantPicker extends Component {
  static propTypes = {
    onAddToCheckoutError: PropTypes.func.isRequired,
    onAddToCheckoutSuccess: PropTypes.func.isRequired,
    store: PropTypes.object.isRequired,
    url: PropTypes.string.isRequired,
    variantAttributes: PropTypes.array.isRequired,
    variants: PropTypes.array.isRequired
  };

  constructor (props) {
    super(props);
    const { variants } = this.props;

    const variant = variants.filter(v => !!Object.keys(v.attributes).length)[0];
    const params = queryString.parse(location.search);
    let selection = {};
    if (Object.keys(params).length) {
      Object.keys(params)
        .some((name) => {
          const valueName = params[name];
          const attribute = this.matchAttributeBySlug(name);
          const value = this.matchAttributeValueByName(attribute, valueName);
          if (attribute && value) {
            selection[attribute.pk] = value.pk.toString();
          } else {
            // if attribute doesn't exist - show variant
            selection = variant ? variant.attributes : {};
            // break
            return true;
          }
        });
    } else if (Object.keys(variant).length) {
      selection = variant.attributes;
    }
    this.state = {
      errors: {},
      quantity: 1,
      selection: selection
    };
    this.matchVariantFromSelection();
  }

  checkVariantAvailability = () => {
    const { store } = this.props;
    return store.variant.availability;
  };

  handleAddToCheckout = () => {
    const { onAddToCheckoutSuccess, onAddToCheckoutError, store } = this.props;
    const { quantity } = this.state;
    if (quantity > 0 && !store.isEmpty) {
      $.ajax({
        url: this.props.url,
        method: 'post',
        data: {
          quantity: quantity,
          variant: store.variant.id
        },
        success: () => {
          onAddToCheckoutSuccess();
        },
        error: (response) => {
          onAddToCheckoutError(response);
        }
      });
    }
  };

  handleAttributeChange = (attrId, valueId) => {
    this.setState({
      selection: Object.assign({}, this.state.selection, { [attrId]: valueId })
    }, () => {
      this.matchVariantFromSelection();
      let params = {};
      Object.keys(this.state.selection)
        .forEach(attrId => {
          const attribute = this.matchAttribute(attrId);
          const value = this.matchAttributeValue(attribute, this.state.selection[attrId]);
          if (attribute && value) {
            params[attribute.slug] = value.slug;
          }
        });
      history.pushState(null, null, '?' + queryString.stringify(params));
    });
  };

  handleQuantityChange = (event) => {
    this.setState({ quantity: parseInt(event.target.value) });
  };

  matchAttribute = (id) => {
    const { variantAttributes } = this.props;
    const match = variantAttributes.filter(attribute => attribute.pk.toString() === id);
    return match.length > 0 ? match[0] : null;
  };

  matchAttributeBySlug = (slug) => {
    const { variantAttributes } = this.props;
    const match = variantAttributes.filter(attribute => attribute.slug === slug);
    return match.length > 0 ? match[0] : null;
  };

  matchAttributeValue = (attribute, id) => {
    const match = attribute.values.filter(attribute => attribute.pk.toString() === id);
    return match.length > 0 ? match[0] : null;
  };

  matchAttributeValueByName = (attribute, name) => {
    const match = attribute ? attribute.values.filter(value => value.slug === name) : [];
    return match.length > 0 ? match[0] : null;
  };

  matchVariantFromSelection () {
    const { store, variants } = this.props;
    let matchedVariant = null;
    variants.forEach(variant => {
      if (_.isEqual(this.state.selection, variant.attributes)) {
        matchedVariant = variant;
      }
    });
    store.setVariant(matchedVariant);
  }

  render () {
    const { store, variantAttributes } = this.props;
    const { errors, selection, quantity } = this.state;
    const disableAddToCheckout = store.isEmpty || !this.checkVariantAvailability();

    const addToCheckoutBtnClasses = classNames({
      'btn btn-primary': true,
      'disabled': disableAddToCheckout
    });

    return (
      <div>
        {variantAttributes.map((attribute, i) =>
          <AttributeSelectionWidget
            attribute={attribute}
            handleChange={this.handleAttributeChange}
            key={i}
            selected={selection[attribute.pk]}
          />
        )}
        <div className="clearfix">
          <QuantityInput
            errors={errors.quantity}
            handleChange={this.handleQuantityChange}
            quantity={quantity}
          />
          <div className="form-group product__info__button">
            <button
              className={addToCheckoutBtnClasses}
              onClick={this.handleAddToCheckout}
              disabled={disableAddToCheckout}>
              {pgettext('Product details primary action', 'Add to checkout')}
            </button>
          </div>
        </div>
      </div>
    );
  }
});
