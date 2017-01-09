import _ from 'lodash'
import $ from 'jquery'
import classNames from 'classnames'
import React, { Component, PropTypes } from 'react'

import AttributeSelectionWidget from './AttributeSelectionWidget'
import QuantityInput from './QuantityInput'
import VariantPrice from './VariantPrice'


export default class VariantPicker extends Component {

  static propTypes = {
    availability: PropTypes.object.isRequired,
    onAddToCartError: PropTypes.func.isRequired,
    onAddToCartSuccess: PropTypes.func.isRequired,
    productAttributes: PropTypes.array.isRequired,
    url: PropTypes.string.isRequired,
    variantAttributes: PropTypes.array.isRequired,
    variants: PropTypes.array.isRequired
  }

  constructor(props) {
    super(props)
    const { variants } = this.props

    const variant = variants.filter(v => !!Object.keys(v.attributes).length)[0]
    const selection = variant ? variant.attributes : {}

    this.state = {
      errors: {},
      quantity: 1,
      variant: variant,
      selection: selection
    }
  }

  handleAddToCart = () => {
    const { onAddToCartSuccess, onAddToCartError } = this.props;
    const { quantity, variant } = this.state
    if (quantity > 0 && variant) {
      $.ajax({
        url: this.props.url,
        method: 'post',
        data: {
          quantity: quantity,
          variant: variant.id
        },
        success: () => {
          onAddToCartSuccess()
        },
        error: (response) => {
          onAddToCartError(response)
        }
      })
    }
  }

  handleAttributeChange = (attrId, valueId) => {
    this.setState({
      selection: Object.assign({}, this.state.selection, { [attrId]: valueId })
    }, () => {
      this.matchVariantFromSelection()
    })
  }

  handleQuantityChange = (event) => {
    this.setState({quantity: parseInt(event.target.value)})
  }

  matchVariantFromSelection() {
    let matchedVariant = null
    this.props.variants.forEach(variant => {
      if (_.isEqual(this.state.selection, variant.attributes)) {
        matchedVariant = variant
      }
    })
    this.setState({ variant: matchedVariant })
  }

  render() {
    const { availability, productAttributes, variantAttributes } = this.props
    const { errors, selection, quantity, variant } = this.state

    const addToCartBtnClasses = classNames({
      'btn primary': true,
      'disabled': !variant
    })

    return (
      <div>
        <VariantPrice availability={availability} variant={variant} />
        {productAttributes.map((item, i) =>
          <div className="form-group" key={i}>
              <label className="control-label"><b>{item.attribute}</b></label>
              <p>{item.value}</p>
          </div>
        )}
        {variantAttributes.map((attribute, i) =>
          <AttributeSelectionWidget
            attribute={attribute}
            handleChange={this.handleAttributeChange}
            key={i}
            selected={selection[attribute.pk]}
          />
        )}
        <QuantityInput
          errors={errors.quantity}
          handleChange={this.handleQuantityChange}
          quantity={quantity}
        />
        <div className="form-group">
          <button
            className={addToCartBtnClasses}
            onClick={this.handleAddToCart}>
            Add to cart
          </button>
        </div>
      </div>
    )
  }
}
