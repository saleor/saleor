import React, { Component, PropTypes } from 'react';

export default class sortBy extends Component {

  constructor(props) {
    super(props);
    this.state = {
      sortedElement: '',
      visibility: false
    };
  }

  static propTypes = {
    sortBy: PropTypes.func,
  }

  setSorting = (event) => {
    this.props.sortBy(event);
    this.setState({
      sortedElement: event.target.classList
    });
    this.changeVisibility();
  }

  changeVisibility = () => {
    this.setState({
      visibility: !this.state.visibility
    });
  }

  render() {
    const { sortedElement, visibility } = this.state;
    return (
      <div className="sort-by">
        <button className="btn btn-link" onClick={this.changeVisibility}>
          <span>Sort by: <strong>{sortedElement}</strong></span>
        </button>
        {visibility ? (
        <ul className="sort-list">
          <li className="name">
            <div className="row">
              <div className="col-md-6">Name:</div>
              <div className="col-md-6">
                <span className="name" onClick={this.setSorting}>ascending</span>
              </div>
            </div>
            <div className="row">
              <div className="col-md-6"></div>
              <div className="col-md-6">
                <span className="-name" onClick={this.setSorting}>descending</span>
              </div>
            </div>
          </li>
          <li className="price">
            <div className="row">
              <div className="col-md-6">Price:</div>
              <div className="col-md-6">
                <span className="price" onClick={this.setSorting}>ascending</span>
              </div>
            </div>
            <div className="row">
              <div className="col-md-6"></div>
              <div className="col-md-6">
                <span className="-price" onClick={this.setSorting}>descending</span>
              </div>
            </div>    
          </li>
        </ul>
        ) : (null)}
      </div>
    );
  }
}