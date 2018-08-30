import * as PropTypes from 'prop-types';
import React, { Component } from 'react';
import InlineSVG from 'react-inlinesvg';

import arrowUpIcon from '../../../images/arrow-up.svg';
import arrowDownIcon from '../../../images/arrow-down.svg';

export default class sortBy extends Component {
  constructor(props) {
    super(props);
    this.state = {
      visibility: false,
      sortBy: this.props.sortBy
    };
  }

  static propTypes = {
    setSorting: PropTypes.func,
    sortedValue: PropTypes.string
  };

  setSorting = (event) => {
    const value = event.currentTarget.className;
    this.props.setSorting(value);
    this.changeVisibility();
    this.changeLabel(value);
  };

  changeLabel = (value) => {
    this.props.sortedValue = value;
    this.setState({
      sortBy: value
    });
  };

  changeVisibility = () => {
    this.setState({
      visibility: !this.state.visibility
    });
  };

  render() {
    const sortedValue = this.props.sortedValue;
    const visibility = this.state.visibility;
    return (
      <div className="sort-by">
        <div className={visibility ? ('click-area') : ('click-area hide')} onClick={this.changeVisibility}></div>
        <button className="btn btn-link" onClick={this.changeVisibility}>
          {sortedValue ? (
            sortedValue.search('-') ? (
              <div>
                <span>{pgettext('Category page filters', 'Sort by:')}
                  <b> {sortedValue}</b>
                </span>
                <div className="sort-order-icon">
                  <InlineSVG key="arrowUpIcon" src={arrowUpIcon}/>
                </div>
              </div>
            ) : (
              <div>
                <span>{pgettext('Category page filters', 'Sort by:')}
                  <b> {sortedValue.replace('-', '')}</b>
                </span>
                <div className="sort-order-icon">
                  <InlineSVG key="arrowDownIcon" src={arrowDownIcon}/>
                </div>
              </div>
            )
          ) : (
            <span>{pgettext('Category page filters', 'Sort by:')}
              <b> {pgettext('Category page filters', 'default')}</b>
            </span>
          )}
        </button>
        {visibility && (
          <ul className="sort-list">
            <li className="name">
              <div className="row">
                <div className="col-6">{pgettext('Category page filters', 'Sort by:')}
                  <b> {gettext('Name')}</b></div>
                <div className="col-6">
                  <div className="name" onClick={this.setSorting}>
                    <span>{pgettext('Category page filters', 'ascending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowUpIcon}/>
                    </div>
                  </div>
                </div>
              </div>
              <div className="row">
                <div className="col-6"></div>
                <div className="col-6">
                  <div className="-name" onClick={this.setSorting}>
                    <span>{pgettext('Category page filters', 'descending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowDownIcon}/>
                    </div>
                  </div>
                </div>
              </div>
            </li>
            <li className="price">
              <div className="row">
                <div className="col-6">{pgettext('Category page filters', 'Sort by:')}
                  <b> {pgettext('Category page filters', 'Price')}</b></div>
                <div className="col-6">
                  <div className="price" onClick={this.setSorting}>
                    <span>{pgettext('Category page filters', 'ascending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowUpIcon}/>
                    </div>
                  </div>
                </div>
              </div>
              <div className="row">
                <div className="col-6"></div>
                <div className="col-6">
                  <div className="-price" onClick={this.setSorting}>
                    <span>{pgettext('Category page filters', 'descending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowDownIcon}/>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        )}
      </div>
    );
  }
}
