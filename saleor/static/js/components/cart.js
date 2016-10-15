/* @flow */

import React, { Component, findDOMNode, PropTypes } from 'react'
import { connect } from 'react-redux'
import $ from 'jquery'

export class CartItemAmountOption extends Component {
  render(): React.Element {
    const value = this.props.value
    const label = this.props.label ? this.props.label : value
    return <option value={value}>{label}</option>
  }
}

class CartItemAmountSelect extends Component {
  static propTypes = {
    className: PropTypes.string,
    fieldName: PropTypes.string.isRequired,
    max: PropTypes.number,
    min: PropTypes.number,
    options: PropTypes.arrayOf(PropTypes.number).isRequired,
    thresholdValue: PropTypes.number,
    value: PropTypes.number.isRequired
  };

  state: {
    error: ?string;
    lastSavedValue: number;
    renderSelect: bool;
    renderSubmit: bool;
    result: ?string;
    sending: bool;
    value: number
  } = {
    error: null,
    lastSavedValue: this.props.value,
    renderSelect: false,
    renderSubmit: false,
    result: null,
    sending: false,
    value: this.props.value
  };

  _change = (event) => {
    let newValue = event.target.value
    this.setState({ result: null })
    if (newValue !== this.props.thresholdValue || !this.state.renderSelect) {
      this.setState({ value: newValue })
    }
    if (newValue >= this.props.thresholdValue) {
      this.setState({ renderSelect: false })
    }
    if (newValue < this.props.thresholdValue && this.state.renderSelect) {
      this.sendQuantity(newValue)
    }
    if (!this.state.renderSelect && !this.state.sending) {
      this.setState({ renderSubmit: true })
    }
  };

  _checkKey = (event) => {
    if (event.key === 'Enter' && this.valueChanged()) {
      this.sendQuantityWrapper()
    }
  };

  componentDidMount() {
    if (this.state.value < this.props.thresholdValue) {
      this.setState({ renderSelect: true })
    }
  }

  valueChanged() {
    return this.state.lastSavedValue != this.state.value
  }

  sendQuantityWrapper() {
    this.sendQuantity(this.state.value)
  }

  sendQuantity(quantity) {
    this.setState({ renderSubmit: false })
    this.setState({ sending: true })

    $.ajax({
      url: this.props.url,
      method: 'post',
      data: { [this.props.fieldName]: quantity },
      complete: () => {
        this.setState({ sending: false })
        if (quantity < this.props.thresholdValue) {
          this.setState({ renderSelect: true })
        }
      },
      success: (response) => {
        if (!quantity) {
          if (!response.total) {
            location.reload()
          }
          $(findDOMNode(this)).parents('tr').fadeOut(function() {
            $(this).remove()
          })
        }
        if (response.hasOwnProperty('variantId')) {
          const { variantId, subtotal, total, localTotal } = response
          this.props.dispatch({
            type: 'UPDATE_SUBTOTAL',
            variantId,
            subtotal
          })
          this.props.dispatch({
            type: 'UPDATE_TOTAL',
            total,
            localTotal
          })
        }
        this.setState({
          result: 'success',
          lastSavedValue: quantity
        })
        setTimeout(() => {
          this.setState({ result: null })
        }, 1000)
      },
      error: (response) => {
        this.setState({
          error: response.error.quantity,
          result: 'error'
        })
      }
    })
  }

  removeFromCart() {
    this.sendQuantity(0)
  }

  render() {
    let classNames = [this.props.className]
    switch (this.state.result) {
      case ('success'):
        classNames.push('has-success')
        break
      case ('error'):
        classNames.push('has-error')
        break
    }
    let classNamesInput = ['input-group', 'cart-item-quantity']
    if (
      (!this.state.renderSubmit || !this.valueChanged())
      && !(this.state.result === 'error')
    ) {
      classNamesInput.push('no-submit')
    }

    const options = this.props.options.map((option) => (
      <CartItemAmountOption
        key={option}
        label={option == this.props.thresholdValue ? `${option} +` : option}
        value={option}
      />
    ))
    const select = (
      <select
        className="form-control cart-item-quantity-select"
        onChange={this._change}
        value={this.state.value}
      >
        {options}
      </select>
    )
    const input = (
      <div className={classNamesInput.join(' ')}>
        <input
          className="form-control"
          id="id_quantity"
          max={this.props.max}
          min={1}
          name="quantity"
          onChange={this._change}
          onKeyUp={this._checkKey}
          ref="inputQuantity"
          type="number"
          value={this.state.value}
        />
        <span className="input-group-btn">
          <button
            className="btn btn-info"
            onClick={this.sendQuantityWrapper.bind(this)}
            type="submit"
          >
            Update
          </button>
        </span>
      </div>
    )
    return (
      <div className={classNames.join(' ')}>
        {this.state.renderSelect ? select : input}
        {this.state.sending && this.state.result !== 'error' ? (
          <i className="glyphicon glyphicon-time"></i>
        ) : undefined}
        {this.state.result === 'error' ? (
          <span className="error text-danger">
            {this.state.error}
          </span>
        ) : undefined}
        <button
          className="btn btn-link btn-sm cart-item-remove"
          onClick={this.removeFromCart.bind(this)}
          type="submit"
        >
          <span className="text-muted">
            Remove from cart
          </span>
        </button>
      </div>
    )
  }
}

const selectQuantities = (state) => ({}) // FIXME: move quantities to store

export const CartItemAmount = connect(selectQuantities)(CartItemAmountSelect);

const renderSubtotal = ({variantId, subtotals}) => {
  let value;
  if (subtotals.hasOwnProperty(variantId)) {
    value = subtotals[variantId]
  }
  return <span>{value}</span>
}

const selectSubtotals = (state) => ({
  subtotals: state.subtotals
})

export const CartItemSubtotal = connect(selectSubtotals)(renderSubtotal)

const renderTotal = ({total, localTotal}) => <span>
  {total}
  {localTotal ? <br/> : undefined}
  {localTotal ? <small className="text-info">&asymp; {localTotal}</small> : undefined}
</span>

const selectTotal = (state) => ({
  total: state.total,
  localTotal: state.localTotal
})

export const CartTotal = connect(selectTotal)(renderTotal)
