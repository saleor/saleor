import React, { Component, PropTypes } from 'react';

export default class sortBy extends Component {

  static propTypes = {
    sortBy: PropTypes.func,
  };

  sortBy = (event) => this.props.sortBy(event);

  render() {
    return (
      <div className="sort-by">
        <button className="btn btn-link">
          <span>Sort by: <strong>Price</strong></span>
          <span className="caret">+</span>
        </button>
        <ul className="sort-list">
          <li className="name">
            <div className="row">
              <div className="col-md-6">Name:</div>
              <div className="col-md-6">
                <span className="name" onClick={this.sortBy}>ascending</span>
              </div>
            </div>
            <div className="row">
              <div className="col-md-6"></div>
              <div className="col-md-6">
                <span className="-name" onClick={this.sortBy}>descending</span>
              </div>
            </div>
          </li>
          <li className="price">
            <div className="row">
              <div className="col-md-6">Price:</div>
              <div className="col-md-6">
                <span className="price" onClick={this.sortBy}>ascending</span>
              </div>
            </div>
            <div className="row">
              <div className="col-md-6"></div>
              <div className="col-md-6">
                <span className="-price" onClick={this.sortBy}>descending</span>
              </div>
            </div>    
          </li>
        </ul>
      </div>
    );
  }
}