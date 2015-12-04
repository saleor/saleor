/* @flow */

import React, {Component, findDOMNode} from 'react';
import {connect} from 'react-redux';
import $ from 'jquery';

export class CartItemAmountOption extends Component {
  render(): Component {
    var value = this.props.value;
    var label = this.props.label ? this.props.label : value;
    return <option value={value}>{label}</option>;
  };
}

class CartItemAmountSelect extends Component {
  constructor() {
    super(...arguments);
    this.state = {
      error: null,
      lastSavedValue: this.props.value,
      renderSelect: false,
      renderSubmit: false,
      result: null,
      sending: false,
      value: this.props.value
    };
  }

  componentDidMount() {
    if (this.state.value < this.props.thresholdValue) {
      this.setState({renderSelect: true});
    }
  }

  change(event) {
    let newValue = event.target.value;
    this.setState({result: null});
    if (newValue != this.props.thresholdValue || !this.state.renderSelect) {
      this.setState({value: newValue});
    }
    if (newValue >= this.props.thresholdValue) {
      this.setState({renderSelect: false});
    }
    if (newValue < this.props.thresholdValue && this.state.renderSelect) {
      this.sendQuantity(newValue);
    }

    if (!this.state.renderSelect && !this.state.sending) {
      this.setState({renderSubmit: true});
    }
  }

  valueChanged() {
    return this.state.lastSavedValue != this.state.value;
  }

  checkKey(event) {
    if (event.key === 'Enter' && this.valueChanged()) {
      this.sendQuantityWrapper();
    }
  }

  sendQuantityWrapper() {
    this.sendQuantity(this.refs.inputQuantity.props.value);
  }

  sendQuantity(quantity) {
    this.setState({renderSubmit: false});
    this.setState({sending: true});

    $.ajax({
      url: this.props.url,
      method: 'post',
      data: {[this.props.fieldName]: quantity},
      complete: () => {
        this.setState({sending: false});
        if (quantity < this.props.thresholdValue) {
          this.setState({renderSelect: true});
        }
      },
      success: (response) => {
        if (!quantity) {
          if (!response.total) {
            location.reload();
          }
          $(findDOMNode(this)).parents('tr').fadeOut(function() {
            $(this).remove();
          });
        }
        if (response.hasOwnProperty('productId')) {
          let {productId, subtotal, total} = response;
          let props = {productId, subtotal};
          this.props.dispatch({type: 'UPDATE_SUBTOTAL', ...props});
          this.props.dispatch({type: 'UPDATE_TOTAL', total});
        }
        this.setState({result: 'success', lastSavedValue: quantity});
        setTimeout(() => {
          this.setState({result: null});
        }, 1000);
      },
      error: (response) => {
        this.setState({error: response.error.quantity, result: 'error'});
      }
    });
  }

  removeFromCart() {
    this.sendQuantity(0);
  }

  render() {
    let classNames = [this.props.className];
    switch (this.state.result) {
      case ('success'):
        classNames.push('has-success');
        break;
      case ('error'):
        classNames.push('has-error');
        break;
    }
    let classNamesInput = ['input-group', 'cart-item-quantity'];
    if ((!this.state.renderSubmit || !this.valueChanged()) && !(this.state.result === 'error')) {
      classNamesInput.push('no-submit');
    }

    let options = this.props.options.map((option) => <CartItemAmountOption key={option} value={option} label={option == this.props.thresholdValue ? `${option} +` : option} />);
    let select = <select onChange={this.change.bind(this)} value={this.state.value} className="form-control cart-item-quantity-select">
      {options}
    </select>;
    let input = <div className={classNamesInput.join(' ')}>
      <input onKeyUp={this.checkKey.bind(this)} onChange={this.change.bind(this)} id="id_quantity" max={this.props.max} min="1" ref="inputQuantity" name="quantity" type="number" alue={this.state.value} />
      <span className="input-group-btn">
        <button onClick={this.sendQuantityWrapper.bind(this)} className="btn btn-info" type="submit">Update</button>
      </span>
    </div>;
    return <div className={classNames.join(' ')}>
      {this.state.renderSelect ? select : input}
      {this.state.sending && !(this.state.result == 'error')? <i className="fa fa-circle-o-notch fa-spin"></i> : ''}
      {this.state.result == 'error' ? <span className="error text-danger">{this.state.error}</span> : ''}
      <button type="submit" className="btn btn-link btn-sm cart-item-remove" onClick={this.removeFromCart.bind(this)}>
        <span className="text-muted">Remove from cart</span>
      </button>
    </div>;
  }
}

function selectQuantities(state) {
  // FIXME: move quantities to store
  return {};
}

export var CartItemAmount = connect(selectQuantities)(CartItemAmountSelect);

let renderSubtotal = ({productId, subtotals}) => {
  let value;
  if (subtotals.hasOwnProperty(productId)) {
    value = subtotals[productId];
  }
  return <span>{value}</span>;
}

function selectSubtotals(state) {
  return {'subtotals': state.subtotals};
}

export var CartItemSubtotal = connect(selectSubtotals)(renderSubtotal);

let renderTotal = ({value}) => <b>{value}</b>;

function selectTotal(state) {
  return {'value': state.total};
}

export var CartTotal = connect(selectTotal)(renderTotal);
