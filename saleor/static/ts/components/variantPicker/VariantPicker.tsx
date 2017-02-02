import _ from 'lodash';
import * as $ from 'jquery';
import classNames from 'classnames';
import { observer } from 'mobx-react';
import * as React from 'react';

import AttributeSelectionWidget from './AttributeSelectionWidget';
import QuantityInput from './QuantityInput';


interface VariantPickerProps {
  onAddToCartError(response: any): any;
  onAddToCartSuccess(): any;
  store: any;
  url: string;
  variantAttributes: [any];
  variants: [any];
};

interface VariantPickerState {
  errors: {};
  quantity: number;
  selection: {};
};

@observer
export default class VariantPicker extends React.Component<VariantPickerProps, VariantPickerState> {
  constructor(props) {
    super(props);
    const { store, variants } = this.props;

    const variant = variants.filter(v => !!Object.keys(v.attributes).length)[0];
    const selection = variant ? variant.attributes : {};

    this.state = {
      errors: {},
      quantity: 1,
      selection: selection
    };
    store.setVariant(variant);
  }

  handleAddToCart = () => {
    const { onAddToCartSuccess, onAddToCartError, store } = this.props;
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
          onAddToCartSuccess();
        },
        error: (response) => {
          onAddToCartError(response);
        }
      });
    }
  }

  handleAttributeChange = (attrId, valueId) => {
    this.setState({
      selection: {...this.state.selection, [attrId]: valueId }
    }, this.matchVariantFromSelection);
  }

  handleQuantityChange = (event) => {
    this.setState({quantity: parseInt(event.target.value)});
  }

  matchVariantFromSelection() {
    const { store, variants } = this.props;
    let matchedVariant = null;
    variants.forEach(variant => {
      if (_.isEqual(this.state.selection, variant.attributes)) {
        matchedVariant = variant;
      }
    });
    store.setVariant(matchedVariant);
  }

  render() {
    const { store, variantAttributes } = this.props;
    const { errors, selection, quantity } = this.state;
    const disableAddToCart = store.isEmpty;

    const addToCartBtnClasses = classNames({
      'btn primary': true,
      'disabled': disableAddToCart
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
            errors={errors['quantity']}
            handleChange={this.handleQuantityChange}
            quantity={quantity}
          />
          <div className="form-group product__info__button">
            <button
              className={addToCartBtnClasses}
              onClick={this.handleAddToCart}
              disabled={disableAddToCart}>
              {gettext('Add to cart')}
            </button>
          </div>
        </div>
      </div>
    );
  }
}
