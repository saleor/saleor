import React, { Component, PropTypes } from 'react';

export default class sortBy extends Component {

  constructor(props) {
    super(props);
    this.state = {
      visibility: false
    };
  }

  static propTypes = {
    setSorting: PropTypes.func,
    sortedValue: PropTypes.string
  }

  setSorting = (event) => {
    const value = event.target.className;
    this.props.setSorting(value);
    this.changeVisibility();
  }

  changeVisibility = () => {
    this.setState({
      visibility: !this.state.visibility
    });
  }

  render() {
    const { sortedValue }  = this.props
    const { visibility } = this.state;
    return (
      <div className="sort-by">
        <div className={visibility ? ('click-area') : ('click-area hide')} onClick={this.changeVisibility}></div>
        <button className="btn btn-link" onClick={this.changeVisibility}>
          {sortedValue ? (
            sortedValue.search('-') ? (
              <div>
                <span>Sort by: <strong>{sortedValue}</strong></span>
                <i className="fa fa-arrow-up" aria-hidden="true"></i>
              </div>
            ) : (
               <div>
                <span>Sort by: <strong>{sortedValue.replace('-','')}</strong></span>
                <i className="fa fa-arrow-down" aria-hidden="true"></i>
              </div>
            )
          ) : (
            <span>Sort by: <strong>default</strong></span>
          )}
        </button>
        {visibility ? (
        <ul className="sort-list">
          <li className="name">
            <div className="row">
              <div className="col-md-6">Sort by <strong>Name</strong></div>
              <div className="col-md-6">
                  <span className="name" onClick={this.setSorting}>ascending</span>
                  <i className="fa fa-arrow-up pull-right" aria-hidden="true"></i>
              </div>
            </div>
            <div className="row">
              <div className="col-md-6"></div>
              <div className="col-md-6">
                  <span className="-name" onClick={this.setSorting}>descending</span>
                  <i className="fa fa-arrow-down pull-right" aria-hidden="true"></i>
              </div>
            </div>
          </li>
          <li className="price">
            <div className="row">
              <div className="col-md-6">Sort by <strong>Price</strong></div>
              <div className="col-md-6">
                  <span className="price" onClick={this.setSorting}>ascending</span>
                  <i className="fa fa-arrow-up pull-right" aria-hidden="true"></i>
              </div>
            </div>
            <div className="row">
              <div className="col-md-6"></div>
              <div className="col-md-6">
                  <span className="-price" onClick={this.setSorting}>descending</span>
                  <i className="fa fa-arrow-down pull-right" aria-hidden="true"></i>
              </div>
            </div>    
          </li>
        </ul>
        ) : (null)}
      </div>
    );
  }
}